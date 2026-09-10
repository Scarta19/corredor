# 0001 — Un monolito modular, no seis servicios

**Estado:** Aceptado · 2026-09-09 · 🇬🇧 [English](../../adr/0001-monolito-modular.md)

## Contexto

El documento del proyecto describe seis módulos —web, cotizador, WhatsApp,
CRM, renovaciones, dashboard— y el §17 es explícito en que no deben
convertirse en seis sistemas independientes. Comparten un mismo conjunto de
datos: un mensaje de WhatsApp se vuelve una solicitud de cotización, que se
vuelve una oportunidad, que se vuelve una póliza, que genera renovaciones,
todo describiendo al mismo cliente.

El equipo que construye esto es pequeño. El primer despliegue atiende a una
agencia.

## Decisión

Una sola API desplegable, dividida internamente por fronteras de módulo:

- `domain/` — el modelo, sin conocimiento de transporte ni de almacenamiento
- `services/` — operaciones de negocio, que reciben una sesión y devuelven objetos de dominio
- `api/` — HTTP, que puede importar servicios pero nunca al revés
- `workers/` — trabajo programado y encolado, sobre los mismos servicios
- `packages/ml/` — modelos, importables sin base de datos ni framework web

Los módulos se hablan por funciones de servicio y por la base de datos
compartida, no por HTTP.

## Consecuencias

**Ganamos:** una sola transacción que abarca la solicitud y su oportunidad, de
modo que un lead no puede quedar a medio crear. Un solo historial de
migraciones. Un solo despliegue. Mover una frontera es una operación de
editor, no un despliegue coordinado.

**Pagamos:** toda la API escala como una unidad, y nada estructural impide que
un import descuidado cruce una frontera —si eso empieza a pasar, CI tendría
que aprender a revisar imports.

**Dejamos abierto:** los servicios son la costura natural. Cuando un módulo
necesite de verdad escalar aparte —el webhook de WhatsApp es el primer
candidato—, puede extraerse detrás de su interfaz de servicio actual sin tocar
a quienes lo llaman.
