"""Turning a quote request into CRM records (Módulos 2 and 4).

This is the hinge of the whole platform. §5 of the brief is explicit about
what it exists to prevent: information arriving as a WhatsApp message that
somebody has to transcribe later. One submission produces, atomically, a
client, a coded request, an opportunity at the head of the pipeline, its first
audit event, and a lead score — or it produces nothing at all.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from corredor.core.logging import get_logger
from corredor.domain.catalogo import Ramo
from corredor.domain.clientes import Cliente
from corredor.domain.comercial import Oportunidad, OportunidadEvento, Solicitud
from corredor.domain.enums import (
    Canal,
    EstadoPoliza,
    EstadoSolicitud,
    EtapaOportunidad,
    NivelRiesgo,
    TipoCliente,
    TipoDocumento,
)
from corredor.domain.inteligencia import PuntajeLead
from corredor.domain.polizas import Poliza
from corredor.domain.validacion import completitud, validar_respuestas
from corredor.services.consecutivos import siguiente_codigo
from corredor_ml.lead_scoring import LeadFeatures, PuntuadorLeadBaseline

log = get_logger(__name__)

_puntuador = PuntuadorLeadBaseline()

#: Score above which an opportunity is worth an advisor's attention first.
UMBRAL_LEAD_ALTO = 0.66
UMBRAL_LEAD_MEDIO = 0.40


def _nivel(puntaje: float) -> NivelRiesgo:
    if puntaje >= UMBRAL_LEAD_ALTO:
        return NivelRiesgo.ALTO
    if puntaje >= UMBRAL_LEAD_MEDIO:
        return NivelRiesgo.MEDIO
    return NivelRiesgo.BAJO


async def _encontrar_cliente(
    session: AsyncSession,
    *,
    tenant_id: uuid.UUID,
    documento: str | None,
    telefono: str | None,
    correo: str | None,
) -> Cliente | None:
    """Match a returning client, in descending order of confidence.

    Document number is near-unique and is tried first. Phone is next: it is
    what people actually give, and a repeated number is almost always the same
    person. Email is last — shared family addresses are common enough that
    matching on it alone would merge distinct clients.
    """

    async def buscar(condicion: Any) -> Cliente | None:
        # `session.scalar` is typed as returning Any for arbitrary statements;
        # the annotation is what keeps this function's contract honest.
        encontrado: Cliente | None = await session.scalar(
            select(Cliente).where(Cliente.tenant_id == tenant_id, condicion)
        )
        return encontrado

    if documento:
        cliente = await buscar(Cliente.documento == documento)
        if cliente is not None:
            return cliente
    if telefono:
        cliente = await buscar(Cliente.telefono == telefono)
        if cliente is not None:
            return cliente
    if correo:
        return await buscar(Cliente.email == func.lower(correo))
    return None


async def registrar_solicitud(
    session: AsyncSession,
    *,
    tenant_id: uuid.UUID,
    ramo: Ramo,
    canal: Canal,
    respuestas: dict[str, Any],
    utm: dict[str, Any] | None = None,
) -> Solicitud:
    """Register a quote request and everything that follows from it.

    Raises `ErroresDeFormulario` when the answers do not satisfy the ramo's
    form; nothing is written in that case.
    """
    formulario = ramo.form
    limpio = validar_respuestas(formulario, respuestas)

    nombre = str(limpio.get("nombre") or "").strip()
    documento = limpio.get("documento")
    telefono = limpio.get("telefono")
    correo = limpio.get("correo")
    ciudad = limpio.get("ciudad")

    cliente = await _encontrar_cliente(
        session,
        tenant_id=tenant_id,
        documento=documento,
        telefono=telefono,
        correo=correo,
    )
    es_cliente_existente = cliente is not None

    if cliente is None:
        cliente = Cliente(
            tenant_id=tenant_id,
            tipo=(
                TipoCliente.EMPRESA
                if ramo.dirigido_a is TipoCliente.EMPRESA
                else TipoCliente.PERSONA
            ),
            nombre=nombre or "Sin nombre",
            tipo_documento=(
                TipoDocumento.NIT if ramo.dirigido_a is TipoCliente.EMPRESA else TipoDocumento.CC
            )
            if documento
            else None,
            documento=documento,
            telefono=telefono,
            email=correo,
            ciudad=ciudad,
            origen=canal,
        )
        session.add(cliente)
        await session.flush()
    else:
        # A returning client may be reaching us with better details than we
        # hold. Fill gaps, but never overwrite what an advisor already curated.
        cliente.telefono = cliente.telefono or telefono
        cliente.email = cliente.email or correo
        cliente.ciudad = cliente.ciudad or ciudad
        cliente.documento = cliente.documento or documento

    polizas_vigentes = (
        await session.scalar(
            select(func.count())
            .select_from(Poliza)
            .where(
                Poliza.cliente_id == cliente.id,
                Poliza.estado.in_((EstadoPoliza.VIGENTE, EstadoPoliza.PROXIMA_A_VENCER)),
            )
        )
    ) or 0

    codigo = await siguiente_codigo(session, tenant_id=tenant_id, entidad="solicitud")

    solicitud = Solicitud(
        tenant_id=tenant_id,
        codigo=codigo,
        cliente_id=cliente.id,
        ramo_id=ramo.id,
        canal=canal,
        estado=EstadoSolicitud.NUEVA,
        respuestas=limpio,
        formulario_version=formulario.version,
        utm=utm or {},
    )
    session.add(solicitud)
    await session.flush()

    oportunidad = Oportunidad(
        tenant_id=tenant_id,
        cliente_id=cliente.id,
        ramo_id=ramo.id,
        solicitud_id=solicitud.id,
        etapa=EtapaOportunidad.NUEVO,
        asesor_id=cliente.asesor_id,
    )
    session.add(oportunidad)
    await session.flush()

    session.add(
        OportunidadEvento(
            tenant_id=tenant_id,
            oportunidad_id=oportunidad.id,
            etapa_anterior=None,
            etapa_nueva=EtapaOportunidad.NUEVO,
            automatico=True,
            nota=f"Solicitud {codigo} recibida por {canal.value}.",
        )
    )

    prediccion = _puntuador.predecir(
        LeadFeatures(
            canal=canal.value,
            completitud_formulario=completitud(formulario, limpio),
            tiene_telefono=bool(telefono),
            tiene_email=bool(correo),
            es_cliente_existente=es_cliente_existente,
            polizas_vigentes=polizas_vigentes,
            horas_desde_solicitud=0.0,
        )
    )
    session.add(
        PuntajeLead(
            tenant_id=tenant_id,
            oportunidad_id=oportunidad.id,
            puntaje=prediccion.puntaje,
            nivel=_nivel(prediccion.puntaje),
            explicacion=[c.model_dump() for c in prediccion.explicacion],
            modelo=prediccion.modelo,
            modelo_version=prediccion.modelo_version,
            features=limpio,
            calculado_en=datetime.now(UTC).replace(tzinfo=None),
        )
    )

    await session.flush()
    log.info(
        "solicitud_registrada",
        codigo=codigo,
        ramo=ramo.codigo,
        canal=canal.value,
        cliente_nuevo=not es_cliente_existente,
        puntaje=round(prediccion.puntaje, 3),
    )
    return solicitud
