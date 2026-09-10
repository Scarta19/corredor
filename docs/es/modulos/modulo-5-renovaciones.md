# Módulo 5 — Renovaciones

🇬🇧 [Read in English](../../modules/modulo-5-renovaciones.md) · [← todos los módulos](README.md)

## Qué tenía que hacer

El §11 dice que este puede convertirse en uno de los activos más importantes
de la plataforma, y tiene razón: una cartera ya vendida se renueva todos los
años, y lo único que separa a la agencia de ese ingreso es acordarse de llamar.
El §12 fija contactos escalonados a 60, 30, 15 y 7 días. El §15 pide una vista
gerencial agrupada por esas ventanas.

El motor de planificación llegó con los cimientos. Este módulo son las dos
cosas que lo vuelven real: algo que lo ejecute y algún lugar donde ver el
resultado.

## Cómo se construyó

**El barrido es un trabajo programado sobre el mismo servicio que llamaría
HTTP.** Arq, una entrada de cron, una vez al día antes de que abra la oficina.
Los umbrales se miden en días, así que correrlo más seguido da el mismo
resultado a mayor costo.

**Cada agencia hace commit por separado.** Los datos malos de una agencia no
pueden impedir que las demás reciban sus tareas de renovación: renovaciones
perdidas para una agencia es un ticket de soporte, perdidas para todas es
ingreso perdido. La agencia que falla se registra en el log y se salta, y la
corrida continúa.

**El riesgo de fuga se calcula en el mismo paso**, pero solo dentro de los 120
días previos al vencimiento. El riesgo de una póliza que vence en dos años es
aritmética sobre la que nadie va a actuar, y puntuar toda la cartera cada noche
es trabajo por el trabajo mismo.

Las variables salen íntegramente de registros que la agencia ya lleva: cuántas
veces se ha renovado esta póliza (recorriendo `poliza_anterior_id` hacia atrás,
con tope para que un dato malo no genere un ciclo), hace cuánto es cliente,
cuántas otras pólizas vigentes tiene, hace cuánto nadie se comunica con él, y
cuánto se movió la prima. **Ninguna variable exige que alguien empiece a
digitar algo nuevo**: un modelo que requiere trabajo manual adicional no se usa.

Los siniestros se pasan en cero y el código dice por qué: todavía no existe el
módulo de siniestros (el §19 lo lista como futuro). Inventar la señal sería
peor que no tenerla.

**El tablero ordena dos veces, y ese es el punto.** Las ventanas son el
calendario; dentro de cada ventana va primero la póliza con más riesgo. Un
gerente puede ver dónde está la presión de fechas y, por separado, dónde es
probable que se pierda el negocio de verdad — que es exactamente la diferencia
entre la vista del §15 y una lista ordenada por fecha.

**Las pólizas vencidas siguen en el tablero.** Una póliza caída suele ser
recuperable, y un tablero que las esconde en silencio es la forma en que una
cartera se desangra.

## Decisiones

| Decisión | Por qué | Costo |
|---|---|---|
| Una corrida nocturna, no cada hora | Los umbrales son en días; más seguido es la misma respuesta por más dinero | Una póliza que cruza un umbral espera hasta la mañana, que es cuando alguien llamaría de todos modos |
| Commit por agencia, fallos salteados | Los datos malos de una no pueden costarle a todas sus renovaciones | Una agencia salteada en silencio requiere monitoreo de logs para notarse |
| Puntuar solo dentro de 120 días | El riesgo sobre el que nadie actuará no vale calcularse cada noche | Las pólizas lejanas muestran "sin calcular" en el tablero |
| Los puntajes se acumulan, no se sobrescriben | Una predicción es un registro (ADR-0005); el historial es como se atribuye una regresión | La tabla crece; algún día necesitará retención |
| Siniestros fijos en cero | El módulo de siniestros no existe; inventar la señal sería deshonesto | El modelo corre con una variable menos de las que podría usar |
| Las vencidas siguen visibles | Suelen ser recuperables | La primera ventana puede verse alarmante en una cartera descuidada |

## Los archivos

```
apps/api/src/corredor/
  services/renovaciones.py     Las reglas de planificación (vinieron con los cimientos)
  services/riesgo.py           Armado de variables y puntuación con procedencia
  workers/tareas.py            barrido_diario: barrer y puntuar, por agencia
  workers/main.py              WorkerSettings de Arq y la entrada de cron
  scripts/barrido.py           Correrlo una vez, a mano
  api/v1/renovaciones.py       Ventanas del §15 · acciones por póliza · PATCH · resumen

apps/admin/src/app/(panel)/renovaciones/   El tablero del gerente
```

## Cómo verificarlo

```bash
make barrido        # corre el barrido una vez
make barrido        # córrelo otra vez — que diga "0 acciones" es todo el diseño
```

```bash
uv run pytest apps/api/tests/unit/test_renovaciones.py          # las reglas
uv run pytest apps/api/tests/integration/test_barrido_renovaciones.py
```

Las pruebas de integración cubren los casos que sí ocurren en producción: un
barrido repetido, una caída de una semana, una póliza vencida y una cadena de
renovaciones contando como lealtad. Una prueba verifica directamente que
ninguna póliza tenga jamás el mismo umbral dos veces.

En el propio tablero, la regla de recuperación se ve en los datos: una póliza
que vence en 3 días tiene **una** acción pendiente, mientras que una que vence
en 34 tiene cuatro. Eso es `planificar_acciones` colapsando los umbrales ya
pasados en vez de inundar la cola.

## Qué se dejó fuera a propósito

- **Notificar a alguien de verdad.** El barrido crea las tareas; enviar el
  WhatsApp o el correo es el Módulo 3 más el trabajo de notificaciones de la
  fase 2. `Renovacion.notificado_en` es la columna que lo espera.
- **Registrar la renovación en sí.** Marcar una acción como completada
  funciona; crear la póliza sucesora y encadenar `poliza_anterior_id` es parte
  del trabajo de escritura listado en el Módulo 4.
- **Umbrales configurables por agencia.** El §12 dice que los tiempos exactos
  los define la agencia. El barrido ya los recibe como parámetro y lee
  `renewal_thresholds_days` de la configuración; los valores por agencia van en
  `Tenant.configuracion` cuando una segunda los necesite distintos.
- **Un modelo de fuga entrenado.** La línea base es criterio documentado, no
  parámetros ajustados. Se vuelve entrenable cuando se haya observado un ciclo
  completo de renovaciones dentro de la plataforma.
