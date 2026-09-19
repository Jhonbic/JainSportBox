<template>
  <div class="animate-fade-in-up">

    <!-- Header -->
    <div class="mb-6">
      <h2 class="text-3xl font-black text-gray-900 tracking-tight">Mis Marcas</h2>
      <p class="text-gray-500 mt-1">Récords personales · Selecciona un ejercicio para ver y registrar tu marca</p>
    </div>

    <!-- Buscador -->
    <div class="mb-5 relative max-w-sm">
      <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4 absolute left-3 top-3 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
      </svg>
      <input
        v-model="busqueda"
        type="text"
        placeholder="Buscar ejercicio..."
        class="w-full pl-9 pr-4 py-2.5 border border-gray-200 rounded-lg focus:ring-2 focus:ring-red-500 outline-none text-sm"
      />
    </div>

    <!-- Loading: filas, para que no salte el layout al llegar la tabla -->
    <div v-if="cargando" class="bg-white rounded-xl border border-gray-100 shadow-sm p-4 space-y-3">
      <div v-for="i in 6" :key="i" class="h-12 bg-gray-100 rounded-lg animate-pulse" />
    </div>

    <!-- Vacío. Son dos casos distintos y conviene separarlos: buscar algo que no
         está no es lo mismo que un catálogo sin ningún ejercicio medible, que es
         una tarea pendiente del staff y no un error del socio. -->
    <div
      v-else-if="ejerciciosFiltrados.length === 0"
      class="bg-gray-50 border-2 border-dashed border-gray-200 rounded-2xl p-14 text-center"
    >
      <svg xmlns="http://www.w3.org/2000/svg" class="h-14 w-14 mx-auto text-gray-300 mb-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M13 10V3L4 14h7v7l9-11h-7z" />
      </svg>
      <template v-if="catalogo.length">
        <p class="text-gray-500 font-medium">No se encontraron ejercicios.</p>
      </template>
      <template v-else>
        <p class="text-gray-500 font-medium">Todavía no hay ejercicios para registrar marcas.</p>
        <RouterLink v-if="canManage" to="/ejercicios"
          class="inline-block mt-3 text-sm font-semibold text-red-600 hover:text-red-700">
          Configurarlos en el catálogo →
        </RouterLink>
        <p v-else class="text-sm text-gray-400 mt-1">Pídele a tu coach que los configure.</p>
      </template>
    </div>

    <!-- Listado: cards en móvil, tabla en desktop (mismo patrón que Ejercicios) -->
    <template v-else>

      <!-- ── Cards (móvil) ── -->
      <div class="sm:hidden space-y-3">
        <RouterLink
          v-for="ej in ejerciciosFiltrados"
          :key="ej.nombre"
          :to="{ name: 'MarcasEjercicio', params: { ejercicio: ej.nombre } }"
          class="block bg-white rounded-xl border border-gray-100 shadow-sm p-4"
        >
          <div class="flex items-center justify-between gap-3">
            <div class="min-w-0 flex-1">
              <h3 class="font-semibold text-gray-900 truncate">{{ ej.nombre }}</h3>
              <p v-if="resumen.get(ej.nombre)" class="text-xs text-gray-500 mt-0.5">
                Última: {{ formatFecha(resumen.get(ej.nombre).ultima) }}
              </p>
              <p v-else class="text-xs text-gray-400 mt-0.5">Sin registros · toca para empezar</p>
            </div>
            <p v-if="resumen.get(ej.nombre)" class="shrink-0 text-lg font-black text-gray-900 whitespace-nowrap">
              {{ resumen.get(ej.nombre).valor }}<span class="text-xs font-semibold text-gray-400 ml-1">{{ resumen.get(ej.nombre).unidad }}</span>
            </p>
            <span v-else class="shrink-0 text-lg text-gray-300">—</span>
          </div>
          <a v-if="ej.video_url" :href="ej.video_url" target="_blank" rel="noopener noreferrer"
            @click.stop.prevent="abrirVideo(ej.video_url)"
            class="mt-3 inline-flex items-center gap-1.5 text-sm font-semibold text-red-600">
            <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="currentColor" viewBox="0 0 24 24">
              <path d="M8 5v14l11-7z" />
            </svg>
            Ver video
          </a>
        </RouterLink>
      </div>

      <!-- ── Tabla (desktop) ── -->
      <div class="hidden sm:block bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden">
        <div class="overflow-x-auto">
          <table class="min-w-full divide-y divide-gray-200">
            <thead class="bg-gray-50">
              <tr>
                <th class="px-6 py-4 text-left text-xs font-bold text-gray-500 uppercase tracking-wider">Ejercicio</th>
                <th class="px-6 py-4 text-left text-xs font-bold text-gray-500 uppercase tracking-wider">Mejor marca</th>
                <th class="px-6 py-4 text-left text-xs font-bold text-gray-500 uppercase tracking-wider">Video</th>
                <th class="px-6 py-4 text-left text-xs font-bold text-gray-500 uppercase tracking-wider">Última</th>
              </tr>
            </thead>
            <tbody class="bg-white divide-y divide-gray-100">
              <!-- La fila entera es clicable, pero el nombre va como RouterLink real:
                   así sigue siendo navegable por teclado y abrible en pestaña nueva. -->
              <tr
                v-for="ej in ejerciciosFiltrados"
                :key="ej.nombre"
                @click="irA(ej.nombre)"
                class="hover:bg-gray-50 transition-colors group cursor-pointer"
              >
                <td class="px-6 py-4 whitespace-nowrap">
                  <RouterLink
                    :to="{ name: 'MarcasEjercicio', params: { ejercicio: ej.nombre } }"
                    @click.stop
                    class="text-sm font-semibold text-gray-900 group-hover:text-red-600 transition-colors"
                  >{{ ej.nombre }}</RouterLink>
                </td>
                <td class="px-6 py-4 whitespace-nowrap">
                  <span v-if="resumen.get(ej.nombre)" class="text-sm font-bold text-gray-900">
                    {{ resumen.get(ej.nombre).valor }}<span class="font-semibold text-gray-400 ml-1">{{ resumen.get(ej.nombre).unidad }}</span>
                  </span>
                  <span v-else class="text-sm text-gray-300">—</span>
                </td>
                <td class="px-6 py-4 whitespace-nowrap">
                  <!-- @click.stop: la fila entera navega al ejercicio, y sin esto
                       abrir el video dispararía además la navegación. -->
                  <a v-if="ej.video_url" :href="ej.video_url" target="_blank" rel="noopener noreferrer"
                    @click.stop
                    class="inline-flex items-center gap-1.5 text-sm font-semibold text-red-600 hover:text-red-700">
                    <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="currentColor" viewBox="0 0 24 24">
                      <path d="M8 5v14l11-7z" />
                    </svg>
                    Ver
                  </a>
                  <span v-else class="text-sm text-gray-300">—</span>
                </td>
                <td class="px-6 py-4 whitespace-nowrap">
                  <span v-if="resumen.get(ej.nombre)" class="text-sm text-gray-600">{{ formatFecha(resumen.get(ej.nombre).ultima) }}</span>
                  <span v-else class="text-sm text-gray-300">—</span>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

    </template>

  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { RouterLink, useRouter } from 'vue-router'
import api from '../api'
import { usarCatalogoMarcas, cargarCatalogo } from '../lib/catalogoMarcas'
import { useAuth } from '../composables/useAuth'

const router = useRouter()

const marcas    = ref([])
const busqueda  = ref('')
const cargando  = ref(true)
const catalogo  = usarCatalogoMarcas()
const { canManage } = useAuth()

const KG_PER_LB = 2.20462
const toKg = (v, u) => u === 'lbs' ? v / KG_PER_LB : v

const formatFecha = (f) =>
  new Date(f + 'T12:00:00').toLocaleDateString('es-CO', { day: '2-digit', month: 'short', year: 'numeric' })

const ejerciciosFiltrados = computed(() => {
  const q = busqueda.value.trim().toLowerCase()
  if (!q) return catalogo.value
  return catalogo.value.filter(e => e.nombre.toLowerCase().includes(q))
})

/**
 * Un solo recorrido de `marcas` → Map por ejercicio con { valor, unidad, conteo, ultima }.
 * Los ejercicios sin registros no entran al Map (la fila muestra "—").
 */
const resumen = computed(() => {
  const porEjercicio = new Map()
  for (const m of marcas.value) {
    if (!porEjercicio.has(m.ejercicio)) porEjercicio.set(m.ejercicio, [])
    porEjercicio.get(m.ejercicio).push(m)
  }

  const out = new Map()
  for (const ej of catalogo.value) {
    const lista = porEjercicio.get(ej.nombre)
    if (!lista?.length) continue
    out.set(ej.nombre, {
      ...mejorDe(ej.tipo, lista),
      conteo: lista.length,
      ultima: lista.reduce((a, b) => (b.fecha > a ? b.fecha : a), lista[0].fecha),
    })
  }
  return out
})

function mejorDe(tipo, lista) {
  if (tipo === 'reps') {
    const mejor = lista.reduce((a, b) => (b.repeticiones || 0) > (a.repeticiones || 0) ? b : a)
    return { valor: mejor.repeticiones, unidad: 'reps' }
  }

  if (tipo === 'leger') {
    // PR = mayor nivel; desempata por palier
    const mejor = lista.reduce((a, b) => {
      if ((b.nivel || 0) !== (a.nivel || 0)) return (b.nivel || 0) > (a.nivel || 0) ? b : a
      return (b.palier || 0) > (a.palier || 0) ? b : a
    })
    return { valor: `nivel ${mejor.nivel}.${mejor.palier}`, unidad: '' }
  }

  // barra / corporal_lastre → 1RM (normalizado para comparar entre kg y lbs)
  const mejor = lista.reduce((a, b) => toKg(b.rm_calculado, b.unidad) > toKg(a.rm_calculado, a.unidad) ? b : a)
  return { valor: mejor.rm_calculado, unidad: mejor.unidad }
}

const irA = (ejercicio) => router.push({ name: 'MarcasEjercicio', params: { ejercicio } })
// En móvil la card entera es un <RouterLink>, así que un <a> anidado no puede
// navegar solo: el .prevent frena al padre y hay que abrir la pestaña a mano.
const abrirVideo = (url) => window.open(url, '_blank', 'noopener')

async function cargar() {
  cargando.value = true
  try {
    // En paralelo: el catálogo dice QUÉ ejercicios se listan y /marcas/ trae los
    // registros. Esperar a los dos antes de bajar el skeleton evita que la tabla
    // aparezca vacía un instante mientras llega el catálogo.
    const [{ data }] = await Promise.all([api.get('/marcas/'), cargarCatalogo()])
    marcas.value = data
  } finally {
    cargando.value = false
  }
}

onMounted(cargar)
</script>

<style scoped>
.animate-fade-in-up { animation: fadeInUp 0.4s ease-out; }
@keyframes fadeInUp {
  from { opacity: 0; transform: translateY(10px); }
  to   { opacity: 1; transform: translateY(0); }
}
</style>
