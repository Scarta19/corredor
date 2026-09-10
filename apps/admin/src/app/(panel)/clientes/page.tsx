import Link from "next/link";

import { Encabezado, Etiqueta, Tarjeta, Vacio, fecha } from "@/components/ui";
import { apiProtegido } from "@/lib/sesion";
import type { ClienteEnLista, Pagina } from "@/lib/tipos";

export const metadata = { title: "Clientes" };

export default async function Clientes({
  searchParams,
}: {
  searchParams: Promise<{ q?: string }>;
}) {
  const { q = "" } = await searchParams;
  const consulta = q ? `&q=${encodeURIComponent(q)}` : "";
  const pagina = await apiProtegido<Pagina<ClienteEnLista>>(
    `/crm/clientes?limite=50${consulta}`,
  );

  return (
    <>
      <Encabezado
        titulo="Clientes"
        descripcion="Personas y empresas registradas en la agencia."
      />

      {/* A GET form keeps the search in the URL, so a result set can be shared
          and the back button behaves. */}
      <form className="mb-4 flex gap-2">
        <input
          type="search"
          name="q"
          defaultValue={q}
          placeholder="Nombre, documento, teléfono o correo"
          aria-label="Buscar clientes"
          className="w-full max-w-md rounded-lg border border-borde bg-superficie px-3.5 py-2 text-sm outline-none focus:border-tinta-500"
        />
        <button
          type="submit"
          className="rounded-lg border border-borde px-4 py-2 text-sm font-medium hover:border-tinta-400"
        >
          Buscar
        </button>
      </form>

      {pagina.elementos.length === 0 ? (
        <Vacio
          mensaje={
            q ? `Sin resultados para "${q}".` : "Todavía no hay clientes registrados."
          }
        />
      ) : (
        <Tarjeta className="overflow-x-auto">
          <table className="w-full min-w-[44rem] text-sm">
            <thead className="border-b border-borde text-left text-xs uppercase tracking-wide text-suave">
              <tr>
                <th className="px-4 py-3 font-medium">Nombre</th>
                <th className="px-4 py-3 font-medium">Documento</th>
                <th className="px-4 py-3 font-medium">Contacto</th>
                <th className="px-4 py-3 font-medium">Ciudad</th>
                <th className="px-4 py-3 font-medium">Origen</th>
                <th className="px-4 py-3 font-medium">Registro</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-borde">
              {pagina.elementos.map((cliente) => (
                <tr
                  key={cliente.id}
                  className="hover:bg-piedra-100/60 dark:hover:bg-piedra-800/40"
                >
                  <td className="px-4 py-3">
                    <Link
                      href={`/clientes/${cliente.id}`}
                      className="font-medium hover:underline"
                    >
                      {cliente.nombre}
                    </Link>
                    <span className="ml-2">
                      <Etiqueta tono={cliente.tipo === "empresa" ? "azul" : "neutro"}>
                        {cliente.tipo}
                      </Etiqueta>
                    </span>
                  </td>
                  <td className="px-4 py-3 font-mono text-xs">
                    {cliente.documento ?? "—"}
                  </td>
                  <td className="px-4 py-3">
                    <span className="block">{cliente.telefono ?? "—"}</span>
                    <span className="block text-xs text-suave">
                      {cliente.email ?? ""}
                    </span>
                  </td>
                  <td className="px-4 py-3">{cliente.ciudad ?? "—"}</td>
                  <td className="px-4 py-3 capitalize text-suave">{cliente.origen}</td>
                  <td className="whitespace-nowrap px-4 py-3 text-suave">
                    {fecha(cliente.fecha_registro)}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </Tarjeta>
      )}

      <p className="mt-4 text-xs text-suave">
        Mostrando {pagina.elementos.length} de {pagina.total}.
      </p>
    </>
  );
}
