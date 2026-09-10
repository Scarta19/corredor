# Architecture Decision Records

🇨🇴 [Leer en español](../es/adr/README.md)

One file per decision that was expensive to make and would be expensive to
reverse. Each records the context at the time, the decision, and what it
costs — including the cases where the cost is real and we took it anyway.

An ADR is never edited once accepted. If a decision changes, a new ADR
supersedes it and says so.

| # | Decision | Status |
|---|----------|--------|
| [0001](0001-monolito-modular.md) | A modular monolith, not six services | Accepted |
| [0002](0002-multi-tenancy.md) | Shared-schema multi-tenancy from day one | Accepted |
| [0003](0003-formularios-dinamicos.md) | Quote forms are data, not code | Accepted |
| [0004](0004-motor-de-renovaciones.md) | Renewals as an idempotent, date-driven state machine | Accepted |
| [0005](0005-capa-de-inteligencia.md) | The intelligence layer is structural, not a phase-3 feature | Accepted |
| [0006](0006-lenguaje-del-dominio.md) | The domain is modelled in Spanish | Accepted |
| [0007](0007-stack-y-monorepo.md) | Python API + Next.js frontends in one repository | Accepted |
| [0008](0008-validacion-en-el-dominio.md) | Submission validation lives in the domain | Accepted |
| [0009](0009-documentacion-bilingue.md) | Documentation is bilingual | Accepted |
