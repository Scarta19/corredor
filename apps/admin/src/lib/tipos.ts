/** Shapes returned by the platform API. Mirrors `apps/api/src/corredor/api/v1/crm.py`. */

export type Etapa =
  | "nuevo"
  | "contactado"
  | "cotizando"
  | "propuesta_enviada"
  | "en_negociacion"
  | "ganado"
  | "perdido";

export type Nivel = "bajo" | "medio" | "alto";
export type Ventana =
  | "critica"
  | "urgente"
  | "proxima"
  | "planificada"
  | "futura"
  | "vencida";

export interface Referencia {
  id: string;
  nombre: string;
}

export interface Pagina<T> {
  total: number;
  limite: number;
  desplazamiento: number;
  elementos: T[];
}

export interface Resumen {
  solicitudes_nuevas: number;
  oportunidades_abiertas: number;
  clientes: number;
  polizas_vigentes: number;
  renovaciones_60_dias: number;
}

export interface SolicitudEnCola {
  id: string;
  codigo: string;
  creada_en: string;
  estado: string;
  canal: string;
  ramo: string;
  cliente: Referencia;
  telefono: string | null;
  asesor: Referencia | null;
  puntaje: number | null;
  nivel: Nivel | null;
  oportunidad_id: string | null;
}

export interface OportunidadResumen {
  id: string;
  ramo: string;
  etapa: Etapa;
  creada_en: string;
  asesor: Referencia | null;
  puntaje: number | null;
}

export interface ColumnaPipeline {
  etapa: Etapa;
  total: number;
  oportunidades: OportunidadResumen[];
}

export interface ClienteEnLista {
  id: string;
  nombre: string;
  tipo: "persona" | "empresa";
  documento: string | null;
  telefono: string | null;
  email: string | null;
  ciudad: string | null;
  origen: string;
  fecha_registro: string;
}

export interface PolizaResumen {
  id: string;
  numero: string;
  ramo: string;
  aseguradora: string;
  fecha_vencimiento: string;
  dias_para_vencimiento: number;
  ventana: Ventana;
  prima: string;
  estado: string;
}

export interface ComunicacionResumen {
  id: string;
  canal: string;
  direccion: string;
  contenido: string;
  creada_en: string;
  automatico: boolean;
}

export interface ClienteDetalle extends ClienteEnLista {
  asesor: Referencia | null;
  notas: string | null;
  solicitudes: SolicitudEnCola[];
  oportunidades: OportunidadResumen[];
  polizas: PolizaResumen[];
  comunicaciones: ComunicacionResumen[];
}

export interface UsuarioSesion {
  id: string;
  nombre: string;
  email: string;
  rol: "admin" | "gerente" | "asesor";
  tenant: string;
  puede_ver_dashboard: boolean;
}

export const ETAPAS: { etapa: Etapa; etiqueta: string }[] = [
  { etapa: "nuevo", etiqueta: "Nuevo" },
  { etapa: "contactado", etiqueta: "Contactado" },
  { etapa: "cotizando", etiqueta: "Cotizando" },
  { etapa: "propuesta_enviada", etiqueta: "Propuesta enviada" },
  { etapa: "en_negociacion", etiqueta: "En negociación" },
  { etapa: "ganado", etiqueta: "Ganado" },
  { etapa: "perdido", etiqueta: "Perdido" },
];

export const MOTIVOS_PERDIDA = [
  { valor: "precio", etiqueta: "Precio" },
  { valor: "competencia", etiqueta: "Competencia" },
  { valor: "sin_respuesta", etiqueta: "Sin respuesta" },
  { valor: "no_asegurable", etiqueta: "No asegurable" },
  { valor: "desiste", etiqueta: "Desiste" },
  { valor: "otro", etiqueta: "Otro" },
];
