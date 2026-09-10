import type { Metadata } from "next";

import { Cierre } from "@/components/cierre";
import { RejillaRamos } from "@/components/ramos";
import { Seccion, TituloSeccion } from "@/components/ui";
import { listarRamos } from "@/lib/api";

export const metadata: Metadata = {
  title: "Seguros",
  description:
    "Automóviles, hogar, vida, accidentes personales, cumplimiento, responsabilidad civil y pólizas empresariales.",
};

export default async function Seguros() {
  const [personas, empresas] = await Promise.all([
    listarRamos("persona"),
    listarRamos("empresa"),
  ]);

  return (
    <>
      <Seccion className="pb-0">
        <TituloSeccion
          ancla="Ramos"
          titulo="Todos los seguros que manejamos"
          descripcion="Elige uno y responde solo las preguntas de ese ramo. Si no encuentras lo que buscas, cuéntanoslo: trabajamos con varias aseguradoras y casi siempre hay una opción."
        />
      </Seccion>

      <Seccion>
        <h2 className="text-xl font-semibold">Para personas y familias</h2>
        <div className="mt-6">
          <RejillaRamos ramos={personas} />
        </div>

        <h2 className="mt-16 text-xl font-semibold">Para empresas</h2>
        <div className="mt-6">
          <RejillaRamos ramos={empresas} />
        </div>
      </Seccion>

      <Cierre />
    </>
  );
}
