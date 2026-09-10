import Link from "next/link";

import { Encabezado, Etiqueta, Puntaje, Tarjeta, Vacio, fecha } from "@/components/ui";
import { apiProtegido } from "@/lib/sesion";
import type { Pagina, Resumen, SolicitudEnCola } from "@/lib/tipos";
import { tonoDeNivel } from "@/components/ui";

export default async function Panel() {
  const [resumen, cola] = await Promise.all([
    apiProtegido<Resumen>("/crm/resumen"),
    apiProtegido<Pagina<SolicitudEnCola>>("/crm/solicitudes?limite=5"),
  ]);

  const cifras = [
    { etiqueta: "Solicitudes nuevas", valor: resumen.solicitudes_nuevas, href: "/solicitudes" },
    { etiqueta: "Oportunidades abiertas", valor: resumen.oportunidades_abiertas, href: "/pipeline" },
    { etiqueta: "Clientes", valor: resumen.clientes, href: "/clientes" },
    { etiqueta: "Pólizas vigentes", valor: resumen.polizas_vigentes, href: "/clientes" },
    { etiqueta: "Vencen en 60 días", valor: resumen.renovaciones_60_dias, href: "/clientes" },
  ] as const;

  return (
    <>
      <Encabezado
        titulo="Resumen"
        descripcion="Lo que necesita atención hoy."
      />

      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-5">
        {cifras.map((cifra) => (
          <Link key={cifra.etiqueta} href={cifra.href}>
            <Tarjeta className="h-full p-4 transition-colors hover:border-tinta-400">
              <p className="text-xs text-suave">{cifra.etiqueta}</p>
              <p className="mt-1 text-3xl font-semibold tabular-nums">{cifra.valor}</p>
            </Tarjeta>
          </Link>
        ))}
      </div>

      <h2 className="mt-10 text-lg font-semibold">Primeras en la cola</h2>
      <p className="mt-1 text-sm text-suave">
        Ordenadas por probabilidad de cierre, no por fecha.
      </p>

      <div className="mt-4">
        {cola.elementos.length === 0 ? (
          <Vacio mensaje="No hay solicitudes registradas todavía." />
        ) : (
          <Tarjeta className="divide-y divide-borde">
            {cola.elementos.map((solicitud) => (
              <div
                key={solicitud.id}
                className="flex flex-wrap items-center justify-between gap-3 p-4"
              >
                <div className="min-w-0">
                  <p className="flex items-center gap-2 font-medium">
                    <Link
                      href={`/clientes/${solicitud.cliente.id}`}
                      className="truncate hover:underline"
                    >
                      {solicitud.cliente.nombre}
                    </Link>
                    {solicitud.nivel ? (
                      <Etiqueta tono={tonoDeNivel[solicitud.nivel]}>
                        {solicitud.nivel}
                      </Etiqueta>
                    ) : null}
                  </p>
                  <p className="mt-0.5 text-xs text-suave">
                    <span className="font-mono">{solicitud.codigo}</span> ·{" "}
                    {solicitud.ramo} · {fecha(solicitud.creada_en)}
                    {solicitud.asesor ? ` · ${solicitud.asesor.nombre}` : " · sin asignar"}
                  </p>
                </div>
                <Puntaje valor={solicitud.puntaje} />
              </div>
            ))}
          </Tarjeta>
        )}
      </div>
    </>
  );
}
