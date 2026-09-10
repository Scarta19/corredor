"""Password hashing and access tokens.

Kept free of FastAPI so it can be used from scripts and workers — creating a
user from a management command must produce exactly the hash the login path
expects.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Any

import jwt
from pwdlib import PasswordHash

from corredor.core.config import Settings
from corredor.core.errors import NoAutorizado

# Argon2id: the current recommendation, and `pwdlib` handles the parameters.
# `verify_and_update` lets a stored hash be upgraded transparently the next
# time its owner logs in, so raising the cost later needs no migration.
_hasher = PasswordHash.recommended()


def hashear_clave(clave: str) -> str:
    return _hasher.hash(clave)


def verificar_clave(clave: str, hash_guardado: str) -> tuple[bool, str | None]:
    """Check a password. Returns `(ok, nuevo_hash)`.

    `nuevo_hash` is not None when the stored hash used weaker parameters than
    the current recommendation and should be replaced.
    """
    return _hasher.verify_and_update(clave, hash_guardado)


@dataclass(frozen=True, slots=True)
class Credenciales:
    """What a validated token asserts.

    `tenant_id` comes from here and never from a request header. A header is
    something the caller controls; for authenticated traffic that would be a
    cross-tenant read waiting to happen (ADR-0002).
    """

    usuario_id: uuid.UUID
    tenant_id: uuid.UUID
    rol: str


def crear_token(
    settings: Settings, *, usuario_id: uuid.UUID, tenant_id: uuid.UUID, rol: str
) -> tuple[str, int]:
    """Issue an access token. Returns the token and its lifetime in seconds."""
    ahora = datetime.now(UTC)
    duracion = timedelta(minutes=settings.access_token_ttl_minutes)
    carga: dict[str, Any] = {
        "sub": str(usuario_id),
        "tenant": str(tenant_id),
        "rol": rol,
        "iat": ahora,
        "exp": ahora + duracion,
    }
    token = jwt.encode(
        carga,
        settings.secret_key.get_secret_value(),
        algorithm=settings.jwt_algorithm,
    )
    return token, int(duracion.total_seconds())


def leer_token(settings: Settings, token: str) -> Credenciales:
    """Validate a token and return what it asserts.

    Every failure — expired, tampered, malformed, wrong algorithm — surfaces
    as the same `NoAutorizado`. Distinguishing them for the caller would tell
    an attacker which part of a forged token to fix.
    """
    try:
        carga = jwt.decode(
            token,
            settings.secret_key.get_secret_value(),
            algorithms=[settings.jwt_algorithm],
        )
        return Credenciales(
            usuario_id=uuid.UUID(carga["sub"]),
            tenant_id=uuid.UUID(carga["tenant"]),
            rol=str(carga["rol"]),
        )
    except (jwt.PyJWTError, KeyError, ValueError) as exc:
        raise NoAutorizado("La sesión no es válida o expiró.") from exc
