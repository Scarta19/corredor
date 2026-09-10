import { Boton, Contenedor } from "@/components/ui";
import { config, whatsappUrl } from "@/lib/config";

/**
 * The closing band that every page ends with.
 *
 * §4 asks for a site that produces actions rather than information. A visitor
 * who reaches the bottom of any page should not have to scroll back up to do
 * something about it.
 */
export function Cierre({
  titulo = "¿Hablamos de lo que necesitas asegurar?",
  descripcion = "Cotizar no cuesta nada y no te compromete. En menos de un día hábil tienes una respuesta de una persona, no de un formulario.",
}: {
  titulo?: string;
  descripcion?: string;
}) {
  return (
    <section className="border-y border-borde bg-superficie">
      <Contenedor className="py-16 sm:py-20">
        <div className="mx-auto max-w-2xl text-center">
          <h2 className="text-3xl font-semibold tracking-tight sm:text-4xl">
            {titulo}
          </h2>
          <p className="mt-4 text-lg leading-relaxed text-suave">{descripcion}</p>
          <div className="mt-8 flex flex-wrap justify-center gap-3">
            <Boton href="/cotizar">Solicitar cotización</Boton>
            <Boton
              href={whatsappUrl(
                `Hola ${config.brand.corto}, quiero hablar con un asesor.`,
              )}
              variante="secundario"
            >
              Hablar con un asesor
            </Boton>
          </div>
        </div>
      </Contenedor>
    </section>
  );
}
