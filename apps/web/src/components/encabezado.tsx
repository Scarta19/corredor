"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useState } from "react";

import { Boton, Contenedor } from "@/components/ui";
import { IconoEscudo } from "@/components/iconos";
import { navegacion } from "@/content/site";
import { config } from "@/lib/config";

export function Encabezado() {
  const ruta = usePathname();
  const [abierto, setAbierto] = useState(false);
  // A menu that survives navigation traps the visitor on mobile, so every
  // item closes it on the way out. Doing it here rather than in an effect
  // keeps it to one render instead of a navigation followed by a correction.
  const cerrar = () => setAbierto(false);

  return (
    <header className="sticky top-0 z-40 border-b border-borde bg-fondo/85 backdrop-blur">
      <Contenedor>
        <div className="flex h-16 items-center justify-between gap-4">
          <Link href="/" className="flex items-center gap-2.5 font-semibold">
            <span className="grid h-9 w-9 place-items-center rounded-lg bg-tinta-700 text-white">
              <IconoEscudo className="h-5 w-5" />
            </span>
            <span className="hidden sm:inline">{config.brand.corto}</span>
          </Link>

          <nav aria-label="Principal" className="hidden lg:block">
            <ul className="flex items-center gap-1">
              {navegacion.map((enlace) => {
                const activo =
                  enlace.href === "/"
                    ? ruta === "/"
                    : ruta.startsWith(enlace.href);
                return (
                  <li key={enlace.href}>
                    <Link
                      href={enlace.href}
                      aria-current={activo ? "page" : undefined}
                      className={`rounded-lg px-3 py-2 text-sm font-medium transition-colors ${
                        activo
                          ? "text-tinta-700 dark:text-tinta-300"
                          : "text-suave hover:text-texto"
                      }`}
                    >
                      {enlace.etiqueta}
                    </Link>
                  </li>
                );
              })}
            </ul>
          </nav>

          <div className="flex items-center gap-2">
            <Boton href="/cotizar" className="hidden sm:inline-flex">
              Solicitar cotización
            </Boton>
            <button
              type="button"
              onClick={() => setAbierto((v) => !v)}
              aria-expanded={abierto}
              aria-controls="menu-movil"
              className="rounded-lg border border-borde p-2.5 lg:hidden"
            >
              <span className="sr-only">
                {abierto ? "Cerrar menú" : "Abrir menú"}
              </span>
              <svg
                className="h-5 w-5"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth={1.8}
                aria-hidden="true"
              >
                {abierto ? (
                  <path d="M6 6l12 12M18 6L6 18" strokeLinecap="round" />
                ) : (
                  <path d="M4 7h16M4 12h16M4 17h16" strokeLinecap="round" />
                )}
              </svg>
            </button>
          </div>
        </div>
      </Contenedor>

      {abierto ? (
        <div id="menu-movil" className="border-t border-borde lg:hidden">
          <Contenedor className="py-3">
            <ul className="flex flex-col">
              {navegacion.map((enlace) => (
                <li key={enlace.href}>
                  <Link
                    href={enlace.href}
                    onClick={cerrar}
                    className="block rounded-lg px-2 py-3 text-base font-medium hover:bg-piedra-100 dark:hover:bg-piedra-800"
                  >
                    {enlace.etiqueta}
                  </Link>
                </li>
              ))}
            </ul>
            <Boton href="/cotizar" onClick={cerrar} className="mt-3 w-full">
              Solicitar cotización
            </Boton>
          </Contenedor>
        </div>
      ) : null}
    </header>
  );
}
