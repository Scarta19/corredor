"""Tenant isolation, through the real HTTP surface.

ADR-0002 is explicit that a forgotten `tenant_id` filter is a data leak rather
than a bug. These tests are what stands between that statement and a
regression: two agencies, populated, and every CRM surface checked from the
outside.
"""

from __future__ import annotations

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from corredor.domain.catalogo import Ramo
from corredor.domain.enums import Canal
from corredor.domain.tenancy import Tenant
from corredor.scripts.ramos_base import RAMOS_BASE
from corredor.services.solicitudes import registrar_solicitud

from .conftest import _crear_agencia, cabecera_de

pytestmark = pytest.mark.integration


async def _sembrar(
    session: AsyncSession, inquilino: Tenant, ramo: Ramo, nombre: str, documento: str
) -> None:
    await registrar_solicitud(
        session,
        tenant_id=inquilino.id,
        ramo=ramo,
        canal=Canal.WEB,
        respuestas={
            "nombre": nombre,
            "documento": documento,
            "telefono": "+57 3001112233",
            "correo": f"{documento}@prueba.test",
            "ciudad": "Medellín",
            "placa": "abc123",
            "marca": "Mazda",
            "linea": "CX-5",
            "modelo": "2021",
            "uso_vehiculo": "particular",
        },
    )


@pytest.fixture
async def dos_agencias(
    session: AsyncSession, tenant: Tenant, ramos: dict[str, Ramo], cliente_http: AsyncClient
):
    """Two populated agencies and their administrators."""
    otro = Tenant(slug=f"{tenant.slug}-b", nombre="Agencia Vecina")
    session.add(otro)
    await session.flush()
    definicion = next(d for d in RAMOS_BASE if d["codigo"] == "automoviles")
    ramo_otro = Ramo(tenant_id=otro.id, **definicion)
    session.add(ramo_otro)
    await session.flush()

    admin_a = await _crear_agencia(session, tenant)
    admin_b = await _crear_agencia(session, otro)

    await _sembrar(session, tenant, ramos["automoviles"], "Cliente De A", "1111111111")
    await _sembrar(session, otro, ramo_otro, "Cliente De B", "2222222222")

    return {
        "a": (tenant, admin_a),
        "b": (otro, admin_b),
        "http": cliente_http,
    }


class TestAislamiento:
    async def test_cada_agencia_ve_solo_sus_clientes(self, dos_agencias) -> None:
        http = dos_agencias["http"]
        for llave, esperado, prohibido in [
            ("a", "Cliente De A", "Cliente De B"),
            ("b", "Cliente De B", "Cliente De A"),
        ]:
            _, admin = dos_agencias[llave]
            respuesta = await http.get(
                "/api/v1/crm/clientes", headers=await cabecera_de(http, admin)
            )
            nombres = {c["nombre"] for c in respuesta.json()["elementos"]}
            assert esperado in nombres
            assert prohibido not in nombres

    async def test_cada_agencia_ve_solo_sus_solicitudes(self, dos_agencias) -> None:
        http = dos_agencias["http"]
        for llave, esperado in [("a", "Cliente De A"), ("b", "Cliente De B")]:
            _, admin = dos_agencias[llave]
            respuesta = await http.get(
                "/api/v1/crm/solicitudes", headers=await cabecera_de(http, admin)
            )
            datos = respuesta.json()
            assert datos["total"] == 1
            assert datos["elementos"][0]["cliente"]["nombre"] == esperado

    async def test_no_se_puede_abrir_la_ficha_de_un_cliente_ajeno(self, dos_agencias) -> None:
        http = dos_agencias["http"]
        _, admin_a = dos_agencias["a"]
        _, admin_b = dos_agencias["b"]

        de_b = await http.get("/api/v1/crm/clientes", headers=await cabecera_de(http, admin_b))
        id_ajeno = de_b.json()["elementos"][0]["id"]

        respuesta = await http.get(
            f"/api/v1/crm/clientes/{id_ajeno}",
            headers=await cabecera_de(http, admin_a),
        )
        # Not found, not forbidden: confirming the id exists would already
        # leak that another agency holds that client.
        assert respuesta.status_code == 404

    async def test_no_se_puede_mover_una_oportunidad_ajena(self, dos_agencias) -> None:
        http = dos_agencias["http"]
        _, admin_a = dos_agencias["a"]
        _, admin_b = dos_agencias["b"]

        de_b = await http.get("/api/v1/crm/solicitudes", headers=await cabecera_de(http, admin_b))
        oportunidad_ajena = de_b.json()["elementos"][0]["oportunidad_id"]

        respuesta = await http.patch(
            f"/api/v1/crm/oportunidades/{oportunidad_ajena}",
            json={"etapa": "contactado"},
            headers=await cabecera_de(http, admin_a),
        )
        assert respuesta.status_code == 404

    async def test_el_encabezado_de_tenant_no_altera_el_trafico_autenticado(
        self, dos_agencias
    ) -> None:
        """The header is for anonymous traffic only; a token outranks it."""
        http = dos_agencias["http"]
        inquilino_b, _ = dos_agencias["b"]
        _, admin_a = dos_agencias["a"]

        cabeceras = await cabecera_de(http, admin_a)
        cabeceras["X-Tenant"] = inquilino_b.slug

        respuesta = await http.get("/api/v1/crm/clientes", headers=cabeceras)
        nombres = {c["nombre"] for c in respuesta.json()["elementos"]}
        assert nombres == {"Cliente De A"}

    async def test_el_resumen_cuenta_solo_lo_propio(self, dos_agencias) -> None:
        http = dos_agencias["http"]
        for llave in ("a", "b"):
            _, admin = dos_agencias[llave]
            respuesta = await http.get(
                "/api/v1/crm/resumen", headers=await cabecera_de(http, admin)
            )
            assert respuesta.json()["clientes"] == 1


class TestAutenticacion:
    async def test_el_crm_exige_sesion(self, cliente_http: AsyncClient) -> None:
        for ruta in ("/api/v1/crm/resumen", "/api/v1/crm/clientes", "/api/v1/crm/pipeline"):
            assert (await cliente_http.get(ruta)).status_code == 401

    async def test_un_token_invalido_no_sirve(self, cliente_http: AsyncClient) -> None:
        respuesta = await cliente_http.get(
            "/api/v1/crm/resumen", headers={"Authorization": "Bearer no-es-un-token"}
        )
        assert respuesta.status_code == 401

    async def test_la_web_publica_sigue_siendo_anonima(
        self, cliente_http: AsyncClient, tenant: Tenant, ramos: dict[str, Ramo]
    ) -> None:
        respuesta = await cliente_http.get("/api/v1/ramos", headers={"X-Tenant": tenant.slug})
        assert respuesta.status_code == 200
        assert len(respuesta.json()) == len(RAMOS_BASE)


class TestRoles:
    """The dashboard is for management; an advisor's job is the queue."""

    @pytest.fixture
    async def asesor(self, session: AsyncSession, tenant: Tenant):
        from corredor.core.seguridad import hashear_clave
        from corredor.domain.enums import RolUsuario
        from corredor.domain.tenancy import Usuario

        from .conftest import CLAVE

        usuario = Usuario(
            tenant_id=tenant.id,
            nombre="Asesora",
            email=f"asesora-{tenant.slug}@prueba.test",
            password_hash=hashear_clave(CLAVE),
            rol=RolUsuario.ASESOR,
        )
        session.add(usuario)
        await session.flush()
        return usuario

    async def test_un_asesor_no_ve_el_dashboard(self, cliente_http: AsyncClient, asesor) -> None:
        respuesta = await cliente_http.get(
            "/api/v1/crm/dashboard", headers=await cabecera_de(cliente_http, asesor)
        )
        assert respuesta.status_code == 403

    async def test_un_asesor_si_ve_su_cola(self, cliente_http: AsyncClient, asesor) -> None:
        respuesta = await cliente_http.get(
            "/api/v1/crm/solicitudes",
            headers=await cabecera_de(cliente_http, asesor),
        )
        assert respuesta.status_code == 200

    async def test_un_administrador_pasa_el_control_de_gerencia(
        self, cliente_http: AsyncClient, session: AsyncSession, tenant: Tenant
    ) -> None:
        # An agency with one administrator and no manager still needs the
        # management views.
        from .conftest import _crear_agencia

        admin = await _crear_agencia(session, tenant)
        respuesta = await cliente_http.get(
            "/api/v1/crm/dashboard", headers=await cabecera_de(cliente_http, admin)
        )
        assert respuesta.status_code == 200
