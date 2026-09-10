# Corredor

[![CI](https://github.com/Scarta19/corredor/actions/workflows/ci.yml/badge.svg)](https://github.com/Scarta19/corredor/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

**Plataforma digital para intermediarios de seguros, con inteligencia comercial desde el diseño.**

🇬🇧 [Read this in English](README.md)

La mayoría de las agencias de seguros funciona con una página web que solo
informa, un número de WhatsApp y una hoja de cálculo con las fechas de
vencimiento. La información existe; lo que no existe es un sitio donde esas
tres cosas se hablen. Así, un prospecto llega como un mensaje de chat que
alguien tiene que transcribir, y una renovación se recuerda o no se recuerda.

Corredor es el sistema que va debajo de todo eso:

```
Cliente → Web → Solicitud → CRM → Asesor → Seguimiento → Venta → Renovación
```

Multi-tenant desde la primera migración: un mismo despliegue atiende a varias
agencias, cada una con su catálogo, sus formularios, su pipeline y su cartera.

> **Estado:** en desarrollo activo. Los módulos 1 y 2 están terminados; el
> resto avanza en el orden de [la hoja de ruta](docs/es/hoja-de-ruta.md).

---

## Los seis módulos

| # | Módulo | Qué hace | Estado |
|---|--------|----------|--------|
| 1 | **Web profesional** | Sitio público diseñado para generar acciones, no solo para informar | **Listo** |
| 2 | **Cotizador inteligente** | Formularios por ramo → una solicitud estructurada, nunca un chat por transcribir | **Listo** |
| 3 | **WhatsApp** | Un canal *hacia dentro* de la plataforma: recibe, clasifica y deriva a una persona | Pendiente |
| 4 | **CRM** | Clientes, solicitudes, cotizaciones, pólizas y el pipeline comercial | Esquema |
| 5 | **Renovaciones** | Control de vencimientos con acciones escalonadas a 60/30/15/7 días | Motor listo |
| 6 | **Dashboard** | Embudo de conversión, riesgo de renovación, desempeño por asesor | Esquema |

## Qué significa "con inteligencia desde el diseño"

La inteligencia no es una función de fase 3 atornillada sobre un CRM: está en
el esquema desde la primera migración ([ADR-0005](docs/es/adr/0005-capa-de-inteligencia.md)).

- **Puntaje de leads** — a cuál de las solicitudes del mes llamar primero, con
  las razones a la vista del asesor
- **Riesgo de renovación** — los días al vencimiento son un calendario; la
  probabilidad de fuga es una cola de trabajo
- **Venta cruzada** — convertir la base de clientes en una fuente de
  oportunidades (§13)
- **Comprensión de mensajes** — la gente escribe "necesito asegurar mi carro",
  no "1"

Cada predicción guarda el modelo, su versión, las variables que la produjeron
y una explicación legible. Ninguna sobrescribe un registro del negocio: la
decisión de una persona siempre manda.

Los modelos que van hoy son **líneas base interpretables**, y lo dicen de
frente. Su trabajo es funcionar desde el primer día sin datos etiquetados,
registrar las variables con las que se entrenará el modelo real, y ser el piso
que ese modelo tendrá que superar.

## Arquitectura

```
                    ┌──────────────┐  ┌──────────────┐
                    │  apps/web    │  │ apps/admin   │
                    │  público     │  │ CRM · panel  │
                    └──────┬───────┘  └──────┬───────┘
                           └────────┬────────┘
                            ┌───────▼────────┐
                            │   apps/api     │   FastAPI · lógica central
                            └───────┬────────┘
              ┌────────────┬────────┼────────┬────────────┐
              ▼            ▼        ▼        ▼            ▼
            CRM      Cotizaciones  Renov.  WhatsApp   packages/ml
              └────────────┴────────┼────────┴────────────┘
                            ┌───────▼────────┐
                            │   PostgreSQL   │
                            └────────────────┘
```

Una sola API, una sola base de datos, módulos que comparten un mismo conjunto
de información en lugar de seis sistemas que se sincronizan
([ADR-0001](docs/es/adr/0001-monolito-modular.md)).

| Capa | Elección |
|---|---|
| API | Python 3.13 · FastAPI · SQLAlchemy 2 (async) · Alembic · Pydantic v2 |
| Datos | PostgreSQL 17 · Redis (cola y agendador) |
| Web | Next.js App Router · TypeScript · Tailwind |
| ML | scikit-learn · SDK de Anthropic |
| Herramientas | uv · ruff · mypy `strict` · pytest · GitHub Actions |

Recorrido completo: [docs/es/arquitectura/vision-general.md](docs/es/arquitectura/vision-general.md).

## Cómo levantarlo

Requiere [uv](https://docs.astral.sh/uv/), Node 22+ y Docker.

```bash
git clone https://github.com/Scarta19/corredor.git
cd corredor
cp .env.example .env

make install     # dependencias de Python y de Node
make up          # Postgres + Redis
make migrate     # aplica las migraciones
make seed        # una agencia de demostración con cartera sintética
make api         # http://localhost:8000/docs
make web         # http://localhost:3000
```

```bash
make test        # pruebas unitarias, sin base de datos
make lint        # ruff + mypy strict
```

Todos los datos de demostración son sintéticos y se generan con una semilla
fija. En este repositorio no hay información de ningún cliente real.

## Decisiones de diseño

Lo que valía la pena discutir está escrito, con su costo:

| # | Decisión |
|---|----------|
| [0001](docs/es/adr/0001-monolito-modular.md) | Un monolito modular, no seis servicios |
| [0002](docs/es/adr/0002-multi-tenancy.md) | Multi-tenancy de esquema compartido desde el primer día |
| [0003](docs/es/adr/0003-formularios-dinamicos.md) | Los formularios de cotización son datos, no código |
| [0004](docs/es/adr/0004-motor-de-renovaciones.md) | Las renovaciones son una máquina de estados idempotente |
| [0005](docs/es/adr/0005-capa-de-inteligencia.md) | La capa de inteligencia es estructural |
| [0006](docs/es/adr/0006-lenguaje-del-dominio.md) | El dominio se modela en español |
| [0007](docs/es/adr/0007-stack-y-monorepo.md) | API en Python y frontends Next.js en un solo repositorio |
| [0008](docs/es/adr/0008-validacion-en-el-dominio.md) | La validación de solicitudes vive en el dominio |
| [0009](docs/es/adr/0009-documentacion-bilingue.md) | La documentación es bilingüe |

El dominio se modela con el vocabulario que los intermediarios usan de verdad
—*ramo*, *póliza*, *cotización*, *asesor*—, mientras que la infraestructura
técnica y los comentarios del código se mantienen en inglés.

## Licencia

MIT — ver [LICENSE](LICENSE).
