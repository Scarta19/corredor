"""The client record — the nucleus of the CRM (Módulo 4)."""

from __future__ import annotations

import uuid
from datetime import date
from typing import TYPE_CHECKING

from sqlalchemy import Date, ForeignKey, Index, String, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID as PgUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from corredor.db.base import Base, TenantScoped, Timestamped, UUIDPrimaryKey
from corredor.domain.enums import Canal, TipoCliente, TipoDocumento
from corredor.domain.types import Json, pg_enum

if TYPE_CHECKING:
    from corredor.domain.comercial import Oportunidad, Solicitud
    from corredor.domain.comunicaciones import Comunicacion
    from corredor.domain.polizas import Poliza
    from corredor.domain.tenancy import Usuario


class Cliente(Base, UUIDPrimaryKey, TenantScoped, Timestamped):
    """A person or company known to the brokerage.

    A cliente is created the moment someone asks for a quote — before any
    sale — so the pipeline and the client base are the same dataset rather
    than two systems that drift apart.
    """

    __tablename__ = "clientes"
    __table_args__ = (
        UniqueConstraint("tenant_id", "documento", name="cliente_documento_tenant"),
        Index("ix_clientes_tenant_telefono", "tenant_id", "telefono"),
        Index("ix_clientes_tenant_email", "tenant_id", "email"),
    )

    tipo: Mapped[TipoCliente] = mapped_column(pg_enum(TipoCliente, "tipo_cliente"), nullable=False)
    nombre: Mapped[str] = mapped_column(String(200), nullable=False)
    tipo_documento: Mapped[TipoDocumento | None] = mapped_column(
        pg_enum(TipoDocumento, "tipo_documento")
    )
    documento: Mapped[str | None] = mapped_column(String(40))
    telefono: Mapped[str | None] = mapped_column(String(32))
    email: Mapped[str | None] = mapped_column(String(160))
    ciudad: Mapped[str | None] = mapped_column(String(80))
    direccion: Mapped[str | None] = mapped_column(String(240))
    fecha_nacimiento: Mapped[date | None] = mapped_column(Date)

    origen: Mapped[Canal] = mapped_column(
        pg_enum(Canal, "canal"), default=Canal.WEB, nullable=False
    )
    fecha_registro: Mapped[date] = mapped_column(
        Date, server_default=func.current_date(), nullable=False
    )
    asesor_id: Mapped[uuid.UUID | None] = mapped_column(
        PgUUID(as_uuid=True), ForeignKey("usuarios.id", ondelete="SET NULL"), index=True
    )
    notas: Mapped[str | None] = mapped_column(String(2000))
    #: Ramo-agnostic profile attributes accumulated across interactions;
    #: feeds the cross-sell model without forcing a migration per attribute.
    perfil: Mapped[dict[str, object]] = mapped_column(Json, default=dict, nullable=False)

    asesor: Mapped[Usuario | None] = relationship(back_populates="clientes")
    solicitudes: Mapped[list[Solicitud]] = relationship(
        back_populates="cliente", cascade="all, delete-orphan"
    )
    oportunidades: Mapped[list[Oportunidad]] = relationship(
        back_populates="cliente", cascade="all, delete-orphan"
    )
    polizas: Mapped[list[Poliza]] = relationship(
        back_populates="cliente", cascade="all, delete-orphan"
    )
    comunicaciones: Mapped[list[Comunicacion]] = relationship(
        back_populates="cliente", cascade="all, delete-orphan"
    )

    @property
    def es_empresa(self) -> bool:
        return self.tipo is TipoCliente.EMPRESA

    def __repr__(self) -> str:
        return f"<Cliente {self.nombre}>"
