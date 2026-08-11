<template>
  <div class="animate-fade-in-up">
    <!-- Header -->
    <div class="mb-6">
      <h2 class="text-3xl font-extrabold text-gray-900 tracking-tight">Resumen del box</h2>
      <p class="text-gray-500 mt-1 capitalize">{{ fechaHoyTexto }}</p>
    </div>

    <!-- Dos pestañas y solo dos: clientes y asistencia. Lo financiero NO vuelve acá —
         vive entero en /finanzas, que tiene su propio selector de período. -->
    <div class="flex items-center gap-6 border-b border-gray-200 mb-6">
      <button v-for="t in TABS" :key="t.key" @click="tab = t.key"
        class="pb-3 -mb-px text-xs font-bold uppercase tracking-widest border-b-2 transition-colors"
        :class="tab === t.key
          ? 'border-red-600 text-red-600'
          : 'border-transparent text-gray-400 hover:text-gray-600'">
        {{ t.label }}
      </button>
      <router-link :to="tab === 'clientes' ? '/usuarios' : '/usuarios?tab=en_box'"
        class="ml-auto pb-3 text-xs font-bold text-red-600 hover:underline">
        Ver todos →
      </router-link>
    </div>

    <!-- ═══════════ BLOQUE: CLIENTES ═══════════ -->
    <section v-show="tab === 'clientes'" class="mb-10">

      <div v-if="cargandoResumen" class="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <div v-for="i in 4" :key="i" class="bg-white rounded-2xl h-28 animate-pulse border border-gray-100" />
      </div>

      <template v-else>
        <div class="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-4">
          <!-- Activos y Pendientes navegan: la flecha del encabezado los marca como enlace. -->
          <router-link :to="{ path: '/usuarios', query: { tab: 'activos' } }"
            class="group bg-white rounded-2xl p-5 border border-gray-100 hover:border-gray-300 shadow-sm transition-colors block">
            <div class="flex items-center justify-between mb-2">
              <p class="text-xs font-bold text-gray-400 uppercase tracking-widest">Activos</p>
              <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4 text-gray-300 group-hover:text-gray-600 group-hover:translate-x-0.5 transition-all flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2.5">
                <path stroke-linecap="round" stroke-linejoin="round" d="M13.5 4.5 21 12m0 0-7.5 7.5M21 12H3" />
              </svg>
            </div>
            <p class="text-3xl font-black text-gray-900">{{ socios.activos }}</p>
            <!-- Compara activos contra activos (cierre del mes pasado), no altas: puesto
                 debajo de este número, un delta de altas se lee como socios perdidos. -->
            <p v-if="deltaActivos !== null" class="text-xs mt-1"
              :class="deltaActivos > 0 ? 'text-emerald-600' : (deltaActivos < 0 ? 'text-red-500' : 'text-gray-400')">
              {{ deltaActivos === 0 ? 'Igual que el mes pasado'
                 : `${deltaActivos > 0 ? '+' : '−'}${Math.abs(deltaActivos)} del mes pasado` }}
            </p>
          </router-link>

          <!-- Sin acento de color aunque haya pendientes: un registro por activar es
               trabajo normal del día, no una alarma. El número ya lo dice. -->
          <router-link :to="{ path: '/usuarios', query: { tab: 'pendientes' } }"
            class="group bg-white rounded-2xl p-5 border border-gray-100 hover:border-gray-300 shadow-sm transition-colors block">
            <div class="flex items-center justify-between mb-2">
              <p class="text-xs font-bold text-gray-400 uppercase tracking-widest">Pendientes</p>
              <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4 text-gray-300 group-hover:text-gray-600 group-hover:translate-x-0.5 transition-all flex-shrink-0"
                fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2.5">
                <path stroke-linecap="round" stroke-linejoin="round" d="M13.5 4.5 21 12m0 0-7.5 7.5M21 12H3" />
              </svg>
            </div>
            <p class="text-3xl font-black text-gray-900">{{ socios.pendientes }}</p>
            <p class="text-xs text-gray-400 mt-1">
              {{ socios.pendientes === 1 ? 'Solicitud por activar' : 'Solicitudes por activar' }}
            </p>
          </router-link>

          <div class="bg-white rounded-2xl p-5 border border-gray-100 shadow-sm">
            <p class="text-xs font-bold text-gray-400 uppercase tracking-widest mb-2">Recuperables</p>
            <p class="text-3xl font-black text-gray-900">{{ socios.vencidos_recuperables }}</p>
            <p class="text-xs text-gray-400 mt-1">Vencidos hace menos de 30 días</p>
          </div>

          <div class="bg-white rounded-2xl p-5 border border-gray-100 shadow-sm">
            <p class="text-xs font-bold text-gray-400 uppercase tracking-widest mb-2">Renovación</p>
            <p class="text-3xl font-black text-gray-900">
              {{ renovacion.porcentaje !== null ? renovacion.porcentaje + '%' : '—' }}
            </p>
            <p class="text-xs text-gray-400 mt-1">
              {{ renovacion.renovaron }} de {{ renovacion.vencieron }} · últimos 30 días
            </p>
          </div>
        </div>

        <div class="grid grid-cols-1 lg:grid-cols-2 gap-4">
          <!-- Cumpleaños de hoy -->
          <div class="border border-gray-200 rounded-2xl overflow-hidden">
            <div class="flex items-center gap-3 px-4 py-3 border-b border-gray-100">
              <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4 text-gray-500 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
                <path stroke-linecap="round" stroke-linejoin="round" d="M12 8.25v-1.5m0 1.5c-1.355 0-2.697.056-4.024.166C6.845 8.51 6 9.473 6 10.608v2.513m6-4.871c1.355 0 2.697.056 4.024.166C17.155 8.51 18 9.473 18 10.608v2.513M15 8.25v-1.5m-6 1.5v-1.5m12 9.75-1.5.75a3.354 3.354 0 0 1-3 0 3.354 3.354 0 0 0-3 0 3.354 3.354 0 0 1-3 0 3.354 3.354 0 0 0-3 0 3.354 3.354 0 0 1-3 0L3 16.5m15-3.379a48.474 48.474 0 0 0-6-.371c-2.032 0-4.034.126-6 .371m12 0c.39.049.777.102 1.163.16 1.07.16 1.837 1.094 1.837 2.175v5.169c0 .621-.504 1.125-1.125 1.125H4.125A1.125 1.125 0 0 1 3 20.625v-5.17c0-1.08.768-2.014 1.837-2.174A47.78 47.78 0 0 1 6 13.12" />
              </svg>
              <button @click="tabCumple = 'pendientes'"
                class="flex items-center gap-1.5 text-xs font-bold uppercase tracking-widest transition-colors"
                :class="tabCumple === 'pendientes' ? 'text-gray-800' : 'text-gray-400 hover:text-gray-600'">
                Cumpleaños hoy
                <span v-if="cumpleSinFelicitar.length" class="text-[10px] font-black bg-red-600 text-white px-1.5 h-4 flex items-center rounded-full">
                  {{ cumpleSinFelicitar.length }}
                </span>
              </button>
              <span class="text-gray-200">|</span>
              <button @click="tabCumple = 'enviadas'"
                class="text-xs font-bold uppercase tracking-widest transition-colors"
                :class="tabCumple === 'enviadas' ? 'text-gray-800' : 'text-gray-400 hover:text-gray-600'">
                Enviados
              </button>
            </div>

            <!-- Vacío: mismo alto que la lista llena, para que la card no salte al cambiar de pestaña -->
            <div v-if="cumpleVisibles.length === 0"
              class="flex flex-col items-center justify-center text-center px-4 min-h-[12.5rem]">
              <svg xmlns="http://www.w3.org/2000/svg" class="h-10 w-10 text-gray-300 mb-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0z" />
              </svg>
              <p class="text-sm font-medium text-gray-400">
                {{ tabCumple === 'pendientes' ? 'No hay clientes por felicitar' : 'Ningún cliente felicitado hoy' }}
              </p>
            </div>
            <!-- Tope de 4 filas visibles; el resto se alcanza scrolleando.
                 Fila = 30px de contenido + 20px de padding vertical → 4 × 50px. -->
            <div v-else class="flex flex-col divide-y divide-gray-100 max-h-[12.5rem] overflow-y-auto">
              <div v-for="u in cumpleVisibles" :key="u.id" class="flex items-center justify-between gap-3 px-4 py-2.5">
                <div class="min-w-0">
                  <p class="text-sm font-semibold text-gray-800 truncate">{{ u.nombre }}</p>
                  <p v-if="tabCumple === 'enviadas'" class="text-xs text-gray-400">
                    Cumplió el {{ fechaCumpleTexto }}
                  </p>
                </div>
                <div class="flex items-center gap-2 flex-shrink-0">
                  <!-- Se pregunta por el link, no por el teléfono: un número incompleto
                       genera un botón que lleva a un error de WhatsApp. -->
                  <a v-if="whatsappCumpleanos(u) && tabCumple === 'pendientes'" :href="whatsappCumpleanos(u)" target="_blank"
                    @click="marcarFelicitado(u)"
                    class="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-bold transition-colors">
                    <svg xmlns="http://www.w3.org/2000/svg" class="h-3.5 w-3.5" viewBox="0 0 24 24" fill="currentColor">
                      <path d="M12 0C5.373 0 0 5.373 0 12c0 2.126.553 4.116 1.522 5.85L0 24l6.335-1.48A11.945 11.945 0 0012 24c6.627 0 12-5.373 12-12S18.627 0 12 0zm0 21.818a9.818 9.818 0 01-5.006-1.371l-.36-.214-3.73.871.938-3.63-.234-.373A9.817 9.817 0 012.182 12C2.182 6.57 6.57 2.182 12 2.182c5.43 0 9.818 4.388 9.818 9.818 0 5.43-4.388 9.818-9.818 9.818z"/>
                    </svg>
                    Felicitar
                  </a>
                  <button @click="router.push(`/usuarios/${u.id}`)"
                    class="px-3 py-1.5 rounded-lg bg-white border border-gray-200 hover:border-gray-300 text-gray-600 text-xs font-semibold transition-colors">
                    Ver perfil
                  </button>
                </div>
              </div>
            </div>
          </div>

          <!-- Membresías por vencer: los recordatorios de WhatsApp -->
          <div class="border border-gray-200 rounded-2xl overflow-hidden">
            <div class="flex items-center gap-3 px-4 py-3 border-b border-gray-100">
              <button @click="tabAlertas = 'pendientes'"
                class="flex items-center gap-1.5 text-xs font-bold uppercase tracking-widest transition-colors"
                :class="tabAlertas === 'pendientes' ? 'text-gray-800' : 'text-gray-400 hover:text-gray-600'">
                Por vencer · 7 días
                <span v-if="pendientes.length" class="text-[10px] font-black bg-amber-500 text-white px-1.5 h-4 flex items-center rounded-full">
                  {{ pendientes.length }}
                </span>
              </button>
              <span class="text-gray-200">|</span>
              <button @click="tabAlertas = 'enviadas'"
                class="text-xs font-bold uppercase tracking-widest transition-colors"
                :class="tabAlertas === 'enviadas' ? 'text-gray-800' : 'text-gray-400 hover:text-gray-600'">
                Enviados
              </button>
            </div>

            <div v-if="cargandoAlertas" class="px-4 py-6 text-center text-sm text-gray-400">Cargando…</div>

            <!-- Pendientes -->
            <template v-else-if="tabAlertas === 'pendientes'">
              <div v-if="pendientes.length === 0"
                class="flex flex-col items-center justify-center text-center px-4 min-h-[14rem]">
                <svg xmlns="http://www.w3.org/2000/svg" class="h-10 w-10 text-gray-300 mb-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9" />
                </svg>
                <p class="text-sm font-medium text-gray-400">Ninguna membresía vence esta semana</p>
              </div>
              <div v-else class="flex flex-col divide-y divide-gray-100 max-h-[14rem] overflow-y-auto">
                <div v-for="a in pendientes" :key="a.id" class="flex items-center justify-between gap-3 px-4 py-2.5">
                  <div class="min-w-0">
                    <p class="text-sm font-semibold text-gray-800 truncate">{{ a.usuario_nombre }}</p>
                    <p class="text-xs" :class="diasParaVencer(a) <= 1 ? 'text-red-600 font-semibold' : 'text-gray-400'">
                      {{ textoVence(diasParaVencer(a)) }}
                    </p>
                  </div>
                  <div class="flex items-center gap-2 flex-shrink-0">
                    <span v-if="sinTelefono(a)"
                      class="px-2 py-0.5 rounded-full bg-gray-100 text-gray-500 text-[10px] font-bold uppercase tracking-wide">
                      Sin teléfono
                    </span>
                    <span v-else-if="a.error_envio" :title="a.error_envio"
                      class="px-2 py-0.5 rounded-full bg-amber-100 text-amber-700 text-[10px] font-bold uppercase tracking-wide cursor-help">
                      Envío automático falló
                    </span>
                    <a v-if="whatsappAlerta(a) && mostrarBotonManual(a)" :href="whatsappAlerta(a)" target="_blank"
                      @click="marcarEnviada(a)"
                      class="px-3 py-1.5 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-bold transition-colors">
                      Recordar
                    </a>
                    <button @click="router.push(`/usuarios/${a.usuario_id}`)"
                      class="px-3 py-1.5 rounded-lg bg-white border border-gray-200 hover:border-gray-300 text-gray-600 text-xs font-semibold transition-colors">
                      Ver
                    </button>
                  </div>
                </div>
              </div>
            </template>

            <!-- Historial de la última semana -->
            <template v-else>
              <div v-if="enviadas.length === 0"
                class="flex flex-col items-center justify-center text-center px-4 min-h-[14rem]">
                <svg xmlns="http://www.w3.org/2000/svg" class="h-10 w-10 text-gray-300 mb-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9" />
                </svg>
                <p class="text-sm font-medium text-gray-400">Sin recordatorios enviados esta semana</p>
              </div>
              <div v-else class="flex flex-col divide-y divide-gray-100 max-h-[14rem] overflow-y-auto">
                <div v-for="a in enviadas" :key="a.id" class="flex items-center justify-between gap-3 px-4 py-2.5">
                  <div class="min-w-0">
                    <p class="text-sm font-semibold text-gray-800 truncate">{{ a.usuario_nombre }}</p>
                    <p class="text-xs text-gray-400 flex items-center gap-1.5">
                      Enviado {{ formatEnviado(a.fecha_enviada) }}
                      <!-- Sin chip si canal es null: son alertas anteriores al
                           envío automático y no se sabe por dónde salieron. -->
                      <span v-if="a.canal === 'whatsapp_api'"
                        class="px-1.5 rounded-full bg-emerald-50 text-emerald-700 text-[10px] font-bold uppercase tracking-wide">
                        Automático
                      </span>
                      <span v-else-if="a.canal === 'manual'"
                        class="px-1.5 rounded-full bg-gray-100 text-gray-500 text-[10px] font-bold uppercase tracking-wide">
                        Manual
                      </span>
                    </p>
                  </div>
                  <button @click="router.push(`/usuarios/${a.usuario_id}`)"
                    class="px-3 py-1.5 rounded-lg bg-white border border-gray-200 hover:border-gray-300 text-gray-600 text-xs font-semibold transition-colors flex-shrink-0">
                    Ver
                  </button>
                </div>
              </div>
            </template>
          </div>
        </div>

        <!-- Evolución de clientes activos, al pie del bloque: arriba van las tarjetas y
             las dos listas accionables (hoy), acá la tendencia (histórico).
             Carga aparte de /resumen: si este endpoint falla, el resto sigue en pie. -->
        <div class="bg-white rounded-2xl p-5 border border-gray-100 shadow-sm mt-4">
          <div class="mb-4">
            <p class="text-xs font-bold text-gray-400 uppercase tracking-widest">Clientes activos por mes</p>
            <!-- No hay histórico de membresías: el número es una inferencia y la
                 pantalla lo dice, igual que la tarjeta de Renovación. -->
            <p class="text-xs text-gray-400 mt-1">Reconstruido a partir de los pagos registrados</p>
          </div>

          <div v-if="cargandoSocios" class="h-56 rounded-xl bg-gray-50 animate-pulse" />
          <p v-else-if="sociosMensuales.length === 0" class="h-56 flex items-center justify-center text-sm text-gray-400">
            Todavía no hay pagos registrados.
          </p>
          <div v-else class="h-56">
            <canvas ref="canvasSocios"></canvas>
          </div>
        </div>
      </template>
    </section>

    <!-- ═══════════ BLOQUE: ASISTENCIA ═══════════ -->
    <!-- v-show y no v-if: SesionesPanel trae sus propios datos al montarse, y con v-if
         cada ida y vuelta entre pestañas dispararía otro refetch. -->
    <section v-show="tab === 'asistencia'" class="mb-6">
      <div v-if="cargandoResumen" class="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <div v-for="i in 4" :key="i" class="bg-white rounded-2xl h-24 animate-pulse border border-gray-100" />
      </div>

      <template v-else>
        <div class="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-4">
          <div class="bg-white rounded-2xl p-5 border border-gray-100 shadow-sm">
            <p class="text-xs font-bold text-gray-400 uppercase tracking-widest mb-2">Hoy</p>
            <p class="text-3xl font-black text-gray-900">{{ asistencia.hoy }}</p>
          </div>
          <div class="bg-white rounded-2xl p-5 border border-gray-100 shadow-sm">
            <p class="text-xs font-bold text-gray-400 uppercase tracking-widest mb-2">Esta semana</p>
            <p class="text-3xl font-black text-gray-900">{{ asistencia.semana }}</p>
          </div>
          <div class="bg-white rounded-2xl p-5 border border-gray-100 shadow-sm">
            <p class="text-xs font-bold text-gray-400 uppercase tracking-widest mb-2">Promedio diario</p>
            <p class="text-3xl font-black text-gray-900">{{ asistencia.promedio_diario }}</p>
            <p class="text-xs text-gray-400 mt-1">Últimos 30 días</p>
          </div>
          <div class="bg-white rounded-2xl p-5 border border-gray-100 shadow-sm">
            <!-- "Participación" en la UI; la clave del API sigue siendo `engagement`. -->
            <p class="text-xs font-bold text-gray-400 uppercase tracking-widest mb-2">Participación</p>
            <p class="text-3xl font-black text-gray-900">
              {{ asistencia.engagement !== null ? asistencia.engagement + '%' : '—' }}
            </p>
            <p class="text-xs text-gray-400 mt-1">{{ asistencia.socios_semana }} de {{ socios.activos }} vinieron</p>
          </div>
        </div>

        <!-- Sesiones por bloque horario (antes era una vista propia en /sesiones) -->
        <SesionesPanel />
      </template>
    </section>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted, onUnmounted, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import api from '../api'
import { getChart } from '../lib/chart'
import { linkWa, telefonoWa } from '../lib/whatsapp'
import SesionesPanel from '../components/SesionesPanel.vue'

const router = useRouter()

// ── Pestañas ─────────────────────────────────────────────────
const TABS = [
  { key: 'clientes',   label: 'Clientes' },
  { key: 'asistencia', label: 'Asistencia' },
]
const tab = ref('clientes')

// ── Estado ───────────────────────────────────────────────────
const socios = ref({ activos: 0, por_vencer: 0, vencidos_recuperables: 0, sin_membresia: 0, pendientes: 0, altas_mes: 0, altas_mes_anterior: 0 })
const asistencia = ref({ hoy: 0, semana: 0, promedio_diario: 0, socios_semana: 0, engagement: null })
const renovacion = ref({ vencieron: 0, renovaron: 0, porcentaje: null })
const cumpleaneros = ref([])
const tabCumple = ref('pendientes')
// Una sola petición trae pendientes + enviadas de la última semana; se separan acá.
const alertas = ref([])
const tabAlertas = ref('pendientes')
// Lo informa POST /alertas/generar. Decide si el botón manual de WhatsApp hace
// falta: sin credenciales de la Cloud API, el envío sigue siendo a mano.
const whatsappAutomatico = ref(false)

const sociosMensuales = ref([])

const cargandoResumen = ref(true)
const cargandoAlertas = ref(true)
const cargandoSocios = ref(true)

/** Reloj reactivo, actualizado por el mismo intervalo que refresca los datos.
 *  Esta pantalla vive abierta todo el día en la PC de recepción, así que "hoy" no puede
 *  quedar congelado en el momento del montaje: la fecha del encabezado, los días que
 *  faltan para cada vencimiento y la clave de felicitados se derivan de acá para que
 *  crucen la medianoche solos. */
const ahora = ref(new Date())

const fechaHoyTexto = computed(() =>
  ahora.value.toLocaleDateString('es-CO', { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' })
)
/** Activos hoy menos activos al cierre del mes pasado, de la misma serie que dibuja
 *  la gráfica. `null` mientras no haya dos meses: sin mes anterior no hay comparación
 *  posible, y mostrar "+17" contra un mes que no existe sería inventar crecimiento. */
const deltaActivos = computed(() => {
  const s = sociosMensuales.value
  return s.length >= 2 ? s[s.length - 1].activos - s[s.length - 2].activos : null
})

// ── WhatsApp ─────────────────────────────────────────────────
// La normalización vive en lib/whatsapp.js, que espeja la del backend. Acá había una
// copia local (`_telefono`) y en PlanesView una tercera que ni ponía el prefijo 57.

const whatsappCumpleanos = (u) =>
  linkWa(u.telefono,
    `¡Feliz cumpleaños, ${u.nombre}! 🎉 De parte de todo el equipo de Jain Sport Box. ` +
    `Pasá hoy por el box y te invitamos un batido. 💪`
  )

// ── Felicitaciones enviadas ──────────────────────────────────
// A diferencia de las alertas de vencimiento, los cumpleaños no tienen tabla propia:
// no hay dónde guardar "ya lo felicité". Se lleva en localStorage con la fecha en la
// clave, así el registro se vacía solo al día siguiente.
// LIMITACIÓN: es por dispositivo. Si felicitás desde el celular, la PC del gym no se entera.
// Derivada de `ahora` y no fijada al montar: con la pantalla abierta al cruzar la
// medianoche, una clave congelada seguiría marcando como felicitados a los de ayer.
const claveFelicitados = computed(() => `felicitados:${ahora.value.toLocaleDateString('en-CA')}`)
const felicitados = ref(new Set())

function cargarFelicitados() {
  // Limpieza de días anteriores: si no, las claves viejas se acumulan para siempre.
  for (let i = localStorage.length - 1; i >= 0; i--) {
    const k = localStorage.key(i)
    if (k?.startsWith('felicitados:') && k !== claveFelicitados.value) localStorage.removeItem(k)
  }
  try {
    felicitados.value = new Set(JSON.parse(localStorage.getItem(claveFelicitados.value) || '[]'))
  } catch {
    felicitados.value = new Set()
  }
}

// Al cambiar el día se relee: descarta los de ayer y arranca la lista nueva vacía.
watch(claveFelicitados, cargarFelicitados)

function marcarFelicitado(u) {
  const s = new Set(felicitados.value)
  s.add(u.id)
  felicitados.value = s                       // Set nuevo: reasignar para que Vue reaccione
  localStorage.setItem(claveFelicitados.value, JSON.stringify([...s]))
}

// La lista es siempre la de los cumpleaños de HOY (el endpoint filtra por el día),
// así que la fecha del cumpleaños es la de la clave de localStorage.
const fechaCumpleTexto = computed(() =>
  new Date(claveFelicitados.value.split(':')[1] + 'T12:00:00')
    .toLocaleDateString('es-CO', { weekday: 'short', day: 'numeric', month: 'short' })
)

const cumpleSinFelicitar = computed(() => cumpleaneros.value.filter(u => !felicitados.value.has(u.id)))
const cumpleFelicitados = computed(() => cumpleaneros.value.filter(u => felicitados.value.has(u.id)))
const cumpleVisibles = computed(() =>
  tabCumple.value === 'pendientes' ? cumpleSinFelicitar.value : cumpleFelicitados.value
)

/** Días que faltan para el vencimiento, calculados AHORA.
 *
 *  Deliberadamente NO se usa `a.dias_anticipacion`: esa columna se congela cuando
 *  `generar_alertas` crea la alerta y nunca se actualiza, así que a los dos días ya
 *  miente — el panel llegaba a decir "Vence en 5 días" el mismo día del vencimiento, y
 *  `whatsappAlerta` le mandaba ese plazo equivocado al socio. El backend ya hace esto
 *  bien para el envío automático (calcula contra `Usuario.fecha_vencimiento` en
 *  `alertas.py`); esto alinea el camino manual con el automático.
 *
 *  `'T00:00:00'` fuerza medianoche LOCAL: sin la hora, `new Date('2026-08-15')` se
 *  parsea como UTC y en Bogotá cae el día anterior. Depende de `ahora` para que la
 *  cuenta avance sola al cruzar la medianoche con la pantalla abierta. */
const diasParaVencer = (a) => {
  const hoy = new Date(ahora.value)
  hoy.setHours(0, 0, 0, 0)
  const vence = new Date(a.fecha_vencimiento + 'T00:00:00')
  return Math.round((vence - hoy) / 86400000)
}

// El backend ordena por `dias_anticipacion`, que es la columna congelada: con alertas
// creadas en días distintos el orden salía cruzado. Se reordena por la fecha real.
const pendientes = computed(() =>
  alertas.value
    .filter(a => !a.enviada)
    .sort((a, b) => a.fecha_vencimiento.localeCompare(b.fecha_vencimiento))
)
const enviadas = computed(() =>
  alertas.value
    .filter(a => a.enviada)
    .sort((a, b) => new Date(b.fecha_enviada || 0) - new Date(a.fecha_enviada || 0))
)

const formatEnviado = (f) =>
  f ? new Date(f).toLocaleDateString('es-CO', { weekday: 'short', day: 'numeric', month: 'short' }) : '—'

const textoVence = (dias) =>
  dias <= 0 ? 'Vence hoy' : dias === 1 ? 'Vence mañana' : `Vence en ${dias} días`

/** El botón manual de WhatsApp es el fallback del envío automático: se muestra
 *  solo si el automático no está configurado, o si esta fila ya falló. Con el
 *  automático andando y sin errores, mostrarlo invitaría a mandar dos veces. */
const mostrarBotonManual = (a) => !whatsappAutomatico.value || !!a.error_envio

/** Distinto de un fallo de la API: acá no hay a quién escribirle, ni siquiera
 *  a mano. Sin este chip la fila quedaba muda y sin explicación.
 *
 *  Usa `telefonoWa` y no `!a.usuario_telefono`: un teléfono cargado incompleto
 *  (menos de 10 dígitos) es igual de inservible, y así el chip coincide con lo que
 *  el backend cuenta como `omitidas` al mandar los recordatorios automáticos. */
const sinTelefono = (a) => !telefonoWa(a.usuario_telefono)

// Único lugar donde vive el texto del recordatorio de vencimiento.
const whatsappAlerta = (a) => {
  const fecha = new Date(a.fecha_vencimiento + 'T12:00:00')
    .toLocaleDateString('es-CO', { year: 'numeric', month: 'short', day: 'numeric' })
  // El caso 0 ("vence hoy") hay que contemplarlo: la alerta vive en el panel hasta el
  // día del vencimiento, y sin esta rama el mensaje decía "en *0 días*".
  const dias = diasParaVencer(a)
  const cuando = dias <= 0 ? `*hoy* (${fecha})`
    : dias === 1 ? `*mañana* (${fecha})`
    : `en *${dias} días* (${fecha})`
  return linkWa(a.usuario_telefono,
    `Hola ${a.usuario_nombre}! 👋 Te recordamos que tu membresía en *Jain Sport Box* vence ${cuando}. ` +
    `Para renovar contáctanos. 💪🔥`
  )
}

// ── Carga ────────────────────────────────────────────────────
// Cada bloque carga por su cuenta: si uno falla, el resto de la pantalla sigue viva.
async function cargarResumen() {
  try {
    const { data } = await api.get('/dashboard/resumen')
    socios.value = data.socios
    asistencia.value = data.asistencia
    renovacion.value = data.renovacion
    cumpleaneros.value = data.cumpleaneros
  } catch (e) {
    console.error(e)
  } finally {
    cargandoResumen.value = false
  }
}

async function cargarAlertas() {
  try {
    // generar/ reconcilia la lista: crea las que faltan y borra las de quien ya renovó.
    const { data: gen } = await api.post('/alertas/generar')
    whatsappAutomatico.value = !!gen.whatsapp_automatico
    alertas.value = (await api.get('/alertas/', {
      params: { solo_pendientes: false, enviadas_ultimos_dias: 7 },
    })).data
  } catch (e) {
    console.error(e)
  } finally {
    cargandoAlertas.value = false
  }
}

/** El recordatorio se marca como enviado al abrir WhatsApp. No se saca de la lista:
 *  se marca, y así pasa de la pestaña "Por vencer" a la de "Enviados". */
async function marcarEnviada(a) {
  try {
    await api.post(`/alertas/${a.id}/marcar-enviada`)
    a.enviada = true
    a.fecha_enviada = new Date().toISOString()
  } catch { /* silencioso: el link de WhatsApp ya se abrió */ }
}

// ── Gráfica de clientes activos ──────────────────────────────
const canvasSocios = ref(null)
let chart = null

function destruirChart() {
  if (chart) {
    chart.destroy()
    chart = null
  }
}

const MESES_CORTOS = ['ene', 'feb', 'mar', 'abr', 'may', 'jun', 'jul', 'ago', 'sep', 'oct', 'nov', 'dic']

/** "2026-08" → "ago 26" */
function etiquetaMes(clave) {
  const [anio, mes] = clave.split('-')
  return `${MESES_CORTOS[Number(mes) - 1]} ${anio.slice(2)}`
}

async function renderChart() {
  if (!canvasSocios.value) return
  const Chart = await getChart()
  destruirChart()
  chart = new Chart(canvasSocios.value, {
    type: 'line',
    data: {
      labels: sociosMensuales.value.map(m => etiquetaMes(m.mes)),
      datasets: [{
        data: sociosMensuales.value.map(m => m.activos),
        borderColor: '#f87171',
        backgroundColor: 'rgba(248, 113, 113, 0.12)',
        pointBackgroundColor: '#f87171',
        pointRadius: 3,
        borderWidth: 2,
        tension: 0.3,
        fill: true,
      }],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { display: false },
        tooltip: {
          callbacks: {
            label: (ctx) => `${ctx.parsed.y} ${ctx.parsed.y === 1 ? 'cliente activo' : 'clientes activos'}`,
          },
        },
      },
      scales: {
        y: {
          beginAtZero: true,
          // Son personas: un eje con decimales no significa nada.
          ticks: { precision: 0, color: '#9ca3af' },
          grid: { color: '#f3f4f6' },
        },
        x: {
          ticks: { color: '#9ca3af' },
          grid: { display: false },
        },
      },
    },
  })
}

async function cargarSociosMensuales() {
  try {
    const { data } = await api.get('/dashboard/socios-mensuales', { params: { meses: 12 } })
    sociosMensuales.value = data.meses
  } catch (e) {
    console.error(e)
  } finally {
    cargandoSocios.value = false
  }
}

/* El canvas está dentro del bloque que espera a /resumen, pero los datos vienen de
   /socios-mensuales: son dos peticiones en paralelo y no hay garantía de orden. Si se
   renderizara al terminar la segunda, cuando esa gana la carrera el canvas todavía no
   existe y el render se aborta en silencio para siempre. Por eso se espera a que las
   DOS condiciones se cumplan. */
const puedeGraficar = computed(() =>
  !cargandoResumen.value && !cargandoSocios.value && sociosMensuales.value.length > 0
)

// Se observa también la serie: en el primer render alcanzaba con `puedeGraficar`, pero
// al refrescar ya está en `true` y no volvería a dispararse, así que la gráfica se
// quedaría con los datos viejos. `sociosMensuales` se reasigna en cada fetch.
watch([puedeGraficar, sociosMensuales], async ([listo]) => {
  if (!listo) return
  await nextTick()
  renderChart()
}, { immediate: true })

// ── Auto-refresh ─────────────────────────────────────────────
// Sin esto la pantalla se congela en el momento del montaje: en recepción queda abierta
// todo el día y "Hoy" no se movía mientras la gente marcaba huella, los cumpleaños no
// rotaban a medianoche y la única forma de ver datos frescos era recargar a mano.
const INTERVALO_MS = 60_000

// `/resumen` es lo barato y lo que se mueve solo, así que es lo único que entra al
// intervalo. `/socios-mensuales` reconstruye la serie sobre toda la tabla `pagos` y
// cambia como mucho una vez al día; `/alertas/generar` además es una ESCRITURA. Esos
// dos se refrescan solo al volver a la pestaña, que es cuando pudo pasar algo.
let intervalo = null
let ultimoCompleto = Date.now()

function refrescarLigero() {
  // Con la pestaña oculta el navegador ya throttlea el timer; igual se salta la
  // petición para no pegarle al backend desde pantallas que nadie está mirando.
  if (document.visibilityState !== 'visible') return
  ahora.value = new Date()
  cargarResumen()
}

function alVolverALaPestana() {
  if (document.visibilityState !== 'visible') return
  ahora.value = new Date()
  cargarResumen()
  // Throttle: cambiar de pestaña es un gesto que se repite mucho y estas dos son las
  // llamadas caras. Una por minuto como máximo.
  if (Date.now() - ultimoCompleto < INTERVALO_MS) return
  ultimoCompleto = Date.now()
  cargarAlertas()
  cargarSociosMensuales()
}

onMounted(() => {
  cargarFelicitados()
  cargarResumen()
  cargarAlertas()
  cargarSociosMensuales()
  intervalo = setInterval(refrescarLigero, INTERVALO_MS)
  document.addEventListener('visibilitychange', alVolverALaPestana)
})

onUnmounted(() => {
  clearInterval(intervalo)
  document.removeEventListener('visibilitychange', alVolverALaPestana)
  destruirChart()
})
</script>
