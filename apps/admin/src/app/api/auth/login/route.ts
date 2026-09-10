/**
 * Exchange credentials for a session cookie.
 *
 * The token never reaches page JavaScript: this handler receives the password,
 * calls the platform API server-side, and stores the result in an httpOnly
 * cookie the browser cannot read.
 */

import { NextResponse } from "next/server";

import { API_URL, COOKIE_SESION } from "@/lib/sesion";

export async function POST(request: Request) {
  const { email, clave } = (await request.json()) as {
    email?: string;
    clave?: string;
  };

  if (!email || !clave) {
    return NextResponse.json(
      { mensaje: "Escribe tu correo y tu contraseña." },
      { status: 400 },
    );
  }

  let datos: { access_token?: string; expires_in?: number; mensaje?: string };
  try {
    const respuesta = await fetch(`${API_URL}/api/v1/auth/login`, {
      method: "POST",
      headers: { "Content-Type": "application/x-www-form-urlencoded" },
      body: new URLSearchParams({ username: email, password: clave }),
      cache: "no-store",
    });
    datos = await respuesta.json();
    if (!respuesta.ok) {
      return NextResponse.json(
        { mensaje: datos.mensaje ?? "Correo o contraseña incorrectos." },
        { status: respuesta.status },
      );
    }
  } catch {
    return NextResponse.json(
      { mensaje: "No pudimos conectarnos con el servidor. Intenta de nuevo." },
      { status: 503 },
    );
  }

  const respuesta = NextResponse.json({ ok: true });
  respuesta.cookies.set({
    name: COOKIE_SESION,
    value: datos.access_token ?? "",
    httpOnly: true,
    sameSite: "lax",
    // Cookies are only sent over TLS outside local development.
    secure: process.env.NODE_ENV === "production",
    path: "/",
    maxAge: datos.expires_in ?? 60 * 60 * 12,
  });
  return respuesta;
}
