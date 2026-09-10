# Hoja de ruta

🇬🇧 [Read in English](../roadmap.md)

Tres fases de entrega. El orden es el del documento del proyecto; el porqué de
construir algunos cimientos antes de su fase está en los ADR enlazados.

## Fase 1 — MVP

*Objetivo: la agencia tiene un canal digital organizado para captar y
administrar clientes.*

- [x] Modelo de dominio: tenancy, catálogo, CRM, pipeline, pólizas, renovaciones
- [x] Esquema y validación de formularios dinámicos ([ADR-0003](adr/0003-formularios-dinamicos.md))
- [x] API pública de catálogo (`/ramos`, `/ramos/{codigo}`)
- [x] Semilla de agencia de demostración con cartera sintética
- [x] **Módulo 1 — Web profesional** — 9 rutas, las cuatro acciones del §4, catálogo servido por la API, sitemap/robots/JSON-LD
- [x] **Módulo 2 — Cotizador inteligente** — formularios dinámicos, validación en el dominio, `POST /solicitudes`, código `COT-000125`, deduplicación de clientes, oportunidad + evento de auditoría + puntaje en una sola transacción
- [x] **Autenticación** — Argon2id, JWT con tenant, sesión httpOnly en el CRM
- [x] **Módulo 4 — CRM** — cola ordenada por puntaje, tablero del §10, ficha única del §9
- [ ] Módulo 4 — escritura: editar clientes, registrar pólizas y cotizaciones a mano ← siguiente

## Fase 2 — Automatización

*Objetivo: el sistema empieza a hacer trabajo que hoy hace una persona.*

- [x] Motor de planificación de renovaciones ([ADR-0004](adr/0004-motor-de-renovaciones.md))
- [x] **Módulo 5 — Renovaciones** — barrido nocturno con Arq, riesgo de fuga, tablero de ventanas del §15
- [ ] Notificaciones: nuevo lead al equipo, acciones de renovación al asesor
- [ ] Reglas de asignación de leads
- [x] **Módulo 3 — WhatsApp** — webhook firmado, clasificación de intención, derivación del §8. Faltan credenciales de Meta para enviar.

## Fase 3 — Inteligencia

*Objetivo: la plataforma deja de ser un sistema de registro y pasa a ser un
instrumento comercial.*

- [x] Esquema de predicciones con modelo, versión, variables y explicaciones ([ADR-0005](adr/0005-capa-de-inteligencia.md))
- [x] Líneas base: puntaje de leads, riesgo de renovación, afinidad de venta cruzada
- [x] **Módulo 6 — Dashboard** — embudo desde el historial, ventanas del §15, motivos de pérdida, solo gerencia
- [x] Comprensión de mensajes en reemplazo del menú numerado (línea base por reglas)
- [ ] Modelos entrenados, cuando haya suficientes oportunidades cerradas para aprender de ellas
- [ ] Segmentación de clientes y automatizaciones comerciales

## Más allá

§19 del documento: la plataforma se generaliza a los intermediarios de seguros
en general. El esquema multi-tenant ([ADR-0002](adr/0002-multi-tenancy.md)) era
la parte que había que decidir temprano; lo demás —módulos configurables,
siniestros, gestión documental— es aditivo.
