import type { ReactNode } from "react";

import type { Etapa, Nivel, Ventana } from "@/lib/tipos";

export function Tarjeta({
  children,
  className = "",
}: {
  children: ReactNode;
  className?: string;
}) {
  return (
    <div className={`rounded-xl border border-borde bg-superficie ${className}`}>
      {children}
    </div>
  );
}

export function Encabezado({
  titulo,
  descripcion,
  children,
}: {
  titulo: string;
  descripcion?: string;
  children?: ReactNode;
}) {
  return (
    <div className="mb-6 flex flex-wrap items-end justify-between gap-4">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight">{titulo}</h1>
        {descripcion ? (
          <p className="mt-1 text-sm text-suave">{descripcion}</p>
        ) : null}
      </div>
      {children}
    </div>
  );
}

export function Vacio({ mensaje }: { mensaje: string }) {
  return (
    <div className="rounded-xl border border-dashed border-borde px-6 py-12 text-center text-sm text-suave">
      {mensaje}
    </div>
  );
}

const tonos = {
  neutro: "bg-piedra-100 text-piedra-700 dark:bg-piedra-800 dark:text-piedra-200",
  azul: "bg-tinta-50 text-tinta-700 dark:bg-tinta-950 dark:text-tinta-300",
  verde: "bg-emerald-50 text-emerald-700 dark:bg-emerald-950 dark:text-emerald-300",
  ambar: "bg-amber-50 text-amber-800 dark:bg-amber-950 dark:text-amber-300",
  rojo: "bg-red-50 text-red-700 dark:bg-red-950 dark:text-red-300",
} as const;

export type Tono = keyof typeof tonos;

export function Etiqueta({
  children,
  tono = "neutro",
}: {
  children: ReactNode;
  tono?: Tono;
}) {
  return (
    <span
      className={`inline-flex items-center rounded-md px-2 py-0.5 text-xs font-medium ${tonos[tono]}`}
    >
      {children}
    </span>
  );
}

export const tonoDeEtapa: Record<Etapa, Tono> = {
  nuevo: "azul",
  contactado: "azul",
  cotizando: "ambar",
  propuesta_enviada: "ambar",
  en_negociacion: "ambar",
  ganado: "verde",
  perdido: "rojo",
};

export const tonoDeNivel: Record<Nivel, Tono> = {
  alto: "verde",
  medio: "ambar",
  bajo: "neutro",
};

/**
 * Renewal windows are coloured by urgency, not by prettiness: a manager
 * scanning the list should see risk before they read anything.
 */
export const tonoDeVentana: Record<Ventana, Tono> = {
  vencida: "rojo",
  critica: "rojo",
  urgente: "ambar",
  proxima: "ambar",
  planificada: "azul",
  futura: "neutro",
};

export const etiquetaDeVentana: Record<Ventana, string> = {
  vencida: "Vencida",
  critica: "Menos de 7 días",
  urgente: "8 a 15 días",
  proxima: "16 a 30 días",
  planificada: "31 a 60 días",
  futura: "Más de 60 días",
};

/** A lead score as a percentage — a probability, shown as one. */
export function Puntaje({ valor }: { valor: number | null }) {
  if (valor === null) {
    return <span className="text-xs text-suave">—</span>;
  }
  return (
    <span className="inline-flex items-center gap-2">
      <span className="h-1.5 w-12 overflow-hidden rounded-full bg-piedra-200 dark:bg-piedra-800">
        <span
          className="block h-full rounded-full bg-tinta-600"
          style={{ width: `${Math.round(valor * 100)}%` }}
        />
      </span>
      <span className="font-mono text-xs tabular-nums">
        {Math.round(valor * 100)}%
      </span>
    </span>
  );
}

const SOLO_FECHA = /^\d{4}-\d{2}-\d{2}$/;

/**
 * Format a date the API sent.
 *
 * `new Date("2026-09-01")` is parsed as UTC midnight, which in Colombia
 * (UTC-5) renders as 31 August — so a policy expiring on the 1st would be
 * shown as expiring the day before. Date-only values are therefore built as
 * local dates; timestamps, which carry a time, are left alone.
 */
export function fecha(iso: string): string {
  const valor = SOLO_FECHA.test(iso)
    ? (() => {
        const [anio, mes, dia] = iso.split("-").map(Number);
        return new Date(anio, mes - 1, dia);
      })()
    : new Date(iso);

  return valor.toLocaleDateString("es-CO", {
    day: "2-digit",
    month: "short",
    year: "numeric",
  });
}

export function fechaHora(iso: string): string {
  return new Date(iso).toLocaleString("es-CO", {
    day: "2-digit",
    month: "short",
    hour: "2-digit",
    minute: "2-digit",
  });
}

export function dinero(valor: string | number): string {
  return new Intl.NumberFormat("es-CO", {
    style: "currency",
    currency: "COP",
    maximumFractionDigits: 0,
  }).format(Number(valor));
}
