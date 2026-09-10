/**
 * Tenant-facing configuration.
 *
 * The platform is multi-tenant, so nothing about a particular brokerage is
 * hard-coded into the site. Brand, contact details and the tenant slug all
 * arrive as environment variables, which is what lets the same build serve a
 * second agency by changing three values.
 */

export const config = {
  /** Tenant slug sent to the API as `X-Tenant`. */
  tenant: process.env.NEXT_PUBLIC_TENANT ?? "demo",
  apiUrl: process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000",

  brand: {
    nombre: process.env.NEXT_PUBLIC_BRAND ?? "Agencia Demo de Seguros",
    corto: process.env.NEXT_PUBLIC_BRAND_SHORT ?? "Agencia Demo",
    eslogan:
      process.env.NEXT_PUBLIC_TAGLINE ?? "Asesoría en seguros, sin vueltas.",
  },

  contacto: {
    telefono: process.env.NEXT_PUBLIC_PHONE ?? "+57 300 000 0000",
    whatsapp: process.env.NEXT_PUBLIC_WHATSAPP ?? "573000000000",
    email: process.env.NEXT_PUBLIC_EMAIL ?? "contacto@demo.test",
    ciudad: process.env.NEXT_PUBLIC_CITY ?? "Caucasia, Antioquia",
    horario: "Lunes a viernes, 8:00 a.m. – 6:00 p.m.",
  },
} as const;

/** A WhatsApp deep link with the message pre-written for the visitor. */
export function whatsappUrl(mensaje: string): string {
  return `https://wa.me/${config.contacto.whatsapp}?text=${encodeURIComponent(mensaje)}`;
}
