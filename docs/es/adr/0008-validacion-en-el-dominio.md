# 0008 — La validación de solicitudes vive en el dominio, no en el borde

**Estado:** Aceptado · 2026-09-10 · 🇬🇧 [English](../../adr/0008-validacion-en-el-dominio.md)

## Contexto

Los formularios de cotización se definen en tiempo de ejecución
([ADR-0003](0003-formularios-dinamicos.md)), así que la forma de un envío no se
conoce hasta cargar el ramo. Ni Postgres ni un modelo Pydantic estático pueden
revisarlo. Algo tiene que hacerlo.

El lugar obvio es la capa HTTP, junto al endpoint que lo recibe. Aquí eso sería
un error: el formulario web es el *primer* canal que captura estos campos, no
el único. El Módulo 3 capturará los mismos campos desde una conversación de
WhatsApp, y con el tiempo un asesor los digitará desde una llamada. Tres
llamadores, una misma pregunta —"¿es esta una solicitud completa y bien
formada?"— y ninguna buena razón para tres respuestas.

## Decisión

`corredor.domain.validacion` es su dueño. Funciones puras sobre un
`FormularioRamo` y un diccionario: sin sesión, sin petición, sin framework.
Valida, convierte y normaliza, devolviendo las respuestas limpias.

Tres propiedades que garantiza:

1. **Todos los errores de una vez.** Un formulario que revela un problema por
   envío es un formulario que la gente abandona, y un formulario abandonado es
   un lead que nunca llegó. Quien llama recibe un mapa `campo → mensaje`.
2. **Normalización, no solo rechazo.** `abc-123` se vuelve `ABC123`,
   `Ana@Test.CO` se vuelve minúscula, `"2021"` se vuelve `2021`. Lo que llega a
   la base es consistente sin importar qué canal lo capturó; de lo contrario el
   mismo vehículo son dos registros según quién lo haya escrito.
3. **Los campos condicionales se exigen en ambos sentidos.** Un campo cuya
   condición no se cumple no es simplemente opcional: enviarlo es un error. Si
   no, un cliente podría mandar `valor_inmueble` declarando que no es el
   propietario, y el registro guardado se contradiría a sí mismo.

El navegador reimplementa la regla de visibilidad para que el formulario se
comporte con coherencia mientras se llena. Esa copia es de presentación; la del
servidor es la que obliga.

## Consecuencias

**Ganamos:** pruebas unitarias exhaustivas sin base de datos —cada tipo, cada
caso condicional, cada ramo entregado. El Módulo 3 hereda la validación gratis.

**Pagamos:** una regla —qué campos son visibles— queda expresada dos veces, en
Python y en TypeScript, y pueden separarse. La mitigación es que esa separación
es *segura*: el servidor rechaza lo que el navegador haya permitido de más, así
que el modo de falla es un formulario confuso y no un registro corrupto.
Generar el TypeScript desde el Python es la solución si algún día molesta.
