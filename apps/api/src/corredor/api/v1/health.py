"""Liveness and readiness."""

from __future__ import annotations

from fastapi import APIRouter, status
from sqlalchemy import text

from corredor import __version__
from corredor.api.deps import Sesion

router = APIRouter(tags=["salud"])


@router.get("/health", summary="Liveness")
async def health() -> dict[str, str]:
    """The process is up. Never touches a dependency, so it never flaps."""
    return {"estado": "ok", "version": __version__}


@router.get(
    "/ready",
    summary="Readiness",
    responses={status.HTTP_503_SERVICE_UNAVAILABLE: {"description": "Dependencia caída"}},
)
async def ready(session: Sesion) -> dict[str, str]:
    """The process can serve traffic: the database answers."""
    await session.execute(text("SELECT 1"))
    return {"estado": "listo"}
