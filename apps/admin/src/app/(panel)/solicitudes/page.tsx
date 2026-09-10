import Link from "next/link";
import type { Route } from "next";

import {
  Encabezado,
  Etiqueta,
  Puntaje,
  Tarjeta,
  Vacio,
  fechaHora,
  tonoDeNivel,
} from "@/components/ui";
import { apiProtegido } from "@/lib/sesion";
import type { Pagina, SolicitudEnCola } from "@/lib/tipos";

const filtros = [
  { etiqueta: "Todas", query: "" },
  { etiqueta: "Nuevas", query: "estado=nueva" },
  { etiqueta: "Sin asignar", query: "sin_asignar=true" },
  { etiqueta: "En proceso", query: "estado=en_proceso" },
];

export default async function Solicitudes({
  searchParams,
}: {
  searchParams: Promise<{ filtro?: string }>;
}) {
  const { filtro = "" } = await searchParams;
  const activo = filtros.find((f) => f.query === filtro) ?? filtros[0];
  const cola = await apiProtegido<Pagina<SolicitudEnCola>>(
    `/crm/solicitudes?limite=50${activo.query ? `&${activo.query}` : ""}`,
  );

  return (
    <>
      <Encabezado
        titulo="Solicitudes"
        descripcion="La cola de trabajo, ordenada por probabilidad de cierre."
      />

      <div className="mb-4 flex flex-wrap gap-2">
        {filtros.map((f) => (
          <Link
            key={f.etiqueta}
            href={(f.query ? `/solicitudes?filtro=${f.query}` : "/solicitudes") as Route}
            className={`rounded-lg border px-3 py-1.5 text-sm transition-colors ${
              f.query === activo.query
                ? "border-tinta-600 bg-tinta-50 text-tinta-800 dark:bg-tinta-950 dark:text-tinta-200"
                : "border-borde hover:border-tinta-400"
            }`}
          >
            {f.etiqueta}
          </Link>
        ))}
      </div>

      {cola.elementos.length === 0 ? (
        <Vacio mensaje="No hay solicitudes con este filtro." />
      ) : (
        <Tarjeta className="overflow-x-auto">
          <table className="w-full min-w-[52rem] text-sm">
            <thead className="border-b border-borde text-left text-xs uppercase tracking-wide text-suave">
              <tr>
                <th className="px-4 py-3 font-medium">Radicado</th>
                <th className="px-4 py-3 font-medium">Cliente</th>
                <th className="px-4 py-3 font-medium">Ramo</th>
                <th className="px-4 py-3 font-medium">Canal</th>
                <th className="px-4 py-3 font-medium">Asesor</th>
                <th className="px-4 py-3 font-medium">Recibida</th>
                <th className="px-4 py-3 font-medium">Prioridad</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-borde">
              {cola.elementos.map((s) => (
                <tr key={s.id} className="hover:bg-piedra-100/60 dark:hover:bg-piedra-800/40">
                  <td className="whitespace-nowrap px-4 py-3 font-mono text-xs">
                    {s.codigo}
                  </td>
                  <td className="px-4 py-3">
                    <Link
                      href={`/clientes/${s.cliente.id}`}
                      className="font-medium hover:underline"
                    >
                      {s.cliente.nombre}
                    </Link>
                    {s.telefono ? (
                      <span className="block text-xs text-suave">{s.telefono}</span>
                    ) : null}
                  </td>
                  <td className="px-4 py-3">{s.ramo}</td>
                  <td className="px-4 py-3 capitalize text-suave">{s.canal}</td>
                  <td className="px-4 py-3">
                    {s.asesor ? (
                      s.asesor.nombre
                    ) : (
                      <Etiqueta tono="ambar">Por asignar</Etiqueta>
                    )}
                  </td>
                  <td className="whitespace-nowrap px-4 py-3 text-suave">
                    {fechaHora(s.creada_en)}
                  </td>
                  <td className="whitespace-nowrap px-4 py-3">
                    <span className="flex items-center gap-2">
                      <Puntaje valor={s.puntaje} />
                      {s.nivel ? (
                        <Etiqueta tono={tonoDeNivel[s.nivel]}>{s.nivel}</Etiqueta>
                      ) : null}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </Tarjeta>
      )}

      <p className="mt-4 text-xs text-suave">
        Mostrando {cola.elementos.length} de {cola.total}.
      </p>
    </>
  );
}
