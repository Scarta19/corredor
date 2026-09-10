# Módulo 1 — Web profesional

🇬🇧 [Read in English](../../modules/modulo-1-web.md) · [← todos los módulos](README.md)

## Qué tenía que hacer

§4: convertir la página web en el principal canal digital de la agencia. El
requisito que le da forma a todo lo demás cabe en una frase: *"No debe ser una
página meramente informativa. Debe estar diseñada para generar acciones."*
Lista nueve secciones y cuatro llamados a la acción, y el §2 pone el
posicionamiento digital primero entre los objetivos.

Entonces: un sitio que se mide por cuántas solicitudes produce, no por cuánto
explica.

## Cómo se construyó

**Cada página termina en las mismas cuatro acciones.** `RejillaAcciones`
renderiza los CTA del §4 —solicitar cotización, hablar con un asesor, renovar
mi póliza, reportar una solicitud— y `Cierre` cierra cada ruta con dos de
ellos. El visitante nunca está a más de un clic de hacer algo, sin importar
dónde dejó de leer.

**El catálogo viene de la API, no del código.** `listarRamos()` consulta
`/api/v1/ramos`; la grilla renderiza lo que llegue. Una agencia que agrega
"Transporte" obtiene una tarjeta, una página en `/cotizar/transporte`, una
entrada en el sitemap y un formulario funcional, sin desplegar el frontend. Es
el [ADR-0003](../adr/0003-formularios-dinamicos.md) llegando al navegador.

**El sitio se degrada en vez de fallar.** `listarRamos` captura el error y
devuelve `[]`; la grilla entonces muestra `CatalogoNoDisponible`, que pone
WhatsApp y la página de contacto delante del visitante. El razonamiento: un
sitio de captación que responde 500 porque un servicio interno está enfermo
pierde el prospecto por completo, mientras que uno que pierde su grilla de
productos todavía lleva a la persona a hablar con alguien. Es verificable:
apaga la API y carga `/cotizar`.

**Aquí no se nombra ninguna agencia.** Marca, teléfono, número de WhatsApp,
ciudad e identificador del tenant son variables de entorno en
`src/lib/config.ts`; todos los textos viven en `src/content/site.ts`. El mismo
build atiende a otra agencia cambiando valores: es el
[ADR-0002](../adr/0002-multi-tenancy.md) aplicado al frontend.

**El SEO es estructural, no un plugin.** El sitemap se genera *desde el
catálogo*, así que la indexabilidad sigue a los datos. `robots.ts` bloquea a
los rastreadores salvo que `NEXT_PUBLIC_INDEXABLE=true`, de modo que un
despliegue de vista previa nunca compita con producción por su propio
posicionamiento. Los datos estructurados `InsuranceAgency` y `FAQPage` marcan
lo que la búsqueda local realmente premia.

## Decisiones

| Decisión | Por qué | Costo |
|---|---|---|
| Rutas separadas, no una sola página con anclas | Cada ramo y cada público necesita su URL indexable y sus metadatos | Más archivos; estado de navegación que mantener coherente |
| Sin librería de componentes ni de iconos | Nueve rutas necesitan unas seis primitivas; una librería es peso de bundle y un segundo vocabulario de diseño | Primitivas escritas a mano en `ui.tsx` |
| `<details>` para las preguntas frecuentes | Funciona antes de que cargue JavaScript, es accesible por teclado sin esfuerzo, y las respuestas quedan en el HTML para los rastreadores | Menos control sobre la animación |
| Radios para los booleanos, no casillas | Una casilla sin marcar es ambigua entre "no" y "sin responder", y los campos condicionales dependen de distinguirlos | Un poco más de marcado |
| La página de contacto tiene canales, no formulario | Un formulario sin backend es una mentira; el real llegó con el Módulo 2 | La página fue menos vistosa durante un commit |

## Los archivos

```
src/lib/config.ts        Configuración de la agencia; el único lugar donde aparece una marca
src/lib/api.ts           Cliente de la API. Devuelve [] ante un fallo en vez de lanzar.
src/content/site.ts      Todos los textos: navegación, las cuatro acciones, por qué, FAQ
src/components/ui.tsx    Contenedor · Seccion · TituloSeccion · Boton · Tarjeta
src/components/acciones.tsx        La rejilla de CTA del §4
src/components/ramos.tsx           Grilla del catálogo y su alternativa degradada
src/components/preguntas.tsx       FAQ sobre <details>
src/components/segmento.tsx        Forma compartida de /personas y /empresas
src/components/datos-estructurados.tsx  JSON-LD
src/app/sitemap.ts       Rutas fijas + una entrada por ramo, desde la API
src/app/robots.ts        Condicionado por entorno
```

## Cómo verificarlo

```bash
make api && make web
curl -s localhost:3000/sitemap.xml | grep -c "cotizar/"   # 8, uno por ramo
curl -s localhost:3000/robots.txt                          # Disallow salvo INDEXABLE
```

Apaga la API y recarga `/cotizar`: la página sigue renderizando y sigue
ofreciendo WhatsApp. Esa es la degradación funcionando.

## Qué se dejó fuera a propósito

- **El formulario de cotización** — Módulo 2. Este módulo termina en el
  selector de ramo.
- **Imágenes reales e imagen para compartir** — marcadores de posición hasta
  que la agencia entregue sus piezas de marca.
- **Un formulario de contacto** — necesita un endpoint de persistencia; llegó
  con el Módulo 2.
