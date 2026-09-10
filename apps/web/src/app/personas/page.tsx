import type { Metadata } from "next";

import { PaginaSegmento } from "@/components/segmento";
import { listarRamos } from "@/lib/api";

export const metadata: Metadata = {
  title: "Seguros para personas",
  description:
    "Automóviles, hogar, vida y accidentes personales. Cotizamos con varias aseguradoras y te acompañamos en el siniestro.",
};

const situaciones = [
  {
    titulo: "Compraste vehículo",
    detalle:
      "El concesionario te ofrece una póliza y no sabes si es la mejor. Podemos comparar esa misma cobertura con otras aseguradoras antes de que firmes.",
  },
  {
    titulo: "Te llegó la renovación con un aumento",
    detalle:
      "Un alza fuerte no siempre se justifica. Revisamos qué cambió y qué ofrece el resto del mercado por la misma cobertura.",
  },
  {
    titulo: "Tienes personas a cargo",
    detalle:
      "Un seguro de vida es la forma más barata de que un imprevisto tuyo no se convierta en un problema económico para tu familia.",
  },
  {
    titulo: "Compraste o remodelaste vivienda",
    detalle:
      "Incendio, terremoto y sustracción cuestan bastante menos de lo que la mayoría supone frente al valor de lo que protegen.",
  },
  {
    titulo: "Trabajas por tu cuenta",
    detalle:
      "Sin incapacidad pagada por un empleador, un accidente son semanas sin ingresos. Accidentes personales cubre justamente eso.",
  },
  {
    titulo: "Ya tienes póliza y nadie te atiende",
    detalle:
      "Puedes trasladar la intermediación sin cambiar de aseguradora ni perder antigüedad. Nosotros hacemos el trámite.",
  },
];

export default async function Personas() {
  const ramos = await listarRamos("persona");

  return (
    <PaginaSegmento
      ancla="Personas y familias"
      titulo="Proteger lo que te costó conseguir"
      descripcion="Tu carro, tu casa, tu capacidad de generar ingresos y la tranquilidad de quienes dependen de ti. Te ayudamos a cubrir lo que de verdad importa, sin venderte lo que no necesitas."
      situaciones={situaciones}
      ramos={ramos}
      cierre="Cuéntanos qué quieres asegurar y te enviamos opciones comparadas. Cotizar es gratis y no te compromete."
    />
  );
}
