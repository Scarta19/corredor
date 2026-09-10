"""Run the renewal sweep once, from the command line.

Useful after importing a book of business, or to catch up after the scheduler
has been down. Safe to run at any time and any number of times — see
`corredor.services.renovaciones.planificar_acciones`.
"""

from __future__ import annotations

import asyncio

from corredor.db.session import dispose_engine
from corredor.workers.tareas import ejecutar_barrido


async def _ejecutar() -> None:
    try:
        print(await ejecutar_barrido())
    finally:
        await dispose_engine()


def main() -> None:
    asyncio.run(_ejecutar())


if __name__ == "__main__":
    main()
