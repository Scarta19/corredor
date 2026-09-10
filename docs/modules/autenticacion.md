# Autenticación

🇨🇴 [Leer en español](../es/modulos/autenticacion.md) · [← all modules](README.md)

## What it had to do

Not a numbered module, but everything from Módulo 4 onward depends on it: the
CRM shows an entire brokerage's client base, and §9 assumes an *asesor
responsable* — a named person — on every client. Nothing after this point can
be built without knowing who is asking.

## How it was built

**Argon2id via `pwdlib`,** with `verify_and_update`. When the recommended cost
parameters rise, a stored hash is upgraded transparently the next time its
owner signs in — so hardening later needs no migration and no forced reset.

**JWT access tokens carrying user, tenant and role.** The tenant in the token
is the point: [ADR-0002](../adr/0002-multi-tenancy.md) says a forgotten
`tenant_id` filter is a data leak, and the way that happens in practice is a
handler trusting a header. Authenticated traffic here takes the tenant from
the token and there is no code path that reads `X-Tenant` for it. A test
asserts that sending the header alongside a valid token changes nothing.

**The signed-in user is re-read from the database on every request.** The
token is treated as an assertion about identity, not as the user record. An
account deactivated a minute ago stops working now, rather than whenever its
token happens to expire.

**Login answers identically for "no such user" and "wrong password".**
Distinguishing them turns the login form into a way to enumerate who works at
the brokerage.

**In the browser, the token lives in an httpOnly cookie.** The CRM never holds
it in JavaScript. Credentials go to a Next route handler, which calls the API
server-side and sets the cookie; every subsequent API call is made from a
Server Component or a route handler. An XSS in the CRM cannot lift the token,
which matters more here than in most apps because the token opens the entire
client base.

## Decisions

| Decision | Why | Cost |
|---|---|---|
| Tenant from the token, never a header | The one mistake that turns multi-tenancy into a breach | Two resolution paths to keep straight — public and authenticated |
| Re-read the user per request | Deactivation takes effect immediately | One extra query per authenticated request |
| httpOnly cookie, not `localStorage` | An XSS must not be able to exfiltrate the whole book of business | Every API call is server-side; no direct browser→API calls |
| Identical message for both login failures | Otherwise the form enumerates staff | Slightly less helpful to a legitimate user who mistyped their email |
| Admins pass every role check implicitly | A one-person agency has an admin and no manager, and still needs the management views | Role checks are a floor, not an exact match |

## A bug this work surfaced

Writing the token tests produced a warning from PyJWT: *"The HMAC key is 12
bytes long, which is below the minimum recommended length of 32 bytes."*

Nothing prevented deploying with a signing key too weak for HS256 — and CI was
itself running with a 7-byte key. `Settings` now refuses to construct below 32
bytes (RFC 7518 §3.2) and refuses the development key outside `local`. It
fails at startup, which is the difference between a deploy that never goes
live and one that quietly issues forgeable sessions.

## The files

```
apps/api/src/corredor/
  core/seguridad.py     Hashing, token issue and validation. No FastAPI import.
  core/config.py        The signing-key floor
  api/deps.py           usuario_actual · tenant_del_usuario · requiere_rol
  api/v1/auth.py        POST /auth/login · GET /auth/yo

apps/admin/src/
  lib/sesion.ts               Cookie name, server-side API client, redirect on 401
  app/api/auth/login/route.ts  Credentials in, httpOnly cookie out
  app/(panel)/layout.tsx       The guard is the data fetch itself
```

## How to verify it

```bash
uv run pytest apps/api/tests/unit/test_seguridad.py           # tokens, hashing, key floor
uv run pytest apps/api/tests/integration/test_aislamiento_tenants.py
```

That second file is the one that matters: two agencies, populated, every CRM
surface checked from outside — including that an `X-Tenant` header cannot
redirect an authenticated request.

## What was deliberately left out

- **Refresh tokens.** A 12-hour access token and a re-login is honest for an
  internal tool; refresh rotation is complexity without a current problem.
- **Password reset by email.** Needs an email provider, which arrives with
  the phase-2 notification work.
- **Per-advisor row filtering.** Every signed-in user currently sees their
  whole agency. Restricting an advisor to their own clients is a policy call
  for the brokerage, not a default worth assuming.
