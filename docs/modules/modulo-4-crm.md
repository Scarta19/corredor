# Módulo 4 — CRM

🇨🇴 [Leer en español](../es/modulos/modulo-4-crm.md) · [← all modules](README.md)

## What it had to do

§9 calls the CRM the nucleus of the platform, and states the requirement
plainly: an advisor should be able to look up everything about a client
*"sin tener que buscar en múltiples archivos, chats u hojas de cálculo."*
§10 adds the commercial pipeline — `NUEVO → CONTACTADO → COTIZANDO →
PROPUESTA ENVIADA → EN NEGOCIACIÓN → GANADO / PERDIDO`.

The data already existed: Módulo 2 has been writing clients, requests,
opportunities and scores since the first submission. This module is the part
a person can actually use.

## How it was built

**The queue is ordered by probability of closing, not by date.** With 127
leads in a month and a team of three, the question is never who to call but
who *first*. `/crm/solicitudes` sorts by lead score.

This is the only place in the platform where a model decides anything — and
what it decides is the order of a list, never the content of a record. Two
details follow from taking that seriously:

- Unscored requests sort **last**, not first. An absent score is not evidence
  of a good lead, and defaulting them to the top would quietly train advisors
  to distrust the ordering.
- The score is shown with its level beside every row. An advisor who disagrees
  can see the number they are disagreeing with.

**The client page is one request, not six.** `/crm/clientes/{id}` returns the
client with their requests, opportunities, policies and communications
together. That is §9 taken literally: the value is in not having to look in
several places, and a page that fires six requests to assemble the same view
has only moved the hunting into the browser.

**Stage changes go through a service, never a bare `UPDATE`.**
`services/oportunidades.cambiar_etapa` records an `OportunidadEvento` on every
transition, because the Módulo 6 funnel is derived entirely from that table. A
stage change that skips the event log is a hole in next month's reporting.

Two rules are enforced, and deliberately no others:

- **Losing requires a reason.** "Perdido" with no motive is the most expensive
  gap a brokerage can have in its data: without it there is no way to separate
  a pricing problem from a service problem, which is the question the pipeline
  exists to answer. The board asks for the motive before sending the change,
  so the advisor never meets the error.
- **Moving backwards is allowed.** Deals genuinely regress — a client goes
  quiet after a proposal. A system that forbids it just teaches people to
  record something false.

**Assignment lands in one place.** Assigning an advisor to an opportunity also
sets it on the originating request, and on the client when they had none — so
"who is responsible for this person" has one answer rather than three.

## Decisions

| Decision | Why | Cost |
|---|---|---|
| Queue sorted by score, unscored last | Ordering is the highest-value thing a model can do here, and a wrong default erodes trust in it | Sorting happens in Python after fetching a page, not in SQL |
| Client detail as one response | §9 is about not hunting; six requests moves the hunt to the browser | A larger response; communications capped at 50 |
| Select to move cards, not drag-and-drop | Advisors use this on a phone between calls. A select is reachable, keyboard-accessible, and cannot be dropped in the wrong column | Less impressive to demo |
| Ask for the loss motive in the UI | The API refuses without it; better to ask than to show an error | One more piece of board state |
| Backwards transitions allowed | Forbidding reality produces false records | The funnel must handle non-monotonic paths |
| 404, not 403, for another tenant's records | Confirming an id exists already leaks that another agency holds it | Slightly less helpful for genuine mistakes |

## The files

```
apps/api/src/corredor/
  api/v1/crm.py                 resumen · solicitudes · clientes · pipeline · PATCH · historial
  services/oportunidades.py     cambiar_etapa · asignar_asesor, both event-recording

apps/admin/src/
  lib/sesion.ts                 Server-side API client
  app/(panel)/page.tsx          Counters + the top of the queue
  app/(panel)/solicitudes/      The work queue, with filters
  app/(panel)/pipeline/         §10 board
  app/(panel)/clientes/[id]/    §9's single view
  components/tablero.tsx        Card movement, loss-motive prompt
  app/api/oportunidades/[id]/   Mutation proxy, because the token is httpOnly
```

## How to verify it

```bash
make api                       # :8000
cd apps/admin && npm run dev   # :3001 — sign in as admin@demo.test / corredor-demo
```

Worth checking by hand, because these prove the design rather than the wiring:

- The queue is **not** in date order. The highest-scoring request is first.
- Move a card to *Perdido*. It asks for a motive before it will save.
- Open a client and read the audit trail: the automatic `NUEVO` event from
  Módulo 2 sits above every human transition since.

```bash
uv run pytest apps/api/tests/integration/test_aislamiento_tenants.py
```

## What was deliberately left out

- **Editing clients and recording notes.** Read-heavy first: an advisor needs
  to *see* the picture before they need to change it.
- **Registering policies and quotations by hand.** The tables exist; the forms
  belong with the Módulo 5 renewals work, where policies are the subject.
- **Assignment rules.** Assignment works one opportunity at a time. Automatic
  round-robin or by-ramo routing is phase 2.
- **Per-advisor visibility.** Everyone sees the whole agency; narrowing it is
  a brokerage policy call, not a default to assume.
