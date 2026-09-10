"""Validating answers against a runtime-defined form.

The form schema is data, so Postgres and Pydantic cannot check a submission
for us. These tests are the safety net that replaces them.
"""

from __future__ import annotations

import pytest

from corredor.domain.formularios import FormularioRamo
from corredor.domain.validacion import (
    ErroresDeFormulario,
    campo_esta_activo,
    completitud,
    validar_respuestas,
)
from corredor.scripts.ramos_base import RAMOS_BASE


def form(*campos: dict[str, object]) -> FormularioRamo:
    return FormularioRamo.model_validate({"campos": list(campos)})


def campo(nombre: str, tipo: str = "texto", **extra: object) -> dict[str, object]:
    return {"nombre": nombre, "etiqueta": nombre, "tipo": tipo, **extra}


def errores_de(formulario: FormularioRamo, respuestas: dict[str, object]) -> dict[str, str]:
    with pytest.raises(ErroresDeFormulario) as excinfo:
        validar_respuestas(formulario, respuestas)
    return dict(excinfo.value.contexto["errores"])


class TestObligatoriedad:
    def test_un_campo_requerido_ausente_es_error(self) -> None:
        assert "nombre" in errores_de(form(campo("nombre")), {})

    def test_una_cadena_en_blanco_cuenta_como_ausente(self) -> None:
        assert "nombre" in errores_de(form(campo("nombre")), {"nombre": "   "})

    def test_un_campo_opcional_ausente_no_es_error(self) -> None:
        limpio = validar_respuestas(form(campo("notas", requerido=False)), {})
        assert limpio == {}

    def test_reporta_todos_los_errores_de_una_vez(self) -> None:
        # A form that surfaces one error per submission is a form people
        # abandon.
        errores = errores_de(form(campo("a"), campo("b"), campo("c")), {})
        assert set(errores) == {"a", "b", "c"}


class TestCamposDesconocidos:
    def test_rechaza_un_campo_que_no_existe(self) -> None:
        errores = errores_de(form(campo("nombre")), {"nombre": "Ana", "otro": "x"})
        assert "otro" in errores


class TestNormalizacion:
    def test_recorta_espacios(self) -> None:
        limpio = validar_respuestas(form(campo("nombre")), {"nombre": "  Ana  "})
        assert limpio["nombre"] == "Ana"

    def test_el_correo_queda_en_minusculas(self) -> None:
        limpio = validar_respuestas(form(campo("correo", "email")), {"correo": "Ana@Test.CO"})
        assert limpio["correo"] == "ana@test.co"

    def test_la_placa_se_normaliza_a_mayusculas_sin_guiones(self) -> None:
        limpio = validar_respuestas(form(campo("placa", "placa")), {"placa": "abc-123"})
        assert limpio["placa"] == "ABC123"

    def test_un_entero_llega_como_int_aunque_venga_como_texto(self) -> None:
        limpio = validar_respuestas(form(campo("modelo", "entero")), {"modelo": "2021"})
        assert limpio["modelo"] == 2021

    def test_un_numero_admite_separadores_de_miles(self) -> None:
        limpio = validar_respuestas(form(campo("valor", "numero")), {"valor": "350,000,000"})
        assert limpio["valor"] == 350_000_000.0

    def test_una_fecha_se_guarda_en_iso(self) -> None:
        limpio = validar_respuestas(
            form(campo("nacimiento", "fecha")), {"nacimiento": "1990-05-04"}
        )
        assert limpio["nacimiento"] == "1990-05-04"


class TestTipos:
    @pytest.mark.parametrize(
        ("tipo", "valor"),
        [
            ("email", "sin-arroba"),
            ("email", "a@b"),
            ("telefono", "abc"),
            ("telefono", "12345"),
            ("documento", "123"),
            ("placa", "!!"),
            ("entero", "dos mil"),
            ("numero", "muchos"),
            ("fecha", "04/05/1990"),
        ],
    )
    def test_valores_invalidos_son_rechazados(self, tipo: str, valor: str) -> None:
        assert "x" in errores_de(form(campo("x", tipo)), {"x": valor})

    def test_un_numero_negativo_es_rechazado(self) -> None:
        assert "x" in errores_de(form(campo("x", "numero")), {"x": "-5"})

    @pytest.mark.parametrize(
        ("entrada", "esperado"),
        [("true", True), ("sí", True), ("1", True), ("no", False), ("false", False)],
    )
    def test_booleanos_aceptan_las_formas_que_la_gente_escribe(
        self, entrada: str, esperado: bool
    ) -> None:
        limpio = validar_respuestas(form(campo("x", "booleano")), {"x": entrada})
        assert limpio["x"] is esperado

    def test_un_booleano_ambiguo_es_rechazado(self) -> None:
        assert "x" in errores_de(form(campo("x", "booleano")), {"x": "quizás"})


class TestSelecciones:
    def seleccion(self) -> FormularioRamo:
        return form(
            campo(
                "uso",
                "seleccion",
                opciones=[
                    {"valor": "particular", "etiqueta": "Particular"},
                    {"valor": "publico", "etiqueta": "Público"},
                ],
            )
        )

    def test_acepta_una_opcion_valida(self) -> None:
        limpio = validar_respuestas(self.seleccion(), {"uso": "particular"})
        assert limpio["uso"] == "particular"

    def test_rechaza_un_valor_fuera_del_catalogo(self) -> None:
        # The options are the contract; a client that invents a value is
        # either broken or hostile.
        assert "uso" in errores_de(self.seleccion(), {"uso": "carga"})

    def test_rechaza_la_etiqueta_en_lugar_del_valor(self) -> None:
        assert "uso" in errores_de(self.seleccion(), {"uso": "Particular"})

    def multi(self) -> FormularioRamo:
        return form(
            campo(
                "coberturas",
                "multiseleccion",
                opciones=[
                    {"valor": "incendio", "etiqueta": "Incendio"},
                    {"valor": "robo", "etiqueta": "Robo"},
                ],
            )
        )

    def test_multiseleccion_acepta_varias_opciones(self) -> None:
        limpio = validar_respuestas(self.multi(), {"coberturas": ["incendio", "robo"]})
        assert limpio["coberturas"] == ["incendio", "robo"]

    def test_multiseleccion_rechaza_un_valor_suelto(self) -> None:
        assert "coberturas" in errores_de(self.multi(), {"coberturas": "incendio"})

    def test_multiseleccion_rechaza_repetidos(self) -> None:
        assert "coberturas" in errores_de(self.multi(), {"coberturas": ["robo", "robo"]})


class TestCamposCondicionales:
    def condicional(self) -> FormularioRamo:
        return form(
            campo("es_propietario", "booleano"),
            campo(
                "valor_inmueble",
                "numero",
                depende_de="es_propietario",
                depende_de_valores=["true"],
            ),
        )

    def test_se_exige_cuando_la_condicion_se_cumple(self) -> None:
        errores = errores_de(self.condicional(), {"es_propietario": True})
        assert "valor_inmueble" in errores

    def test_no_se_exige_cuando_la_condicion_no_se_cumple(self) -> None:
        limpio = validar_respuestas(self.condicional(), {"es_propietario": False})
        assert limpio == {"es_propietario": False}

    def test_enviarlo_cuando_no_aplica_es_un_error(self) -> None:
        errores = errores_de(self.condicional(), {"es_propietario": False, "valor_inmueble": "100"})
        assert "valor_inmueble" in errores

    def test_campo_esta_activo_refleja_la_dependencia(self) -> None:
        formulario = self.condicional()
        condicional = next(c for c in formulario.campos if c.nombre == "valor_inmueble")
        assert campo_esta_activo(condicional, {"es_propietario": True})
        assert not campo_esta_activo(condicional, {"es_propietario": False})
        assert not campo_esta_activo(condicional, {})


class TestCompletitud:
    def test_un_formulario_lleno_da_uno(self) -> None:
        formulario = form(campo("a"), campo("b"))
        assert completitud(formulario, {"a": "1", "b": "2"}) == 1.0

    def test_un_formulario_vacio_da_cero(self) -> None:
        assert completitud(form(campo("a"), campo("b")), {}) == 0.0

    def test_los_campos_que_no_aplican_no_penalizan(self) -> None:
        # Someone who is not a homeowner has answered everything asked of
        # them; the hidden field must not count against their score.
        formulario = form(
            campo("es_propietario", "booleano"),
            campo(
                "valor_inmueble",
                "numero",
                depende_de="es_propietario",
                depende_de_valores=["true"],
            ),
        )
        assert completitud(formulario, {"es_propietario": False}) == 1.0


class TestCatalogoReal:
    """The shipped forms must accept a realistic submission."""

    def test_automoviles_acepta_una_solicitud_completa(self) -> None:
        auto = next(r for r in RAMOS_BASE if r["codigo"] == "automoviles")
        formulario = FormularioRamo.model_validate(auto["formulario"])
        limpio = validar_respuestas(
            formulario,
            {
                "nombre": "Juan Pérez",
                "documento": "1020304050",
                "telefono": "+57 3001112233",
                "correo": "juan@test.co",
                "ciudad": "Medellín",
                "placa": "abc123",
                "marca": "Mazda",
                "linea": "CX-5",
                "modelo": "2021",
                "uso_vehiculo": "particular",
            },
        )
        assert limpio["placa"] == "ABC123"
        assert limpio["modelo"] == 2021

    @pytest.mark.parametrize("definicion", RAMOS_BASE, ids=lambda d: str(d["codigo"]))
    def test_una_solicitud_vacia_falla_en_todo_ramo(self, definicion: dict[str, object]) -> None:
        formulario = FormularioRamo.model_validate(definicion["formulario"])
        with pytest.raises(ErroresDeFormulario):
            validar_respuestas(formulario, {})
