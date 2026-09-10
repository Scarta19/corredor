import type { Metadata } from "next";

import { PaginaSegmento } from "@/components/segmento";
import { listarRamos } from "@/lib/api";

export const metadata: Metadata = {
  title: "Seguros para empresas",
  description:
    "Cumplimiento, responsabilidad civil, pólizas empresariales y vida grupo, incluidas las garantías que exigen las entidades contratantes.",
};

const situaciones = [
  {
    titulo: "Te adjudicaron un contrato",
    detalle:
      "Casi toda licitación exige pólizas de cumplimiento y responsabilidad civil, con plazos cortos. Conocemos los requisitos y los tiempos de expedición.",
  },
  {
    titulo: "Vas a presentarte a una licitación",
    detalle:
      "La garantía de seriedad de la oferta se pide antes de adjudicar. Mejor tenerla lista que perder el proceso por un trámite.",
  },
  {
    titulo: "Creció tu operación",
    detalle:
      "Maquinaria, inventario o sedes nuevas cambian tu exposición. Revisamos si los valores asegurados siguen teniendo sentido.",
  },
  {
    titulo: "Contrataste personal",
    detalle:
      "Vida grupo y accidentes personales son de las prestaciones que más se valoran y de las menos costosas de otorgar.",
  },
  {
    titulo: "Tienes flota o vehículos de trabajo",
    detalle:
      "Una flota se negocia distinto a una póliza individual. Ahí es donde un intermediario consigue condiciones que no están en mostrador.",
  },
  {
    titulo: "Manejas varias pólizas dispersas",
    detalle:
      "Vencimientos en fechas distintas y con varios contactos. Las centralizamos y unificamos el control de renovaciones.",
  },
];

export default async function Empresas() {
  const ramos = await listarRamos("empresa");

  return (
    <PaginaSegmento
      ancla="Empresas"
      titulo="Cobertura que no frena la operación"
      descripcion="Desde la garantía que exige una entidad contratante hasta la protección de tus activos y tu equipo. Entendemos los plazos con los que trabaja una empresa."
      situaciones={situaciones}
      ramos={ramos}
      cierre="Cuéntanos qué contrato o qué riesgo necesitas cubrir y te decimos qué pólizas aplican y en cuánto tiempo se expiden."
    />
  );
}
