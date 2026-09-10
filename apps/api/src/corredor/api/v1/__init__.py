"""Version 1 of the public and internal API."""

from fastapi import APIRouter

from corredor.api.v1 import health, ramos

router = APIRouter()
router.include_router(health.router)
router.include_router(ramos.router)

__all__ = ["router"]
