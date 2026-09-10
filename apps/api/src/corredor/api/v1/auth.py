"""Sign-in for advisors, managers and administrators."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel, ConfigDict
from sqlalchemy import func, select

from corredor.api.deps import Sesion, UsuarioActual
from corredor.core.config import get_settings
from corredor.core.errors import NoAutorizado
from corredor.core.logging import get_logger
from corredor.core.seguridad import crear_token, verificar_clave
from corredor.domain.enums import RolUsuario
from corredor.domain.tenancy import Tenant, Usuario

router = APIRouter(prefix="/auth", tags=["autenticación"])
log = get_logger(__name__)


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"  # noqa: S105 - an OAuth2 scheme name, not a secret
    expires_in: int


class UsuarioPublico(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    nombre: str
    email: str
    rol: RolUsuario
    tenant: str
    puede_ver_dashboard: bool


@router.post("/login", summary="Iniciar sesión")
async def login(datos: Annotated[OAuth2PasswordRequestForm, Depends()], session: Sesion) -> Token:
    """Exchange an email and password for an access token.

    The email is matched case-insensitively and globally, not within a tenant:
    a person signing in has no way to name their agency, and the account is
    what determines it.
    """
    correo = datos.username.strip().lower()
    usuario = await session.scalar(
        select(Usuario).where(func.lower(Usuario.email) == correo, Usuario.activo.is_(True))
    )

    # One message for "no such user" and for "wrong password". Telling them
    # apart turns the login form into a way to enumerate who works here.
    generico = NoAutorizado("Correo o contraseña incorrectos.")
    if usuario is None:
        raise generico

    valido, nuevo_hash = verificar_clave(datos.password, usuario.password_hash)
    if not valido:
        log.info("login_fallido", email=correo)
        raise generico
    if nuevo_hash is not None:
        # The stored hash used weaker parameters than we now require.
        usuario.password_hash = nuevo_hash

    settings = get_settings()
    token, duracion = crear_token(
        settings,
        usuario_id=usuario.id,
        tenant_id=usuario.tenant_id,
        rol=usuario.rol.value,
    )
    log.info("login_exitoso", usuario=str(usuario.id), rol=usuario.rol.value)
    return Token(access_token=token, expires_in=duracion)


@router.get("/yo", summary="Usuario de la sesión actual")
async def yo(usuario: UsuarioActual, session: Sesion) -> UsuarioPublico:
    tenant = await session.get(Tenant, usuario.tenant_id)
    return UsuarioPublico(
        id=str(usuario.id),
        nombre=usuario.nombre,
        email=usuario.email,
        rol=usuario.rol,
        tenant=tenant.nombre if tenant else "",
        puede_ver_dashboard=usuario.puede_ver_dashboard,
    )
