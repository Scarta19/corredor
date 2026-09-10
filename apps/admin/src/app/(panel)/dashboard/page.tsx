import {
  BarrasHorizontales,
  Cifra,
  CifraPrincipal,
  RAMPA_AZUL,
  RAMPA_NARANJA,
} from "@/components/graficos";
import { Encabezado, Tarjeta, Vacio, dinero, fecha } from "@/components/ui";
import { apiProtegido } from "@/lib/sesion";
import type { TableroGerencial } from "@/lib/tipos";

export const metadata = { title: "Dashboard" };

const porcentaje = (v: number) =>
  `${(v * 100).toLocaleString("es-CO", { maximumFractionDigits: 1 })}%`;

export default async function Dashboard() {
  const t = await apiProtegido<TableroGerencial>("/crm/dashboard");

  const hayEmbudo = t.embudo.some((p) => p.alcanzadas > 0);

  return (
    <>
      <Encabezado
        titulo="Dashboard"
        descripcion={`Periodo del ${fecha(t.desde)} al ${fecha(t.hasta)}.`}
      />

      {/* §16 — the headline numbers. One hero figure, then the counts. */}
      <div className="grid gap-3 lg:grid-cols-[1fr_2fr]">
        <CifraPrincipal
          etiqueta="Conversión"
          valor={porcentaje(t.comercial.conversion)}
          nota="Sobre oportunidades ya resueltas. Las abiertas todavía no cuentan ni a favor ni en contra."
        />
        <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
          <Cifra etiqueta="Leads del mes" valor={t.comercial.leads} />
          <Cifra etiqueta="Cotizaciones" valor={t.comercial.cotizaciones} />
          <Cifra etiqueta="Ventas" valor={t.comercial.ventas} />
          <Cifra etiqueta="Perdidas" valor={t.comercial.perdidas} />
        </div>
      </div>

      <div className="mt-6 grid gap-4 lg:grid-cols-2">
        {/* §6 — the funnel, from the event log rather than current stages. */}
        {hayEmbudo ? (
          <BarrasHorizontales
            titulo="Embudo comercial"
            descripcion="Oportunidades del periodo que alcanzaron cada etapa, en cualquier momento."
            rampa={RAMPA_AZUL}
            barras={t.embudo.map((paso) => ({
              etiqueta: paso.etiqueta,
              valor: paso.alcanzadas,
              detalle: `${porcentaje(paso.conversion_desde_inicio)} de las recibidas · ${porcentaje(paso.conversion_desde_anterior)} de la etapa anterior`,
            }))}
            pie="Una oportunidad ganada pasó antes por contactada y en cotización: el embudo se arma con el historial, no con la etapa actual."
          />
        ) : (
          <Tarjeta className="p-5">
            <h3 className="text-sm font-semibold">Embudo comercial</h3>
            <div className="mt-4">
              <Vacio mensaje="Todavía no hay oportunidades en este periodo." />
            </div>
          </Tarjeta>
        )}

        {/* §15 — the renewal distribution. */}
        <BarrasHorizontales
          titulo="Renovaciones por ventana"
          descripcion="Pólizas vivas según cuánto les falta para vencer."
          rampa={RAMPA_NARANJA}
          barras={t.ventanas_renovacion.map((v) => ({
            etiqueta: v.etiqueta,
            valor: v.total,
            detalle: `${v.total} póliza(s)`,
          }))}
          pie={`Alertas automáticas a ${t.umbrales_renovacion.join(", ")} días del vencimiento.`}
        />
      </div>

      <div className="mt-6 grid gap-4 lg:grid-cols-2">
        <Tarjeta className="p-5">
          <h3 className="text-sm font-semibold">¿Por qué se pierden?</h3>
          <p className="mt-1 text-xs text-suave">
            El motivo es obligatorio al marcar una oportunidad como perdida.
            Sin él no se puede distinguir un problema de precio de uno de
            servicio.
          </p>
          {t.motivos_perdida.length === 0 ? (
            <div className="mt-4">
              <Vacio mensaje="Sin pérdidas registradas en el periodo." />
            </div>
          ) : (
            <dl className="mt-4 divide-y divide-borde">
              {t.motivos_perdida.map((m) => (
                <div
                  key={m.motivo}
                  className="flex items-baseline justify-between py-2"
                >
                  <dt className="text-sm">{m.etiqueta}</dt>
                  <dd className="text-sm font-medium tabular-nums">{m.total}</dd>
                </div>
              ))}
            </dl>
          )}
        </Tarjeta>

        <div className="grid content-start gap-3 sm:grid-cols-2">
          <Cifra etiqueta="Clientes nuevos" valor={t.clientes.nuevos} />
          <Cifra
            etiqueta="Clientes activos"
            valor={t.clientes.activos}
            nota="Con al menos una póliza vigente"
          />
          <Cifra
            etiqueta="Clientes recurrentes"
            valor={t.clientes.recurrentes}
            nota="Con más de una póliza"
          />
          <Cifra etiqueta="Prima emitida" valor={dinero(t.comercial.prima_ganada)} />
          <Cifra etiqueta="Pólizas vigentes" valor={t.polizas.activas} />
          <Cifra
            etiqueta="Próximas a vencer"
            valor={t.polizas.proximas_a_vencer}
          />
          <Cifra etiqueta="Pólizas vencidas" valor={t.polizas.vencidas} />
          <Cifra
            etiqueta="Renovaciones pendientes"
            valor={t.polizas.renovaciones_pendientes}
            nota={`${t.polizas.renovaciones_completadas} completadas`}
          />
        </div>
      </div>
    </>
  );
}
