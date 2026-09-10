import { BarraLateral } from "@/components/barra-lateral";
import { usuarioActual } from "@/lib/sesion";

/**
 * Every page under this layout requires a session.
 *
 * `usuarioActual` redirects to /login when the token is missing, expired or
 * belongs to a deactivated account — so the guard is the data fetch itself
 * rather than a separate check that could drift out of step with it.
 */
export default async function PanelLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const usuario = await usuarioActual();

  return (
    <div className="flex min-h-dvh flex-col lg:flex-row">
      <BarraLateral usuario={usuario} />
      <main className="flex-1 overflow-x-hidden px-5 py-8 sm:px-8">
        <div className="mx-auto max-w-6xl">{children}</div>
      </main>
    </div>
  );
}
