<template>
  <div class="animate-fade-in-up">

    <!-- ── Header ── -->
    <div class="mb-6">
      <h2 class="text-3xl font-extrabold text-gray-900 tracking-tight">Mensajes a clientes</h2>
      <p class="text-gray-500 mt-1">Lo que el box les dice, por WhatsApp y dentro de la app</p>
    </div>

    <!-- Dos pestañas y no dos entradas en el sidebar: son dos canales de lo mismo, y el
         sidebar viene achicándose a propósito. `v-show` y no `v-if` — cada pestaña trae
         sus datos al montarse, y con `v-if` ir y volver dispararía otro fetch. -->
    <div class="flex flex-wrap gap-2 mb-6">
      <button v-for="t in TABS" :key="t.key" @click="tab = t.key"
        class="px-4 py-1.5 rounded-full text-sm font-semibold transition-colors"
        :class="tab === t.key
          ? 'bg-red-600 text-white shadow'
          : 'bg-white text-gray-600 border border-gray-200 hover:border-red-300 hover:text-red-600'">
        {{ t.label }}
      </button>
    </div>

    <div v-show="tab === 'whatsapp'"><MensajesWhatsapp /></div>
    <div v-show="tab === 'aviso'"><AvisosEditor /></div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import MensajesWhatsapp from '../components/MensajesWhatsapp.vue'
import AvisosEditor from '../components/AvisosEditor.vue'

const TABS = [
  { key: 'whatsapp', label: 'WhatsApp' },
  { key: 'aviso', label: 'Aviso en la app' },
]
const tab = ref('whatsapp')
</script>

<style>
.animate-fade-in-up {
  animation: fadeInUp 0.4s ease-out;
}
@keyframes fadeInUp {
  from { opacity: 0; transform: translateY(10px); }
  to   { opacity: 1; transform: translateY(0); }
}
</style>
