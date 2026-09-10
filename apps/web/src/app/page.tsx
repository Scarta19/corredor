import { RejillaAcciones } from "@/components/acciones";
import { Cierre } from "@/components/cierre";
import { ListaPreguntas } from "@/components/preguntas";
import { RejillaRamos } from "@/components/ramos";
import { Boton, Contenedor, Seccion, TituloSeccion } from "@/components/ui";
import { pasos, propuestas } from "@/content/site";
import { listarRamos } from "@/lib/api";
import { config, whatsappUrl } from "@/lib/config";

export default async function Inicio() {
  const ramos = await listarRamos();

  return (
    <>
      {/* Hero */}
      <section className="relative overflow-hidden border-b border-borde">
        <div
          aria-hidden="true"
          className="pointer-events-none absolute inset-0 bg-[radial-gradient(60%_60%_at_50%_0%,var(--color-tinta-100)_0%,transparent_70%)] dark:bg-[radial-gradient(60%_60%_at_50%_0%,var(--color-tinta-950)_0%,transparent_70%)]"
        />
        <Contenedor className="relative py-20 sm:py-28">
          <div className="max-w-3xl">
            <p className="text-sm font-semibold uppercase tracking-widest text-tinta-600 dark:text-tinta-400">
              {config.brand.eslogan}
            </p>
            <h1 className="mt-4 text-4xl font-semibold tracking-tight sm:text-6xl">
              Un seguro bien elegido, y alguien que responde cuando lo
              necesitas.
            </h1>
            <p className="mt-6 max-w-2xl text-lg leading-relaxed text-suave">
              Comparamos varias aseguradoras, te explicamos las diferencias en
              español claro y nos quedamos contigo después de la firma: para la
              renovación, para un cambio, y sobre todo para el siniestro.
            </p>
            <div className="mt-8 flex flex-wrap gap-3">
              <Boton href="/cotizar" className="px-6 py-3.5 text-base">
                Solicitar cotización
              </Boton>
              <Boton
                href={whatsappUrl(
                  `Hola ${config.brand.corto}, quiero hablar con un asesor.`,
                )}
                variante="secundario"
                className="px-6 py-3.5 text-base"
              >
                Hablar con un asesor
              </Boton>
            </div>
            <p className="mt-5 text-sm text-suave">
              Cotizar es gratis y no te compromete · Respondemos el mismo día
              hábil
            </p>
          </div>
        </Contenedor>
      </section>

      {/* §4 — the four calls to action */}
      <Seccion className="pt-14 sm:pt-16">
        <h2 className="sr-only">¿Qué necesitas hacer hoy?</h2>
        <RejillaAcciones />
      </Seccion>

      {/* §4 — productos / ramos */}
      <Seccion id="seguros" className="pt-0">
        <TituloSeccion
          ancla="Nuestros seguros"
          titulo="Cobertura para lo que ya construiste"
          descripcion="Para personas y para empresas. Elige un ramo y responde solo las preguntas que ese seguro necesita."
        />
        <div className="mt-10">
          <RejillaRamos ramos={ramos} />
        </div>
      </Seccion>

      {/* How it works — the §6 flow, told to the visitor */}
      <section className="border-y border-borde bg-superficie">
        <Contenedor className="py-16 sm:py-24">
          <TituloSeccion
            ancla="Cómo funciona"
            titulo="Cuatro pasos, sin vueltas"
            descripcion="Así se ve el proceso desde tu lado."
          />
          <ol className="mt-12 grid gap-8 sm:grid-cols-2 lg:grid-cols-4">
            {pasos.map((paso) => (
              <li key={paso.numero} className="relative">
                <span className="grid h-10 w-10 place-items-center rounded-full bg-tinta-700 text-sm font-semibold text-white">
                  {paso.numero}
                </span>
                <h3 className="mt-4 text-base font-semibold">{paso.titulo}</h3>
                <p className="mt-2 text-sm leading-relaxed text-suave">
                  {paso.detalle}
                </p>
              </li>
            ))}
          </ol>
        </Contenedor>
      </section>

      {/* §4 — ¿Por qué elegirnos? */}
      <Seccion>
        <TituloSeccion
          ancla="¿Por qué elegirnos?"
          titulo="Lo que cambia al tener un intermediario"
          descripcion="No emitimos pólizas: negociamos con quienes las emiten, del lado del cliente."
        />
        <div className="mt-12 grid gap-x-10 gap-y-10 sm:grid-cols-2">
          {propuestas.map((propuesta) => (
            <div key={propuesta.titulo} className="border-l-2 border-tinta-600 pl-5">
              <h3 className="text-lg font-semibold">{propuesta.titulo}</h3>
              <p className="mt-2 leading-relaxed text-suave">
                {propuesta.detalle}
              </p>
            </div>
          ))}
        </div>
      </Seccion>

      {/* §4 — preguntas frecuentes */}
      <Seccion id="preguntas" className="pt-0">
        <TituloSeccion
          ancla="Preguntas frecuentes"
          titulo="Lo que más nos preguntan"
        />
        <div className="mt-10">
          <ListaPreguntas />
        </div>
      </Seccion>

      <Cierre />
    </>
  );
}
