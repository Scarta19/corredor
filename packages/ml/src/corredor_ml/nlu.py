"""Understanding an inbound message (Módulo 3).

§7 sketches a numbered menu: "1. Cotizar, 2. Consultar, 3. Renovar, 4. Hablar
con un asesor". A menu is a reasonable floor, but people do not write "1" —
they write *"necesito asegurar mi carro"*, and a bot that answers "opción no
válida" to that has already lost the lead.

So the menu stays as a fallback and this module reads meaning first.

§8 draws the line this module must respect: automation handles reception,
FAQs, capture and classification; a person takes over when the situation needs
commercial or technical judgement. `requiere_humano` is that line made
explicit, and it is deliberately generous — the cost of handing a simple
question to a person is a few seconds of their time, while the cost of a bot
mishandling a claim is a client.
"""

from __future__ import annotations

import re
import unicodedata
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field


class Intencion(StrEnum):
    COTIZAR = "cotizar"
    CONSULTAR_POLIZA = "consultar_poliza"
    RENOVAR = "renovar"
    SINIESTRO = "siniestro"
    HABLAR_ASESOR = "hablar_asesor"
    SALUDO = "saludo"
    OTRO = "otro"


class Analisis(BaseModel):
    model_config = ConfigDict(extra="forbid")

    intencion: Intencion
    confianza: float = Field(ge=0.0, le=1.0)
    #: Ramo code guessed from the text, when the message names one.
    ramo: str | None = None
    #: Structured data lifted from free text, to pre-fill the quote form.
    entidades: dict[str, str] = Field(default_factory=dict)
    requiere_humano: bool = False
    modelo: str = "nlu"
    modelo_version: str = "reglas-0.1.0"


def normalizar(texto: str) -> str:
    """Lowercase, strip accents, collapse whitespace.

    People write "automóvil", "automovil" and "AUTOMOVIL" in the same
    conversation; matching should not care.
    """
    sin_tildes = "".join(
        c for c in unicodedata.normalize("NFD", texto.lower()) if unicodedata.category(c) != "Mn"
    )
    return re.sub(r"\s+", " ", sin_tildes).strip()


# --- Vocabulary -------------------------------------------------------------

_INTENCIONES: list[tuple[Intencion, tuple[str, ...]]] = [
    # Order matters: a claim outranks everything else in the same message.
    (
        Intencion.SINIESTRO,
        (
            "siniestro",
            "choque",
            "choque",
            "accidente",
            "me robaron",
            "robo",
            "hurto",
            "se incendio",
            "incendio",
            "reclamacion",
            "reclamo",
            "me chocaron",
            "perdida total",
            "grua",
        ),
    ),
    (
        Intencion.RENOVAR,
        ("renovar", "renovacion", "se me vence", "vence mi poliza", "vencimiento"),
    ),
    (
        Intencion.COTIZAR,
        (
            "cotizar",
            "cotizacion",
            "precio",
            "cuanto cuesta",
            "cuanto vale",
            "asegurar",
            "seguro para",
            "necesito un seguro",
            "quiero un seguro",
            "poliza nueva",
            "tarifa",
        ),
    ),
    (
        Intencion.CONSULTAR_POLIZA,
        (
            "mi poliza",
            "consultar",
            "estado de mi",
            "certificado",
            "copia de",
            "numero de poliza",
            "cobertura",
            "que cubre",
            "esta vigente",
        ),
    ),
    (
        Intencion.HABLAR_ASESOR,
        ("asesor", "hablar con alguien", "una persona", "humano", "agente"),
    ),
    (
        Intencion.SALUDO,
        ("hola", "buenas", "buenos dias", "buenas tardes", "buenas noches"),
    ),
]

_RAMOS: dict[str, tuple[str, ...]] = {
    "automoviles": ("carro", "auto", "vehiculo", "moto", "camioneta", "soat", "carros"),
    "hogar": ("casa", "hogar", "apartamento", "vivienda", "apto"),
    "vida": ("vida",),
    "accidentes_personales": ("accidentes personales", "accidente personal"),
    "salud": ("salud", "medicina prepagada"),
    "cumplimiento": ("cumplimiento", "licitacion", "contrato estatal", "garantia"),
    "responsabilidad_civil": ("responsabilidad civil", "rc ", "danos a terceros"),
    "empresarial": ("empresa", "empresarial", "negocio", "pyme", "local comercial"),
}

#: The numbered menu of §7, kept as a fallback for people who prefer it.
_MENU: dict[str, Intencion] = {
    "1": Intencion.COTIZAR,
    "2": Intencion.CONSULTAR_POLIZA,
    "3": Intencion.RENOVAR,
    "4": Intencion.HABLAR_ASESOR,
}

_PLACA = re.compile(r"\b([a-z]{3}[\s-]?\d{2,3}[a-z]?)\b")
_DOCUMENTO = re.compile(r"\b(\d{6,12})\b")
_CORREO = re.compile(r"\b([^@\s]+@[^@\s.]+\.[^@\s]+)\b")

#: Intents where a person should take over. §8: automation handles reception
#: and classification; judgement goes to an advisor.
_REQUIEREN_HUMANO = {
    Intencion.SINIESTRO,
    Intencion.HABLAR_ASESOR,
    Intencion.CONSULTAR_POLIZA,
}


def _detectar_ramo(texto: str) -> str | None:
    for codigo, palabras in _RAMOS.items():
        if any(p in texto for p in palabras):
            return codigo
    return None


def _extraer_entidades(texto: str, original: str) -> dict[str, str]:
    """Lift anything the quote form would otherwise have to ask for again."""
    entidades: dict[str, str] = {}
    if (placa := _PLACA.search(texto)) is not None:
        entidades["placa"] = placa.group(1).replace(" ", "").replace("-", "").upper()
    if (correo := _CORREO.search(original.lower())) is not None:
        entidades["correo"] = correo.group(1)
    # A plate like ABC123 also contains digits; do not read it as a document.
    documento = _DOCUMENTO.search(texto)
    if documento is not None and documento.group(1) not in entidades.get("placa", ""):
        entidades["documento"] = documento.group(1)
    return entidades


def analizar(texto: str) -> Analisis:
    """Classify a message with rules only — no network, no API key.

    This is the baseline. It handles the vocabulary a broker's clients actually
    use, runs in microseconds, and works when the LLM is unreachable or
    unconfigured. `corredor.services.whatsapp` layers a model on top of it when
    one is available, and falls back here when it is not.
    """
    limpio = normalizar(texto)

    if limpio in _MENU:
        intencion = _MENU[limpio]
        return Analisis(
            intencion=intencion,
            confianza=1.0,
            requiere_humano=intencion in _REQUIEREN_HUMANO,
        )

    encontrada: Intencion | None = None
    for intencion, palabras in _INTENCIONES:
        if any(palabra in limpio for palabra in palabras):
            encontrada = intencion
            break

    ramo = _detectar_ramo(limpio)
    entidades = _extraer_entidades(limpio, texto)

    if encontrada is None:
        # A message naming a line of business but no verb is still almost
        # certainly a quote request: "seguro de moto".
        if ramo is not None:
            return Analisis(
                intencion=Intencion.COTIZAR,
                confianza=0.5,
                ramo=ramo,
                entidades=entidades,
            )
        # Unclassifiable. Hand it to a person rather than guess at someone
        # who is already talking to a business about money.
        return Analisis(
            intencion=Intencion.OTRO,
            confianza=0.2,
            entidades=entidades,
            requiere_humano=True,
        )

    # A greeting that also carries a real request is the real request.
    if encontrada is Intencion.SALUDO and (ramo or entidades):
        encontrada = Intencion.COTIZAR

    confianza = 0.9 if encontrada is not Intencion.SALUDO else 0.7
    if encontrada is Intencion.COTIZAR and ramo is None:
        # "quiero cotizar" with no product named: right intent, incomplete.
        confianza = 0.7

    return Analisis(
        intencion=encontrada,
        confianza=confianza,
        ramo=ramo,
        entidades=entidades,
        requiere_humano=encontrada in _REQUIEREN_HUMANO,
    )
