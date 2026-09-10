"use client";

import { useRouter } from "next/navigation";
import { useState, useTransition } from "react";

import { Etiqueta, Puntaje, fecha, tonoDeEtapa } from "@/components/ui";
import { ETAPAS, MOTIVOS_PERDIDA } from "@/lib/tipos";
import type { ColumnaPipeline, Etapa, OportunidadResumen } from "@/lib/tipos";

/**
 * The §10 board.
 *
 * Cards move through a select rather than drag-and-drop. Dragging is nicer to
 * demo and worse to use here: advisors work this board on a phone between
 * calls, and a select is reachable, keyboard-accessible and impossible to drop
 * in the wrong column by accident.
 */
export function Tablero({ columnas }: { columnas: ColumnaPipeline[] }) {
  const router = useRouter();
  const [pendiente, iniciar] = useTransition();
  const [error, setError] = useState<string | null>(null);
  const [pidiendoMotivo, setPidiendoMotivo] = useState<string | null>(null);

  async function mover(id: string, etapa: Etapa, motivo?: string) {
    setError(null);
    const respuesta = await fetch(`/api/oportunidades/${id}`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ etapa, motivo_perdida: motivo ?? null }),
    });
    if (!respuesta.ok) {
      const datos = await respuesta.json().catch(() => ({}));
      setError(datos.mensaje ?? "No pudimos mover la oportunidad.");
      return;
    }
    setPidiendoMotivo(null);
    iniciar(() => router.refresh());
  }

  function alCambiar(oportunidad: OportunidadResumen, etapa: Etapa) {
    // Losing requires a reason; the API refuses without one, so ask here
    // rather than let the advisor hit an error.
    if (etapa === "perdido") {
      setPidiendoMotivo(oportunidad.id);
      return;
    }
    void mover(oportunidad.id, etapa);
  }

  return (
    <div className="space-y-4">
      {error ? (
        <p
          role="alert"
          className="rounded-lg border border-red-300 bg-red-50 px-3.5 py-2.5 text-sm text-red-800 dark:border-red-900 dark:bg-red-950 dark:text-red-200"
        >
          {error}
        </p>
      ) : null}

      <div
        className={`grid gap-4 md:grid-cols-2 xl:grid-cols-4 ${pendiente ? "opacity-60" : ""}`}
      >
        {columnas.map((columna) => {
          const etiqueta =
            ETAPAS.find((e) => e.etapa === columna.etapa)?.etiqueta ?? columna.etapa;
          return (
            <section key={columna.etapa} className="min-w-0">
              <header className="mb-2 flex items-center justify-between">
                <h2 className="text-sm font-semibold">{etiqueta}</h2>
                <span className="rounded-md bg-piedra-100 px-1.5 py-0.5 text-xs tabular-nums text-suave dark:bg-piedra-800">
                  {columna.total}
                </span>
              </header>

              <div className="space-y-2">
                {columna.oportunidades.length === 0 ? (
                  <p className="rounded-lg border border-dashed border-borde px-3 py-6 text-center text-xs text-suave">
                    Vacío
                  </p>
                ) : (
                  columna.oportunidades.map((oportunidad) => (
                    <article
                      key={oportunidad.id}
                      className="rounded-lg border border-borde bg-superficie p-3"
                    >
                      <div className="flex items-start justify-between gap-2">
                        <p className="text-sm font-medium">{oportunidad.ramo}</p>
                        <Etiqueta tono={tonoDeEtapa[oportunidad.etapa]}>
                          {etiqueta}
                        </Etiqueta>
                      </div>
                      <p className="mt-1 text-xs text-suave">
                        {fecha(oportunidad.creada_en)}
                        {oportunidad.asesor
                          ? ` · ${oportunidad.asesor.nombre}`
                          : " · sin asignar"}
                      </p>
                      <div className="mt-2">
                        <Puntaje valor={oportunidad.puntaje} />
                      </div>

                      {pidiendoMotivo === oportunidad.id ? (
                        <div className="mt-3 rounded-lg border border-borde p-2">
                          <label
                            htmlFor={`motivo-${oportunidad.id}`}
                            className="text-xs font-medium"
                          >
                            ¿Por qué se perdió?
                          </label>
                          <select
                            id={`motivo-${oportunidad.id}`}
                            defaultValue=""
                            onChange={(e) =>
                              e.target.value &&
                              void mover(oportunidad.id, "perdido", e.target.value)
                            }
                            className="mt-1 w-full rounded-md border border-borde bg-superficie px-2 py-1.5 text-xs"
                          >
                            <option value="" disabled>
                              Elige un motivo
                            </option>
                            {MOTIVOS_PERDIDA.map((m) => (
                              <option key={m.valor} value={m.valor}>
                                {m.etiqueta}
                              </option>
                            ))}
                          </select>
                          <button
                            type="button"
                            onClick={() => setPidiendoMotivo(null)}
                            className="mt-2 text-xs text-suave hover:underline"
                          >
                            Cancelar
                          </button>
                        </div>
                      ) : (
                        <select
                          aria-label="Mover a otra etapa"
                          value={oportunidad.etapa}
                          onChange={(e) =>
                            alCambiar(oportunidad, e.target.value as Etapa)
                          }
                          className="mt-3 w-full rounded-md border border-borde bg-superficie px-2 py-1.5 text-xs"
                        >
                          {ETAPAS.map((e) => (
                            <option key={e.etapa} value={e.etapa}>
                              {e.etiqueta}
                            </option>
                          ))}
                        </select>
                      )}
                    </article>
                  ))
                )}
              </div>
            </section>
          );
        })}
      </div>
    </div>
  );
}
