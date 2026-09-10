import type { Metadata } from "next";
import { redirect } from "next/navigation";

import { FormularioAcceso } from "@/components/formulario-acceso";
import { tokenDeSesion } from "@/lib/sesion";

export const metadata: Metadata = { title: "Ingresar" };

export default async function Login() {
  // Someone already signed in has no business on this page.
  if (await tokenDeSesion()) redirect("/");

  return (
    <main className="grid min-h-dvh place-items-center px-5 py-12">
      <div className="w-full max-w-sm">
        <p className="text-xs uppercase tracking-widest text-suave">Corredor</p>
        <h1 className="mt-1 text-2xl font-semibold tracking-tight">
          Ingresa al CRM
        </h1>
        <p className="mt-2 text-sm text-suave">
          Gestión de solicitudes, clientes y renovaciones de tu agencia.
        </p>
        <FormularioAcceso />
      </div>
    </main>
  );
}
