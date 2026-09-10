"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import type { Route } from "next";

import type { UsuarioSesion } from "@/lib/tipos";

const enlaces: { href: Route; etiqueta: string }[] = [
  { href: "/", etiqueta: "Resumen" },
  { href: "/solicitudes", etiqueta: "Solicitudes" },
  { href: "/pipeline", etiqueta: "Pipeline" },
  { href: "/renovaciones", etiqueta: "Renovaciones" },
  { href: "/clientes", etiqueta: "Clientes" },
];

export function BarraLateral({ usuario }: { usuario: UsuarioSesion }) {
  const ruta = usePathname();
  const router = useRouter();

  async function salir() {
    await fetch("/api/auth/logout", { method: "POST" });
    router.replace("/login");
    router.refresh();
  }

  return (
    <aside className="flex w-full shrink-0 flex-col border-b border-borde bg-superficie lg:h-dvh lg:w-64 lg:border-b-0 lg:border-r">
      <div className="border-borde px-5 py-4 lg:border-b">
        <p className="text-xs uppercase tracking-widest text-suave">Corredor</p>
        <p className="mt-0.5 truncate font-semibold">{usuario.tenant}</p>
      </div>

      <nav className="flex gap-1 overflow-x-auto px-3 py-3 lg:flex-1 lg:flex-col lg:overflow-visible">
        {enlaces.map((enlace) => {
          const activo =
            enlace.href === "/" ? ruta === "/" : ruta.startsWith(enlace.href);
          return (
            <Link
              key={enlace.href}
              href={enlace.href}
              aria-current={activo ? "page" : undefined}
              className={`whitespace-nowrap rounded-lg px-3 py-2 text-sm font-medium transition-colors ${
                activo
                  ? "bg-tinta-50 text-tinta-800 dark:bg-tinta-950 dark:text-tinta-200"
                  : "text-suave hover:bg-piedra-100 hover:text-texto dark:hover:bg-piedra-800"
              }`}
            >
              {enlace.etiqueta}
            </Link>
          );
        })}
      </nav>

      <div className="border-borde px-5 py-4 lg:border-t">
        <p className="truncate text-sm font-medium">{usuario.nombre}</p>
        <p className="truncate text-xs capitalize text-suave">{usuario.rol}</p>
        <button
          type="button"
          onClick={salir}
          className="mt-3 text-xs font-medium text-tinta-700 hover:underline dark:text-tinta-300"
        >
          Cerrar sesión
        </button>
      </div>
    </aside>
  );
}
