"""WhatsApp as a channel into the platform, not a tool beside it (Módulo 3).

§7 describes the flow; §8 sets the rule that governs it. Automation handles
reception, frequently asked questions, capture, classification, request
creation and notification. Anything needing commercial or technical judgement
goes to a person — and the handoff is recorded, not implied.

Everything a conversation produces lands in the same tables the web form
writes to. A quote request arriving here is a `Solicitud` with a `COT-` code,
identical to one typed on the site, which is the entire point: §5 exists so
that information stops arriving as a message somebody has to transcribe.
"""

from __future__ import annotations

import hashlib
import hmac
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from corredor.core.config import Settings
from corredor.core.logging import get_logger
from corredor.domain.catalogo import Ramo
from corredor.domain.clientes import Cliente
from corredor.domain.comunicaciones import Comunicacion
from corredor.domain.enums import Canal, DireccionComunicacion, TipoCliente
from corredor.domain.inteligencia import AnalisisMensaje
from corredor.domain.tenancy import Tenant
from corredor_ml.nlu import Analisis, Intencion, analizar

log = get_logger(__name__)


def verificar_firma(*, cuerpo: bytes, firma: str | None, secreto: str) -> bool:
    """Verify Meta's `X-Hub-Signature-256` header.

    Without this the webhook is an open endpoint that will create clients and
    quote requests for anyone who finds the URL. Compared in constant time so
    the check cannot be probed byte by byte.
    """
    if not firma or not firma.startswith("sha256="):
        return False
    esperado = hmac.new(secreto.encode(), cuerpo, hashlib.sha256).hexdigest()
    return hmac.compare_digest(esperado, firma.removeprefix("sha256="))


@dataclass(frozen=True, slots=True)
class MensajeEntrante:
    external_id: str
    telefono: str
    texto: str
    nombre_perfil: str | None = None


def extraer_mensajes(payload: dict[str, Any]) -> list[MensajeEntrante]:
    """Pull the text messages out of a Cloud API webhook envelope.

    The envelope also carries delivery receipts, read receipts and status
    changes; those are ignored rather than treated as conversation. Anything
    unexpected is skipped instead of raising — a webhook that 500s gets retried
    forever and eventually disabled by Meta.
    """
    mensajes: list[MensajeEntrante] = []
    for entrada in payload.get("entry", []) or []:
        for cambio in entrada.get("changes", []) or []:
            valor = cambio.get("value") or {}
            perfiles = {
                c.get("wa_id"): (c.get("profile") or {}).get("name")
                for c in valor.get("contacts", []) or []
            }
            for mensaje in valor.get("messages", []) or []:
                if mensaje.get("type") != "text":
                    continue
                texto = ((mensaje.get("text") or {}).get("body") or "").strip()
                telefono = mensaje.get("from")
                identificador = mensaje.get("id")
                if not texto or not telefono or not identificador:
                    continue
                mensajes.append(
                    MensajeEntrante(
                        external_id=identificador,
                        telefono=str(telefono),
                        texto=texto,
                        nombre_perfil=perfiles.get(telefono),
                    )
                )
    return mensajes


MENU = (
    "¡Hola! 👋 Bienvenido a {agencia}. ¿Qué necesitas?\n\n"
    "1️⃣ Cotizar un seguro\n"
    "2️⃣ Consultar una póliza\n"
    "3️⃣ Renovar mi póliza\n"
    "4️⃣ Hablar con un asesor\n\n"
    "Responde con el número, o simplemente cuéntanos con tus palabras."
)

RESPUESTAS: dict[Intencion, str] = {
    Intencion.COTIZAR: (
        "Con gusto te cotizamos. 📋\n"
        "Cuéntanos qué necesitas asegurar y un asesor te contacta hoy mismo.\n"
        "También puedes llenar el formulario aquí: {url}/cotizar"
    ),
    Intencion.RENOVAR: (
        "Te ayudamos con la renovación. 🔄\n"
        "Pásanos el número de póliza o la aseguradora y revisamos si sigue "
        "siendo tu mejor opción antes del vencimiento."
    ),
    Intencion.CONSULTAR_POLIZA: (
        "Claro que sí. Un asesor va a revisar tu póliza y te responde en un momento. 🔎"
    ),
    Intencion.SINIESTRO: (
        "Lamentamos lo ocurrido. 🙏\n"
        "Si es una emergencia, llama primero a la línea de asistencia de tu "
        "aseguradora, que atiende 24 horas.\n"
        "Ya avisamos a un asesor para que te acompañe con el trámite."
    ),
    Intencion.HABLAR_ASESOR: ("Claro. Un asesor te escribe en un momento. 👤"),
    Intencion.OTRO: (
        "Gracias por escribirnos. Un asesor va a leer tu mensaje y te responde en un momento. 👤"
    ),
}

RESPUESTA_RAMO = (
    "Perfecto, un seguro de {ramo}. 📋\n"
    "Para cotizarlo necesitamos unos datos. Puedes enviarlos aquí o llenar el "
    "formulario en {url}/cotizar/{codigo} — toma dos minutos."
)


def redactar_respuesta(
    analisis: Analisis, *, agencia: str, url_publica: str, nombre_ramo: str | None
) -> str:
    """Choose the reply. Deliberately a template, not generated text.

    A generated reply is a liability on a channel where the brokerage is
    legally the one speaking: it can invent a coverage, quote a price or
    promise a timeline. The model decides *what the message is about*; a human
    wrote every word that goes back out.
    """
    if analisis.intencion is Intencion.SALUDO:
        return MENU.format(agencia=agencia)

    if analisis.intencion is Intencion.COTIZAR and analisis.ramo and nombre_ramo:
        return RESPUESTA_RAMO.format(
            ramo=nombre_ramo.lower(), url=url_publica, codigo=analisis.ramo
        )

    return RESPUESTAS.get(analisis.intencion, RESPUESTAS[Intencion.OTRO]).format(url=url_publica)


async def _cliente_por_telefono(
    session: AsyncSession, *, tenant_id: uuid.UUID, telefono: str, nombre: str | None
) -> Cliente:
    """Find the client behind a phone number, or open a record for them.

    A person writing on WhatsApp becomes a client record immediately, before
    any sale — the same rule the web form follows, so both channels feed one
    dataset instead of two.
    """
    cliente = await session.scalar(
        select(Cliente).where(Cliente.tenant_id == tenant_id, Cliente.telefono == telefono)
    )
    if cliente is not None:
        return cliente

    cliente = Cliente(
        tenant_id=tenant_id,
        tipo=TipoCliente.PERSONA,
        nombre=nombre or f"WhatsApp {telefono[-4:]}",
        telefono=telefono,
        origen=Canal.WHATSAPP,
    )
    session.add(cliente)
    await session.flush()
    return cliente


@dataclass(slots=True)
class ResultadoMensaje:
    cliente_id: uuid.UUID
    intencion: Intencion
    requiere_humano: bool
    respuesta: str
    duplicado: bool = False


async def manejar_mensaje(
    session: AsyncSession,
    *,
    tenant: Tenant,
    mensaje: MensajeEntrante,
    settings: Settings,
) -> ResultadoMensaje:
    """Record, classify and answer one inbound message."""
    # Meta retries webhooks. The unique constraint on (tenant, external_id) is
    # the backstop; this check keeps a retry from re-replying to the client.
    ya_visto = await session.scalar(
        select(Comunicacion).where(
            Comunicacion.tenant_id == tenant.id,
            Comunicacion.external_id == mensaje.external_id,
        )
    )
    if ya_visto is not None:
        log.info("whatsapp_mensaje_duplicado", external_id=mensaje.external_id)
        return ResultadoMensaje(
            cliente_id=ya_visto.cliente_id,
            intencion=Intencion.OTRO,
            requiere_humano=False,
            respuesta="",
            duplicado=True,
        )

    cliente = await _cliente_por_telefono(
        session,
        tenant_id=tenant.id,
        telefono=mensaje.telefono,
        nombre=mensaje.nombre_perfil,
    )

    entrante = Comunicacion(
        tenant_id=tenant.id,
        cliente_id=cliente.id,
        canal=Canal.WHATSAPP,
        direccion=DireccionComunicacion.ENTRANTE,
        contenido=mensaje.texto,
        external_id=mensaje.external_id,
        payload={"telefono": mensaje.telefono, "perfil": mensaje.nombre_perfil},
    )
    session.add(entrante)
    await session.flush()

    analisis = analizar(mensaje.texto)

    nombre_ramo: str | None = None
    ramo_id: uuid.UUID | None = None
    if analisis.ramo:
        ramo = await session.scalar(
            select(Ramo).where(
                Ramo.tenant_id == tenant.id,
                Ramo.codigo == analisis.ramo,
                Ramo.activo.is_(True),
            )
        )
        if ramo is not None:
            nombre_ramo, ramo_id = ramo.nombre, ramo.id

    session.add(
        AnalisisMensaje(
            tenant_id=tenant.id,
            comunicacion_id=entrante.id,
            intencion=analisis.intencion.value,
            confianza=analisis.confianza,
            ramo_detectado_id=ramo_id,
            entidades=dict(analisis.entidades),
            requiere_humano=analisis.requiere_humano,
            modelo=analisis.modelo,
            modelo_version=analisis.modelo_version,
            features={"texto": mensaje.texto},
            calculado_en=datetime.now(UTC).replace(tzinfo=None),
        )
    )

    respuesta = redactar_respuesta(
        analisis,
        agencia=tenant.nombre,
        url_publica=str(tenant.configuracion.get("url_publica", "")).rstrip("/"),
        nombre_ramo=nombre_ramo,
    )

    session.add(
        Comunicacion(
            tenant_id=tenant.id,
            cliente_id=cliente.id,
            canal=Canal.WHATSAPP,
            direccion=DireccionComunicacion.SALIENTE,
            contenido=respuesta,
            automatico=True,
            payload={"intencion": analisis.intencion.value},
        )
    )
    await session.flush()

    if analisis.requiere_humano:
        # §8's boundary, crossed explicitly and logged. Routing this to a
        # specific advisor is the phase-2 notification work.
        log.info(
            "whatsapp_derivado_a_asesor",
            cliente=str(cliente.id),
            intencion=analisis.intencion.value,
            confianza=analisis.confianza,
        )

    return ResultadoMensaje(
        cliente_id=cliente.id,
        intencion=analisis.intencion,
        requiere_humano=analisis.requiere_humano,
        respuesta=respuesta,
    )


async def enviar_mensaje(settings: Settings, *, telefono: str, texto: str) -> bool:
    """Send a reply through the Cloud API.

    Returns False when WhatsApp is not configured, which is the normal state
    in development and in this repository's demo. The conversation is still
    recorded either way, so the CRM shows what *would* have been said — the
    channel is optional, the record is not.
    """
    if not settings.whatsapp_access_token or not settings.whatsapp_phone_number_id:
        log.info("whatsapp_no_configurado", telefono=telefono[-4:], enviado=False)
        return False

    url = f"https://graph.facebook.com/v21.0/{settings.whatsapp_phone_number_id}/messages"
    async with httpx.AsyncClient(timeout=10) as cliente:
        respuesta = await cliente.post(
            url,
            headers={
                "Authorization": (f"Bearer {settings.whatsapp_access_token.get_secret_value()}")
            },
            json={
                "messaging_product": "whatsapp",
                "to": telefono,
                "type": "text",
                "text": {"body": texto},
            },
        )
    if respuesta.status_code >= 400:
        log.error("whatsapp_envio_fallido", estado=respuesta.status_code)
        return False
    return True
