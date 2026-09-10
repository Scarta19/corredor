# 0008 — Submission validation lives in the domain, not at the edge

**Status:** Accepted · 2026-09-10

## Context

Quote forms are defined at runtime ([ADR-0003](0003-formularios-dinamicos.md)),
so a submission's shape is unknown until the ramo is loaded. Neither Postgres
nor a static Pydantic model can check it. Something has to.

The obvious place is the HTTP layer, next to the endpoint that receives it.
That would be wrong here: the web form is the *first* channel to capture these
fields, not the only one. Módulo 3 captures the same fields from a WhatsApp
conversation, and an advisor will eventually key them in from a phone call.
Three callers, one question — "is this a complete, well-formed request?" — and
no good reason for three answers.

## Decision

`corredor.domain.validacion` owns it. Pure functions over a `FormularioRamo`
and a dict: no session, no request, no framework. It validates, coerces and
normalises, returning cleaned answers.

Three properties it guarantees:

1. **Every error at once.** A form that reveals one problem per submission is
   a form people abandon, and an abandoned form is a lead that never arrives.
   Callers get a `campo → mensaje` map.
2. **Normalisation, not just rejection.** `abc-123` becomes `ABC123`,
   `Ana@Test.CO` becomes lowercase, `"2021"` becomes `2021`. What reaches the
   database is consistent regardless of which channel captured it — otherwise
   the same vehicle is two records depending on who typed it.
3. **Conditional fields are enforced both ways.** A field whose condition is
   unmet is not merely optional; sending it is an error. Otherwise a client
   could submit `valor_inmueble` while declaring they are not the owner, and
   the stored record would contradict itself.

The browser re-implements the visibility rule so the form behaves sensibly as
it is filled in. That copy is presentational; the server's is binding.

## Consequences

**We get:** exhaustive unit tests with no database — every type, every
conditional case, every shipped ramo. Módulo 3 inherits validation for free.

**We pay:** one rule — which fields are visible — is expressed twice, in
Python and in TypeScript, and they can drift. The mitigation is that drift is
*safe*: the server rejects anything the browser wrongly allowed, so the failure
mode is a confusing form rather than a corrupt record. Generating the
TypeScript from the Python is the fix if it ever bites.
