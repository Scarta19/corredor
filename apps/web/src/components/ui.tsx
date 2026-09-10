/**
 * The small set of primitives every page is built from.
 *
 * Deliberately few: one container, one section wrapper, one button in two
 * weights. A marketing site that grows a component per screen stops being
 * editable by the people who own the copy.
 */

import Link from "next/link";
import type { Route } from "next";
import type { ReactNode } from "react";

export function Contenedor({
  children,
  className = "",
}: {
  children: ReactNode;
  className?: string;
}) {
  return (
    <div className={`mx-auto w-full max-w-6xl px-5 sm:px-8 ${className}`}>
      {children}
    </div>
  );
}

export function Seccion({
  children,
  className = "",
  id,
}: {
  children: ReactNode;
  className?: string;
  id?: string;
}) {
  return (
    <section id={id} className={`py-16 sm:py-24 ${className}`}>
      <Contenedor>{children}</Contenedor>
    </section>
  );
}

export function TituloSeccion({
  ancla,
  titulo,
  descripcion,
  centrado = false,
}: {
  ancla?: string;
  titulo: string;
  descripcion?: string;
  centrado?: boolean;
}) {
  return (
    <div className={`max-w-2xl ${centrado ? "mx-auto text-center" : ""}`}>
      {ancla ? (
        <p className="text-sm font-semibold uppercase tracking-widest text-tinta-600 dark:text-tinta-400">
          {ancla}
        </p>
      ) : null}
      <h2 className="mt-2 text-3xl font-semibold tracking-tight text-texto sm:text-4xl">
        {titulo}
      </h2>
      {descripcion ? (
        <p className="mt-4 text-lg leading-relaxed text-suave">{descripcion}</p>
      ) : null}
    </div>
  );
}

const estilos = {
  primario:
    "bg-tinta-700 text-white hover:bg-tinta-800 focus-visible:outline-tinta-700 shadow-sm",
  secundario:
    "border border-borde bg-superficie text-texto hover:border-tinta-400 hover:text-tinta-700 dark:hover:text-tinta-300",
  fantasma: "text-tinta-700 hover:text-tinta-900 dark:text-tinta-300",
} as const;

export function Boton({
  href,
  children,
  variante = "primario",
  className = "",
  onClick,
}: {
  href: Route | string;
  children: ReactNode;
  variante?: keyof typeof estilos;
  className?: string;
  onClick?: () => void;
}) {
  const clases = `inline-flex items-center justify-center gap-2 rounded-xl px-5 py-3 text-sm font-semibold transition-colors ${estilos[variante]} ${className}`;
  const externo = href.toString().startsWith("http");

  if (externo) {
    return (
      <a
        href={href.toString()}
        className={clases}
        onClick={onClick}
        target="_blank"
        rel="noopener noreferrer"
      >
        {children}
      </a>
    );
  }
  return (
    <Link href={href as Route} className={clases} onClick={onClick}>
      {children}
    </Link>
  );
}

export function Tarjeta({
  children,
  className = "",
}: {
  children: ReactNode;
  className?: string;
}) {
  return (
    <div
      className={`rounded-2xl border border-borde bg-superficie p-6 ${className}`}
    >
      {children}
    </div>
  );
}
