/**
 * Chart primitives.
 *
 * Horizontal bars only, because every measure on this dashboard is magnitude
 * across a handful of ordered categories — funnel stages, renewal windows —
 * and a bar is the form that reads without decoding.
 *
 * The two ordinal ramps below were validated with the palette checker rather
 * than chosen by eye: monotone lightness, visible step gaps, and a light end
 * that still clears 2:1 against the surface it is drawn on. Blue carries the
 * funnel, orange the renewal windows, so two sequential scales on one page are
 * never mistaken for each other.
 */

import type { CSSProperties, ReactNode } from "react";

/** blue 250→650 on light, 200→600 on dark. */
export const RAMPA_AZUL = {
  claro: ["#86b6ef", "#5598e7", "#2a78d6", "#1c5cab", "#104281"],
  oscuro: ["#9ec5f4", "#6da7ec", "#3987e5", "#256abf", "#184f95"],
};

/** orange, stepped and validated for both surfaces. */
export const RAMPA_NARANJA = {
  claro: ["#f0a077", "#e88355", "#dc6636", "#c04f21", "#98401a", "#702f12"],
  oscuro: ["#f9cbb3", "#f2a884", "#e88355", "#d95926", "#b34620", "#8c3718"],
};

export interface Barra {
  etiqueta: string;
  valor: number;
  /** Shown in the hover tooltip; the chart stays readable without it. */
  detalle?: string;
}

/**
 * A single-series horizontal bar chart.
 *
 * One series means no legend: the title already says what is plotted, and a
 * box with one swatch would only restate it.
 */
export function BarrasHorizontales({
  titulo,
  descripcion,
  barras,
  rampa,
  formatear = (v) => v.toLocaleString("es-CO"),
  pie,
}: {
  titulo: string;
  descripcion?: string;
  barras: Barra[];
  rampa: { claro: string[]; oscuro: string[] };
  formatear?: (valor: number) => string;
  pie?: ReactNode;
}) {
  const maximo = Math.max(...barras.map((b) => b.valor), 1);

  return (
    <figure className="rounded-xl border border-borde bg-superficie p-5">
      <figcaption>
        <h3 className="text-sm font-semibold">{titulo}</h3>
        {descripcion ? (
          <p className="mt-1 text-xs text-suave">{descripcion}</p>
        ) : null}
      </figcaption>

      <div className="mt-5 space-y-3">
        {barras.map((barra, indice) => {
          const claro = rampa.claro[Math.min(indice, rampa.claro.length - 1)];
          const oscuro = rampa.oscuro[Math.min(indice, rampa.oscuro.length - 1)];
          const ancho = maximo > 0 ? (barra.valor / maximo) * 100 : 0;

          return (
            <div key={barra.etiqueta} className="group relative">
              <div className="flex items-baseline justify-between gap-3">
                {/* Labels wear text tokens, never the series colour. */}
                <span className="text-xs text-suave">{barra.etiqueta}</span>
                <span className="text-xs font-medium tabular-nums">
                  {formatear(barra.valor)}
                </span>
              </div>

              <div className="mt-1 h-5 w-full rounded-sm bg-piedra-100 dark:bg-piedra-800">
                {/* The step is passed as two custom properties and picked by
                    the dark variant, so the swap needs no client component and
                    degrades to a visible bar if either value is unsupported. */}
                <div
                  className="h-5 rounded-r-[4px] bg-[var(--paso-claro)] transition-[width] dark:bg-[var(--paso-oscuro)]"
                  style={
                    {
                      width: `${Math.max(ancho, barra.valor > 0 ? 1.5 : 0)}%`,
                      "--paso-claro": claro,
                      "--paso-oscuro": oscuro,
                    } as CSSProperties
                  }
                />
              </div>

              {barra.detalle ? (
                <div
                  role="tooltip"
                  className="pointer-events-none absolute -top-1 right-0 z-10 hidden -translate-y-full rounded-lg border border-borde bg-superficie px-2.5 py-1.5 text-xs shadow-lg group-hover:block"
                >
                  {barra.detalle}
                </div>
              ) : null}
            </div>
          );
        })}
      </div>

      {pie ? <p className="mt-4 text-xs text-suave">{pie}</p> : null}

      {/* Every chart carries a table view, so nothing is gated behind colour
          or hover. */}
      <details className="mt-4">
        <summary className="cursor-pointer text-xs text-suave hover:text-texto">
          Ver los datos
        </summary>
        <table className="mt-2 w-full text-xs">
          <tbody className="divide-y divide-borde">
            {barras.map((barra) => (
              <tr key={barra.etiqueta}>
                <th scope="row" className="py-1.5 text-left font-normal text-suave">
                  {barra.etiqueta}
                </th>
                {barra.detalle ? (
                  <td className="py-1.5 pl-3 text-left text-suave">
                    {barra.detalle}
                  </td>
                ) : null}
                <td className="py-1.5 pl-3 text-right tabular-nums">
                  {formatear(barra.valor)}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </details>
    </figure>
  );
}

/**
 * The one number the dashboard leads with.
 *
 * Proportional figures, not tabular: `tabular-nums` gives every digit the
 * width of a zero, which looks loose at display sizes. Tabular is for columns.
 */
export function CifraPrincipal({
  etiqueta,
  valor,
  nota,
}: {
  etiqueta: string;
  valor: string;
  nota?: string;
}) {
  return (
    <div className="rounded-xl border border-borde bg-superficie p-5">
      <p className="text-xs text-suave">{etiqueta}</p>
      <p className="mt-1 text-5xl font-semibold tracking-tight">{valor}</p>
      {nota ? <p className="mt-2 text-xs text-suave">{nota}</p> : null}
    </div>
  );
}

export function Cifra({
  etiqueta,
  valor,
  nota,
}: {
  etiqueta: string;
  valor: string | number;
  nota?: string;
}) {
  return (
    <div className="rounded-xl border border-borde bg-superficie p-4">
      <p className="text-xs text-suave">{etiqueta}</p>
      <p className="mt-1 text-2xl font-semibold">{valor}</p>
      {nota ? <p className="mt-1 text-xs text-suave">{nota}</p> : null}
    </div>
  );
}
