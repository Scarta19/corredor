import Link from "next/link";

import {
  Encabezado,
  Etiqueta,
  Puntaje,
  Tarjeta,
  Vacio,
  dinero,
  etiquetaDeVentana,
  fecha,
  fechaHora,
  tonoDeEtapa,
  tonoDeVentana,
} from "@/components/ui";
import { apiProtegido } from "@/lib/sesion";
import { ETAPAS } from "@/lib/tipos";
import type { ClienteDetalle } from "@/lib/tipos";

type Params = { params: Promise<{ id: string }> };

export async function generateMetadata({ params }: Params) {
  const { id } = await params;
  const cliente = await apiProtegido<ClienteDetalle>(`/crm/clientes/${id}`);
  return { title: cliente.nombre };
}

/**
 * §9's single view.
 *
 * The whole point of the CRM is that an advisor does not have to hunt through
 * files, chats and spreadsheets — so everything about this client is on one
 * page, in one request.
 */
export default async function Cliente({ params }: Params) {
  const { id } = await params;
  const cliente = await apiProtegido<ClienteDetalle>(`/crm/clientes/${id}`);

  return (
    <>
      <Link
        href="/clientes"
        className="text-sm text-tinta-700 hover:underline dark:text-tinta-300"
      >
        ← Clientes
      </Link>

      <div className="mt-3">
        <Encabezado
          titulo={cliente.nombre}
          descripcion={[
            cliente.documento,
            cliente.telefono,
            cliente.email,
            cliente.ciudad,
          ]
            .filter(Boolean)
            .join(" · ")}
        >
          <div className="flex items-center gap-2">
            <Etiqueta tono={cliente.tipo === "empresa" ? "azul" : "neutro"}>
              {cliente.tipo}
            </Etiqueta>
            <Etiqueta>
              {cliente.asesor ? cliente.asesor.nombre : "Sin asesor"}
            </Etiqueta>
          </div>
        </Encabezado>
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        <section>
          <h2 className="mb-3 text-sm font-semibold uppercase tracking-wide text-suave">
            Pólizas ({cliente.polizas.length})
          </h2>
          {cliente.polizas.length === 0 ? (
            <Vacio mensaje="Sin pólizas registradas." />
          ) : (
            <Tarjeta className="divide-y divide-borde">
              {cliente.polizas.map((poliza) => (
                <div key={poliza.id} className="p-4">
                  <div className="flex flex-wrap items-center justify-between gap-2">
                    <p className="font-medium">
                      {poliza.ramo}
                      <span className="ml-2 font-mono text-xs text-suave">
                        {poliza.numero}
                      </span>
                    </p>
                    <Etiqueta tono={tonoDeVentana[poliza.ventana]}>
                      {etiquetaDeVentana[poliza.ventana]}
                    </Etiqueta>
                  </div>
                  <p className="mt-1 text-xs text-suave">
                    {poliza.aseguradora} · {dinero(poliza.prima)} · vence{" "}
                    {fecha(poliza.fecha_vencimiento)}
                    {poliza.dias_para_vencimiento >= 0
                      ? ` (faltan ${poliza.dias_para_vencimiento} días)`
                      : ` (venció hace ${Math.abs(poliza.dias_para_vencimiento)} días)`}
                  </p>
                </div>
              ))}
            </Tarjeta>
          )}
        </section>

        <section>
          <h2 className="mb-3 text-sm font-semibold uppercase tracking-wide text-suave">
            Oportunidades ({cliente.oportunidades.length})
          </h2>
          {cliente.oportunidades.length === 0 ? (
            <Vacio mensaje="Sin oportunidades abiertas." />
          ) : (
            <Tarjeta className="divide-y divide-borde">
              {cliente.oportunidades.map((oportunidad) => (
                <div
                  key={oportunidad.id}
                  className="flex flex-wrap items-center justify-between gap-2 p-4"
                >
                  <div>
                    <p className="font-medium">{oportunidad.ramo}</p>
                    <p className="mt-0.5 text-xs text-suave">
                      {fecha(oportunidad.creada_en)}
                      {oportunidad.asesor ? ` · ${oportunidad.asesor.nombre}` : ""}
                    </p>
                  </div>
                  <div className="flex items-center gap-2">
                    <Puntaje valor={oportunidad.puntaje} />
                    <Etiqueta tono={tonoDeEtapa[oportunidad.etapa]}>
                      {ETAPAS.find((e) => e.etapa === oportunidad.etapa)?.etiqueta ??
                        oportunidad.etapa}
                    </Etiqueta>
                  </div>
                </div>
              ))}
            </Tarjeta>
          )}
        </section>

        <section>
          <h2 className="mb-3 text-sm font-semibold uppercase tracking-wide text-suave">
            Solicitudes ({cliente.solicitudes.length})
          </h2>
          {cliente.solicitudes.length === 0 ? (
            <Vacio mensaje="Sin solicitudes." />
          ) : (
            <Tarjeta className="divide-y divide-borde">
              {cliente.solicitudes.map((solicitud) => (
                <div key={solicitud.id} className="p-4">
                  <p className="font-medium">
                    <span className="font-mono text-xs">{solicitud.codigo}</span>{" "}
                    · {solicitud.ramo}
                  </p>
                  <p className="mt-0.5 text-xs capitalize text-suave">
                    {solicitud.estado.replace("_", " ")} · {solicitud.canal} ·{" "}
                    {fechaHora(solicitud.creada_en)}
                  </p>
                </div>
              ))}
            </Tarjeta>
          )}
        </section>

        <section>
          <h2 className="mb-3 text-sm font-semibold uppercase tracking-wide text-suave">
            Comunicaciones ({cliente.comunicaciones.length})
          </h2>
          {cliente.comunicaciones.length === 0 ? (
            <Vacio mensaje="Sin comunicaciones registradas. Llegarán con el Módulo 3." />
          ) : (
            <Tarjeta className="divide-y divide-borde">
              {cliente.comunicaciones.map((comunicacion) => (
                <div key={comunicacion.id} className="p-4">
                  <p className="text-xs capitalize text-suave">
                    {comunicacion.canal} · {comunicacion.direccion} ·{" "}
                    {fechaHora(comunicacion.creada_en)}
                    {comunicacion.automatico ? " · automático" : ""}
                  </p>
                  <p className="mt-1 text-sm">{comunicacion.contenido}</p>
                </div>
              ))}
            </Tarjeta>
          )}
        </section>
      </div>
    </>
  );
}
