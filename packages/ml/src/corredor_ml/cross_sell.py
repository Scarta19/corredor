"""Next-best-product recommendations (§13 of the platform brief).

An affinity table, not a neural network — and on purpose. With a few thousand
clients and eight lines of business, a collaborative filter has almost
nothing to learn from, while the co-occurrence patterns a broker can recite
from memory are already most of the available signal. The interface is the
part that matters: once the book is large enough, the table is replaced by a
learned recommender and every caller stays as it is.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class RecomendacionRamo(BaseModel):
    model_config = ConfigDict(extra="forbid")

    ramo: str
    puntaje: float = Field(ge=0.0, le=1.0)
    razon: str


class PerfilCrossSell(BaseModel):
    model_config = ConfigDict(extra="forbid")

    es_empresa: bool
    #: Ramo codes the client already holds a policy in.
    ramos_vigentes: list[str] = Field(default_factory=list)
    tiene_vehiculo: bool | None = None
    tiene_vivienda_propia: bool | None = None
    numero_empleados: int | None = Field(default=None, ge=0)


# From ramo held -> (ramo to offer, affinity, reason an advisor can say aloud).
_AFINIDAD_PERSONAS: dict[str, list[tuple[str, float, str]]] = {
    "automoviles": [
        ("accidentes_personales", 0.62, "Complementa la cobertura del conductor"),
        ("vida", 0.45, "Perfil con capacidad de pago ya demostrada"),
        ("hogar", 0.40, "Suele tener vivienda asegurable"),
    ],
    "hogar": [
        ("automoviles", 0.55, "Hogar y vehículo se aseguran juntos con frecuencia"),
        ("vida", 0.42, "Protección patrimonial del núcleo familiar"),
    ],
    "vida": [
        ("accidentes_personales", 0.50, "Cobertura complementaria de bajo costo"),
        ("hogar", 0.35, "Protección patrimonial del núcleo familiar"),
    ],
    "accidentes_personales": [
        ("vida", 0.48, "Ampliación natural de la cobertura personal"),
    ],
}

_AFINIDAD_EMPRESAS: dict[str, list[tuple[str, float, str]]] = {
    "cumplimiento": [
        ("responsabilidad_civil", 0.70, "Exigida en la mayoría de contratos públicos"),
        ("empresarial", 0.48, "Protección de activos de la operación"),
    ],
    "responsabilidad_civil": [
        ("cumplimiento", 0.66, "Suelen contratarse para la misma licitación"),
        ("vida_grupo", 0.44, "Cobertura para la nómina"),
    ],
    "empresarial": [
        ("responsabilidad_civil", 0.58, "Riesgo frente a terceros no cubierto por daños"),
        ("vida_grupo", 0.46, "Cobertura para la nómina"),
        ("automoviles", 0.38, "Flota o vehículos de la operación"),
    ],
    "automoviles": [
        ("responsabilidad_civil", 0.52, "Exposición frente a terceros de la flota"),
        ("empresarial", 0.40, "Protección de activos de la operación"),
    ],
}

MODELO = "cross_sell"
VERSION = "afinidad-0.1.0"


def recomendar(perfil: PerfilCrossSell, limite: int = 3) -> list[RecomendacionRamo]:
    """Rank lines of business the client does not yet hold.

    Scores from several held policies reinforce one another: a client with
    both `cumplimiento` and `empresarial` is a stronger candidate for
    `responsabilidad_civil` than either alone would suggest.
    """
    tabla = _AFINIDAD_EMPRESAS if perfil.es_empresa else _AFINIDAD_PERSONAS
    vigentes = set(perfil.ramos_vigentes)

    acumulado: dict[str, float] = {}
    # The reason shown is the one from the single strongest piece of evidence,
    # because an advisor repeats one sentence to the client, not a sum.
    mejor_evidencia: dict[str, tuple[float, str]] = {}

    def acumular(candidato: str, afinidad: float, razon: str) -> None:
        if candidato in vigentes:
            return
        previo = acumulado.get(candidato, 0.0)
        # Probabilistic OR: independent evidence accumulates but the score
        # stays bounded by 1.
        acumulado[candidato] = previo + afinidad * (1.0 - previo)
        if afinidad > mejor_evidencia.get(candidato, (0.0, ""))[0]:
            mejor_evidencia[candidato] = (afinidad, razon)

    for ramo_actual in vigentes:
        for candidato, afinidad, razon in tabla.get(ramo_actual, []):
            acumular(candidato, afinidad, razon)

    for candidato, ajuste, razon in _senales_explicitas(perfil):
        acumular(candidato, ajuste, razon)

    ranking = sorted(acumulado.items(), key=lambda item: item[1], reverse=True)
    return [
        RecomendacionRamo(ramo=ramo, puntaje=round(puntaje, 4), razon=mejor_evidencia[ramo][1])
        for ramo, puntaje in ranking[:limite]
    ]


def _senales_explicitas(perfil: PerfilCrossSell) -> list[tuple[str, float, str]]:
    """Signals volunteered in quote forms, independent of policies held."""
    senales: list[tuple[str, float, str]] = []
    if perfil.tiene_vivienda_propia:
        senales.append(("hogar", 0.45, "Declaró vivienda propia en una cotización"))
    if perfil.tiene_vehiculo:
        senales.append(("automoviles", 0.45, "Declaró vehículo en una cotización"))
    if perfil.numero_empleados and perfil.numero_empleados >= 10:
        senales.append(("vida_grupo", 0.50, f"Nómina de {perfil.numero_empleados} empleados"))
    return senales
