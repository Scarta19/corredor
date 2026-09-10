import type { Metadata } from "next";
import { notFound } from "next/navigation";

import { FormularioCotizacion } from "@/components/formulario-cotizacion";
import { IconoWhatsapp } from "@/components/iconos";
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

const garantias = [
  "Cotizar no tiene costo y no te compromete.",
  "Comparamos varias aseguradoras, no una sola.",
  "Te responde un asesor con nombre propio, el mismo día hábil.",
  "Tus datos se usan solo para preparar tu cotización.",
];

export default async function CotizarRamo({ params }: Params) {
  const { codigo } = await params;
  const ramo = await obtenerRamo(codigo);
  if (!ramo) notFound();

  return (
    <Seccion>
      <TituloSeccion
        ancla={`Cotizar · ${ramo.nombre}`}
        titulo={`Cotización de ${ramo.nombre.toLowerCase()}`}
        descripcion={ramo.descripcion ?? undefined}
      />

      <div className="mt-10 grid gap-8 lg:grid-cols-[1.6fr_1fr] lg:items-start">
        <FormularioCotizacion ramo={ramo} />

        <div className="space-y-4 lg:sticky lg:top-24">
          <Tarjeta>
            <h2 className="text-base font-semibold">Qué puedes esperar</h2>
            <ul className="mt-4 space-y-3">
              {garantias.map((garantia) => (
                <li key={garantia} className="flex items-start gap-2.5 text-sm leading-relaxed">
                  <span
                    aria-hidden="true"
                    className="mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full bg-tinta-500"
                  />
                  <span className="text-suave">{garantia}</span>
                </li>
              ))}
            </ul>
          </Tarjeta>

          <Tarjeta>
            <h2 className="text-base font-semibold">¿Prefieres escribirnos?</h2>
            <p className="mt-2 text-sm leading-relaxed text-suave">
              También puedes cotizar por WhatsApp y un asesor te va guiando.
            </p>
            <Boton
              href={whatsappUrl(
                `Hola ${config.brand.corto}, quiero cotizar un seguro de ${ramo.nombre}.`,
              )}
              variante="secundario"
              className="mt-4 w-full"
            >
              <IconoWhatsapp className="h-4 w-4" />
              Cotizar por WhatsApp
            </Boton>
          </Tarjeta>
        </div>
      </div>

      <div className="mt-10">
        <Boton href="/cotizar" variante="fantasma" className="px-0">
          ← Ver todos los seguros
        </Boton>
      </div>
    </Seccion>
  );
}
