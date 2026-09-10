# Módulo 6 — Dashboard gerencial

🇬🇧 [Read in English](../../modules/modulo-6-dashboard.md) · [← todos los módulos](README.md)

## Qué tenía que hacer

El §14 lista los indicadores; el §16 muestra las cifras de cabecera; el §15 es
la distribución de renovaciones. El objetivo declarado es el que importa:
*"pasar de tomar decisiones basadas en percepción a tomar decisiones basadas en
datos."*

El §6 fija el requisito más difícil que hay debajo: medir cuántas personas
piden cotización, cuántas son **atendidas**, cuántas reciben propuesta y
cuántas compran.

## Cómo se construyó

**El embudo es alcance acumulado, no una foto.** Esta es toda la razón por la
que `oportunidad_eventos` existe desde el Módulo 2. Una oportunidad que hoy
está en `GANADO` pasó antes por `CONTACTADO` y `COTIZANDO`; un embudo armado
con las etapas *actuales* la contaría una sola vez al final y reportaría que
nunca se contactó a nadie.

Se puede ver funcionando en los datos de demostración: una oportunidad está hoy
en `PERDIDO` y aun así cuenta en "Contactadas" y "En cotización", porque el
historial recuerda por dónde pasó.

El embudo se acota por cuándo se creó la **oportunidad**, no por cuándo ocurrió
la transición. Si no, un negocio que cerró este mes pero llegó el mes pasado
aparece como venta sin lead detrás, y la conversión pasa del 100%.

**La conversión se mide sobre oportunidades resueltas, no sobre todos los
leads.** Contar los negocios abiertos como fracasos subestima a un equipo que
simplemente está a mitad de ciclo, y el número bajaría todos los días sin que
nadie hiciera nada mal.

**Los motivos de pérdida tienen su propio panel.** Para esto se recogía el
motivo obligatorio del Módulo 4. Un gerente que ve caer la conversión necesita
saber si el problema es precio o servicio: tienen respuestas opuestas, y sin el
motivo el gráfico solo puede decir "peor".

**Restringido a gerencia y administración.** El trabajo de un asesor es la
cola. Los administradores pasan el control implícitamente, porque una agencia
con un administrador y sin gerente igual necesita las vistas de gestión.

### Los gráficos

Ambos siguen un método aplicado en orden: elegir la forma, después asignar el
color según el trabajo que hace, y después **validar la paleta con un script en
vez de a ojo**.

- **Forma.** Todo lo que se mide aquí es magnitud sobre unas pocas categorías
  ordenadas, así que ambos son barras horizontales. La tasa de conversión es un
  solo número, así que es una cifra principal, no un gráfico. Nada es una torta.
- **Color.** Las etapas del embudo y las ventanas de renovación son *ordinales*,
  así que cada una lleva una rampa de un solo tono: azul para el embudo, naranja
  para renovaciones, de modo que dos escalas secuenciales en una misma página no
  puedan confundirse.
- **Validación.** Ambas rampas pasaron por el validador de paleta para superficie
  clara y oscura: luminosidad monótona, saltos visibles entre pasos, un solo tono
  y un extremo claro que aún supera 2:1 contra la superficie. El primer candidato
  naranja **falló** (su paso más claro midió 1.73:1) y se volvió a escalonar hasta
  pasar. Ese es justamente el punto de correr la verificación en vez de confiar en
  la vista.
- **Marcas.** Las barras son de 20px (el estándar las limita a 24), con extremo de
  dato redondeado a 4px y base cuadrada. Sin líneas de grilla, sin bordes alrededor
  de las marcas, sin líneas punteadas.
- **El texto nunca lleva el color del dato.** Etiquetas y valores usan los tokens de
  texto; la barra de color al lado es la que carga la identidad.
- **Nada queda detrás del hover.** Todo valor es visible como texto, y cada gráfico
  trae una tabla "Ver los datos" que incluye el detalle del tooltip.

## Decisiones

| Decisión | Por qué | Costo |
|---|---|---|
| Embudo desde eventos, no desde la etapa actual | El §6 pregunta cuántas fueron *atendidas*, y una foto no puede responderlo | Depende de que el historial esté completo, por eso los cambios de etapa pasan por un servicio |
| Acotar el embudo por creación de la oportunidad | Si no, la conversión puede pasar del 100% | Un negocio que cierra en un mes posterior se acredita al mes en que llegó |
| Conversión sobre resueltas, no sobre todos los leads | Los negocios abiertos no son fracasos | La tasa se mueve a saltos, no suavemente |
| Dos rampas, azul y naranja | Dos escalas ordinales en una página no pueden ser confundibles | Hubo que derivar y validar una rampa naranja; el primer intento falló |
| Cifra principal para conversión, tarjetas para los conteos | Un solo número no es un gráfico | Solo se permite una cifra principal por vista; la conversión se la ganó |
| Solo gerencia y administración | El trabajo del asesor es la cola, no el marcador | Un asesor todavía no puede consultar sus propios números |

## Los archivos

```
apps/api/src/corredor/
  services/metricas.py     embudo · comerciales · clientes · polizas · motivos_de_perdida
  api/v1/dashboard.py      GET /crm/dashboard, solo gerencia

apps/admin/src/
  components/graficos.tsx  Rampas validadas, gráfico de barras, cifras
  app/(panel)/dashboard/   La vista del §14/§15/§16
```

## Cómo verificarlo

```bash
make api && cd apps/admin && npm run dev    # ingresa como admin@demo.test
```

Lo que vale la pena revisar a mano es el embudo. Mueve una oportunidad por
varias etapas en `/pipeline` y recarga `/dashboard`: cada etapa por la que pasó
conserva su conteo, incluso después de ganarse o perderse. Un embudo basado en
una foto perdería ese historial.

```bash
uv run pytest apps/api/tests/integration/test_aislamiento_tenants.py
```

Incluye los controles de rol: un asesor recibe 403 en el dashboard y 200 en la
cola, y un administrador pasa el control de gerencia sin ser gerente.

## Qué se dejó fuera a propósito

- **Series de tiempo.** Las tendencias necesitan meses de historia; la
  plataforma tiene días. Una línea sobre un mes de datos sería decoración
  disfrazada de evidencia.
- **Comparación contra el periodo anterior.** Por la misma razón: todavía no hay
  periodo anterior. La tarjeta de cifra ya tiene el espacio previsto.
- **Desempeño por asesor.** Los datos lo permiten (`oportunidad_eventos`
  registra quién movió qué), pero rankear colegas es una decisión de gestión que
  la agencia debe elegir, no algo que esta plataforma suponga.
- **Exportar a hoja de cálculo.** La siguiente petición evidente, y pequeña;
  corresponde a la cadencia de reportes que la agencia termine definiendo.
