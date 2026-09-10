"""The nightly sweep, against a real database.

The unit tests in `test_renovaciones.py` prove the planning rules. These prove
the thing that actually runs them: that a sweep can be repeated, interrupted
or delayed without duplicating a task or re-contacting a client.
"""

from __future__ import annotations

from datetime import date, timedelta
from decimal import Decimal

import pytest
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from corredor.domain.catalogo import Aseguradora, Ramo
from corredor.domain.clientes import Cliente
from corredor.domain.enums import EstadoPoliza, EstadoRenovacion, TipoCliente
from corredor.domain.inteligencia import RiesgoRenovacion
from corredor.domain.polizas import Poliza, Renovacion
from corredor.domain.tenancy import Tenant
from corredor.services.renovaciones import barrer_renovaciones
from corredor.services.riesgo import calcular_riesgo, construir_features

pytestmark = pytest.mark.integration

HOY = date(2026, 9, 10)


@pytest.fixture
async def cartera(session: AsyncSession, tenant: Tenant, ramos: dict[str, Ramo]):
    """A client with policies spread across the renewal buckets."""
    aseguradora = Aseguradora(tenant_id=tenant.id, nombre="Aseguradora de Prueba")
    cliente = Cliente(
        tenant_id=tenant.id,
        tipo=TipoCliente.PERSONA,
        nombre="Cliente Con Cartera",
        documento="1234567890",
    )
    session.add_all([aseguradora, cliente])
    await session.flush()

    polizas = []
    for dias in (5, 20, 45, 200, -30):
        vencimiento = HOY + timedelta(days=dias)
        poliza = Poliza(
            tenant_id=tenant.id,
            numero=f"POL-{dias}",
            cliente_id=cliente.id,
            ramo_id=ramos["automoviles"].id,
            aseguradora_id=aseguradora.id,
            fecha_inicio=vencimiento - timedelta(days=365),
            fecha_vencimiento=vencimiento,
            prima=Decimal("1200000"),
            estado=EstadoPoliza.VIGENTE if dias >= 0 else EstadoPoliza.VENCIDA,
        )
        session.add(poliza)
        polizas.append(poliza)
    await session.flush()
    return {"cliente": cliente, "polizas": polizas, "aseguradora": aseguradora}


async def _contar_renovaciones(session: AsyncSession, tenant: Tenant) -> int:
    return (
        await session.scalar(
            select(func.count()).select_from(Renovacion).where(Renovacion.tenant_id == tenant.id)
        )
    ) or 0


class TestBarrido:
    async def test_programa_acciones_para_las_polizas_vigentes(
        self, session: AsyncSession, tenant: Tenant, cartera
    ) -> None:
        resultado = await barrer_renovaciones(session, tenant_id=tenant.id, hoy=HOY)
        assert resultado.acciones_creadas > 0
        assert await _contar_renovaciones(session, tenant) == resultado.acciones_creadas

    async def test_es_idempotente(self, session: AsyncSession, tenant: Tenant, cartera) -> None:
        primero = await barrer_renovaciones(session, tenant_id=tenant.id, hoy=HOY)
        total = await _contar_renovaciones(session, tenant)

        segundo = await barrer_renovaciones(session, tenant_id=tenant.id, hoy=HOY)

        assert primero.acciones_creadas > 0
        assert segundo.acciones_creadas == 0, "un segundo barrido no debe duplicar nada"
        assert await _contar_renovaciones(session, tenant) == total

    async def test_una_caida_de_una_semana_se_recupera_sin_duplicar(
        self, session: AsyncSession, tenant: Tenant, cartera
    ) -> None:
        await barrer_renovaciones(session, tenant_id=tenant.id, hoy=HOY)
        total_inicial = await _contar_renovaciones(session, tenant)

        # The cron did not run for a week; the next sweep must catch up.
        await barrer_renovaciones(session, tenant_id=tenant.id, hoy=HOY + timedelta(days=7))
        total_final = await _contar_renovaciones(session, tenant)

        assert total_final >= total_inicial
        duplicados = await session.execute(
            select(Renovacion.poliza_id, Renovacion.umbral_dias, func.count())
            .where(Renovacion.tenant_id == tenant.id)
            .group_by(Renovacion.poliza_id, Renovacion.umbral_dias)
            .having(func.count() > 1)
        )
        assert duplicados.all() == [], "ninguna póliza puede repetir un umbral"

    async def test_no_agenda_nada_para_una_poliza_vencida(
        self, session: AsyncSession, tenant: Tenant, cartera
    ) -> None:
        await barrer_renovaciones(session, tenant_id=tenant.id, hoy=HOY)
        vencida = next(p for p in cartera["polizas"] if p.numero == "POL--30")
        total = await session.scalar(
            select(func.count()).select_from(Renovacion).where(Renovacion.poliza_id == vencida.id)
        )
        assert total == 0

    async def test_actualiza_el_estado_segun_el_calendario(
        self, session: AsyncSession, tenant: Tenant, cartera
    ) -> None:
        await barrer_renovaciones(session, tenant_id=tenant.id, hoy=HOY)
        for poliza in cartera["polizas"]:
            await session.refresh(poliza)
        estados = {p.numero: p.estado for p in cartera["polizas"]}

        assert estados["POL-5"] is EstadoPoliza.PROXIMA_A_VENCER
        assert estados["POL-45"] is EstadoPoliza.PROXIMA_A_VENCER
        assert estados["POL-200"] is EstadoPoliza.VIGENTE

    async def test_las_acciones_nacen_pendientes_y_con_fecha(
        self, session: AsyncSession, tenant: Tenant, cartera
    ) -> None:
        await barrer_renovaciones(session, tenant_id=tenant.id, hoy=HOY)
        acciones = (
            await session.scalars(select(Renovacion).where(Renovacion.tenant_id == tenant.id))
        ).all()
        assert acciones
        assert all(a.estado is EstadoRenovacion.PENDIENTE for a in acciones)
        assert all(a.fecha_objetivo is not None for a in acciones)


class TestRiesgo:
    async def test_calcula_y_guarda_con_procedencia(
        self, session: AsyncSession, tenant: Tenant, cartera
    ) -> None:
        poliza = next(p for p in cartera["polizas"] if p.numero == "POL-45")
        riesgo = await calcular_riesgo(session, poliza=poliza, hoy=HOY)
        await session.flush()

        assert 0.0 <= riesgo.probabilidad_fuga <= 1.0
        assert riesgo.modelo_version, "una predicción sin versión no es auditable"
        assert riesgo.features, "sin variables no se puede reproducir ni reentrenar"
        assert riesgo.explicacion

    async def test_las_features_salen_de_datos_que_ya_existen(
        self, session: AsyncSession, tenant: Tenant, cartera
    ) -> None:
        poliza = next(p for p in cartera["polizas"] if p.numero == "POL-45")
        features = await construir_features(session, poliza=poliza, hoy=HOY)

        assert features.dias_para_vencimiento == 45
        # Four other live policies belong to the same client.
        assert features.otras_polizas_vigentes >= 1
        assert features.renovaciones_previas == 0
        assert features.dias_desde_ultimo_contacto is None

    async def test_una_cadena_de_renovaciones_cuenta_como_lealtad(
        self, session: AsyncSession, tenant: Tenant, cartera
    ) -> None:
        anterior = cartera["polizas"][0]
        actual = Poliza(
            tenant_id=tenant.id,
            numero="POL-RENOVADA",
            cliente_id=cartera["cliente"].id,
            ramo_id=anterior.ramo_id,
            aseguradora_id=anterior.aseguradora_id,
            fecha_inicio=HOY,
            fecha_vencimiento=HOY + timedelta(days=365),
            prima=Decimal("1300000"),
            poliza_anterior_id=anterior.id,
        )
        session.add(actual)
        await session.flush()

        features = await construir_features(session, poliza=actual, hoy=HOY)
        assert features.renovaciones_previas == 1
        # 1.3M from 1.2M is roughly an 8% increase.
        assert 0.07 < features.variacion_prima < 0.09

    async def test_un_puntaje_por_corrida_deja_historial(
        self, session: AsyncSession, tenant: Tenant, cartera
    ) -> None:
        poliza = next(p for p in cartera["polizas"] if p.numero == "POL-45")
        await calcular_riesgo(session, poliza=poliza, hoy=HOY)
        await calcular_riesgo(session, poliza=poliza, hoy=HOY + timedelta(days=1))
        await session.flush()

        total = await session.scalar(
            select(func.count())
            .select_from(RiesgoRenovacion)
            .where(RiesgoRenovacion.poliza_id == poliza.id)
        )
        # Scores accumulate rather than overwrite: a prediction is a record.
        assert total == 2
