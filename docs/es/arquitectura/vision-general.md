# Visión general de la arquitectura

🇬🇧 [Read in English](../../architecture/overview.md)

## La forma del sistema

Una sola API es dueña del dominio. Todo lo demás —el sitio público, el CRM, el
canal de WhatsApp, el worker programado— es cliente suyo. Hay exactamente un
lugar donde una solicitud se convierte en oportunidad, y exactamente una
definición de qué significa "próxima a vencer".

```
apps/api/src/corredor/
├── api/           HTTP. Puede importar servicios; nada lo importa a él.
│   ├── deps.py    Resolución de sesión y de tenant
│   └── v1/        Rutas versionadas
├── core/          Configuración, logging, errores de dominio
├── db/            Base declarativa, mixins, ciclo de vida de la sesión
├── domain/        El modelo. No sabe nada de HTTP ni de tareas en segundo plano.
├── services/      Operaciones de negocio sobre una sesión
├── workers/       Trabajo programado y encolado, sobre los mismos servicios
└── scripts/       Semillas y utilidades operativas

packages/ml/src/corredor_ml/
├── base.py        El protocolo `Modelo` y el contrato `Prediccion`
├── lead_scoring.py
├── renovacion.py
└── cross_sell.py  Sin base de datos ni framework web: se importa desde un notebook
```

## El modelo de datos

Diecisiete tablas en cinco grupos.

**Tenancy.** `tenants` y `usuarios`. Todas las demás tablas llevan `tenant_id`.

**Catálogo.** `ramos` —cada uno dueño de la definición de su formulario— y
`aseguradoras`. Se configuran por agencia y se siembran con valores razonables.

**CRM.** `clientes` es el núcleo. Un cliente se crea en el momento en que
alguien pide una cotización, antes de cualquier venta, para que el pipeline y
la base de clientes sean el mismo conjunto de datos y no dos que se separan
con el tiempo.

**Comercial.** `solicitudes` → `oportunidades` → `cotizaciones`, con
`oportunidad_eventos` registrando cada cambio de etapa. Esa tabla de eventos es
lo que vuelve medible el embudo del §6 en lugar de anecdótico: las tasas de
conversión, el tiempo en cada etapa y el desempeño por asesor se derivan de
ella, así que el dashboard nunca tiene que reconstruir una historia que no
guardó.

**Pólizas y renovaciones.** `polizas`, encadenadas por `poliza_anterior_id`
para que la retención se mida en vez de suponerse, y `renovaciones` —una fila
por póliza y por umbral, con restricción de unicidad.

**Inteligencia.** `puntajes_lead`, `riesgos_renovacion`,
`recomendaciones_cross_sell`, `analisis_mensajes`. Todas versionadas, todas
explicadas, ninguna con autoridad sobre una decisión humana.

## Tres ideas que vale la pena entender

### Los formularios son datos

Un `ramo` lleva un `formulario` JSONB validado por `FormularioRamo`: campos
tipados y ordenados, con dependencias opcionales entre ellos. El sitio le
pregunta a la API qué necesita un ramo y renderiza la respuesta. Agregar una
línea de negocio, o una pregunta más, nunca exige un despliegue del frontend.

Las solicitudes guardan las respuestas junto con la `formulario_version` con la
que se capturaron, de modo que una solicitud de hace seis meses sigue siendo
interpretable después de que el formulario cambió.

### La planificación de renovaciones es una función pura

`planificar_acciones` recibe fechas y umbrales existentes, y devuelve las
acciones que faltan. Sin sesión, sin E/S. Los casos incómodos —un barrido
repetido, una caída de una semana, la cartera de una agencia importada tres
semanas antes de que venzan sus pólizas— son pruebas unitarias que corren en
milisegundos.

La restricción única sobre `(poliza_id, umbral_dias)` es la red de seguridad;
el planificador es la intención. Juntos permiten que el barrido corra tan
seguido como quiera sin duplicar jamás una tarea ni volver a contactar a un
cliente.

### Las predicciones son registros, no columnas

Un puntaje es una fila con procedencia, no un número que se sobrescribe. Eso
cuesta cuatro tablas y compra tres cosas: un conjunto de entrenamiento que ya
existe cuando por fin hay datos suficientes, una explicación con la que el
asesor puede estar en desacuerdo con fundamento, y la posibilidad de atribuir
una regresión a una versión del modelo en vez de discutirla.

## Ciclo de vida de una solicitud

1. Un visitante elige un ramo en el sitio público.
2. El sitio consulta `GET /api/v1/ramos/{codigo}` y renderiza su formulario.
3. El envío crea —en una sola transacción— un `cliente` (o encuentra el
   existente), una `solicitud` con un código por agencia como `COT-000125`, y
   una `oportunidad` en la etapa `NUEVO`.
4. Se escribe un `PuntajeLead` junto a la oportunidad, que ordena la cola del
   asesor.
5. Cada cambio de etapa agrega un `OportunidadEvento`.
6. Una oportunidad ganada produce una `poliza`, que el barrido nocturno toma
   para programarle renovaciones.

Los pasos 3 y 4 son una sola unidad de trabajo: un lead no puede quedar a
medio crear.

## Pruebas

- **Unitarias** — lógica pura, sin base de datos. El planificador de
  renovaciones, la validación de formularios y las líneas base de los modelos.
  Milisegundos.
- **De integración** — marcadas `integration`, requieren Postgres. Migraciones,
  consultas, aislamiento entre agencias.

CI además ejecuta `alembic check`, que falla cuando un modelo cambió sin su
migración. Ese tipo de error, si no, se descubre en un despliegue.
