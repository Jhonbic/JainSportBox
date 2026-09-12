<template>
  <Teleport to="body">
    <div v-if="aviso" class="fixed inset-0 z-[60] flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm"
      @click.self="cerrar">
      <div class="bg-white rounded-3xl shadow-2xl w-full max-w-md overflow-hidden animate-aviso-in">

        <!-- Franja de marca: el cartel tiene que leerse como del box y no como un popup
             cualquiera de internet, que es lo que se cierra sin leer. -->
        <div class="h-1.5 bg-red-600"></div>

        <div class="p-6">
          <div class="flex items-start justify-between gap-3 mb-3">
            <h3 class="text-xl font-extrabold text-gray-900 leading-tight">{{ aviso.titulo }}</h3>
            <button @click="cerrar" aria-label="Cerrar"
              class="flex-shrink-0 -mt-1 -mr-1 p-1.5 rounded-lg text-gray-400 hover:text-gray-700 hover:bg-gray-100 transition-colors">
              <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                <path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>

          <!-- `whitespace-pre-line` y no v-html: el cuerpo lo escribe el admin y los
               saltos de línea son lo único que necesita para separar párrafos. Meterlo
               como HTML abriría la puerta a inyectar markup en la pantalla del cliente
               a cambio de nada. -->
          <p class="text-gray-600 leading-relaxed whitespace-pre-line">{{ aviso.cuerpo }}</p>

          <!-- Botón opcional. Interno va por el router (no recarga la SPA); externo,
               con noopener por el target _blank. -->
          <div v-if="aviso.boton_texto && aviso.boton_url" class="mt-5">
            <RouterLink v-if="esInterno" :to="aviso.boton_url" @click="cerrar"
              class="block w-full text-center bg-red-600 hover:bg-red-700 text-white font-bold py-3 px-5 rounded-xl shadow transition-colors">
              {{ aviso.boton_texto }}
            </RouterLink>
            <a v-else :href="aviso.boton_url" target="_blank" rel="noopener noreferrer" @click="cerrar"
              class="block w-full text-center bg-red-600 hover:bg-red-700 text-white font-bold py-3 px-5 rounded-xl shadow transition-colors">
              {{ aviso.boton_texto }}
            </a>
          </div>
        </div>

        <div class="px-6 py-4 bg-gray-50 border-t border-gray-100">
          <label class="flex items-center gap-2.5 cursor-pointer select-none">
            <input type="checkbox" v-model="noMostrar"
              class="h-4 w-4 rounded border-gray-300 text-red-600 focus:ring-red-500 cursor-pointer">
            <span class="text-sm text-gray-500">No volver a mostrar este aviso</span>
          </label>
        </div>
      </div>
    </div>
  </Teleport>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { RouterLink } from 'vue-router'
import api from '../api'

const aviso = ref(null)
const noMostrar = ref(false)

const esInterno = computed(() => aviso.value?.boton_url?.startsWith('/'))

/** Clave de "ya lo cerré en esta pestaña".
 *
 *  sessionStorage y no localStorage: cerrar sin tildar la casilla tiene que volver a
 *  mostrarlo la próxima vez que abra la app —es lo pedido—, pero recargar la página
 *  cinco veces seguidas no debería traer el cartel cinco veces. sessionStorage muere
 *  al cerrar la pestaña, que es exactamente esa distinción. */
const claveSesion = (id) => `aviso_cerrado:${id}`

async function cargar() {
  try {
    const { data } = await api.get('/avisos/mio')
    const a = data?.aviso
    if (!a) return
    if (sessionStorage.getItem(claveSesion(a.id))) return
    aviso.value = a
  } catch {
    // Silencioso a propósito: un aviso es lo menos importante de la pantalla. Si el
    // endpoint falla, el cliente entra a su cuenta como siempre y no ve nada raro.
  }
}

async function cerrar() {
  const id = aviso.value?.id
  const persistir = noMostrar.value
  aviso.value = null
  if (!id) return
  try { sessionStorage.setItem(claveSesion(id), '1') } catch { /* modo privado */ }
  if (!persistir) return
  // El cartel ya se fue de la pantalla antes de esperar la respuesta: que el "no volver
  // a mostrar" quede guardado importa, pero no al punto de dejar el modal abierto
  // mientras viaja el request.
  try { await api.post(`/avisos/${id}/visto`) } catch { /* lo vuelve a ver, no es grave */ }
}

onMounted(cargar)
</script>

<style scoped>
.animate-aviso-in {
  animation: avisoIn 0.25s cubic-bezier(0.16, 1, 0.3, 1);
}
@keyframes avisoIn {
  from { opacity: 0; transform: translateY(12px) scale(0.97); }
  to   { opacity: 1; transform: translateY(0) scale(1); }
}
</style>
