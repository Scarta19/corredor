"""Lead scoring: how likely is this opportunity to close?

Why a heuristic first. On day one the platform has no labelled outcomes —
nobody has won or lost a deal inside it yet — so a learned model would be
fitting noise. This baseline encodes what brokers already know, ships with
the MVP, and starts logging the features and outcomes that a trained model
will need. `LogisticoEntrenado` replaces it once roughly a few hundred closed
opportunities exist, behind the same interface and without a caller change.
"""

from __future__ import annotations

import math
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from corredor_ml.base import Contribucion, Prediccion

CanalOrigen = Literal["web", "whatsapp", "telefono", "presencial", "referido", "manual"]


class LeadFeatures(BaseModel):
    """Everything known about an opportunity at scoring time.

    Deliberately plain: no database objects, so this can be built from a live
    request, from a backfill query, or from a training dataframe row.
    """

    model_config = ConfigDict(extra="forbid")

    canal: CanalOrigen
    #: Share of the ramo's form fields the visitor actually filled in (0-1).
    completitud_formulario: float = Field(ge=0.0, le=1.0)
    tiene_telefono: bool
    tiene_email: bool
    es_cliente_existente: bool
    polizas_vigentes: int = Field(ge=0, default=0)
    #: Hours between the request arriving and an advisor first responding.
    #: None while nobody has responded yet.
    horas_hasta_primer_contacto: float | None = Field(default=None, ge=0.0)
    horas_desde_solicitud: float = Field(ge=0.0, default=0.0)
    valor_estimado: float | None = Field(default=None, ge=0.0)


# Log-odds contributions. Signs and magnitudes come from how brokerages
# actually convert; they are documented rather than tuned so that the first
# trained model has something honest to be compared against.
_INTERCEPTO = -0.85

_PESO_CANAL: dict[CanalOrigen, float] = {
    "referido": 1.30,  # warmest possible lead
    "presencial": 0.90,
    "telefono": 0.55,
    "whatsapp": 0.35,
    "web": 0.00,  # reference level
    "manual": 0.10,
}

_PESO_COMPLETITUD = 1.40  # effort spent on the form signals intent
_PESO_TELEFONO = 0.60  # unreachable leads do not convert
_PESO_EMAIL = 0.20
_PESO_CLIENTE_EXISTENTE = 0.95
_PESO_POR_POLIZA = 0.18
_TOPE_POLIZAS = 4

# Response speed dominates conversion in every brokerage funnel study, and it
# is the one factor the platform can actually change.
_PESO_RESPUESTA_RAPIDA = 1.10  # answered within an hour
_PESO_RESPUESTA_LENTA = -0.70  # answered after a day
_PESO_SIN_RESPUESTA_24H = -1.20  # still untouched after a day


def _sigmoide(x: float) -> float:
    return 1.0 / (1.0 + math.exp(-x))


class PuntuadorLeadBaseline:
    """Interpretable v0 scorer. Implements `Modelo[LeadFeatures]`."""

    nombre = "lead_scoring"
    version = "baseline-0.1.0"

    def predecir(self, features: LeadFeatures) -> Prediccion:
        contribuciones: list[Contribucion] = []
        log_odds = _INTERCEPTO

        peso_canal = _PESO_CANAL[features.canal]
        log_odds += peso_canal
        if peso_canal:
            contribuciones.append(
                Contribucion(
                    factor="canal",
                    detalle=f"Origen: {features.canal}",
                    peso=peso_canal,
                )
            )

        peso = _PESO_COMPLETITUD * features.completitud_formulario
        log_odds += peso
        contribuciones.append(
            Contribucion(
                factor="completitud_formulario",
                detalle=f"Formulario completado al {features.completitud_formulario:.0%}",
                peso=peso,
            )
        )

        if features.tiene_telefono:
            log_odds += _PESO_TELEFONO
            contribuciones.append(
                Contribucion(
                    factor="contactabilidad",
                    detalle="Dejó teléfono",
                    peso=_PESO_TELEFONO,
                )
            )
        if features.tiene_email:
            log_odds += _PESO_EMAIL
            contribuciones.append(
                Contribucion(factor="contactabilidad", detalle="Dejó correo", peso=_PESO_EMAIL)
            )

        if features.es_cliente_existente:
            log_odds += _PESO_CLIENTE_EXISTENTE
            contribuciones.append(
                Contribucion(
                    factor="relacion",
                    detalle="Ya es cliente de la agencia",
                    peso=_PESO_CLIENTE_EXISTENTE,
                )
            )

        if features.polizas_vigentes:
            peso = _PESO_POR_POLIZA * min(features.polizas_vigentes, _TOPE_POLIZAS)
            log_odds += peso
            contribuciones.append(
                Contribucion(
                    factor="relacion",
                    detalle=f"{features.polizas_vigentes} póliza(s) vigente(s)",
                    peso=peso,
                )
            )

        peso, detalle = self._factor_respuesta(features)
        if peso:
            log_odds += peso
            contribuciones.append(
                Contribucion(factor="tiempo_de_respuesta", detalle=detalle, peso=peso)
            )

        puntaje = _sigmoide(log_odds)
        contribuciones.sort(key=lambda c: abs(c.peso), reverse=True)
        return Prediccion(
            puntaje=puntaje,
            modelo=self.nombre,
            modelo_version=self.version,
            explicacion=contribuciones,
        )

    @staticmethod
    def _factor_respuesta(features: LeadFeatures) -> tuple[float, str]:
        horas = features.horas_hasta_primer_contacto
        if horas is None:
            if features.horas_desde_solicitud >= 24:
                return _PESO_SIN_RESPUESTA_24H, "Sin contactar hace más de 24 horas"
            return 0.0, ""
        if horas <= 1:
            return _PESO_RESPUESTA_RAPIDA, "Contactado en menos de 1 hora"
        if horas >= 24:
            return _PESO_RESPUESTA_LENTA, f"Contactado tras {horas:.0f} horas"
        return 0.0, ""
