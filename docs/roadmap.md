# Roadmap

🇨🇴 [Leer en español](es/hoja-de-ruta.md)

Three delivery phases. The order is the brief's; the reasoning for building
some foundations ahead of their phase is in the ADRs they link to.

## Phase 1 — MVP

*Goal: the brokerage has an organised digital channel for capturing and
managing clients.*

- [x] Domain model: tenancy, catalogue, CRM, pipeline, policies, renewals
- [x] Dynamic quote-form schema and validation ([ADR-0003](adr/0003-formularios-dinamicos.md))
- [x] Public catalogue API (`/ramos`, `/ramos/{codigo}`)
- [x] Demo tenant seed with a synthetic book of business
- [x] **Módulo 1 — Web profesional** — 9 routes, the four §4 actions, catalogue driven by the API, sitemap/robots/JSON-LD
- [x] **Módulo 2 — Cotizador inteligente** — dynamic form rendering, domain-level validation, `POST /solicitudes`, código `COT-000125`, client dedup, opportunity + audit event + lead score in one transaction
- [ ] Authentication and advisor accounts ← next
- [ ] Módulo 4 — CRM: client record, request queue, pipeline board

## Phase 2 — Automation

*Goal: the system starts doing work that people do by hand today.*

- [x] Renewal planning engine ([ADR-0004](adr/0004-motor-de-renovaciones.md))
- [ ] Scheduled renewal sweep (Arq worker, daily)
- [ ] Notifications: new lead to the team, renewal actions to the advisor
- [ ] Lead assignment rules
- [ ] Módulo 3 — WhatsApp Cloud API: inbound webhook, capture, handoff

## Phase 3 — Intelligence

*Goal: the platform stops being a system of record and becomes a commercial
instrument.*

- [x] Prediction schema with model, version, features and explanations ([ADR-0005](adr/0005-capa-de-inteligencia.md))
- [x] Baselines: lead scoring, renewal risk, cross-sell affinity
- [ ] Módulo 6 — dashboard: funnel, renewal buckets (§15), advisor performance
- [ ] Message understanding replacing the numbered WhatsApp menu
- [ ] Trained models, once there are enough closed opportunities to learn from
- [ ] Client segmentation and commercial automations

## Beyond

§19 of the brief: the platform generalises to insurance intermediaries at
large. The multi-tenant schema ([ADR-0002](adr/0002-multi-tenancy.md)) is the
part of that which had to be decided early; everything else — configurable
modules, siniestros, document management — is additive.
