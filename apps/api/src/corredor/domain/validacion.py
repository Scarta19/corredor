"""Validating a visitor's answers against a ramo's quote form.

The form definition is data ([ADR-0003]), so nothing about these answers can
be checked by Postgres or by a static Pydantic model — the shape is only known
at runtime. This module is that missing type checker.

It is deliberately pure: no session, no HTTP. The web form is the first caller
and the WhatsApp module (Módulo 3) will be the second, capturing the same
fields from a conversation. Both need the same answer to "is this a complete,
well-formed quote request?", and neither should be the place it is decided.
"""

from __future__ import annotations

import re
from datetime import date
from typing import Any

from corredor.core.errors import DatosInvalidos
from corredor.domain.enums import TipoCampo
from corredor.domain.formularios import CampoFormulario, FormularioRamo

_EMAIL = re.compile(r"^[^@\s]+@[^@\s.]+\.[^@\s]+$")
_TELEFONO = re.compile(r"^\+?[\d\s()-]{7,20}$")
_DOCUMENTO = re.compile(r"^[A-Za-z0-9.-]{5,20}$")
_PLACA = re.compile(r"^[A-Z0-9]{5,8}$")

MAX_TEXTO = 500


class ErroresDeFormulario(DatosInvalidos):
    """Every problem with a submission, reported at once.

    Returning the first error and stopping makes the visitor resubmit
    repeatedly, and a quote form that is annoying to complete is a lead that
    never arrives. Callers get a `campo -> mensaje` map instead.
    """

    codigo = "formulario_invalido"

    def __init__(self, errores: dict[str, str]) -> None:
        super().__init__(
            "Revisa los datos del formulario.",
            errores=errores,
        )


def _texto_de(valor: Any) -> str:
    """Render a value the way `depende_de_valores` writes it.

    Booleans are compared as "true"/"false" because that is what a form
    definition author naturally writes in JSON.
    """
    if isinstance(valor, bool):
        return "true" if valor else "false"
    return str(valor).strip()


def campo_esta_activo(campo: CampoFormulario, respuestas: dict[str, Any]) -> bool:
    """Whether a conditional field applies, given the answers so far."""
    if campo.depende_de is None:
        return True
    valor = respuestas.get(campo.depende_de)
    if valor is None:
        return False
    if not campo.depende_de_valores:
        # No values listed means "shown whenever the other field is answered".
        return _texto_de(valor) not in ("", "false")
    return _texto_de(valor) in campo.depende_de_valores


def validar_respuestas(formulario: FormularioRamo, respuestas: dict[str, Any]) -> dict[str, Any]:
    """Check and normalise a submission.

    Returns the cleaned answers — trimmed strings, real integers, uppercase
    plates, ISO dates — so that what reaches the database is consistent
    regardless of which channel captured it.

    Raises `ErroresDeFormulario` with every problem found.
    """
    campos = {campo.nombre: campo for campo in formulario.campos}
    errores: dict[str, str] = {}
    limpio: dict[str, Any] = {}

    desconocidos = set(respuestas) - set(campos)
    for nombre in sorted(desconocidos):
        errores[nombre] = "Este campo no pertenece al formulario."

    for campo in formulario.campos_ordenados:
        activo = campo_esta_activo(campo, respuestas)
        valor = respuestas.get(campo.nombre)
        vacio = valor is None or (isinstance(valor, str) and not valor.strip())

        if not activo:
            if not vacio:
                errores[campo.nombre] = "Este campo no aplica según las respuestas anteriores."
            continue

        if vacio:
            if campo.requerido:
                errores[campo.nombre] = "Este campo es obligatorio."
            continue

        try:
            limpio[campo.nombre] = _normalizar(campo, valor)
        except ValueError as exc:
            errores[campo.nombre] = str(exc)

    if errores:
        raise ErroresDeFormulario(errores)
    return limpio


def _normalizar(campo: CampoFormulario, valor: Any) -> Any:
    """Coerce and validate one answer, or raise `ValueError` with the reason."""
    match campo.tipo:
        case TipoCampo.BOOLEANO:
            if isinstance(valor, bool):
                return valor
            texto = _texto_de(valor).lower()
            if texto in ("true", "si", "sí", "1"):
                return True
            if texto in ("false", "no", "0"):
                return False
            raise ValueError("Indica sí o no.")

        case TipoCampo.ENTERO:
            try:
                return int(str(valor).strip())
            except (TypeError, ValueError):
                raise ValueError("Debe ser un número entero.") from None

        case TipoCampo.NUMERO:
            try:
                numero = float(str(valor).replace(",", "").strip())
            except (TypeError, ValueError):
                raise ValueError("Debe ser un número.") from None
            if numero < 0:
                raise ValueError("No puede ser negativo.")
            return numero

        case TipoCampo.EMAIL:
            texto = _texto_de(valor).lower()
            if not _EMAIL.match(texto):
                raise ValueError("Escribe un correo válido.")
            return texto

        case TipoCampo.TELEFONO:
            texto = _texto_de(valor)
            if not _TELEFONO.match(texto) or sum(c.isdigit() for c in texto) < 7:
                raise ValueError("Escribe un teléfono válido.")
            return texto

        case TipoCampo.DOCUMENTO:
            texto = _texto_de(valor)
            if not _DOCUMENTO.match(texto):
                raise ValueError("Escribe un número de documento válido.")
            return texto

        case TipoCampo.PLACA:
            texto = _texto_de(valor).upper().replace("-", "").replace(" ", "")
            if not _PLACA.match(texto):
                raise ValueError("Escribe una placa válida, por ejemplo ABC123.")
            return texto

        case TipoCampo.FECHA:
            if isinstance(valor, date):
                return valor.isoformat()
            try:
                return date.fromisoformat(_texto_de(valor)).isoformat()
            except ValueError:
                raise ValueError("Escribe una fecha válida (AAAA-MM-DD).") from None

        case TipoCampo.SELECCION:
            texto = _texto_de(valor)
            validos = {opcion.valor for opcion in campo.opciones}
            if texto not in validos:
                raise ValueError("Elige una de las opciones disponibles.")
            return texto

        case TipoCampo.MULTISELECCION:
            if not isinstance(valor, list):
                raise ValueError("Elige una o más opciones.")
            validos = {opcion.valor for opcion in campo.opciones}
            elegidos = [_texto_de(v) for v in valor]
            if any(v not in validos for v in elegidos):
                raise ValueError("Alguna de las opciones no es válida.")
            if len(set(elegidos)) != len(elegidos):
                raise ValueError("Hay opciones repetidas.")
            return elegidos

        case _:
            texto = _texto_de(valor)
            if len(texto) > MAX_TEXTO:
                raise ValueError(f"Máximo {MAX_TEXTO} caracteres.")
            return texto


def completitud(formulario: FormularioRamo, respuestas: dict[str, Any]) -> float:
    """Share of applicable fields the visitor actually answered (0 to 1).

    Feeds the lead score: effort spent on a form is one of the better signals
    of intent available before anyone has spoken to the person.
    """
    aplicables = [campo for campo in formulario.campos if campo_esta_activo(campo, respuestas)]
    if not aplicables:
        return 0.0
    respondidos = sum(
        1 for campo in aplicables if respuestas.get(campo.nombre) not in (None, "", [])
    )
    return respondidos / len(aplicables)
