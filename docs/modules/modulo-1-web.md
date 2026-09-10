# Módulo 1 — Web profesional

🇨🇴 [Leer en español](../es/modulos/modulo-1-web.md) · [← all modules](README.md)

## What it had to do

§4 of the brief: turn the website into the brokerage's main digital channel.
The requirement that shapes everything else is one sentence — *"No debe ser
una página meramente informativa. Debe estar diseñada para generar acciones."*
It lists nine sections and four calls to action, and §2 puts digital
positioning first among the platform's objectives.

So: a site measured by how many requests it produces, not by how much it
explains.

## How it was built

**Every page ends in the same four actions.** `RejillaAcciones` renders the
§4 CTAs — solicitar cotización, hablar con un asesor, renovar mi póliza,
reportar una solicitud — and `Cierre` closes every route with two of them. A
visitor is never more than one click from doing something, wherever they
stopped reading.

**The catalogue comes from the API, not from the codebase.** `listarRamos()`
fetches `/api/v1/ramos`; the grid renders whatever comes back. A brokerage
that adds "Transporte" gets a card, a page at `/cotizar/transporte`, a sitemap
entry and a working form, with no frontend release. This is
[ADR-0003](../adr/0003-formularios-dinamicos.md) reaching the browser.

**The site degrades instead of failing.** `listarRamos` catches and returns
`[]`; the grid then renders `CatalogoNoDisponible`, which puts WhatsApp and
the contact page in front of the visitor. The reasoning: a marketing site that
returns 500 because an internal service is unhealthy loses the lead outright,
while one that loses its product grid still gets the person to a human. This
is verifiable — stop the API and load `/cotizar`.

**Nothing names a brokerage.** Brand, phone, WhatsApp number, city and tenant
slug are environment variables in `src/lib/config.ts`; all prose lives in
`src/content/site.ts`. The same build serves a second agency by changing
values, which is [ADR-0002](../adr/0002-multi-tenancy.md) applied to the
frontend.

**SEO is structural, not a plugin.** The sitemap is generated *from the
catalogue*, so indexability follows the data. `robots.ts` blocks crawlers
unless `NEXT_PUBLIC_INDEXABLE=true`, so a preview deployment can never compete
with production for its own rankings. `InsuranceAgency` and `FAQPage` JSON-LD
mark up what local search actually rewards.

## Decisions

| Decision | Why | Cost |
|---|---|---|
| Separate routes, not one long page with anchors | Each ramo and audience needs its own indexable URL and its own metadata | More files; navigation state to keep consistent |
| No component or icon library | Nine routes need about six primitives; a library is bundle weight and a second design vocabulary | Primitives written by hand in `ui.tsx` |
| `<details>` for the FAQ | Works before JavaScript, keyboard accessible for free, answers present in the HTML for crawlers | Less control over the open/close animation |
| Radios for booleans, not checkboxes | An unchecked box is ambiguous between "no" and "unanswered", and conditional fields depend on telling those apart | Slightly more markup |
| Contact page has channels, not a form | A form with no backend is a lie; the real one arrived with Módulo 2 | The page was less impressive for one commit |

## The files

```
src/lib/config.ts        Tenant-facing configuration; the only place a brand appears
src/lib/api.ts           API client. Returns [] on failure rather than throwing.
src/content/site.ts      All copy: nav, the four actions, why-us, FAQ, about
src/components/ui.tsx    Contenedor · Seccion · TituloSeccion · Boton · Tarjeta
src/components/acciones.tsx        The §4 CTA grid
src/components/ramos.tsx           Catalogue grid + the degraded fallback
src/components/preguntas.tsx       FAQ on <details>
src/components/segmento.tsx        Shared shape of /personas and /empresas
src/components/datos-estructurados.tsx  JSON-LD
src/app/sitemap.ts       Static routes + one entry per ramo from the API
src/app/robots.ts        Environment-gated
```

## How to verify it

```bash
make api && make web
curl -s localhost:3000/sitemap.xml | grep -c "cotizar/"   # 8, one per ramo
curl -s localhost:3000/robots.txt                          # Disallow unless INDEXABLE
```

Stop the API and reload `/cotizar`: the page still renders and still offers
WhatsApp. That is the degradation path working.

## What was deliberately left out

- **The quote form itself** — Módulo 2. This module ends at the ramo selector.
- **Real imagery and an OG image** — placeholders until the brokerage supplies
  brand assets.
- **A contact form** — needs a persistence endpoint; arrived with Módulo 2.
