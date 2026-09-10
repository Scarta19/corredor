/**
 * Schema.org structured data.
 *
 * An insurance brokerage is a local business, and local intent — "seguros en
 * <ciudad>" — is most of its organic traffic. Marking the agency up as an
 * `InsuranceAgency`, and the FAQ as a `FAQPage`, is what lets that show up as
 * a rich result instead of a plain blue link.
 */

import { preguntas } from "@/content/site";
import { config } from "@/lib/config";

const base = process.env.NEXT_PUBLIC_SITE_URL ?? "http://localhost:3000";

function Jsonld({ datos }: { datos: object }) {
  return (
    <script
      type="application/ld+json"
      // The payload is built from our own configuration, never from user
      // input, so there is nothing here for a visitor to inject into.
      dangerouslySetInnerHTML={{ __html: JSON.stringify(datos) }}
    />
  );
}

export function DatosAgencia() {
  const [ciudad, region] = config.contacto.ciudad.split(",").map((p) => p.trim());

  return (
    <Jsonld
      datos={{
        "@context": "https://schema.org",
        "@type": "InsuranceAgency",
        name: config.brand.nombre,
        description:
          "Agencia de seguros para personas y empresas: cotizamos con varias aseguradoras, asignamos un asesor responsable y controlamos las renovaciones.",
        url: base,
        telephone: config.contacto.telefono,
        email: config.contacto.email,
        areaServed: region ?? ciudad,
        address: {
          "@type": "PostalAddress",
          addressLocality: ciudad,
          addressRegion: region ?? ciudad,
          addressCountry: "CO",
        },
        openingHoursSpecification: {
          "@type": "OpeningHoursSpecification",
          dayOfWeek: [
            "Monday",
            "Tuesday",
            "Wednesday",
            "Thursday",
            "Friday",
          ],
          opens: "08:00",
          closes: "18:00",
        },
      }}
    />
  );
}

export function DatosPreguntas() {
  return (
    <Jsonld
      datos={{
        "@context": "https://schema.org",
        "@type": "FAQPage",
        mainEntity: preguntas.map((item) => ({
          "@type": "Question",
          name: item.pregunta,
          acceptedAnswer: { "@type": "Answer", text: item.respuesta },
        })),
      }}
    />
  );
}
