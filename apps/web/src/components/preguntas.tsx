import { preguntas } from "@/content/site";

/**
 * FAQ (§4).
 *
 * Built on `<details>`, so it works before JavaScript loads, is keyboard
 * accessible for free, and its answers are in the HTML for search engines.
 */
export function ListaPreguntas() {
  return (
    <div className="divide-y divide-borde overflow-hidden rounded-2xl border border-borde bg-superficie">
      {preguntas.map((item) => (
        <details key={item.pregunta} className="group p-6">
          <summary className="flex cursor-pointer list-none items-start justify-between gap-4 font-medium">
            {item.pregunta}
            <span
              aria-hidden="true"
              className="mt-1 shrink-0 text-suave transition-transform group-open:rotate-45"
            >
              <svg className="h-5 w-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.8}>
                <path d="M12 5v14M5 12h14" strokeLinecap="round" />
              </svg>
            </span>
          </summary>
          <p className="mt-3 max-w-3xl text-sm leading-relaxed text-suave">
            {item.respuesta}
          </p>
        </details>
      ))}
    </div>
  );
}
