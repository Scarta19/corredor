# 0006 — El dominio se modela en español

**Estado:** Aceptado · 2026-09-09 · 🇬🇧 [English](../../adr/0006-lenguaje-del-dominio.md)
**Modificado por:** [0009 — La documentación es bilingüe](0009-documentacion-bilingue.md)

## Contexto

Los usuarios son intermediarios de seguros colombianos. Dicen *ramo*, *póliza*,
*cotización*, *siniestro*, *asesor*, *prima*. Varios de esos términos no tienen
un equivalente limpio en inglés: *ramo* no es del todo "product" ni del todo
"line of business", y *cumplimiento* es un producto de caución específicamente
latinoamericano.

Traducirlos al inglés en el esquema significa que toda conversación entre un
desarrollador y un intermediario pasa por un glosario, y los glosarios se
desactualizan.

## Decisión

Los sustantivos del dominio, los valores de los enums y los campos de la API
usan el vocabulario del negocio: `Cliente`, `Poliza`, `Ramo`, `Oportunidad`,
`Renovacion`, y estados como `propuesta_enviada` y `proxima_a_vencer`.

La infraestructura técnica se queda en inglés —`Base`, `TenantScoped`,
`get_session`, `create_app`—, igual que los docstrings y comentarios, para que
el código siga siendo legible para alguien que no hable español.

## Consecuencias

**Ganamos:** un esquema que un intermediario puede leer y corregir. Un reporte
de error que dice "el ramo está mal" corresponde a exactamente una columna.

**Pagamos:** identificadores en dos idiomas, que se ven inconsistentes hasta
que se entiende la regla. Los acentos se omiten en los identificadores
(`Poliza`, no `Póliza`) y se conservan en todo texto de cara al usuario.

## Nota posterior

El [ADR-0009](0009-documentacion-bilingue.md) revisó la parte de este ADR
referida a la documentación: la prosa ahora existe en ambos idiomas. Lo
relativo al código sigue vigente tal como está escrito arriba.
