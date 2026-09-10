"""Every interaction with a client, on any channel, in one timeline (Módulo 3).

WhatsApp is treated as a channel into the platform rather than a tool beside
it, so an advisor opening a client sees the chat, the calls and the emails as
one history instead of hunting through three apps.
"""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Index, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID as PgUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from corredor.db.base import Base, TenantScoped, Timestamped, UUIDPrimaryKey
from corredor.domain.enums import Canal, DireccionComunicacion
from corredor.domain.types import Json, pg_enum

if TYPE_CHECKING:
    from corredor.domain.clientes import Cliente
    from corredor.domain.inteligencia import AnalisisMensaje
    from corredor.domain.tenancy import Usuario


class Comunicacion(Base, UUIDPrimaryKey, TenantScoped, Timestamped):
    __tablename__ = "comunicaciones"
    __table_args__ = (
        # Providers retry webhooks; the external id makes ingestion idempotent.
        UniqueConstraint("tenant_id", "external_id", name="comunicacion_external_tenant"),
        Index("ix_comunicaciones_cliente_created", "cliente_id", "created_at"),
    )

    cliente_id: Mapped[uuid.UUID] = mapped_column(
        PgUUID(as_uuid=True), ForeignKey("clientes.id", ondelete="CASCADE"), index=True
    )
    canal: Mapped[Canal] = mapped_column(pg_enum(Canal, "canal"), nullable=False)
    direccion: Mapped[DireccionComunicacion] = mapped_column(
        pg_enum(DireccionComunicacion, "direccion_comunicacion"), nullable=False
    )
    contenido: Mapped[str] = mapped_column(Text, nullable=False)
    #: NULL when the platform itself sent the message.
    usuario_id: Mapped[uuid.UUID | None] = mapped_column(
        PgUUID(as_uuid=True), ForeignKey("usuarios.id", ondelete="SET NULL")
    )
    automatico: Mapped[bool] = mapped_column(default=False, nullable=False)
    #: Provider message id (WhatsApp wamid, email Message-ID, …).
    external_id: Mapped[str | None] = mapped_column(String(160))
    #: Raw provider envelope, kept for debugging and for replaying ingestion.
    payload: Mapped[dict[str, object]] = mapped_column(Json, default=dict, nullable=False)

    cliente: Mapped[Cliente] = relationship(back_populates="comunicaciones")
    usuario: Mapped[Usuario | None] = relationship()
    analisis: Mapped[AnalisisMensaje | None] = relationship(
        back_populates="comunicacion", cascade="all, delete-orphan", uselist=False
    )

    @property
    def es_entrante(self) -> bool:
        return self.direccion is DireccionComunicacion.ENTRANTE

    def __repr__(self) -> str:
        return f"<Comunicacion {self.canal} {self.direccion}>"
