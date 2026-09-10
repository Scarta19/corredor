# 0007 — Python API + Next.js frontends in one repository

**Status:** Accepted · 2026-09-09

## Context

The platform needs a public marketing site that ranks and converts, an
internal CRM, a scheduled worker, and a place for models to live. Those have
genuinely different requirements: the public site wants server rendering and
good Core Web Vitals; the CRM wants rich interactivity behind a login; the
models want the Python data ecosystem.

## Decision

One repository, four deployable pieces:

```
apps/api     FastAPI · SQLAlchemy 2 · Alembic · Postgres   the central logic
apps/web     Next.js App Router                             public site (Módulo 1–2)
apps/admin   Next.js App Router                             CRM + dashboard (Módulo 4, 6)
packages/ml  scikit-learn · Anthropic SDK                   the models
```

Python owns the domain, the persistence and the intelligence. TypeScript owns
rendering. The boundary between them is the OpenAPI schema the API already
generates, so frontend types are derived rather than hand-maintained.

## Consequences

**We get:** a schema change and its frontend consequences land in one commit
and one CI run. Public site and CRM share components and design tokens. The
model library is importable by the API, by a worker and by a notebook.

**We pay:** two toolchains — `uv` and `npm` — in one repo, and CI has to run
both. Contributors need both installed; `make install` exists for that reason.

**We reject:** a single Next.js full-stack app, which would put the domain
logic in TypeScript and leave the models stranded in a service on the side —
backwards for a platform whose stated end state is commercial intelligence.
