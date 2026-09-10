import Link from "next/link";

import {
  Encabezado,
  Etiqueta,
  Tarjeta,
  Vacio,
  dinero,
  fecha,
  tonoDeNivel,
  tonoDeVentana,
} from "@/components/ui";
import { apiProtegido } from "@/lib/sesion";
import type { Bucket, ResumenRenovaciones } from "@/lib/tipos";

export const metadata = { title: "Renovaciones" };

/**
 * §15's view.
 *
 * Two orderings at once, and that is the point: the buckets are the calendar,
 * and inside each bucket the riskiest policy comes first. A manager can see
 * where the deadline pressure is and, separately, where the business is
 * actually likely to be lost.
 */
export default async function Renovaciones() {
  const [buckets, resumen] = await Promise.all([
    apiProtegido<Bucket[]>("/crm/renovaciones?horizonte_dias=90"),
    apiProtegido<ResumenRenovaciones>("/crm/renovaciones/resumen"),
  ]);

  return (
    <>
      <Encabezado
        titulo="Renovaciones"
        descripcion={`Alertas a ${resumen.umbrales.join(", ")} días del vencimiento. ${resumen.pendientes} acción(es) pendientes.`}
      />

      <div className="mb-8 grid gap-3 sm:grid-cols-3">
        <Tarjeta className="p-4">
          <p className="text-xs text-suave">Prima que vence en 60 días</p>
          <p className="mt-1 text-2xl font-semibold tabular-nums">
            {dinero(resumen.prima_en_riesgo)}
          </p>
        </Tarjeta>
        <Tarjeta className="p-4">
          <p className="text-xs text-suave">Acciones pendientes</p>
          <p className="mt-1 text-2xl font-semibold tabular-nums">
            {resumen.pendientes}
          </p>
        </Tarjeta>
        <Tarjeta className="p-4">
          <p className="text-xs text-suave">Completadas</p>
          <p className="mt-1 text-2xl font-semibold tabular-nums">
            {resumen.completadas}
          </p>
        </Tarjeta>
      </div>

      {buckets.every((b) => b.total === 0) ? (
        <Vacio mensaje="No hay pólizas por vencer en los próximos 90 días." />
      ) : (
        <div className="space-y-6">
          {buckets
            .filter((bucket) => bucket.total > 0)
            .map((bucket) => (
              <section key={bucket.ventana}>
                <header className="mb-2 flex flex-wrap items-center justify-between gap-2">
                  <h2 className="flex items-center gap-2 text-sm font-semibold">
                    <Etiqueta tono={tonoDeVentana[bucket.ventana]}>
                      {bucket.total}
                    </Etiqueta>
                    {bucket.etiqueta}
                  </h2>
                  <span className="text-xs tabular-nums text-suave">
                    {dinero(bucket.prima_total)} en prima
                  </span>
                </header>

                <Tarjeta className="overflow-x-auto">
                  <table className="w-full min-w-[48rem] text-sm">
                    <thead className="border-b border-borde text-left text-xs uppercase tracking-wide text-suave">
                      <tr>
                        <th className="px-4 py-2.5 font-medium">Cliente</th>
                        <th className="px-4 py-2.5 font-medium">Póliza</th>
                        <th className="px-4 py-2.5 font-medium">Vence</th>
                        <th className="px-4 py-2.5 font-medium">Prima</th>
                        <th className="px-4 py-2.5 font-medium">Riesgo de fuga</th>
                        <th className="px-4 py-2.5 font-medium">Asesor</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-borde">
                      {bucket.polizas.map((poliza) => (
                        <tr
                          key={poliza.id}
                          className="hover:bg-piedra-100/60 dark:hover:bg-piedra-800/40"
                        >
                          <td className="px-4 py-2.5">
                            <Link
                              href={`/clientes/${poliza.cliente_id}`}
                              className="font-medium hover:underline"
                            >
                              {poliza.cliente}
                            </Link>
                            {poliza.telefono ? (
                              <span className="block text-xs text-suave">
                                {poliza.telefono}
                              </span>
                            ) : null}
                          </td>
                          <td className="px-4 py-2.5">
                            {poliza.ramo}
                            <span className="block font-mono text-xs text-suave">
                              {poliza.numero} · {poliza.aseguradora}
                            </span>
                          </td>
                          <td className="whitespace-nowrap px-4 py-2.5">
                            {fecha(poliza.fecha_vencimiento)}
                            <span className="block text-xs text-suave">
                              {poliza.dias_para_vencimiento >= 0
                                ? `faltan ${poliza.dias_para_vencimiento} días`
                                : `venció hace ${Math.abs(poliza.dias_para_vencimiento)} días`}
                            </span>
                          </td>
                          <td className="whitespace-nowrap px-4 py-2.5 tabular-nums">
                            {dinero(poliza.prima)}
                          </td>
                          <td className="px-4 py-2.5">
                            {poliza.riesgo === null ? (
                              <span className="text-xs text-suave">sin calcular</span>
                            ) : (
                              <span className="flex items-center gap-2">
                                <span className="font-mono text-xs tabular-nums">
                                  {Math.round(poliza.riesgo * 100)}%
                                </span>
                                {poliza.nivel_riesgo ? (
                                  <Etiqueta tono={tonoDeNivel[poliza.nivel_riesgo]}>
                                    {poliza.nivel_riesgo}
                                  </Etiqueta>
                                ) : null}
                              </span>
                            )}
                          </td>
                          <td className="px-4 py-2.5">
                            {poliza.asesor ?? (
                              <Etiqueta tono="ambar">Sin asignar</Etiqueta>
                            )}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </Tarjeta>
              </section>
            ))}
        </div>
      )}

      <p className="mt-6 text-xs text-suave">
        El barrido nocturno programa las acciones y recalcula el riesgo. Es
        idempotente: correrlo de nuevo no duplica tareas ni vuelve a contactar a
        nadie.
      </p>
    </>
  );
}
