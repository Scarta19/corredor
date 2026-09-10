# How each module was built

🇨🇴 [Leer en español](../es/modulos/README.md)

One document per module. Each answers the same questions, in the same order:

1. **What it had to do** — the brief's requirement, in one paragraph
2. **How it was built** — the shape of the solution and why that shape
3. **Decisions** — what was chosen, what was rejected, what it costs
4. **The files** — where to look, and what each part owns
5. **How to verify it** — commands that prove it works
6. **What was deliberately left out** — and which module picks it up

These are build logs, not API reference. They explain *why the code looks the
way it does*, which is the thing that goes missing first and is hardest to
reconstruct later.

| # | Module | State | Document |
|---|--------|-------|----------|
| 1 | Web profesional | Done | [modulo-1-web.md](modulo-1-web.md) |
| 2 | Cotizador inteligente | Done | [modulo-2-cotizador.md](modulo-2-cotizador.md) |
| — | Autenticación | Done | [autenticacion.md](autenticacion.md) |
| 4 | CRM | In progress | [modulo-4-crm.md](modulo-4-crm.md) |
| 5 | Renovaciones | Done | [modulo-5-renovaciones.md](modulo-5-renovaciones.md) |
| 6 | Dashboard | Planned | — |
| 3 | WhatsApp | Planned | — |

Deeper background lives in the [ADRs](../adr/README.md); this tree assumes
them rather than repeating them.
