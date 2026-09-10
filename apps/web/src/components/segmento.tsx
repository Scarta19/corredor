import { Cierre } from "@/components/cierre";
import { RejillaRamos } from "@/components/ramos";
import { Contenedor, Seccion, TituloSeccion } from "@/components/ui";
import type { RamoResumen } from "@/lib/api";

/**
 * The shared shape of the two audience pages (§4).
 *
 * Personas and empresas buy for different reasons and need different words,
 * but the page is the same page — so the copy is a prop and the layout is not
 * duplicated.
 */
export function PaginaSegmento({
  ancla,
  titulo,
  descripcion,
  situaciones,
  ramos,
  cierre,
}: {
  ancla: string;
  titulo: string;
  descripcion: string;
  situaciones: { titulo: string; detalle: string }[];
  ramos: RamoResumen[];
  cierre: string;
}) {
  return (
    <>
      <Seccion className="pb-0">
        <TituloSeccion ancla={ancla} titulo={titulo} descripcion={descripcion} />
      </Seccion>

      <Seccion>
        <RejillaRamos ramos={ramos} />
      </Seccion>

      <section className="border-y border-borde bg-superficie">
        <Contenedor className="py-16 sm:py-24">
          <TituloSeccion ancla="Cuándo llamarnos" titulo="Situaciones típicas" />
          <div className="mt-10 grid gap-8 sm:grid-cols-2 lg:grid-cols-3">
            {situaciones.map((situacion) => (
              <div key={situacion.titulo}>
                <h3 className="font-semibold">{situacion.titulo}</h3>
                <p className="mt-2 text-sm leading-relaxed text-suave">
                  {situacion.detalle}
                </p>
              </div>
            ))}
          </div>
        </Contenedor>
      </section>

      <Cierre descripcion={cierre} />
    </>
  );
}
