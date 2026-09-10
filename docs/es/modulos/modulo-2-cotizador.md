# Módulo 2 — Cotizador inteligente

🇬🇧 [Read in English](../../modules/modulo-2-cotizador.md) · [← todos los módulos](README.md)

## Qué tenía que hacer

El §5 llama a este uno de los componentes más importantes del proyecto. En
lugar de un formulario genérico con demasiados campos, el sistema identifica
qué seguro quiere el visitante y pregunta solo lo que esa línea necesita.
Automóviles quiere placa, marca, línea, modelo y uso; cumplimiento quiere
valor y plazo del contrato.

El requisito de fondo está en la última línea del §5: esto existe para que la
información deje de llegar *"simplemente como un mensaje de WhatsApp que
posteriormente alguien debe transcribir."* La salida es un registro
estructurado con un código —`COT-000125`—, no un mensaje.

## Cómo se construyó

Son cuatro piezas, deliberadamente en capas para que la lógica interesante
nunca toque HTTP.

**1. El formulario es dato.** Ya venía de los cimientos: cada `ramo` es dueño
de un `formulario` JSONB validado por `FormularioRamo`
([ADR-0003](../adr/0003-formularios-dinamicos.md)).

**2. La validación vive en el dominio.** `domain/validacion.py` recibe un
`FormularioRamo` y un diccionario, y devuelve respuestas limpias: sin sesión,
sin objeto de petición, sin framework. Esa ubicación es el
[ADR-0008](../adr/0008-validacion-en-el-dominio.md), y la razón es el Módulo 3:
WhatsApp capturará los mismos campos desde una conversación, y con el tiempo un
asesor los digitará desde una llamada. Tres llamadores, una pregunta.

Tres propiedades que garantiza:

- **Todos los errores de una vez.** Un mapa `campo → mensaje`, no el primer
  fallo. Un formulario que revela un problema por envío es un formulario que la
  gente abandona, y un formulario abandonado es un lead que nunca llegó.
- **Normalización, no solo rechazo.** `abc-123` → `ABC123`, `Ana@Test.CO` →
  minúscula, `"2021"` → `2021`. Lo que aterriza en la base es consistente sin
  importar qué canal lo capturó; si no, el mismo vehículo se vuelve dos
  registros según quién lo haya escrito.
- **Campos condicionales exigidos en ambos sentidos.** Un campo cuya condición
  no se cumple no es simplemente opcional: *enviarlo* es un error. Si no,
  alguien podría mandar `valor_inmueble` declarando que no es propietario, y el
  registro guardado se contradiría.

**3. Un envío, una transacción.** `services/solicitudes.py` hace toda la
cadena: encuentra o crea el cliente, emite el código, crea la `Solicitud`, abre
una `Oportunidad` en `NUEVO`, agrega su primer `OportunidadEvento` y escribe un
`PuntajeLead` con su explicación. Todo dentro de la transacción de la petición:
un lead no puede quedar a medio crear.

La búsqueda de cliente va en orden descendente de confianza: número de
documento (casi único), luego teléfono (lo que la gente da de verdad, y un
repetido casi siempre es la misma persona), y por último correo (al final,
porque los correos familiares compartidos fusionarían personas distintas). Si
encuentra coincidencia, *rellena huecos* —un cliente que vuelve suele traer
datos que nunca tuvimos— pero nunca sobrescribe un valor que un asesor ya
corrigió.

**4. El navegador renderiza lo que le digan.** `FormularioCotizacion` elige un
control por tipo de campo, muestra y oculta los condicionales según cambian las
respuestas, y borra las que dejan de aplicar para que nunca se envíen.
Reimplementa la regla de visibilidad; esa copia es de presentación, y la del
servidor es la que obliga.

Los envíos van a un route handler del mismo origen en Next, no directo a la
API. Así el encabezado del tenant queda bajo control del servidor (un visitante
no puede enviar solicitudes a otra agencia editando una petición), la URL
interna no llega al bundle, se elimina el CORS de un endpoint público, y queda
un lugar evidente para agregar límite de tasa.

## Decisiones

| Decisión | Por qué | Costo |
|---|---|---|
| Validación en `domain/`, no en el endpoint | El Módulo 3 necesita las mismas reglas; una pregunta no debería tener tres respuestas | Ninguno todavía, pero es una capa que la gente espera encontrar junto a la ruta |
| Reportar todos los errores de una vez | El abandono es el verdadero modo de falla de un cotizador | Un poco más de código que fallar al primero |
| Códigos desde una fila bloqueada | Un `COT-000125` duplicado es una llamada a soporte; el bloqueo dura microsegundos | Los envíos concurrentes se serializan por agencia |
| Enviar a través de Next | Integridad del tenant, sin CORS, sin URL filtrada, y un lugar para el límite de tasa | Un salto adicional |
| Regla de visibilidad duplicada en TS | El formulario tiene que comportarse bien mientras se llena | Puede desincronizarse, pero de forma *segura*: el servidor rechaza lo que el navegador permitió de más |
| Deduplicación por documento → teléfono → correo | Ordenado por qué tan únicamente identifica cada dato a una persona | Dos personas que comparten teléfono pueden fusionarse; por eso el documento va primero |

## Los archivos

```
apps/api/src/corredor/
  domain/validacion.py          Validación pura, conversión, normalización, completitud
  services/consecutivos.py      COT-000125, emitido con SELECT ... FOR UPDATE
  services/solicitudes.py       Toda la cadena, en una transacción
  api/v1/solicitudes.py         POST /api/v1/solicitudes

apps/web/src/
  app/api/solicitudes/route.ts        Proxy del mismo origen
  components/formulario-cotizacion.tsx  Estado, condicionales, envío, confirmación
  components/campo-formulario.tsx       Un control por tipo de campo
  app/cotizar/[codigo]/page.tsx         Página por ramo, generada estáticamente
```

## Cómo verificarlo

```bash
uv run pytest apps/api/tests/unit/test_validacion.py   # 50 pruebas, sin base de datos
uv run pytest apps/api/tests/integration               # la cadena, contra Postgres
```

De punta a punta, por el proxy del propio sitio:

```bash
curl -s -X POST localhost:3000/api/solicitudes -H "Content-Type: application/json" -d '{
  "ramo":"automoviles",
  "respuestas":{"nombre":"Ana Restrepo","documento":"1098765432","telefono":"+57 3009998877",
    "correo":"ana@test.co","ciudad":"Medellín","placa":"xyz-987","marca":"Renault",
    "linea":"Duster","modelo":"2022","uso_vehiculo":"particular"}}'
```

Dos comportamientos que vale la pena revisar a mano, porque son los que prueban
el diseño y no la plomería:

- Envía el mismo documento dos veces. Un solo cliente, dos solicitudes, y la
  segunda puntúa **más alto**, porque `es_cliente_existente` ya es verdadero.
- Envía `valor_inmueble` en `hogar` con `es_propietario: false`. Se rechaza con
  *"no aplica según las respuestas anteriores"*, no se descarta en silencio.

## Qué se dejó fuera a propósito

- **Límite de tasa** en el endpoint público. El proxy es su lugar; necesita
  cableado con Redis que corresponde al trabajo del Módulo 2 al 3.
- **Avisar al equipo** de que llegó un lead — fase 2, y necesita las cuentas de
  asesores que introduce la autenticación.
- **Asignación de leads.** Las solicitudes nuevas llevan el asesor del cliente
  cuando ya lo tiene, y si no quedan sin asignar. Las reglas son de fase 2.
- **El formulario de la página de contacto.** El endpoint ya existe; conectarlo
  es pequeño y corresponde al trabajo del CRM.
