import type { Metadata } from "next";

import { RejillaAcciones } from "@/components/acciones";
import { IconoConversacion, IconoWhatsapp } from "@/components/iconos";
import { Boton, Seccion, Tarjeta, TituloSeccion } from "@/components/ui";
import { config, whatsappUrl } from "@/lib/config";

export const metadata: Metadata = {
  title: "Contacto",
  description:
    "Habla con un asesor por WhatsApp, teléfono o correo. Respondemos el mismo día hábil.",
};

const canales = [
  {
    titulo: "WhatsApp",
    detalle: "La vía más rápida. Escribes y te responde una persona.",
    accion: "Abrir WhatsApp",
    href: whatsappUrl(
      `Hola ${config.brand.corto}, quiero hablar con un asesor.`,
    ),
  },
  {
    titulo: "Teléfono",
    detalle: config.contacto.horario,
    accion: config.contacto.telefono,
    href: `tel:${config.contacto.telefono.replace(/\s/g, "")}`,
  },
  {
    titulo: "Correo",
    detalle: "Para documentos, pólizas vigentes y temas que requieren adjuntos.",
    accion: config.contacto.email,
    href: `mailto:${config.contacto.email}`,
  },
];

export default function Contacto() {
  return (
    <>
      <Seccion className="pb-0">
        <TituloSeccion
          ancla="Contacto"
          titulo="Hablas con una persona, no con un formulario"
          descripcion={`Estamos en ${config.contacto.ciudad}. ${config.contacto.horario}. Toda solicitud queda registrada y asignada a un asesor responsable — no se pierde en un chat.`}
        />
      </Seccion>

      <Seccion>
        <div className="grid gap-4 sm:grid-cols-3">
          {canales.map((canal) => (
            <Tarjeta key={canal.titulo} className="flex flex-col">
              <span className="grid h-10 w-10 place-items-center rounded-xl bg-tinta-50 text-tinta-700 dark:bg-tinta-950 dark:text-tinta-300">
                {canal.titulo === "WhatsApp" ? (
                  <IconoWhatsapp className="h-5 w-5" />
                ) : (
                  <IconoConversacion className="h-5 w-5" />
                )}
              </span>
              <h2 className="mt-4 text-lg font-semibold">{canal.titulo}</h2>
              <p className="mt-2 flex-1 text-sm leading-relaxed text-suave">
                {canal.detalle}
              </p>
              <Boton
                href={canal.href}
                variante="secundario"
                className="mt-5 w-full"
              >
                {canal.accion}
              </Boton>
            </Tarjeta>
          ))}
        </div>

        <div className="mt-14">
          <h2 className="text-xl font-semibold">O ve directo a lo que necesitas</h2>
          <div className="mt-6">
            <RejillaAcciones compacta />
          </div>
        </div>
      </Seccion>
    </>
  );
}
