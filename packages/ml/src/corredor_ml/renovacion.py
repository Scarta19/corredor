"""Renewal risk: how likely is this policy to walk?

Days-to-expiry alone is a schedule, not a priority. A policy expiring in 45
days whose premium jumped 30% and whose owner has not been contacted in a
year is a more urgent call than one expiring in 10 days that has renewed
three times without friction. This model is what turns the renewal dashboard
from a calendar into a work queue.
"""

from __future__ import annotations

import math

from pydantic import BaseModel, ConfigDict, Field

from corredor_ml.base import Contribucion, Prediccion

NivelRiesgo = str


class RenovacionFeatures(BaseModel):
    model_config = ConfigDict(extra="forbid")

    dias_para_vencimiento: int
    #: How many times this policy line has already been renewed with us.
    renovaciones_previas: int = Field(ge=0, default=0)
    antiguedad_cliente_meses: int = Field(ge=0, default=0)
    #: Relative premium change vs. the expiring policy. 0.30 = a 30% increase.
    variacion_prima: float = 0.0
    siniestros_ultimo_periodo: int = Field(ge=0, default=0)
    dias_desde_ultimo_contacto: int | None = Field(default=None, ge=0)
    #: Number of other active policies the client holds with the brokerage.
    otras_polizas_vigentes: int = Field(ge=0, default=0)


_INTERCEPTO = -0.60

_PESO_POR_RENOVACION = -0.42  # loyalty compounds
_TOPE_RENOVACIONES = 4
_PESO_ANTIGUEDAD_ANUAL = -0.10
_TOPE_ANTIGUEDAD_ANIOS = 5.0
_PESO_VARIACION_PRIMA = 2.20  # price shock is the dominant churn driver
_PESO_SINIESTRO = 0.28
_PESO_ABANDONO = 0.85  # no contact in six months
_PESO_POR_OTRA_POLIZA = -0.30  # multi-line clients are far stickier
_TOPE_OTRAS_POLIZAS = 3
_PESO_URGENCIA = 0.45  # expiring inside a week, still unmanaged

_UMBRAL_RIESGO_ALTO = 0.60
_UMBRAL_RIESGO_MEDIO = 0.35


def _sigmoide(x: float) -> float:
    return 1.0 / (1.0 + math.exp(-x))


def clasificar_nivel(probabilidad: float) -> NivelRiesgo:
    if probabilidad >= _UMBRAL_RIESGO_ALTO:
        return "alto"
    if probabilidad >= _UMBRAL_RIESGO_MEDIO:
        return "medio"
    return "bajo"


class RiesgoRenovacionBaseline:
    """Interpretable v0 churn model. Implements `Modelo[RenovacionFeatures]`."""

    nombre = "riesgo_renovacion"
    version = "baseline-0.1.0"

    def predecir(self, features: RenovacionFeatures) -> Prediccion:
        contribuciones: list[Contribucion] = []
        log_odds = _INTERCEPTO

        def aportar(factor: str, detalle: str, peso: float) -> None:
            nonlocal log_odds
            if peso:
                log_odds += peso
                contribuciones.append(Contribucion(factor=factor, detalle=detalle, peso=peso))

        aportar(
            "lealtad",
            f"{features.renovaciones_previas} renovación(es) previa(s)",
            _PESO_POR_RENOVACION * min(features.renovaciones_previas, _TOPE_RENOVACIONES),
        )
        anios = min(features.antiguedad_cliente_meses / 12.0, _TOPE_ANTIGUEDAD_ANIOS)
        aportar(
            "lealtad",
            f"Cliente hace {anios:.1f} año(s)",
            _PESO_ANTIGUEDAD_ANUAL * anios,
        )
        aportar(
            "cartera",
            f"{features.otras_polizas_vigentes} póliza(s) adicional(es)",
            _PESO_POR_OTRA_POLIZA * min(features.otras_polizas_vigentes, _TOPE_OTRAS_POLIZAS),
        )
        if features.variacion_prima:
            aportar(
                "precio",
                f"La prima varía {features.variacion_prima:+.0%}",
                _PESO_VARIACION_PRIMA * features.variacion_prima,
            )
        aportar(
            "siniestralidad",
            f"{features.siniestros_ultimo_periodo} siniestro(s) en el período",
            _PESO_SINIESTRO * features.siniestros_ultimo_periodo,
        )
        if (
            features.dias_desde_ultimo_contacto is not None
            and features.dias_desde_ultimo_contacto >= 180
        ):
            aportar(
                "relacion",
                f"Sin contacto hace {features.dias_desde_ultimo_contacto} días",
                _PESO_ABANDONO,
            )
        if 0 <= features.dias_para_vencimiento <= 7:
            aportar("urgencia", "Vence en menos de 7 días", _PESO_URGENCIA)

        probabilidad = _sigmoide(log_odds)
        contribuciones.sort(key=lambda c: abs(c.peso), reverse=True)
        return Prediccion(
            puntaje=probabilidad,
            modelo=self.nombre,
            modelo_version=self.version,
            explicacion=contribuciones,
        )
