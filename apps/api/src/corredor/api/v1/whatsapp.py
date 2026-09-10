"""WhatsApp Cloud API webhook (Módulo 3)."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Header, Query, Request, Response, status

from corredor.api.deps import Sesion, TenantActual
from corredor.core.config import get_settings
from corredor.core.errors import NoAutorizado
from corredor.core.logging import get_logger
from corredor.services.whatsapp import (
    enviar_mensaje,
    extraer_mensajes,
    manejar_mensaje,
    verificar_firma,
)

router = APIRouter(prefix="/whatsapp", tags=["WhatsApp"])
log = get_logger(__name__)


@router.get("/webhook", summary="Verificación del webhook (Meta)")
async def verificar(
    modo: Annotated[str | None, Query(alias="hub.mode")] = None,
    token: Annotated[str | None, Query(alias="hub.verify_token")] = None,
    desafio: Annotated[str | None, Query(alias="hub.challenge")] = None,
) -> Response:
    """Meta's one-time subscription handshake.

    It expects the challenge echoed back as plain text, not JSON.
    """
    settings = get_settings()
    esperado = (
        settings.whatsapp_verify_token.get_secret_value()
        if settings.whatsapp_verify_token
        else None
    )
    if modo == "subscribe" and esperado and token == esperado and desafio:
        return Response(content=desafio, media_type="text/plain")
    raise NoAutorizado("Verificación de webhook inválida.")


@router.post(
    "/webhook",
    status_code=status.HTTP_200_OK,
    summary="Recepción de mensajes de WhatsApp",
)
async def recibir(
    request: Request,
    session: Sesion,
    tenant: TenantActual,
    firma: Annotated[str | None, Header(alias="X-Hub-Signature-256")] = None,
) -> dict[str, object]:
    """Receive an inbound message batch.

    Two rules govern the response:

    - **Always answer 200 once the signature checks out.** Meta retries any
      non-2xx and eventually disables a webhook that keeps failing, so a bug
      handling one message must not cost the brokerage the whole channel.
      Failures are logged and the batch continues.
    - **Verify the signature first.** Without it this is an open endpoint that
      creates clients and quote requests for anyone who finds the URL.
    """
    cuerpo = await request.body()
    settings = get_settings()

    if settings.whatsapp_verify_token is not None:
        if not verificar_firma(
            cuerpo=cuerpo,
            firma=firma,
            secreto=settings.whatsapp_verify_token.get_secret_value(),
        ):
            raise NoAutorizado("Firma del webhook inválida.")
    elif settings.is_production:
        # Refusing here is safer than accepting unsigned traffic in production.
        raise NoAutorizado("El canal de WhatsApp no está configurado.")

    payload = await request.json()
    mensajes = extraer_mensajes(payload)

    procesados = 0
    for mensaje in mensajes:
        try:
            resultado = await manejar_mensaje(
                session, tenant=tenant, mensaje=mensaje, settings=settings
            )
            if not resultado.duplicado and resultado.respuesta:
                await enviar_mensaje(settings, telefono=mensaje.telefono, texto=resultado.respuesta)
            procesados += 1
        except Exception:
            log.exception("whatsapp_mensaje_fallido", external_id=mensaje.external_id)

    return {"recibidos": len(mensajes), "procesados": procesados}
