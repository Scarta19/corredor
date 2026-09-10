# apps/web — Módulo 1, web profesional

🇬🇧 [Read in English](README.md)

El sitio público: la puerta de entrada de la plataforma y su principal canal de
captación.

Según el §4 del documento del proyecto, esto **no** es un folleto. Cada página
termina con las mismas cuatro acciones, y el trabajo del sitio es producirlas:

| Acción | Ruta |
|---|---|
| Solicitar cotización | `/cotizar` → `/cotizar/[codigo]` |
| Hablar con un asesor | `/contacto` |
| Renovar mi póliza | `/renovar` |
| Reportar una solicitud | `/reportar` |

## Rutas

```
/            Inicio — hero, acciones, catálogo, cómo funciona, por qué, FAQ
/nosotros    Quiénes somos y cómo trabajamos
/personas    Seguros para personas y familias
/empresas    Seguros para empresas
/seguros     Catálogo completo, agrupado por público
/cotizar     Selector de ramo
/cotizar/[codigo]  Formulario dinámico de ese ramo
/contacto    WhatsApp, teléfono, correo
/renovar     Proceso de renovación
/reportar    Siniestros, cambios, certificados
```

## Tres cosas que vale la pena saber

**El catálogo no está escrito a mano.** Los ramos y los campos de sus
formularios vienen de `GET /api/v1/ramos`. Una agencia que agrega un ramo lo ve
en el sitio —con su propia página en `/cotizar/[codigo]` y su formulario
completo— sin ningún despliegue del frontend. Ver
[ADR-0003](../../docs/es/adr/0003-formularios-dinamicos.md).

**Los envíos pasan por un route handler del propio sitio.** El navegador
publica en `/api/solicitudes`, del mismo origen, y Next reenvía a la API con el
encabezado del tenant. Así el visitante no puede enviar solicitudes a otra
agencia editando una petición, la URL interna no llega al bundle, y no hace
falta CORS en un endpoint público.

**El sitio sobrevive a que la API se caiga.** `listarRamos` devuelve una lista
vacía en lugar de lanzar, y el catálogo muestra una alternativa que pone
WhatsApp y la página de contacto delante del visitante. Un sitio de captación
que responde 500 porque un servicio interno está enfermo pierde el prospecto
por completo; uno que pierde su grilla de productos todavía lleva a la persona
a hablar con alguien.

## Aquí no se nombra ninguna agencia

La marca, los datos de contacto y el identificador del tenant son variables de
entorno (`src/lib/config.ts`), de modo que el mismo build atiende a otra
agencia cambiando tres valores. Los textos viven en `src/content/site.ts`.

```bash
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_TENANT=demo
NEXT_PUBLIC_BRAND="Agencia Demo de Seguros"
NEXT_PUBLIC_WHATSAPP=573000000000
NEXT_PUBLIC_INDEXABLE=false   # robots.txt bloquea salvo que sea "true"
```

## Desarrollo

```bash
npm install
npm run dev        # http://localhost:3000
npm run lint
npm run typecheck
npm run build
```

Next.js 16 (App Router) · React 19 · Tailwind v4 · TypeScript estricto.
Sin librería de componentes ni de iconos: las primitivas están en
`src/components/ui.tsx` y los iconos son SVG en línea.
