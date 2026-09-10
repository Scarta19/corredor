"""The declarative schema behind the intelligent quote form (Módulo 2).

Each ramo (line of business) owns a form definition. The public web app asks
the API "what do you need to quote *automóviles*?" and renders whatever comes
back, so adding a line of business — or changing which fields a broker asks
for — is data, not a release. See docs/adr/0004-dynamic-quote-forms.md.
"""

from __future__ import annotations

from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from corredor.domain.enums import TipoCampo

Slug = Annotated[str, Field(pattern=r"^[a-z][a-z0-9_]{0,48}$")]


class OpcionCampo(BaseModel):
    model_config = ConfigDict(extra="forbid")

    valor: str = Field(min_length=1, max_length=80)
    etiqueta: str = Field(min_length=1, max_length=120)


class CampoFormulario(BaseModel):
    """One question shown to the visitor."""

    model_config = ConfigDict(extra="forbid")

    nombre: Slug
    etiqueta: str = Field(min_length=1, max_length=160)
    tipo: TipoCampo
    requerido: bool = True
    ayuda: str | None = Field(default=None, max_length=240)
    opciones: list[OpcionCampo] = Field(default_factory=list)
    #: Rendering order within the form; lower comes first.
    orden: int = 0
    #: Only show this field when another field holds one of these values,
    #: e.g. ask for `placa` only when `tiene_vehiculo` is true.
    depende_de: Slug | None = None
    depende_de_valores: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def _validar_opciones(self) -> CampoFormulario:
        requiere_opciones = self.tipo in (TipoCampo.SELECCION, TipoCampo.MULTISELECCION)
        if requiere_opciones and not self.opciones:
            raise ValueError(f"el campo '{self.nombre}' de tipo {self.tipo} requiere opciones")
        if not requiere_opciones and self.opciones:
            raise ValueError(f"el campo '{self.nombre}' de tipo {self.tipo} no admite opciones")
        if self.depende_de_valores and self.depende_de is None:
            raise ValueError(f"el campo '{self.nombre}' declara valores sin 'depende_de'")
        return self


class FormularioRamo(BaseModel):
    """The full set of questions for a ramo, plus its display grouping."""

    model_config = ConfigDict(extra="forbid")

    version: int = Field(default=1, ge=1)
    campos: list[CampoFormulario] = Field(min_length=1)

    @field_validator("campos")
    @classmethod
    def _nombres_unicos(cls, campos: list[CampoFormulario]) -> list[CampoFormulario]:
        nombres = [campo.nombre for campo in campos]
        duplicados = {n for n in nombres if nombres.count(n) > 1}
        if duplicados:
            raise ValueError(f"campos duplicados: {sorted(duplicados)}")
        return campos

    @model_validator(mode="after")
    def _dependencias_resueltas(self) -> FormularioRamo:
        conocidos = {campo.nombre for campo in self.campos}
        for campo in self.campos:
            if campo.depende_de is not None and campo.depende_de not in conocidos:
                raise ValueError(
                    f"el campo '{campo.nombre}' depende de '{campo.depende_de}', que no existe"
                )
        return self

    @property
    def campos_ordenados(self) -> list[CampoFormulario]:
        return sorted(self.campos, key=lambda campo: (campo.orden, campo.nombre))

    @property
    def campos_requeridos(self) -> list[str]:
        """Fields that must be present when the form is unconditionally shown.

        Conditional fields are excluded: whether they are required depends on
        the answers given, and that is enforced at submission time.
        """
        return [c.nombre for c in self.campos if c.requerido and c.depende_de is None]
