"""FastAPI application factory.

This is the "API / LÓGICA CENTRAL" box of the architecture diagram: the one
place the website, the CRM, the WhatsApp channel and the dashboard all talk
to, so that adding a module never means adding a second source of truth.
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from corredor import __version__
from corredor.api.v1 import router as router_v1
from corredor.core.config import Settings, get_settings
from corredor.core.errors import CorredorError
from corredor.core.logging import configure_logging, get_logger
from corredor.db.session import dispose_engine

log = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    settings: Settings = app.state.settings
    log.info("api_iniciando", entorno=settings.environment, version=__version__)
    yield
    await dispose_engine()
    log.info("api_detenida")


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or get_settings()
    configure_logging(settings)

    app = FastAPI(
        title=f"{settings.project_name} API",
        version=__version__,
        summary="Plataforma digital para intermediarios de seguros.",
        docs_url="/docs" if not settings.is_production else None,
        redoc_url=None,
        lifespan=lifespan,
    )
    app.state.settings = settings

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.exception_handler(CorredorError)
    async def manejar_error_dominio(_: Request, exc: CorredorError) -> JSONResponse:
        """Domain errors answer with a stable machine-readable code.

        Clients branch on `codigo`, never on the prose in `mensaje`, so the
        wording stays free to change.
        """
        if exc.status_code >= 500:
            log.error("error_dominio", codigo=exc.codigo, mensaje=exc.mensaje, **exc.contexto)
        return JSONResponse(status_code=exc.status_code, content=exc.to_payload())

    app.include_router(router_v1, prefix=settings.api_v1_prefix)
    return app


app = create_app()
