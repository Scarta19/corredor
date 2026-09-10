# apps/web — Módulo 1, web profesional

🇨🇴 [Leer en español](README.es.md)

The public site: the platform's front door and its main capture channel.

Per §4 of the platform brief this is **not** a brochure. Every page ends with
the same four actions, and the site's job is to produce them:

| Action | Route |
|---|---|
| Solicitar cotización | `/cotizar` → `/cotizar/[codigo]` |
| Hablar con un asesor | `/contacto` |
| Renovar mi póliza | `/renovar` |
| Reportar una solicitud | `/reportar` |

## Routes

```
/            Inicio — hero, acciones, catálogo, cómo funciona, por qué, FAQ
/nosotros    Quiénes somos y cómo trabajamos
/personas    Seguros para personas y familias
/empresas    Seguros para empresas
/seguros     Catálogo completo, agrupado por audiencia
/cotizar     Selector de ramo
/cotizar/[codigo]  Formulario dinámico de ese ramo
/contacto    WhatsApp, teléfono, correo
/renovar     Proceso de renovación
/reportar    Siniestros, cambios, certificados
```

## Three things worth knowing

**The catalogue is not hard-coded.** Lines of business and their form fields
come from `GET /api/v1/ramos`. A brokerage that adds a ramo sees it on the
site — with its own page at `/cotizar/[codigo]` and a working form — with no
frontend release. See [ADR-0003](../../docs/adr/0003-formularios-dinamicos.md).

**Submissions go through the site's own route handler.** The browser posts to
same-origin `/api/solicitudes` and Next forwards it to the API with the tenant
header attached. A visitor cannot submit into another brokerage by editing a
request, the internal API URL never reaches the client bundle, and a public
endpoint needs no CORS.

**The site survives the API being down.** `listarRamos` returns an empty list
rather than throwing, and the catalogue renders a fallback that puts WhatsApp
and the contact page in front of the visitor. A marketing site that 500s
because an internal service is unhealthy loses the lead entirely; one that
loses its product grid still gets the visitor to a human.

## Nothing here names a brokerage

Brand, contact details and tenant slug are environment variables
(`src/lib/config.ts`), so the same build serves a second agency by changing
three values. Copy lives in `src/content/site.ts`.

```bash
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_TENANT=demo
NEXT_PUBLIC_BRAND="Agencia Demo de Seguros"
NEXT_PUBLIC_WHATSAPP=573000000000
NEXT_PUBLIC_INDEXABLE=false   # robots.txt blocks crawlers unless "true"
```

## Development

```bash
npm install
npm run dev        # http://localhost:3000
npm run lint
npm run typecheck
npm run build
```

Next.js 16 (App Router) · React 19 · Tailwind v4 · TypeScript strict.
No icon or component library: the primitives are in `src/components/ui.tsx`
and the icons are inline SVG.
