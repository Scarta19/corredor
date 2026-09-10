"""The renewal planner — the awkward cases, which are the ones that matter."""

from __future__ import annotations

from datetime import date, timedelta

import pytest

from corredor.domain.enums import EstadoPoliza, VentanaVencimiento
from corredor.services.renovaciones import (
    UMBRALES_POR_DEFECTO,
    estado_por_vencimiento,
    planificar_acciones,
)

HOY = date(2026, 9, 9)


def _planificar(dias_hasta_vencimiento: int, existentes: list[int] | None = None):
    return planificar_acciones(
        fecha_vencimiento=HOY + timedelta(days=dias_hasta_vencimiento),
        umbrales_existentes=existentes or [],
        hoy=HOY,
    )


class TestPolizaNueva:
    def test_poliza_a_un_anio_programa_los_cuatro_umbrales(self) -> None:
        acciones = _planificar(365)
        assert [a.umbral_dias for a in acciones] == [60, 30, 15, 7]
        assert not any(a.recuperada for a in acciones)

    def test_las_fechas_objetivo_son_el_vencimiento_menos_el_umbral(self) -> None:
        vencimiento = HOY + timedelta(days=365)
        for accion in _planificar(365):
            assert accion.fecha_objetivo == vencimiento - timedelta(days=accion.umbral_dias)

    def test_las_acciones_salen_en_orden_cronologico(self) -> None:
        fechas = [a.fecha_objetivo for a in _planificar(365)]
        assert fechas == sorted(fechas)


class TestIdempotencia:
    def test_no_reprograma_un_umbral_que_ya_existe(self) -> None:
        acciones = _planificar(365, existentes=[60, 30])
        assert [a.umbral_dias for a in acciones] == [15, 7]

    def test_un_segundo_barrido_no_produce_nada(self) -> None:
        primero = _planificar(365)
        segundo = _planificar(365, existentes=[a.umbral_dias for a in primero])
        assert segundo == []

    def test_todos_los_umbrales_cubiertos_no_produce_nada(self) -> None:
        assert _planificar(100, existentes=list(UMBRALES_POR_DEFECTO)) == []


class TestPolizaImportadaTarde:
    """A brokerage's existing book arrives mid-cycle; most thresholds are past."""

    def test_colapsa_los_umbrales_vencidos_en_una_sola_accion(self) -> None:
        # Expires in 20 days: the 60- and 30-day marks have already passed.
        acciones = _planificar(20)
        recuperadas = [a for a in acciones if a.recuperada]
        assert len(recuperadas) == 1, "una póliza importada tarde no debe inundar la cola"
        assert recuperadas[0].umbral_dias == 30, "se recupera el umbral más reciente, no el mayor"

    def test_la_accion_recuperada_se_agenda_para_hoy(self) -> None:
        recuperada = next(a for a in _planificar(20) if a.recuperada)
        assert recuperada.fecha_objetivo == HOY

    def test_los_umbrales_futuros_siguen_programandose_normalmente(self) -> None:
        acciones = _planificar(20)
        futuras = [a.umbral_dias for a in acciones if not a.recuperada]
        assert futuras == [15, 7]

    def test_no_recupera_cuando_ya_hay_gestion_previa(self) -> None:
        # Someone already worked this policy; do not manufacture history.
        acciones = _planificar(20, existentes=[30])
        assert not any(a.recuperada for a in acciones)
        assert [a.umbral_dias for a in acciones] == [15, 7]

    def test_poliza_que_vence_manana_solo_genera_la_recuperacion(self) -> None:
        acciones = _planificar(1)
        assert len(acciones) == 1
        assert acciones[0].umbral_dias == 7
        assert acciones[0].recuperada


class TestPolizaVencida:
    def test_una_poliza_vencida_no_genera_acciones(self) -> None:
        assert _planificar(-1) == []
        assert _planificar(-90) == []

    def test_el_dia_del_vencimiento_todavia_genera_accion(self) -> None:
        acciones = _planificar(0)
        assert len(acciones) == 1
        assert acciones[0].recuperada


class TestUmbralesPersonalizados:
    """§12 says the exact timings are the brokerage's call."""

    def test_respeta_umbrales_configurados(self) -> None:
        acciones = planificar_acciones(
            fecha_vencimiento=HOY + timedelta(days=200),
            umbrales_existentes=[],
            hoy=HOY,
            umbrales=[90, 45],
        )
        assert [a.umbral_dias for a in acciones] == [90, 45]

    def test_sin_umbrales_no_genera_nada(self) -> None:
        assert (
            planificar_acciones(
                fecha_vencimiento=HOY + timedelta(days=200),
                umbrales_existentes=[],
                hoy=HOY,
                umbrales=[],
            )
            == []
        )


class TestEstadoPorVencimiento:
    @pytest.mark.parametrize(
        ("dias", "esperado"),
        [
            (365, EstadoPoliza.VIGENTE),
            (61, EstadoPoliza.VIGENTE),
            (60, EstadoPoliza.PROXIMA_A_VENCER),
            (1, EstadoPoliza.PROXIMA_A_VENCER),
            (0, EstadoPoliza.PROXIMA_A_VENCER),
            (-1, EstadoPoliza.VENCIDA),
        ],
    )
    def test_estado_derivado_del_calendario(self, dias: int, esperado: EstadoPoliza) -> None:
        assert (
            estado_por_vencimiento(fecha_vencimiento=HOY + timedelta(days=dias), hoy=HOY)
            is esperado
        )


class TestVentanaVencimiento:
    """The renewal dashboard buckets of §15."""

    @pytest.mark.parametrize(
        ("dias", "esperado"),
        [
            (-1, VentanaVencimiento.VENCIDA),
            (0, VentanaVencimiento.CRITICA),
            (7, VentanaVencimiento.CRITICA),
            (8, VentanaVencimiento.URGENTE),
            (15, VentanaVencimiento.URGENTE),
            (16, VentanaVencimiento.PROXIMA),
            (30, VentanaVencimiento.PROXIMA),
            (31, VentanaVencimiento.PLANIFICADA),
            (60, VentanaVencimiento.PLANIFICADA),
            (61, VentanaVencimiento.FUTURA),
        ],
    )
    def test_limites_de_cada_bucket(self, dias: int, esperado: VentanaVencimiento) -> None:
        assert VentanaVencimiento.desde_dias(dias) is esperado

    def test_los_buckets_no_dejan_huecos(self) -> None:
        ventanas = {VentanaVencimiento.desde_dias(d) for d in range(-5, 400)}
        assert ventanas == set(VentanaVencimiento)
