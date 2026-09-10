# Corredor

**An AI-native platform for insurance brokers.**

Most brokerages run on a website that only informs, a WhatsApp number, and a
spreadsheet of renewal dates. The information exists; it is just scattered
across three places that never talk to each other, so a lead arrives as a chat
message someone has to transcribe, and a renewal is remembered or it is not.

Corredor is the single system underneath all of it:

```
Cliente → Web → Solicitud → CRM → Asesor → Seguimiento → Venta → Renovación
```

Multi-tenant from the first migration: one deployment serves many brokerages,
each with its own catalogue, forms, pipeline and book of business.

> **Status:** in active development. The domain model, renewal engine,
> intelligence baselines and public catalogue API are implemented and tested;
> modules are being built in the order set out in [the roadmap](docs/roadmap.md).

---

## The six modules

| # | Module | What it does | State |
|---|--------|--------------|-------|
| 1 | **Web profesional** | Public site built to generate actions, not just inform | **Done** |
| 2 | **Cotizador inteligente** | Per-ramo dynamic forms → a structured request, never a chat message to transcribe | In progress |
| 3 | **WhatsApp** | A channel *into* the platform: capture, classify, hand off to a person | Planned |
| 4 | **CRM** | Clients, requests, quotes, policies and the commercial pipeline | Schema |
| 5 | **Renovaciones** | Expiry tracking with escalating 60/30/15/7-day actions | Engine done |
| 6 | **Dashboard** | Conversion funnel, renewal risk buckets, advisor performance | Schema |

## What makes it AI-native

The intelligence isn't a phase-three feature bolted onto a CRM — it's in the
schema from the first migration ([ADR-0005](docs/adr/0005-capa-de-inteligencia.md)):

- **Lead scoring** — which of this month's requests to call first, with the
  reasons shown to the advisor
- **Renewal risk** — days-to-expiry is a calendar; churn probability is a work
  queue
- **Cross-sell** — turning a client base into a source of opportunities (§13)
- **Message understanding** — people write "necesito asegurar mi carro", not "1"

Every prediction records the model, its version, its input features and a
human-readable explanation, and none of them ever overwrite a business record.
A human decision always wins.

The shipped models are **interpretable baselines**, and they say so. Their job
is to work from day one with no labelled data, log the features a real model
will train on, and be a floor that a learned model has to beat.

## Architecture

```
                    ┌──────────────┐  ┌──────────────┐
                    │  apps/web    │  │ apps/admin   │
                    │ público      │  │ CRM · panel  │
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

One API, one database, modules that share a dataset rather than six systems
that synchronise ([ADR-0001](docs/adr/0001-monolito-modular.md)).

| Layer | Choice |
|---|---|
| API | Python 3.13 · FastAPI · SQLAlchemy 2 (async) · Alembic · Pydantic v2 |
| Data | PostgreSQL 17 · Redis (queue + scheduler) |
| Web | Next.js App Router · TypeScript · Tailwind |
| ML | scikit-learn · Anthropic SDK |
| Tooling | uv · ruff · mypy `strict` · pytest · GitHub Actions |

Full walkthrough: [docs/architecture/overview.md](docs/architecture/overview.md).

## Getting started

Requires [uv](https://docs.astral.sh/uv/), Node 22+ and Docker.

```bash
git clone https://github.com/Scarta19/corredor.git
cd corredor
cp .env.example .env

make install     # Python + Node dependencies
make up          # Postgres + Redis
make migrate     # apply migrations
make seed        # a demo tenant with a synthetic book of business
make api         # http://localhost:8000/docs
make web         # http://localhost:3000
```

```bash
make test        # unit tests, no database required
make lint        # ruff + mypy strict
```

All demo data is synthetic and generated from a fixed seed. No real client
data is in this repository.

## Design decisions

The choices worth arguing about are written down, with their costs:

| # | Decision |
|---|----------|
| [0001](docs/adr/0001-monolito-modular.md) | A modular monolith, not six services |
| [0002](docs/adr/0002-multi-tenancy.md) | Shared-schema multi-tenancy from day one |
| [0003](docs/adr/0003-formularios-dinamicos.md) | Quote forms are data, not code |
| [0004](docs/adr/0004-motor-de-renovaciones.md) | Renewals as an idempotent state machine |
| [0005](docs/adr/0005-capa-de-inteligencia.md) | The intelligence layer is structural |
| [0006](docs/adr/0006-lenguaje-del-dominio.md) | The domain is modelled in Spanish |
| [0007](docs/adr/0007-stack-y-monorepo.md) | Python API + Next.js in one repository |

The domain is modelled in the vocabulary brokers actually use — *ramo*,
*póliza*, *cotización*, *asesor* — while the technical scaffolding and all
documentation stay in English.

## License

MIT — see [LICENSE](LICENSE).
