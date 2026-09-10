"""Public catalogue endpoints.

These are what make the intelligent quote form possible: the website asks the
API which lines of business exist and what each one needs to be quoted, then
renders whatever it is told. Adding a ramo never requires a frontend release.
"""

from __future__ import annotations

from fastapi import APIRouter, Query
from pydantic import BaseModel, ConfigDict
from sqlalchemy import select

from corredor.api.deps import Sesion, TenantActual
from corredor.core.errors import NoEncontrado
from corredor.domain.catalogo import Ramo
from corredor.domain.enums import TipoCliente
from corredor.domain.formularios import FormularioRamo

router = APIRouter(prefix="/ramos", tags=["catálogo"])


class RamoResumen(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    codigo: str
    nombre: str
    descripcion: str | None
    dirigido_a: TipoCliente | None


class RamoDetalle(RamoResumen):
    formulario: FormularioRamo


@router.get("", summary="Ramos disponibles")
async def listar_ramos(
    session: Sesion,
    tenant: TenantActual,
    dirigido_a: TipoCliente | None = Query(
        default=None,
        description="Filtra los ramos ofrecidos a personas o a empresas.",
    ),
) -> list[RamoResumen]:
    consulta = (
        select(Ramo)
        .where(Ramo.tenant_id == tenant.id, Ramo.activo.is_(True))
        .order_by(Ramo.orden, Ramo.nombre)
    )
    if dirigido_a is not None:
        # A ramo with no audience set is offered to everyone.
        consulta = consulta.where((Ramo.dirigido_a == dirigido_a) | (Ramo.dirigido_a.is_(None)))
    ramos = (await session.scalars(consulta)).all()
    return [RamoResumen.model_validate(r) for r in ramos]


@router.get("/{codigo}", summary="Formulario de cotización de un ramo")
async def obtener_ramo(codigo: str, session: Sesion, tenant: TenantActual) -> RamoDetalle:
    ramo = await session.scalar(
        select(Ramo).where(
            Ramo.tenant_id == tenant.id, Ramo.codigo == codigo, Ramo.activo.is_(True)
        )
    )
    if ramo is None:
        raise NoEncontrado(f"El ramo '{codigo}' no está disponible.")
    return RamoDetalle(
        codigo=ramo.codigo,
        nombre=ramo.nombre,
        descripcion=ramo.descripcion,
        dirigido_a=ramo.dirigido_a,
        formulario=ramo.form,
    )
