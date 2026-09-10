# Módulo 6 — Dashboard gerencial

🇨🇴 [Leer en español](../es/modulos/modulo-6-dashboard.md) · [← all modules](README.md)

## What it had to do

§14 lists the indicators; §16 shows the headline numbers; §15 is the renewal
distribution. The stated goal is the one that matters: *"pasar de tomar
decisiones basadas en percepción a tomar decisiones basadas en datos."*

§6 sets the harder requirement underneath it — measuring how many people ask
for a quote, how many are **attended**, how many receive a proposal, how many
buy.

## How it was built

**The funnel is cumulative reach, not a snapshot.** This is the whole reason
`oportunidad_eventos` has existed since Módulo 2. An opportunity sitting in
`GANADO` today passed through `CONTACTADO` and `COTIZANDO` on the way; a funnel
built from *current* stages would count it once at the end and report that
nobody was ever contacted.

You can see it working in the demo data: one opportunity is currently
`PERDIDO`, yet it still counts at "Contactadas" and "En cotización", because
the event log remembers where it went.

The funnel is scoped by when the **opportunity** was created, not when the
transition happened. Otherwise a deal that closed this month but arrived last
month appears as a sale with no lead behind it, and conversion reads above 100%.

**Conversion is measured against resolved opportunities, not all leads.**
Counting still-open deals as failures understates a team that is simply
mid-cycle, and the number would drift downward every day without anyone doing
anything wrong.

**Loss reasons get their own panel.** This is what the mandatory motive in
Módulo 4 was collected for. A manager who sees conversion fall needs to know
whether the problem is price or service — those have opposite responses, and
without the motive the chart can only say "worse".

**Restricted to managers and administrators.** An advisor's job is the queue.
Administrators pass the check implicitly, because an agency with one
administrator and no manager still needs the management views.

### The charts

Both charts follow one method, applied in order: pick the form, then assign
colour by the job it does, then **validate the palette with a script rather
than by eye**.

- **Form.** Every measure here is magnitude across a handful of ordered
  categories, so both are horizontal bars. The conversion rate is a single
  number, so it is a hero figure, not a chart. Nothing is a pie.
- **Colour.** Funnel stages and renewal windows are both *ordinal*, so each
  gets a one-hue ramp — blue for the funnel, orange for renewals, so two
  sequential scales on one page can never be confused for each other.
- **Validation.** Both ramps were run through the palette validator for both
  light and dark surfaces: monotone lightness, visible step gaps, single hue,
  and a light end that still clears 2:1 against the surface. The first orange
  candidate **failed** (its lightest step measured 1.73:1) and was re-stepped
  until it passed. That is the point of running the check instead of trusting
  the eye.
- **Marks.** Bars are 20px (the spec caps them at 24), with a 4px rounded
  data-end and a square baseline. No gridlines, no borders around marks, no
  dashed rules.
- **Text never wears the data colour.** Labels and values use text tokens; the
  coloured bar beside them carries the identity.
- **Nothing is gated behind hover.** Every value is visible as text, and each
  chart carries a "Ver los datos" table that includes the tooltip's detail.

## Decisions

| Decision | Why | Cost |
|---|---|---|
| Funnel from events, not current stage | §6 asks how many were *attended*, which a snapshot cannot answer | Depends on the event log being complete — which is why stage changes go through a service |
| Scope the funnel by opportunity creation | Otherwise conversion can exceed 100% | A deal that closes in a later month is credited to the month it arrived |
| Conversion over resolved, not all leads | Open deals are not failures | The rate moves in steps as deals resolve, rather than smoothly |
| Two ramps, blue and orange | Two ordinal scales on one page must not be confusable | An orange ramp had to be derived and validated; the first attempt failed |
| Hero figure for conversion, tiles for counts | A single number is not a chart | Only one hero is allowed per view — conversion earned it |
| Manager/admin only | An advisor's job is the queue, not the scoreboard | An advisor cannot self-serve their own numbers yet |

## The files

```
apps/api/src/corredor/
  services/metricas.py     embudo · comerciales · clientes · polizas · motivos_de_perdida
  api/v1/dashboard.py      GET /crm/dashboard, manager-only

apps/admin/src/
  components/graficos.tsx  Validated ramps, bar chart, hero and stat figures
  app/(panel)/dashboard/   The §14/§15/§16 view
```

## How to verify it

```bash
make api && cd apps/admin && npm run dev    # sign in as admin@demo.test
```

The funnel is the thing worth checking by hand. Move an opportunity through
several stages in `/pipeline`, then reload `/dashboard`: every stage it passed
through keeps its count, even after the deal is won or lost. A snapshot-based
funnel would lose that history.

```bash
uv run pytest apps/api/tests/integration/test_aislamiento_tenants.py
```

Includes the role checks: an advisor gets 403 on the dashboard and 200 on the
queue, and an administrator passes the management gate without being a manager.

## What was deliberately left out

- **Time series.** Trends need months of history; the platform has days. A
  sparkline over one month of data would be decoration pretending to be
  evidence.
- **Comparison against the previous period.** Same reason — there is no
  previous period yet. The stat tile contract has a `delta` slot waiting.
- **Per-advisor performance.** The data supports it (`oportunidad_eventos`
  records who moved what), but ranking colleagues is a management decision
  a brokerage should opt into, not a default this platform assumes.
- **Export to spreadsheet.** The obvious next request, and small — it belongs
  with whatever reporting cadence the brokerage settles on.
