"""Per-tenant human-readable codes: COT-000125, CTZ-000087, POL-000042.

Brokers read these aloud on the phone and paste them into WhatsApp, so they
have to be short and per-tenant — properties neither a UUID nor a global
sequence provides.
"""

from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from corredor.domain.secuencias import Consecutivo

PREFIJOS = {"solicitud": "COT", "cotizacion": "CTZ", "poliza": "POL"}


async def siguiente_codigo(session: AsyncSession, *, tenant_id: uuid.UUID, entidad: str) -> str:
    """Issue the next code for an entity within a tenant.

    The counter row is locked FOR UPDATE for the remainder of the transaction,
    so two quote requests arriving at the same instant cannot be handed the
    same number. That serialises concurrent submissions *per tenant and
    entity* — a deliberate trade: the lock is held for microseconds, and a
    duplicate `COT-000125` is a support call that costs far more.
    """
    consecutivo = await session.scalar(
        select(Consecutivo)
        .where(Consecutivo.tenant_id == tenant_id, Consecutivo.entidad == entidad)
        .with_for_update()
    )

    if consecutivo is None:
        # A tenant created before this entity existed, or one seeded without
        # it. Start the series rather than failing the visitor's submission.
        consecutivo = Consecutivo(
            tenant_id=tenant_id,
            entidad=entidad,
            prefijo=PREFIJOS.get(entidad, entidad[:3].upper()),
            valor=0,
        )
        session.add(consecutivo)
        await session.flush()

    consecutivo.valor += 1
    await session.flush()
    return consecutivo.formatear(consecutivo.valor)
