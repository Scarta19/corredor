"use client";

import type { CampoFormulario } from "@/lib/api";

/**
 * One field of a runtime-defined form.
 *
 * The `tipo` decides the control. Everything else — label, options,
 * requiredness — comes straight from the API, so a ramo added next month
 * renders correctly without this file changing.
 */

const claseControl =
  "w-full rounded-xl border border-borde bg-superficie px-4 py-3 text-base outline-none transition-colors focus:border-tinta-500";

export function Campo({
  campo,
  valor,
  error,
  onChange,
}: {
  campo: CampoFormulario;
  valor: unknown;
  error?: string;
  onChange: (valor: unknown) => void;
}) {
  const id = `campo-${campo.nombre}`;
  const idError = `${id}-error`;
  const idAyuda = `${id}-ayuda`;
  const descrito =
    [error ? idError : null, campo.ayuda ? idAyuda : null]
      .filter(Boolean)
      .join(" ") || undefined;

  return (
    <div className={campo.tipo === "multiseleccion" ? "sm:col-span-2" : ""}>
      <label htmlFor={id} className="block text-sm font-medium">
        {campo.etiqueta}
        {!campo.requerido ? (
          <span className="font-normal text-suave"> (opcional)</span>
        ) : null}
      </label>

      <div className="mt-2">
        <Control
          campo={campo}
          id={id}
          valor={valor}
          invalido={Boolean(error)}
          descrito={descrito}
          onChange={onChange}
        />
      </div>

      {campo.ayuda ? (
        <p id={idAyuda} className="mt-1.5 text-xs text-suave">
          {campo.ayuda}
        </p>
      ) : null}
      {error ? (
        <p id={idError} role="alert" className="mt-1.5 text-xs font-medium text-red-600 dark:text-red-400">
          {error}
        </p>
      ) : null}
    </div>
  );
}

function Control({
  campo,
  id,
  valor,
  invalido,
  descrito,
  onChange,
}: {
  campo: CampoFormulario;
  id: string;
  valor: unknown;
  invalido: boolean;
  descrito?: string;
  onChange: (valor: unknown) => void;
}) {
  const comunes = {
    id,
    name: campo.nombre,
    "aria-invalid": invalido || undefined,
    "aria-describedby": descrito,
    className: `${claseControl} ${invalido ? "border-red-500" : ""}`,
  };

  switch (campo.tipo) {
    case "seleccion":
      return (
        <select
          {...comunes}
          value={typeof valor === "string" ? valor : ""}
          onChange={(e) => onChange(e.target.value)}
        >
          <option value="">Selecciona una opción</option>
          {campo.opciones.map((opcion) => (
            <option key={opcion.valor} value={opcion.valor}>
              {opcion.etiqueta}
            </option>
          ))}
        </select>
      );

    case "multiseleccion": {
      const elegidos = Array.isArray(valor) ? (valor as string[]) : [];
      return (
        <fieldset aria-describedby={descrito} className="flex flex-wrap gap-2">
          <legend className="sr-only">{campo.etiqueta}</legend>
          {campo.opciones.map((opcion) => {
            const activo = elegidos.includes(opcion.valor);
            return (
              <label
                key={opcion.valor}
                className={`cursor-pointer rounded-xl border px-4 py-2 text-sm transition-colors ${
                  activo
                    ? "border-tinta-600 bg-tinta-50 text-tinta-800 dark:bg-tinta-950 dark:text-tinta-200"
                    : "border-borde bg-superficie hover:border-tinta-400"
                }`}
              >
                <input
                  type="checkbox"
                  className="sr-only"
                  checked={activo}
                  onChange={() =>
                    onChange(
                      activo
                        ? elegidos.filter((v) => v !== opcion.valor)
                        : [...elegidos, opcion.valor],
                    )
                  }
                />
                {opcion.etiqueta}
              </label>
            );
          })}
        </fieldset>
      );
    }

    case "booleano":
      // Radios rather than a checkbox: an unchecked box is ambiguous between
      // "no" and "not answered", and conditional fields depend on knowing
      // which of those it is.
      return (
        <fieldset aria-describedby={descrito} className="flex gap-2">
          <legend className="sr-only">{campo.etiqueta}</legend>
          {[
            { v: true, etiqueta: "Sí" },
            { v: false, etiqueta: "No" },
          ].map(({ v, etiqueta }) => (
            <label
              key={etiqueta}
              className={`cursor-pointer rounded-xl border px-5 py-2.5 text-sm transition-colors ${
                valor === v
                  ? "border-tinta-600 bg-tinta-50 text-tinta-800 dark:bg-tinta-950 dark:text-tinta-200"
                  : "border-borde bg-superficie hover:border-tinta-400"
              }`}
            >
              <input
                type="radio"
                name={campo.nombre}
                className="sr-only"
                checked={valor === v}
                onChange={() => onChange(v)}
              />
              {etiqueta}
            </label>
          ))}
        </fieldset>
      );

    default: {
      const tipos: Record<string, string> = {
        email: "email",
        telefono: "tel",
        numero: "number",
        entero: "number",
        fecha: "date",
      };
      const modos: Record<string, "numeric" | "tel" | "email"> = {
        numero: "numeric",
        entero: "numeric",
        telefono: "tel",
        email: "email",
      };
      return (
        <input
          {...comunes}
          type={tipos[campo.tipo] ?? "text"}
          inputMode={modos[campo.tipo]}
          autoComplete={autocompletadoDe(campo.nombre)}
          value={typeof valor === "string" || typeof valor === "number" ? String(valor) : ""}
          onChange={(e) => onChange(e.target.value)}
        />
      );
    }
  }
}

/** Let the browser fill in what it already knows about the visitor. */
function autocompletadoDe(nombre: string): string | undefined {
  const mapa: Record<string, string> = {
    nombre: "name",
    correo: "email",
    telefono: "tel",
    ciudad: "address-level2",
  };
  return mapa[nombre];
}
