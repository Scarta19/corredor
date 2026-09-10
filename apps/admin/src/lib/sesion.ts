/**
 * Session handling for the CRM.
 *
 * The access token lives in an httpOnly cookie, never in `localStorage`.
 * Script running on the page cannot read it, which is the whole point: this
 * application shows an entire brokerage's client base, and an XSS that can
 * lift the token can lift the book of business with it.
 *
 * Because the cookie is httpOnly, every API call is made from the server —
 * pages are Server Components and mutations go through route handlers. The
 * browser never talks to the platform API directly.
 */

import { cookies } from "next/headers";
import { redirect } from "next/navigation";

import type { UsuarioSesion } from "./tipos";

export const COOKIE_SESION = "corredor_sesion";

/** Server-side only: the platform API is never addressed from the browser. */
export const API_URL = process.env.API_URL ?? "http://localhost:8000";

export class SesionExpirada extends Error {}

export async function tokenDeSesion(): Promise<string | null> {
  const almacen = await cookies();
  return almacen.get(COOKIE_SESION)?.value ?? null;
}

/**
 * Call the platform API as the signed-in user.
 *
 * A 401 means the token expired or the account was deactivated; the caller is
 * sent back to the login screen rather than shown a broken page.
 */
export async function api<T>(
  ruta: string,
  opciones: RequestInit = {},
): Promise<T> {
  const token = await tokenDeSesion();
  if (!token) throw new SesionExpirada();

  const respuesta = await fetch(`${API_URL}/api/v1${ruta}`, {
    ...opciones,
    headers: {
      ...opciones.headers,
      Authorization: `Bearer ${token}`,
    },
    cache: "no-store",
  });

  if (respuesta.status === 401) throw new SesionExpirada();
  if (!respuesta.ok) {
    throw new Error(`API ${respuesta.status} en ${ruta}: ${await respuesta.text()}`);
  }
  return (await respuesta.json()) as T;
}

/** Fetch for a page that requires a session, redirecting when there is none. */
export async function apiProtegido<T>(ruta: string): Promise<T> {
  try {
    return await api<T>(ruta);
  } catch (error) {
    if (error instanceof SesionExpirada) redirect("/login");
    throw error;
  }
}

export async function usuarioActual(): Promise<UsuarioSesion> {
  return apiProtegido<UsuarioSesion>("/auth/yo");
}
