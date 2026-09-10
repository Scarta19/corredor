/**
 * Client for the platform API.
 *
 * The site renders whatever the catalogue endpoint returns rather than
 * hard-coding lines of business, so a brokerage adding a ramo sees it appear
 * without a frontend release. See docs/adr/0003-formularios-dinamicos.md.
 */

import { config } from "./config";

export type TipoCliente = "persona" | "empresa";

export interface RamoResumen {
  codigo: string;
  nombre: string;
  descripcion: string | null;
  dirigido_a: TipoCliente | null;
}

export interface OpcionCampo {
  valor: string;
  etiqueta: string;
}

export interface CampoFormulario {
  nombre: string;
  etiqueta: string;
  tipo: string;
  requerido: boolean;
  ayuda: string | null;
  opciones: OpcionCampo[];
  orden: number;
  depende_de: string | null;
  depende_de_valores: string[];
}

export interface RamoDetalle extends RamoResumen {
  formulario: { version: number; campos: CampoFormulario[] };
}

async function pedir<T>(ruta: string, revalidate = 300): Promise<T> {
  const respuesta = await fetch(`${config.apiUrl}/api/v1${ruta}`, {
    headers: { "X-Tenant": config.tenant },
    next: { revalidate },
  });
  if (!respuesta.ok) {
    throw new Error(`API ${respuesta.status} en ${ruta}`);
  }
  return (await respuesta.json()) as T;
}

/**
 * Lines of business on offer.
 *
 * The catalogue is presentation, not function: if the API is unreachable the
 * marketing site must still render, still rank and still let a visitor reach
 * a human. Callers get an empty list and show the fallback copy instead of a
 * 500 page.
 */
export async function listarRamos(
  dirigidoA?: TipoCliente,
): Promise<RamoResumen[]> {
  const query = dirigidoA ? `?dirigido_a=${dirigidoA}` : "";
  try {
    return await pedir<RamoResumen[]>(`/ramos${query}`);
  } catch {
    return [];
  }
}

export async function obtenerRamo(codigo: string): Promise<RamoDetalle | null> {
  try {
    return await pedir<RamoDetalle>(`/ramos/${codigo}`);
  } catch {
    return null;
  }
}
