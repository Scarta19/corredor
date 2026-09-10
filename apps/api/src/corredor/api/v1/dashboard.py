"""The management dashboard (Módulo 6).

§14 lists the indicators; §15 and §16 are the two views. Restricted to
managers and administrators — an advisor's job is the queue, not the scoreboard.
"""

from __future__ import annotations

from dataclasses import asdict
from datetime import date
from decimal import Decimal

from fastapi import APIRouter
from pydantic import BaseModel
from sqlalchemy import select

from corredor.api.deps import Gerencia, Sesion, TenantId
from corredor.domain.enums import (
    EstadoPoliza,
    EtapaOportunidad,
    MotivoPerdida,
    VentanaVencimiento,
)
from corredor.domain.polizas import Poliza
from corredor.services import metricas
from corredor.services.renovaciones import UMBRALES_POR_DEFECTO

router = APIRouter(prefix="/crm/dashboard", tags=["dashboard"])


class PasoEmbudo(BaseModel):
    etapa: EtapaOportunidad
    etiqueta: str
    alcanzadas: int
    conversion_desde_inicio: float
    conversion_desde_anterior: float


class Comercial(BaseModel):
    leads: int
    cotizaciones: int
    ventas: int
    perdidas: int
    conversion: float
    prima_ganada: Decimal


class Clientes(BaseModel):
    nuevos: int
    activos: int
    recurrentes: int


class Polizas(BaseModel):
    activas: int
    proximas_a_vencer: int
    vencidas: int
    renovaciones_completadas: int
    renovaciones_pendientes: int


class Motivo(BaseModel):
    motivo: MotivoPerdida
    etiqueta: str
    total: int


class VentanaConTotal(BaseModel):
    ventana: VentanaVencimiento
    etiqueta: str
    total: int


class Tablero(BaseModel):
    desde: date
    hasta: date
    umbrales_renovacion: list[int]
    comercial: Comercial
    clientes: Clientes
    polizas: Polizas
    embudo: list[PasoEmbudo]
    motivos_perdida: list[Motivo]
    ventanas_renovacion: list[VentanaConTotal]


ETIQUETAS_ETAPA = {
    EtapaOportunidad.NUEVO: "Recibidas",
    EtapaOportunidad.CONTACTADO: "Contactadas",
    EtapaOportunidad.COTIZANDO: "En cotización",
    EtapaOportunidad.PROPUESTA_ENVIADA: "Propuesta enviada",
    EtapaOportunidad.EN_NEGOCIACION: "En negociación",
}

ETIQUETAS_MOTIVO = {
    MotivoPerdida.PRECIO: "Precio",
    MotivoPerdida.COMPETENCIA: "Competencia",
    MotivoPerdida.SIN_RESPUESTA: "Sin respuesta",
    MotivoPerdida.NO_ASEGURABLE: "No asegurable",
    MotivoPerdida.DESISTE: "Desiste",
    MotivoPerdida.OTRO: "Otro",
}

ETIQUETAS_VENTANA = {
    VentanaVencimiento.VENCIDA: "Vencidas",
    VentanaVencimiento.CRITICA: "Menos de 7 días",
    VentanaVencimiento.URGENTE: "8 a 15 días",
    VentanaVencimiento.PROXIMA: "16 a 30 días",
    VentanaVencimiento.PLANIFICADA: "31 a 60 días",
    VentanaVencimiento.FUTURA: "Más de 60 días",
}

ORDEN_VENTANAS = [
    VentanaVencimiento.VENCIDA,
    VentanaVencimiento.CRITICA,
    VentanaVencimiento.URGENTE,
    VentanaVencimiento.PROXIMA,
    VentanaVencimiento.PLANIFICADA,
    VentanaVencimiento.FUTURA,
]


@router.get("", summary="Tablero gerencial")
async def tablero(
    session: Sesion,
    tenant_id: TenantId,
    _gerencia: Gerencia,
    desde: date | None = None,
    hasta: date | None = None,
) -> Tablero:
    """Everything §14 asks for, for one period.

    Defaults to the current month, which is the period §16 shows and the one a
    manager checks without being asked.
    """
    if desde is None or hasta is None:
        desde, hasta = metricas.mes_actual()

    comercial = await metricas.comerciales(session, tenant_id=tenant_id, desde=desde, hasta=hasta)
    pasos = await metricas.embudo(session, tenant_id=tenant_id, desde=desde, hasta=hasta)
    datos_clientes = await metricas.clientes(session, tenant_id=tenant_id, desde=desde, hasta=hasta)
    datos_polizas = await metricas.polizas(session, tenant_id=tenant_id)
    motivos = await metricas.motivos_de_perdida(
        session, tenant_id=tenant_id, desde=desde, hasta=hasta
    )

    # §15's distribution counts every policy the brokerage could still act on.
    # Renewed and cancelled ones are settled and would only inflate the chart.
    hoy = date.today()
    vivas = (
        await session.scalars(
            select(Poliza).where(
                Poliza.tenant_id == tenant_id,
                Poliza.estado.in_(
                    (
                        EstadoPoliza.VIGENTE,
                        EstadoPoliza.PROXIMA_A_VENCER,
                        EstadoPoliza.VENCIDA,
                    )
                ),
            )
        )
    ).all()
    conteo_ventanas = dict.fromkeys(ORDEN_VENTANAS, 0)
    for poliza in vivas:
        conteo_ventanas[poliza.ventana(hoy)] += 1

    return Tablero(
        desde=desde,
        hasta=hasta,
        umbrales_renovacion=list(UMBRALES_POR_DEFECTO),
        comercial=Comercial(**asdict(comercial)),
        clientes=Clientes(**asdict(datos_clientes)),
        polizas=Polizas(**asdict(datos_polizas)),
        embudo=[
            PasoEmbudo(
                etapa=p.etapa,
                etiqueta=ETIQUETAS_ETAPA[p.etapa],
                alcanzadas=p.alcanzadas,
                conversion_desde_inicio=p.conversion_desde_inicio,
                conversion_desde_anterior=p.conversion_desde_anterior,
            )
            for p in pasos
        ],
        motivos_perdida=[
            Motivo(motivo=m.motivo, etiqueta=ETIQUETAS_MOTIVO[m.motivo], total=m.total)
            for m in motivos
        ],
        ventanas_renovacion=[
            VentanaConTotal(ventana=v, etiqueta=ETIQUETAS_VENTANA[v], total=conteo_ventanas[v])
            for v in ORDEN_VENTANAS
        ],
    )
