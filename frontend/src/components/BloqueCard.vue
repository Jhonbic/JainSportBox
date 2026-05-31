<template>
  <div class="bg-white rounded-2xl border border-gray-100 shadow-sm overflow-hidden">

    <!-- Header -->
    <div class="px-5 py-4 border-b border-gray-50 flex items-center justify-between gap-2">
      <h3 class="text-xl font-extrabold text-gray-900">{{ bloque.bloque }}</h3>
      <span class="bg-red-100 text-red-700 font-black text-sm px-3 py-1 rounded-full whitespace-nowrap">
        {{ visibles.length }} {{ visibles.length === 1 ? 'persona' : 'personas' }}
      </span>
    </div>

    <!-- Lista -->
    <ul class="divide-y divide-gray-50">
      <li
        v-for="a in mostrados"
        :key="a.usuario_id + a.hora_exacta"
        class="px-5 py-2.5 flex items-center justify-between gap-2">
        <span class="text-sm text-gray-700 font-medium truncate">{{ a.nombre }}</span>
        <span class="text-xs font-bold text-gray-400 bg-gray-100 px-2 py-0.5 rounded-full whitespace-nowrap">
          {{ a.hora_exacta }}
        </span>
      </li>
    </ul>

    <!-- Ver más -->
    <div v-if="visibles.length > 5" class="px-5 py-3 border-t border-gray-50">
      <button @click="expandido = !expandido" class="text-xs text-red-500 font-semibold hover:underline">
        {{ expandido ? 'Ver menos' : `+${visibles.length - 5} más` }}
      </button>
    </div>

  </div>
</template>

<script setup>
import { ref, computed } from 'vue'

const props = defineProps({
  bloque:   { type: Object, required: true },
  busqueda: { type: String, default: '' },
})

const expandido = ref(false)

const visibles = computed(() => {
  const q = props.busqueda.trim().toLowerCase()
  return q
    ? props.bloque.asistentes.filter(a => a.nombre.toLowerCase().includes(q))
    : props.bloque.asistentes
})

const mostrados = computed(() =>
  expandido.value ? visibles.value : visibles.value.slice(0, 5)
)
</script>
