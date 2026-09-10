"""Scoring the risk that a policy will not be renewed (Módulo 5 + §13 data).

Days-to-expiry is a calendar. This is what turns it into a work queue: a
policy expiring in 45 days whose premium jumped 30%, whose owner has not been
contacted in a year, is a more urgent call than one expiring in 10 days that
has renewed three times without friction.
"""

from __future__ import annotations

import uuid
from datetime import UTC, date, datetime

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from corredor.core.logging import get_logger
from corredor.domain.comunicaciones import Comunicacion
from corredor.domain.enums import EstadoPoliza, NivelRiesgo
from corredor.domain.inteligencia import RiesgoRenovacion
from corredor.domain.polizas import Poliza
from corredor_ml.renovacion import (
    RenovacionFeatures,
    RiesgoRenovacionBaseline,
    clasificar_nivel,
)

log = get_logger(__name__)

_modelo = RiesgoRenovacionBaseline()


async def construir_features(
    session: AsyncSession, *, poliza: Poliza, hoy: date
) -> RenovacionFeatures:
    """Assemble what the model needs, from what the platform actually knows.

    Everything here is derived from records the brokerage already keeps. No
    feature depends on data somebody would have to start entering by hand,
    because a model that needs new manual work does not get used.
    """
    renovaciones_previas = await _contar_cadena(session, poliza)

    antiguedad = await session.scalar(
        select(func.min(Poliza.fecha_inicio)).where(Poliza.cliente_id == poliza.cliente_id)
    )
    meses = 0
    if antiguedad is not None:
        meses = max(0, (hoy.year - antiguedad.year) * 12 + hoy.month - antiguedad.month)

    otras = (
        await session.scalar(
            select(func.count())
            .select_from(Poliza)
            .where(
                Poliza.cliente_id == poliza.cliente_id,
                Poliza.id != poliza.id,
                Poliza.estado.in_((EstadoPoliza.VIGENTE, EstadoPoliza.PROXIMA_A_VENCER)),
            )
        )
    ) or 0

    ultimo_contacto = await session.scalar(
        select(func.max(Comunicacion.created_at)).where(
            Comunicacion.cliente_id == poliza.cliente_id
        )
    )
    dias_sin_contacto = (hoy - ultimo_contacto.date()).days if ultimo_contacto is not None else None

    variacion = 0.0
    if poliza.poliza_anterior_id is not None:
        anterior = await session.get(Poliza, poliza.poliza_anterior_id)
        if anterior is not None and anterior.prima:
            variacion = float((poliza.prima - anterior.prima) / anterior.prima)

    return RenovacionFeatures(
        dias_para_vencimiento=poliza.dias_para_vencimiento(hoy),
        renovaciones_previas=renovaciones_previas,
        antiguedad_cliente_meses=meses,
        variacion_prima=variacion,
        # Claims are not tracked yet — the siniestros module is future work
        # (§19). Passing zero is honest: the model simply has one fewer signal.
        siniestros_ultimo_periodo=0,
        dias_desde_ultimo_contacto=dias_sin_contacto,
        otras_polizas_vigentes=otras,
    )


async def _contar_cadena(session: AsyncSession, poliza: Poliza) -> int:
    """How many times this policy has already been renewed with us.

    Walks `poliza_anterior_id` backwards. The chain is short by construction —
    one link per year — and bounded so a cycle from bad data cannot hang the
    sweep.
    """
    previas = 0
    actual = poliza.poliza_anterior_id
    vistas: set[uuid.UUID] = {poliza.id}
    while actual is not None and previas < 20 and actual not in vistas:
        vistas.add(actual)
        anterior = await session.get(Poliza, actual)
        if anterior is None:
            break
        previas += 1
        actual = anterior.poliza_anterior_id
    return previas


async def calcular_riesgo(
    session: AsyncSession, *, poliza: Poliza, hoy: date | None = None
) -> RiesgoRenovacion:
    """Score one policy and store the result with its provenance."""
    hoy = hoy or date.today()
    features = await construir_features(session, poliza=poliza, hoy=hoy)
    prediccion = _modelo.predecir(features)

    riesgo = RiesgoRenovacion(
        tenant_id=poliza.tenant_id,
        poliza_id=poliza.id,
        probabilidad_fuga=prediccion.puntaje,
        nivel=NivelRiesgo(clasificar_nivel(prediccion.puntaje)),
        explicacion=[c.model_dump() for c in prediccion.explicacion],
        modelo=prediccion.modelo,
        modelo_version=prediccion.modelo_version,
        features=features.model_dump(),
        calculado_en=datetime.now(UTC).replace(tzinfo=None),
    )
    session.add(riesgo)
    return riesgo
