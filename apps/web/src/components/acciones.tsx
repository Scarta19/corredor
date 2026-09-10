import Link from "next/link";

import { Icono } from "@/components/iconos";
import { acciones } from "@/content/site";

/**
 * The four calls to action of §4, as a grid.
 *
 * These are the page's reason for existing: every route ends with them, so a
 * visitor is never more than one click from doing something.
 */
export function RejillaAcciones({ compacta = false }: { compacta?: boolean }) {
  return (
    <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
      {acciones.map((accion) => (
        <Link
          key={accion.href}
          href={accion.href}
          className={`group flex flex-col rounded-2xl border p-6 transition-colors ${
            accion.estilo === "primario"
              ? "border-tinta-700 bg-tinta-700 text-white hover:bg-tinta-800"
              : "border-borde bg-superficie hover:border-tinta-400"
          }`}
        >
          <Icono
            nombre={accion.icono}
            className={`h-7 w-7 ${
              accion.estilo === "primario"
                ? "text-tinta-100"
                : "text-tinta-600 dark:text-tinta-400"
            }`}
          />
          <span className="mt-4 text-base font-semibold">{accion.etiqueta}</span>
          {!compacta ? (
            <span
              className={`mt-2 text-sm leading-relaxed ${
                accion.estilo === "primario" ? "text-tinta-100" : "text-suave"
              }`}
            >
              {accion.descripcion}
            </span>
          ) : null}
          <span className="mt-4 text-sm font-medium">
            Continuar
            <span aria-hidden="true" className="ml-1 inline-block transition-transform group-hover:translate-x-0.5">
              →
            </span>
          </span>
        </Link>
      ))}
    </div>
  );
}
