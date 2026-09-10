"""Quote request submission — the public end of Módulo 2."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from fastapi import APIRouter, status
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import select

from corredor.api.deps import Sesion, TenantActual
from corredor.core.errors import NoEncontrado
from corredor.domain.catalogo import Ramo
from corredor.domain.enums import Canal
from corredor.services.solicitudes import registrar_solicitud

router = APIRouter(prefix="/solicitudes", tags=["cotizaciones"])


class SolicitudEntrada(BaseModel):
    model_config = ConfigDict(extra="forbid")

    ramo: str = Field(description="Código del ramo, por ejemplo 'automoviles'.")
    respuestas: dict[str, Any] = Field(
        description="Respuestas al formulario del ramo, indexadas por nombre de campo."
    )
    utm: dict[str, Any] = Field(
        default_factory=dict,
        description="Parámetros de origen de la visita, para atribución.",
    )


class SolicitudCreada(BaseModel):
    codigo: str
    ramo: str
    estado: str
    creada_en: datetime
    mensaje: str


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    summary="Registrar una solicitud de cotización",
    responses={
        422: {
            "description": (
                "El formulario tiene errores. `contexto.errores` trae un mensaje por campo."
            )
        },
        404: {"description": "El ramo no existe o no está activo."},
    },
)
async def crear_solicitud(
    entrada: SolicitudEntrada, session: Sesion, tenant: TenantActual
) -> SolicitudCreada:
    """Register a request and create the CRM records that follow from it.

    Everything happens in the request's transaction: the visitor is only told
    the request was received once the client, the opportunity, its first event
    and the lead score are all durable.
    """
    ramo = await session.scalar(
        select(Ramo).where(
            Ramo.tenant_id == tenant.id,
            Ramo.codigo == entrada.ramo,
            Ramo.activo.is_(True),
        )
    )
    if ramo is None:
        raise NoEncontrado(f"El ramo '{entrada.ramo}' no está disponible.")

    solicitud = await registrar_solicitud(
        session,
        tenant_id=tenant.id,
        ramo=ramo,
        canal=Canal.WEB,
        respuestas=entrada.respuestas,
        utm=entrada.utm,
    )

    return SolicitudCreada(
        codigo=solicitud.codigo,
        ramo=ramo.nombre,
        estado=solicitud.estado.value,
        creada_en=solicitud.created_at,
        mensaje=(
            "Solicitud recibida correctamente. Un asesor la tomará y te "
            "contactará el mismo día hábil."
        ),
    )
