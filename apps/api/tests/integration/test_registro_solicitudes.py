"""One submission must produce a complete, consistent CRM state — or none.

§5 of the platform brief exists to stop information arriving as a message
somebody has to retype. That only holds if the request, the client, the
opportunity, its first event and the lead score are created together.
"""

from __future__ import annotations

import pytest
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from corredor.domain.catalogo import Ramo
from corredor.domain.clientes import Cliente
from corredor.domain.comercial import Oportunidad, OportunidadEvento, Solicitud
from corredor.domain.enums import (
    Canal,
    EstadoSolicitud,
    EtapaOportunidad,
    TipoCliente,
)
from corredor.domain.inteligencia import PuntajeLead
from corredor.domain.tenancy import Tenant
from corredor.domain.validacion import ErroresDeFormulario
from corredor.scripts.ramos_base import RAMOS_BASE
from corredor.services.solicitudes import registrar_solicitud

pytestmark = pytest.mark.integration

RESPUESTAS_AUTO = {
    "nombre": "Ana Restrepo",
    "documento": "1098765432",
    "telefono": "+57 3009998877",
    "correo": "ana@test.co",
    "ciudad": "Medellín",
    "placa": "xyz987",
    "marca": "Renault",
    "linea": "Duster",
    "modelo": "2022",
    "uso_vehiculo": "particular",
}


async def registrar(
    session: AsyncSession,
    tenant: Tenant,
    ramo: Ramo,
    respuestas: dict[str, object] | None = None,
) -> Solicitud:
    return await registrar_solicitud(
        session,
        tenant_id=tenant.id,
        ramo=ramo,
        canal=Canal.WEB,
        respuestas=respuestas or dict(RESPUESTAS_AUTO),
    )


class TestRegistroCompleto:
    async def test_crea_la_cadena_completa(
        self, session: AsyncSession, tenant: Tenant, ramos: dict[str, Ramo]
    ) -> None:
        solicitud = await registrar(session, tenant, ramos["automoviles"])

        assert solicitud.estado is EstadoSolicitud.NUEVA
        assert solicitud.codigo.startswith("COT-")

        oportunidad = await session.scalar(
            select(Oportunidad).where(Oportunidad.solicitud_id == solicitud.id)
        )
        assert oportunidad is not None
        assert oportunidad.etapa is EtapaOportunidad.NUEVO

        eventos = (
            await session.scalars(
                select(OportunidadEvento).where(OportunidadEvento.oportunidad_id == oportunidad.id)
            )
        ).all()
        assert len(eventos) == 1
        assert eventos[0].etapa_anterior is None
        assert eventos[0].automatico is True

        puntaje = await session.scalar(
            select(PuntajeLead).where(PuntajeLead.oportunidad_id == oportunidad.id)
        )
        assert puntaje is not None
        assert 0.0 <= puntaje.puntaje <= 1.0
        assert puntaje.modelo_version, "una predicción sin versión no es auditable"
        assert puntaje.explicacion, "un puntaje sin explicación no es discutible"

    async def test_normaliza_lo_que_guarda(
        self, session: AsyncSession, tenant: Tenant, ramos: dict[str, Ramo]
    ) -> None:
        solicitud = await registrar(
            session,
            tenant,
            ramos["automoviles"],
            {**RESPUESTAS_AUTO, "placa": "xyz-987", "correo": "ANA@TEST.CO"},
        )
        assert solicitud.respuestas["placa"] == "XYZ987"
        assert solicitud.respuestas["correo"] == "ana@test.co"

    async def test_registra_la_version_del_formulario(
        self, session: AsyncSession, tenant: Tenant, ramos: dict[str, Ramo]
    ) -> None:
        # Without this, a request captured today becomes uninterpretable the
        # first time the brokerage edits its form.
        solicitud = await registrar(session, tenant, ramos["automoviles"])
        assert solicitud.formulario_version == ramos["automoviles"].form.version


class TestConsecutivos:
    async def test_los_codigos_avanzan_sin_repetirse(
        self, session: AsyncSession, tenant: Tenant, ramos: dict[str, Ramo]
    ) -> None:
        codigos = [
            (await registrar(session, tenant, ramos["automoviles"])).codigo for _ in range(3)
        ]
        assert codigos == ["COT-000001", "COT-000002", "COT-000003"]

    async def test_cada_tenant_lleva_su_propia_numeracion(
        self, session: AsyncSession, tenant: Tenant, ramos: dict[str, Ramo]
    ) -> None:
        """Two brokerages both start at COT-000001 and never see each other's."""
        await registrar(session, tenant, ramos["automoviles"])
        await registrar(session, tenant, ramos["automoviles"])

        otro = Tenant(slug=f"{tenant.slug}-b", nombre="Otra Agencia")
        session.add(otro)
        await session.flush()
        definicion = next(d for d in RAMOS_BASE if d["codigo"] == "automoviles")
        ramo_otro = Ramo(tenant_id=otro.id, **definicion)
        session.add(ramo_otro)
        await session.flush()

        primera_del_otro = await registrar(session, otro, ramo_otro)
        assert primera_del_otro.codigo == "COT-000001"

        siguiente_del_primero = await registrar(session, tenant, ramos["automoviles"])
        assert siguiente_del_primero.codigo == "COT-000003"


class TestClienteRecurrente:
    async def test_reutiliza_el_cliente_por_documento(
        self, session: AsyncSession, tenant: Tenant, ramos: dict[str, Ramo]
    ) -> None:
        await registrar(session, tenant, ramos["automoviles"])
        await registrar(
            session,
            tenant,
            ramos["hogar"],
            {
                "nombre": "Ana Restrepo",
                "documento": "1098765432",
                "telefono": "+57 3009998877",
                "correo": "ana@test.co",
                "ciudad": "Medellín",
                "tipo_vivienda": "apartamento",
                "es_propietario": True,
                "valor_inmueble": "350000000",
            },
        )
        total = await session.scalar(
            select(func.count()).select_from(Cliente).where(Cliente.tenant_id == tenant.id)
        )
        assert total == 1, "un cliente que vuelve no debe duplicarse"

    async def test_un_cliente_conocido_puntua_mas_alto(
        self, session: AsyncSession, tenant: Tenant, ramos: dict[str, Ramo]
    ) -> None:
        primera = await registrar(session, tenant, ramos["automoviles"])
        segunda = await registrar(session, tenant, ramos["automoviles"])

        puntajes = {}
        for solicitud in (primera, segunda):
            oportunidad = await session.scalar(
                select(Oportunidad).where(Oportunidad.solicitud_id == solicitud.id)
            )
            assert oportunidad is not None
            puntaje = await session.scalar(
                select(PuntajeLead).where(PuntajeLead.oportunidad_id == oportunidad.id)
            )
            assert puntaje is not None
            puntajes[solicitud.codigo] = puntaje.puntaje

        assert puntajes[segunda.codigo] > puntajes[primera.codigo]

    async def test_completa_los_huecos_del_cliente_existente(
        self, session: AsyncSession, tenant: Tenant, ramos: dict[str, Ramo]
    ) -> None:
        """A returning client often arrives with details we never had."""
        cliente = Cliente(
            tenant_id=tenant.id,
            tipo=TipoCliente.PERSONA,
            nombre="Ana Restrepo",
            documento="1098765432",
            telefono=None,
            email=None,
            ciudad=None,
        )
        session.add(cliente)
        await session.flush()

        await registrar(session, tenant, ramos["automoviles"])

        await session.refresh(cliente)
        assert cliente.email == "ana@test.co"
        assert cliente.telefono == "+57 3009998877"
        assert cliente.ciudad == "Medellín"

    async def test_no_pisa_los_datos_que_ya_tenia(
        self, session: AsyncSession, tenant: Tenant, ramos: dict[str, Ramo]
    ) -> None:
        """An advisor's correction outranks whatever a web form says."""
        cliente = Cliente(
            tenant_id=tenant.id,
            tipo=TipoCliente.PERSONA,
            nombre="Ana Restrepo",
            documento="1098765432",
            email="corregido-por-el-asesor@test.co",
            ciudad="Bogotá",
        )
        session.add(cliente)
        await session.flush()

        await registrar(session, tenant, ramos["automoviles"])

        await session.refresh(cliente)
        assert cliente.email == "corregido-por-el-asesor@test.co"
        assert cliente.ciudad == "Bogotá"


class TestAtomicidad:
    async def test_un_formulario_invalido_no_escribe_nada(
        self, session: AsyncSession, tenant: Tenant, ramos: dict[str, Ramo]
    ) -> None:
        with pytest.raises(ErroresDeFormulario):
            await registrar(session, tenant, ramos["automoviles"], {"nombre": "Ana"})

        for modelo in (Cliente, Solicitud, Oportunidad):
            total = await session.scalar(
                select(func.count()).select_from(modelo).where(modelo.tenant_id == tenant.id)
            )
            assert total == 0, f"{modelo.__name__} no debía crearse"
