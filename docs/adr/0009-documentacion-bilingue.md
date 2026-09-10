# 0009 — Documentation is bilingual

**Status:** Accepted · 2026-09-10
**Amends:** [0006 — The domain is modelled in Spanish](0006-lenguaje-del-dominio.md)

## Context

ADR-0006 settled the code: domain vocabulary in Spanish, technical scaffolding
and documentation in English. The reasoning for keeping documentation in
English was that it stays readable to a contributor who does not speak
Spanish.

That reasoning was incomplete. It weighed one audience and ignored the other.
The people who decide whether this platform is worth adopting — the brokerage
owner, the manager reading the renewal dashboard, the advisor being onboarded —
work in Spanish. Handing them an English architecture document is handing them
nothing.

Both audiences are real, and neither is a subset of the other.

## Decision

Prose documentation exists in both languages, in parallel trees:

```
README.md            docs/roadmap.md   docs/architecture/   docs/adr/       ← English
README.es.md         docs/es/hoja-de-ruta.md  docs/es/arquitectura/  docs/es/adr/   ← Spanish
```

Every document carries a switcher to its counterpart. Neither tree is a
machine translation of the other: they are written to read naturally, and a
change to one is not complete until the other matches.

Code, docstrings and inline comments stay in English, exactly as ADR-0006
decided — that part of it stands. The split is: **the code speaks to
developers, the documentation speaks to everyone.**

## Consequences

**We get:** a repository a Colombian brokerage can evaluate on its own terms,
and one an international engineer can still read.

**We pay:** every documentation change is two changes, and the copies will
drift when someone is in a hurry. There is no tooling to catch that — the
honest mitigation is that documentation drift is visible to readers, unlike
code drift, and either version being out of date is still better than one of
them not existing.

**We accept:** if the burden ever exceeds the value, the right move is to drop
the English tree and keep Spanish, not the reverse. The users come first.
