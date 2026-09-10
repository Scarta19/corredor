"""Tenants (brokerages) and the people who work inside them."""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import Boolean, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from corredor.db.base import Base, TenantScoped, Timestamped, UUIDPrimaryKey
from corredor.domain.enums import RolUsuario
from corredor.domain.types import Json, pg_enum

if TYPE_CHECKING:
    from corredor.domain.clientes import Cliente


class Tenant(Base, UUIDPrimaryKey, Timestamped):
    """A brokerage using the platform.

    The first tenant is the pilot client; the architecture assumes there will
    be others (§19 of the platform brief).
    """

    __tablename__ = "tenants"

    slug: Mapped[str] = mapped_column(String(63), unique=True, nullable=False)
    nombre: Mapped[str] = mapped_column(String(160), nullable=False)
    nit: Mapped[str | None] = mapped_column(String(32))
    ciudad: Mapped[str | None] = mapped_column(String(80))
    telefono: Mapped[str | None] = mapped_column(String(32))
    email: Mapped[str | None] = mapped_column(String(160))
    activo: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    #: Per-tenant feature flags and branding, so onboarding a brokerage is
    #: configuration rather than a deploy.
    configuracion: Mapped[dict[str, object]] = mapped_column(Json, default=dict, nullable=False)

    usuarios: Mapped[list[Usuario]] = relationship(
        back_populates="tenant", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Tenant {self.slug}>"


class Usuario(Base, UUIDPrimaryKey, TenantScoped, Timestamped):
    """An advisor, manager or administrator inside a tenant."""

    __tablename__ = "usuarios"
    __table_args__ = (UniqueConstraint("tenant_id", "email", name="usuario_email_tenant"),)

    nombre: Mapped[str] = mapped_column(String(160), nullable=False)
    email: Mapped[str] = mapped_column(String(160), nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    rol: Mapped[RolUsuario] = mapped_column(
        pg_enum(RolUsuario, "rol_usuario"), default=RolUsuario.ASESOR, nullable=False
    )
    telefono: Mapped[str | None] = mapped_column(String(32))
    activo: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    tenant: Mapped[Tenant] = relationship(back_populates="usuarios")
    clientes: Mapped[list[Cliente]] = relationship(back_populates="asesor")

    @property
    def puede_ver_dashboard(self) -> bool:
        return self.rol in (RolUsuario.ADMIN, RolUsuario.GERENTE)

    def __repr__(self) -> str:
        return f"<Usuario {self.email} ({self.rol})>"


__all__ = ["Tenant", "Usuario"]
