import { RejillaAcciones } from "@/components/acciones";
import { Seccion, TituloSeccion } from "@/components/ui";

export default function NoEncontrado() {
  return (
    <Seccion>
      <TituloSeccion
        ancla="Error 404"
        titulo="Esta página no existe"
        descripcion="Puede que el enlace esté roto o que la página haya cambiado de sitio. Estas son las cosas que la mayoría viene a hacer:"
      />
      <div className="mt-10">
        <RejillaAcciones />
      </div>
    </Seccion>
  );
}
