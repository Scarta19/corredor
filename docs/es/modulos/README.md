# Cómo se construyó cada módulo

🇬🇧 [Read in English](../../modules/README.md)

Un documento por módulo. Todos responden las mismas preguntas, en el mismo
orden:

1. **Qué tenía que hacer** — el requisito del documento del proyecto, en un párrafo
2. **Cómo se construyó** — la forma de la solución y por qué esa forma
3. **Decisiones** — qué se eligió, qué se descartó y qué cuesta
4. **Los archivos** — dónde mirar y de qué se encarga cada parte
5. **Cómo verificarlo** — comandos que prueban que funciona
6. **Qué se dejó fuera a propósito** — y qué módulo lo retoma

Son bitácoras de construcción, no referencia de API. Explican *por qué el
código se ve como se ve*, que es lo primero que se pierde y lo más difícil de
reconstruir después.

| # | Módulo | Estado | Documento |
|---|--------|--------|-----------|
| 1 | Web profesional | Listo | [modulo-1-web.md](modulo-1-web.md) |
| 2 | Cotizador inteligente | Listo | [modulo-2-cotizador.md](modulo-2-cotizador.md) |
| — | Autenticación | Listo | [autenticacion.md](autenticacion.md) |
| 4 | CRM | En curso | [modulo-4-crm.md](modulo-4-crm.md) |
| 5 | Renovaciones | Listo | [modulo-5-renovaciones.md](modulo-5-renovaciones.md) |
| 6 | Dashboard | Listo | [modulo-6-dashboard.md](modulo-6-dashboard.md) |
| 3 | WhatsApp | Listo (faltan credenciales de Meta) | [modulo-3-whatsapp.md](modulo-3-whatsapp.md) |

El trasfondo más profundo está en los [ADR](../adr/README.md); este árbol los
da por supuestos en vez de repetirlos.
