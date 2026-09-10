# 0007 — API en Python y frontends Next.js en un solo repositorio

**Estado:** Aceptado · 2026-09-09 · 🇬🇧 [English](../../adr/0007-stack-y-monorepo.md)

## Contexto

La plataforma necesita un sitio público que posicione y convierta, un CRM
interno, un worker programado y un lugar donde vivan los modelos. Esas piezas
tienen requisitos genuinamente distintos: el sitio público quiere renderizado
en servidor y buenas métricas de carga; el CRM quiere interactividad rica
detrás de un login; los modelos quieren el ecosistema de datos de Python.

## Decisión

Un repositorio, cuatro piezas desplegables:

```
apps/api     FastAPI · SQLAlchemy 2 · Alembic · Postgres   la lógica central
apps/web     Next.js App Router                             sitio público (Módulos 1–2)
apps/admin   Next.js App Router                             CRM + dashboard (Módulos 4, 6)
packages/ml  scikit-learn · SDK de Anthropic                los modelos
```

Python es dueño del dominio, la persistencia y la inteligencia. TypeScript es
dueño del renderizado. La frontera entre ambos es el esquema OpenAPI que la API
ya genera, así que los tipos del frontend se derivan en lugar de mantenerse a
mano.

## Consecuencias

**Ganamos:** un cambio de esquema y sus consecuencias en el frontend caen en un
solo commit y una sola corrida de CI. El sitio público y el CRM comparten
componentes y tokens de diseño. La librería de modelos es importable desde la
API, desde un worker y desde un notebook.

**Pagamos:** dos cadenas de herramientas —`uv` y `npm`— en un mismo
repositorio, y CI tiene que correr ambas. Quien contribuya necesita las dos
instaladas; para eso existe `make install`.

**Descartamos:** una sola aplicación Next.js full-stack, que pondría la lógica
de dominio en TypeScript y dejaría los modelos varados en un servicio aparte
—al revés de lo que conviene a una plataforma cuyo estado final declarado es
la inteligencia comercial.
