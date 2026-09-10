"""Create a demo tenant with a believable book of business.

Run with `make seed`. Everything here is synthetic: names come from a fixed
list, and the numbers are generated from a fixed seed so the demo looks the
same on every machine. No real client data ever enters this repository.
"""

from __future__ import annotations

import asyncio
import random
from datetime import date, timedelta
from decimal import Decimal

from pwdlib import PasswordHash
from sqlalchemy import select

from corredor.core.config import get_settings
from corredor.core.logging import configure_logging, get_logger
from corredor.db.session import dispose_engine, get_session_factory
from corredor.domain.catalogo import Aseguradora, Ramo
from corredor.domain.clientes import Cliente
from corredor.domain.enums import (
    Canal,
    EstadoPoliza,
    RolUsuario,
    TipoCliente,
    TipoDocumento,
)
from corredor.domain.polizas import Poliza
from corredor.domain.secuencias import Consecutivo
from corredor.domain.tenancy import Tenant, Usuario
from corredor.scripts.ramos_base import RAMOS_BASE

log = get_logger(__name__)
hasher = PasswordHash.recommended()

SLUG_DEMO = "demo"
SEMILLA = 20260909

ASEGURADORAS = [
    "Seguros Bolívar",
    "Sura",
    "Allianz",
    "Mapfre",
    "Previsora",
    "Liberty",
]

NOMBRES = [
    "Juan Pérez",
    "María Gómez",
    "Carlos Ramírez",
    "Ana Torres",
    "Luis Herrera",
    "Diana Castro",
    "Jorge Mejía",
    "Paula Ríos",
    "Andrés Vargas",
    "Laura Peña",
    "Miguel Ospina",
    "Sandra Lozano",
    "Felipe Cárdenas",
    "Natalia Duarte",
    "Ricardo Salazar",
    "Camila Restrepo",
    "Óscar Bedoya",
    "Valentina Arias",
]

EMPRESAS = [
    "Constructora del Bajo Cauca S.A.S.",
    "Transportes Río Grande Ltda.",
    "Agroinsumos del Norte S.A.S.",
    "Comercializadora La Esperanza",
    "Ingeniería y Montajes del Caribe",
    "Distribuidora Central S.A.S.",
]

ASESORES = [
    ("Carlos Andrés Mesa", "carlos@demo.test", RolUsuario.ASESOR),
    ("Laura Jiménez", "laura@demo.test", RolUsuario.ASESOR),
    ("Sofía Naranjo", "sofia@demo.test", RolUsuario.GERENTE),
]

CLAVE_DEMO = "corredor-demo"


async def sembrar() -> None:
    configure_logging(get_settings())
    rng = random.Random(SEMILLA)  # noqa: S311 - demo data, not security
    factory = get_session_factory()

    async with factory() as session:
        existente = await session.scalar(select(Tenant).where(Tenant.slug == SLUG_DEMO))
        if existente is not None:
            log.info("seed_omitido", motivo="el tenant demo ya existe", slug=SLUG_DEMO)
            return

        tenant = Tenant(
            slug=SLUG_DEMO,
            nombre="Agencia Demo de Seguros",
            ciudad="Caucasia",
            telefono="+57 300 000 0000",
            email="contacto@demo.test",
            configuracion={
                "whatsapp": "+573000000000",
                "eslogan": "Asesoría en seguros, sin vueltas.",
            },
        )
        session.add(tenant)
        await session.flush()

        admin = Usuario(
            tenant_id=tenant.id,
            nombre="Administrador Demo",
            email="admin@demo.test",
            password_hash=hasher.hash(CLAVE_DEMO),
            rol=RolUsuario.ADMIN,
        )
        session.add(admin)
        usuarios = [admin]
        for nombre, email, rol in ASESORES:
            usuario = Usuario(
                tenant_id=tenant.id,
                nombre=nombre,
                email=email,
                password_hash=hasher.hash(CLAVE_DEMO),
                rol=rol,
            )
            session.add(usuario)
            usuarios.append(usuario)

        session.add_all(
            [
                Consecutivo(tenant_id=tenant.id, entidad="solicitud", prefijo="COT"),
                Consecutivo(tenant_id=tenant.id, entidad="cotizacion", prefijo="CTZ"),
                Consecutivo(tenant_id=tenant.id, entidad="poliza", prefijo="POL"),
            ]
        )

        ramos: dict[str, Ramo] = {}
        for definicion in RAMOS_BASE:
            ramo = Ramo(tenant_id=tenant.id, **definicion)
            session.add(ramo)
            ramos[ramo.codigo] = ramo

        aseguradoras = [Aseguradora(tenant_id=tenant.id, nombre=n) for n in ASEGURADORAS]
        session.add_all(aseguradoras)
        await session.flush()

        asesores = [u for u in usuarios if u.rol is not RolUsuario.ADMIN]
        clientes: list[Cliente] = []

        for i, nombre in enumerate(NOMBRES):
            clientes.append(
                Cliente(
                    tenant_id=tenant.id,
                    tipo=TipoCliente.PERSONA,
                    nombre=nombre,
                    tipo_documento=TipoDocumento.CC,
                    documento=str(1_000_000_000 + rng.randrange(99_999_999)),
                    telefono=f"+57 3{rng.randrange(10, 25)}{rng.randrange(1000000, 9999999)}",
                    email=f"{nombre.split()[0].lower()}{i}@demo.test",
                    ciudad=rng.choice(["Caucasia", "Medellín", "Montería", "Planeta Rica"]),
                    origen=rng.choice([Canal.WEB, Canal.WHATSAPP, Canal.REFERIDO]),
                    asesor_id=rng.choice(asesores).id,
                )
            )
        for i, nombre in enumerate(EMPRESAS):
            clientes.append(
                Cliente(
                    tenant_id=tenant.id,
                    tipo=TipoCliente.EMPRESA,
                    nombre=nombre,
                    tipo_documento=TipoDocumento.NIT,
                    documento=f"9{rng.randrange(10_000_000, 99_999_999)}",
                    telefono=f"+57 60{rng.randrange(1000000, 9999999)}",
                    email=f"contacto{i}@empresa.test",
                    ciudad="Caucasia",
                    origen=Canal.REFERIDO,
                    asesor_id=rng.choice(asesores).id,
                )
            )
        session.add_all(clientes)
        await session.flush()

        # A book of policies whose expiry dates are spread across every bucket
        # of the renewal dashboard, so the §15 view has something to show.
        hoy = date.today()
        desplazamientos = [3, 5, 9, 12, 18, 25, 28, 34, 40, 52, 58, 75, 90, 120, 200, -10, -45]
        for indice, cliente in enumerate(clientes):
            codigos = (
                ["empresarial", "cumplimiento", "responsabilidad_civil"]
                if cliente.tipo is TipoCliente.EMPRESA
                else ["automoviles", "hogar", "vida", "accidentes_personales"]
            )
            for n in range(rng.randint(1, 2)):
                ramo = ramos[rng.choice(codigos)]
                dias = desplazamientos[(indice * 2 + n) % len(desplazamientos)]
                vencimiento = hoy + timedelta(days=dias)
                estado = EstadoPoliza.VENCIDA if dias < 0 else EstadoPoliza.VIGENTE
                session.add(
                    Poliza(
                        tenant_id=tenant.id,
                        numero=f"{ramo.codigo[:4].upper()}-{100000 + indice * 10 + n}",
                        cliente_id=cliente.id,
                        ramo_id=ramo.id,
                        aseguradora_id=rng.choice(aseguradoras).id,
                        asesor_id=cliente.asesor_id,
                        fecha_inicio=vencimiento - timedelta(days=365),
                        fecha_vencimiento=vencimiento,
                        prima=Decimal(rng.randrange(400_000, 8_000_000)),
                        estado=estado,
                    )
                )

        await session.commit()
        log.info(
            "seed_completado",
            tenant=SLUG_DEMO,
            ramos=len(ramos),
            clientes=len(clientes),
            usuarios=len(usuarios),
        )
        print(
            f"\nTenant demo creado.\n"
            f"  Ingreso al CRM: admin@demo.test / {CLAVE_DEMO}\n"
            f"  Cabecera para la web pública: X-Tenant: {SLUG_DEMO}\n"
        )


def main() -> None:
    try:
        asyncio.run(sembrar())
    finally:
        asyncio.run(dispose_engine())


if __name__ == "__main__":
    main()
