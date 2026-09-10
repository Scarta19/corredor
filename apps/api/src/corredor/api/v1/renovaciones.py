"""Renewals (Módulo 5) and the §15 dashboard view.

§15 asks for one screen where a manager can see, at a glance, where the risk
of losing business is. That is the bucket view: policies grouped by how long
they have left, with churn risk beside each one so that "expires soonest" and
"most likely to be lost" can be told apart.
"""

from __future__ import annotations

import uuid
from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import Annotated

from fastapi import APIRouter, Query
from pydantic import BaseModel, ConfigDict
from sqlalchemy import func, select
from sqlalchemy.orm import selectinload

from corredor.api.deps import Sesion, TenantId, UsuarioActual
from corredor.core.errors import NoEncontrado
from corredor.domain.enums import (
    EstadoPoliza,
    EstadoRenovacion,
    NivelRiesgo,
    VentanaVencimiento,
)
from corredor.domain.inteligencia import RiesgoRenovacion
from corredor.domain.polizas import Poliza, Renovacion
from corredor.services.renovaciones import UMBRALES_POR_DEFECTO

router = APIRouter(prefix="/crm/renovaciones", tags=["renovaciones"])


class PolizaPorVencer(BaseModel):
    id: uuid.UUID
    numero: str
    cliente_id: uuid.UUID
    cliente: str
    telefono: str | None
    ramo: str
    aseguradora: str
    prima: Decimal
    fecha_vencimiento: date
    dias_para_vencimiento: int
    ventana: VentanaVencimiento
    asesor: str | None
    riesgo: float | None
    nivel_riesgo: NivelRiesgo | None
    #: Renewal actions already scheduled, and how many are still open.
    acciones_pendientes: int


class Bucket(BaseModel):
    ventana: VentanaVencimiento
    etiqueta: str
    total: int
    prima_total: Decimal
    polizas: list[PolizaPorVencer]


ETIQUETAS = {
    VentanaVencimiento.VENCIDA: "Vencidas",
    VentanaVencimiento.CRITICA: "Vencen en menos de 7 días",
    VentanaVencimiento.URGENTE: "Vencen entre 8 y 15 días",
    VentanaVencimiento.PROXIMA: "Vencen entre 16 y 30 días",
    VentanaVencimiento.PLANIFICADA: "Vencen entre 31 y 60 días",
    VentanaVencimiento.FUTURA: "Más de 60 días",
}

#: The order a manager reads them in: most urgent first.
ORDEN = [
    VentanaVencimiento.VENCIDA,
    VentanaVencimiento.CRITICA,
    VentanaVencimiento.URGENTE,
    VentanaVencimiento.PROXIMA,
    VentanaVencimiento.PLANIFICADA,
    VentanaVencimiento.FUTURA,
]


@router.get("", summary="Tablero de renovaciones por ventana de vencimiento")
async def tablero(
    session: Sesion,
    tenant_id: TenantId,
    asesor_id: uuid.UUID | None = None,
    horizonte_dias: Annotated[int, Query(ge=1, le=400)] = 90,
) -> list[Bucket]:
    """Policies grouped into the §15 buckets.

    Expired policies are included rather than hidden: a lapsed policy is
    usually still recoverable, and a dashboard that quietly drops them is how
    a book of business leaks.
    """
    hoy = date.today()
    consulta = (
        select(Poliza)
        .where(
            Poliza.tenant_id == tenant_id,
            Poliza.estado.in_(
                (
                    EstadoPoliza.VIGENTE,
                    EstadoPoliza.PROXIMA_A_VENCER,
                    EstadoPoliza.VENCIDA,
                )
            ),
            Poliza.fecha_vencimiento <= hoy + timedelta(days=horizonte_dias),
        )
        .options(
            selectinload(Poliza.cliente),
            selectinload(Poliza.ramo),
            selectinload(Poliza.aseguradora),
            selectinload(Poliza.asesor),
        )
        .order_by(Poliza.fecha_vencimiento)
    )
    if asesor_id is not None:
        consulta = consulta.where(Poliza.asesor_id == asesor_id)
    polizas = (await session.scalars(consulta)).all()

    riesgos = await _riesgos_mas_recientes(session, [p.id for p in polizas])
    pendientes = await _acciones_pendientes(session, [p.id for p in polizas])

    filas = [
        PolizaPorVencer(
            id=p.id,
            numero=p.numero,
            cliente_id=p.cliente_id,
            cliente=p.cliente.nombre,
            telefono=p.cliente.telefono,
            ramo=p.ramo.nombre,
            aseguradora=p.aseguradora.nombre,
            prima=p.prima,
            fecha_vencimiento=p.fecha_vencimiento,
            dias_para_vencimiento=p.dias_para_vencimiento(hoy),
            ventana=p.ventana(hoy),
            asesor=p.asesor.nombre if p.asesor else None,
            riesgo=riesgos[p.id].probabilidad_fuga if p.id in riesgos else None,
            nivel_riesgo=riesgos[p.id].nivel if p.id in riesgos else None,
            acciones_pendientes=pendientes.get(p.id, 0),
        )
        for p in polizas
    ]

    buckets: list[Bucket] = []
    for ventana in ORDEN:
        de_la_ventana = [f for f in filas if f.ventana is ventana]
        if not de_la_ventana and ventana is VentanaVencimiento.FUTURA:
            continue
        # Within a bucket, the riskiest first — that is the whole reason for
        # scoring them. Days-to-expiry already decided the bucket.
        de_la_ventana.sort(key=lambda f: (f.riesgo is not None, f.riesgo or 0), reverse=True)
        buckets.append(
            Bucket(
                ventana=ventana,
                etiqueta=ETIQUETAS[ventana],
                total=len(de_la_ventana),
                prima_total=sum((f.prima for f in de_la_ventana), Decimal(0)),
                polizas=de_la_ventana,
            )
        )
    return buckets


async def _riesgos_mas_recientes(
    session: Sesion, ids: list[uuid.UUID]
) -> dict[uuid.UUID, RiesgoRenovacion]:
    """The latest score per policy, in one query rather than one per row."""
    if not ids:
        return {}
    ultimos: dict[uuid.UUID, RiesgoRenovacion] = {}
    for riesgo in await session.scalars(
        select(RiesgoRenovacion)
        .where(RiesgoRenovacion.poliza_id.in_(ids))
        .order_by(RiesgoRenovacion.calculado_en.desc())
    ):
        ultimos.setdefault(riesgo.poliza_id, riesgo)
    return ultimos


async def _acciones_pendientes(session: Sesion, ids: list[uuid.UUID]) -> dict[uuid.UUID, int]:
    if not ids:
        return {}
    filas = await session.execute(
        select(Renovacion.poliza_id, func.count())
        .where(
            Renovacion.poliza_id.in_(ids),
            Renovacion.estado.in_((EstadoRenovacion.PENDIENTE, EstadoRenovacion.EN_GESTION)),
        )
        .group_by(Renovacion.poliza_id)
    )
    return dict(filas.all())  # type: ignore[arg-type]


class AccionRenovacion(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    umbral_dias: int
    fecha_objetivo: date
    estado: EstadoRenovacion
    notas: str | None
    completada_en: datetime | None


@router.get("/poliza/{poliza_id}", summary="Acciones de renovación de una póliza")
async def acciones_de_poliza(
    poliza_id: uuid.UUID, session: Sesion, tenant_id: TenantId
) -> list[AccionRenovacion]:
    acciones = (
        await session.scalars(
            select(Renovacion)
            .where(Renovacion.poliza_id == poliza_id, Renovacion.tenant_id == tenant_id)
            .order_by(Renovacion.umbral_dias.desc())
        )
    ).all()
    return [AccionRenovacion.model_validate(a) for a in acciones]


class CambioAccion(BaseModel):
    model_config = ConfigDict(extra="forbid")

    estado: EstadoRenovacion
    notas: str | None = None


@router.patch("/{renovacion_id}", summary="Actualizar una acción de renovación")
async def actualizar_accion(
    renovacion_id: uuid.UUID,
    cambio: CambioAccion,
    session: Sesion,
    tenant_id: TenantId,
    usuario: UsuarioActual,
) -> AccionRenovacion:
    accion = await session.scalar(
        select(Renovacion).where(Renovacion.id == renovacion_id, Renovacion.tenant_id == tenant_id)
    )
    if accion is None:
        raise NoEncontrado("Esa acción de renovación no existe en esta agencia.")

    accion.estado = cambio.estado
    if cambio.notas is not None:
        accion.notas = cambio.notas
    # Whoever closes an action owns it, so the queue reflects who actually did
    # the work rather than who was assigned when it was created.
    if cambio.estado is EstadoRenovacion.COMPLETADA:
        accion.completada_en = datetime.now()
        accion.asesor_id = accion.asesor_id or usuario.id
    else:
        accion.completada_en = None

    await session.flush()
    return AccionRenovacion.model_validate(accion)


class ResumenRenovaciones(BaseModel):
    umbrales: list[int]
    pendientes: int
    en_gestion: int
    completadas: int
    prima_en_riesgo: Decimal


@router.get("/resumen", summary="Cifras del módulo de renovaciones")
async def resumen(session: Sesion, tenant_id: TenantId) -> ResumenRenovaciones:
    async def contar(estado: EstadoRenovacion) -> int:
        return (
            await session.scalar(
                select(func.count())
                .select_from(Renovacion)
                .where(Renovacion.tenant_id == tenant_id, Renovacion.estado == estado)
            )
        ) or 0

    hoy = date.today()
    prima = await session.scalar(
        select(func.coalesce(func.sum(Poliza.prima), 0)).where(
            Poliza.tenant_id == tenant_id,
            Poliza.estado.in_((EstadoPoliza.VIGENTE, EstadoPoliza.PROXIMA_A_VENCER)),
            Poliza.fecha_vencimiento.between(hoy, hoy + timedelta(days=60)),
        )
    )

    return ResumenRenovaciones(
        umbrales=list(UMBRALES_POR_DEFECTO),
        pendientes=await contar(EstadoRenovacion.PENDIENTE),
        en_gestion=await contar(EstadoRenovacion.EN_GESTION),
        completadas=await contar(EstadoRenovacion.COMPLETADA),
        prima_en_riesgo=Decimal(prima or 0),
    )
