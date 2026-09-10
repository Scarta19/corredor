"""Per-tenant human-readable identifiers (COT-000125, POL-000087, …).

Brokers quote these codes over the phone and in WhatsApp, so they must be
short, per-tenant and gap-free — properties a UUID or a global sequence will
not give us. The counter lives in a row that is locked FOR UPDATE while a
code is issued; see `corredor.services.consecutivos`.
"""

from __future__ import annotations

from sqlalchemy import BigInteger, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from corredor.db.base import Base, TenantScoped, Timestamped, UUIDPrimaryKey


class Consecutivo(Base, UUIDPrimaryKey, TenantScoped, Timestamped):
    __tablename__ = "consecutivos"
    __table_args__ = (UniqueConstraint("tenant_id", "entidad", name="consecutivo_entidad_tenant"),)

    #: Logical entity being numbered, e.g. "solicitud" or "poliza".
    entidad: Mapped[str] = mapped_column(String(32), nullable=False)
    prefijo: Mapped[str] = mapped_column(String(8), nullable=False)
    valor: Mapped[int] = mapped_column(BigInteger, default=0, nullable=False)
    ancho: Mapped[int] = mapped_column(default=6, nullable=False)

    def formatear(self, valor: int) -> str:
        return f"{self.prefijo}-{valor:0{self.ancho}d}"

    def __repr__(self) -> str:
        return f"<Consecutivo {self.entidad}={self.valor}>"
