<template>
  <div class="grid grid-cols-1 lg:grid-cols-5 gap-6">

    <!-- ── Formulario ── -->
    <div class="lg:col-span-3 space-y-4">
      <div class="bg-white rounded-2xl border border-gray-100 shadow-sm overflow-hidden">
        <div class="px-5 py-4 border-b border-gray-100">
          <h4 class="font-bold text-gray-800">{{ editandoId ? 'Editar aviso' : 'Nuevo aviso' }}</h4>
          <p class="text-xs text-gray-400 mt-0.5">
            Se muestra al cliente al entrar a la app, hasta que lo descarte o lo apagues.
          </p>
        </div>

        <div class="p-5 space-y-4">
          <div>
            <label class="block text-xs font-bold text-gray-500 uppercase tracking-widest mb-1.5">Título</label>
            <input v-model="form.titulo" type="text" maxlength="120" placeholder="Promo de septiembre"
              class="w-full text-sm border border-gray-300 rounded-xl px-3 py-2.5 focus:ring-2 focus:ring-red-500 focus:border-red-500 outline-none">
          </div>

          <div>
            <label class="block text-xs font-bold text-gray-500 uppercase tracking-widest mb-1.5">Mensaje</label>
            <textarea v-model="form.cuerpo" rows="4" maxlength="1000"
              placeholder="Trae un amigo y los dos entrenan gratis el sábado."
              class="w-full text-sm border border-gray-300 rounded-xl px-3 py-2.5 focus:ring-2 focus:ring-red-500 focus:border-red-500 outline-none resize-y leading-relaxed"></textarea>
            <p class="text-xs text-gray-400 mt-1">{{ (form.cuerpo || '').length }} / 1000</p>
          </div>

          <!-- Botón: los dos campos van juntos o no va ninguno. Un texto sin destino no
               se puede dibujar y un destino sin texto no se puede rotular. -->
          <div class="grid grid-cols-1 sm:grid-cols-2 gap-3">
            <div>
              <label class="block text-xs font-bold text-gray-500 uppercase tracking-widest mb-1.5">
                Botón <span class="font-semibold normal-case tracking-normal text-gray-300">(opcional)</span>
              </label>
              <input v-model="form.boton_texto" type="text" maxlength="40" placeholder="Ver planes"
                class="w-full text-sm border border-gray-300 rounded-xl px-3 py-2.5 focus:ring-2 focus:ring-red-500 focus:border-red-500 outline-none">
            </div>
            <div>
              <label class="block text-xs font-bold text-gray-500 uppercase tracking-widest mb-1.5">A dónde lleva</label>
              <input v-model="form.boton_url" type="text" maxlength="300" placeholder="/planes"
                class="w-full text-sm border border-gray-300 rounded-xl px-3 py-2.5 focus:ring-2 focus:ring-red-500 focus:border-red-500 outline-none">
            </div>
          </div>
          <div class="flex flex-wrap gap-2 -mt-1">
            <span class="text-xs text-gray-400">Destinos comunes:</span>
            <button v-for="d in DESTINOS" :key="d.url" type="button" @click="usarDestino(d)"
              class="text-xs font-semibold px-2 py-1 rounded-lg border border-gray-200 text-gray-600 hover:border-red-300 hover:text-red-600 transition-colors">
              {{ d.label }}
            </button>
          </div>

          <div class="grid grid-cols-1 sm:grid-cols-2 gap-3 pt-1">
            <div>
              <label class="block text-xs font-bold text-gray-500 uppercase tracking-widest mb-1.5">
                Se apaga el <span class="font-semibold normal-case tracking-normal text-gray-300">(opcional)</span>
              </label>
              <input v-model="form.hasta" type="date" :min="hoyISO()"
                class="w-full text-sm border border-gray-300 rounded-xl px-3 py-2.5 focus:ring-2 focus:ring-red-500 focus:border-red-500 outline-none">
            </div>
            <div class="flex items-end">
              <label class="flex items-center gap-2.5 cursor-pointer select-none pb-2.5">
                <input type="checkbox" v-model="form.activo"
                  class="h-4 w-4 rounded border-gray-300 text-red-600 focus:ring-red-500 cursor-pointer">
                <span class="text-sm font-semibold text-gray-600">Publicarlo ahora</span>
              </label>
            </div>
          </div>

          <!-- Publicar apaga el que esté en el aire, y hay que decirlo antes: es la
               regla que hace que un solo aviso llegue al cliente, y desde el formulario
               no se ve. -->
          <p v-if="form.activo && vigente && vigente.id !== editandoId"
            class="text-xs text-amber-700 bg-amber-50 border border-amber-200 rounded-xl px-3 py-2">
            Al publicarlo se apaga <strong>{{ vigente.titulo }}</strong>, que es el que se está
            mostrando ahora. Solo se muestra un aviso a la vez.
          </p>

          <p v-if="error" class="text-xs text-red-600">{{ error }}</p>

          <div class="flex flex-wrap items-center gap-2 pt-1">
            <button @click="guardar" :disabled="!puedeGuardar || guardando"
              class="bg-red-600 hover:bg-red-700 disabled:opacity-40 disabled:hover:bg-red-600 text-white font-bold text-sm py-2 px-4 rounded-lg shadow-sm transition-colors">
              {{ guardando ? 'Guardando…' : (editandoId ? 'Guardar cambios' : 'Crear aviso') }}
            </button>
            <button v-if="editandoId" @click="limpiar"
              class="text-sm font-semibold text-gray-500 hover:text-gray-800 py-2 px-3 transition-colors">
              Cancelar
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- ── Vista previa + historial ── -->
    <div class="lg:col-span-2 space-y-4">

      <!-- Lo que va a ver el cliente, con la misma forma que el modal real: es un
           cartel que le llega a todos a la vez, así que conviene verlo antes. -->
      <div>
        <p class="text-xs font-bold text-gray-500 uppercase tracking-widest mb-2">Así lo va a ver</p>
        <div class="rounded-2xl overflow-hidden shadow-sm border border-gray-100 bg-white">
          <div class="h-1.5 bg-red-600"></div>
          <div class="p-5">
            <h3 class="text-lg font-extrabold text-gray-900 leading-tight">
              {{ form.titulo || 'Título del aviso' }}
            </h3>
            <p class="text-sm text-gray-600 leading-relaxed whitespace-pre-line mt-2">
              {{ form.cuerpo || 'Acá va el mensaje que le llega al cliente.' }}
            </p>
            <div v-if="form.boton_texto && form.boton_url"
              class="mt-4 text-center bg-red-600 text-white font-bold py-2.5 px-4 rounded-xl text-sm">
              {{ form.boton_texto }}
            </div>
          </div>
          <div class="px-5 py-3 bg-gray-50 border-t border-gray-100 text-xs text-gray-400">
            ☐ No volver a mostrar este aviso
          </div>
        </div>
      </div>

      <!-- Historial -->
      <div class="bg-white rounded-2xl border border-gray-100 shadow-sm overflow-hidden">
        <div class="px-5 py-3 border-b border-gray-100">
          <h4 class="text-xs font-bold text-gray-500 uppercase tracking-widest">Avisos</h4>
        </div>

        <div v-if="cargando" class="p-5 space-y-2">
          <div v-for="i in 2" :key="i" class="h-12 bg-gray-100 rounded-xl animate-pulse"></div>
        </div>
        <p v-else-if="avisos.length === 0" class="px-5 py-8 text-center text-sm text-gray-400">
          Todavía no creaste ningún aviso.
        </p>

        <ul v-else class="divide-y divide-gray-100">
          <li v-for="a in avisos" :key="a.id" class="px-5 py-3">
            <div class="flex items-start justify-between gap-2">
              <div class="min-w-0">
                <p class="text-sm font-semibold text-gray-800 truncate">{{ a.titulo }}</p>
                <p class="text-xs text-gray-400 mt-0.5">
                  <span v-if="a.activo && !a.vencido" class="text-emerald-600 font-bold">En el aire</span>
                  <span v-else-if="a.vencido" class="text-gray-400">Vencido el {{ formatearFecha(a.hasta) }}</span>
                  <span v-else>Apagado</span>
                  <template v-if="a.descartes"> · {{ a.descartes }} lo descartaron</template>
                </p>
              </div>
              <div class="flex items-center gap-1 flex-shrink-0">
                <button @click="editar(a)" title="Editar"
                  class="p-1.5 rounded-lg text-gray-400 hover:text-gray-700 hover:bg-gray-100 transition-colors">
                  <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                    <path stroke-linecap="round" stroke-linejoin="round" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                  </svg>
                </button>
                <button @click="alternar(a)" :title="a.activo ? 'Apagar' : 'Publicar'"
                  class="p-1.5 rounded-lg text-gray-400 hover:text-gray-700 hover:bg-gray-100 transition-colors">
                  <svg v-if="a.activo" xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                    <path stroke-linecap="round" stroke-linejoin="round" d="M13.875 18.825A10.05 10.05 0 0112 19c-4.478 0-8.268-2.943-9.543-7a9.97 9.97 0 011.563-3.029m5.858.908a3 3 0 114.243 4.243M9.878 9.878l4.242 4.242M9.88 9.88l-3.29-3.29m7.532 7.532l3.29 3.29M3 3l3.59 3.59m0 0A9.953 9.953 0 0112 5c4.478 0 8.268 2.943 9.543 7a10.025 10.025 0 01-4.132 5.411m0 0L21 21" />
                  </svg>
                  <svg v-else xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                    <path stroke-linecap="round" stroke-linejoin="round" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                    <path stroke-linecap="round" stroke-linejoin="round" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
                  </svg>
                </button>
                <button @click="eliminar(a)" title="Eliminar"
                  class="p-1.5 rounded-lg text-gray-400 hover:text-red-600 hover:bg-red-50 transition-colors">
                  <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                    <path stroke-linecap="round" stroke-linejoin="round" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                  </svg>
                </button>
              </div>
            </div>
          </li>
        </ul>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import api from '../api'
import { hoyISO, formatearFecha } from '../lib/fechas'

// Atajos para no tener que recordar las rutas de memoria. Son las dos pantallas a las
// que tiene sentido mandar a un cliente desde un aviso.
const DESTINOS = [
  { label: 'Planes', url: '/planes', texto: 'Ver planes' },
  { label: 'Tienda', url: '/tienda', texto: 'Ver la tienda' },
]

const avisos = ref([])
const cargando = ref(true)
const guardando = ref(false)
const error = ref('')
const editandoId = ref(null)

const VACIO = { titulo: '', cuerpo: '', boton_texto: '', boton_url: '', activo: true, hasta: '' }
const form = reactive({ ...VACIO })

/** El que hoy le llega al cliente. Alimenta el aviso de "al publicar se apaga X". */
const vigente = computed(() => avisos.value.find(a => a.activo && !a.vencido) || null)

const puedeGuardar = computed(() => form.titulo.trim() && form.cuerpo.trim())

function usarDestino(d) {
  form.boton_url = d.url
  if (!form.boton_texto.trim()) form.boton_texto = d.texto
}

function limpiar() {
  Object.assign(form, VACIO)
  editandoId.value = null
  error.value = ''
}

function editar(a) {
  editandoId.value = a.id
  Object.assign(form, {
    titulo: a.titulo,
    cuerpo: a.cuerpo,
    boton_texto: a.boton_texto || '',
    boton_url: a.boton_url || '',
    activo: a.activo,
    hasta: a.hasta || '',
  })
  error.value = ''
  window.scrollTo({ top: 0, behavior: 'smooth' })
}

async function cargar() {
  cargando.value = true
  try {
    avisos.value = (await api.get('/avisos/')).data
  } catch (e) {
    error.value = 'No se pudieron cargar los avisos.'
  } finally {
    cargando.value = false
  }
}

function payload() {
  return {
    titulo: form.titulo.trim(),
    cuerpo: form.cuerpo.trim(),
    // Cadena vacía → null: el backend distingue "sin botón" de "botón sin rótulo", y un
    // "" viajando como texto dibujaría un botón en blanco.
    boton_texto: form.boton_texto.trim() || null,
    boton_url: form.boton_url.trim() || null,
    activo: form.activo,
    hasta: form.hasta || null,
  }
}

async function guardar() {
  guardando.value = true
  error.value = ''
  try {
    if (editandoId.value) await api.patch(`/avisos/${editandoId.value}`, payload())
    else await api.post('/avisos/', payload())
    limpiar()
    await cargar()
  } catch (e) {
    error.value = detalle(e) || 'No se pudo guardar el aviso.'
  } finally {
    guardando.value = false
  }
}

async function alternar(a) {
  try {
    await api.patch(`/avisos/${a.id}`, { activo: !a.activo })
    await cargar()
  } catch (e) {
    error.value = detalle(e) || 'No se pudo cambiar el estado.'
  }
}

async function eliminar(a) {
  if (!confirm(`¿Eliminar el aviso "${a.titulo}"?`)) return
  try {
    await api.delete(`/avisos/${a.id}`)
    if (editandoId.value === a.id) limpiar()
    await cargar()
  } catch (e) {
    error.value = detalle(e) || 'No se pudo eliminar.'
  }
}

/** El 422 de Pydantic trae el detalle como lista de objetos, no como string: mostrarlo
 *  crudo dejaría "[object Object]" en pantalla. */
function detalle(e) {
  const d = e.response?.data?.detail
  if (typeof d === 'string') return d
  if (Array.isArray(d)) return d.map(x => x.msg).join('. ')
  return ''
}

onMounted(cargar)
</script>
