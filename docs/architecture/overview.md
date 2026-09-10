# Architecture overview

🇨🇴 [Leer en español](../es/arquitectura/vision-general.md)

## The shape of the system

One API owns the domain. Everything else — the public site, the CRM, the
WhatsApp channel, the scheduled worker — is a client of it. There is exactly
one place where a quote request becomes an opportunity, and exactly one
definition of what "próxima a vencer" means.

```
apps/api/src/corredor/
├── api/           HTTP. May import services; nothing imports it back.
│   ├── deps.py    Session and tenant resolution
│   └── v1/        Versioned routes
├── core/          Settings, logging, domain errors
├── db/            Declarative base, mixins, session lifecycle
├── domain/        The model. Knows nothing about HTTP or background jobs.
├── services/      Business operations over a session
├── workers/       Scheduled and queued work, calling the same services
└── scripts/       Seeding and operational one-offs

packages/ml/src/corredor_ml/
├── base.py        The `Modelo` protocol and `Prediccion` contract
├── lead_scoring.py
├── renovacion.py
└── cross_sell.py  No database, no web framework — importable from a notebook
```

## The data model

Seventeen tables in five groups.

**Tenancy.** `tenants` and `usuarios`. Every other table carries `tenant_id`.

**Catalogue.** `ramos` — lines of business, each owning its quote-form
definition — and `aseguradoras`. Configured per tenant, seeded with sensible
defaults.

**CRM.** `clientes` is the nucleus. A client is created the moment someone
asks for a quote, before any sale, so the pipeline and the client base are the
same dataset rather than two that drift apart.

**Commercial.** `solicitudes` → `oportunidades` → `cotizaciones`, with
`oportunidad_eventos` recording every stage transition. That event table is
what makes the §6 funnel measurable instead of anecdotal: conversion rates,
time-in-stage and advisor performance are all derived from it, so the
dashboard never has to reconstruct history it did not record.

**Policies and renewals.** `polizas`, chained through `poliza_anterior_id` so
retention is measurable rather than inferred, and `renovaciones` — one row per
policy per threshold, uniquely constrained.

**Intelligence.** `puntajes_lead`, `riesgos_renovacion`,
`recomendaciones_cross_sell`, `analisis_mensajes`. All versioned, all
explained, none authoritative over a human decision.

## Three ideas worth understanding

### Forms are data

A `ramo` carries a JSONB `formulario` validated by `FormularioRamo`: ordered
typed fields, with optional dependencies between them. The website asks the
API what a ramo needs and renders the answer. Adding a line of business, or
one more question, never requires a frontend release.

Submissions store both the answers and the `formulario_version` they were
captured against, so a request from six months ago is still interpretable
after the form has changed.

### Renewal planning is a pure function

`planificar_acciones` takes dates and existing thresholds and returns the
actions that are missing. No session, no I/O. The awkward cases — a retried
sweep, a week-long outage, a brokerage's existing book imported three weeks
before its policies expire — are unit tests that run in milliseconds.

The unique constraint on `(poliza_id, umbral_dias)` is the backstop; the
planner is the intent. Together they mean the sweep can run as often as it
likes without ever duplicating a task or re-contacting a client.

### Predictions are records, not columns

A score is a row with provenance, not a float overwritten in place. That costs
four tables and buys three things: a training set that already exists when
there is finally enough data to train on, an explanation the advisor can
disagree with, and the ability to attribute a regression to a model version
rather than argue about it.

## Request lifecycle

1. A visitor picks a ramo on the public site.
2. The site fetches `GET /api/v1/ramos/{codigo}` and renders its form.
3. Submission creates — in one transaction — a `cliente` (or matches an
   existing one), a `solicitud` with a per-tenant code like `COT-000125`, and
   an `oportunidad` at stage `NUEVO`.
4. A `PuntajeLead` is written beside the opportunity, ordering the advisor's
   queue.
5. Every stage change appends an `OportunidadEvento`.
6. A won opportunity produces a `poliza`, which the nightly sweep picks up and
   schedules renewals for.

Steps 3 and 4 are one unit of work: a lead cannot exist half-created.

## Testing

- **Unit** — pure logic, no database. The renewal planner, form validation and
  the model baselines. Milliseconds.
- **Integration** — marked `integration`, requires Postgres. Migrations,
  repository queries, tenant isolation.

CI additionally runs `alembic check`, which fails when a model has changed
without a migration. That class of mistake is otherwise found in a deploy.
