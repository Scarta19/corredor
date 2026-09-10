"""Shared FastAPI dependencies.

Two ways of establishing which brokerage a request belongs to, and they are
deliberately not interchangeable:

- **Public traffic** carries no credentials, so the tenant comes from the
  `X-Tenant` slug the site's own frontend sets.
- **Authenticated traffic** takes it from the token and never from a header.
  A header is caller-controlled; trusting one here would be a cross-tenant
  read waiting to happen (ADR-0002).
"""

from __future__ import annotations

import uuid
from collections.abc import Awaitable, Callable
from typing import Annotated

from fastapi import Depends, Header
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from corredor.core.config import get_settings
from corredor.core.errors import NoAutorizado, NoEncontrado, SinPermiso
from corredor.core.seguridad import leer_token
from corredor.db.session import get_session
from corredor.domain.enums import RolUsuario
from corredor.domain.tenancy import Tenant, Usuario

Sesion = Annotated[AsyncSession, Depends(get_session)]

esquema_oauth = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login", auto_error=False)


# --- Public traffic ---------------------------------------------------------


async def resolver_tenant(
    session: Sesion,
    x_tenant: Annotated[str | None, Header(alias="X-Tenant")] = None,
) -> Tenant:
    """Resolve the tenant for an anonymous public request."""
    slug = x_tenant or "demo"
    tenant = await session.scalar(
        select(Tenant).where(Tenant.slug == slug, Tenant.activo.is_(True))
    )
    if tenant is None:
        raise NoEncontrado(f"No existe una agencia activa con el identificador '{slug}'.")
    return tenant


TenantActual = Annotated[Tenant, Depends(resolver_tenant)]


# --- Authenticated traffic --------------------------------------------------


async def usuario_actual(
    session: Sesion,
    token: Annotated[str | None, Depends(esquema_oauth)] = None,
) -> Usuario:
    """The signed-in user, loaded fresh from the database.

    The token is not treated as the user record. Re-reading means an account
    deactivated a minute ago stops working now, rather than when its token
    happens to expire.
    """
    if not token:
        raise NoAutorizado("Se requiere iniciar sesión.")

    credenciales = leer_token(get_settings(), token)
    usuario = await session.scalar(
        select(Usuario).where(Usuario.id == credenciales.usuario_id, Usuario.activo.is_(True))
    )
    if usuario is None:
        raise NoAutorizado("La sesión ya no es válida.")
    if usuario.tenant_id != credenciales.tenant_id:
        # The account moved agencies after the token was issued.
        raise NoAutorizado("La sesión ya no corresponde a esta agencia.")
    return usuario


UsuarioActual = Annotated[Usuario, Depends(usuario_actual)]


async def tenant_del_usuario(usuario: UsuarioActual) -> uuid.UUID:
    """The tenant every authenticated query must be scoped by."""
    return usuario.tenant_id


TenantId = Annotated[uuid.UUID, Depends(tenant_del_usuario)]


def requiere_rol(*roles: RolUsuario) -> Callable[..., Awaitable[Usuario]]:
    """Restrict an endpoint to specific roles.

    Administrators pass every check without being listed: an agency with one
    administrator and no manager still needs the management views.
    """
    permitidos = {*roles, RolUsuario.ADMIN}

    async def verificar(usuario: UsuarioActual) -> Usuario:
        if usuario.rol not in permitidos:
            raise SinPermiso(
                "Tu rol no tiene acceso a esta información.",
                rol=usuario.rol.value,
            )
        return usuario

    return verificar


Gerencia = Annotated[Usuario, Depends(requiere_rol(RolUsuario.GERENTE))]
