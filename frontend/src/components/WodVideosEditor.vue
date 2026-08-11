<template>
  <div>
    <label class="block text-sm font-semibold text-gray-700 mb-1">Videos</label>
    <p class="text-xs text-gray-400 mb-2.5">
      Los videos que el cliente debe ver. La rutina va en el campo de notas.
    </p>

    <!-- Selector + agregar -->
    <div class="flex gap-2 mb-3">
      <select
        v-model="seleccionado"
        class="flex-1 px-3 py-2.5 rounded-lg border border-gray-300 focus:ring-2 focus:ring-red-500 focus:border-red-500 outline-none transition-all text-sm bg-white"
      >
        <option value="">Selecciona un video…</option>
        <option v-for="ej in disponibles" :key="ej.id" :value="ej.id">
          {{ ej.nombre }}{{ ej.video_url ? '' : ' · sin video' }}
        </option>
      </select>
      <button
        type="button"
        @click="agregar"
        :disabled="!seleccionado"
        class="px-4 py-2.5 rounded-lg bg-gray-800 hover:bg-gray-900 text-white font-semibold text-sm transition-colors disabled:opacity-40 disabled:cursor-not-allowed"
      >
        Agregar
      </button>
    </div>

    <p v-if="catalogo.length === 0" class="text-xs text-gray-400 italic mb-3">
      No hay ejercicios en el catálogo. Créalos con su link de video en la sección
      <span class="font-semibold">Ejercicios</span>.
    </p>

    <!-- Lista de seleccionados -->
    <div v-if="items.length > 0" class="space-y-2">
      <div
        v-for="(it, idx) in items"
        :key="it.ejercicio_id"
        class="flex items-center justify-between gap-2 rounded-lg p-3 border bg-gray-50 border-gray-200"
      >
        <div class="flex items-center gap-2 min-w-0">
          <span class="text-xs font-bold text-gray-400 w-5 flex-shrink-0">{{ idx + 1 }}.</span>
          <span class="font-semibold text-gray-800 text-sm truncate">{{ it.nombre }}</span>
          <span v-if="it.video_url" class="flex-shrink-0 inline-flex items-center text-red-500" title="Tiene video">
            <svg xmlns="http://www.w3.org/2000/svg" class="h-3.5 w-3.5" fill="currentColor" viewBox="0 0 24 24"><path d="M8 5v14l11-7z" /></svg>
          </span>
          <span
            v-else
            class="flex-shrink-0 text-xs font-semibold px-1.5 py-0.5 rounded-full bg-amber-50 text-amber-700"
            title="Este ejercicio no tiene link de video en el catálogo"
          >
            sin video
          </span>
        </div>
        <div class="flex items-center gap-1 flex-shrink-0">
          <button type="button" @click="mover(idx, -1)" :disabled="idx === 0" class="p-1 rounded text-gray-400 hover:bg-gray-200 disabled:opacity-30" title="Subir">
            <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 15l7-7 7 7" /></svg>
          </button>
          <button type="button" @click="mover(idx, 1)" :disabled="idx === items.length - 1" class="p-1 rounded text-gray-400 hover:bg-gray-200 disabled:opacity-30" title="Bajar">
            <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" /></svg>
          </button>
          <button type="button" @click="quitar(idx)" class="p-1 rounded text-gray-400 hover:bg-red-100 hover:text-red-600" title="Quitar">
            <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" /></svg>
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue'

const props = defineProps({
  modelValue: { type: Array, default: () => [] },
  catalogo: { type: Array, default: () => [] },
})
const emit = defineEmits(['update:modelValue'])

const items        = ref([...props.modelValue])
const seleccionado = ref('')

watch(() => props.modelValue, (val) => {
  items.value = [...val]
}, { deep: true })

const disponibles = computed(() =>
  props.catalogo.filter(ej => !items.value.some(it => it.ejercicio_id === ej.id))
)

function emitir() {
  emit('update:modelValue', items.value.map(it => ({ ...it })))
}

function agregar() {
  if (!seleccionado.value) return
  const ej = props.catalogo.find(e => e.id === seleccionado.value)
  if (!ej) return
  items.value.push({
    ejercicio_id: ej.id,
    nombre:       ej.nombre,
    video_url:    ej.video_url,
  })
  seleccionado.value = ''
  emitir()
}

function quitar(idx) {
  items.value.splice(idx, 1)
  emitir()
}

function mover(idx, dir) {
  const destino = idx + dir
  if (destino < 0 || destino >= items.value.length) return
  const [el] = items.value.splice(idx, 1)
  items.value.splice(destino, 0, el)
  emitir()
}
</script>
