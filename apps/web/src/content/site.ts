/**
 * Copy for the public site.
 *
 * Kept in one place, in the language the visitor reads, so a brokerage can
 * revise its own wording without going through the components. Nothing here
 * names a specific agency — the brand comes from `config`.
 */

import type { Route } from "next";

export interface EnlaceNav {
  href: Route;
  etiqueta: string;
}

export const navegacion: EnlaceNav[] = [
  { href: "/", etiqueta: "Inicio" },
  { href: "/nosotros", etiqueta: "Nosotros" },
  { href: "/personas", etiqueta: "Personas" },
  { href: "/empresas", etiqueta: "Empresas" },
  { href: "/seguros", etiqueta: "Seguros" },
  { href: "/contacto", etiqueta: "Contacto" },
];

export type EstiloAccion = "primario" | "secundario";

export interface Accion {
  href: Route;
  etiqueta: string;
  descripcion: string;
  icono: string;
  estilo: EstiloAccion;
}

/**
 * The four calls to action from §4 of the platform brief.
 *
 * The site's purpose is to produce these, not to inform. They appear in the
 * header, in the hero, and again at the foot of every page.
 */
export const acciones: Accion[] = [
  {
    href: "/cotizar",
    etiqueta: "Solicitar cotización",
    descripcion:
      "Cuéntanos qué necesitas asegurar y recibe una propuesta a tu medida.",
    icono: "documento",
    estilo: "primario",
  },
  {
    href: "/contacto",
    etiqueta: "Hablar con un asesor",
    descripcion:
      "Resuelve tus dudas con una persona que conoce el mercado, no con un robot.",
    icono: "conversacion",
    estilo: "secundario",
  },
  {
    href: "/renovar",
    etiqueta: "Renovar mi póliza",
    descripcion:
      "¿Tu póliza está por vencer? Nos encargamos de la renovación por ti.",
    icono: "renovar",
    estilo: "secundario",
  },
  {
    href: "/reportar",
    etiqueta: "Reportar una solicitud",
    descripcion:
      "Siniestros, cambios en tu póliza o cualquier novedad que necesites reportar.",
    icono: "reportar",
    estilo: "secundario",
  },
];

export interface Propuesta {
  titulo: string;
  detalle: string;
}

/** §4 — "¿Por qué elegirnos?" */
export const propuestas: Propuesta[] = [
  {
    titulo: "Comparamos, no vendemos una sola marca",
    detalle:
      "Trabajamos con varias aseguradoras. Ponemos las opciones lado a lado y te explicamos en qué se diferencian de verdad, más allá del precio.",
  },
  {
    titulo: "Un asesor con nombre propio",
    detalle:
      "Cada cliente queda asignado a un asesor responsable. No vuelves a explicar tu caso desde cero cada vez que llamas.",
  },
  {
    titulo: "No dejamos vencer tu póliza",
    detalle:
      "Controlamos las fechas de vencimiento y te buscamos con anticipación. Renovar deja de depender de que tú te acuerdes.",
  },
  {
    titulo: "Te acompañamos cuando toca usarla",
    detalle:
      "El momento que importa es el siniestro. Ahí es donde un intermediario se gana el puesto, y donde nos vas a encontrar.",
  },
];

export interface Paso {
  numero: number;
  titulo: string;
  detalle: string;
}

/** The visitor-facing version of the §6 flow. */
export const pasos: Paso[] = [
  {
    numero: 1,
    titulo: "Nos cuentas qué necesitas",
    detalle:
      "Eliges el tipo de seguro y respondes solo las preguntas de ese ramo. Nada de formularios interminables.",
  },
  {
    numero: 2,
    titulo: "Un asesor toma tu caso",
    detalle:
      "Tu solicitud queda registrada y asignada. No se pierde en un chat ni en una hoja de cálculo.",
  },
  {
    numero: 3,
    titulo: "Comparamos el mercado",
    detalle:
      "Cotizamos con varias aseguradoras y te presentamos las opciones con sus diferencias explicadas.",
  },
  {
    numero: 4,
    titulo: "Quedas acompañado",
    detalle:
      "Renovaciones, cambios y siniestros: seguimos ahí después de la venta.",
  },
];

export interface Pregunta {
  pregunta: string;
  respuesta: string;
}

/** §4 — "Preguntas frecuentes" */
export const preguntas: Pregunta[] = [
  {
    pregunta: "¿Cotizar tiene algún costo?",
    respuesta:
      "No. Cotizar y recibir asesoría es gratuito. Como intermediarios, nuestra remuneración la paga la aseguradora, no tú: el precio de la póliza es el mismo que tomándola directamente.",
  },
  {
    pregunta: "¿En cuánto tiempo recibo respuesta?",
    respuesta:
      "Buscamos responder toda solicitud el mismo día hábil. Para pólizas sencillas, como automóviles, normalmente tendrás opciones en pocas horas.",
  },
  {
    pregunta: "¿Qué documentos necesito para cotizar?",
    respuesta:
      "Para cotizar basta con la información del formulario. Los documentos se piden solo cuando decides tomar la póliza, y te decimos exactamente cuáles según el ramo.",
  },
  {
    pregunta: "¿Puedo pasar mi póliza actual con ustedes?",
    respuesta:
      "Sí. Puedes trasladar la intermediación de una póliza vigente sin cambiar de aseguradora ni perder antigüedad. Escríbenos y te explicamos el proceso.",
  },
  {
    pregunta: "¿Qué pasa si tengo un siniestro?",
    respuesta:
      "Nos reportas la novedad y nosotros te guiamos en el trámite ante la aseguradora: qué documentos reunir, en qué orden y qué esperar en cada etapa.",
  },
  {
    pregunta: "¿Trabajan con empresas?",
    respuesta:
      "Sí. Manejamos pólizas de cumplimiento, responsabilidad civil, riesgos empresariales y vida grupo, incluidas las garantías que exigen las entidades contratantes.",
  },
];

export const nosotros = {
  titulo: "Intermediarios de seguros, del lado del cliente",
  parrafos: [
    "Somos una agencia de seguros: nuestro trabajo es entender qué necesitas proteger, buscar en el mercado quién lo cubre mejor y acompañarte cuando toque usar la póliza.",
    "No pertenecemos a una aseguradora. Eso nos deja libres para comparar y para recomendar lo que realmente le conviene a cada cliente, incluso cuando la respuesta correcta es que no necesitas más cobertura de la que ya tienes.",
    "Atendemos a personas y a empresas, desde el seguro de un vehículo particular hasta las pólizas de cumplimiento que exige una licitación.",
  ],
  cifras: [
    { valor: "8", etiqueta: "ramos de seguros" },
    { valor: "6+", etiqueta: "aseguradoras aliadas" },
    { valor: "24 h", etiqueta: "meta de respuesta" },
  ],
};
