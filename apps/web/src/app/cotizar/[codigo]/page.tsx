import type { Metadata } from "next";
import { notFound } from "next/navigation";

import { Boton, Seccion, Tarjeta, TituloSeccion } from "@/components/ui";
import { listarRamos, obtenerRamo } from "@/lib/api";
import { config, whatsappUrl } from "@/lib/config";

type Params = { params: Promise<{ codigo: string }> };

/**
 * Pre-render a page per ramo at build time. The catalogue changes rarely, and
 * these are the pages search traffic lands on.
 */
export async function generateStaticParams() {
  const ramos = await listarRamos();
  return ramos.map((ramo) => ({ codigo: ramo.codigo }));
}

export async function generateMetadata({ params }: Params): Promise<Metadata> {
  const { codigo } = await params;
  const ramo = await obtenerRamo(codigo);
  if (!ramo) return { title: "Cotización" };
  return {
    title: `Cotizar ${ramo.nombre}`,
    description:
      ramo.descripcion ??
      `Solicita una cotización de ${ramo.nombre.toLowerCase()} con ${config.brand.nombre}.`,
  };
}

export default async function CotizarRamo({ params }: Params) {
  const { codigo } = await params;
  const ramo = await obtenerRamo(codigo);
  if (!ramo) notFound();

  // The form definition comes from the API, so this page lists exactly what
  // the visitor will be asked — including for a ramo added after this page
  // was written. Conditional fields are left out: whether they are asked
  // depends on earlier answers.
  const campos = ramo.formulario.campos
    .filter((campo) => campo.depende_de === null)
    .sort((a, b) => a.orden - b.orden || a.nombre.localeCompare(b.nombre));

  const mensaje = `Hola ${config.brand.corto}, quiero cotizar un seguro de ${ramo.nombre}.`;

  return (
    <Seccion>
      <TituloSeccion
        ancla={`Cotizar · ${ramo.nombre}`}
        titulo={`Cotización de ${ramo.nombre.toLowerCase()}`}
        descripcion={ramo.descripcion ?? undefined}
      />

      <div className="mt-10 grid gap-8 lg:grid-cols-[1.4fr_1fr]">
        <Tarjeta>
          <h2 className="text-lg font-semibold">Esto es lo que te preguntaremos</h2>
          <p className="mt-2 text-sm leading-relaxed text-suave">
            Solo lo necesario para cotizar este ramo. Ten la información a mano
            y el proceso toma un par de minutos.
          </p>
          <ul className="mt-6 grid gap-x-8 gap-y-3 sm:grid-cols-2">
            {campos.map((campo) => (
              <li key={campo.nombre} className="flex items-start gap-2.5 text-sm">
                <span
                  aria-hidden="true"
                  className="mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full bg-tinta-500"
                />
                <span>
                  {campo.etiqueta}
                  {campo.requerido ? null : (
                    <span className="text-suave"> (opcional)</span>
                  )}
                </span>
              </li>
            ))}
          </ul>
        </Tarjeta>

        <Tarjeta className="h-fit">
          <h2 className="text-lg font-semibold">Empecemos</h2>
          <p className="mt-2 text-sm leading-relaxed text-suave">
            Escríbenos con estos datos y un asesor toma tu caso el mismo día
            hábil. Tu solicitud queda registrada y asignada, no se pierde en un
            chat.
          </p>
          <div className="mt-6 space-y-3">
            <Boton href={whatsappUrl(mensaje)} className="w-full">
              Cotizar por WhatsApp
            </Boton>
            <Boton href="/contacto" variante="secundario" className="w-full">
              Ver otras formas de contacto
            </Boton>
          </div>
          <p className="mt-5 text-xs leading-relaxed text-suave">
            Cotizar es gratis y no te compromete.
          </p>
        </Tarjeta>
      </div>

      <div className="mt-10">
        <Boton href="/cotizar" variante="fantasma" className="px-0">
          ← Ver todos los seguros
        </Boton>
      </div>
    </Seccion>
  );
}
