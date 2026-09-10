"""Tokens and password hashing."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta

import jwt
import pytest

from corredor.core.config import CLAVE_DE_DESARROLLO, Settings
from corredor.core.errors import NoAutorizado
from corredor.core.seguridad import (
    crear_token,
    hashear_clave,
    leer_token,
    verificar_clave,
)

SETTINGS = Settings(secret_key="secreto-de-prueba-con-longitud-suficiente", environment="test")
OTRO = Settings(secret_key="otro-secreto-distinto-y-suficientemente-largo", environment="test")


def emitir() -> tuple[str, uuid.UUID, uuid.UUID]:
    usuario_id, tenant_id = uuid.uuid4(), uuid.uuid4()
    token, _ = crear_token(SETTINGS, usuario_id=usuario_id, tenant_id=tenant_id, rol="asesor")
    return token, usuario_id, tenant_id


class TestClaves:
    def test_el_hash_no_contiene_la_clave(self) -> None:
        assert "abril2026" not in hashear_clave("abril2026")

    def test_dos_hashes_de_la_misma_clave_difieren(self) -> None:
        # Salted: identical passwords must not produce identical hashes, or
        # the hash list itself reveals who shares a password.
        assert hashear_clave("abril2026") != hashear_clave("abril2026")

    def test_la_clave_correcta_verifica(self) -> None:
        ok, _ = verificar_clave("abril2026", hashear_clave("abril2026"))
        assert ok

    def test_la_clave_incorrecta_no_verifica(self) -> None:
        ok, _ = verificar_clave("otra", hashear_clave("abril2026"))
        assert not ok


class TestTokens:
    def test_ida_y_vuelta_conserva_las_credenciales(self) -> None:
        token, usuario_id, tenant_id = emitir()
        credenciales = leer_token(SETTINGS, token)
        assert credenciales.usuario_id == usuario_id
        assert credenciales.tenant_id == tenant_id
        assert credenciales.rol == "asesor"

    def test_el_token_lleva_el_tenant(self) -> None:
        # This is what lets authenticated requests ignore any tenant header.
        token, _, tenant_id = emitir()
        assert leer_token(SETTINGS, token).tenant_id == tenant_id

    def test_un_token_firmado_con_otro_secreto_se_rechaza(self) -> None:
        token, _, _ = emitir()
        with pytest.raises(NoAutorizado):
            leer_token(OTRO, token)

    def test_un_token_alterado_se_rechaza(self) -> None:
        token, _, _ = emitir()
        with pytest.raises(NoAutorizado):
            leer_token(SETTINGS, token[:-3] + "aaa")

    def test_un_token_expirado_se_rechaza(self) -> None:
        vencido = jwt.encode(
            {
                "sub": str(uuid.uuid4()),
                "tenant": str(uuid.uuid4()),
                "rol": "asesor",
                "exp": datetime.now(UTC) - timedelta(minutes=1),
            },
            SETTINGS.secret_key.get_secret_value(),
            algorithm=SETTINGS.jwt_algorithm,
        )
        with pytest.raises(NoAutorizado):
            leer_token(SETTINGS, vencido)

    def test_un_token_sin_firma_se_rechaza(self) -> None:
        # The classic `alg: none` forgery.
        falso = jwt.encode(
            {"sub": str(uuid.uuid4()), "tenant": str(uuid.uuid4()), "rol": "admin"},
            "",
            algorithm="none",
        )
        with pytest.raises(NoAutorizado):
            leer_token(SETTINGS, falso)

    def test_basura_se_rechaza(self) -> None:
        with pytest.raises(NoAutorizado):
            leer_token(SETTINGS, "no-es-un-token")


class TestClaveDeFirma:
    """A too-short signing key must stop the process, not warn."""

    def test_rechaza_una_clave_corta(self) -> None:
        with pytest.raises(ValueError, match="al menos 32 bytes"):
            Settings(secret_key="corta", environment="local")

    def test_acepta_una_clave_de_longitud_suficiente(self) -> None:
        assert Settings(secret_key="a" * 32, environment="local")

    @pytest.mark.parametrize("entorno", ["staging", "production"])
    def test_rechaza_la_clave_de_desarrollo_fuera_de_local(self, entorno: str) -> None:
        with pytest.raises(ValueError, match="sigue siendo la de desarrollo"):
            Settings(secret_key=CLAVE_DE_DESARROLLO, environment=entorno)  # type: ignore[arg-type]

    def test_permite_la_clave_de_desarrollo_en_local(self) -> None:
        assert Settings(secret_key=CLAVE_DE_DESARROLLO, environment="local")
