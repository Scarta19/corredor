"""The nightly renewal sweep (Módulo 5, §12).

Runs once a day per tenant: schedule any renewal actions that have come due,
move policy states the calendar has decided, and re-score churn risk for the
policies close enough to expiry for the score to matter.

Everything here is safe to run twice. `planificar_acciones` is idempotent by
construction and the unique constraint on `(poliza_id, umbral_dias)` is the
backstop, so a retried job, a doubled cron or a manual run after an outage all
converge on the same state.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import date, timedelta
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from corredor.core.config import get_settings
from corredor.core.logging import get_logger
from corredor.db.session import get_session_factory
from corredor.domain.enums import EstadoPoliza
from corredor.domain.polizas import Poliza
from corredor.domain.tenancy import Tenant
from corredor.services.renovaciones import barrer_renovaciones
from corredor.services.riesgo import calcular_riesgo

log = get_logger(__name__)

#: Only score policies inside this horizon. Churn risk for something expiring
#: in two years is arithmetic nobody will act on, and scoring the whole book
#: every night is work for its own sake.
HORIZONTE_RIESGO_DIAS = 120


@dataclass(slots=True)
class ResultadoDiario:
    tenants: int = 0
    acciones_creadas: int = 0
    polizas_actualizadas: int = 0
    riesgos_calculados: int = 0

    def __str__(self) -> str:
        return (
            f"{self.tenants} agencias · {self.acciones_creadas} acciones · "
            f"{self.polizas_actualizadas} estados · {self.riesgos_calculados} riesgos"
        )


async def _puntuar_riesgos(session: AsyncSession, *, tenant_id: uuid.UUID, hoy: date) -> int:
    polizas = (
        await session.scalars(
            select(Poliza).where(
                Poliza.tenant_id == tenant_id,
                Poliza.estado.in_((EstadoPoliza.VIGENTE, EstadoPoliza.PROXIMA_A_VENCER)),
                Poliza.fecha_vencimiento <= hoy + timedelta(days=HORIZONTE_RIESGO_DIAS),
                Poliza.fecha_vencimiento >= hoy,
            )
        )
    ).all()

    for poliza in polizas:
        await calcular_riesgo(session, poliza=poliza, hoy=hoy)
    return len(polizas)


async def ejecutar_barrido(hoy: date | None = None) -> ResultadoDiario:
    """Sweep every active tenant.

    Each tenant commits separately: one agency's bad data must not stop the
    others from getting their renewal tasks.
    """
    settings = get_settings()
    hoy = hoy or date.today()
    factory = get_session_factory()
    resultado = ResultadoDiario()

    async with factory() as session:
        tenants = (await session.scalars(select(Tenant).where(Tenant.activo.is_(True)))).all()
        identificadores = [t.id for t in tenants]

    for tenant_id in identificadores:
        try:
            async with factory() as session:
                barrido = await barrer_renovaciones(
                    session,
                    tenant_id=tenant_id,
                    hoy=hoy,
                    umbrales=settings.renewal_thresholds_days,
                )
                puntuadas = await _puntuar_riesgos(session, tenant_id=tenant_id, hoy=hoy)
                await session.commit()

            resultado.tenants += 1
            resultado.acciones_creadas += barrido.acciones_creadas
            resultado.polizas_actualizadas += barrido.polizas_actualizadas
            resultado.riesgos_calculados += puntuadas
        except Exception:
            # A tenant that fails is logged and skipped, not allowed to abort
            # the run. Renewals missed for one agency is a support ticket;
            # missed for all of them is lost revenue.
            log.exception("barrido_fallido", tenant_id=str(tenant_id))

    log.info("barrido_diario_completado", resultado=str(resultado))
    return resultado


async def barrido_diario(ctx: dict[str, Any]) -> str:
    """Arq entry point.

    Arq calls its tasks with a context dict as the first argument; keeping
    that signature separate from `ejecutar_barrido` means the sweep stays
    callable from a script, a test or a shell without inventing a fake
    context.
    """
    del ctx  # the sweep needs nothing from arq's context
    return str(await ejecutar_barrido())
