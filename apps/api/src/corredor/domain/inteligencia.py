"""The intelligence layer.

The platform brief parks "IA para atención y clasificación" in phase 3. The
schema does not: every model output is a first-class, versioned, explainable
row from day one, because retrofitting an audit trail onto predictions that a
business already acts on is how ML projects lose the trust of the people
using them.

Three rules hold across this module:

1. A prediction always records the model and version that produced it, so a
   regression can be attributed rather than argued about.
2. A prediction always records its input features, so it can be replayed and
   so training sets can be rebuilt from production truth.
3. A prediction never overwrites the business record it describes. Scores sit
   beside `oportunidades` and `polizas`; a human decision always wins.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, Float, ForeignKey, Index, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID as PgUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from corredor.db.base import Base, TenantScoped, Timestamped, UUIDPrimaryKey
from corredor.domain.enums import NivelRiesgo
from corredor.domain.types import Json, pg_enum

if TYPE_CHECKING:
    from corredor.domain.comunicaciones import Comunicacion


class PrediccionMixin:
    """Provenance every model output carries."""

    modelo: Mapped[str] = mapped_column(String(64), nullable=False)
    modelo_version: Mapped[str] = mapped_column(String(32), nullable=False)
    features: Mapped[dict[str, object]] = mapped_column(Json, default=dict, nullable=False)
    calculado_en: Mapped[datetime] = mapped_column(nullable=False)


class PuntajeLead(Base, UUIDPrimaryKey, TenantScoped, Timestamped, PrediccionMixin):
    """How likely an opportunity is to convert, and why.

    Used to order the advisor's queue: with 127 leads in a month and a team
    of three, the question is never "who do we call" but "who first".
    """

    __tablename__ = "puntajes_lead"
    __table_args__ = (
        Index("ix_puntajes_lead_tenant_calculado", "tenant_id", "calculado_en"),
        CheckConstraint("puntaje >= 0 AND puntaje <= 1", name="puntaje_normalizado"),
    )

    oportunidad_id: Mapped[uuid.UUID] = mapped_column(
        PgUUID(as_uuid=True), ForeignKey("oportunidades.id", ondelete="CASCADE"), index=True
    )
    #: Calibrated probability of reaching GANADO.
    puntaje: Mapped[float] = mapped_column(Float, nullable=False)
    nivel: Mapped[NivelRiesgo] = mapped_column(pg_enum(NivelRiesgo, "nivel_riesgo"))
    #: Top contributing features in human-readable form, shown in the CRM so
    #: an advisor can disagree with the model on informed terms.
    explicacion: Mapped[list[dict[str, object]]] = mapped_column(Json, default=list, nullable=False)

    def __repr__(self) -> str:
        return f"<PuntajeLead {self.puntaje:.2f}>"


class RiesgoRenovacion(Base, UUIDPrimaryKey, TenantScoped, Timestamped, PrediccionMixin):
    """Probability that a policy will NOT be renewed.

    Feeds the renewal dashboard: a policy expiring in 45 days with high churn
    risk deserves attention before one expiring in 10 days with low risk.
    """

    __tablename__ = "riesgos_renovacion"
    __table_args__ = (
        Index("ix_riesgos_renovacion_tenant_nivel", "tenant_id", "nivel"),
        CheckConstraint(
            "probabilidad_fuga >= 0 AND probabilidad_fuga <= 1", name="probabilidad_normalizada"
        ),
    )

    poliza_id: Mapped[uuid.UUID] = mapped_column(
        PgUUID(as_uuid=True), ForeignKey("polizas.id", ondelete="CASCADE"), index=True
    )
    probabilidad_fuga: Mapped[float] = mapped_column(Float, nullable=False)
    nivel: Mapped[NivelRiesgo] = mapped_column(pg_enum(NivelRiesgo, "nivel_riesgo"), nullable=False)
    explicacion: Mapped[list[dict[str, object]]] = mapped_column(Json, default=list, nullable=False)

    def __repr__(self) -> str:
        return f"<RiesgoRenovacion {self.nivel} {self.probabilidad_fuga:.2f}>"


class RecomendacionCrossSell(Base, UUIDPrimaryKey, TenantScoped, Timestamped, PrediccionMixin):
    """A next-best-product suggestion for an existing client (§13).

    This is what turns the client base from a database into a source of
    commercial opportunity: someone holding only an auto policy is a
    candidate for hogar, vida or accidentes personales.
    """

    __tablename__ = "recomendaciones_cross_sell"
    __table_args__ = (
        UniqueConstraint(
            "cliente_id", "ramo_id", "modelo_version", name="recomendacion_cliente_ramo_version"
        ),
        Index("ix_recomendaciones_tenant_puntaje", "tenant_id", "puntaje"),
        CheckConstraint("puntaje >= 0 AND puntaje <= 1", name="puntaje_normalizado"),
    )

    cliente_id: Mapped[uuid.UUID] = mapped_column(
        PgUUID(as_uuid=True), ForeignKey("clientes.id", ondelete="CASCADE"), index=True
    )
    ramo_id: Mapped[uuid.UUID] = mapped_column(
        PgUUID(as_uuid=True), ForeignKey("ramos.id", ondelete="CASCADE")
    )
    puntaje: Mapped[float] = mapped_column(Float, nullable=False)
    #: Plain-language justification the advisor can repeat to the client.
    razon: Mapped[str | None] = mapped_column(Text)
    #: Set when an advisor acts on (or dismisses) the suggestion. This is the
    #: feedback signal the next model version trains on.
    aceptada: Mapped[bool | None] = mapped_column()
    revisada_en: Mapped[datetime | None] = mapped_column()

    def __repr__(self) -> str:
        return f"<RecomendacionCrossSell cliente={self.cliente_id} {self.puntaje:.2f}>"


class AnalisisMensaje(Base, UUIDPrimaryKey, TenantScoped, Timestamped, PrediccionMixin):
    """Understanding of one inbound message (Módulo 3).

    The brief's WhatsApp flow is a numbered menu. A menu is a reasonable
    fallback, but people do not write "1" — they write "necesito asegurar mi
    carro". This row is what lets the platform route on meaning, while §8's
    principle still holds: automation handles reception and classification,
    and hands anything needing commercial judgement to a person.
    """

    __tablename__ = "analisis_mensajes"
    __table_args__ = (
        CheckConstraint("confianza >= 0 AND confianza <= 1", name="confianza_normalizada"),
    )

    comunicacion_id: Mapped[uuid.UUID] = mapped_column(
        PgUUID(as_uuid=True),
        ForeignKey("comunicaciones.id", ondelete="CASCADE"),
        unique=True,
        index=True,
    )
    #: cotizar | consultar_poliza | renovar | reclamar | hablar_asesor | otro
    intencion: Mapped[str] = mapped_column(String(48), nullable=False)
    confianza: Mapped[float] = mapped_column(Float, nullable=False)
    ramo_detectado_id: Mapped[uuid.UUID | None] = mapped_column(
        PgUUID(as_uuid=True), ForeignKey("ramos.id", ondelete="SET NULL")
    )
    #: Structured data lifted from free text (placa, ciudad, fechas…), which
    #: pre-fills the quote form instead of asking the client to repeat itself.
    entidades: Mapped[dict[str, object]] = mapped_column(Json, default=dict, nullable=False)
    sentimiento: Mapped[float | None] = mapped_column(Float)
    #: The §8 boundary, made explicit and auditable.
    requiere_humano: Mapped[bool] = mapped_column(default=False, nullable=False)

    comunicacion: Mapped[Comunicacion] = relationship(back_populates="analisis")

    def __repr__(self) -> str:
        return f"<AnalisisMensaje {self.intencion} ({self.confianza:.2f})>"
