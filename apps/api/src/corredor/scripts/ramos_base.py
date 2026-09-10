"""The starter catalogue of lines of business, with their quote forms.

These are the eight options from §5 of the platform brief. A brokerage edits
them after onboarding — the point of the dynamic form is that this is data,
not code — but shipping a sensible default means a new tenant has a working
quote flow the moment it is created.
"""

from __future__ import annotations

from typing import Any

from corredor.domain.enums import TipoCliente

# Asked on every form, before anything ramo-specific.
_IDENTIDAD: list[dict[str, Any]] = [
    {"nombre": "nombre", "etiqueta": "Nombre completo", "tipo": "texto", "orden": 0},
    {
        "nombre": "documento",
        "etiqueta": "Documento / NIT",
        "tipo": "documento",
        "orden": 1,
    },
    {"nombre": "telefono", "etiqueta": "Teléfono", "tipo": "telefono", "orden": 2},
    {"nombre": "correo", "etiqueta": "Correo electrónico", "tipo": "email", "orden": 3},
    {"nombre": "ciudad", "etiqueta": "Ciudad", "tipo": "texto", "orden": 4},
]


def _form(*campos: dict[str, Any]) -> dict[str, Any]:
    return {"version": 1, "campos": [*_IDENTIDAD, *campos]}


def _opciones(*valores: str) -> list[dict[str, str]]:
    return [{"valor": v.lower().replace(" ", "_"), "etiqueta": v} for v in valores]


RAMOS_BASE: list[dict[str, Any]] = [
    {
        "codigo": "automoviles",
        "nombre": "Automóviles",
        "descripcion": "Protege tu vehículo ante daños, robo y responsabilidad frente a terceros.",
        "dirigido_a": None,
        "orden": 10,
        "formulario": _form(
            {"nombre": "placa", "etiqueta": "Placa", "tipo": "placa", "orden": 10},
            {"nombre": "marca", "etiqueta": "Marca", "tipo": "texto", "orden": 11},
            {"nombre": "linea", "etiqueta": "Línea", "tipo": "texto", "orden": 12},
            {"nombre": "modelo", "etiqueta": "Modelo (año)", "tipo": "entero", "orden": 13},
            {
                "nombre": "uso_vehiculo",
                "etiqueta": "Uso del vehículo",
                "tipo": "seleccion",
                "orden": 14,
                "opciones": _opciones("Particular", "Público", "Carga", "Taxi", "Empresarial"),
            },
        ),
    },
    {
        "codigo": "cumplimiento",
        "nombre": "Cumplimiento",
        "descripcion": "Garantiza el cumplimiento de contratos ante entidades públicas y privadas.",
        "dirigido_a": TipoCliente.EMPRESA,
        "orden": 20,
        "formulario": _form(
            {
                "nombre": "tipo_contrato",
                "etiqueta": "Tipo de contrato",
                "tipo": "seleccion",
                "orden": 10,
                "opciones": _opciones("Obra", "Suministro", "Servicios", "Consultoría", "Otro"),
            },
            {
                "nombre": "entidad_contratante",
                "etiqueta": "Entidad contratante",
                "tipo": "texto",
                "orden": 11,
            },
            {
                "nombre": "valor_contrato",
                "etiqueta": "Valor del contrato (COP)",
                "tipo": "numero",
                "orden": 12,
            },
            {
                "nombre": "plazo_meses",
                "etiqueta": "Plazo del contrato (meses)",
                "tipo": "entero",
                "orden": 13,
            },
        ),
    },
    {
        "codigo": "responsabilidad_civil",
        "nombre": "Responsabilidad Civil",
        "descripcion": "Cubre los daños que tu actividad pueda causar a terceros.",
        "dirigido_a": None,
        "orden": 30,
        "formulario": _form(
            {
                "nombre": "actividad",
                "etiqueta": "Actividad económica",
                "tipo": "texto",
                "orden": 10,
            },
            {
                "nombre": "valor_asegurado",
                "etiqueta": "Valor asegurado deseado (COP)",
                "tipo": "numero",
                "orden": 11,
                "requerido": False,
            },
        ),
    },
    {
        "codigo": "vida",
        "nombre": "Vida",
        "descripcion": "Protección económica para tu familia.",
        "dirigido_a": TipoCliente.PERSONA,
        "orden": 40,
        "formulario": _form(
            {
                "nombre": "fecha_nacimiento",
                "etiqueta": "Fecha de nacimiento",
                "tipo": "fecha",
                "orden": 10,
            },
            {
                "nombre": "fumador",
                "etiqueta": "¿Fumas actualmente?",
                "tipo": "booleano",
                "orden": 11,
            },
            {
                "nombre": "valor_asegurado",
                "etiqueta": "Valor asegurado deseado (COP)",
                "tipo": "numero",
                "orden": 12,
                "requerido": False,
            },
        ),
    },
    {
        "codigo": "accidentes_personales",
        "nombre": "Accidentes Personales",
        "descripcion": "Cobertura ante accidentes, incapacidad y gastos médicos.",
        "dirigido_a": None,
        "orden": 50,
        "formulario": _form(
            {
                "nombre": "fecha_nacimiento",
                "etiqueta": "Fecha de nacimiento",
                "tipo": "fecha",
                "orden": 10,
            },
            {
                "nombre": "ocupacion",
                "etiqueta": "Ocupación",
                "tipo": "texto",
                "orden": 11,
            },
        ),
    },
    {
        "codigo": "hogar",
        "nombre": "Hogar",
        "descripcion": "Asegura tu vivienda y su contenido.",
        "dirigido_a": TipoCliente.PERSONA,
        "orden": 60,
        "formulario": _form(
            {
                "nombre": "tipo_vivienda",
                "etiqueta": "Tipo de vivienda",
                "tipo": "seleccion",
                "orden": 10,
                "opciones": _opciones("Casa", "Apartamento", "Finca", "Local"),
            },
            {
                "nombre": "es_propietario",
                "etiqueta": "¿Eres el propietario?",
                "tipo": "booleano",
                "orden": 11,
            },
            {
                "nombre": "valor_inmueble",
                "etiqueta": "Valor aproximado del inmueble (COP)",
                "tipo": "numero",
                "orden": 12,
                "requerido": False,
                "depende_de": "es_propietario",
                "depende_de_valores": ["true"],
            },
        ),
    },
    {
        "codigo": "empresarial",
        "nombre": "Empresarial",
        "descripcion": "Protección integral para los activos y la operación de tu empresa.",
        "dirigido_a": TipoCliente.EMPRESA,
        "orden": 70,
        "formulario": _form(
            {
                "nombre": "actividad",
                "etiqueta": "Actividad económica",
                "tipo": "texto",
                "orden": 10,
            },
            {
                "nombre": "numero_empleados",
                "etiqueta": "Número de empleados",
                "tipo": "entero",
                "orden": 11,
            },
            {
                "nombre": "coberturas_interes",
                "etiqueta": "Coberturas de interés",
                "tipo": "multiseleccion",
                "orden": 12,
                "requerido": False,
                "opciones": _opciones(
                    "Incendio", "Sustracción", "Equipo eléctrico", "Lucro cesante", "Transporte"
                ),
            },
        ),
    },
    {
        "codigo": "otros",
        "nombre": "Otros",
        "descripcion": "¿No encuentras lo que buscas? Cuéntanos qué necesitas asegurar.",
        "dirigido_a": None,
        "orden": 99,
        "formulario": _form(
            {
                "nombre": "necesidad",
                "etiqueta": "¿Qué necesitas asegurar?",
                "tipo": "texto",
                "orden": 10,
                "ayuda": "Descríbelo brevemente y un asesor te contactará.",
            },
        ),
    },
]
