import Link from "next/link";

import { Contenedor } from "@/components/ui";
import { IconoEscudo } from "@/components/iconos";
import { acciones, navegacion } from "@/content/site";
import { config } from "@/lib/config";

export function PieDePagina() {
  const anio = new Date().getFullYear();

  return (
    <footer className="border-t border-borde bg-superficie">
      <Contenedor className="py-14">
        <div className="grid gap-10 sm:grid-cols-2 lg:grid-cols-4">
          <div className="lg:col-span-2">
            <div className="flex items-center gap-2.5 font-semibold">
              <span className="grid h-9 w-9 place-items-center rounded-lg bg-tinta-700 text-white">
                <IconoEscudo className="h-5 w-5" />
              </span>
              {config.brand.nombre}
            </div>
            <p className="mt-4 max-w-sm text-sm leading-relaxed text-suave">
              Agencia de seguros para personas y empresas. Comparamos el
              mercado, te asignamos un asesor responsable y controlamos tus
              renovaciones.
            </p>
          </div>

          <nav aria-label="Secciones">
            <h2 className="text-sm font-semibold">Navegación</h2>
            <ul className="mt-4 space-y-2.5 text-sm text-suave">
              {navegacion.map((enlace) => (
                <li key={enlace.href}>
                  <Link href={enlace.href} className="hover:text-texto">
                    {enlace.etiqueta}
                  </Link>
                </li>
              ))}
            </ul>
          </nav>

          <div>
            <h2 className="text-sm font-semibold">Contacto</h2>
            <ul className="mt-4 space-y-2.5 text-sm text-suave">
              <li>
                <a href={`tel:${config.contacto.telefono.replace(/\s/g, "")}`} className="hover:text-texto">
                  {config.contacto.telefono}
                </a>
              </li>
              <li>
                <a href={`mailto:${config.contacto.email}`} className="hover:text-texto">
                  {config.contacto.email}
                </a>
              </li>
              <li>{config.contacto.ciudad}</li>
              <li>{config.contacto.horario}</li>
            </ul>
          </div>
        </div>

        <div className="mt-10 flex flex-wrap gap-x-6 gap-y-2 border-t border-borde pt-6 text-sm">
          {acciones.map((accion) => (
            <Link
              key={accion.href}
              href={accion.href}
              className="font-medium text-tinta-700 hover:text-tinta-900 dark:text-tinta-300"
            >
              {accion.etiqueta}
            </Link>
          ))}
        </div>

        <p className="mt-6 text-xs text-suave">
          © {anio} {config.brand.nombre}. Los seguros son intermediados; la
          cobertura la otorga la aseguradora emisora de cada póliza, sujeta a
          sus términos y condiciones.
        </p>
      </Contenedor>
    </footer>
  );
}
