"""Domain models.

Importing this package registers every table on `Base.metadata`, which is
what Alembic autogenerate and the test fixtures rely on. Add new models here
when you add them.
"""

from corredor.domain.catalogo import Aseguradora, Ramo
from corredor.domain.clientes import Cliente
from corredor.domain.comercial import (
    Cotizacion,
    Oportunidad,
    OportunidadEvento,
    Solicitud,
)
from corredor.domain.comunicaciones import Comunicacion
from corredor.domain.inteligencia import (
    AnalisisMensaje,
    PuntajeLead,
    RecomendacionCrossSell,
    RiesgoRenovacion,
)
from corredor.domain.polizas import Poliza, Renovacion
from corredor.domain.secuencias import Consecutivo
from corredor.domain.tenancy import Tenant, Usuario

__all__ = [
    "AnalisisMensaje",
    "Aseguradora",
    "Cliente",
    "Comunicacion",
    "Consecutivo",
    "Cotizacion",
    "Oportunidad",
    "OportunidadEvento",
    "Poliza",
    "PuntajeLead",
    "Ramo",
    "RecomendacionCrossSell",
    "Renovacion",
    "RiesgoRenovacion",
    "Solicitud",
    "Tenant",
    "Usuario",
]
