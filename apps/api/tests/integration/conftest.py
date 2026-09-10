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
from sqlalchemy.ext.asyncio import AsyncSession

from corredor.db.session import dispose_engine, get_engine
from corredor.domain.catalogo import Ramo
from corredor.domain.tenancy import Tenant
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
