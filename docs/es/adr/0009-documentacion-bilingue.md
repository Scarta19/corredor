# 0009 — La documentación es bilingüe

**Estado:** Aceptado · 2026-09-10 · 🇬🇧 [English](../../adr/0009-documentacion-bilingue.md)
**Modifica:** [0006 — El dominio se modela en español](0006-lenguaje-del-dominio.md)

## Contexto

El ADR-0006 resolvió el código: vocabulario de dominio en español,
infraestructura técnica y documentación en inglés. El argumento para dejar la
documentación en inglés era que así sigue siendo legible para alguien que no
hable español.

Ese argumento estaba incompleto. Pesaba a un público e ignoraba al otro. Las
personas que deciden si esta plataforma vale la pena —el dueño de la agencia,
el gerente que lee el tablero de renovaciones, el asesor que se está
capacitando— trabajan en español. Entregarles un documento de arquitectura en
inglés es no entregarles nada.

Ambos públicos son reales, y ninguno es subconjunto del otro.

## Decisión

La prosa existe en los dos idiomas, en árboles paralelos:

```
README.md            docs/roadmap.md   docs/architecture/   docs/adr/            ← inglés
README.es.md         docs/es/hoja-de-ruta.md  docs/es/arquitectura/  docs/es/adr/  ← español
```

Cada documento lleva un enlace a su contraparte. Ninguno de los dos árboles es
una traducción automática del otro: están escritos para leerse con naturalidad,
y un cambio en uno no está terminado hasta que el otro coincide.

El código, los docstrings y los comentarios se quedan en inglés, exactamente
como lo decidió el ADR-0006 —esa parte sigue en pie. La división es: **el
código le habla a quien programa, la documentación le habla a todos.**

## Consecuencias

**Ganamos:** un repositorio que una agencia colombiana puede evaluar en sus
propios términos, y que un ingeniero de cualquier país todavía puede leer.

**Pagamos:** cada cambio de documentación son dos cambios, y las copias se van a
separar cuando alguien ande de afán. No hay herramienta que lo detecte —la
mitigación honesta es que la desactualización de la documentación es visible
para quien la lee, a diferencia de la del código, y que cualquiera de las dos
versiones desactualizada sigue siendo mejor que una de ellas inexistente.

**Aceptamos:** si algún día la carga supera al valor, lo correcto es eliminar
el árbol en inglés y conservar el español, no al revés. Los usuarios van
primero.
