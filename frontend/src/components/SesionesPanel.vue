<!-- Panel de sesiones por bloque horario. Vivía en views/SesionesView.vue, que se
     eliminó al mover esta pantalla dentro del Resumen (/dashboard).

     Layout de dos columnas: el calendario del mes a la izquierda manda la selección,
     y las sesiones del día elegido se renderizan a la derecha. Antes había tres modos
     (semana / mes / fecha específica); el calendario mensual los cubre a todos. -->
<template>
  <div class="grid lg:grid-cols-5 gap-6 items-start">

    <!-- ═══════════ COLUMNA IZQUIERDA · CALENDARIO ═══════════ -->
    <div class="lg:col-span-2 lg:sticky lg:top-4">
      <div class="bg-white rounded-2xl border border-gray-100 p-4 shadow-sm">

        <!-- Navegación de mes -->
        <div class="flex items-center justify-between mb-4">
          <button
            @click="cambiarMes(-1)"
            class="p-2 rounded-xl border border-gray-200 hover:border-gray-400 transition-colors">
            <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5 text-gray-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7" />
            </svg>
          </button>
          <h3 class="text-base font-extrabold text-gray-900 capitalize">{{ nombreMesActual }}</h3>
          <button
            @click="cambiarMes(1)"
            :disabled="mesOffset >= 0"
            class="p-2 rounded-xl border border-gray-200 hover:border-gray-400 transition-colors disabled:opacity-30 disabled:cursor-not-allowed">
            <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5 text-gray-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7" />
            </svg>
          </button>
        </div>

        <!-- Skeleton -->
        <div v-if="cargandoMes" class="grid grid-cols-7 gap-1 animate-pulse">
          <div v-for="i in 35" :key="i" class="h-12 bg-gray-100 rounded-xl"></div>
        </div>

        <template v-else>
          <!-- Encabezados días -->
          <div class="grid grid-cols-7 gap-1 mb-2">
            <div
              v-for="h in ['Lun','Mar','Mié','Jue','Vie','Sáb','Dom']"
              :key="h"
              class="text-center text-xs font-bold text-gray-400 py-1 uppercase tracking-wide">
              {{ h }}
            </div>
          </div>
          <!-- Semanas -->
          <div v-for="(semana, si) in semanaMes" :key="si" class="grid grid-cols-7 gap-1 mb-1">
            <div
              v-for="(dia, di) in semana"
              :key="di"
              @click="dia && seleccionarDia(dia.fecha)"
              class="relative flex flex-col items-center justify-center rounded-xl py-1.5 min-h-[52px] transition-all"
              :class="[
                !dia ? 'pointer-events-none' : 'cursor-pointer',
                dia && diaSeleccionado === dia.fecha
                  ? 'bg-red-600 text-white shadow-md'
                  : dia && dia.esHoy
                    ? 'bg-gray-900 text-white'
                    : dia && dia.total > 0
                      ? 'bg-red-50 hover:bg-red-100 text-gray-800'
                      : dia
                        ? 'hover:bg-gray-50 text-gray-400'
                        : ''
              ]">
              <span v-if="dia" class="text-sm font-bold leading-none">{{ dia.numeroDia }}</span>
              <span
                v-if="dia && dia.total > 0"
                class="mt-1 text-xs font-semibold px-1.5 py-0.5 rounded-full leading-none"
                :class="diaSeleccionado === dia.fecha
                  ? 'bg-red-500 text-white'
                  : dia.esHoy
                    ? 'bg-gray-700 text-white'
                    : 'bg-red-200 text-red-700'">
                {{ dia.total }}
              </span>
            </div>
          </div>

          <!-- Total del mes -->
          <p class="text-xs text-gray-400 text-center mt-3 pt-3 border-t border-gray-100">
            {{ totalMes }} {{ totalMes === 1 ? 'asistencia' : 'asistencias' }} este mes
          </p>
        </template>
      </div>

      <p v-if="error" class="mt-3 text-sm text-red-600 font-medium">{{ error }}</p>
    </div>

    <!-- ═══════════ COLUMNA DERECHA · SESIONES DEL DÍA ═══════════ -->
    <div class="lg:col-span-3">

      <div class="flex flex-wrap items-center justify-between gap-3 mb-4">
        <h4 class="font-bold text-gray-700 text-sm uppercase tracking-wide">
          {{ diaSeleccionado ? `Sesiones del ${etiquetaDia}` : 'Sesiones' }}
        </h4>
        <input
          v-if="diaSeleccionado"
          type="text"
          v-model="busqueda"
          placeholder="Buscar por nombre…"
          class="border border-gray-200 rounded-xl px-4 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-red-400 w-full sm:w-64" />
      </div>

      <div v-if="cargandoMes" class="grid grid-cols-1 sm:grid-cols-2 gap-4">
        <div v-for="i in 4" :key="i" class="bg-gray-100 rounded-2xl h-16 animate-pulse"></div>
      </div>

      <template v-else-if="diaSeleccionado">
        <div v-if="bloquesDia.length > 0" class="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <BloqueCard
            v-for="b in bloquesDia"
            :key="b.fecha + '-' + b.hora_inicio"
            :bloque="b"
            :busqueda="busqueda" />
        </div>
        <div v-else class="text-center py-16 text-gray-400">
          <svg xmlns="http://www.w3.org/2000/svg" class="h-10 w-10 mx-auto mb-3 text-gray-300" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
          </svg>
          <p class="font-semibold text-gray-500">
            {{ busqueda ? `Sin resultados para "${busqueda}"` : 'Sin asistencias este día' }}
          </p>
        </div>
      </template>

      <div v-else class="text-center py-16 text-gray-400 text-sm">
        Selecciona un día del calendario para ver sus sesiones
      </div>
    </div>

  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import api from '../api'
import BloqueCard from './BloqueCard.vue'

// ── Estado ──
const bloquesMes       = ref([])   // todos los bloques del mes visible
const diaSeleccionado  = ref('')
const mesOffset        = ref(0)    // 0 = mes actual, -1 = mes anterior, etc.
const busqueda         = ref('')
const cargandoMes      = ref(false)
const error            = ref('')

// ── Helpers de fecha ──
const MESES_LARGO = ['Enero','Febrero','Marzo','Abril','Mayo','Junio','Julio','Agosto','Septiembre','Octubre','Noviembre','Diciembre']

/** "YYYY-MM-DD" del día LOCAL. `toISOString()` da la fecha en UTC, y Bogotá es UTC-5:
 *  de 19:00 en adelante devolvía el día siguiente, así que el calendario pintaba "hoy"
 *  en la celda equivocada justo en el horario de más gente. Peor el último día del mes:
 *  la preselección de `cargarMes` dejaba de reconocer el mes visible y caía en "el
 *  último día con datos". `en-CA` formatea ISO y respeta la zona del navegador — es el
 *  mismo recurso que usa DashboardView para la clave de felicitados. */
function isoHoy() {
  return new Date().toLocaleDateString('en-CA')
}

function getMesInfo(offset) {
  const hoy = new Date()
  const d = new Date(hoy.getFullYear(), hoy.getMonth() + offset, 1)
  return { year: d.getFullYear(), month: d.getMonth() }  // month: 0-indexed
}

const nombreMesActual = computed(() => {
  const { year, month } = getMesInfo(mesOffset.value)
  return `${MESES_LARGO[month]} ${year}`
})

const etiquetaDia = computed(() => diaSeleccionado.value.split('-').reverse().join('/'))

const totalMes = computed(() => bloquesMes.value.reduce((acc, b) => acc + b.total, 0))

const semanaMes = computed(() => {
  const { year, month } = getMesInfo(mesOffset.value)
  const ultimoDia = new Date(year, month + 1, 0).getDate()

  const totales = {}
  for (const b of bloquesMes.value) {
    totales[b.fecha] = (totales[b.fecha] || 0) + b.total
  }

  const hoy = isoHoy()

  // DOW del primer día (Mon=0 … Sun=6)
  let dow = new Date(year, month, 1).getDay()
  dow = dow === 0 ? 6 : dow - 1

  const semanas = []
  let semana = Array(dow).fill(null)

  for (let d = 1; d <= ultimoDia; d++) {
    const f = `${year}-${String(month + 1).padStart(2, '0')}-${String(d).padStart(2, '0')}`
    semana.push({ fecha: f, numeroDia: d, esHoy: f === hoy, total: totales[f] || 0 })
    if (semana.length === 7) { semanas.push(semana); semana = [] }
  }
  if (semana.length) {
    while (semana.length < 7) semana.push(null)
    semanas.push(semana)
  }
  return semanas
})

// ── Bloques del día seleccionado, filtrados por el buscador ──
const bloquesDia = computed(() => {
  if (!diaSeleccionado.value) return []
  const q = busqueda.value.trim().toLowerCase()
  return bloquesMes.value
    .filter(b => b.fecha === diaSeleccionado.value)
    .map(b => ({
      ...b,
      asistentes: q ? b.asistentes.filter(a => a.nombre.toLowerCase().includes(q)) : b.asistentes,
    }))
    .filter(b => b.asistentes.length > 0)
})

// ── Fetch ──
async function cargarMes() {
  const { year, month } = getMesInfo(mesOffset.value)
  const mm = String(month + 1).padStart(2, '0')
  const ultimoDia = new Date(year, month + 1, 0).getDate()
  const desde = `${year}-${mm}-01`
  const hasta = `${year}-${mm}-${String(ultimoDia).padStart(2, '0')}`

  cargandoMes.value = true
  error.value = ''
  try {
    const { data } = await api.get('/asistencia/sesiones-por-bloque', { params: { desde, hasta } })
    bloquesMes.value = data.bloques
    // Preselección: hoy si el mes visible es el actual; si no, el último día con datos.
    const hoy = isoHoy()
    if (hoy.startsWith(`${year}-${mm}`)) {
      diaSeleccionado.value = hoy
    } else {
      diaSeleccionado.value = data.bloques[data.bloques.length - 1]?.fecha || ''
    }
  } catch (e) {
    error.value = e.response?.data?.detail || 'Error al cargar el mes'
    bloquesMes.value = []
    diaSeleccionado.value = ''
  } finally {
    cargandoMes.value = false
  }
}

async function cambiarMes(delta) {
  mesOffset.value = Math.min(0, mesOffset.value + delta)
  busqueda.value = ''
  await cargarMes()
}

// En dos columnas, deseleccionar dejaría la derecha vacía: el clic siempre selecciona.
function seleccionarDia(fecha) {
  diaSeleccionado.value = fecha
  busqueda.value = ''
}

onMounted(cargarMes)
</script>
