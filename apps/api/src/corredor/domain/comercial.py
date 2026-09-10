"""The commercial path: request → opportunity → quotation → won or lost.

This mirrors §6 and §10 of the platform brief. Every stage transition is
recorded as an event, which is what later makes the funnel in Módulo 6
measurable rather than anecdotal.
"""

from __future__ import annotations

import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import Date, ForeignKey, Index, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID as PgUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from corredor.db.base import Base, TenantScoped, Timestamped, UUIDPrimaryKey
from corredor.domain.enums import (
    Canal,
    EstadoCotizacion,
    EstadoSolicitud,
    EtapaOportunidad,
    MotivoPerdida,
)
from corredor.domain.types import Dinero, Json, pg_enum

if TYPE_CHECKING:
    from corredor.domain.catalogo import Aseguradora, Ramo
    from corredor.domain.clientes import Cliente
    from corredor.domain.tenancy import Usuario


class Solicitud(Base, UUIDPrimaryKey, TenantScoped, Timestamped):
    """An inbound quote request, from the web form or from WhatsApp.

    The request is stored as structured data the moment it arrives, so nobody
    has to transcribe a chat message into a spreadsheet later.
    """

    __tablename__ = "solicitudes"
    __table_args__ = (
        UniqueConstraint("tenant_id", "codigo", name="solicitud_codigo_tenant"),
        Index("ix_solicitudes_tenant_estado", "tenant_id", "estado"),
    )

    codigo: Mapped[str] = mapped_column(String(24), nullable=False)
    cliente_id: Mapped[uuid.UUID] = mapped_column(
        PgUUID(as_uuid=True), ForeignKey("clientes.id", ondelete="CASCADE"), index=True
    )
    ramo_id: Mapped[uuid.UUID] = mapped_column(
        PgUUID(as_uuid=True), ForeignKey("ramos.id", ondelete="RESTRICT"), index=True
    )
    canal: Mapped[Canal] = mapped_column(pg_enum(Canal, "canal"), nullable=False)
    estado: Mapped[EstadoSolicitud] = mapped_column(
        pg_enum(EstadoSolicitud, "estado_solicitud"),
        default=EstadoSolicitud.NUEVA,
        nullable=False,
    )
    #: The answers given to the ramo's dynamic form, keyed by field name, plus
    #: the form version they were captured against.
    respuestas: Mapped[dict[str, object]] = mapped_column(Json, nullable=False)
    formulario_version: Mapped[int] = mapped_column(default=1, nullable=False)
    asesor_id: Mapped[uuid.UUID | None] = mapped_column(
        PgUUID(as_uuid=True), ForeignKey("usuarios.id", ondelete="SET NULL"), index=True
    )
    asignada_en: Mapped[datetime | None] = mapped_column()
    #: Where the visitor came from, for attribution.
    utm: Mapped[dict[str, object]] = mapped_column(Json, default=dict, nullable=False)

    cliente: Mapped[Cliente] = relationship(back_populates="solicitudes")
    ramo: Mapped[Ramo] = relationship()
    asesor: Mapped[Usuario | None] = relationship()
    oportunidad: Mapped[Oportunidad | None] = relationship(back_populates="solicitud")

    @property
    def esta_asignada(self) -> bool:
        return self.asesor_id is not None

    def __repr__(self) -> str:
        return f"<Solicitud {self.codigo}>"


class Oportunidad(Base, UUIDPrimaryKey, TenantScoped, Timestamped):
    """A commercial opportunity moving through the pipeline of §10."""

    __tablename__ = "oportunidades"
    __table_args__ = (
        Index("ix_oportunidades_tenant_etapa", "tenant_id", "etapa"),
        Index("ix_oportunidades_tenant_asesor", "tenant_id", "asesor_id"),
    )

    cliente_id: Mapped[uuid.UUID] = mapped_column(
        PgUUID(as_uuid=True), ForeignKey("clientes.id", ondelete="CASCADE"), index=True
    )
    ramo_id: Mapped[uuid.UUID] = mapped_column(
        PgUUID(as_uuid=True), ForeignKey("ramos.id", ondelete="RESTRICT"), index=True
    )
    solicitud_id: Mapped[uuid.UUID | None] = mapped_column(
        PgUUID(as_uuid=True), ForeignKey("solicitudes.id", ondelete="SET NULL"), unique=True
    )
    asesor_id: Mapped[uuid.UUID | None] = mapped_column(
        PgUUID(as_uuid=True), ForeignKey("usuarios.id", ondelete="SET NULL")
    )

    etapa: Mapped[EtapaOportunidad] = mapped_column(
        pg_enum(EtapaOportunidad, "etapa_oportunidad"),
        default=EtapaOportunidad.NUEVO,
        nullable=False,
    )
    valor_estimado: Mapped[Decimal | None] = mapped_column(Dinero)
    fecha_cierre_estimada: Mapped[date | None] = mapped_column(Date)
    cerrada_en: Mapped[datetime | None] = mapped_column()
    motivo_perdida: Mapped[MotivoPerdida | None] = mapped_column(
        pg_enum(MotivoPerdida, "motivo_perdida")
    )
    notas: Mapped[str | None] = mapped_column(Text)

    cliente: Mapped[Cliente] = relationship(back_populates="oportunidades")
    ramo: Mapped[Ramo] = relationship()
    solicitud: Mapped[Solicitud | None] = relationship(back_populates="oportunidad")
    asesor: Mapped[Usuario | None] = relationship()
    eventos: Mapped[list[OportunidadEvento]] = relationship(
        back_populates="oportunidad",
        cascade="all, delete-orphan",
        order_by="OportunidadEvento.created_at",
    )
    cotizaciones: Mapped[list[Cotizacion]] = relationship(
        back_populates="oportunidad", cascade="all, delete-orphan"
    )

    @property
    def esta_abierta(self) -> bool:
        return not self.etapa.es_terminal

    def __repr__(self) -> str:
        return f"<Oportunidad {self.id} {self.etapa}>"


class OportunidadEvento(Base, UUIDPrimaryKey, TenantScoped, Timestamped):
    """An immutable record of one pipeline transition.

    Conversion rates, time-in-stage and advisor performance are all derived
    from this table, so the dashboard never has to guess at history.
    """

    __tablename__ = "oportunidad_eventos"
    __table_args__ = (Index("ix_oportunidad_eventos_tenant_created", "tenant_id", "created_at"),)

    oportunidad_id: Mapped[uuid.UUID] = mapped_column(
        PgUUID(as_uuid=True), ForeignKey("oportunidades.id", ondelete="CASCADE"), index=True
    )
    etapa_anterior: Mapped[EtapaOportunidad | None] = mapped_column(
        pg_enum(EtapaOportunidad, "etapa_oportunidad")
    )
    etapa_nueva: Mapped[EtapaOportunidad] = mapped_column(
        pg_enum(EtapaOportunidad, "etapa_oportunidad"), nullable=False
    )
    usuario_id: Mapped[uuid.UUID | None] = mapped_column(
        PgUUID(as_uuid=True), ForeignKey("usuarios.id", ondelete="SET NULL")
    )
    #: True when the transition was made by an automation rather than a person.
    automatico: Mapped[bool] = mapped_column(default=False, nullable=False)
    nota: Mapped[str | None] = mapped_column(Text)

    oportunidad: Mapped[Oportunidad] = relationship(back_populates="eventos")

    def __repr__(self) -> str:
        return f"<OportunidadEvento {self.etapa_anterior}->{self.etapa_nueva}>"


class Cotizacion(Base, UUIDPrimaryKey, TenantScoped, Timestamped):
    """A concrete offer from one carrier for one opportunity.

    An opportunity typically carries several, one per aseguradora; comparing
    them is the advisor's actual job.
    """

    __tablename__ = "cotizaciones"
    __table_args__ = (UniqueConstraint("tenant_id", "codigo", name="cotizacion_codigo_tenant"),)

    codigo: Mapped[str] = mapped_column(String(24), nullable=False)
    oportunidad_id: Mapped[uuid.UUID] = mapped_column(
        PgUUID(as_uuid=True), ForeignKey("oportunidades.id", ondelete="CASCADE"), index=True
    )
    aseguradora_id: Mapped[uuid.UUID] = mapped_column(
        PgUUID(as_uuid=True), ForeignKey("aseguradoras.id", ondelete="RESTRICT")
    )
    estado: Mapped[EstadoCotizacion] = mapped_column(
        pg_enum(EstadoCotizacion, "estado_cotizacion"),
        default=EstadoCotizacion.BORRADOR,
        nullable=False,
    )
    prima: Mapped[Decimal] = mapped_column(Dinero, nullable=False)
    deducible: Mapped[Decimal | None] = mapped_column(Dinero)
    valor_asegurado: Mapped[Decimal | None] = mapped_column(Dinero)
    vigencia_desde: Mapped[date | None] = mapped_column(Date)
    vigencia_hasta: Mapped[date | None] = mapped_column(Date)
    #: Carrier-specific coverage breakdown; shapes differ per ramo and insurer.
    coberturas: Mapped[dict[str, object]] = mapped_column(Json, default=dict, nullable=False)
    enviada_en: Mapped[datetime | None] = mapped_column()
    documento_url: Mapped[str | None] = mapped_column(String(500))

    oportunidad: Mapped[Oportunidad] = relationship(back_populates="cotizaciones")
    aseguradora: Mapped[Aseguradora] = relationship()

    def __repr__(self) -> str:
        return f"<Cotizacion {self.codigo}>"
