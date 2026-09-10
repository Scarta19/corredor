"""Moving an opportunity through the pipeline (Módulo 4, §10).

Every transition is recorded rather than merely applied. The funnel in Módulo
6 — how many requests are attended, how many receive a proposal, how many
close — is derived entirely from `oportunidad_eventos`, so a stage change that
skips the event log is a hole in next month's reporting.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy.ext.asyncio import AsyncSession

from corredor.core.errors import ReglaDeNegocio
from corredor.core.logging import get_logger
from corredor.domain.comercial import Oportunidad, OportunidadEvento, Solicitud
from corredor.domain.enums import EstadoSolicitud, EtapaOportunidad, MotivoPerdida
from corredor.domain.tenancy import Usuario

log = get_logger(__name__)


async def cambiar_etapa(
    session: AsyncSession,
    *,
    oportunidad: Oportunidad,
    etapa_nueva: EtapaOportunidad,
    usuario: Usuario,
    motivo_perdida: MotivoPerdida | None = None,
    nota: str | None = None,
) -> Oportunidad:
    """Move an opportunity, recording what happened and why.

    Two rules are enforced, and no others:

    - Losing requires a reason. "Perdido" with no motive is the single most
      expensive gap in a brokerage's data: without it there is no way to tell
      a pricing problem from a service problem, which is exactly the question
      the pipeline exists to answer.
    - A stage change to where it already is does nothing, silently. Advisors
      double-click.

    Moving *backwards* is deliberately allowed. Deals genuinely regress — a
    client stops answering after a proposal — and a system that forbids it
    just teaches people to record something false.
    """
    if etapa_nueva is oportunidad.etapa:
        return oportunidad

    if etapa_nueva is EtapaOportunidad.PERDIDO and motivo_perdida is None:
        raise ReglaDeNegocio("Para marcar una oportunidad como perdida hay que indicar el motivo.")

    etapa_anterior = oportunidad.etapa
    oportunidad.etapa = etapa_nueva
    oportunidad.motivo_perdida = motivo_perdida if etapa_nueva is EtapaOportunidad.PERDIDO else None
    oportunidad.cerrada_en = (
        datetime.now(UTC).replace(tzinfo=None) if etapa_nueva.es_terminal else None
    )

    session.add(
        OportunidadEvento(
            tenant_id=oportunidad.tenant_id,
            oportunidad_id=oportunidad.id,
            etapa_anterior=etapa_anterior,
            etapa_nueva=etapa_nueva,
            usuario_id=usuario.id,
            automatico=False,
            nota=nota,
        )
    )

    # The originating request follows the opportunity out of the queue, so an
    # advisor working the list is not shown work they have already started.
    if oportunidad.solicitud_id is not None:
        solicitud = await session.get(Solicitud, oportunidad.solicitud_id)
        if solicitud is not None:
            solicitud.estado = _estado_de_solicitud(etapa_nueva, solicitud.estado)

    await session.flush()
    log.info(
        "oportunidad_movida",
        oportunidad=str(oportunidad.id),
        de=etapa_anterior.value,
        a=etapa_nueva.value,
        usuario=str(usuario.id),
    )
    return oportunidad


def _estado_de_solicitud(etapa: EtapaOportunidad, actual: EstadoSolicitud) -> EstadoSolicitud:
    if etapa is EtapaOportunidad.GANADO:
        return EstadoSolicitud.CONVERTIDA
    if etapa is EtapaOportunidad.PERDIDO:
        return EstadoSolicitud.DESCARTADA
    if etapa is EtapaOportunidad.NUEVO:
        return actual
    return EstadoSolicitud.EN_PROCESO


async def asignar_asesor(
    session: AsyncSession,
    *,
    oportunidad: Oportunidad,
    asesor_id: uuid.UUID | None,
    usuario: Usuario,
) -> Oportunidad:
    """Assign or unassign the advisor responsible for an opportunity.

    The assignment also lands on the originating request and, when the client
    had none, on the client — so "who is responsible for this person" has one
    answer rather than three.
    """
    if oportunidad.asesor_id == asesor_id:
        return oportunidad

    oportunidad.asesor_id = asesor_id

    if oportunidad.solicitud_id is not None:
        solicitud = await session.get(Solicitud, oportunidad.solicitud_id)
        if solicitud is not None:
            solicitud.asesor_id = asesor_id
            solicitud.asignada_en = datetime.now(UTC).replace(tzinfo=None)
            if solicitud.estado is EstadoSolicitud.NUEVA and asesor_id is not None:
                solicitud.estado = EstadoSolicitud.ASIGNADA

    if asesor_id is not None and oportunidad.cliente is not None:
        oportunidad.cliente.asesor_id = oportunidad.cliente.asesor_id or asesor_id

    session.add(
        OportunidadEvento(
            tenant_id=oportunidad.tenant_id,
            oportunidad_id=oportunidad.id,
            etapa_anterior=oportunidad.etapa,
            etapa_nueva=oportunidad.etapa,
            usuario_id=usuario.id,
            automatico=False,
            nota=("Asignada a un asesor." if asesor_id else "Asignación retirada."),
        )
    )
    await session.flush()
    return oportunidad
