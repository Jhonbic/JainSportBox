<template>
  <div class="max-w-lg mx-auto">
    <h2 class="text-2xl font-black text-gray-800 mb-1">Acceso Manual</h2>
    <p class="text-sm text-gray-500 mb-8">
      Escribe la cédula o TI del cliente. Si su mensualidad está activa se registra la entrada y se abre la palanquera.
    </p>

    <!-- Input grande estilo recepción -->
    <form @submit.prevent="registrarAcceso" class="mb-6">
      <label class="block text-xs font-bold text-gray-500 uppercase tracking-wide mb-2">Cédula / TI</label>
      <div class="flex gap-3">
        <input
          ref="inputDoc"
          v-model="documento"
          type="text"
          inputmode="numeric"
          autocomplete="off"
          placeholder="Ej. 1020456789"
          class="flex-1 px-5 py-4 rounded-2xl border-2 border-gray-200 text-2xl font-black tracking-wider text-gray-800 focus:outline-none focus:border-red-500 transition-colors"
          :disabled="procesando"
        />
        <button type="submit" :disabled="procesando || !documento.trim()"
          class="px-6 rounded-2xl bg-red-600 hover:bg-red-700 disabled:bg-red-300 text-white font-black text-sm uppercase tracking-wide transition-colors flex items-center gap-2">
          <span v-if="procesando" class="animate-spin rounded-full h-5 w-5 border-b-2 border-white"></span>
          <template v-else>
            <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13.5 10.5V6.75a4.5 4.5 0 119 0v3.75M3.75 21.75h10.5a2.25 2.25 0 002.25-2.25v-6.75a2.25 2.25 0 00-2.25-2.25H3.75a2.25 2.25 0 00-2.25 2.25v6.75a2.25 2.25 0 002.25 2.25z"/>
            </svg>
            Abrir
          </template>
        </button>
      </div>
    </form>

    <!-- Resultado: acceso permitido -->
    <div v-if="resultado" class="bg-emerald-50 border-2 border-emerald-300 rounded-2xl p-6 text-center mb-4">
      <img v-if="resultado.foto_url" :src="mediaUrl(resultado.foto_url)"
        class="h-20 w-20 rounded-full object-cover mx-auto mb-3 border-4 border-white shadow" alt=""/>
      <svg v-else xmlns="http://www.w3.org/2000/svg" class="h-14 w-14 text-emerald-500 mx-auto mb-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"/>
      </svg>
      <p class="text-xl font-black text-emerald-800">{{ resultado.nombre }}</p>
      <p class="text-sm font-semibold text-emerald-700 mt-1">✓ Entrada registrada — palanquera abierta</p>
      <p class="text-xs text-emerald-600 mt-2">
        Membresía activa · vence en {{ resultado.dias_restantes }} día{{ resultado.dias_restantes !== 1 ? 's' : '' }}
        ({{ formatFecha(resultado.fecha_vencimiento) }})
      </p>
      <p v-if="avisoBridge" class="text-xs font-semibold text-gray-600 bg-white/70 rounded-lg px-3 py-2 mt-3 inline-block">
        ⚠ La entrada quedó registrada, pero no se pudo abrir la palanquera ({{ avisoBridge }}).
      </p>
    </div>

    <!-- Resultado: acceso denegado / error -->
    <div v-if="error" class="bg-red-50 border-2 border-red-300 rounded-2xl p-6 text-center mb-4">
      <svg xmlns="http://www.w3.org/2000/svg" class="h-14 w-14 text-red-500 mx-auto mb-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M18.364 5.636a9 9 0 11-12.728 12.728 9 9 0 0112.728-12.728zM12 8v4m0 4h.01"/>
      </svg>
      <p class="text-lg font-black text-red-800">Acceso denegado</p>
      <p class="text-sm font-semibold text-red-600 mt-1">{{ error }}</p>
    </div>

    <p class="text-xs text-gray-400 text-center">
      La palanquera se abre desde la PC del gym (bridge en localhost:8001). En otros equipos solo se registra la entrada.
    </p>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import api, { mediaUrl } from '../api'

const BRIDGE_URL = 'http://localhost:8001'

const inputDoc    = ref(null)
const documento   = ref('')
const procesando  = ref(false)
const resultado   = ref(null)
const error       = ref('')
const avisoBridge = ref('')

onMounted(() => inputDoc.value?.focus())

const formatFecha = (f) =>
  new Date(f + 'T12:00:00').toLocaleDateString('es-CO', { day: '2-digit', month: 'short', year: 'numeric' })

async function registrarAcceso() {
  const doc = documento.value.trim()
  if (!doc || procesando.value) return
  procesando.value = true
  resultado.value = null
  error.value = ''
  avisoBridge.value = ''
  try {
    // 1) Backend: valida membresía y registra la entrada
    const { data } = await api.post(`/asistencia/por-documento/${encodeURIComponent(doc)}`)
    resultado.value = data

    // 2) Bridge local: abre la palanquera (solo funciona en la PC del gym)
    try {
      const r = await fetch(`${BRIDGE_URL}/palanquera/abrir`, { method: 'POST' })
      if (!r.ok) avisoBridge.value = r.status === 503 ? 'relé no conectado' : `bridge respondió ${r.status}`
    } catch {
      avisoBridge.value = 'bridge no disponible en este equipo'
    }
  } catch (e) {
    const d = e.response?.data?.detail
    error.value = Array.isArray(d) ? d[0].msg : (d || 'Error al conectar con el servidor.')
  } finally {
    procesando.value = false
    // Listo para el siguiente cliente
    documento.value = ''
    inputDoc.value?.focus()
  }
}
</script>
