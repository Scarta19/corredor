# apps/admin — Módulo 4, el CRM

🇨🇴 [Leer en español](README.es.md)

The internal panel: the work queue, the commercial pipeline and the single
client view of §9.

```
/              Resumen — counters and the top of the queue
/solicitudes   The work queue, ordered by probability of closing
/pipeline      §10 board: nuevo → … → ganado / perdido
/clientes      Search by name, document, phone or email
/clientes/[id] Everything about one client, in one request
/login         Sign-in
```

## The token never reaches page JavaScript

Credentials go to a Next route handler, which calls the platform API
server-side and stores the access token in an **httpOnly** cookie. Every
subsequent API call is made from a Server Component or a route handler; the
browser never talks to the API directly.

This is a deliberate constraint rather than an accident of the framework. The
token opens an entire brokerage's client base, so an XSS on this page must not
be able to lift it. The cost is that mutations need a proxy route — see
`app/api/oportunidades/[id]/route.ts`.

The session guard is the data fetch itself: `(panel)/layout.tsx` calls
`usuarioActual()`, which redirects to `/login` on 401. There is no separate
check that could drift out of step with the request it protects.

## Development

```bash
make api                 # the platform API on :8000
npm install
npm run dev              # :3001
```

```bash
API_URL=http://localhost:8000     # server-side only; never NEXT_PUBLIC
```

Sign in with the seeded administrator: `admin@demo.test` / `corredor-demo`
(`make seed`).

```bash
npm run lint
npm run typecheck
npm run build
```

Next.js 16 (App Router) · React 19 · Tailwind v4 · TypeScript strict. Design
tokens are shared with `apps/web`.
