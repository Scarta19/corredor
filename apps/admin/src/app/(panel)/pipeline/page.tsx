import { Encabezado } from "@/components/ui";
import { Tablero } from "@/components/tablero";
import { apiProtegido } from "@/lib/sesion";
import type { ColumnaPipeline } from "@/lib/tipos";

export const metadata = { title: "Pipeline" };

export default async function Pipeline() {
  const columnas = await apiProtegido<ColumnaPipeline[]>("/crm/pipeline");
  const abiertas = columnas
    .filter((c) => c.etapa !== "ganado" && c.etapa !== "perdido")
    .reduce((total, c) => total + c.total, 0);

  return (
    <>
      <Encabezado
        titulo="Pipeline"
        descripcion={`${abiertas} oportunidad(es) abiertas. Cada movimiento queda registrado en el historial.`}
      />
      <Tablero columnas={columnas} />
    </>
  );
}
