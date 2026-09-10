/**
 * Same-origin proxy for quote submissions.
 *
 * The browser posts here rather than to the platform API directly. That keeps
 * the tenant header server-controlled (a visitor cannot submit into another
 * brokerage by editing a request), keeps the internal API URL out of the
 * client bundle, and removes the need for CORS on a public endpoint. It is
 * also the natural place to add rate limiting.
 */

import { NextResponse } from "next/server";

import { config } from "@/lib/config";

export async function POST(request: Request) {
  let cuerpo: unknown;
  try {
    cuerpo = await request.json();
  } catch {
    return NextResponse.json(
      { codigo: "json_invalido", mensaje: "No pudimos leer la solicitud." },
      { status: 400 },
    );
  }

  try {
    const respuesta = await fetch(`${config.apiUrl}/api/v1/solicitudes`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-Tenant": config.tenant,
      },
      body: JSON.stringify(cuerpo),
      cache: "no-store",
    });

    const datos = await respuesta.json();
    return NextResponse.json(datos, { status: respuesta.status });
  } catch {
    // The API is unreachable. Say so plainly and point at WhatsApp, rather
    // than leaving the visitor staring at a spinner.
    return NextResponse.json(
      {
        codigo: "servicio_no_disponible",
        mensaje:
          "No pudimos registrar tu solicitud en este momento. Escríbenos por WhatsApp y la tomamos de una vez.",
      },
      { status: 503 },
    );
  }
}
