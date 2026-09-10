"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";

export function FormularioAcceso() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [clave, setClave] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [enviando, setEnviando] = useState(false);

  async function enviar(evento: React.FormEvent) {
    evento.preventDefault();
    setError(null);
    setEnviando(true);
    try {
      const respuesta = await fetch("/api/auth/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, clave }),
      });
      if (respuesta.ok) {
        router.replace("/");
        router.refresh();
        return;
      }
      const datos = await respuesta.json();
      setError(datos.mensaje ?? "No pudimos iniciar sesión.");
    } catch {
      setError("No pudimos conectarnos. Revisa tu conexión.");
    } finally {
      setEnviando(false);
    }
  }

  const campo =
    "mt-1.5 w-full rounded-lg border border-borde bg-superficie px-3.5 py-2.5 text-sm outline-none focus:border-tinta-500";

  return (
    <form onSubmit={enviar} className="mt-8 space-y-4">
      {error ? (
        <p
          role="alert"
          className="rounded-lg border border-red-300 bg-red-50 px-3.5 py-2.5 text-sm text-red-800 dark:border-red-900 dark:bg-red-950 dark:text-red-200"
        >
          {error}
        </p>
      ) : null}

      <div>
        <label htmlFor="email" className="text-sm font-medium">
          Correo
        </label>
        <input
          id="email"
          type="email"
          autoComplete="username"
          required
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          className={campo}
        />
      </div>

      <div>
        <label htmlFor="clave" className="text-sm font-medium">
          Contraseña
        </label>
        <input
          id="clave"
          type="password"
          autoComplete="current-password"
          required
          value={clave}
          onChange={(e) => setClave(e.target.value)}
          className={campo}
        />
      </div>

      <button
        type="submit"
        disabled={enviando}
        className="w-full rounded-lg bg-tinta-700 px-4 py-2.5 text-sm font-semibold text-white transition-colors hover:bg-tinta-800 disabled:opacity-60"
      >
        {enviando ? "Ingresando…" : "Ingresar"}
      </button>
    </form>
  );
}
