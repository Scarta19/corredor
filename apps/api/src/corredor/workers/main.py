"""Arq worker entry point.

Run with `uv run arq corredor.workers.main.WorkerSettings`.

The schedule is intentionally boring: once a day, early, before the office
opens. Renewal thresholds are measured in days, so anything more frequent
produces the same result at more cost — and the sweep is idempotent, so a
missed night is caught up by the next one rather than skipped.
"""

from __future__ import annotations

from arq import cron
from arq.connections import RedisSettings

from corredor.core.config import get_settings
from corredor.core.logging import configure_logging, get_logger
from corredor.db.session import dispose_engine
from corredor.workers.tareas import barrido_diario

log = get_logger(__name__)


async def al_iniciar(_contexto: dict[str, object]) -> None:
    configure_logging(get_settings())
    log.info("worker_iniciado")


async def al_terminar(_contexto: dict[str, object]) -> None:
    await dispose_engine()
    log.info("worker_detenido")


class WorkerSettings:
    functions = [barrido_diario]  # noqa: RUF012 - arq reads this as a plain list
    cron_jobs = [  # noqa: RUF012
        cron(barrido_diario, hour=get_settings().renewal_sweep_hour_utc, minute=0)
    ]
    on_startup = al_iniciar
    on_shutdown = al_terminar
    redis_settings = RedisSettings.from_dsn(str(get_settings().redis_url))
    max_tries = 3
    job_timeout = 600
