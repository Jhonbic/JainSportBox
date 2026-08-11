<template>
  <div class="min-h-screen flex items-center justify-center bg-black px-4 py-8">
    <div class="max-w-md w-full">

      <!-- Logo (se funde con el fondo negro de la página) -->
      <img src="/logo.png" alt="Jain Sport Box" class="h-36 sm:h-40 w-auto mx-auto mb-6 select-none" draggable="false">

      <div class="w-full bg-white rounded-xl shadow-lg overflow-hidden relative">
      <!-- Barra superior roja -->
      <div class="absolute top-0 left-0 w-full h-2 bg-red-600"></div>

      <!-- Espaciado superior de la tarjeta -->
      <div class="pt-8"></div>

      <!-- Tabs -->
      <div class="flex mx-8 mb-6 bg-gray-100 rounded-xl p-1">
        <button @click="tab = 'login'"
          class="flex-1 py-2 rounded-lg text-sm font-bold transition-all"
          :class="tab === 'login' ? 'bg-white shadow text-gray-900' : 'text-gray-500 hover:text-gray-700'">
          Iniciar Sesión
        </button>
        <button @click="tab = 'registro'"
          class="flex-1 py-2 rounded-lg text-sm font-bold transition-all"
          :class="tab === 'registro' ? 'bg-white shadow text-gray-900' : 'text-gray-500 hover:text-gray-700'">
          Registrarse
        </button>
      </div>

      <!-- ── FORMULARIO LOGIN ── -->
      <form v-if="tab === 'login'" @submit.prevent="handleLogin" class="px-8 pb-8 space-y-5">
        <div>
          <label class="block text-sm font-semibold text-gray-700 mb-1.5">Correo Electrónico</label>
          <input v-model="loginEmail" type="email" required
            class="w-full px-4 py-3 rounded-lg border border-gray-300 focus:ring-2 focus:ring-red-500 focus:border-red-500 outline-none transition-all text-sm"
            placeholder="ejemplo@correo.com">
        </div>
        <div>
          <label class="block text-sm font-semibold text-gray-700 mb-1.5">Contraseña</label>
          <InputPassword v-model="loginPassword" required autocomplete="current-password"
            placeholder="••••••••"
            input-class="w-full px-4 py-3 rounded-lg border border-gray-300 focus:ring-2 focus:ring-red-500 focus:border-red-500 outline-none transition-all text-sm" />
        </div>

        <div v-if="loginError" class="bg-red-50 text-red-600 text-sm p-3 rounded-lg border border-red-100 flex items-start gap-2">
          <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5 flex-shrink-0 mt-0.5" viewBox="0 0 20 20" fill="currentColor">
            <path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clip-rule="evenodd" />
          </svg>
          <span class="font-medium">{{ loginError }}</span>
        </div>

        <button type="submit" :disabled="loginLoading"
          class="w-full bg-red-600 hover:bg-red-700 disabled:bg-red-300 text-white font-bold py-3 rounded-lg shadow-md transition-all flex items-center justify-center gap-2">
          <span v-if="loginLoading" class="animate-spin rounded-full h-5 w-5 border-b-2 border-white"></span>
          {{ loginLoading ? 'Autenticando...' : 'Ingresar' }}
        </button>
      </form>

      <!-- ── FORMULARIO REGISTRO ── -->
      <form v-else @submit.prevent="handleRegistro" class="px-8 pb-8 space-y-4">

        <!-- Éxito de registro -->
        <div v-if="registroExitoso" class="bg-emerald-50 border border-emerald-200 rounded-xl p-4 text-center">
          <svg xmlns="http://www.w3.org/2000/svg" class="h-10 w-10 text-emerald-500 mx-auto mb-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          <p class="font-bold text-emerald-800">¡Registro exitoso!</p>
          <p class="text-sm text-emerald-700 mt-1">Tu cuenta está pendiente de aprobación. Inicia sesión para ver los planes disponibles.</p>
          <button type="button" @click="tab = 'login'; registroExitoso = false"
            class="mt-3 text-sm font-semibold text-emerald-700 underline hover:text-emerald-900">
            Ir a iniciar sesión
          </button>
        </div>

        <template v-else>

          <!-- Honeypot: invisible para una persona, tentador para un bot que rellena
               todos los inputs. Si viene con algo, el backend descarta el registro.
               No usa v-show ni `hidden` para que el bot no lo detecte tan fácil. -->
          <div aria-hidden="true" class="absolute w-px h-px -left-[9999px] overflow-hidden">
            <label for="sitio-web">No completar</label>
            <input id="sitio-web" v-model="regForm.sitio_web" type="text" tabindex="-1" autocomplete="off">
          </div>

          <div>
            <label class="block text-sm font-semibold text-gray-700 mb-1.5">Nombre Completo <span class="text-red-500">*</span></label>
            <input v-model="regForm.nombre" type="text" required minlength="2" maxlength="120"
              class="w-full px-4 py-2.5 rounded-lg border border-gray-300 focus:ring-2 focus:ring-red-500 outline-none transition-all text-sm">
          </div>

          <div>
            <label class="block text-sm font-semibold text-gray-700 mb-1.5">Correo Electrónico <span class="text-red-500">*</span></label>
            <input v-model="regForm.email" type="email" required
              class="w-full px-4 py-2.5 rounded-lg border border-gray-300 focus:ring-2 focus:ring-red-500 outline-none transition-all text-sm"
              placeholder="ejemplo@correo.com">
          </div>

          <div>
            <label class="block text-sm font-semibold text-gray-700 mb-1.5">Documento de Identidad <span class="text-red-500">*</span></label>
            <input v-model="regForm.documento_identidad" type="text" required minlength="5" maxlength="20"
              class="w-full px-4 py-2.5 rounded-lg border border-gray-300 focus:ring-2 focus:ring-red-500 outline-none transition-all text-sm">
          </div>

          <div>
            <label class="block text-sm font-semibold text-gray-700 mb-1.5">Teléfono / WhatsApp <span class="text-red-500">*</span></label>
            <input v-model="regForm.telefono" type="tel" required minlength="7" maxlength="20"
              class="w-full px-4 py-2.5 rounded-lg border border-gray-300 focus:ring-2 focus:ring-red-500 outline-none transition-all text-sm">
          </div>

          <div>
            <label class="block text-sm font-semibold text-gray-700 mb-1.5">Fecha de Nacimiento <span class="text-red-500">*</span></label>
            <input v-model="regForm.fecha_nacimiento" type="date" required :max="hoyISO"
              class="w-full px-4 py-2.5 rounded-lg border border-gray-300 focus:ring-2 focus:ring-red-500 outline-none transition-all text-sm">
            <p v-if="edad !== null" class="text-xs text-gray-400 mt-1">Edad: {{ edad }} años</p>
          </div>

          <div>
            <label class="block text-sm font-semibold text-gray-700 mb-1.5">EPS <span class="text-red-500">*</span></label>
            <input v-model="regForm.eps" type="text" required minlength="2" maxlength="100"
              class="w-full px-4 py-2.5 rounded-lg border border-gray-300 focus:ring-2 focus:ring-red-500 outline-none transition-all text-sm">
          </div>

          <div>
            <label class="block text-sm font-semibold text-gray-700 mb-1.5">Barrio <span class="text-red-500">*</span></label>
            <input v-model="regForm.barrio" type="text" required minlength="2" maxlength="100"
              class="w-full px-4 py-2.5 rounded-lg border border-gray-300 focus:ring-2 focus:ring-red-500 outline-none transition-all text-sm">
          </div>

          <!-- Contacto de emergencia -->
          <div class="border border-gray-200 rounded-xl p-4 space-y-3">
            <p class="text-sm font-bold text-gray-700">Contacto de emergencia</p>
            <div>
              <label class="block text-sm font-semibold text-gray-700 mb-1.5">Nombre <span class="text-red-500">*</span></label>
              <input v-model="regForm.contacto_emergencia_nombre" type="text" required minlength="2" maxlength="120"
                class="w-full px-4 py-2.5 rounded-lg border border-gray-300 focus:ring-2 focus:ring-red-500 outline-none transition-all text-sm">
            </div>
            <div>
              <label class="block text-sm font-semibold text-gray-700 mb-1.5">Teléfono <span class="text-red-500">*</span></label>
              <input v-model="regForm.contacto_emergencia_telefono" type="tel" required minlength="7" maxlength="20"
                class="w-full px-4 py-2.5 rounded-lg border border-gray-300 focus:ring-2 focus:ring-red-500 outline-none transition-all text-sm">
            </div>
          </div>

          <div>
            <label class="block text-sm font-semibold text-gray-700 mb-1.5">Género <span class="text-red-500">*</span></label>
            <div class="grid grid-cols-2 gap-2">
              <button type="button" @click="regForm.genero = 'masculino'"
                class="py-2.5 rounded-lg border text-sm font-semibold transition-colors"
                :class="regForm.genero === 'masculino' ? 'border-gray-800 bg-gray-800 text-white' : 'border-gray-300 text-gray-500 hover:border-gray-400'">
                Masculino
              </button>
              <button type="button" @click="regForm.genero = 'femenino'"
                class="py-2.5 rounded-lg border text-sm font-semibold transition-colors"
                :class="regForm.genero === 'femenino' ? 'border-gray-800 bg-gray-800 text-white' : 'border-gray-300 text-gray-500 hover:border-gray-400'">
                Femenino
              </button>
            </div>
          </div>

          <div>
            <label class="block text-sm font-semibold text-gray-700 mb-1.5">Contraseña <span class="text-red-500">*</span></label>
            <InputPassword v-model="regForm.password" required minlength="6" autocomplete="new-password"
              placeholder="Mínimo 6 caracteres"
              input-class="w-full px-4 py-2.5 rounded-lg border border-gray-300 focus:ring-2 focus:ring-red-500 outline-none transition-all text-sm" />
          </div>

          <!-- Menor de edad: aparece automáticamente según la fecha de nacimiento -->
          <div v-if="esMenor" class="border border-red-300 bg-red-50 rounded-xl p-4 space-y-3">
            <label class="flex items-start gap-2.5 cursor-pointer">
              <input v-model="regForm.es_menor" type="checkbox" required
                class="mt-0.5 h-4 w-4 rounded border-gray-300 text-red-600 focus:ring-red-500">
              <span class="text-sm text-red-900">
                <span class="font-bold">Confirmo que la persona a registrar es menor de edad</span> y declaro, como padre, madre,
                tutor legal o representante autorizado, que acepto este registro en su nombre (cláusula 7 del contrato).
              </span>
            </label>
            <div>
              <label class="block text-sm font-semibold text-gray-700 mb-1.5">Nombre del acudiente <span class="text-red-500">*</span></label>
              <input v-model="regForm.acudiente_nombre" type="text" required minlength="2" maxlength="120"
                class="w-full px-4 py-2.5 rounded-lg border border-gray-300 focus:ring-2 focus:ring-red-500 outline-none transition-all text-sm">
            </div>
            <div>
              <label class="block text-sm font-semibold text-gray-700 mb-1.5">Cédula del acudiente <span class="text-red-500">*</span></label>
              <input v-model="regForm.acudiente_documento" type="text" required minlength="5" maxlength="20"
                class="w-full px-4 py-2.5 rounded-lg border border-gray-300 focus:ring-2 focus:ring-red-500 outline-none transition-all text-sm">
            </div>
            <div>
              <label class="block text-sm font-semibold text-gray-700 mb-1.5">Teléfono del acudiente <span class="text-red-500">*</span></label>
              <input v-model="regForm.acudiente_telefono" type="tel" required minlength="7" maxlength="20"
                class="w-full px-4 py-2.5 rounded-lg border border-gray-300 focus:ring-2 focus:ring-red-500 outline-none transition-all text-sm">
            </div>
          </div>

          <!-- Aceptación de términos y condiciones -->
          <label class="flex items-start gap-2.5 cursor-pointer">
            <input v-model="regForm.acepta_terminos" type="checkbox" required
              class="mt-0.5 h-4 w-4 rounded border-gray-300 text-red-600 focus:ring-red-500">
            <span class="text-sm text-gray-600">
              Acepto los
              <button type="button" @click.prevent="mostrarTerminos = true"
                class="font-bold text-red-600 underline hover:text-red-700">
                Términos, Condiciones y el Consentimiento Informado
              </button>
              de Jain Sport Box. <span class="text-red-500">*</span>
            </span>
          </label>

          <div v-if="registroError" class="bg-red-50 text-red-600 text-sm p-3 rounded-lg border border-red-100 flex items-start gap-2">
            <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5 flex-shrink-0 mt-0.5" viewBox="0 0 20 20" fill="currentColor">
              <path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clip-rule="evenodd" />
            </svg>
            <span class="font-medium">{{ registroError }}</span>
          </div>

          <button type="submit" :disabled="registroLoading"
            class="w-full bg-red-600 hover:bg-red-700 disabled:bg-red-300 text-white font-bold py-3 rounded-lg shadow-md transition-all flex items-center justify-center gap-2">
            <span v-if="registroLoading" class="animate-spin rounded-full h-5 w-5 border-b-2 border-white"></span>
            {{ registroLoading ? 'Registrando...' : 'Crear Cuenta' }}
          </button>
        </template>
      </form>
      </div>
    </div>

    <!-- Modal de Términos y Condiciones -->
    <TerminosModal v-if="mostrarTerminos"
      @cerrar="mostrarTerminos = false"
      @aceptar="regForm.acepta_terminos = true; mostrarTerminos = false" />
  </div>
</template>

<script setup>
import { computed, ref, watch } from 'vue'
import api from '../api'
import { useRouter } from 'vue-router'
import TerminosModal from '../components/TerminosModal.vue'
import InputPassword from '../components/InputPassword.vue'
import { desactivarKiosco } from '../composables/useKiosco'

const router = useRouter()
const tab = ref('login')

// ── Login ──────────────────────────────────────────────────────
const loginEmail = ref('')
const loginPassword = ref('')
const loginError = ref('')
const loginLoading = ref(false)

const handleLogin = async () => {
  loginError.value = ''
  loginLoading.value = true
  try {
    const formData = new URLSearchParams()
    formData.append('username', loginEmail.value)
    formData.append('password', loginPassword.value)
    const { data } = await api.post('/login', formData)
    localStorage.setItem('token', data.access_token)

    const me = await api.get('/me')
    localStorage.setItem('userRol', me.data.rol)
    localStorage.setItem('userName', me.data.nombre)
    localStorage.setItem('fechaVencimiento', me.data.fecha_vencimiento || '')

    // Quien acaba de escribir email y contraseña es staff, no un cliente en el
    // mostrador: si había un kiosco activo en esta pestaña, se libera. Sin esto el
    // guard lo dejaría encerrado en /acceso justo después de loguearse.
    desactivarKiosco()

    // Con `await`. Sin él, el `finally` apagaba el spinner apenas se dispara la
    // navegación, pero la vista de destino es una ruta lazy y todavía tiene que
    // bajar su chunk: el botón volvía a "Ingresar" y la pantalla de login se quedaba
    // quieta unos instantes antes de saltar, que es exactamente la sensación de que
    // el sistema se colgó.
    await router.push('/')
  } catch (e) {
    loginError.value = e.response?.status === 401
      ? 'Credenciales incorrectas. Verifica tu email y contraseña.'
      : 'Error al conectar con el servidor.'
  } finally {
    loginLoading.value = false
  }
}

// ── Registro ───────────────────────────────────────────────────
const REG_FORM_VACIO = () => ({
  nombre: '', email: '', documento_identidad: '', telefono: '', genero: '', password: '',
  fecha_nacimiento: '', eps: '', barrio: '',
  contacto_emergencia_nombre: '', contacto_emergencia_telefono: '',
  acepta_terminos: false, es_menor: false, acudiente_nombre: '', acudiente_telefono: '', acudiente_documento: '',
  sitio_web: '',  // honeypot: si llega con algo, el backend descarta el registro
})
const regForm = ref(REG_FORM_VACIO())
const registroError = ref('')
const registroLoading = ref(false)
const registroExitoso = ref(false)
const mostrarTerminos = ref(false)

const hoyISO = new Date().toISOString().slice(0, 10)

// Edad calculada a partir de la fecha de nacimiento (no se envía: el backend la deriva).
const edad = computed(() => {
  if (!regForm.value.fecha_nacimiento) return null
  const nac = new Date(regForm.value.fecha_nacimiento + 'T00:00:00')
  const hoy = new Date()
  let e = hoy.getFullYear() - nac.getFullYear()
  if (hoy.getMonth() < nac.getMonth() || (hoy.getMonth() === nac.getMonth() && hoy.getDate() < nac.getDate())) e--
  return e
})
const esMenor = computed(() => edad.value !== null && edad.value >= 0 && edad.value < 18)

// Si cambia la fecha y ya no es menor, limpiar la sección de acudiente.
watch(esMenor, (v) => {
  if (!v) {
    regForm.value.es_menor = false
    regForm.value.acudiente_nombre = ''
    regForm.value.acudiente_telefono = ''
    regForm.value.acudiente_documento = ''
  }
})

const handleRegistro = async () => {
  registroError.value = ''
  if (!regForm.value.genero) {
    registroError.value = 'Selecciona tu género.'
    return
  }
  if (!regForm.value.acepta_terminos) {
    registroError.value = 'Debes aceptar los Términos, Condiciones y el Consentimiento Informado.'
    return
  }
  if (esMenor.value && !regForm.value.es_menor) {
    registroError.value = 'Según la fecha de nacimiento eres menor de edad: marca la casilla y registra los datos del acudiente.'
    return
  }
  registroLoading.value = true
  try {
    const fd = new FormData()
    fd.append('nombre', regForm.value.nombre)
    fd.append('email', regForm.value.email)
    fd.append('password', regForm.value.password)
    fd.append('documento_identidad', regForm.value.documento_identidad)
    fd.append('genero', regForm.value.genero)
    fd.append('telefono', regForm.value.telefono)
    fd.append('fecha_nacimiento', regForm.value.fecha_nacimiento)
    fd.append('eps', regForm.value.eps)
    fd.append('barrio', regForm.value.barrio)
    fd.append('contacto_emergencia_nombre', regForm.value.contacto_emergencia_nombre)
    fd.append('contacto_emergencia_telefono', regForm.value.contacto_emergencia_telefono)
    fd.append('acepta_terminos', regForm.value.acepta_terminos ? 'true' : 'false')
    fd.append('es_menor', regForm.value.es_menor ? 'true' : 'false')
    if (regForm.value.es_menor) {
      fd.append('acudiente_nombre', regForm.value.acudiente_nombre)
      fd.append('acudiente_telefono', regForm.value.acudiente_telefono)
      fd.append('acudiente_documento', regForm.value.acudiente_documento)
    }
    fd.append('sitio_web', regForm.value.sitio_web)

    await api.post('/registro', fd, { headers: { 'Content-Type': 'multipart/form-data' } })
    registroExitoso.value = true
    regForm.value = REG_FORM_VACIO()
  } catch (e) {
    const d = e.response?.data?.detail
    registroError.value = Array.isArray(d) ? d[0].msg : (d || 'Error al registrar la cuenta.')
  } finally {
    registroLoading.value = false
  }
}
</script>
