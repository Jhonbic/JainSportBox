<!-- Los cinco textos de WhatsApp. Era la vista `/mensajes` entera; se extrajo a
     componente al sumarle la pestaña de avisos, para que el shell quede con el
     encabezado y las pestañas y nada más. -->
<template>
  <div>

    <!-- Skeleton -->
    <div v-if="cargando" class="space-y-4">
      <div v-for="i in 3" :key="i" class="bg-white rounded-2xl border border-gray-100 h-56 animate-pulse"></div>
    </div>

    <div v-else class="space-y-8">
      <section v-for="grupo in grupos" :key="grupo.nombre">
        <h3 class="text-xs font-bold text-gray-500 uppercase tracking-widest mb-3">{{ grupo.nombre }}</h3>

        <div class="space-y-4">
          <div v-for="p in grupo.plantillas" :key="p.clave"
            class="bg-white rounded-2xl border border-gray-100 shadow-sm overflow-hidden">

            <!-- Encabezado de la plantilla -->
            <div class="px-5 py-4 border-b border-gray-100 flex items-start justify-between gap-3">
              <div>
                <h4 class="font-bold text-gray-800">{{ p.titulo }}</h4>
                <p class="text-xs text-gray-400 mt-0.5">{{ p.cuando }}</p>
              </div>
              <span v-if="esPersonalizado(p.clave)"
                class="text-[10px] font-bold uppercase tracking-widest bg-gray-100 text-gray-600 px-2 py-1 rounded-full flex-shrink-0">
                Personalizado
              </span>
            </div>

            <div class="p-5 space-y-3">

              <!-- El aviso es CONDICIONAL: solo si el envío automático está prendido.
                   Con la API de Meta sin configurar —que es el caso mientras nadie cargue
                   las credenciales— advertir sobre un envío que no ocurre es peor que no
                   decir nada: manda a buscar en WhatsApp Manager un mensaje que no existe.
                   Cuando se prenda, el aviso vuelve solo.

                   Va en la tarjeta de `vence` y no arriba de todo porque es la única
                   plantilla a la que le aplica; un cartel general haría dudar de las
                   otras cuatro. -->
              <div v-if="p.clave === 'vence' && envioAutomatico"
                class="flex gap-2 bg-amber-50 border border-amber-200 rounded-xl px-3 py-2.5">
                <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4 text-amber-600 flex-shrink-0 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M12 9v2m0 4h.01M5.07 19h13.86a2 2 0 001.74-2.99l-6.93-12a2 2 0 00-3.48 0l-6.93 12A2 2 0 005.07 19z"/>
                </svg>
                <p class="text-xs text-amber-800 leading-relaxed">
                  Esto cambia el mensaje del botón <strong>Recordar</strong>, el que se abre a mano.
                  El recordatorio que sale solo a las 9:10 usa una plantilla aprobada por Meta que
                  se edita desde WhatsApp Manager, no desde acá.
                </p>
              </div>
              <p v-else-if="p.clave === 'vence'" class="text-xs text-gray-400">
                El envío automático de recordatorios está apagado, así que este es el único
                texto que le llega al cliente.
              </p>

              <textarea
                :ref="el => { if (el) areas[p.clave] = el }"
                v-model="borradores[p.clave]"
                rows="4"
                class="w-full text-sm border border-gray-300 rounded-xl px-3 py-2.5 focus:ring-2 focus:ring-red-500 focus:border-red-500 outline-none resize-y leading-relaxed"
                placeholder="Escribe el mensaje…"></textarea>

              <!-- Variables disponibles: se insertan en el cursor. Escribirlas a mano
                   invita al typo, y un {nombree} llega literal al WhatsApp del socio. -->
              <div class="flex flex-wrap items-center gap-2">
                <span class="text-xs text-gray-400">Insertar:</span>
                <button v-for="v in p.vars" :key="v" type="button" @click="insertarVar(p.clave, v)"
                  :title="AYUDA_VARS[v]"
                  class="text-xs font-mono font-semibold px-2 py-1 rounded-lg border border-gray-200 text-gray-600 hover:border-red-300 hover:text-red-600 transition-colors">
                  {{ '{' + v + '}' }}
                </button>
              </div>

              <!-- Vista previa: con las variables ya resueltas y el *negrita* de WhatsApp
                   aplicado, que es como lo va a ver el socio. -->
              <div class="bg-gray-50 border border-gray-100 rounded-xl p-3">
                <p class="text-[10px] font-bold text-gray-400 uppercase tracking-widest mb-1.5">Vista previa</p>
                <p class="text-sm text-gray-800 leading-relaxed whitespace-pre-wrap" v-html="preview(p)"></p>
              </div>

              <p v-if="desconocidas(p).length" class="text-xs text-red-600">
                No conozco {{ listaDesconocidas(p) }} —
                va a llegar así, tal cual, al WhatsApp del cliente.
              </p>
              <p v-if="errores[p.clave]" class="text-xs text-red-600">{{ errores[p.clave] }}</p>

              <!-- Acciones -->
              <div class="flex flex-wrap items-center gap-2 pt-1">
                <button @click="guardar(p)" :disabled="!hayCambios(p.clave) || guardando[p.clave]"
                  class="bg-red-600 hover:bg-red-700 disabled:opacity-40 disabled:hover:bg-red-600 text-white font-bold text-sm py-2 px-4 rounded-lg shadow-sm transition-colors">
                  {{ guardando[p.clave] ? 'Guardando…' : 'Guardar' }}
                </button>
                <button v-if="hayCambios(p.clave)" @click="descartar(p.clave)"
                  class="text-sm font-semibold text-gray-500 hover:text-gray-800 py-2 px-3 transition-colors">
                  Descartar
                </button>
                <button v-if="esPersonalizado(p.clave)" @click="restaurar(p)" :disabled="guardando[p.clave]"
                  class="ml-auto text-sm font-semibold text-gray-500 hover:text-red-600 py-2 px-3 transition-colors">
                  Restaurar el original
                </button>
                <span v-if="guardado[p.clave]" class="text-xs font-semibold text-emerald-600">Guardado ✓</span>
              </div>
            </div>
          </div>
        </div>
      </section>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, nextTick } from 'vue'
import api from '../api'
import { PLANTILLAS, AYUDA_VARS, EJEMPLO, DEFAULTS, renderMensaje, varsDesconocidas } from '../lib/mensajes'
import { useMensajes, cargarMensajes, actualizarLocal } from '../composables/useMensajes'

const { overrides, envioAutomatico, textoDe } = useMensajes()

const cargando = ref(true)
const borradores = reactive({})
const guardando = reactive({})
const guardado = reactive({})
const errores = reactive({})
const areas = {}

const grupos = computed(() => {
  const orden = []
  for (const p of PLANTILLAS) {
    let g = orden.find(x => x.nombre === p.grupo)
    if (!g) { g = { nombre: p.grupo, plantillas: [] }; orden.push(g) }
    g.plantillas.push(p)
  }
  return orden
})

const esPersonalizado = (clave) => clave in overrides.value
const hayCambios = (clave) => (borradores[clave] ?? '') !== textoDe(clave)

const desconocidas = (p) => varsDesconocidas(borradores[p.clave], p.vars)
// Armar la lista en el script y no en el template: un `{${v}}` dentro de las llaves
// dobles le cierra la interpolación a Vue y el archivo no compila.
const listaDesconocidas = (p) => desconocidas(p).map(v => '{' + v + '}').join(', ')

/** El `*negrita*` de WhatsApp, para que la previa se parezca a lo que le llega al socio.
 *  El escape va ANTES de meter el `<strong>`: el texto lo escribe el admin, pero va a
 *  `v-html` y un `<script>` tipeado ahí no tiene por qué ejecutarse. */
function preview(p) {
  const texto = renderMensaje(borradores[p.clave] ?? '', EJEMPLO)
  const escapado = texto
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
  return escapado.replace(/\*([^*\n]+)\*/g, '<strong>$1</strong>')
}

function insertarVar(clave, v) {
  const area = areas[clave]
  const marca = `{${v}}`
  if (!area) { borradores[clave] = (borradores[clave] || '') + marca; return }
  const ini = area.selectionStart ?? borradores[clave].length
  const fin = area.selectionEnd ?? ini
  const texto = borradores[clave] || ''
  borradores[clave] = texto.slice(0, ini) + marca + texto.slice(fin)
  // El cursor queda después de lo insertado; si no, seguir escribiendo lo pisa.
  nextTick(() => {
    area.focus()
    area.setSelectionRange(ini + marca.length, ini + marca.length)
  })
}

function descartar(clave) {
  borradores[clave] = textoDe(clave)
  errores[clave] = ''
}

async function guardar(p) {
  const texto = (borradores[p.clave] || '').trim()
  if (!texto) { errores[p.clave] = 'El mensaje no puede quedar vacío.'; return }
  guardando[p.clave] = true
  errores[p.clave] = ''
  try {
    await api.put(`/mensajes/${p.clave}`, { texto })
    actualizarLocal(p.clave, texto)
    borradores[p.clave] = texto
    avisarGuardado(p.clave)
  } catch (e) {
    errores[p.clave] = e.response?.data?.detail || 'No se pudo guardar.'
  } finally {
    guardando[p.clave] = false
  }
}

async function restaurar(p) {
  guardando[p.clave] = true
  errores[p.clave] = ''
  try {
    await api.delete(`/mensajes/${p.clave}`)
    actualizarLocal(p.clave, null)
    borradores[p.clave] = DEFAULTS[p.clave]
    avisarGuardado(p.clave)
  } catch (e) {
    errores[p.clave] = e.response?.data?.detail || 'No se pudo restaurar.'
  } finally {
    guardando[p.clave] = false
  }
}

function avisarGuardado(clave) {
  guardado[clave] = true
  setTimeout(() => { guardado[clave] = false }, 2500)
}

onMounted(async () => {
  // `forzar`: el cache de módulo puede venir de otra pantalla y acá se está por editar.
  await cargarMensajes({ forzar: true })
  for (const p of PLANTILLAS) borradores[p.clave] = textoDe(p.clave)
  cargando.value = false
})
</script>
