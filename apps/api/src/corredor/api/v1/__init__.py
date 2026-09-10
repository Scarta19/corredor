"""Version 1 of the public and internal API."""

from fastapi import APIRouter

from corredor.api.v1 import auth, crm, health, ramos, solicitudes

router = APIRouter()
router.include_router(health.router)
router.include_router(auth.router)
router.include_router(crm.router)
router.include_router(ramos.router)
router.include_router(solicitudes.router)

__all__ = ["router"]
