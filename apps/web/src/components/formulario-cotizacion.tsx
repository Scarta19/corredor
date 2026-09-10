"use client";

import { useMemo, useState } from "react";

import { Campo } from "@/components/campo-formulario";
import { Boton } from "@/components/ui";
import type { CampoFormulario, RamoDetalle } from "@/lib/api";
import { config, whatsappUrl } from "@/lib/config";

type Respuestas = Record<string, unknown>;

/**
 * Mirrors `campo_esta_activo` in the API.
 *
 * Both sides need this rule: the browser to decide what to show, the server
 * to decide what to accept. The server's copy is the one that is binding —
 * this one only exists so the visitor sees a coherent form.
 */
function campoEstaActivo(campo: CampoFormulario, respuestas: Respuestas): boolean {
  if (!campo.depende_de) return true;
  const valor = respuestas[campo.depende_de];
  if (valor === undefined || valor === null || valor === "") return false;
  const texto = typeof valor === "boolean" ? String(valor) : String(valor).trim();
  if (campo.depende_de_valores.length === 0) {
    return texto !== "" && texto !== "false";
  }
  return campo.depende_de_valores.includes(texto);
}

function estaVacio(valor: unknown): boolean {
  if (valor === undefined || valor === null) return true;
  if (typeof valor === "string") return valor.trim() === "";
  if (Array.isArray(valor)) return valor.length === 0;
  return false;
}

interface Creada {
  codigo: string;
  ramo: string;
  mensaje: string;
}

export function FormularioCotizacion({ ramo }: { ramo: RamoDetalle }) {
  const [respuestas, setRespuestas] = useState<Respuestas>({});
  const [errores, setErrores] = useState<Record<string, string>>({});
  const [aviso, setAviso] = useState<string | null>(null);
  const [enviando, setEnviando] = useState(false);
  const [creada, setCreada] = useState<Creada | null>(null);

  const campos = useMemo(
    () =>
      [...ramo.formulario.campos].sort(
        (a, b) => a.orden - b.orden || a.nombre.localeCompare(b.nombre),
      ),
    [ramo],
  );

  const visibles = campos.filter((campo) => campoEstaActivo(campo, respuestas));

  function actualizar(campo: CampoFormulario, valor: unknown) {
    setRespuestas((previas) => {
      const siguientes = { ...previas, [campo.nombre]: valor };
      // Answers to fields that no longer apply must not be submitted; the
      // API rejects them, and rightly so.
      for (const otro of campos) {
        if (otro.depende_de && !campoEstaActivo(otro, siguientes)) {
          delete siguientes[otro.nombre];
        }
      }
      return siguientes;
    });
    setErrores((previos) => {
      if (!(campo.nombre in previos)) return previos;
      const resto = { ...previos };
      delete resto[campo.nombre];
      return resto;
    });
  }

  async function enviar(evento: React.FormEvent) {
    evento.preventDefault();
    setAviso(null);

    const faltantes: Record<string, string> = {};
    for (const campo of visibles) {
      if (campo.requerido && estaVacio(respuestas[campo.nombre])) {
        faltantes[campo.nombre] = "Este campo es obligatorio.";
      }
    }
    if (Object.keys(faltantes).length > 0) {
      setErrores(faltantes);
      document
        .getElementById(`campo-${Object.keys(faltantes)[0]}`)
        ?.focus({ preventScroll: false });
      return;
    }

    setEnviando(true);
    try {
      const respuesta = await fetch("/api/solicitudes", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ ramo: ramo.codigo, respuestas }),
      });
      const datos = await respuesta.json();

      if (respuesta.ok) {
        setCreada(datos as Creada);
        return;
      }
      // The API validates the same rules again and is the authority; surface
      // its per-field messages verbatim.
      const delServidor = datos?.contexto?.errores;
      if (delServidor && typeof delServidor === "object") {
        setErrores(delServidor as Record<string, string>);
        setAviso("Revisa los campos marcados.");
      } else {
        setAviso(datos?.mensaje ?? "No pudimos registrar tu solicitud.");
      }
    } catch {
      setAviso(
        "No pudimos conectarnos. Revisa tu conexión o escríbenos por WhatsApp.",
      );
    } finally {
      setEnviando(false);
    }
  }

  if (creada) {
    return <Confirmacion creada={creada} />;
  }

  return (
    <form onSubmit={enviar} noValidate className="rounded-2xl border border-borde bg-superficie p-6 sm:p-8">
      <h2 className="text-lg font-semibold">Cuéntanos lo necesario</h2>
      <p className="mt-1.5 text-sm text-suave">
        Solo las preguntas de este ramo. Toma un par de minutos.
      </p>

      {aviso ? (
        <p
          role="alert"
          className="mt-5 rounded-xl border border-red-300 bg-red-50 px-4 py-3 text-sm text-red-800 dark:border-red-900 dark:bg-red-950 dark:text-red-200"
        >
          {aviso}
        </p>
      ) : null}

      <div className="mt-6 grid gap-5 sm:grid-cols-2">
        {visibles.map((campo) => (
          <Campo
            key={campo.nombre}
            campo={campo}
            valor={respuestas[campo.nombre]}
            error={errores[campo.nombre]}
            onChange={(valor) => actualizar(campo, valor)}
          />
        ))}
      </div>

      <div className="mt-8 flex flex-wrap items-center gap-4">
        <button
          type="submit"
          disabled={enviando}
          className="inline-flex items-center justify-center rounded-xl bg-tinta-700 px-6 py-3.5 text-sm font-semibold text-white transition-colors hover:bg-tinta-800 disabled:cursor-not-allowed disabled:opacity-60"
        >
          {enviando ? "Enviando…" : "Enviar solicitud"}
        </button>
        <p className="text-xs text-suave">
          Cotizar es gratis y no te compromete.
        </p>
      </div>
    </form>
  );
}

function Confirmacion({ creada }: { creada: Creada }) {
  return (
    <div
      role="status"
      className="rounded-2xl border border-borde bg-superficie p-8 text-center"
    >
      <span className="mx-auto grid h-14 w-14 place-items-center rounded-full bg-verde-500/10 text-verde-600">
        <svg className="h-7 w-7" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2} aria-hidden="true">
          <path d="m5 13 4 4L19 7" strokeLinecap="round" strokeLinejoin="round" />
        </svg>
      </span>

      <h2 className="mt-5 text-2xl font-semibold">
        Solicitud recibida correctamente
      </h2>
      <p className="mx-auto mt-3 max-w-md text-sm leading-relaxed text-suave">
        {creada.mensaje}
      </p>

      <div className="mx-auto mt-6 inline-flex flex-col items-center rounded-xl border border-borde px-6 py-4">
        <span className="text-xs uppercase tracking-widest text-suave">
          Tu radicado
        </span>
        <span className="mt-1 font-mono text-2xl font-semibold tracking-tight">
          {creada.codigo}
        </span>
      </div>
      <p className="mx-auto mt-4 max-w-md text-xs leading-relaxed text-suave">
        Guarda este número: con él podemos ubicar tu solicitud de inmediato.
      </p>

      <div className="mt-7 flex flex-wrap justify-center gap-3">
        <Boton
          href={whatsappUrl(
            `Hola ${config.brand.corto}, acabo de enviar la solicitud ${creada.codigo} de ${creada.ramo}.`,
          )}
        >
          Continuar por WhatsApp
        </Boton>
        <Boton href="/seguros" variante="secundario">
          Ver otros seguros
        </Boton>
      </div>
    </div>
  );
}
