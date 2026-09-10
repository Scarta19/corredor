# Módulo 4 — CRM

🇬🇧 [Read in English](../../modules/modulo-4-crm.md) · [← todos los módulos](README.md)

## Qué tenía que hacer

El §9 llama al CRM el núcleo de la plataforma, y enuncia el requisito sin
rodeos: un asesor debería poder consultar todo sobre un cliente *"sin tener que
buscar en múltiples archivos, chats u hojas de cálculo."* El §10 agrega el
pipeline comercial: `NUEVO → CONTACTADO → COTIZANDO → PROPUESTA ENVIADA → EN
NEGOCIACIÓN → GANADO / PERDIDO`.

Los datos ya existían: el Módulo 2 viene escribiendo clientes, solicitudes,
oportunidades y puntajes desde el primer envío. Este módulo es la parte que una
persona puede usar de verdad.

## Cómo se construyó

**La cola se ordena por probabilidad de cierre, no por fecha.** Con 127 leads
en un mes y un equipo de tres, la pregunta nunca es a quién llamar sino a quién
*primero*. `/crm/solicitudes` ordena por puntaje.

Este es el único lugar de la plataforma donde un modelo decide algo, y lo que
decide es el orden de una lista, nunca el contenido de un registro. De tomarse
eso en serio salen dos detalles:

- Las solicitudes sin puntaje van **al final**, no al principio. La ausencia de
  puntaje no es evidencia de un buen lead, y ponerlas arriba enseñaría a los
  asesores a desconfiar del orden.
- El puntaje se muestra con su nivel en cada fila. Quien esté en desacuerdo
  puede ver el número con el que está en desacuerdo.

**La ficha del cliente es una petición, no seis.** `/crm/clientes/{id}`
devuelve al cliente con sus solicitudes, oportunidades, pólizas y
comunicaciones juntas. Es el §9 tomado literalmente: el valor está en no tener
que buscar en varios lados, y una página que dispara seis peticiones para armar
la misma vista solo trasladó la búsqueda al navegador.

**Los cambios de etapa pasan por un servicio, nunca por un `UPDATE` suelto.**
`services/oportunidades.cambiar_etapa` registra un `OportunidadEvento` en cada
transición, porque el embudo del Módulo 6 se deriva por completo de esa tabla.
Un cambio de etapa que se salte el registro es un hueco en el reporte del mes
siguiente.

Se aplican dos reglas, y deliberadamente ninguna más:

- **Perder exige un motivo.** "Perdido" sin motivo es el hueco más caro que
  puede tener una agencia en sus datos: sin él no hay forma de separar un
  problema de precio de uno de servicio, que es justo la pregunta para la que
  existe el pipeline. El tablero pide el motivo antes de enviar el cambio, así
  que el asesor nunca se topa con el error.
- **Retroceder está permitido.** Los negocios sí retroceden: un cliente deja de
  responder después de una propuesta. Un sistema que lo prohíbe solo enseña a
  la gente a registrar algo falso.

**La asignación aterriza en un solo lugar.** Asignar un asesor a una
oportunidad también lo fija en la solicitud que la originó, y en el cliente
cuando no tenía uno, para que "quién responde por esta persona" tenga una
respuesta y no tres.

## Decisiones

| Decisión | Por qué | Costo |
|---|---|---|
| Cola ordenada por puntaje, sin puntaje al final | Ordenar es lo más valioso que un modelo puede hacer aquí, y un valor por defecto equivocado erosiona la confianza en él | El orden se resuelve en Python tras traer la página, no en SQL |
| Ficha del cliente en una sola respuesta | El §9 trata de no buscar; seis peticiones mueven la búsqueda al navegador | Una respuesta más grande; comunicaciones limitadas a 50 |
| Select para mover tarjetas, no arrastrar | Los asesores usan esto en el celular entre llamadas. Un select es alcanzable, accesible por teclado y no se puede soltar en la columna equivocada | Menos vistoso en una demostración |
| Pedir el motivo de pérdida en la interfaz | La API lo rechaza sin él; mejor preguntar que mostrar un error | Un estado más en el tablero |
| Permitir transiciones hacia atrás | Prohibir la realidad produce registros falsos | El embudo debe tolerar caminos no monótonos |
| 404, no 403, para registros de otra agencia | Confirmar que un id existe ya filtra que otra agencia lo tiene | Un poco menos útil ante un error genuino |

## Los archivos

```
apps/api/src/corredor/
  api/v1/crm.py                 resumen · solicitudes · clientes · pipeline · PATCH · historial
  services/oportunidades.py     cambiar_etapa · asignar_asesor, ambos registrando eventos

apps/admin/src/
  lib/sesion.ts                 Cliente de la API del lado del servidor
  app/(panel)/page.tsx          Cifras y la cabeza de la cola
  app/(panel)/solicitudes/      La cola de trabajo, con filtros
  app/(panel)/pipeline/         El tablero del §10
  app/(panel)/clientes/[id]/    La vista única del §9
  components/tablero.tsx        Movimiento de tarjetas y motivo de pérdida
  app/api/oportunidades/[id]/   Proxy de mutación, porque el token es httpOnly
```

## Cómo verificarlo

```bash
make api                       # :8000
cd apps/admin && npm run dev   # :3001 — ingresa con admin@demo.test / corredor-demo
```

Vale la pena revisar a mano, porque prueban el diseño y no el cableado:

- La cola **no** está en orden de fecha. La solicitud con mayor puntaje va
  primero.
- Mueve una tarjeta a *Perdido*. Pide un motivo antes de guardar.
- Abre un cliente y lee el historial: el evento automático de `NUEVO` del
  Módulo 2 está por encima de cada transición humana posterior.

```bash
uv run pytest apps/api/tests/integration/test_aislamiento_tenants.py
```

## Qué se dejó fuera a propósito

- **Editar clientes y registrar notas.** Primero leer: un asesor necesita *ver*
  el panorama antes de necesitar cambiarlo.
- **Registrar pólizas y cotizaciones a mano.** Las tablas existen; los
  formularios corresponden al trabajo de renovaciones del Módulo 5, donde las
  pólizas son el tema.
- **Reglas de asignación.** La asignación funciona de a una oportunidad. El
  reparto automático por turnos o por ramo es de fase 2.
- **Visibilidad por asesor.** Todos ven la agencia completa; acotarlo es una
  decisión de política de la agencia, no un valor por defecto que suponer.
