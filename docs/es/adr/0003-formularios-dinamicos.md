# 0003 — Los formularios de cotización son datos, no código

**Estado:** Aceptado · 2026-09-09 · 🇬🇧 [English](../../adr/0003-formularios-dinamicos.md)

## Contexto

El §5 llama al formulario inteligente uno de los componentes más importantes
del proyecto: el visitante elige una línea de negocio y ve únicamente los
campos que esa línea necesita. Automóviles pide placa, marca, línea, modelo y
uso; cumplimiento pide valor y plazo del contrato; casi no tienen nada en
común más allá de la identificación.

Modelar eso como una tabla por ramo, o un componente de formulario por ramo,
significa un despliegue cada vez que una agencia quiera hacer una pregunta
más —y la va a querer, porque esas preguntas son con las que tarifica.

## Decisión

Cada `ramo` es dueño de un documento JSONB `formulario` validado por el modelo
Pydantic `FormularioRamo`: una lista ordenada de campos tipados, cada uno con
su etiqueta, si es obligatorio, sus opciones cuando es una selección, y una
dependencia opcional respecto de la respuesta de otro campo.

El sitio público obtiene la definición de `GET /api/v1/ramos/{codigo}` y
renderiza lo que reciba. Los envíos se guardan en `solicitudes.respuestas`
junto con la `formulario_version` con la que fueron capturados.

## Consecuencias

**Ganamos:** agregar un ramo, o un campo, es configuración. El frontend no
tiene código por ramo. Las solicitudes históricas siguen siendo interpretables,
porque queda registrada la versión que las produjo.

**Pagamos:** las respuestas no tienen esquema para Postgres, así que un valor
tipado no puede ser restringido por la base de datos —la validación vive
enteramente en la aplicación, y por eso `FormularioRamo` carga peso real y está
ampliamente probado. Reportar sobre un campo JSONB es más incómodo que sobre
una columna; cuando un campo concreto se vuelva una métrica de negocio de
primera clase, se promueve a columna.

**Descartamos:** una tabla por ramo (una migración por pregunta de negocio) y
una única tabla ancha de columnas nulas (que es justamente el formulario
genérico que el documento no quiere).
