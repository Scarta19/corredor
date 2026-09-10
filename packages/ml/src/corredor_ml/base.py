"""Contracts shared by every model in the platform.

A model is anything that turns a typed feature object into a typed
`Prediccion`. Whether it is a hand-written heuristic, a gradient-boosted tree
or a call to an LLM is an implementation detail the platform does not need to
know — which is what lets the baseline ship on day one and be replaced later
without touching a caller.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Protocol

from pydantic import BaseModel, ConfigDict, Field


class Contribucion(BaseModel):
    """One feature's contribution to a score, for display to an advisor."""

    model_config = ConfigDict(extra="forbid")

    factor: str
    detalle: str
    #: Signed influence on the score; positive pushes the score up.
    peso: float


class Prediccion(BaseModel):
    """A model output, carrying everything needed to audit it later."""

    model_config = ConfigDict(extra="forbid")

    puntaje: float = Field(ge=0.0, le=1.0)
    modelo: str
    modelo_version: str
    explicacion: list[Contribucion] = Field(default_factory=list)
    calculado_en: datetime = Field(default_factory=lambda: datetime.now(UTC))


class Modelo[Features: BaseModel](Protocol):
    """Structural interface every scorer implements."""

    nombre: str
    version: str

    def predecir(self, features: Features) -> Prediccion: ...
