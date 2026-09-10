"""Fixtures for tests that need a real Postgres.

Each test runs inside a transaction that is rolled back afterwards, so tests
share one migrated database without sharing state and without a truncate step
between them.

Run `make up && make migrate` first, or let CI's Postgres service provide it.
"""

from __future__ import annotations

import uuid
from collections.abc import AsyncIterator

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from corredor.core.seguridad import hashear_clave
from corredor.db.session import dispose_engine, get_engine, get_session
from corredor.domain.catalogo import Ramo
from corredor.domain.enums import RolUsuario
from corredor.domain.tenancy import Tenant, Usuario
from corredor.main import create_app
from corredor.scripts.ramos_base import RAMOS_BASE

pytestmark = pytest.mark.integration


@pytest.fixture(scope="session")
async def engine() -> AsyncIterator[object]:
    motor = get_engine()
    yield motor
    await dispose_engine()


@pytest.fixture
async def session(engine: object) -> AsyncIterator[AsyncSession]:
    """A session whose work is always rolled back."""
    async with get_engine().connect() as conexion:
        transaccion = await conexion.begin()
        sesion = AsyncSession(bind=conexion, expire_on_commit=False)
        try:
            yield sesion
        finally:
            await sesion.close()
            await transaccion.rollback()


@pytest.fixture
async def tenant(session: AsyncSession) -> Tenant:
    """A tenant unique to this test, so parallel runs cannot collide."""
    inquilino = Tenant(
        slug=f"prueba-{uuid.uuid4().hex[:10]}",
        nombre="Agencia de Prueba",
        ciudad="Medellín",
    )
    session.add(inquilino)
    await session.flush()
    return inquilino


@pytest.fixture
async def ramos(session: AsyncSession, tenant: Tenant) -> dict[str, Ramo]:
    """The shipped catalogue, loaded for this tenant."""
    catalogo: dict[str, Ramo] = {}
    for definicion in RAMOS_BASE:
        ramo = Ramo(tenant_id=tenant.id, **definicion)
        session.add(ramo)
        catalogo[ramo.codigo] = ramo
    await session.flush()
    return catalogo


@pytest.fixture
async def cliente_http(session: AsyncSession) -> AsyncIterator[AsyncClient]:
    """An HTTP client wired to the test's transactional session.

    Overriding `get_session` is what lets a request go through the real
    routing, dependencies and serialisation while still rolling back.
    """
    app = create_app()

    async def sesion_de_prueba() -> AsyncIterator[AsyncSession]:
        yield session

    app.dependency_overrides[get_session] = sesion_de_prueba
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://prueba") as cliente:
        yield cliente
    app.dependency_overrides.clear()


CLAVE = "clave-de-prueba-suficientemente-larga"


@pytest.fixture
async def agencia(session: AsyncSession, tenant: Tenant, ramos: dict[str, Ramo]):
    """A tenant with an administrator, ready to sign in."""
    return await _crear_agencia(session, tenant)


async def _crear_agencia(session: AsyncSession, inquilino: Tenant) -> Usuario:
    usuario = Usuario(
        tenant_id=inquilino.id,
        nombre="Administradora",
        email=f"admin-{inquilino.slug}@prueba.test",
        password_hash=hashear_clave(CLAVE),
        rol=RolUsuario.ADMIN,
    )
    session.add(usuario)
    await session.flush()
    return usuario


async def token_de(cliente: AsyncClient, usuario: Usuario) -> str:
    respuesta = await cliente.post(
        "/api/v1/auth/login",
        data={"username": usuario.email, "password": CLAVE},
    )
    assert respuesta.status_code == 200, respuesta.text
    return str(respuesta.json()["access_token"])


async def cabecera_de(cliente: AsyncClient, usuario: Usuario) -> dict[str, str]:
    return {"Authorization": f"Bearer {await token_de(cliente, usuario)}"}
