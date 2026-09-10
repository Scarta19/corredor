# Módulo 3 — WhatsApp automatizado

🇨🇴 [Leer en español](../es/modulos/modulo-3-whatsapp.md) · [← all modules](README.md)

## What it had to do

§7 is explicit that WhatsApp must be *"un canal conectado al sistema, no una
herramienta aislada"*, and sketches a numbered menu. §8 sets the rule that
governs everything here:

> La automatización no debe intentar reemplazar al asesor. Debe encargarse
> principalmente de: recepción, preguntas frecuentes, captura de información,
> clasificación, creación de solicitudes, notificaciones y seguimientos
> básicos. El asesor debe intervenir cuando exista una situación que requiera
> criterio comercial o técnico.

## How it was built

**The menu is the fallback, not the interface.** §7's numbered options still
work — someone who types `3` gets renewals — but people do not write "1", they
write *"necesito asegurar mi carro"*. A bot that answers "opción no válida" to
that has already lost the lead. So the message is read for meaning first, and
the menu is what a greeting gets.

**Understanding is rule-based, and that is a choice, not a limitation.**
`corredor_ml.nlu` matches the vocabulary a broker's clients actually use —
accents stripped, "me chocaron" and "me robaron" and "se me vence" and
"cuánto cuesta" — runs in microseconds, needs no API key, and cannot be
unavailable. An LLM sits above it as an upgrade path, not as a dependency the
channel needs in order to work at all.

Priority order matters: a claim outranks everything else in the same message,
so *"quiero cotizar pero me chocaron"* is a claim, not a quote request.

**The model classifies; it never writes.** Every outbound message is a
template a person wrote. On this channel the brokerage is legally the one
speaking, and generated text can invent a coverage, quote a price or promise a
timeline. What the model decides is *which* template — and a test asserts that
no reply path can emit an unfilled placeholder.

**§8's boundary is a column, not a vibe.** `AnalisisMensaje.requiere_humano` is
set on claims, policy questions, explicit requests for a person, and anything
the classifier could not read. It is deliberately generous: handing a simple
question to an advisor costs a few seconds of their time, while a bot
mishandling a claim costs a client.

**Everything lands in the same tables the web form writes to.** A person who
writes on WhatsApp becomes a `Cliente` immediately — same rule as the web
form — with their messages, the platform's replies, and the classification
that produced them all on the client's timeline in the CRM.

**The webhook is defensive on both sides.** Meta's `X-Hub-Signature-256` is
verified in constant time before anything is written; without it this is an
open endpoint that creates clients for whoever finds the URL. And once the
signature checks out it always answers 200: Meta retries non-2xx responses and
eventually disables a webhook that keeps failing, so a bug handling one
message must not cost the brokerage the entire channel.

## Decisions

| Decision | Why | Cost |
|---|---|---|
| Rules first, LLM as an upgrade | The channel must work with no API key and no latency budget | Vocabulary is hand-maintained; it will miss phrasings until someone adds them |
| Templates for every reply | The brokerage is legally the speaker; generated text can invent coverage | Replies are less fluent than a model's would be |
| Claims outrank everything | "Cotizar pero me chocaron" is a claim | A message doing two things gets routed by the more serious one |
| Unreadable message → a person | Guessing at someone already talking to a business about money is worse than handing over | Advisors see some noise |
| Always 200 after a valid signature | Meta disables webhooks that keep failing | A failure is a log line, so log monitoring matters |
| Client created on first message | Same rule as the web form; one dataset, not two | Wrong numbers create thin client records |

## The files

```
packages/ml/src/corredor_ml/nlu.py    Intent, ramo, entities, the §8 boundary
apps/api/src/corredor/
  services/whatsapp.py                Signature check · envelope parsing · conversation
  api/v1/whatsapp.py                  GET verify · POST receive
```

## How to verify it

```bash
uv run pytest apps/api/tests/unit/test_whatsapp.py          # 46, no database
uv run pytest apps/api/tests/integration/test_whatsapp_webhook.py
```

The integration suite covers what actually goes wrong in production: an
unsigned body, a body signed with the wrong secret (and that neither writes
anything), Meta's retry of the same message (one inbound row, one reply — the
client is never written to twice), two messages from one number creating one
client, and a delivery receipt answering 200 rather than looking like an error.

## What is needed to switch it on

The code is complete and tested; the channel needs credentials the brokerage
must supply from its own Meta Business account:

```bash
WHATSAPP_VERIFY_TOKEN=...      # also verifies the webhook signature
WHATSAPP_ACCESS_TOKEN=...
WHATSAPP_PHONE_NUMBER_ID=...
```

Then point Meta's webhook at `POST /api/v1/whatsapp/webhook`. Until those
exist, `enviar_mensaje` logs instead of sending and returns `False` — **the
conversation is still recorded either way**, so the CRM shows what would have
been said. The channel is optional; the record is not.

## What was deliberately left out

- **Creating a `Solicitud` straight from the chat.** The classifier already
  extracts placa, document and email; turning a conversation into a coded
  quote request needs multi-turn state to collect the rest of the ramo's
  fields, and that state machine is its own piece of work.
- **An LLM classifier.** The interface is ready and `ANTHROPIC_API_KEY` is
  already a setting. The baseline should be measured against real traffic
  first — otherwise there is nothing to know whether the model beat.
- **Templated outbound campaigns.** Renewal reminders over WhatsApp need
  Meta-approved message templates and an opt-in record; that belongs with the
  phase-2 notification work.
- **Media messages.** Photos of a crashed car and PDFs of a policy are the
  obvious next thing; they need file storage, which no module has needed yet.
