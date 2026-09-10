# 0006 — The domain is modelled in Spanish

**Status:** Accepted · 2026-09-09
**Amended by:** [0009 — Documentation is bilingual](0009-documentacion-bilingue.md)

## Context

The users are Colombian insurance brokers. They say *ramo*, *póliza*,
*cotización*, *siniestro*, *asesor*, *prima*. Several of these have no clean
English equivalent: *ramo* is not quite "product" and not quite "line of
business", and *cumplimiento* is a specifically Latin American surety product.

Translating them into English in the schema means every conversation between
a developer and a broker passes through a glossary, and glossaries drift.

## Decision

Domain nouns, enum values and API fields use the business's own vocabulary:
`Cliente`, `Poliza`, `Ramo`, `Oportunidad`, `Renovacion`, and states like
`propuesta_enviada` and `proxima_a_vencer`.

Technical scaffolding stays in English — `Base`, `TenantScoped`, `get_session`,
`create_app` — as do docstrings and comments, so the codebase remains
readable to a contributor who does not speak Spanish.

## Consequences

**We get:** a schema a broker can read and correct. A bug report that says
"the ramo is wrong" maps to exactly one column.

**We pay:** mixed-language identifiers, which look inconsistent until the rule
is understood. Accents are dropped in identifiers (`Poliza`, not `Póliza`) and
kept in every user-facing string.

## Later note

[ADR-0009](0009-documentacion-bilingue.md) revised the documentation half of
this decision: prose now exists in both languages. The part about code stands
exactly as written above.
