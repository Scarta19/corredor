import type { Metadata } from "next";

import { RejillaRamos } from "@/components/ramos";
import { Seccion, TituloSeccion } from "@/components/ui";
import { listarRamos } from "@/lib/api";

export const metadata: Metadata = {
  title: "Solicitar cotización",
  description:
    "Elige el seguro que necesitas y responde solo las preguntas de ese ramo. Cotizar es gratis y no compromete.",
};

export default async function Cotizar() {
  const ramos = await listarRamos();

  return (
    <Seccion>
      <TituloSeccion
        ancla="Solicitar cotización"
        titulo="¿Qué seguro necesitas?"
        descripcion="Elige una opción. Según lo que escojas te preguntaremos únicamente lo necesario para cotizar ese seguro — nada de formularios genéricos con veinte campos."
      />
      <div className="mt-10">
        <RejillaRamos ramos={ramos} />
      </div>
      <p className="mt-8 max-w-2xl text-sm leading-relaxed text-suave">
        Cotizar no tiene costo y no te compromete a nada. Como intermediarios,
        nuestra remuneración la paga la aseguradora: el precio de la póliza es
        el mismo que tomándola directamente.
      </p>
    </Seccion>
  );
}
