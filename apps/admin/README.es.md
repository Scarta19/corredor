# apps/admin — Módulo 4, el CRM

🇬🇧 [Read in English](README.md)

El panel interno: la cola de trabajo, el pipeline comercial y la vista única
del cliente del §9.

```
/              Resumen — cifras y la cabeza de la cola
/solicitudes   La cola de trabajo, ordenada por probabilidad de cierre
/pipeline      Tablero del §10: nuevo → … → ganado / perdido
/clientes      Búsqueda por nombre, documento, teléfono o correo
/clientes/[id] Todo sobre un cliente, en una sola petición
/login         Ingreso
```

## El token nunca llega al JavaScript de la página

Las credenciales van a un route handler de Next, que llama a la API desde el
servidor y guarda el token de acceso en una cookie **httpOnly**. Toda llamada
posterior a la API se hace desde un Server Component o un route handler; el
navegador nunca habla directo con la API.

Es una restricción deliberada, no un accidente del framework. Ese token abre la
base de clientes completa de una agencia, así que un XSS en esta página no debe
poder llevárselo. El costo es que las mutaciones necesitan un proxy: ver
`app/api/oportunidades/[id]/route.ts`.

La guarda de sesión es la propia carga de datos: `(panel)/layout.tsx` llama a
`usuarioActual()`, que redirige a `/login` ante un 401. No hay un control
aparte que pueda desincronizarse de la petición que protege.

## Desarrollo

```bash
make api                 # la API de la plataforma en :8000
npm install
npm run dev              # :3001
```

```bash
API_URL=http://localhost:8000     # solo del lado del servidor; nunca NEXT_PUBLIC
```

Ingresa con la administradora sembrada: `admin@demo.test` / `corredor-demo`
(`make seed`).

```bash
npm run lint
npm run typecheck
npm run build
```

Next.js 16 (App Router) · React 19 · Tailwind v4 · TypeScript estricto. Los
tokens de diseño se comparten con `apps/web`.
