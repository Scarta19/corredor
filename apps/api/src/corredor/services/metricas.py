"""Management indicators (Módulo 6).

§6 asks the question this module exists to answer: how many people ask for a
quote, how many are attended, how many receive a proposal, how many buy.

That is **cumulative reach**, not a snapshot. An opportunity sitting in
`GANADO` today passed through `CONTACTADO` and `COTIZANDO` on the way, and a
funnel built from current stages would count it once at the end and report
that nobody was ever contacted. Only `oportunidad_eventos` can answer it —
which is why every transition has been recorded since Módulo 2.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from corredor.domain.clientes import Cliente
from corredor.domain.comercial import Oportunidad, OportunidadEvento, Solicitud
from corredor.domain.enums import (
    EstadoPoliza,
    EstadoRenovacion,
    EtapaOportunidad,
    MotivoPerdida,
)
from corredor.domain.polizas import Poliza, Renovacion

#: The stages the funnel reports, in order. GANADO and PERDIDO are outcomes
#: rather than steps, and are counted separately.
ETAPAS_DEL_EMBUDO = [
    EtapaOportunidad.NUEVO,
    EtapaOportunidad.CONTACTADO,
    EtapaOportunidad.COTIZANDO,
    EtapaOportunidad.PROPUESTA_ENVIADA,
    EtapaOportunidad.EN_NEGOCIACION,
]


@dataclass(slots=True)
class PasoEmbudo:
    etapa: EtapaOportunidad
    #: Opportunities that reached this stage at any point in the period.
    alcanzadas: int
    #: Share of the first step that got this far.
    conversion_desde_inicio: float
    #: Share of the *previous* step that got this far — where the drop is.
    conversion_desde_anterior: float


def _rango(desde: date, hasta: date) -> tuple[datetime, datetime]:
    """A closed day range as timestamps, so the last day is included."""
    return datetime.combine(desde, time.min), datetime.combine(hasta, time.max)


async def embudo(
    session: AsyncSession, *, tenant_id: uuid.UUID, desde: date, hasta: date
) -> list[PasoEmbudo]:
    """How far opportunities created in the period got.

    Scoped by when the *opportunity* was created, not when the transition
    happened — otherwise a deal that closed this month but arrived last month
    would appear as a sale with no lead behind it, and conversion would read
    above 100%.
    """
    inicio, fin = _rango(desde, hasta)

    filas = await session.execute(
        select(
            OportunidadEvento.etapa_nueva,
            func.count(func.distinct(OportunidadEvento.oportunidad_id)),
        )
        .join(Oportunidad, Oportunidad.id == OportunidadEvento.oportunidad_id)
        .where(
            OportunidadEvento.tenant_id == tenant_id,
            Oportunidad.created_at.between(inicio, fin),
        )
        .group_by(OportunidadEvento.etapa_nueva)
    )
    alcanzadas: dict[EtapaOportunidad, int] = dict(filas.all())  # type: ignore[arg-type]

    pasos: list[PasoEmbudo] = []
    base = alcanzadas.get(ETAPAS_DEL_EMBUDO[0], 0)
    anterior = base
    for etapa in ETAPAS_DEL_EMBUDO:
        total = alcanzadas.get(etapa, 0)
        pasos.append(
            PasoEmbudo(
                etapa=etapa,
                alcanzadas=total,
                conversion_desde_inicio=(total / base) if base else 0.0,
                conversion_desde_anterior=(total / anterior) if anterior else 0.0,
            )
        )
        anterior = total or anterior
    return pasos


@dataclass(slots=True)
class IndicadoresComerciales:
    """§14 and §16: the numbers a manager reads first."""

    leads: int
    cotizaciones: int
    ventas: int
    perdidas: int
    conversion: float
    prima_ganada: Decimal


async def comerciales(
    session: AsyncSession, *, tenant_id: uuid.UUID, desde: date, hasta: date
) -> IndicadoresComerciales:
    inicio, fin = _rango(desde, hasta)

    async def contar_alcanzaron(etapa: EtapaOportunidad) -> int:
        return (
            await session.scalar(
                select(func.count(func.distinct(OportunidadEvento.oportunidad_id)))
                .join(Oportunidad, Oportunidad.id == OportunidadEvento.oportunidad_id)
                .where(
                    OportunidadEvento.tenant_id == tenant_id,
                    OportunidadEvento.etapa_nueva == etapa,
                    Oportunidad.created_at.between(inicio, fin),
                )
            )
        ) or 0

    leads = (
        await session.scalar(
            select(func.count())
            .select_from(Solicitud)
            .where(
                Solicitud.tenant_id == tenant_id,
                Solicitud.created_at.between(inicio, fin),
            )
        )
    ) or 0

    ventas = await contar_alcanzaron(EtapaOportunidad.GANADO)
    perdidas = await contar_alcanzaron(EtapaOportunidad.PERDIDO)
    cotizaciones = await contar_alcanzaron(EtapaOportunidad.COTIZANDO)

    prima = await session.scalar(
        select(func.coalesce(func.sum(Poliza.prima), 0)).where(
            Poliza.tenant_id == tenant_id,
            Poliza.created_at.between(inicio, fin),
        )
    )

    # Conversion is measured against *resolved* opportunities, not against all
    # leads. Counting still-open deals as failures understates a team that is
    # simply mid-cycle, and the number would drift every day without anyone
    # doing anything wrong.
    resueltas = ventas + perdidas
    return IndicadoresComerciales(
        leads=leads,
        cotizaciones=cotizaciones,
        ventas=ventas,
        perdidas=perdidas,
        conversion=(ventas / resueltas) if resueltas else 0.0,
        prima_ganada=Decimal(prima or 0),
    )


@dataclass(slots=True)
class IndicadoresClientes:
    nuevos: int
    activos: int
    recurrentes: int


async def clientes(
    session: AsyncSession, *, tenant_id: uuid.UUID, desde: date, hasta: date
) -> IndicadoresClientes:
    nuevos = (
        await session.scalar(
            select(func.count())
            .select_from(Cliente)
            .where(
                Cliente.tenant_id == tenant_id,
                Cliente.fecha_registro.between(desde, hasta),
            )
        )
    ) or 0

    vigentes = (EstadoPoliza.VIGENTE, EstadoPoliza.PROXIMA_A_VENCER)
    con_poliza = (
        select(Poliza.cliente_id, func.count().label("total"))
        .where(Poliza.tenant_id == tenant_id, Poliza.estado.in_(vigentes))
        .group_by(Poliza.cliente_id)
        .subquery()
    )

    activos = (await session.scalar(select(func.count()).select_from(con_poliza))) or 0
    # "Recurrente" is a client the brokerage has sold to more than once — the
    # §13 cross-sell target, and the population worth protecting.
    recurrentes = (
        await session.scalar(
            select(func.count()).select_from(con_poliza).where(con_poliza.c.total > 1)
        )
    ) or 0

    return IndicadoresClientes(nuevos=nuevos, activos=activos, recurrentes=recurrentes)


@dataclass(slots=True)
class IndicadoresPolizas:
    activas: int
    proximas_a_vencer: int
    vencidas: int
    renovaciones_completadas: int
    renovaciones_pendientes: int


async def polizas(session: AsyncSession, *, tenant_id: uuid.UUID) -> IndicadoresPolizas:
    async def contar_estado(estado: EstadoPoliza) -> int:
        return (
            await session.scalar(
                select(func.count())
                .select_from(Poliza)
                .where(Poliza.tenant_id == tenant_id, Poliza.estado == estado)
            )
        ) or 0

    async def contar_renovacion(estado: EstadoRenovacion) -> int:
        return (
            await session.scalar(
                select(func.count())
                .select_from(Renovacion)
                .where(Renovacion.tenant_id == tenant_id, Renovacion.estado == estado)
            )
        ) or 0

    return IndicadoresPolizas(
        activas=await contar_estado(EstadoPoliza.VIGENTE),
        proximas_a_vencer=await contar_estado(EstadoPoliza.PROXIMA_A_VENCER),
        vencidas=await contar_estado(EstadoPoliza.VENCIDA),
        renovaciones_completadas=await contar_renovacion(EstadoRenovacion.COMPLETADA),
        renovaciones_pendientes=await contar_renovacion(EstadoRenovacion.PENDIENTE),
    )


@dataclass(slots=True)
class MotivoConTotal:
    motivo: MotivoPerdida
    total: int


async def motivos_de_perdida(
    session: AsyncSession, *, tenant_id: uuid.UUID, desde: date, hasta: date
) -> list[MotivoConTotal]:
    """Why deals were lost.

    This is the question the mandatory loss motive was collected for. Without
    it a manager can see that conversion fell but not whether the problem is
    price or service — and those have opposite responses.
    """
    inicio, fin = _rango(desde, hasta)
    filas = await session.execute(
        select(Oportunidad.motivo_perdida, func.count())
        .where(
            Oportunidad.tenant_id == tenant_id,
            Oportunidad.etapa == EtapaOportunidad.PERDIDO,
            Oportunidad.motivo_perdida.isnot(None),
            Oportunidad.cerrada_en.between(inicio, fin),
        )
        .group_by(Oportunidad.motivo_perdida)
        .order_by(func.count().desc())
    )
    return [MotivoConTotal(motivo=m, total=t) for m, t in filas if m is not None]


def mes_actual(hoy: date | None = None) -> tuple[date, date]:
    hoy = hoy or date.today()
    primero = hoy.replace(day=1)
    siguiente = (primero + timedelta(days=32)).replace(day=1)
    return primero, siguiente - timedelta(days=1)
