"""Shared FastAPI dependencies."""

from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import Depends, Header
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from corredor.core.errors import NoEncontrado
from corredor.db.session import get_session
from corredor.domain.tenancy import Tenant

Sesion = Annotated[AsyncSession, Depends(get_session)]


async def resolver_tenant(
    session: Sesion,
    x_tenant: Annotated[str | None, Header(alias="X-Tenant")] = None,
) -> Tenant:
    """Resolve the tenant for a public request.

    Public traffic carries no credentials, so the tenant comes from the
    `X-Tenant` slug that the site's own frontend sets. Authenticated CRM
    requests take it from the token instead — never from a header a browser
    controls.
    """
    slug = x_tenant or "demo"
    tenant = await session.scalar(
        select(Tenant).where(Tenant.slug == slug, Tenant.activo.is_(True))
    )
    if tenant is None:
        raise NoEncontrado(f"No existe una agencia activa con el identificador '{slug}'.")
    return tenant


TenantActual = Annotated[Tenant, Depends(resolver_tenant)]


def tenant_id_de(tenant: Tenant) -> uuid.UUID:
    return tenant.id
