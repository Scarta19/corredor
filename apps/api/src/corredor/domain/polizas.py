"""Policies and the renewal engine (Módulo 5).

The brief calls renewals "one of the most important assets of the platform",
and it is right: a book of business that is already sold renews every year,
and the only thing standing between the brokerage and that revenue is
remembering to call. This module makes remembering a property of the system.
"""

from __future__ import annotations

import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import (
    CheckConstraint,
    Date,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID as PgUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from corredor.db.base import Base, TenantScoped, Timestamped, UUIDPrimaryKey
from corredor.domain.enums import EstadoPoliza, EstadoRenovacion, VentanaVencimiento
from corredor.domain.types import Dinero, Json, pg_enum

if TYPE_CHECKING:
    from corredor.domain.catalogo import Aseguradora, Ramo
    from corredor.domain.clientes import Cliente
    from corredor.domain.tenancy import Usuario


class Poliza(Base, UUIDPrimaryKey, TenantScoped, Timestamped):
    """An in-force (or historical) policy placed by the brokerage."""

    __tablename__ = "polizas"
    __table_args__ = (
        UniqueConstraint("tenant_id", "aseguradora_id", "numero", name="poliza_numero_aseguradora"),
        # The renewal sweep scans by expiry within a tenant; this is the index
        # that keeps it cheap as the book grows.
        Index("ix_polizas_tenant_vencimiento", "tenant_id", "fecha_vencimiento"),
        Index("ix_polizas_tenant_estado", "tenant_id", "estado"),
        CheckConstraint("fecha_vencimiento > fecha_inicio", name="vigencia_coherente"),
    )

    numero: Mapped[str] = mapped_column(String(64), nullable=False)
    cliente_id: Mapped[uuid.UUID] = mapped_column(
        PgUUID(as_uuid=True), ForeignKey("clientes.id", ondelete="CASCADE"), index=True
    )
    ramo_id: Mapped[uuid.UUID] = mapped_column(
        PgUUID(as_uuid=True), ForeignKey("ramos.id", ondelete="RESTRICT"), index=True
    )
    aseguradora_id: Mapped[uuid.UUID] = mapped_column(
        PgUUID(as_uuid=True), ForeignKey("aseguradoras.id", ondelete="RESTRICT")
    )
    asesor_id: Mapped[uuid.UUID | None] = mapped_column(
        PgUUID(as_uuid=True), ForeignKey("usuarios.id", ondelete="SET NULL"), index=True
    )
    oportunidad_id: Mapped[uuid.UUID | None] = mapped_column(
        PgUUID(as_uuid=True), ForeignKey("oportunidades.id", ondelete="SET NULL")
    )

    fecha_inicio: Mapped[date] = mapped_column(Date, nullable=False)
    fecha_vencimiento: Mapped[date] = mapped_column(Date, nullable=False)
    prima: Mapped[Decimal] = mapped_column(Dinero, nullable=False)
    valor_asegurado: Mapped[Decimal | None] = mapped_column(Dinero)
    estado: Mapped[EstadoPoliza] = mapped_column(
        pg_enum(EstadoPoliza, "estado_poliza"), default=EstadoPoliza.VIGENTE, nullable=False
    )

    #: Chains a renewal back to the policy it replaced, so the platform can
    #: measure true retention instead of counting new policies twice.
    poliza_anterior_id: Mapped[uuid.UUID | None] = mapped_column(
        PgUUID(as_uuid=True), ForeignKey("polizas.id", ondelete="SET NULL")
    )
    detalles: Mapped[dict[str, object]] = mapped_column(Json, default=dict, nullable=False)
    documento_url: Mapped[str | None] = mapped_column(String(500))

    cliente: Mapped[Cliente] = relationship(back_populates="polizas")
    ramo: Mapped[Ramo] = relationship()
    aseguradora: Mapped[Aseguradora] = relationship()
    asesor: Mapped[Usuario | None] = relationship()
    poliza_anterior: Mapped[Poliza | None] = relationship(remote_side="Poliza.id")
    renovaciones: Mapped[list[Renovacion]] = relationship(
        back_populates="poliza", cascade="all, delete-orphan"
    )

    def dias_para_vencimiento(self, hoy: date | None = None) -> int:
        """Days remaining before expiry; negative once the policy has lapsed."""
        referencia = hoy or date.today()
        return (self.fecha_vencimiento - referencia).days

    def ventana(self, hoy: date | None = None) -> VentanaVencimiento:
        """Which renewal-dashboard bucket this policy currently falls into."""
        return VentanaVencimiento.desde_dias(self.dias_para_vencimiento(hoy))

    @property
    def esta_vigente(self) -> bool:
        return self.estado in (EstadoPoliza.VIGENTE, EstadoPoliza.PROXIMA_A_VENCER)

    def __repr__(self) -> str:
        return f"<Poliza {self.numero} vence={self.fecha_vencimiento}>"


class Renovacion(Base, UUIDPrimaryKey, TenantScoped, Timestamped):
    """One scheduled renewal action for one policy at one threshold.

    §12 of the brief defines escalating touchpoints at 60/30/15/7 days. Each
    threshold produces exactly one row — enforced by the unique constraint
    below — which is what lets the daily sweep run as often as it likes
    without ever duplicating a task or re-notifying a client.
    """

    __tablename__ = "renovaciones"
    __table_args__ = (
        UniqueConstraint("poliza_id", "umbral_dias", name="renovacion_umbral_poliza"),
        Index("ix_renovaciones_tenant_estado", "tenant_id", "estado"),
        Index("ix_renovaciones_tenant_objetivo", "tenant_id", "fecha_objetivo"),
        CheckConstraint("umbral_dias >= 0", name="umbral_no_negativo"),
    )

    poliza_id: Mapped[uuid.UUID] = mapped_column(
        PgUUID(as_uuid=True), ForeignKey("polizas.id", ondelete="CASCADE"), index=True
    )
    #: Days-before-expiry threshold that produced this action. 0 means the
    #: expiry date itself.
    umbral_dias: Mapped[int] = mapped_column(Integer, nullable=False)
    fecha_objetivo: Mapped[date] = mapped_column(Date, nullable=False)
    estado: Mapped[EstadoRenovacion] = mapped_column(
        pg_enum(EstadoRenovacion, "estado_renovacion"),
        default=EstadoRenovacion.PENDIENTE,
        nullable=False,
    )
    asesor_id: Mapped[uuid.UUID | None] = mapped_column(
        PgUUID(as_uuid=True), ForeignKey("usuarios.id", ondelete="SET NULL"), index=True
    )
    completada_en: Mapped[datetime | None] = mapped_column()
    notificado_en: Mapped[datetime | None] = mapped_column()
    notas: Mapped[str | None] = mapped_column(Text)

    poliza: Mapped[Poliza] = relationship(back_populates="renovaciones")
    asesor: Mapped[Usuario | None] = relationship()

    @property
    def esta_pendiente(self) -> bool:
        return self.estado in (EstadoRenovacion.PENDIENTE, EstadoRenovacion.EN_GESTION)

    def __repr__(self) -> str:
        return f"<Renovacion poliza={self.poliza_id} d-{self.umbral_dias}>"
