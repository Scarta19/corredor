# Módulo 3 — WhatsApp automatizado

🇬🇧 [Read in English](../../modules/modulo-3-whatsapp.md) · [← todos los módulos](README.md)

## Qué tenía que hacer

El §7 es explícito en que WhatsApp debe ser *"un canal conectado al sistema, no
una herramienta aislada"*, y esboza un menú numerado. El §8 fija la regla que
gobierna todo lo de aquí:

> La automatización no debe intentar reemplazar al asesor. Debe encargarse
> principalmente de: recepción, preguntas frecuentes, captura de información,
> clasificación, creación de solicitudes, notificaciones y seguimientos
> básicos. El asesor debe intervenir cuando exista una situación que requiera
> criterio comercial o técnico.

## Cómo se construyó

**El menú es el respaldo, no la interfaz.** Las opciones numeradas del §7
siguen funcionando —quien escriba `3` llega a renovaciones—, pero la gente no
escribe "1", escribe *"necesito asegurar mi carro"*. Un bot que a eso responde
"opción no válida" ya perdió el prospecto. Así que el mensaje se lee primero
por significado, y el menú es lo que recibe un saludo.

**La comprensión es por reglas, y eso es una decisión, no una limitación.**
`corredor_ml.nlu` reconoce el vocabulario que los clientes de un intermediario
usan de verdad —sin tildes, "me chocaron", "me robaron", "se me vence",
"cuánto cuesta"—, corre en microsegundos, no necesita API key y no puede estar
caído. Un LLM se ubica encima como mejora, no como una dependencia sin la cual
el canal no funciona.

El orden de prioridad importa: un siniestro le gana a todo lo demás en el mismo
mensaje, así que *"quiero cotizar pero me chocaron"* es un siniestro, no una
cotización.

**El modelo clasifica; nunca escribe.** Todo mensaje que sale es una plantilla
escrita por una persona. En este canal la agencia es legalmente quien habla, y
un texto generado puede inventarse una cobertura, cotizar un precio o prometer
un plazo. Lo que el modelo decide es *cuál* plantilla — y una prueba verifica
que ninguna ruta de respuesta pueda emitir un marcador sin reemplazar.

**La frontera del §8 es una columna, no una intención.**
`AnalisisMensaje.requiere_humano` se marca en siniestros, consultas de póliza,
peticiones explícitas de hablar con alguien y todo lo que el clasificador no
pudo leer. Es deliberadamente generosa: pasarle una pregunta sencilla a un
asesor cuesta unos segundos de su tiempo, mientras que un bot manejando mal un
siniestro cuesta un cliente.

**Todo aterriza en las mismas tablas que escribe el formulario web.** Quien
escribe por WhatsApp se vuelve `Cliente` de inmediato —la misma regla del
formulario— con sus mensajes, las respuestas de la plataforma y la
clasificación que las produjo, todo en la línea de tiempo del cliente en el CRM.

**El webhook es defensivo por ambos lados.** La firma `X-Hub-Signature-256` de
Meta se verifica en tiempo constante antes de escribir nada; sin eso esto es un
endpoint abierto que crea clientes para quien encuentre la URL. Y una vez que
la firma pasa, siempre responde 200: Meta reintenta las respuestas que no son
2xx y termina deshabilitando un webhook que falla seguido, así que un error
procesando un mensaje no puede costarle a la agencia el canal completo.

## Decisiones

| Decisión | Por qué | Costo |
|---|---|---|
| Reglas primero, LLM como mejora | El canal debe funcionar sin API key y sin presupuesto de latencia | El vocabulario se mantiene a mano; se le van a escapar formas hasta que alguien las agregue |
| Plantillas para toda respuesta | La agencia es legalmente quien habla; un texto generado puede inventar coberturas | Las respuestas son menos fluidas que las de un modelo |
| El siniestro le gana a todo | "Cotizar pero me chocaron" es un siniestro | Un mensaje que hace dos cosas se enruta por la más seria |
| Mensaje ilegible → una persona | Adivinar con alguien que ya está hablando de dinero con un negocio es peor que derivar | Los asesores ven algo de ruido |
| Siempre 200 tras una firma válida | Meta deshabilita los webhooks que fallan seguido | Un fallo es una línea de log, así que el monitoreo importa |
| Cliente creado en el primer mensaje | La misma regla del formulario web; un solo conjunto de datos, no dos | Los números equivocados crean fichas de cliente delgadas |

## Los archivos

```
packages/ml/src/corredor_ml/nlu.py    Intención, ramo, entidades y la frontera del §8
apps/api/src/corredor/
  services/whatsapp.py                Verificación de firma · envoltura · conversación
  api/v1/whatsapp.py                  GET verificación · POST recepción
```

## Cómo verificarlo

```bash
uv run pytest apps/api/tests/unit/test_whatsapp.py          # 46, sin base de datos
uv run pytest apps/api/tests/integration/test_whatsapp_webhook.py
```

Las pruebas de integración cubren lo que de verdad sale mal en producción: un
cuerpo sin firma, uno firmado con otro secreto (y que ninguno escriba nada), el
reintento de Meta del mismo mensaje (una fila de entrada, una respuesta: al
cliente no se le vuelve a escribir), dos mensajes de un mismo número creando un
solo cliente, y un recibo de entrega respondiendo 200 en vez de parecer un error.

## Qué hace falta para encenderlo

El código está completo y probado; el canal necesita credenciales que la
agencia debe entregar desde su propia cuenta de Meta Business:

```bash
WHATSAPP_VERIFY_TOKEN=...      # también verifica la firma del webhook
WHATSAPP_ACCESS_TOKEN=...
WHATSAPP_PHONE_NUMBER_ID=...
```

Después se apunta el webhook de Meta a `POST /api/v1/whatsapp/webhook`. Hasta
que existan, `enviar_mensaje` registra en el log en vez de enviar y devuelve
`False` — **la conversación queda guardada igual**, así que el CRM muestra lo
que se habría dicho. El canal es opcional; el registro no.

## Qué se dejó fuera a propósito

- **Crear una `Solicitud` directamente desde el chat.** El clasificador ya
  extrae placa, documento y correo; convertir una conversación en una solicitud
  con código exige estado multi-turno para recoger el resto de los campos del
  ramo, y esa máquina de estados es un trabajo en sí mismo.
- **Un clasificador con LLM.** La interfaz está lista y `ANTHROPIC_API_KEY` ya
  es una opción de configuración. Primero hay que medir la línea base contra
  tráfico real; si no, no hay contra qué saber si el modelo mejoró.
- **Campañas salientes con plantillas.** Los recordatorios de renovación por
  WhatsApp requieren plantillas aprobadas por Meta y registro de consentimiento;
  eso va con el trabajo de notificaciones de la fase 2.
- **Mensajes con multimedia.** Las fotos de un carro chocado y los PDF de
  pólizas son lo siguiente evidente; necesitan almacenamiento de archivos, que
  ningún módulo ha necesitado hasta ahora.
