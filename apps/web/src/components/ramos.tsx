import Link from "next/link";

import { IconoEscudo } from "@/components/iconos";
import { Boton } from "@/components/ui";
import type { RamoResumen } from "@/lib/api";
import { config, whatsappUrl } from "@/lib/config";

/**
 * The catalogue, rendered from whatever the API returns.
 *
 * Nothing about a specific line of business is hard-coded here: a brokerage
 * that adds "Transporte" tomorrow sees it on the site without a deploy.
 */
export function RejillaRamos({ ramos }: { ramos: RamoResumen[] }) {
  if (ramos.length === 0) {
    return <CatalogoNoDisponible />;
  }

  return (
    <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
      {ramos.map((ramo) => (
        <Link
          key={ramo.codigo}
          href={`/cotizar/${ramo.codigo}`}
          className="group flex flex-col rounded-2xl border border-borde bg-superficie p-6 transition-colors hover:border-tinta-400"
        >
          <span className="grid h-10 w-10 place-items-center rounded-xl bg-tinta-50 text-tinta-700 dark:bg-tinta-950 dark:text-tinta-300">
            <IconoEscudo className="h-5 w-5" />
          </span>
          <h3 className="mt-4 text-lg font-semibold">{ramo.nombre}</h3>
          {ramo.descripcion ? (
            <p className="mt-2 flex-1 text-sm leading-relaxed text-suave">
              {ramo.descripcion}
            </p>
          ) : null}
          <span className="mt-4 text-sm font-medium text-tinta-700 dark:text-tinta-300">
            Cotizar
            <span aria-hidden="true" className="ml-1 inline-block transition-transform group-hover:translate-x-0.5">
              →
            </span>
          </span>
        </Link>
      ))}
    </div>
  );
}

/**
 * Shown when the catalogue endpoint is unreachable.
 *
 * The site's job is to get the visitor to a human. Losing the product list is
 * a degraded page, not a dead end, so the contact routes stay in front of them.
 */
function CatalogoNoDisponible() {
  return (
    <div className="rounded-2xl border border-dashed border-borde bg-superficie p-8 text-center">
      <h3 className="text-lg font-semibold">
        No pudimos cargar el listado de seguros
      </h3>
      <p className="mx-auto mt-2 max-w-md text-sm leading-relaxed text-suave">
        Es un problema nuestro, no tuyo. Escríbenos y te decimos enseguida si
        manejamos lo que necesitas asegurar.
      </p>
      <div className="mt-6 flex flex-wrap justify-center gap-3">
        <Boton
          href={whatsappUrl(
            `Hola ${config.brand.corto}, quiero información sobre un seguro.`,
          )}
        >
          Escribir por WhatsApp
        </Boton>
        <Boton href="/contacto" variante="secundario">
          Dejar mis datos
        </Boton>
      </div>
    </div>
  );
}
