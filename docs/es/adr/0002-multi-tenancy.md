# 0002 — Multi-tenancy de esquema compartido desde el primer día

**Estado:** Aceptado · 2026-09-09 · 🇬🇧 [English](../../adr/0002-multi-tenancy.md)

## Contexto

El §19 es la parte comercialmente interesante: la primera agencia es un caso
de validación, y el producto real es una plataforma para intermediarios de
seguros en general. Meter tenancy después, sobre un esquema de un solo
inquilino, significa tocar cada tabla, cada consulta y cada índice justo en el
momento en que los datos del primer cliente que paga ya están en producción.

## Decisión

Toda tabla de negocio lleva `tenant_id` desde la primera migración, por medio
del mixin `TenantScoped`. Los índices compuestos empiezan por él. La unicidad
está acotada a él: dos agencias pueden tener un cliente con la misma cédula, y
ninguna debería ver jamás la del otro.

El tenant se resuelve una vez por petición —del token autenticado para el
tráfico del CRM, del encabezado `X-Tenant` para el tráfico público anónimo— y
nunca se toma de datos suministrados por el usuario más abajo en la pila.

## Consecuencias

**Ganamos:** dar de alta una agencia es una fila, no un despliegue. La
analítica entre agencias sigue siendo posible. Una sola base que respaldar y
migrar.

**Pagamos:** toda consulta debe filtrar por tenant, y un filtro olvidado es una
fuga de datos, no un simple error. Ese es el filo de esta decisión y no
desaparece.

**Mitigamos:** los helpers de repositorio reciben el tenant como argumento
obligatorio, de modo que omitirlo es un error de tipos y no una lectura
silenciosa de toda la tabla. La seguridad a nivel de fila de Postgres es la
segunda capa prevista —el esquema ya tiene la forma para ello— y valdrá su
costo operativo cuando las agencias dejen de ser dadas de alta por nosotros.
