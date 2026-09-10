"""Message understanding, signature checking and envelope parsing.

All pure: no database, no network, no WhatsApp account.
"""

from __future__ import annotations

import hashlib
import hmac

import pytest

from corredor.services.whatsapp import (
    MENU,
    extraer_mensajes,
    redactar_respuesta,
    verificar_firma,
)
from corredor_ml.nlu import Intencion, analizar, normalizar

SECRETO = "secreto-de-webhook-suficientemente-largo"


def firmar(cuerpo: bytes, secreto: str = SECRETO) -> str:
    return "sha256=" + hmac.new(secreto.encode(), cuerpo, hashlib.sha256).hexdigest()


class TestFirma:
    """Without this check the webhook creates clients for anyone who finds it."""

    def test_acepta_una_firma_valida(self) -> None:
        cuerpo = b'{"entry":[]}'
        assert verificar_firma(cuerpo=cuerpo, firma=firmar(cuerpo), secreto=SECRETO)

    def test_rechaza_un_cuerpo_alterado(self) -> None:
        firma = firmar(b'{"entry":[]}')
        assert not verificar_firma(
            cuerpo=b'{"entry":[{"malicioso":true}]}', firma=firma, secreto=SECRETO
        )

    def test_rechaza_otro_secreto(self) -> None:
        cuerpo = b'{"entry":[]}'
        assert not verificar_firma(
            cuerpo=cuerpo, firma=firmar(cuerpo, "otro-secreto"), secreto=SECRETO
        )

    @pytest.mark.parametrize("firma", [None, "", "abc123", "sha1=deadbeef"])
    def test_rechaza_firmas_malformadas(self, firma: str | None) -> None:
        assert not verificar_firma(cuerpo=b"{}", firma=firma, secreto=SECRETO)


def envoltura(*mensajes: dict[str, object], contactos: list | None = None) -> dict:
    return {
        "entry": [
            {
                "changes": [
                    {
                        "value": {
                            "contacts": contactos or [],
                            "messages": list(mensajes),
                        }
                    }
                ]
            }
        ]
    }


class TestEnvoltura:
    def test_extrae_un_mensaje_de_texto(self) -> None:
        payload = envoltura(
            {
                "id": "wamid.1",
                "from": "573001112233",
                "type": "text",
                "text": {"body": "Hola"},
            },
            contactos=[{"wa_id": "573001112233", "profile": {"name": "Ana"}}],
        )
        mensajes = extraer_mensajes(payload)
        assert len(mensajes) == 1
        assert mensajes[0].texto == "Hola"
        assert mensajes[0].nombre_perfil == "Ana"

    def test_ignora_recibos_de_entrega(self) -> None:
        # Status callbacks share the envelope and are not conversation.
        assert extraer_mensajes({"entry": [{"changes": [{"value": {"statuses": [{}]}}]}]}) == []

    def test_ignora_tipos_que_no_son_texto(self) -> None:
        payload = envoltura({"id": "wamid.2", "from": "57300", "type": "image"})
        assert extraer_mensajes(payload) == []

    @pytest.mark.parametrize(
        "payload", [{}, {"entry": None}, {"entry": [{"changes": None}]}, {"entry": [{}]}]
    )
    def test_una_envoltura_rara_no_revienta(self, payload: dict) -> None:
        # A webhook that raises gets retried forever and eventually disabled.
        assert extraer_mensajes(payload) == []


class TestIntenciones:
    @pytest.mark.parametrize(
        ("texto", "esperada"),
        [
            ("Hola, quiero información sobre un seguro", Intencion.SALUDO),
            ("necesito asegurar mi carro", Intencion.COTIZAR),
            ("cuanto cuesta un seguro de vida", Intencion.COTIZAR),
            ("se me vence la póliza", Intencion.RENOVAR),
            ("quiero renovar", Intencion.RENOVAR),
            ("me chocaron ayer", Intencion.SINIESTRO),
            ("me robaron la moto", Intencion.SINIESTRO),
            ("quiero hablar con un asesor", Intencion.HABLAR_ASESOR),
            ("necesito copia de mi póliza", Intencion.CONSULTAR_POLIZA),
        ],
    )
    def test_clasifica_lo_que_la_gente_escribe(self, texto: str, esperada: Intencion) -> None:
        assert analizar(texto).intencion is esperada

    @pytest.mark.parametrize(
        ("numero", "esperada"),
        [
            ("1", Intencion.COTIZAR),
            ("2", Intencion.CONSULTAR_POLIZA),
            ("3", Intencion.RENOVAR),
            ("4", Intencion.HABLAR_ASESOR),
        ],
    )
    def test_el_menu_numerado_del_brief_sigue_funcionando(
        self, numero: str, esperada: Intencion
    ) -> None:
        analisis = analizar(numero)
        assert analisis.intencion is esperada
        assert analisis.confianza == 1.0

    def test_un_siniestro_gana_sobre_cualquier_otra_cosa(self) -> None:
        # "quiero cotizar pero primero: me chocaron" must not be read as a quote.
        assert analizar("quiero cotizar pero me chocaron").intencion is Intencion.SINIESTRO

    def test_las_tildes_no_cambian_el_resultado(self) -> None:
        assert analizar("automóvil").intencion is analizar("automovil").intencion
        assert normalizar("PÓLIZA") == "poliza"

    @pytest.mark.parametrize(
        ("texto", "ramo"),
        [
            ("seguro para mi carro", "automoviles"),
            ("asegurar mi apartamento", "hogar"),
            ("póliza de cumplimiento para una licitación", "cumplimiento"),
            ("seguro de vida", "vida"),
        ],
    )
    def test_detecta_el_ramo_mencionado(self, texto: str, ramo: str) -> None:
        assert analizar(texto).ramo == ramo

    def test_extrae_la_placa_para_no_volver_a_preguntarla(self) -> None:
        analisis = analizar("quiero asegurar el carro de placa abc-123")
        assert analisis.entidades["placa"] == "ABC123"

    def test_extrae_el_correo(self) -> None:
        analisis = analizar("cotizar seguro, mi correo es ana@test.co")
        assert analisis.entidades["correo"] == "ana@test.co"


class TestFronteraHumana:
    """§8: automation classifies; a person exercises judgement."""

    @pytest.mark.parametrize(
        "texto",
        ["me chocaron", "quiero hablar con un asesor", "consultar mi póliza", "asdkjh"],
    )
    def test_deriva_a_una_persona(self, texto: str) -> None:
        assert analizar(texto).requiere_humano

    @pytest.mark.parametrize("texto", ["cotizar seguro de carro", "quiero renovar", "hola"])
    def test_la_automatizacion_puede_con_esto(self, texto: str) -> None:
        assert not analizar(texto).requiere_humano

    def test_un_mensaje_incomprensible_va_a_una_persona(self) -> None:
        # Guessing at someone already talking to a business about money is
        # worse than handing them over.
        analisis = analizar("xyzzy plugh")
        assert analisis.intencion is Intencion.OTRO
        assert analisis.requiere_humano


class TestRespuestas:
    def test_un_saludo_recibe_el_menu_del_brief(self) -> None:
        respuesta = redactar_respuesta(
            analizar("hola"),
            agencia="Agencia Demo",
            url_publica="https://demo.test",
            nombre_ramo=None,
        )
        assert respuesta == MENU.format(agencia="Agencia Demo")
        for opcion in ("Cotizar", "Consultar", "Renovar", "asesor"):
            assert opcion in respuesta

    def test_un_ramo_detectado_lleva_a_su_formulario(self) -> None:
        respuesta = redactar_respuesta(
            analizar("quiero asegurar mi carro"),
            agencia="Agencia Demo",
            url_publica="https://demo.test",
            nombre_ramo="Automóviles",
        )
        assert "/cotizar/automoviles" in respuesta

    def test_toda_respuesta_es_una_plantilla_escrita_por_una_persona(self) -> None:
        # The model decides what a message is about; it never writes the reply.
        # On this channel the brokerage is legally the one speaking.
        for texto in ("hola", "me chocaron", "cotizar", "renovar", "xyzzy"):
            respuesta = redactar_respuesta(
                analizar(texto),
                agencia="Agencia Demo",
                url_publica="https://demo.test",
                nombre_ramo=None,
            )
            assert respuesta.strip()
            assert "{" not in respuesta, "quedó un marcador sin reemplazar"
