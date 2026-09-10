# 0005 — The intelligence layer is structural, not a phase-3 feature

**Status:** Accepted · 2026-09-09

## Context

§18 of the brief places "IA para atención y clasificación" in phase 3, after
the CRM and the automations are working. As a *delivery* sequence that is
correct: a brokerage with no organised data has nothing to be intelligent
about, and shipping a model before the CRM would be building on sand.

As a *schema* decision it is a trap. Predictions that arrive later, into
tables that were not designed to hold them, end up as a column bolted onto
`oportunidades` — unversioned, unexplained, overwritten on every run, and
impossible to audit the first time someone asks why a lead was deprioritised.

## Decision

The delivery order stays as the brief has it. The schema does not wait.

`puntajes_lead`, `riesgos_renovacion`, `recomendaciones_cross_sell` and
`analisis_mensajes` exist from the first migration, and every one of them
carries the model name, the model version, the input features and a
human-readable explanation. Three rules hold:

1. A prediction records the model and version that produced it.
2. A prediction records its inputs, so it can be replayed and so training
   sets can be rebuilt from production truth.
3. A prediction never overwrites the business record it describes. Scores sit
   beside the CRM; a human decision always wins.

`packages/ml` ships interpretable baselines behind a `Modelo` protocol —
a logistic-style scorer for leads and churn, an affinity table for cross-sell.
They are honest about being baselines and they run without a database.

## Consequences

**We get:** the day there are enough closed opportunities to train on, the
training set already exists, because production has been logging features and
outcomes since the MVP. Swapping a baseline for a learned model is one class,
behind an unchanged interface.

**We pay:** four tables and a package that earn their keep slowly. The
baselines' weights are documented judgement, not fitted parameters, and saying
otherwise would be dishonest — their real job is to be a floor that a trained
model must beat.

**We accept:** §8's principle is binding on the WhatsApp module. Automation
handles reception, FAQs, capture and classification. Anything requiring
commercial or technical judgement goes to a person, and
`analisis_mensajes.requiere_humano` makes that boundary explicit and auditable
rather than implicit in a prompt.
