import { IconoWhatsapp } from "@/components/iconos";
import { config, whatsappUrl } from "@/lib/config";

/**
 * The floating WhatsApp entry point from §4.
 *
 * It is a plain link, not a widget: no third-party script, no cookie, no
 * effect on the page's loading performance.
 */
export function BotonWhatsapp() {
  return (
    <a
      href={whatsappUrl(
        `Hola ${config.brand.corto}, quiero información sobre un seguro.`,
      )}
      target="_blank"
      rel="noopener noreferrer"
      className="fixed bottom-5 right-5 z-40 flex items-center gap-2 rounded-full bg-verde-600 px-4 py-3 text-sm font-semibold text-white shadow-lg transition-transform hover:scale-105 hover:bg-verde-500"
    >
      <IconoWhatsapp className="h-5 w-5" />
      <span className="hidden sm:inline">Escríbenos</span>
      <span className="sr-only sm:hidden">Escríbenos por WhatsApp</span>
    </a>
  );
}
