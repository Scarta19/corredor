# 0004 — Renovaciones como máquina de estados idempotente y guiada por fechas

**Estado:** Aceptado · 2026-09-09 · 🇬🇧 [English](../../adr/0004-motor-de-renovaciones.md)

## Contexto

Los §11–12 describen contactos escalonados a 60, 30, 15 y 7 días antes del
vencimiento. Es el módulo que el documento llama uno de los activos más
importantes de la plataforma, y es donde un error se le nota más al cliente:
una tarea duplicada le desperdicia la mañana a un asesor, un mensaje duplicado
hace ver descuidada a la agencia, y uno que falta pierde la renovación.

Tres realidades hacen que la versión ingenua esté mal. Los barridos se
reintentan. Los barridos se pierden —nadie corre un cron una semana sin que
falle alguna vez. Y la cartera de una agencia existente se importa a mitad de
ciclo, así que la mayoría de las pólizas llega con varios umbrales ya vencidos.

## Decisión

Una fila de `renovaciones` representa una póliza en un umbral, con restricción
de unicidad sobre `(poliza_id, umbral_dias)`. La planificación es una función
pura, `planificar_acciones`, sobre fechas y umbrales ya existentes:

1. Un umbral que ya tiene fila nunca se vuelve a producir.
2. Un umbral todavía futuro se agenda en su propia fecha.
3. Los umbrales ya vencidos se colapsan en **una sola** acción de recuperación
   en el más reciente, y solo cuando la póliza no tiene ningún historial de
   renovación.

Una póliza vencida no produce acciones; mover su estado es tarea del barrido,
no agendar llamadas sobre ella.

## Consecuencias

**Ganamos:** el barrido puede correr cada hora, dos veces, o después de una
semana caído, y el resultado es idéntico —la restricción única es la red y el
planificador es la intención. Importar una cartera de mil pólizas produce una
tarea por póliza en lugar de cuatro.

**Pagamos:** la regla de recuperación es un criterio, no una ley. Una agencia
que prefiera ver todos los umbrales perdidos no puede hacerlo hoy sin una
opción de configuración.

**Ganamos, además:** como la planificación es pura, cada caso de arriba es una
prueba unitaria que corre en milisegundos sin base de datos —que es la razón
real por la que los casos incómodos están contemplados.
