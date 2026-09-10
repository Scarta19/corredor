# Autenticación

🇬🇧 [Read in English](../../modules/autenticacion.md) · [← todos los módulos](README.md)

## Qué tenía que hacer

No es un módulo numerado, pero todo lo que viene del Módulo 4 en adelante
depende de ella: el CRM muestra la base de clientes completa de una agencia, y
el §9 asume un *asesor responsable* —una persona con nombre— en cada cliente.
Nada después de este punto se puede construir sin saber quién está preguntando.

## Cómo se construyó

**Argon2id vía `pwdlib`,** con `verify_and_update`. Cuando suban los parámetros
de costo recomendados, un hash guardado se actualiza de forma transparente la
próxima vez que su dueño ingrese: endurecer después no exige migración ni
restablecer contraseñas.

**Tokens JWT que llevan usuario, tenant y rol.** El tenant en el token es el
punto: el [ADR-0002](../adr/0002-multi-tenancy.md) dice que un filtro
`tenant_id` olvidado es una fuga de datos, y la forma en que eso ocurre en la
práctica es un handler confiando en un encabezado. Aquí el tráfico autenticado
toma el tenant del token y no existe ninguna ruta de código que lea `X-Tenant`
para eso. Una prueba verifica que enviar el encabezado junto a un token válido
no cambia nada.

**El usuario se relee de la base en cada petición.** El token se trata como una
afirmación sobre identidad, no como el registro del usuario. Una cuenta
desactivada hace un minuto deja de funcionar ahora, y no cuando expire su token.

**El login responde igual ante "no existe" y ante "contraseña incorrecta".**
Distinguirlos convierte el formulario en una forma de enumerar quién trabaja en
la agencia.

**En el navegador, el token vive en una cookie httpOnly.** El CRM nunca lo
tiene en JavaScript. Las credenciales van a un route handler de Next, que llama
a la API desde el servidor y fija la cookie; toda llamada posterior a la API se
hace desde un Server Component o un route handler. Un XSS en el CRM no puede
llevarse el token, lo que importa más aquí que en la mayoría de aplicaciones
porque ese token abre la base de clientes completa.

## Decisiones

| Decisión | Por qué | Costo |
|---|---|---|
| Tenant del token, nunca de un encabezado | Es el único error que convierte el multi-tenancy en una brecha | Dos rutas de resolución que mantener claras: pública y autenticada |
| Releer el usuario en cada petición | La desactivación surte efecto de inmediato | Una consulta extra por petición autenticada |
| Cookie httpOnly, no `localStorage` | Un XSS no puede exfiltrar toda la cartera | Todas las llamadas a la API son del lado del servidor |
| Mismo mensaje para ambos fallos de login | Si no, el formulario enumera al personal | Un poco menos útil para quien escribió mal su correo |
| Los administradores pasan todo control de rol | Una agencia de una persona tiene admin y no gerente, y aun así necesita las vistas de gestión | Los roles son un piso, no una coincidencia exacta |

## Un error que este trabajo destapó

Al escribir las pruebas de tokens, PyJWT emitió una advertencia: *"The HMAC key
is 12 bytes long, which is below the minimum recommended length of 32 bytes."*

Nada impedía desplegar con una clave de firma demasiado débil para HS256 —y CI
estaba corriendo con una de 7 bytes. Ahora `Settings` se niega a construirse por
debajo de 32 bytes (RFC 7518 §3.2) y rechaza la clave de desarrollo fuera de
`local`. Falla al arrancar, que es la diferencia entre un despliegue que nunca
sale a producción y uno que emite sesiones falsificables en silencio.

## Los archivos

```
apps/api/src/corredor/
  core/seguridad.py     Hashing, emisión y validación de tokens. Sin importar FastAPI.
  core/config.py        El mínimo de la clave de firma
  api/deps.py           usuario_actual · tenant_del_usuario · requiere_rol
  api/v1/auth.py        POST /auth/login · GET /auth/yo

apps/admin/src/
  lib/sesion.ts               Nombre de la cookie, cliente de API del servidor, redirección ante 401
  app/api/auth/login/route.ts  Entran credenciales, sale una cookie httpOnly
  app/(panel)/layout.tsx       La guarda es la propia carga de datos
```

## Cómo verificarlo

```bash
uv run pytest apps/api/tests/unit/test_seguridad.py           # tokens, hashing, mínimo de clave
uv run pytest apps/api/tests/integration/test_aislamiento_tenants.py
```

El segundo archivo es el que importa: dos agencias, con datos, y cada
superficie del CRM revisada desde afuera —incluido que un encabezado `X-Tenant`
no puede redirigir una petición autenticada.

## Qué se dejó fuera a propósito

- **Tokens de refresco.** Un token de 12 horas y volver a ingresar es honesto
  para una herramienta interna; la rotación es complejidad sin un problema actual.
- **Restablecer contraseña por correo.** Necesita un proveedor de correo, que
  llega con el trabajo de notificaciones de la fase 2.
- **Filtrado por asesor.** Hoy todo usuario autenticado ve su agencia completa.
  Restringir a un asesor a sus propios clientes es una decisión de política de
  la agencia, no un valor por defecto que convenga suponer.
