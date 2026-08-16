<template>
  <!-- Pantalla completa: esta vista NO va dentro del shell de Dashboard, así el
       cliente que marca su cédula no tiene sidebar ni menú por donde salir. -->
  <div class="min-h-screen bg-gray-50 flex flex-col">

    <!-- Barra superior. Negra como el sidebar y la top bar móvil: el logo es
         blanco/rojo sobre fondo negro OPACO, en una barra blanca se vería como un
         rectángulo negro. -->
    <header class="bg-black text-white px-4 sm:px-6 py-3 flex items-center justify-between gap-3 shadow-lg">
      <div class="flex items-center gap-3 min-w-0">
        <img src="/logo.png" alt="Jain Sport Box" class="h-9 w-auto select-none flex-shrink-0" draggable="false">
        <div class="min-w-0">
          <p class="font-black leading-none">Acceso</p>
          <p class="text-xs text-gray-400 mt-1 truncate">Registra tu entrada con tu cédula</p>
        </div>
      </div>

      <!-- Kiosco activo: solo un candado discreto. Cuanto menos invite a clickearlo, mejor. -->
      <div v-if="kioscoActivo" class="flex items-center gap-2 flex-shrink-0">
        <span class="hidden sm:inline-flex items-center gap-1.5 text-xs font-bold text-gray-500 uppercase tracking-wide">
          <svg xmlns="http://www.w3.org/2000/svg" class="h-3.5 w-3.5" viewBox="0 0 20 20" fill="currentColor">
            <path fill-rule="evenodd" d="M5 9V7a5 5 0 0110 0v2a2 2 0 012 2v5a2 2 0 01-2 2H5a2 2 0 01-2-2v-5a2 2 0 012-2zm8-2v2H7V7a3 3 0 016 0z" clip-rule="evenodd" />
          </svg>
          Modo kiosco
        </span>
        <button
          @click="abrirModalSalir"
          title="Salir del modo kiosco (requiere contraseña)"
          class="p-2 rounded-lg text-gray-600 hover:text-white hover:bg-gray-800 transition-colors"
        >
          <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
          </svg>
        </button>
      </div>

      <!-- Sin kiosco: el staff puede activarlo o volver al panel -->
      <div v-else class="flex items-center gap-2 flex-shrink-0">
        <button
          @click="modalActivar = true"
          class="px-3 py-2 rounded-lg bg-red-600 hover:bg-red-700 text-white font-bold text-xs sm:text-sm transition-colors flex items-center gap-1.5"
        >
          <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" viewBox="0 0 20 20" fill="currentColor">
            <path fill-rule="evenodd" d="M5 9V7a5 5 0 0110 0v2a2 2 0 012 2v5a2 2 0 01-2 2H5a2 2 0 01-2-2v-5a2 2 0 012-2zm8-2v2H7V7a3 3 0 016 0z" clip-rule="evenodd" />
          </svg>
          <span class="hidden sm:inline">Activar modo kiosco</span>
          <span class="sm:hidden">Kiosco</span>
        </button>
        <router-link
          to="/"
          class="px-3 py-2 rounded-lg border border-gray-700 hover:border-gray-500 hover:bg-gray-800 text-gray-300 font-bold text-xs sm:text-sm transition-colors"
        >
          Volver al panel
        </router-link>
      </div>
    </header>

    <main class="flex-1 flex items-start sm:items-center justify-center p-4 sm:p-8">
      <div class="w-full max-w-xl">

        <!-- Input grande estilo recepción -->
        <form @submit.prevent="registrarAcceso" class="mb-6">
          <label class="block text-xs font-bold text-gray-500 uppercase tracking-wide mb-2">Cédula / TI</label>
          <!-- En móvil el botón va debajo y a lo ancho: en fila, el ancho intrínseco del
               input (con text-2xl) empujaba el botón fuera de la pantalla. -->
          <div class="flex flex-col sm:flex-row gap-3">
            <input
              ref="inputDoc"
              v-model="documento"
              type="text"
              inputmode="numeric"
              autocomplete="off"
              placeholder="1020456789"
              class="w-full sm:flex-1 min-w-0 px-5 py-4 rounded-2xl border-2 border-gray-200 text-2xl font-black tracking-wider text-gray-800 focus:outline-none focus:border-red-500 transition-colors placeholder:font-normal placeholder:tracking-normal placeholder:text-lg placeholder:text-gray-300"
              :disabled="procesando"
            />
            <button type="submit" :disabled="procesando || !documento.trim()"
              class="w-full sm:w-auto shrink-0 px-6 py-4 sm:py-0 rounded-2xl bg-red-600 hover:bg-red-700 disabled:bg-red-300 text-white font-black text-sm uppercase tracking-wide transition-colors flex items-center justify-center gap-2">
              <span v-if="procesando" class="animate-spin rounded-full h-5 w-5 border-b-2 border-white"></span>
              <template v-else>
                <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13.5 10.5V6.75a4.5 4.5 0 119 0v3.75M3.75 21.75h10.5a2.25 2.25 0 002.25-2.25v-6.75a2.25 2.25 0 00-2.25-2.25H3.75a2.25 2.25 0 00-2.25 2.25v6.75a2.25 2.25 0 002.25 2.25z"/>
                </svg>
                Ingresar
              </template>
            </button>
          </div>
        </form>

        <!-- Resultado: acceso permitido -->
        <div v-if="resultado" class="bg-emerald-50 border-2 border-emerald-300 rounded-2xl p-6 sm:p-8 text-center">
          <img v-if="resultado.foto_url" :src="mediaUrl(resultado.foto_url)"
            class="h-24 w-24 rounded-full object-cover mx-auto mb-4 border-4 border-white shadow" alt=""/>
          <svg v-else xmlns="http://www.w3.org/2000/svg" class="h-16 w-16 text-emerald-500 mx-auto mb-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"/>
          </svg>
          <p class="text-3xl sm:text-4xl font-black text-emerald-900 leading-tight">{{ resultado.nombre }}</p>
          <p class="text-sm font-bold text-emerald-700 uppercase tracking-wide mt-2">✓ Entrada registrada</p>

          <!-- En un bono lo que le importa al socio es cuántas entradas le quedan;
               los días pasan a la línea chica junto con la fecha de caducidad. -->
          <div class="mt-5 pt-5 border-t border-emerald-200">
            <!-- El staff entra sin membresía: no tiene días ni fecha que mostrar, y
                 sin esta rama el cartel decía "null días restantes / Invalid Date". -->
            <template v-if="resultado.es_staff">
              <p class="text-2xl font-black text-emerald-800 leading-none">Equipo del box</p>
              <p class="text-sm font-semibold text-emerald-700 mt-1">Acceso sin membresía</p>
            </template>
            <template v-else-if="resultado.ingresos_restantes !== null && resultado.ingresos_restantes !== undefined">
              <p class="text-4xl sm:text-5xl font-black text-emerald-800 leading-none">
                {{ resultado.ingresos_restantes }}
              </p>
              <p class="text-sm font-bold text-emerald-700 mt-1">
                {{ resultado.ingresos_restantes === 1 ? 'acceso restante' : 'accesos restantes' }}
              </p>
              <p class="text-xs text-emerald-600 mt-2">
                Vencen el {{ formatFecha(resultado.fecha_vencimiento) }}
                ({{ resultado.dias_restantes }} {{ resultado.dias_restantes === 1 ? 'día' : 'días' }})
              </p>
            </template>
            <template v-else>
              <p class="text-4xl sm:text-5xl font-black text-emerald-800 leading-none">
                {{ resultado.dias_restantes }}
              </p>
              <p class="text-sm font-bold text-emerald-700 mt-1">
                {{ resultado.dias_restantes === 1 ? 'día restante' : 'días restantes' }}
              </p>
              <p class="text-xs text-emerald-600 mt-2">Vence el {{ formatFecha(resultado.fecha_vencimiento) }}</p>
            </template>
          </div>

          <p v-if="avisoBridge" class="text-xs font-semibold text-gray-600 bg-white/70 rounded-lg px-3 py-2 mt-4 inline-block">
            ⚠ La entrada quedó registrada, pero no se pudo abrir la palanquera ({{ avisoBridge }}).
          </p>
        </div>

        <!-- Resultado: acceso denegado -->
        <div v-else-if="fallo" class="bg-red-50 border-2 border-red-300 rounded-2xl p-6 sm:p-8 text-center">
          <svg xmlns="http://www.w3.org/2000/svg" class="h-16 w-16 text-red-500 mx-auto mb-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M18.364 5.636a9 9 0 11-12.728 12.728 9 9 0 0112.728-12.728zM12 8v4m0 4h.01"/>
          </svg>
          <p class="text-2xl sm:text-3xl font-black text-red-800 leading-tight">{{ fallo.titulo }}</p>
          <p class="text-sm font-semibold text-red-600 mt-2">{{ fallo.detalle }}</p>
        </div>

        <!-- Fallback: la persona no aparece o es un invitado. Oculto en modo kiosco:
             abre la puerta SIN registrar entrada, y a la vista de cualquier cliente
             sería la forma obvia de meter a un amigo. -->
        <div v-if="!kioscoActivo" class="border-t border-gray-200 pt-5 mt-8">
          <p class="text-sm font-semibold text-gray-600 mb-1">¿No aparece o es un invitado?</p>
          <p class="text-xs text-gray-400 mb-3">Abre la puerta sin registrar entrada.</p>
          <div class="flex flex-wrap items-center gap-3">
            <button @click="abrirManual" :disabled="abriendoManual"
              class="px-4 py-2.5 rounded-xl border border-gray-300 hover:border-gray-500 disabled:opacity-50 text-gray-700 font-bold text-sm transition-colors flex items-center gap-2">
              <span v-if="abriendoManual" class="animate-spin rounded-full h-4 w-4 border-b-2 border-gray-500"></span>
              <svg v-else xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" viewBox="0 0 20 20" fill="currentColor">
                <path fill-rule="evenodd" d="M5 9V7a5 5 0 019.9-1 1 1 0 11-1.98.32A3 3 0 007 7v2h6a2 2 0 012 2v5a2 2 0 01-2 2H5a2 2 0 01-2-2v-5a2 2 0 012-2zm5 3a1 1 0 00-1 1v2a1 1 0 102 0v-2a1 1 0 00-1-1z" clip-rule="evenodd" />
              </svg>
              {{ abriendoManual ? 'Abriendo…' : 'Abrir palanquera' }}
            </button>
            <p v-if="manualMsg" class="text-xs font-semibold"
              :class="manualMsg.ok ? 'text-emerald-700' : 'text-red-600'">
              {{ manualMsg.ok ? '✓' : '⚠' }} {{ manualMsg.texto }}
            </p>
          </div>
        </div>

        <p class="text-xs text-gray-400 text-center mt-8">
          <template v-if="kioscoActivo">Escribe tu documento y presiona Ingresar.</template>
          <template v-else>La palanquera se abre desde la PC del gym (bridge en localhost:8001). En otros equipos solo se registra la entrada.</template>
        </p>
      </div>
    </main>

    <!-- Modal: activar el modo kiosco. No es una confirmación de rutina: explica que
         el candado es solo de ESTA pestaña, que era justo la duda razonable. -->
    <div v-if="modalActivar" class="fixed inset-0 bg-black/60 flex items-center justify-center p-4 z-50" @click.self="modalActivar = false">
      <div class="bg-white rounded-2xl p-6 w-full max-w-md shadow-2xl">
        <h3 class="text-lg font-black text-gray-800">Activar modo kiosco</h3>
        <ul class="text-sm text-gray-600 mt-3 space-y-2">
          <li class="flex gap-2">
            <span class="text-red-600 font-bold flex-shrink-0">•</span>
            <span><span class="font-semibold">Solo esta pestaña</span> queda bloqueada en Acceso. Para seguir trabajando, abre otra pestaña con tu misma sesión — el panel funciona normal ahí.</span>
          </li>
          <li class="flex gap-2">
            <span class="text-red-600 font-bold flex-shrink-0">•</span>
            <span>Acá se oculta el botón de abrir la palanquera a mano, porque abre la puerta sin registrar entrada.</span>
          </li>
          <li class="flex gap-2">
            <span class="text-red-600 font-bold flex-shrink-0">•</span>
            <span>Para desbloquear esta pestaña vas a necesitar tu contraseña.</span>
          </li>
        </ul>
        <div class="flex gap-3 mt-6">
          <button type="button" @click="modalActivar = false"
            class="flex-1 py-3 rounded-xl border border-gray-300 text-gray-600 font-semibold hover:bg-gray-50 transition-colors">
            Cancelar
          </button>
          <button type="button" @click="activar"
            class="flex-1 py-3 rounded-xl bg-red-600 hover:bg-red-700 text-white font-bold transition-colors">
            Activar
          </button>
        </div>
      </div>
    </div>

    <!-- Modal: salir del modo kiosco -->
    <div v-if="modalSalir" class="fixed inset-0 bg-black/60 flex items-center justify-center p-4 z-50" @click.self="cerrarModalSalir">
      <div class="bg-white rounded-2xl p-6 w-full max-w-sm shadow-2xl">
        <h3 class="text-lg font-black text-gray-800">Salir del modo kiosco</h3>
        <p class="text-sm text-gray-500 mt-1 mb-4">
          Escribe la contraseña de <span class="font-semibold">{{ nombreStaff }}</span> para desbloquear la pantalla.
        </p>
        <form @submit.prevent="confirmarSalir">
          <InputPassword
            ref="inputPass"
            v-model="password"
            autocomplete="current-password"
            placeholder="Contraseña"
            input-class="w-full px-4 py-3 rounded-xl border border-gray-200 focus:ring-2 focus:ring-red-500 focus:border-red-500 outline-none transition-all"
            :disabled="verificando"
          />
          <p v-if="errorPass" class="text-xs font-semibold text-red-600 mt-2">{{ errorPass }}</p>
          <div class="flex gap-3 mt-5">
            <button type="button" @click="cerrarModalSalir"
              class="flex-1 py-3 rounded-xl border border-gray-300 text-gray-600 font-semibold hover:bg-gray-50 transition-colors">
              Cancelar
            </button>
            <button type="submit" :disabled="verificando || !password"
              class="flex-1 py-3 rounded-xl bg-red-600 hover:bg-red-700 disabled:bg-red-300 text-white font-bold transition-colors flex items-center justify-center gap-2">
              <span v-if="verificando" class="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></span>
              {{ verificando ? 'Verificando…' : 'Desbloquear' }}
            </button>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, nextTick, onMounted, onBeforeUnmount } from 'vue'
import api, { mediaUrl } from '../api'
import InputPassword from '../components/InputPassword.vue'
import { kioscoActivo, activarKiosco, desactivarKiosco } from '../composables/useKiosco'

const BRIDGE_URL = 'http://localhost:8001'

// Cuánto queda en pantalla el resultado antes de limpiarse solo. En recepción la
// pantalla la ve el siguiente de la fila, así que no puede quedarse con el nombre y
// los días del cliente anterior.
const SEGUNDOS_RESULTADO = 8

const inputDoc    = ref(null)
const documento   = ref('')
const procesando  = ref(false)
const resultado   = ref(null)
const fallo       = ref(null)   // { titulo, detalle }
const avisoBridge = ref('')

const nombreStaff = ref(localStorage.getItem('userName') || 'staff')

// Apertura manual: estado propio. Si reusara resultado/fallo, abrir la puerta a un
// invitado borraría de pantalla el resultado del cliente anterior.
const abriendoManual = ref(false)
const manualMsg      = ref(null)   // { ok: bool, texto: string }

const modalActivar = ref(false)
const modalSalir   = ref(false)
const inputPass   = ref(null)
const password    = ref('')
const errorPass   = ref('')
const verificando = ref(false)

let timerResultado = null

onMounted(() => inputDoc.value?.focus())
onBeforeUnmount(() => clearTimeout(timerResultado))

const formatFecha = (f) =>
  new Date(f + 'T12:00:00').toLocaleDateString('es-CO', { day: '2-digit', month: 'short', year: 'numeric' })

function limpiarResultado() {
  clearTimeout(timerResultado)
  resultado.value = null
  fallo.value = null
  avisoBridge.value = ''
}

function programarLimpieza() {
  clearTimeout(timerResultado)
  timerResultado = setTimeout(limpiarResultado, SEGUNDOS_RESULTADO * 1000)
}

// ── Modo kiosco ──────────────────────────────────────────────────

function activar() {
  activarKiosco()
  modalActivar.value = false
  limpiarResultado()
  inputDoc.value?.focus()
}

function abrirModalSalir() {
  modalSalir.value = true
  password.value = ''
  errorPass.value = ''
  nextTick(() => inputPass.value?.focus())
}

function cerrarModalSalir() {
  modalSalir.value = false
  password.value = ''
  errorPass.value = ''
}

async function confirmarSalir() {
  if (!password.value || verificando.value) return
  verificando.value = true
  errorPass.value = ''
  try {
    await api.post('/me/verificar-password', { password: password.value })
    desactivarKiosco()
    cerrarModalSalir()
  } catch (e) {
    // El backend responde 403 (no 401) con contraseña incorrecta, justamente para
    // que el interceptor global no interprete esto como sesión expirada.
    errorPass.value = e.response?.status === 403
      ? 'Contraseña incorrecta.'
      : (e.response?.data?.detail || 'No se pudo verificar. Intenta de nuevo.')
    password.value = ''
    nextTick(() => inputPass.value?.focus())
  } finally {
    verificando.value = false
  }
}

// ── Acceso ───────────────────────────────────────────────────────

/** Abre la palanquera vía bridge local. Devuelve '' si abrió, o el motivo del fallo. */
async function abrirPalanqueraBridge() {
  try {
    const r = await fetch(`${BRIDGE_URL}/palanquera/abrir`, { method: 'POST' })
    if (!r.ok) return r.status === 503 ? 'relé no conectado' : `bridge respondió ${r.status}`
    return ''
  } catch {
    return 'bridge no disponible en este equipo'
  }
}

async function abrirManual() {
  abriendoManual.value = true
  manualMsg.value = null
  try {
    const falloBridge = await abrirPalanqueraBridge()
    manualMsg.value = falloBridge
      ? { ok: false, texto: `No se pudo abrir (${falloBridge}).` }
      : { ok: true, texto: 'Palanquera abierta' }
  } finally {
    abriendoManual.value = false
    setTimeout(() => { manualMsg.value = null }, 3500)
  }
}

/** Traduce el error del backend al cartel de recepción. */
function _falloDesde(e) {
  const status = e.response?.status
  if (status === 403) {
    // Los dos casos son 403, pero el socio tiene que hacer cosas distintas: uno
    // renueva la fecha y el otro compra más accesos. El backend manda un detail
    // estructurado solo para el de accesos (el código sigue siendo `sin_ingresos`,
    // que es el nombre del campo en la API; en pantalla se dice "accesos").
    if (e.response?.data?.detail?.codigo === 'sin_ingresos') {
      return { titulo: 'Sin accesos disponibles', detalle: 'Acércate a recepción para comprar más accesos.' }
    }
    return { titulo: 'Membresía vencida', detalle: 'Acércate a recepción para renovar tu mensualidad.' }
  }
  if (status === 404) {
    return { titulo: 'Documento no encontrado', detalle: 'Revisa el número o acércate a recepción.' }
  }
  const d = e.response?.data?.detail
  const detalle = Array.isArray(d) ? d[0].msg : (d || 'Error al conectar con el servidor.')
  return { titulo: 'No se pudo registrar', detalle }
}

async function registrarAcceso() {
  const doc = documento.value.trim()
  if (!doc || procesando.value) return
  procesando.value = true
  limpiarResultado()
  try {
    // 1) Backend: valida membresía y registra la entrada
    const { data } = await api.post(`/asistencia/por-documento/${encodeURIComponent(doc)}`)
    resultado.value = data

    // 2) Bridge local: abre la palanquera (solo funciona en la PC del gym)
    avisoBridge.value = await abrirPalanqueraBridge()
  } catch (e) {
    fallo.value = _falloDesde(e)
  } finally {
    procesando.value = false
    programarLimpieza()
    // Listo para el siguiente cliente
    documento.value = ''
    inputDoc.value?.focus()
  }
}
</script>
