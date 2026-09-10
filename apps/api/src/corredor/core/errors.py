"""Domain errors and their HTTP translation.

Business rules raise these; the API layer decides what a client sees. Keeping
the mapping in one place means a service never imports `fastapi`.
"""

from __future__ import annotations

from typing import Any


class CorredorError(Exception):
    """Base class for every expected failure in the platform."""

    codigo = "error_interno"
    status_code = 500
    mensaje = "Ocurrió un error procesando la solicitud."

    def __init__(self, mensaje: str | None = None, **contexto: Any) -> None:
        self.mensaje = mensaje or self.mensaje
        self.contexto = contexto
        super().__init__(self.mensaje)

    def to_payload(self) -> dict[str, Any]:
        return {"codigo": self.codigo, "mensaje": self.mensaje, "contexto": self.contexto}


class NoEncontrado(CorredorError):
    codigo = "no_encontrado"
    status_code = 404
    mensaje = "El recurso solicitado no existe."


class ReglaDeNegocio(CorredorError):
    """A request that is well-formed but not allowed by the business rules."""

    codigo = "regla_de_negocio"
    status_code = 409
    mensaje = "La operación no es válida en el estado actual."


class DatosInvalidos(CorredorError):
    codigo = "datos_invalidos"
    status_code = 422
    mensaje = "Los datos enviados no son válidos."


class NoAutorizado(CorredorError):
    codigo = "no_autorizado"
    status_code = 401
    mensaje = "Credenciales inválidas o ausentes."


class SinPermiso(CorredorError):
    codigo = "sin_permiso"
    status_code = 403
    mensaje = "No tiene permisos para esta operación."
