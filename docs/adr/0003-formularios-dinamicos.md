# 0003 — Quote forms are data, not code

**Status:** Accepted · 2026-09-09

## Context

§5 calls the intelligent form one of the most important components of the
project: the visitor picks a line of business and sees only the fields that
line needs. Automóviles asks for placa, marca, línea, modelo and uso;
cumplimiento asks for contract value and term; they have almost nothing in
common beyond identity.

Modelling that as one table per ramo, or one form component per ramo, means a
release every time a brokerage wants to ask one more question — and they will,
because the questions are how they price.

## Decision

Each `ramo` owns a `formulario` JSONB document validated by the
`FormularioRamo` Pydantic model: an ordered list of typed fields, each with a
label, a requiredness flag, options for enumerations, and an optional
dependency on another field's answer.

The public site fetches the definition from `GET /api/v1/ramos/{codigo}` and
renders whatever it receives. Submissions are stored in `solicitudes.respuestas`
alongside the `formulario_version` they were captured against.

## Consequences

**We get:** adding a ramo, or a field, is configuration. The frontend has no
per-ramo code. Historical requests stay interpretable, because the version
that produced them is recorded.

**We pay:** the answers are schemaless to Postgres, so a typed value cannot be
constrained by the database — validation lives entirely in the application,
and `FormularioRamo` is therefore load-bearing and heavily tested. Reporting
across a JSONB field is more awkward than across a column; when a specific
field becomes a first-class business metric, it gets promoted to one.

**We reject:** a table per ramo (a migration per business question) and a
single wide table of nullable columns (which is the generic form the brief
explicitly does not want).
