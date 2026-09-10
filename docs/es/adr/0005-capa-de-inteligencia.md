# 0005 — La capa de inteligencia es estructural, no una función de fase 3

**Estado:** Aceptado · 2026-09-09 · 🇬🇧 [English](../../adr/0005-capa-de-inteligencia.md)

## Contexto

El §18 ubica la "IA para atención y clasificación" en la fase 3, después de que
el CRM y las automatizaciones estén funcionando. Como secuencia de *entrega*
eso es correcto: una agencia sin datos organizados no tiene sobre qué ser
inteligente, y desplegar un modelo antes del CRM sería construir sobre arena.

Como decisión de *esquema* es una trampa. Las predicciones que llegan después,
a tablas que no fueron diseñadas para guardarlas, terminan como una columna
atornillada a `oportunidades`: sin versión, sin explicación, sobrescrita en
cada corrida e imposible de auditar la primera vez que alguien pregunte por
qué se despriorizó un lead.

## Decisión

El orden de entrega se queda como está en el documento. El esquema no espera.

`puntajes_lead`, `riesgos_renovacion`, `recomendaciones_cross_sell` y
`analisis_mensajes` existen desde la primera migración, y cada uno lleva el
nombre del modelo, su versión, las variables de entrada y una explicación
legible. Rigen tres reglas:

1. Una predicción registra el modelo y la versión que la produjeron.
2. Una predicción registra sus entradas, para poder reproducirla y para poder
   reconstruir conjuntos de entrenamiento desde la verdad de producción.
3. Una predicción nunca sobrescribe el registro de negocio que describe. Los
   puntajes viven al lado del CRM; la decisión de una persona siempre manda.

`packages/ml` entrega líneas base interpretables detrás de un protocolo
`Modelo` —un puntuador de tipo logístico para leads y fuga, y una tabla de
afinidad para venta cruzada. Son honestas respecto de ser líneas base y corren
sin base de datos.

## Consecuencias

**Ganamos:** el día que haya suficientes oportunidades cerradas para entrenar,
el conjunto de entrenamiento ya existe, porque producción viene registrando
variables y resultados desde el MVP. Cambiar una línea base por un modelo
aprendido es una clase, detrás de una interfaz que no cambia.

**Pagamos:** cuatro tablas y un paquete que se ganan el sustento despacio. Los
pesos de las líneas base son criterio documentado, no parámetros ajustados, y
decir otra cosa sería deshonesto —su verdadero trabajo es ser un piso que un
modelo entrenado deba superar.

**Aceptamos:** el principio del §8 es vinculante para el módulo de WhatsApp. La
automatización se encarga de recepción, preguntas frecuentes, captura y
clasificación. Todo lo que requiera criterio comercial o técnico pasa a una
persona, y `analisis_mensajes.requiere_humano` hace esa frontera explícita y
auditable en lugar de dejarla implícita en un prompt.
