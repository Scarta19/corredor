import type { Metadata } from "next";

import { Boton, Seccion, Tarjeta, TituloSeccion } from "@/components/ui";
import { config, whatsappUrl } from "@/lib/config";

export const metadata: Metadata = {
  title: "Renovar mi póliza",
  description:
    "¿Tu póliza está por vencer? Revisamos si sigue siendo la mejor opción y gestionamos la renovación por ti.",
};

const pasos = [
  {
    titulo: "Nos dices qué póliza es",
    detalle:
      "Número de póliza y aseguradora, o simplemente el ramo y la fecha de vencimiento. Con eso arrancamos.",
  },
  {
    titulo: "Revisamos si sigue conviniéndote",
    detalle:
      "Comparamos tu renovación con lo que ofrece hoy el mercado. A veces la respuesta es quedarte donde estás, y también te lo decimos.",
  },
  {
    titulo: "Gestionamos el trámite",
    detalle:
      "Nos encargamos de la expedición y te confirmamos antes del vencimiento. Sin períodos descubiertos.",
  },
];

export default function Renovar() {
  return (
    <Seccion>
      <TituloSeccion
        ancla="Renovar mi póliza"
        titulo="Que no se te venza sin darte cuenta"
        descripcion="Un vencimiento que pasa desapercibido deja un período sin cobertura y, en muchos ramos, hace perder la antigüedad acumulada. Nosotros llevamos ese control."
      />

      <div className="mt-10 grid gap-8 lg:grid-cols-[1.4fr_1fr]">
        <div>
          <ol className="space-y-6">
            {pasos.map((paso, indice) => (
              <li key={paso.titulo} className="flex gap-4">
                <span className="grid h-9 w-9 shrink-0 place-items-center rounded-full bg-tinta-700 text-sm font-semibold text-white">
                  {indice + 1}
                </span>
                <div>
                  <h2 className="font-semibold">{paso.titulo}</h2>
                  <p className="mt-1.5 text-sm leading-relaxed text-suave">
                    {paso.detalle}
                  </p>
                </div>
              </li>
            ))}
          </ol>

          <Tarjeta className="mt-10 border-tinta-200 bg-tinta-50 dark:border-tinta-900 dark:bg-tinta-950">
            <h2 className="font-semibold">¿Tu póliza está con otro intermediario?</h2>
            <p className="mt-2 text-sm leading-relaxed text-suave">
              Puedes trasladar la intermediación sin cambiar de aseguradora y
              sin perder antigüedad. El trámite lo hacemos nosotros.
            </p>
          </Tarjeta>
        </div>

        <Tarjeta className="h-fit">
          <h2 className="text-lg font-semibold">Escríbenos</h2>
          <p className="mt-2 text-sm leading-relaxed text-suave">
            Cuanto antes lo veamos, más opciones tenemos. Lo ideal es entre 30 y
            60 días antes del vencimiento.
          </p>
          <div className="mt-6 space-y-3">
            <Boton
              href={whatsappUrl(
                `Hola ${config.brand.corto}, quiero renovar mi póliza.`,
              )}
              className="w-full"
            >
              Renovar por WhatsApp
            </Boton>
            <Boton href="/contacto" variante="secundario" className="w-full">
              Otras formas de contacto
            </Boton>
          </div>
        </Tarjeta>
      </div>
    </Seccion>
  );
}
