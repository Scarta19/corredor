import { NextResponse } from "next/server";

import { API_URL, tokenDeSesion } from "@/lib/sesion";

export async function PATCH(
  request: Request,
  { params }: { params: Promise<{ id: string }> },
) {
  const token = await tokenDeSesion();
  if (!token) {
    return NextResponse.json({ mensaje: "Sesión expirada." }, { status: 401 });
  }
  const { id } = await params;
  const respuesta = await fetch(`${API_URL}/api/v1/crm/renovaciones/${id}`, {
    method: "PATCH",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify(await request.json()),
    cache: "no-store",
  });
  return NextResponse.json(await respuesta.json(), { status: respuesta.status });
}
