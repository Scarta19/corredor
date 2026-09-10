# Módulo 2 — Cotizador inteligente

🇨🇴 [Leer en español](../es/modulos/modulo-2-cotizador.md) · [← all modules](README.md)

## What it had to do

§5 calls this one of the most important components of the project. Instead of
a generic form with too many fields, the system identifies which insurance the
visitor wants and asks only what that line needs. Automóviles wants placa,
marca, línea, modelo and uso; cumplimiento wants contract value and term.

The requirement underneath is in the last line of §5: this exists so that
information stops arriving *"simplemente como un mensaje de WhatsApp que
posteriormente alguien debe transcribir."* The output is a structured record
with a code — `COT-000125` — not a message.

## How it was built

The module is four pieces, deliberately layered so that the interesting logic
never touches HTTP.

**1. The form is data.** Already true from the foundation: each `ramo` owns a
JSONB `formulario` validated by `FormularioRamo`
([ADR-0003](../adr/0003-formularios-dinamicos.md)).

**2. Validation lives in the domain.** `domain/validacion.py` takes a
`FormularioRamo` and a dict and returns cleaned answers — no session, no
request object, no framework. This placement is
[ADR-0008](../adr/0008-validacion-en-el-dominio.md), and the reason is Módulo
3: WhatsApp will capture the same fields from a conversation, and an advisor
will eventually key them in from a phone call. Three callers, one question.

Three properties it guarantees:

- **Every error at once.** A `campo → mensaje` map, not the first failure. A
  form that reveals one problem per submission is a form people abandon, and
  an abandoned form is a lead that never arrived.
- **Normalisation, not just rejection.** `abc-123` → `ABC123`, `Ana@Test.CO` →
  lowercase, `"2021"` → `2021`. What lands in the database is consistent
  regardless of which channel captured it; otherwise the same vehicle becomes
  two records depending on who typed it.
- **Conditional fields enforced both ways.** A field whose condition is unmet
  is not merely optional — *sending* it is an error. Otherwise someone could
  submit `valor_inmueble` while declaring they are not the owner, and the
  stored record would contradict itself.

**3. One submission, one transaction.** `services/solicitudes.py` does the
whole chain: match or create the client, issue the code, create the
`Solicitud`, open an `Oportunidad` at `NUEVO`, append its first
`OportunidadEvento`, and write a `PuntajeLead` with its explanation. All of it
in the request's transaction — a lead cannot exist half-created.

Client matching runs in descending order of confidence: document number
(near-unique), then phone (what people actually give, and a repeat is almost
always the same person), then email (last, because shared family addresses
would merge distinct people). On a match it *fills gaps* — a returning client
often arrives with details we never had — but never overwrites a value an
advisor already curated.

**4. The browser renders whatever it is told.** `FormularioCotizacion` picks a
control per field type, shows and hides conditional fields as answers change,
and clears answers that stop applying so they are never submitted. It
re-implements the visibility rule; that copy is presentational, and the
server's is binding.

Submissions go to a same-origin Next route handler rather than to the API
directly. That keeps the tenant header server-controlled (a visitor cannot
submit into another brokerage by editing a request), keeps the internal API
URL out of the client bundle, removes CORS from a public endpoint, and leaves
an obvious place to add rate limiting.

## Decisions

| Decision | Why | Cost |
|---|---|---|
| Validation in `domain/`, not at the endpoint | Módulo 3 needs the same rules; one question should not have three answers | None yet — but it is a layer people expect to find near the route |
| Report every error at once | Abandonment is the real failure mode of a quote form | Slightly more code than fail-fast |
| Codes from a locked counter row | A duplicate `COT-000125` is a support call; the lock is held for microseconds | Concurrent submissions serialise per tenant |
| Proxy submissions through Next | Tenant integrity, no CORS, no leaked URL, a place for rate limiting | One extra hop |
| Visibility rule duplicated in TS | The form has to behave sensibly while being filled | Drift is possible — but *safe*: the server rejects anything the browser wrongly allowed |
| Client dedup on document → phone → email | Ordered by how uniquely each identifies a person | Two people sharing a phone can merge; document is checked first for that reason |

## The files

```
apps/api/src/corredor/
  domain/validacion.py          Pure validation, coercion, normalisation, completeness
  services/consecutivos.py      COT-000125, issued under SELECT ... FOR UPDATE
  services/solicitudes.py       The whole chain, in one transaction
  api/v1/solicitudes.py         POST /api/v1/solicitudes

apps/web/src/
  app/api/solicitudes/route.ts        Same-origin proxy
  components/formulario-cotizacion.tsx  State, conditionals, submit, confirmation
  components/campo-formulario.tsx       One control per field type
  app/cotizar/[codigo]/page.tsx         Page per ramo, statically generated
```

## How to verify it

```bash
uv run pytest apps/api/tests/unit/test_validacion.py   # 50 tests, no database
uv run pytest apps/api/tests/integration               # the chain, against Postgres
```

End to end, through the site's own proxy:

```bash
curl -s -X POST localhost:3000/api/solicitudes -H "Content-Type: application/json" -d '{
  "ramo":"automoviles",
  "respuestas":{"nombre":"Ana Restrepo","documento":"1098765432","telefono":"+57 3009998877",
    "correo":"ana@test.co","ciudad":"Medellín","placa":"xyz-987","marca":"Renault",
    "linea":"Duster","modelo":"2022","uso_vehiculo":"particular"}}'
```

Two behaviours worth checking by hand, because they are the ones that prove
the design rather than the plumbing:

- Submit the same document twice. One client row, two requests — and the
  second scores **higher**, because `es_cliente_existente` is now true.
- Submit `valor_inmueble` on `hogar` with `es_propietario: false`. Rejected as
  *"no aplica según las respuestas anteriores"*, not silently dropped.

## What was deliberately left out

- **Rate limiting** on the public endpoint. The proxy is where it goes; it
  needs Redis wiring that belongs with the Módulo 2 → 3 work.
- **Notifying the team** that a lead arrived — phase 2, and it needs the
  advisor accounts that authentication introduces.
- **Lead assignment.** New requests carry the client's existing advisor when
  there is one, and are otherwise unassigned. Assignment rules are phase 2.
- **A contact-page form.** The endpoint now exists; wiring the page to it is
  small and belongs with the CRM work.
