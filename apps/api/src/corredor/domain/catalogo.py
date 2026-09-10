"""Reference data a brokerage configures once: lines of business and insurers."""

from __future__ import annotations

from sqlalchemy import Boolean, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from corredor.db.base import Base, TenantScoped, Timestamped, UUIDPrimaryKey
from corredor.domain.enums import TipoCliente
from corredor.domain.formularios import FormularioRamo
from corredor.domain.types import Json, pg_enum


class Ramo(Base, UUIDPrimaryKey, TenantScoped, Timestamped):
    """A line of insurance business: automóviles, vida, cumplimiento, hogar…

    A ramo carries its own quote-form definition, which is what makes the
    intelligent form "intelligent": the visitor picks a ramo and only ever
    sees the fields that ramo needs.
    """

    __tablename__ = "ramos"
    __table_args__ = (UniqueConstraint("tenant_id", "codigo", name="ramo_codigo_tenant"),)

    codigo: Mapped[str] = mapped_column(String(48), nullable=False)
    nombre: Mapped[str] = mapped_column(String(120), nullable=False)
    descripcion: Mapped[str | None] = mapped_column(String(500))
    dirigido_a: Mapped[TipoCliente | None] = mapped_column(
        pg_enum(TipoCliente, "tipo_cliente"),
        doc="Restrict a ramo to personas or empresas; NULL means both.",
    )
    #: Serialised `FormularioRamo`. Validated through the Pydantic model on
    #: every write, so malformed forms can never reach the public site.
    formulario: Mapped[dict[str, object]] = mapped_column(Json, nullable=False)
    orden: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    activo: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    @property
    def form(self) -> FormularioRamo:
        return FormularioRamo.model_validate(self.formulario)

    def __repr__(self) -> str:
        return f"<Ramo {self.codigo}>"


class Aseguradora(Base, UUIDPrimaryKey, TenantScoped, Timestamped):
    """An insurance carrier the brokerage places business with."""

    __tablename__ = "aseguradoras"
    __table_args__ = (UniqueConstraint("tenant_id", "nombre", name="aseguradora_nombre_tenant"),)

    nombre: Mapped[str] = mapped_column(String(160), nullable=False)
    nit: Mapped[str | None] = mapped_column(String(32))
    contacto: Mapped[str | None] = mapped_column(String(160))
    activo: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    def __repr__(self) -> str:
        return f"<Aseguradora {self.nombre}>"
