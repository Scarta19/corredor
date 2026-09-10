import type { MetadataRoute } from "next";

import { listarRamos } from "@/lib/api";
import { config } from "@/lib/config";

const base = process.env.NEXT_PUBLIC_SITE_URL ?? "http://localhost:3000";

/**
 * The sitemap includes a URL per ramo, discovered from the API.
 *
 * §2 puts digital positioning first among the platform's objectives, and
 * `/cotizar/[codigo]` pages are what rank for "seguro de <ramo> en <ciudad>".
 * Generating them from the catalogue means a brokerage that adds a line of
 * business is indexable without anybody remembering to edit a list.
 */
export default async function sitemap(): Promise<MetadataRoute.Sitemap> {
  const estaticas = [
    { ruta: "", prioridad: 1.0, frecuencia: "weekly" as const },
    { ruta: "/cotizar", prioridad: 0.9, frecuencia: "weekly" as const },
    { ruta: "/seguros", prioridad: 0.9, frecuencia: "weekly" as const },
    { ruta: "/personas", prioridad: 0.8, frecuencia: "monthly" as const },
    { ruta: "/empresas", prioridad: 0.8, frecuencia: "monthly" as const },
    { ruta: "/renovar", prioridad: 0.7, frecuencia: "monthly" as const },
    { ruta: "/reportar", prioridad: 0.7, frecuencia: "monthly" as const },
    { ruta: "/contacto", prioridad: 0.7, frecuencia: "monthly" as const },
    { ruta: "/nosotros", prioridad: 0.5, frecuencia: "yearly" as const },
  ];

  const ramos = await listarRamos();
  const ahora = new Date();

  return [
    ...estaticas.map(({ ruta, prioridad, frecuencia }) => ({
      url: `${base}${ruta}`,
      lastModified: ahora,
      changeFrequency: frecuencia,
      priority: prioridad,
    })),
    ...ramos.map((ramo) => ({
      url: `${base}/cotizar/${ramo.codigo}`,
      lastModified: ahora,
      changeFrequency: "monthly" as const,
      priority: 0.85,
    })),
  ];
}

export const revalidate = 3600;

// Referenced so the tenant slug is part of the module's contract, making an
// accidental cross-tenant sitemap obvious in review.
export const tenant = config.tenant;
