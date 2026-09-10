import type { Metadata, Viewport } from "next";
import { Inter } from "next/font/google";

import { Encabezado } from "@/components/encabezado";
import { PieDePagina } from "@/components/pie-de-pagina";
import { BotonWhatsapp } from "@/components/boton-whatsapp";
import { DatosAgencia } from "@/components/datos-estructurados";
import { config } from "@/lib/config";

import "./globals.css";

const inter = Inter({
  subsets: ["latin"],
  variable: "--font-inter",
  display: "swap",
});

export const metadata: Metadata = {
  metadataBase: new URL(
    process.env.NEXT_PUBLIC_SITE_URL ?? "http://localhost:3000",
  ),
  title: {
    default: `${config.brand.nombre} — ${config.brand.eslogan}`,
    template: `%s · ${config.brand.corto}`,
  },
  description:
    "Agencia de seguros para personas y empresas: cotizamos con varias aseguradoras, te asignamos un asesor y controlamos tus renovaciones.",
  openGraph: {
    type: "website",
    locale: "es_CO",
    siteName: config.brand.nombre,
  },
  robots: { index: true, follow: true },
};

export const viewport: Viewport = {
  themeColor: [
    { media: "(prefers-color-scheme: light)", color: "#f8fafb" },
    { media: "(prefers-color-scheme: dark)", color: "#11161c" },
  ],
};

export default function RootLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="es-CO" className={inter.variable}>
      <body className="font-sans antialiased">
        <a
          href="#contenido"
          className="sr-only focus:not-sr-only focus:absolute focus:left-4 focus:top-4 focus:z-50 focus:rounded-lg focus:bg-tinta-700 focus:px-4 focus:py-2 focus:text-white"
        >
          Saltar al contenido
        </a>
        <div className="flex min-h-dvh flex-col">
          <Encabezado />
          <main id="contenido" className="flex-1">
            {children}
          </main>
          <PieDePagina />
        </div>
        <BotonWhatsapp />
        <DatosAgencia />
      </body>
    </html>
  );
}
