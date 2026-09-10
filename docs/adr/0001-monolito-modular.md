# 0001 — A modular monolith, not six services

**Status:** Accepted · 2026-09-09

## Context

The brief describes six modules — web, quoting, WhatsApp, CRM, renewals,
dashboard — and §17 is explicit that they must not become six independent
systems. They share one dataset: a WhatsApp message becomes a quote request,
which becomes an opportunity, which becomes a policy, which generates
renewals, all describing the same client.

The team building this is small. The first deployment serves one brokerage.

## Decision

One deployable API, internally divided by module boundaries:

- `domain/` — the model, with no knowledge of transport or storage mechanics
- `services/` — business operations, taking a session and returning domain objects
- `api/` — HTTP, which is allowed to import services but never the reverse
- `workers/` — scheduled and queued work, calling the same services as HTTP
- `packages/ml/` — models, importable with no database or web framework attached

Modules talk through service functions and the shared database, not over HTTP.

## Consequences

**We get:** one transaction across a quote request and its opportunity, so a
lead cannot be half-created. One migration history. One deploy. Refactoring a
boundary is an editor operation rather than a coordinated release.

**We pay:** the whole API scales as one unit, and nothing structural stops a
careless import from crossing a boundary — CI would have to grow an import
lint if that starts happening.

**We keep open:** services are the natural seam. When one module genuinely
needs separate scaling — the WhatsApp webhook is the likely first — it can be
extracted behind its existing service interface without touching callers.
