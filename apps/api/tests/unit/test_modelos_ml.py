"""The intelligence layer's baselines.

These do not assert exact scores — a baseline is meant to be replaced, and
pinning its arithmetic would make replacing it a chore. They assert the
properties any successor must also satisfy: the ordering is sensible, the
output is a probability, and every score can be explained.
"""

from __future__ import annotations

import pytest

from corredor_ml.cross_sell import PerfilCrossSell, recomendar
from corredor_ml.lead_scoring import LeadFeatures, PuntuadorLeadBaseline
from corredor_ml.renovacion import (
    RenovacionFeatures,
    RiesgoRenovacionBaseline,
    clasificar_nivel,
)


def lead(**cambios: object) -> LeadFeatures:
    base: dict[str, object] = {
        "canal": "web",
        "completitud_formulario": 0.6,
        "tiene_telefono": True,
        "tiene_email": True,
        "es_cliente_existente": False,
    }
    base.update(cambios)
    return LeadFeatures.model_validate(base)


class TestPuntuadorLead:
    def test_el_puntaje_es_una_probabilidad(self) -> None:
        assert 0.0 <= PuntuadorLeadBaseline().predecir(lead()).puntaje <= 1.0

    def test_un_referido_supera_a_un_lead_web(self) -> None:
        modelo = PuntuadorLeadBaseline()
        assert (
            modelo.predecir(lead(canal="referido")).puntaje
            > modelo.predecir(lead(canal="web")).puntaje
        )

    def test_mas_completitud_nunca_baja_el_puntaje(self) -> None:
        modelo = PuntuadorLeadBaseline()
        puntajes = [modelo.predecir(lead(completitud_formulario=c / 10)).puntaje for c in range(11)]
        assert puntajes == sorted(puntajes)

    def test_un_cliente_existente_puntua_mas_alto(self) -> None:
        modelo = PuntuadorLeadBaseline()
        assert (
            modelo.predecir(lead(es_cliente_existente=True, polizas_vigentes=3)).puntaje
            > modelo.predecir(lead()).puntaje
        )

    def test_responder_rapido_supera_a_responder_tarde(self) -> None:
        modelo = PuntuadorLeadBaseline()
        assert (
            modelo.predecir(lead(horas_hasta_primer_contacto=0.5)).puntaje
            > modelo.predecir(lead(horas_hasta_primer_contacto=48)).puntaje
        )

    def test_un_lead_sin_atender_se_penaliza(self) -> None:
        modelo = PuntuadorLeadBaseline()
        assert (
            modelo.predecir(lead(horas_desde_solicitud=48)).puntaje
            < modelo.predecir(lead(horas_desde_solicitud=2)).puntaje
        )

    def test_todo_puntaje_viene_explicado_y_ordenado_por_influencia(self) -> None:
        prediccion = PuntuadorLeadBaseline().predecir(lead(canal="referido"))
        assert prediccion.explicacion
        pesos = [abs(c.peso) for c in prediccion.explicacion]
        assert pesos == sorted(pesos, reverse=True)

    def test_registra_el_modelo_y_la_version(self) -> None:
        prediccion = PuntuadorLeadBaseline().predecir(lead())
        assert prediccion.modelo == "lead_scoring"
        assert prediccion.modelo_version

    def test_rechaza_una_completitud_fuera_de_rango(self) -> None:
        with pytest.raises(ValueError):
            lead(completitud_formulario=1.4)


class TestRiesgoRenovacion:
    def test_un_cliente_fiel_arriesga_menos_que_uno_nuevo_con_alza_de_prima(self) -> None:
        modelo = RiesgoRenovacionBaseline()
        fiel = modelo.predecir(
            RenovacionFeatures(
                dias_para_vencimiento=30,
                renovaciones_previas=4,
                antiguedad_cliente_meses=60,
                otras_polizas_vigentes=3,
            )
        )
        nuevo = modelo.predecir(
            RenovacionFeatures(
                dias_para_vencimiento=30,
                renovaciones_previas=0,
                variacion_prima=0.4,
                dias_desde_ultimo_contacto=300,
            )
        )
        assert fiel.puntaje < nuevo.puntaje

    def test_subir_la_prima_nunca_reduce_el_riesgo(self) -> None:
        modelo = RiesgoRenovacionBaseline()
        puntajes = [
            modelo.predecir(
                RenovacionFeatures(dias_para_vencimiento=30, variacion_prima=v / 10)
            ).puntaje
            for v in range(0, 8)
        ]
        assert puntajes == sorted(puntajes)

    @pytest.mark.parametrize(
        ("probabilidad", "nivel"), [(0.05, "bajo"), (0.45, "medio"), (0.9, "alto")]
    )
    def test_clasificacion_por_nivel(self, probabilidad: float, nivel: str) -> None:
        assert clasificar_nivel(probabilidad) == nivel


class TestCrossSell:
    def test_no_recomienda_un_ramo_que_el_cliente_ya_tiene(self) -> None:
        recomendaciones = recomendar(
            PerfilCrossSell(es_empresa=False, ramos_vigentes=["automoviles", "hogar"])
        )
        assert not {r.ramo for r in recomendaciones} & {"automoviles", "hogar"}

    def test_un_cliente_sin_polizas_ni_senales_no_recibe_nada(self) -> None:
        assert recomendar(PerfilCrossSell(es_empresa=False)) == []

    def test_la_evidencia_repetida_refuerza_pero_no_pasa_de_uno(self) -> None:
        recomendaciones = recomendar(
            PerfilCrossSell(
                es_empresa=True, ramos_vigentes=["cumplimiento", "empresarial", "automoviles"]
            )
        )
        rc = next(r for r in recomendaciones if r.ramo == "responsabilidad_civil")
        assert 0.70 < rc.puntaje <= 1.0

    def test_personas_y_empresas_usan_tablas_distintas(self) -> None:
        persona = {
            r.ramo
            for r in recomendar(PerfilCrossSell(es_empresa=False, ramos_vigentes=["automoviles"]))
        }
        empresa = {
            r.ramo
            for r in recomendar(PerfilCrossSell(es_empresa=True, ramos_vigentes=["automoviles"]))
        }
        assert persona != empresa

    def test_respeta_el_limite_solicitado(self) -> None:
        recomendaciones = recomendar(
            PerfilCrossSell(es_empresa=True, ramos_vigentes=["empresarial"]), limite=2
        )
        assert len(recomendaciones) <= 2

    def test_el_ranking_viene_ordenado_de_mayor_a_menor(self) -> None:
        puntajes = [
            r.puntaje
            for r in recomendar(
                PerfilCrossSell(es_empresa=True, ramos_vigentes=["cumplimiento", "empresarial"])
            )
        ]
        assert puntajes == sorted(puntajes, reverse=True)

    def test_toda_recomendacion_trae_una_razon_para_el_asesor(self) -> None:
        for r in recomendar(PerfilCrossSell(es_empresa=False, ramos_vigentes=["hogar"])):
            assert r.razon.strip()

    def test_una_senal_declarada_genera_recomendacion_sin_polizas(self) -> None:
        recomendaciones = recomendar(PerfilCrossSell(es_empresa=False, tiene_vivienda_propia=True))
        assert [r.ramo for r in recomendaciones] == ["hogar"]
