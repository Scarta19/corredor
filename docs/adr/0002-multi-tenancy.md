# 0002 — Shared-schema multi-tenancy from day one

**Status:** Accepted · 2026-09-09

## Context

§19 of the brief is the commercially interesting part: the first brokerage is
a validation case, and the real product is a platform for insurance
intermediaries generally. Retrofitting tenancy onto a single-tenant schema
means touching every table, every query and every index at exactly the moment
the first paying customer's data is in production.

## Decision

Every business table carries `tenant_id` from the first migration, via the
`TenantScoped` mixin. Composite indexes lead with it. Uniqueness is scoped to
it: two brokerages may both have a client with the same national ID, and
neither should ever see the other's.

The tenant is resolved once per request — from the authenticated token for
CRM traffic, from the `X-Tenant` header for anonymous public traffic — and
never taken from user-supplied input further down the stack.

## Consequences

**We get:** onboarding a brokerage is a row, not a deployment. Cross-tenant
analytics stay possible. One database to back up and migrate.

**We pay:** every query must filter by tenant, and a forgotten filter is a
data leak rather than a bug. That is the sharp edge of this decision and it
does not go away.

**We mitigate:** repository helpers take the tenant as a required argument, so
omitting it is a type error rather than a silent full-table read. Postgres
row-level security is the intended second layer — the schema is already
shaped for it — and becomes worth its operational cost at the point where
tenants are no longer all onboarded by us.
