"""The WhatsApp webhook, end to end.

A message arriving here must land in the same tables the web form writes to —
that is the §7 requirement that WhatsApp be a channel *into* the platform
rather than a tool beside it.
"""

from __future__ import annotations

import hashlib
import hmac
import json

import pytest
from httpx import AsyncClient
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from corredor.core.config import Settings, get_settings
from corredor.domain.catalogo import Ramo
from corredor.domain.clientes import Cliente
from corredor.domain.comunicaciones import Comunicacion
from corredor.domain.enums import Canal, DireccionComunicacion
from corredor.domain.inteligencia import AnalisisMensaje
from corredor.domain.tenancy import Tenant
from corredor.main import create_app

pytestmark = pytest.mark.integration

VERIFY = "token-de-verificacion-de-prueba-largo"


@pytest.fixture
def settings_whatsapp() -> Settings:
    """Settings with the channel configured, applied to the cached instance."""
    settings = get_settings()
    original = settings.whatsapp_verify_token
    object.__setattr__(settings, "whatsapp_verify_token", None)
    from pydantic import SecretStr

    settings.whatsapp_verify_token = SecretStr(VERIFY)
    yield settings
    settings.whatsapp_verify_token = original


def envoltura(texto: str, *, external_id: str = "wamid.1", telefono: str = "573001112233"):
    return {
        "entry": [
            {
                "changes": [
                    {
                        "value": {
                            "contacts": [{"wa_id": telefono, "profile": {"name": "Ana Prueba"}}],
                            "messages": [
                                {
                                    "id": external_id,
                                    "from": telefono,
                                    "type": "text",
                                    "text": {"body": texto},
                                }
                            ],
                        }
                    }
                ]
            }
        ]
    }


def firmado(payload: dict) -> tuple[bytes, dict[str, str]]:
    cuerpo = json.dumps(payload).encode()
    firma = hmac.new(VERIFY.encode(), cuerpo, hashlib.sha256).hexdigest()
    return cuerpo, {
        "Content-Type": "application/json",
        "X-Hub-Signature-256": f"sha256={firma}",
    }


async def enviar(cliente: AsyncClient, tenant: Tenant, payload: dict) -> object:
    cuerpo, cabeceras = firmado(payload)
    cabeceras["X-Tenant"] = tenant.slug
    return await cliente.post("/api/v1/whatsapp/webhook", content=cuerpo, headers=cabeceras)


class TestSeguridadDelWebhook:
    async def test_rechaza_un_cuerpo_sin_firma(
        self, cliente_http: AsyncClient, tenant: Tenant, settings_whatsapp: Settings
    ) -> None:
        respuesta = await cliente_http.post(
            "/api/v1/whatsapp/webhook",
            json=envoltura("hola"),
            headers={"X-Tenant": tenant.slug},
        )
        assert respuesta.status_code == 401

    async def test_rechaza_una_firma_de_otro_secreto(
        self, cliente_http: AsyncClient, tenant: Tenant, settings_whatsapp: Settings
    ) -> None:
        cuerpo = json.dumps(envoltura("hola")).encode()
        firma = hmac.new(b"otro-secreto", cuerpo, hashlib.sha256).hexdigest()
        respuesta = await cliente_http.post(
            "/api/v1/whatsapp/webhook",
            content=cuerpo,
            headers={
                "Content-Type": "application/json",
                "X-Hub-Signature-256": f"sha256={firma}",
                "X-Tenant": tenant.slug,
            },
        )
        assert respuesta.status_code == 401

    async def test_no_escribe_nada_cuando_la_firma_falla(
        self,
        cliente_http: AsyncClient,
        session: AsyncSession,
        tenant: Tenant,
        settings_whatsapp: Settings,
    ) -> None:
        await cliente_http.post(
            "/api/v1/whatsapp/webhook",
            json=envoltura("hola"),
            headers={"X-Tenant": tenant.slug},
        )
        total = await session.scalar(
            select(func.count()).select_from(Cliente).where(Cliente.tenant_id == tenant.id)
        )
        assert total == 0

    async def test_la_verificacion_devuelve_el_desafio_en_texto_plano(
        self, cliente_http: AsyncClient, settings_whatsapp: Settings
    ) -> None:
        respuesta = await cliente_http.get(
            "/api/v1/whatsapp/webhook",
            params={
                "hub.mode": "subscribe",
                "hub.verify_token": VERIFY,
                "hub.challenge": "1234567890",
            },
        )
        assert respuesta.status_code == 200
        assert respuesta.text == "1234567890"

    async def test_la_verificacion_rechaza_un_token_incorrecto(
        self, cliente_http: AsyncClient, settings_whatsapp: Settings
    ) -> None:
        respuesta = await cliente_http.get(
            "/api/v1/whatsapp/webhook",
            params={
                "hub.mode": "subscribe",
                "hub.verify_token": "equivocado",
                "hub.challenge": "1234",
            },
        )
        assert respuesta.status_code == 401


class TestConversacion:
    async def test_un_mensaje_crea_cliente_conversacion_y_analisis(
        self,
        cliente_http: AsyncClient,
        session: AsyncSession,
        tenant: Tenant,
        ramos: dict[str, Ramo],
        settings_whatsapp: Settings,
    ) -> None:
        respuesta = await enviar(cliente_http, tenant, envoltura("quiero asegurar mi carro"))
        assert respuesta.status_code == 200
        assert respuesta.json() == {"recibidos": 1, "procesados": 1}

        cliente = await session.scalar(select(Cliente).where(Cliente.tenant_id == tenant.id))
        assert cliente is not None
        assert cliente.origen is Canal.WHATSAPP
        assert cliente.nombre == "Ana Prueba"
        assert cliente.telefono == "573001112233"

        comunicaciones = (
            await session.scalars(select(Comunicacion).where(Comunicacion.cliente_id == cliente.id))
        ).all()
        direcciones = {c.direccion for c in comunicaciones}
        assert direcciones == {
            DireccionComunicacion.ENTRANTE,
            DireccionComunicacion.SALIENTE,
        }

        analisis = await session.scalar(select(AnalisisMensaje))
        assert analisis is not None
        assert analisis.intencion == "cotizar"
        assert analisis.ramo_detectado_id == ramos["automoviles"].id
        assert analisis.modelo_version, "una predicción sin versión no es auditable"

    async def test_un_reintento_de_meta_no_duplica_ni_vuelve_a_responder(
        self,
        cliente_http: AsyncClient,
        session: AsyncSession,
        tenant: Tenant,
        ramos: dict[str, Ramo],
        settings_whatsapp: Settings,
    ) -> None:
        payload = envoltura("hola", external_id="wamid.repetido")
        await enviar(cliente_http, tenant, payload)
        await enviar(cliente_http, tenant, payload)

        entrantes = await session.scalar(
            select(func.count())
            .select_from(Comunicacion)
            .where(
                Comunicacion.tenant_id == tenant.id,
                Comunicacion.direccion == DireccionComunicacion.ENTRANTE,
            )
        )
        salientes = await session.scalar(
            select(func.count())
            .select_from(Comunicacion)
            .where(
                Comunicacion.tenant_id == tenant.id,
                Comunicacion.direccion == DireccionComunicacion.SALIENTE,
            )
        )
        assert entrantes == 1
        assert salientes == 1, "un reintento no puede volver a escribirle al cliente"

    async def test_el_mismo_numero_no_crea_dos_clientes(
        self,
        cliente_http: AsyncClient,
        session: AsyncSession,
        tenant: Tenant,
        ramos: dict[str, Ramo],
        settings_whatsapp: Settings,
    ) -> None:
        await enviar(cliente_http, tenant, envoltura("hola", external_id="wamid.a"))
        await enviar(cliente_http, tenant, envoltura("cotizar", external_id="wamid.b"))

        total = await session.scalar(
            select(func.count()).select_from(Cliente).where(Cliente.tenant_id == tenant.id)
        )
        assert total == 1

    async def test_un_siniestro_queda_marcado_para_una_persona(
        self,
        cliente_http: AsyncClient,
        session: AsyncSession,
        tenant: Tenant,
        ramos: dict[str, Ramo],
        settings_whatsapp: Settings,
    ) -> None:
        await enviar(cliente_http, tenant, envoltura("me chocaron el carro ayer"))
        analisis = await session.scalar(select(AnalisisMensaje))
        assert analisis is not None
        assert analisis.intencion == "siniestro"
        assert analisis.requiere_humano is True

    async def test_una_envoltura_sin_mensajes_responde_200(
        self,
        cliente_http: AsyncClient,
        tenant: Tenant,
        ramos: dict[str, Ramo],
        settings_whatsapp: Settings,
    ) -> None:
        # Meta disables a webhook that keeps failing; delivery receipts must
        # not look like an error.
        respuesta = await enviar(
            cliente_http, tenant, {"entry": [{"changes": [{"value": {"statuses": []}}]}]}
        )
        assert respuesta.status_code == 200
        assert respuesta.json()["recibidos"] == 0


def test_la_app_expone_el_webhook() -> None:
    rutas = create_app().openapi()["paths"]
    assert "/api/v1/whatsapp/webhook" in rutas
