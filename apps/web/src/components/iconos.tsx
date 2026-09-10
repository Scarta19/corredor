/**
 * Inline icons.
 *
 * Small enough to hand-write, which keeps the site free of an icon package
 * and its bundle. `currentColor` everywhere so they inherit the text colour
 * in both themes.
 */

type Props = { className?: string };

const base = "h-6 w-6";

export function IconoDocumento({ className = base }: Props) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.6} aria-hidden="true">
      <path d="M14 3v5h5" strokeLinecap="round" strokeLinejoin="round" />
      <path d="M14 3H6a1 1 0 0 0-1 1v16a1 1 0 0 0 1 1h12a1 1 0 0 0 1-1V8l-5-5Z" strokeLinecap="round" strokeLinejoin="round" />
      <path d="M9 13h6M9 17h4" strokeLinecap="round" />
    </svg>
  );
}

export function IconoConversacion({ className = base }: Props) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.6} aria-hidden="true">
      <path d="M20 12a7.5 7.5 0 0 1-10.9 6.7L4 20l1.3-4.1A7.5 7.5 0 1 1 20 12Z" strokeLinecap="round" strokeLinejoin="round" />
      <path d="M9 11h6M9 14h3" strokeLinecap="round" />
    </svg>
  );
}

export function IconoRenovar({ className = base }: Props) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.6} aria-hidden="true">
      <path d="M20 11a8 8 0 0 0-13.7-5.3L4 8" strokeLinecap="round" strokeLinejoin="round" />
      <path d="M4 4v4h4" strokeLinecap="round" strokeLinejoin="round" />
      <path d="M4 13a8 8 0 0 0 13.7 5.3L20 16" strokeLinecap="round" strokeLinejoin="round" />
      <path d="M20 20v-4h-4" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}

export function IconoReportar({ className = base }: Props) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.6} aria-hidden="true">
      <path d="M12 4.5 2.8 20h18.4L12 4.5Z" strokeLinecap="round" strokeLinejoin="round" />
      <path d="M12 10v4" strokeLinecap="round" />
      <circle cx="12" cy="17" r="0.9" fill="currentColor" stroke="none" />
    </svg>
  );
}

export function IconoEscudo({ className = base }: Props) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.6} aria-hidden="true">
      <path d="M12 3l7 3v5.5c0 4.3-2.9 8.3-7 9.5-4.1-1.2-7-5.2-7-9.5V6l7-3Z" strokeLinecap="round" strokeLinejoin="round" />
      <path d="m9 12 2 2 4-4" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}

export function IconoWhatsapp({ className = base }: Props) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="currentColor" aria-hidden="true">
      <path d="M12.04 2C6.58 2 2.13 6.45 2.13 11.91c0 1.75.46 3.45 1.32 4.95L2 22l5.25-1.38a9.9 9.9 0 0 0 4.79 1.22h.01c5.46 0 9.91-4.45 9.91-9.91C21.96 6.45 17.5 2 12.04 2Zm5.8 14.12c-.24.68-1.42 1.31-1.95 1.36-.5.05-.96.23-3.24-.68-2.72-1.08-4.44-3.87-4.58-4.05-.13-.18-1.09-1.46-1.09-2.78 0-1.32.69-1.97.94-2.24a.98.98 0 0 1 .71-.33c.18 0 .35 0 .51.01.16.01.38-.06.6.46.23.55.77 1.9.84 2.04.07.14.11.3.02.48-.09.18-.14.29-.27.45-.13.16-.28.35-.4.47-.13.13-.27.28-.12.54.15.27.66 1.09 1.42 1.76.97.87 1.79 1.14 2.05 1.27.26.13.41.11.56-.07.15-.18.65-.76.82-1.02.17-.26.34-.22.58-.13.23.09 1.5.71 1.75.84.26.13.43.2.5.31.06.11.06.64-.18 1.31Z" />
    </svg>
  );
}

const registro = {
  documento: IconoDocumento,
  conversacion: IconoConversacion,
  renovar: IconoRenovar,
  reportar: IconoReportar,
  escudo: IconoEscudo,
} as const;

export type NombreIcono = keyof typeof registro;

export function Icono({ nombre, className }: { nombre: string; className?: string }) {
  const Componente = registro[nombre as NombreIcono] ?? IconoEscudo;
  return <Componente className={className} />;
}
