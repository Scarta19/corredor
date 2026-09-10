import type { Metadata } from "next";

import { Cierre } from "@/components/cierre";
import { Contenedor, Seccion, TituloSeccion } from "@/components/ui";
import { nosotros, propuestas } from "@/content/site";
import { config } from "@/lib/config";

export const metadata: Metadata = {
  title: "Nosotros",
  description:
    "Somos intermediarios de seguros: comparamos el mercado del lado del cliente y acompañamos la póliza después de la venta.",
};

export default function Nosotros() {
  return (
    <>
      <Seccion className="pb-0">
        <TituloSeccion ancla="Nosotros" titulo={nosotros.titulo} />
        <div className="mt-8 max-w-3xl space-y-5 text-lg leading-relaxed text-suave">
          {nosotros.parrafos.map((parrafo) => (
            <p key={parrafo.slice(0, 24)}>{parrafo}</p>
          ))}
        </div>
      </Seccion>

      <Seccion>
        <dl className="grid gap-6 sm:grid-cols-3">
          {nosotros.cifras.map((cifra) => (
            <div
              key={cifra.etiqueta}
              className="rounded-2xl border border-borde bg-superficie p-6"
            >
              <dt className="text-sm text-suave">{cifra.etiqueta}</dt>
              <dd className="mt-1 text-4xl font-semibold tracking-tight text-tinta-700 dark:text-tinta-300">
                {cifra.valor}
              </dd>
            </div>
          ))}
        </dl>
      </Seccion>

      <section className="border-y border-borde bg-superficie">
        <Contenedor className="py-16 sm:py-24">
          <TituloSeccion
            ancla="Cómo trabajamos"
            titulo="Cuatro compromisos concretos"
          />
          <div className="mt-12 grid gap-x-10 gap-y-10 sm:grid-cols-2">
            {propuestas.map((propuesta) => (
              <div key={propuesta.titulo}>
                <h3 className="text-lg font-semibold">{propuesta.titulo}</h3>
                <p className="mt-2 leading-relaxed text-suave">
                  {propuesta.detalle}
                </p>
              </div>
            ))}
          </div>
          <p className="mt-12 max-w-3xl text-sm leading-relaxed text-suave">
            {config.brand.nombre} opera desde {config.contacto.ciudad} y atiende
            clientes en toda la región. Nuestra remuneración la paga la
            aseguradora: para ti, el precio de la póliza es el mismo que
            tomándola directamente.
          </p>
        </Contenedor>
      </section>

      <Cierre />
    </>
  );
}
