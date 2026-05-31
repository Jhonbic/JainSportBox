<template>
  <div class="animate-fade-in-up">

    <!-- Header -->
    <div class="mb-6">
      <h2 class="text-3xl font-extrabold text-gray-900 tracking-tight">Sesiones</h2>
      <p class="text-gray-500 mt-1">Asistentes por bloque horario</p>
    </div>

    <!-- Selector de modo -->
    <div class="flex gap-2 mb-6">
      <button
        @click="setModo('semana')"
        class="px-5 py-2 rounded-xl font-bold text-sm transition-colors border"
        :class="modo === 'semana'
          ? 'bg-gray-900 text-white border-gray-900'
          : 'bg-white text-gray-600 border-gray-200 hover:border-gray-400'">
        Esta semana
      </button>
      <button
        @click="setModo('fecha')"
        class="px-5 py-2 rounded-xl font-bold text-sm transition-colors border"
        :class="modo === 'fecha'
          ? 'bg-gray-900 text-white border-gray-900'
          : 'bg-white text-gray-600 border-gray-200 hover:border-gray-400'">
        Fecha específica
      </button>
    </div>

    <!-- ── MODO SEMANA ── -->
    <template v-if="modo === 'semana'">

      <!-- Tabs de días -->
      <div class="flex gap-2 mb-6 overflow-x-auto pb-1">
        <button
          v-for="d in diasSemana" :key="d.fecha"
          @click="diaSeleccionado = d.fecha"
          class="flex-shrink-0 flex flex-col items-center px-4 py-3 rounded-2xl border font-semibold transition-all"
          :class="[
            diaSeleccionado === d.fecha
              ? 'bg-red-600 text-white border-red-600 shadow-md'
              : d.esHoy
                ? 'bg-gray-900 text-white border-gray-900'
                : 'bg-white text-gray-600 border-gray-200 hover:border-red-400',
            d.total === 0 ? 'opacity-40' : ''
          ]">
          <span class="text-xs uppercase tracking-widest mb-1">{{ d.nombreDia }}</span>
          <span class="text-lg font-extrabold leading-none">{{ d.numeroDia }}</span>
          <span
            v-if="d.total > 0"
            class="mt-1.5 text-xs font-bold px-2 py-0.5 rounded-full"
            :class="diaSeleccionado === d.fecha ? 'bg-red-500 text-white' : 'bg-red-100 text-red-600'">
            {{ d.total }}
          </span>
          <span v-else class="mt-1.5 text-xs text-gray-400">—</span>
        </button>
      </div>

      <!-- Búsqueda -->
      <div class="mb-4">
        <input
          type="text"
          v-model="busqueda"
          placeholder="Buscar por nombre…"
          class="w-full max-w-sm border border-gray-200 rounded-xl px-4 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-red-400" />
      </div>

      <!-- Skeleton -->
      <div v-if="cargando" class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
        <div v-for="i in 3" :key="i" class="bg-gray-100 rounded-2xl h-44 animate-pulse"></div>
      </div>

      <!-- Bloques del día seleccionado -->
      <template v-else>
        <div v-if="bloquesDiaFiltrados.length > 0" class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          <BloqueCard
            v-for="b in bloquesDiaFiltrados"
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
    </template>

    <!-- ── MODO FECHA ESPECÍFICA ── -->
    <template v-else>
      <div class="flex flex-wrap items-end gap-3 mb-6">
        <div>
          <label class="block text-xs font-semibold text-gray-500 mb-1 uppercase tracking-wide">Fecha</label>
          <input
            type="date"
            v-model="fechaEspecifica"
            class="border border-gray-200 rounded-xl px-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-red-400" />
        </div>
        <button
          @click="consultarFecha"
          :disabled="!fechaEspecifica || cargando"
          class="px-5 py-2.5 bg-red-600 hover:bg-red-700 disabled:opacity-40 text-white font-bold rounded-xl text-sm transition-colors">
          Ver sesiones
        </button>
        <div class="flex-1 min-w-[180px]">
          <label class="block text-xs font-semibold text-gray-500 mb-1 uppercase tracking-wide">Buscar persona</label>
          <input
            type="text"
            v-model="busqueda"
            placeholder="Nombre del asistente…"
            class="w-full border border-gray-200 rounded-xl px-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-red-400" />
        </div>
      </div>

      <p v-if="error" class="mb-4 text-sm text-red-600 font-medium">{{ error }}</p>

      <div v-if="cargando" class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
        <div v-for="i in 3" :key="i" class="bg-gray-100 rounded-2xl h-44 animate-pulse"></div>
      </div>
      <template v-else-if="consultado">
        <div v-if="bloquesFechaFiltrados.length > 0" class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          <BloqueCard
            v-for="b in bloquesFechaFiltrados"
            :key="b.fecha + '-' + b.hora_inicio"
            :bloque="b"
            :busqueda="busqueda" />
        </div>
        <div v-else class="text-center py-16 text-gray-400">
          <p class="font-semibold text-gray-500">
            {{ busqueda ? `Sin resultados para "${busqueda}"` : 'Sin asistencias en esta fecha' }}
          </p>
        </div>
      </template>
    </template>

  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import api from '../api'
import BloqueCard from '../components/BloqueCard.vue'

// ── Estado ──
const modo = ref('semana')
const bloques = ref([])        // todos los bloques traídos del backend
const bloquesDate = ref([])    // bloques para modo fecha específica
const busqueda = ref('')
const cargando = ref(false)
const error = ref('')
const consultado = ref(false)

// Semana
const diasSemana = ref([])
const diaSeleccionado = ref('')

// Fecha específica
const fechaEspecifica = ref('')

// ── Helpers de fecha ──
const DIAS_CORTO  = ['Dom', 'Lun', 'Mar', 'Mié', 'Jue', 'Vie', 'Sáb']
const MESES_CORTO = ['Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun', 'Jul', 'Ago', 'Sep', 'Oct', 'Nov', 'Dic']

function isoHoy() {
  return new Date().toISOString().slice(0, 10)
}

function calcularSemana() {
  const hoy = new Date()
  const dow = hoy.getDay()                         // 0=Dom
  const lunes = new Date(hoy)
  lunes.setDate(hoy.getDate() - (dow === 0 ? 6 : dow - 1))
  return Array.from({ length: 7 }, (_, i) => {
    const d = new Date(lunes)
    d.setDate(lunes.getDate() + i)
    return d.toISOString().slice(0, 10)
  })
}

function buildDiasSemana(fechas, bloquesData) {
  const conteosPorFecha = {}
  for (const b of bloquesData) {
    conteosPorFecha[b.fecha] = (conteosPorFecha[b.fecha] || 0) + b.total
  }
  const hoy = isoHoy()
  return fechas.map(f => {
    const [y, m, d] = f.split('-').map(Number)
    const dt = new Date(y, m - 1, d)
    return {
      fecha:      f,
      nombreDia:  DIAS_CORTO[dt.getDay()],
      numeroDia:  d,
      mes:        MESES_CORTO[m - 1],
      esHoy:      f === hoy,
      total:      conteosPorFecha[f] || 0,
    }
  })
}

// ── Bloques filtrados por día (modo semana) ──
const bloquesDiaFiltrados = computed(() => {
  const q = busqueda.value.trim().toLowerCase()
  return bloques.value
    .filter(b => b.fecha === diaSeleccionado.value)
    .map(b => ({
      ...b,
      asistentes: q
        ? b.asistentes.filter(a => a.nombre.toLowerCase().includes(q))
        : b.asistentes,
    }))
    .filter(b => b.asistentes.length > 0)
})

// ── Bloques filtrados para fecha específica ──
const bloquesFechaFiltrados = computed(() => {
  const q = busqueda.value.trim().toLowerCase()
  return bloquesDate.value
    .map(b => ({
      ...b,
      asistentes: q
        ? b.asistentes.filter(a => a.nombre.toLowerCase().includes(q))
        : b.asistentes,
    }))
    .filter(b => b.asistentes.length > 0)
})

// ── Fetch semana ──
async function cargarSemana() {
  const fechas = calcularSemana()
  const desde  = fechas[0]
  const hasta  = fechas[6]
  cargando.value = true
  error.value = ''
  try {
    const { data } = await api.get('/asistencia/sesiones-por-bloque', {
      params: { desde, hasta },
    })
    bloques.value = data.bloques
    diasSemana.value = buildDiasSemana(fechas, data.bloques)
    // Seleccionar hoy si está en la semana, si no el primer día con datos
    const hoy = isoHoy()
    const conDatos = diasSemana.value.find(d => d.total > 0 && d.fecha === hoy)
      || diasSemana.value.find(d => d.total > 0)
    diaSeleccionado.value = conDatos ? conDatos.fecha : fechas[0]
  } catch (e) {
    error.value = e.response?.data?.detail || 'Error al cargar la semana'
  } finally {
    cargando.value = false
  }
}

// ── Fetch fecha específica ──
async function consultarFecha() {
  if (!fechaEspecifica.value) return
  cargando.value = true
  error.value = ''
  busqueda.value = ''
  try {
    const { data } = await api.get('/asistencia/sesiones-por-bloque', {
      params: { desde: fechaEspecifica.value, hasta: fechaEspecifica.value },
    })
    bloquesDate.value = data.bloques
    consultado.value = true
  } catch (e) {
    error.value = e.response?.data?.detail || 'Error al consultar'
    bloquesDate.value = []
  } finally {
    cargando.value = false
  }
}

function setModo(m) {
  modo.value = m
  busqueda.value = ''
  error.value = ''
  consultado.value = false
  if (m === 'semana') cargarSemana()
}

onMounted(() => cargarSemana())
</script>
