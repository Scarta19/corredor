"""The renewal engine (Módulo 5).

The planning rules live in `planificar_acciones`, a pure function over dates.
Keeping it free of the database is what makes the awkward cases — a policy
imported three weeks before it expires, a sweep that runs twice, a sweep that
does not run for a week — cheap to test exhaustively instead of reasoned
about in a code review.
"""

from __future__ import annotations

import uuid
from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from datetime import date, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from corredor.core.logging import get_logger
from corredor.domain.enums import EstadoPoliza, EstadoRenovacion
from corredor.domain.polizas import Poliza, Renovacion

log = get_logger(__name__)

#: Thresholds from §12 of the platform brief, in days before expiry.
UMBRALES_POR_DEFECTO: tuple[int, ...] = (60, 30, 15, 7)


@dataclass(frozen=True, slots=True)
class AccionRenovacion:
    """A renewal task that should exist but does not yet."""

    umbral_dias: int
    fecha_objetivo: date
    #: True when the threshold's date had already passed when we first saw
    #: the policy — an import of an existing book, typically.
    recuperada: bool = False


def planificar_acciones(
    *,
    fecha_vencimiento: date,
    umbrales_existentes: Iterable[int],
    hoy: date,
    umbrales: Sequence[int] = UMBRALES_POR_DEFECTO,
) -> list[AccionRenovacion]:
    """Decide which renewal actions are missing for one policy.

    Three rules, in order:

    1. A threshold that already has a row is never produced again. This is
       what makes the sweep idempotent — it can run hourly, or twice after a
       retry, without duplicating a task or re-contacting a client.
    2. A threshold still in the future produces a task on its own date.
    3. Thresholds already in the past — because the policy was imported late,
       or the sweep did not run — collapse into a *single* catch-up task at
       the most recent one. Creating four overdue tasks for one policy floods
       the advisor's queue and tells them nothing they cannot see from the
       expiry date itself.

    An already-expired policy produces nothing; it is the sweep's job to move
    it to `VENCIDA`, not to schedule calls about it.
    """
    if fecha_vencimiento < hoy:
        return []

    ya_existen = set(umbrales_existentes)
    pendientes = sorted((u for u in umbrales if u not in ya_existen), reverse=True)

    futuras: list[AccionRenovacion] = []
    vencidas: list[AccionRenovacion] = []
    for umbral in pendientes:
        objetivo = fecha_vencimiento - timedelta(days=umbral)
        if objetivo >= hoy:
            futuras.append(AccionRenovacion(umbral_dias=umbral, fecha_objetivo=objetivo))
        else:
            vencidas.append(
                AccionRenovacion(umbral_dias=umbral, fecha_objetivo=hoy, recuperada=True)
            )

    # `vencidas` is ordered by descending threshold, so the last element is
    # the one whose date passed most recently: the only catch-up worth doing.
    acciones = futuras
    if vencidas and not ya_existen:
        acciones = [vencidas[-1], *futuras]
    return sorted(acciones, key=lambda a: a.fecha_objetivo)


def estado_por_vencimiento(
    *, fecha_vencimiento: date, hoy: date, umbral_aviso: int = 60
) -> EstadoPoliza:
    """The state a live policy should be in, given today's date.

    Only ever returns states the calendar can justify. `RENOVADA` and
    `CANCELADA` are human decisions and are never applied here.
    """
    dias = (fecha_vencimiento - hoy).days
    if dias < 0:
        return EstadoPoliza.VENCIDA
    if dias <= umbral_aviso:
        return EstadoPoliza.PROXIMA_A_VENCER
    return EstadoPoliza.VIGENTE


@dataclass(slots=True)
class ResultadoBarrido:
    """What one sweep did, for logging and for the admin's peace of mind."""

    polizas_revisadas: int = 0
    acciones_creadas: int = 0
    polizas_actualizadas: int = 0

    def __str__(self) -> str:
        return (
            f"{self.polizas_revisadas} pólizas revisadas, "
            f"{self.acciones_creadas} acciones creadas, "
            f"{self.polizas_actualizadas} estados actualizados"
        )


async def barrer_renovaciones(
    session: AsyncSession,
    *,
    tenant_id: uuid.UUID,
    hoy: date | None = None,
    umbrales: Sequence[int] = UMBRALES_POR_DEFECTO,
) -> ResultadoBarrido:
    """Bring every live policy of a tenant in line with the renewal rules.

    Safe to run as often as desired; see `planificar_acciones` for why.
    """
    hoy = hoy or date.today()
    horizonte = max(umbrales) if umbrales else 0
    resultado = ResultadoBarrido()

    consulta = (
        select(Poliza)
        .where(
            Poliza.tenant_id == tenant_id,
            Poliza.estado.in_((EstadoPoliza.VIGENTE, EstadoPoliza.PROXIMA_A_VENCER)),
            Poliza.fecha_vencimiento <= hoy + timedelta(days=horizonte),
        )
        .order_by(Poliza.fecha_vencimiento)
    )
    polizas = (await session.scalars(consulta)).all()

    for poliza in polizas:
        resultado.polizas_revisadas += 1

        existentes = (
            await session.scalars(
                select(Renovacion.umbral_dias).where(Renovacion.poliza_id == poliza.id)
            )
        ).all()

        for accion in planificar_acciones(
            fecha_vencimiento=poliza.fecha_vencimiento,
            umbrales_existentes=existentes,
            hoy=hoy,
            umbrales=umbrales,
        ):
            session.add(
                Renovacion(
                    tenant_id=tenant_id,
                    poliza_id=poliza.id,
                    umbral_dias=accion.umbral_dias,
                    fecha_objetivo=accion.fecha_objetivo,
                    estado=EstadoRenovacion.PENDIENTE,
                    asesor_id=poliza.asesor_id,
                    notas="Generada por recuperación de histórico." if accion.recuperada else None,
                )
            )
            resultado.acciones_creadas += 1

        nuevo_estado = estado_por_vencimiento(
            fecha_vencimiento=poliza.fecha_vencimiento, hoy=hoy, umbral_aviso=horizonte
        )
        if nuevo_estado is not poliza.estado:
            poliza.estado = nuevo_estado
            poliza.updated_at = datetime.now()
            resultado.polizas_actualizadas += 1

    await session.flush()
    log.info("barrido_renovaciones", tenant_id=str(tenant_id), resultado=str(resultado))
    return resultado
