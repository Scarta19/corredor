"""Validation of the dynamic quote-form schema (Módulo 2).

A malformed form definition must fail loudly at write time. If it reaches the
public site, the visitor sees a broken quote flow and the brokerage loses the
lead without ever knowing it existed.
"""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from corredor.domain.formularios import CampoFormulario, FormularioRamo
from corredor.scripts.ramos_base import RAMOS_BASE


def campo(nombre: str, **extra: object) -> dict[str, object]:
    base: dict[str, object] = {"nombre": nombre, "etiqueta": nombre.title(), "tipo": "texto"}
    base.update(extra)
    return base


class TestCampo:
    def test_un_campo_de_seleccion_exige_opciones(self) -> None:
        with pytest.raises(ValidationError, match="requiere opciones"):
            CampoFormulario.model_validate(campo("uso", tipo="seleccion"))

    def test_un_campo_de_texto_rechaza_opciones(self) -> None:
        with pytest.raises(ValidationError, match="no admite opciones"):
            CampoFormulario.model_validate(
                campo("ciudad", opciones=[{"valor": "a", "etiqueta": "A"}])
            )

    def test_valores_condicionales_exigen_un_campo_del_que_depender(self) -> None:
        with pytest.raises(ValidationError, match="sin 'depende_de'"):
            CampoFormulario.model_validate(campo("valor", depende_de_valores=["true"]))

    @pytest.mark.parametrize("nombre", ["Placa", "1placa", "placa-vehiculo", "", "a" * 60])
    def test_rechaza_nombres_que_no_son_identificadores(self, nombre: str) -> None:
        with pytest.raises(ValidationError):
            CampoFormulario.model_validate(campo(nombre))

    def test_rechaza_atributos_desconocidos(self) -> None:
        with pytest.raises(ValidationError):
            CampoFormulario.model_validate(campo("placa", obligatorio=True))


class TestFormulario:
    def test_rechaza_campos_duplicados(self) -> None:
        with pytest.raises(ValidationError, match="campos duplicados"):
            FormularioRamo.model_validate({"campos": [campo("placa"), campo("placa")]})

    def test_rechaza_una_dependencia_hacia_un_campo_inexistente(self) -> None:
        with pytest.raises(ValidationError, match="no existe"):
            FormularioRamo.model_validate({"campos": [campo("valor", depende_de="es_propietario")]})

    def test_rechaza_un_formulario_vacio(self) -> None:
        with pytest.raises(ValidationError):
            FormularioRamo.model_validate({"campos": []})

    def test_ordena_por_orden_y_luego_por_nombre(self) -> None:
        form = FormularioRamo.model_validate(
            {
                "campos": [
                    campo("zeta", orden=2),
                    campo("beta", orden=1),
                    campo("alfa", orden=1),
                ]
            }
        )
        assert [c.nombre for c in form.campos_ordenados] == ["alfa", "beta", "zeta"]

    def test_los_campos_condicionales_no_cuentan_como_requeridos(self) -> None:
        form = FormularioRamo.model_validate(
            {
                "campos": [
                    campo("es_propietario", tipo="booleano"),
                    campo("valor", depende_de="es_propietario", depende_de_valores=["true"]),
                ]
            }
        )
        assert form.campos_requeridos == ["es_propietario"]


class TestCatalogoBase:
    """Every shipped ramo must be usable the moment a tenant is created."""

    @pytest.mark.parametrize("definicion", RAMOS_BASE, ids=lambda d: str(d["codigo"]))
    def test_el_formulario_del_ramo_es_valido(self, definicion: dict[str, object]) -> None:
        form = FormularioRamo.model_validate(definicion["formulario"])
        assert form.campos

    def test_todos_piden_como_minimo_un_medio_de_contacto(self) -> None:
        for definicion in RAMOS_BASE:
            nombres = {
                c.nombre for c in FormularioRamo.model_validate(definicion["formulario"]).campos
            }
            assert {"telefono", "correo"} <= nombres, definicion["codigo"]

    def test_automoviles_pide_exactamente_los_campos_del_brief(self) -> None:
        # §5 of the platform brief lists these by name.
        auto = next(d for d in RAMOS_BASE if d["codigo"] == "automoviles")
        nombres = {c.nombre for c in FormularioRamo.model_validate(auto["formulario"]).campos}
        assert nombres == {
            "nombre",
            "documento",
            "telefono",
            "correo",
            "ciudad",
            "placa",
            "marca",
            "linea",
            "modelo",
            "uso_vehiculo",
        }

    def test_los_codigos_de_ramo_son_unicos(self) -> None:
        codigos = [d["codigo"] for d in RAMOS_BASE]
        assert len(codigos) == len(set(codigos))
