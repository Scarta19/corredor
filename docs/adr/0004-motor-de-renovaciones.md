# 0004 — Renewals as an idempotent, date-driven state machine

**Status:** Accepted · 2026-09-09

## Context

§11–12 describe escalating renewal touchpoints at 60, 30, 15 and 7 days before
expiry. This is the module the brief calls one of the platform's most
important assets, and it is the one where a bug is most visible to the
client: a duplicate task wastes an advisor's morning, a duplicate message
makes the brokerage look careless, and a missed one loses a renewal.

Three realities make the naive version wrong. Sweeps get retried. Sweeps get
missed — nobody runs a cron for a week without it failing once. And an
existing brokerage's book is imported mid-cycle, so most policies arrive with
several thresholds already in the past.

## Decision

A `renovaciones` row represents one policy at one threshold, with a unique
constraint on `(poliza_id, umbral_dias)`. Planning is a pure function,
`planificar_acciones`, over dates and already-existing thresholds:

1. A threshold with a row is never produced again.
2. A future threshold is scheduled on its own date.
3. Thresholds already past collapse into a **single** catch-up action at the
   most recent one, and only when the policy has no renewal history at all.

An expired policy produces no actions; the sweep moves its state instead.

## Consequences

**We get:** the sweep can run hourly, twice, or after a week's outage, and the
result is identical — the unique constraint is the backstop and the planner is
the intent. Importing a thousand-policy book produces one task per policy
instead of four.

**We pay:** the catch-up rule is a judgement call, not a law. A brokerage that
would rather see every missed threshold cannot have that today without a
configuration flag.

**We get, additionally:** because planning is pure, every case above is a unit
test that runs in milliseconds with no database — which is the actual reason
the awkward cases are handled at all.
