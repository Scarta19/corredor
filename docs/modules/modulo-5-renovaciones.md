# Módulo 5 — Renovaciones

🇨🇴 [Leer en español](../es/modulos/modulo-5-renovaciones.md) · [← all modules](README.md)

## What it had to do

§11 calls this potentially the platform's most important asset, and it is
right: a book of business that is already sold renews every year, and the only
thing standing between the brokerage and that revenue is remembering to call.
§12 sets escalating touchpoints at 60, 30, 15 and 7 days. §15 asks for a
manager's view grouped into those windows.

The planning engine shipped with the foundation. This module is the two things
that make it real: something that runs it, and somewhere to see the result.

## How it was built

**The sweep is a scheduled job over the same service HTTP would call.** Arq,
one cron entry, once a day before the office opens. Renewal thresholds are
measured in days, so running more often produces the same result at more cost.

**Each tenant commits separately.** One agency's bad data must not stop the
others from getting their renewal tasks — renewals missed for one brokerage is
a support ticket, missed for all of them is lost revenue. A tenant that raises
is logged and skipped, and the run continues.

**Churn risk is scored during the same pass**, but only within 120 days of
expiry. Risk for a policy expiring in two years is arithmetic nobody will act
on, and scoring the whole book nightly is work for its own sake.

The features come entirely from records the brokerage already keeps: how many
times this policy has renewed (walking `poliza_anterior_id` backwards, bounded
so bad data cannot loop), how long the client has been with the agency, how
many other live policies they hold, how long since anyone communicated with
them, and how much the premium moved. **No feature requires anyone to start
entering something new** — a model that needs new manual work does not get used.

Claims are passed as zero and the code says why: there is no siniestros module
yet (§19 lists it as future). Fabricating the signal would be worse than
missing it.

**The board sorts twice, and that is the point.** Buckets are the calendar;
inside each bucket the riskiest policy comes first. A manager can see where the
deadline pressure is and, separately, where the business is actually likely to
be lost — which is exactly the difference between §15's view and a list sorted
by date.

**Expired policies stay on the board.** A lapsed policy is usually still
recoverable, and a dashboard that quietly drops them is how a book leaks.

## Decisions

| Decision | Why | Cost |
|---|---|---|
| One nightly run, not hourly | Thresholds are in days; more often is the same answer for more money | A policy crossing a threshold waits until morning — which is when anyone would call anyway |
| Per-tenant commit, failures skipped | One agency's bad data must not cost every other agency its renewals | A silently skipped tenant needs log monitoring to notice |
| Score only within 120 days | Risk nobody will act on is not worth computing nightly | Long-dated policies show "sin calcular" on the board |
| Scores accumulate, never overwrite | A prediction is a record (ADR-0005); history is how a regression gets attributed | The table grows; it will need retention eventually |
| Claims feature hard-coded to zero | The siniestros module does not exist; inventing the signal would be dishonest | The model runs with one fewer input than it could use |
| Expired policies remain visible | They are usually recoverable | The first bucket can look alarming on a neglected book |

## The files

```
apps/api/src/corredor/
  services/renovaciones.py     The planning rules (shipped with the foundation)
  services/riesgo.py           Feature assembly + scoring with provenance
  workers/tareas.py            barrido_diario: sweep + score, per tenant
  workers/main.py              Arq WorkerSettings and the cron entry
  scripts/barrido.py           Run it once, by hand
  api/v1/renovaciones.py       §15 buckets · per-policy actions · PATCH · resumen

apps/admin/src/app/(panel)/renovaciones/   The manager's board
```

## How to verify it

```bash
make barrido        # run the sweep once
make barrido        # run it again — "0 acciones" is the whole design
```

```bash
uv run pytest apps/api/tests/unit/test_renovaciones.py          # the planning rules
uv run pytest apps/api/tests/integration/test_barrido_renovaciones.py
```

The integration suite covers the cases that actually happen in production: a
repeated sweep, a week-long outage, an expired policy, and a renewal chain
counting as loyalty. One test asserts directly that no policy ever holds the
same threshold twice.

On the board itself, the catch-up rule is visible in the data: a policy
expiring in 3 days has **one** pending action, while one expiring in 34 days
has four. That is `planificar_acciones` collapsing already-passed thresholds
instead of flooding the queue.

## What was deliberately left out

- **Actually notifying anyone.** The sweep creates the tasks; sending the
  WhatsApp or the email is Módulo 3 plus the phase-2 notification work.
  `Renovacion.notificado_en` is the column waiting for it.
- **Recording the renewal itself.** Marking an action complete works; creating
  the successor policy and chaining `poliza_anterior_id` is the policy-writing
  work listed under Módulo 4.
- **Per-tenant threshold configuration.** §12 says the exact timings are the
  brokerage's call. The sweep already accepts them as a parameter and reads
  `renewal_thresholds_days` from settings; per-tenant overrides go in
  `Tenant.configuracion` when a second agency needs different ones.
- **A trained churn model.** The baseline is documented judgement, not fitted
  parameters. It becomes trainable once a full renewal cycle has been observed
  inside the platform.
