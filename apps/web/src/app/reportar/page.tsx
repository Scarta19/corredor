import type { Metadata } from "next";

import { Boton, Seccion, Tarjeta, TituloSeccion } from "@/components/ui";
import { config, whatsappUrl } from "@/lib/config";

export const metadata: Metadata = {
  title: "Reportar una solicitud",
  description:
    "Siniestros, cambios en tu póliza, certificados y cualquier novedad. Te guiamos en el trámite ante la aseguradora.",
};

const tipos = [
  {
    titulo: "Siniestro",
    detalle:
      "Un choque, un robo, un daño. Repórtalo cuanto antes: casi todas las pólizas tienen plazos para avisar, y el nuestro es acompañarte en el trámite.",
    mensaje: "quiero reportar un siniestro",
  },
  {
    titulo: "Cambio en mi póliza",
    detalle:
      "Cambiaste de vehículo, de dirección, de beneficiarios o de valor asegurado. Tramitamos la modificación con la aseguradora.",
    mensaje: "necesito modificar mi póliza",
  },
  {
    titulo: "Certificados y documentos",
    detalle:
      "Copia de la póliza, certificado de cobertura o el soporte que te esté pidiendo un tercero.",
    mensaje: "necesito un certificado de mi póliza",
  },
  {
    titulo: "Otra novedad",
    detalle:
      "Dudas de cobertura, problemas con un pago o cualquier cosa que no encaje en las anteriores.",
    mensaje: "tengo una novedad con mi póliza",
  },
];

export default function Reportar() {
  return (
    <Seccion>
      <TituloSeccion
        ancla="Reportar una solicitud"
        titulo="¿Qué necesitas reportar?"
        descripcion="El momento que importa de un seguro es cuando toca usarlo. Cuéntanos qué pasó y te decimos exactamente qué documentos reunir y en qué orden."
      />

      <div className="mt-10 grid gap-4 sm:grid-cols-2">
        {tipos.map((tipo) => (
          <Tarjeta key={tipo.titulo} className="flex flex-col">
            <h2 className="text-lg font-semibold">{tipo.titulo}</h2>
            <p className="mt-2 flex-1 text-sm leading-relaxed text-suave">
              {tipo.detalle}
            </p>
            <Boton
              href={whatsappUrl(
                `Hola ${config.brand.corto}, ${tipo.mensaje}.`,
              )}
              variante="secundario"
              className="mt-5 w-full"
            >
              Reportar por WhatsApp
            </Boton>
          </Tarjeta>
        ))}
      </div>

      <Tarjeta className="mt-10 border-tinta-200 bg-tinta-50 dark:border-tinta-900 dark:bg-tinta-950">
        <h2 className="font-semibold">Si es una emergencia</h2>
        <p className="mt-2 text-sm leading-relaxed text-suave">
          Llama primero a la línea de asistencia de tu aseguradora, que opera
          24 horas — grúa, ambulancia y acompañamiento en vía. Luego repórtanos
          la novedad y seguimos nosotros con el trámite.
        </p>
        <Boton
          href={`tel:${config.contacto.telefono.replace(/\s/g, "")}`}
          variante="secundario"
          className="mt-5"
        >
          Llamar a {config.brand.corto}: {config.contacto.telefono}
        </Boton>
      </Tarjeta>
    </Seccion>
  );
}
