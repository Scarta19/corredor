"""The CRM (Módulo 4).

§9 asks for one place where an advisor sees everything about a client without
hunting through files, chats and spreadsheets. That is what the client detail
endpoint is; the rest of this module is the work queue and the pipeline board
that decide what an advisor looks at first.

Every query here is scoped by the tenant taken from the caller's token. There
is no code path that accepts a tenant from the request body or a header.
"""

from __future__ import annotations

import uuid
from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import Annotated, Any

from fastapi import APIRouter, Query
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import Select, func, or_, select
from sqlalchemy.orm import selectinload

from corredor.api.deps import Sesion, TenantId, UsuarioActual
from corredor.core.errors import NoEncontrado
from corredor.domain.clientes import Cliente
from corredor.domain.comercial import Oportunidad, OportunidadEvento, Solicitud
from corredor.domain.comunicaciones import Comunicacion
from corredor.domain.enums import (
    Canal,
    EstadoPoliza,
    EstadoSolicitud,
    EtapaOportunidad,
    MotivoPerdida,
    NivelRiesgo,
    TipoCliente,
    VentanaVencimiento,
)
from corredor.domain.inteligencia import PuntajeLead
from corredor.domain.polizas import Poliza
from corredor.domain.tenancy import Usuario
from corredor.services.oportunidades import asignar_asesor, cambiar_etapa

router = APIRouter(prefix="/crm", tags=["CRM"])


# --- Shared shapes ----------------------------------------------------------


class Pagina[T](BaseModel):
    """A page of results, with enough to render a pager."""

    total: int
    limite: int
    desplazamiento: int
    elementos: list[T]


class Referencia(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    nombre: str


async def _paginar[T](
    session: Sesion, consulta: Select[tuple[T]], limite: int, desplazamiento: int
) -> tuple[int, list[T]]:
    total = await session.scalar(
        select(func.count()).select_from(consulta.order_by(None).subquery())
    )
    filas = (await session.scalars(consulta.limit(limite).offset(desplazamiento))).all()
    return total or 0, list(filas)


# --- Overview ---------------------------------------------------------------


class Resumen(BaseModel):
    solicitudes_nuevas: int
    oportunidades_abiertas: int
    clientes: int
    polizas_vigentes: int
    renovaciones_60_dias: int


@router.get("/resumen", summary="Cifras de cabecera del CRM")
async def resumen(session: Sesion, tenant_id: TenantId) -> Resumen:
    async def contar(consulta: Select[tuple[Any]]) -> int:
        total = await session.scalar(select(func.count()).select_from(consulta.subquery()))
        return total or 0

    hoy = date.today()
    en_sesenta_dias = hoy + timedelta(days=60)
    vigentes = (EstadoPoliza.VIGENTE, EstadoPoliza.PROXIMA_A_VENCER)

    return Resumen(
        solicitudes_nuevas=await contar(
            select(Solicitud.id).where(
                Solicitud.tenant_id == tenant_id,
                Solicitud.estado == EstadoSolicitud.NUEVA,
            )
        ),
        oportunidades_abiertas=await contar(
            select(Oportunidad.id).where(
                Oportunidad.tenant_id == tenant_id,
                Oportunidad.etapa.notin_((EtapaOportunidad.GANADO, EtapaOportunidad.PERDIDO)),
            )
        ),
        clientes=await contar(select(Cliente.id).where(Cliente.tenant_id == tenant_id)),
        polizas_vigentes=await contar(
            select(Poliza.id).where(Poliza.tenant_id == tenant_id, Poliza.estado.in_(vigentes))
        ),
        renovaciones_60_dias=await contar(
            select(Poliza.id).where(
                Poliza.tenant_id == tenant_id,
                Poliza.estado.in_(vigentes),
                Poliza.fecha_vencimiento.between(hoy, en_sesenta_dias),
            )
        ),
    )


# --- Advisors ---------------------------------------------------------------


@router.get("/asesores", summary="Asesores de la agencia")
async def listar_asesores(session: Sesion, tenant_id: TenantId) -> list[Referencia]:
    usuarios = (
        await session.scalars(
            select(Usuario)
            .where(Usuario.tenant_id == tenant_id, Usuario.activo.is_(True))
            .order_by(Usuario.nombre)
        )
    ).all()
    return [Referencia(id=u.id, nombre=u.nombre) for u in usuarios]


# --- Request queue ----------------------------------------------------------


class SolicitudEnCola(BaseModel):
    id: uuid.UUID
    codigo: str
    creada_en: datetime
    estado: EstadoSolicitud
    canal: Canal
    ramo: str
    cliente: Referencia
    telefono: str | None
    asesor: Referencia | None
    puntaje: float | None
    nivel: NivelRiesgo | None
    oportunidad_id: uuid.UUID | None


@router.get("/solicitudes", summary="Cola de solicitudes")
async def cola_de_solicitudes(
    session: Sesion,
    tenant_id: TenantId,
    estado: EstadoSolicitud | None = None,
    asesor_id: uuid.UUID | None = None,
    sin_asignar: bool = False,
    limite: Annotated[int, Query(ge=1, le=100)] = 25,
    desplazamiento: Annotated[int, Query(ge=0)] = 0,
) -> Pagina[SolicitudEnCola]:
    """Requests, ordered by how likely they are to close.

    With 127 leads in a month and a team of three, the question is never who
    to call but who *first*. The lead score answers it, and the ordering is
    the only place in the platform where a model decides anything on its own —
    it changes the order of a list, never the content of a record.
    """
    consulta = (
        select(Solicitud)
        .where(Solicitud.tenant_id == tenant_id)
        .options(
            selectinload(Solicitud.cliente),
            selectinload(Solicitud.ramo),
            selectinload(Solicitud.asesor),
            selectinload(Solicitud.oportunidad),
        )
        .order_by(Solicitud.created_at.desc())
    )
    if estado is not None:
        consulta = consulta.where(Solicitud.estado == estado)
    if asesor_id is not None:
        consulta = consulta.where(Solicitud.asesor_id == asesor_id)
    if sin_asignar:
        consulta = consulta.where(Solicitud.asesor_id.is_(None))

    total, solicitudes = await _paginar(session, consulta, limite, desplazamiento)

    # One query for the scores of this page, rather than one per row.
    ids = [s.oportunidad.id for s in solicitudes if s.oportunidad is not None]
    puntajes: dict[uuid.UUID, PuntajeLead] = {}
    if ids:
        for puntaje in await session.scalars(
            select(PuntajeLead)
            .where(PuntajeLead.oportunidad_id.in_(ids))
            .order_by(PuntajeLead.calculado_en.desc())
        ):
            puntajes.setdefault(puntaje.oportunidad_id, puntaje)

    elementos = [
        SolicitudEnCola(
            id=s.id,
            codigo=s.codigo,
            creada_en=s.created_at,
            estado=s.estado,
            canal=s.canal,
            ramo=s.ramo.nombre,
            cliente=Referencia(id=s.cliente.id, nombre=s.cliente.nombre),
            telefono=s.cliente.telefono,
            asesor=(Referencia(id=s.asesor.id, nombre=s.asesor.nombre) if s.asesor else None),
            puntaje=(
                puntajes[s.oportunidad.id].puntaje
                if s.oportunidad and s.oportunidad.id in puntajes
                else None
            ),
            nivel=(
                puntajes[s.oportunidad.id].nivel
                if s.oportunidad and s.oportunidad.id in puntajes
                else None
            ),
            oportunidad_id=s.oportunidad.id if s.oportunidad else None,
        )
        for s in solicitudes
    ]
    # Highest-scoring first, then most recent. Unscored requests sort last
    # rather than first: an absent score is not evidence of a good lead.
    elementos.sort(key=lambda e: (e.puntaje is not None, e.puntaje or 0), reverse=True)
    return Pagina(total=total, limite=limite, desplazamiento=desplazamiento, elementos=elementos)


# --- Clients ----------------------------------------------------------------


class ClienteEnLista(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    nombre: str
    tipo: TipoCliente
    documento: str | None
    telefono: str | None
    email: str | None
    ciudad: str | None
    origen: Canal
    fecha_registro: date


@router.get("/clientes", summary="Clientes de la agencia")
async def listar_clientes(
    session: Sesion,
    tenant_id: TenantId,
    q: Annotated[str | None, Query(description="Nombre, documento, teléfono o correo")] = None,
    tipo: TipoCliente | None = None,
    limite: Annotated[int, Query(ge=1, le=100)] = 25,
    desplazamiento: Annotated[int, Query(ge=0)] = 0,
) -> Pagina[ClienteEnLista]:
    consulta = select(Cliente).where(Cliente.tenant_id == tenant_id).order_by(Cliente.nombre)
    if tipo is not None:
        consulta = consulta.where(Cliente.tipo == tipo)
    if q:
        # Advisors search with whatever they have to hand: half a name, the
        # phone number that just called, a document from a form.
        patron = f"%{q.strip().lower()}%"
        consulta = consulta.where(
            or_(
                func.lower(Cliente.nombre).like(patron),
                Cliente.documento.like(patron),
                Cliente.telefono.like(patron),
                func.lower(Cliente.email).like(patron),
            )
        )
    total, clientes = await _paginar(session, consulta, limite, desplazamiento)
    return Pagina(
        total=total,
        limite=limite,
        desplazamiento=desplazamiento,
        elementos=[ClienteEnLista.model_validate(c) for c in clientes],
    )


class PolizaResumen(BaseModel):
    id: uuid.UUID
    numero: str
    ramo: str
    aseguradora: str
    fecha_vencimiento: date
    dias_para_vencimiento: int
    ventana: VentanaVencimiento
    prima: Decimal
    estado: EstadoPoliza


class OportunidadResumen(BaseModel):
    id: uuid.UUID
    ramo: str
    etapa: EtapaOportunidad
    creada_en: datetime
    asesor: Referencia | None
    puntaje: float | None


class ComunicacionResumen(BaseModel):
    id: uuid.UUID
    canal: Canal
    direccion: str
    contenido: str
    creada_en: datetime
    automatico: bool


class ClienteDetalle(ClienteEnLista):
    """§9's single view: everything about one client, in one response."""

    asesor: Referencia | None
    notas: str | None
    solicitudes: list[SolicitudEnCola]
    oportunidades: list[OportunidadResumen]
    polizas: list[PolizaResumen]
    comunicaciones: list[ComunicacionResumen]


@router.get("/clientes/{cliente_id}", summary="Ficha completa de un cliente")
async def obtener_cliente(
    cliente_id: uuid.UUID, session: Sesion, tenant_id: TenantId
) -> ClienteDetalle:
    cliente = await session.scalar(
        select(Cliente)
        .where(Cliente.id == cliente_id, Cliente.tenant_id == tenant_id)
        .options(selectinload(Cliente.asesor))
    )
    if cliente is None:
        raise NoEncontrado("Ese cliente no existe en esta agencia.")

    solicitudes = (
        await session.scalars(
            select(Solicitud)
            .where(Solicitud.cliente_id == cliente.id)
            .options(
                selectinload(Solicitud.ramo),
                selectinload(Solicitud.asesor),
                selectinload(Solicitud.oportunidad),
                selectinload(Solicitud.cliente),
            )
            .order_by(Solicitud.created_at.desc())
        )
    ).all()

    oportunidades = (
        await session.scalars(
            select(Oportunidad)
            .where(Oportunidad.cliente_id == cliente.id)
            .options(selectinload(Oportunidad.ramo), selectinload(Oportunidad.asesor))
            .order_by(Oportunidad.created_at.desc())
        )
    ).all()

    puntajes: dict[uuid.UUID, float] = {}
    if oportunidades:
        for p in await session.scalars(
            select(PuntajeLead)
            .where(PuntajeLead.oportunidad_id.in_([o.id for o in oportunidades]))
            .order_by(PuntajeLead.calculado_en.desc())
        ):
            puntajes.setdefault(p.oportunidad_id, p.puntaje)

    polizas = (
        await session.scalars(
            select(Poliza)
            .where(Poliza.cliente_id == cliente.id)
            .options(selectinload(Poliza.ramo), selectinload(Poliza.aseguradora))
            .order_by(Poliza.fecha_vencimiento)
        )
    ).all()

    comunicaciones = (
        await session.scalars(
            select(Comunicacion)
            .where(Comunicacion.cliente_id == cliente.id)
            .order_by(Comunicacion.created_at.desc())
            .limit(50)
        )
    ).all()

    hoy = date.today()
    return ClienteDetalle(
        **ClienteEnLista.model_validate(cliente).model_dump(),
        asesor=(
            Referencia(id=cliente.asesor.id, nombre=cliente.asesor.nombre)
            if cliente.asesor
            else None
        ),
        notas=cliente.notas,
        solicitudes=[
            SolicitudEnCola(
                id=s.id,
                codigo=s.codigo,
                creada_en=s.created_at,
                estado=s.estado,
                canal=s.canal,
                ramo=s.ramo.nombre,
                cliente=Referencia(id=cliente.id, nombre=cliente.nombre),
                telefono=cliente.telefono,
                asesor=(Referencia(id=s.asesor.id, nombre=s.asesor.nombre) if s.asesor else None),
                puntaje=puntajes.get(s.oportunidad.id) if s.oportunidad else None,
                nivel=None,
                oportunidad_id=s.oportunidad.id if s.oportunidad else None,
            )
            for s in solicitudes
        ],
        oportunidades=[
            OportunidadResumen(
                id=o.id,
                ramo=o.ramo.nombre,
                etapa=o.etapa,
                creada_en=o.created_at,
                asesor=(Referencia(id=o.asesor.id, nombre=o.asesor.nombre) if o.asesor else None),
                puntaje=puntajes.get(o.id),
            )
            for o in oportunidades
        ],
        polizas=[
            PolizaResumen(
                id=p.id,
                numero=p.numero,
                ramo=p.ramo.nombre,
                aseguradora=p.aseguradora.nombre,
                fecha_vencimiento=p.fecha_vencimiento,
                dias_para_vencimiento=p.dias_para_vencimiento(hoy),
                ventana=p.ventana(hoy),
                prima=p.prima,
                estado=p.estado,
            )
            for p in polizas
        ],
        comunicaciones=[
            ComunicacionResumen(
                id=c.id,
                canal=c.canal,
                direccion=c.direccion.value,
                contenido=c.contenido,
                creada_en=c.created_at,
                automatico=c.automatico,
            )
            for c in comunicaciones
        ],
    )


# --- Pipeline ---------------------------------------------------------------


class ColumnaPipeline(BaseModel):
    etapa: EtapaOportunidad
    total: int
    oportunidades: list[OportunidadResumen]


@router.get("/pipeline", summary="Tablero comercial por etapa")
async def pipeline(
    session: Sesion,
    tenant_id: TenantId,
    asesor_id: uuid.UUID | None = None,
    por_columna: Annotated[int, Query(ge=1, le=100)] = 25,
) -> list[ColumnaPipeline]:
    """The §10 board: one column per stage, ordered by lead score."""
    consulta = (
        select(Oportunidad)
        .where(Oportunidad.tenant_id == tenant_id)
        .options(selectinload(Oportunidad.ramo), selectinload(Oportunidad.asesor))
        .order_by(Oportunidad.created_at.desc())
    )
    if asesor_id is not None:
        consulta = consulta.where(Oportunidad.asesor_id == asesor_id)
    oportunidades = (await session.scalars(consulta)).all()

    puntajes: dict[uuid.UUID, float] = {}
    if oportunidades:
        for p in await session.scalars(
            select(PuntajeLead)
            .where(PuntajeLead.oportunidad_id.in_([o.id for o in oportunidades]))
            .order_by(PuntajeLead.calculado_en.desc())
        ):
            puntajes.setdefault(p.oportunidad_id, p.puntaje)

    columnas: list[ColumnaPipeline] = []
    for etapa in EtapaOportunidad:
        de_la_etapa = [o for o in oportunidades if o.etapa is etapa]
        resumenes = sorted(
            (
                OportunidadResumen(
                    id=o.id,
                    ramo=o.ramo.nombre,
                    etapa=o.etapa,
                    creada_en=o.created_at,
                    asesor=(
                        Referencia(id=o.asesor.id, nombre=o.asesor.nombre) if o.asesor else None
                    ),
                    puntaje=puntajes.get(o.id),
                )
                for o in de_la_etapa
            ),
            key=lambda r: (r.puntaje is not None, r.puntaje or 0),
            reverse=True,
        )
        columnas.append(
            ColumnaPipeline(
                etapa=etapa, total=len(de_la_etapa), oportunidades=resumenes[:por_columna]
            )
        )
    return columnas


class CambioOportunidad(BaseModel):
    model_config = ConfigDict(extra="forbid")

    etapa: EtapaOportunidad | None = None
    motivo_perdida: MotivoPerdida | None = None
    asesor_id: uuid.UUID | None = None
    reasignar: bool = Field(
        default=False,
        description="Marca true para aplicar `asesor_id`, incluso cuando es null.",
    )
    nota: str | None = None


@router.patch("/oportunidades/{oportunidad_id}", summary="Mover o asignar una oportunidad")
async def actualizar_oportunidad(
    oportunidad_id: uuid.UUID,
    cambio: CambioOportunidad,
    session: Sesion,
    tenant_id: TenantId,
    usuario: UsuarioActual,
) -> OportunidadResumen:
    oportunidad = await session.scalar(
        select(Oportunidad)
        .where(Oportunidad.id == oportunidad_id, Oportunidad.tenant_id == tenant_id)
        .options(
            selectinload(Oportunidad.ramo),
            selectinload(Oportunidad.asesor),
            selectinload(Oportunidad.cliente),
        )
    )
    if oportunidad is None:
        raise NoEncontrado("Esa oportunidad no existe en esta agencia.")

    if cambio.reasignar:
        await asignar_asesor(
            session,
            oportunidad=oportunidad,
            asesor_id=cambio.asesor_id,
            usuario=usuario,
        )
    if cambio.etapa is not None:
        await cambiar_etapa(
            session,
            oportunidad=oportunidad,
            etapa_nueva=cambio.etapa,
            usuario=usuario,
            motivo_perdida=cambio.motivo_perdida,
            nota=cambio.nota,
        )

    await session.refresh(oportunidad, ["asesor", "ramo"])
    return OportunidadResumen(
        id=oportunidad.id,
        ramo=oportunidad.ramo.nombre,
        etapa=oportunidad.etapa,
        creada_en=oportunidad.created_at,
        asesor=(
            Referencia(id=oportunidad.asesor.id, nombre=oportunidad.asesor.nombre)
            if oportunidad.asesor
            else None
        ),
        puntaje=None,
    )


class EventoHistorial(BaseModel):
    etapa_anterior: EtapaOportunidad | None
    etapa_nueva: EtapaOportunidad
    automatico: bool
    nota: str | None
    ocurrio_en: datetime


@router.get("/oportunidades/{oportunidad_id}/historial", summary="Historial de una oportunidad")
async def historial(
    oportunidad_id: uuid.UUID, session: Sesion, tenant_id: TenantId
) -> list[EventoHistorial]:
    eventos = (
        await session.scalars(
            select(OportunidadEvento)
            .where(
                OportunidadEvento.oportunidad_id == oportunidad_id,
                OportunidadEvento.tenant_id == tenant_id,
            )
            .order_by(OportunidadEvento.created_at)
        )
    ).all()
    return [
        EventoHistorial(
            etapa_anterior=e.etapa_anterior,
            etapa_nueva=e.etapa_nueva,
            automatico=e.automatico,
            nota=e.nota,
            ocurrio_en=e.created_at,
        )
        for e in eventos
    ]
