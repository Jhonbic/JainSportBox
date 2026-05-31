<template>
  <div v-if="ejercicio" class="animate-fade-in-up">

    <!-- Header -->
    <div class="flex items-center gap-3 mb-6">
      <RouterLink :to="{ name: 'Marcas' }"
        class="flex items-center gap-1.5 text-sm font-semibold text-gray-400 hover:text-gray-700 transition-colors">
        <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7"/>
        </svg>
        Mis Marcas
      </RouterLink>
      <span class="text-gray-200">/</span>
      <h2 class="text-2xl font-extrabold text-gray-900 truncate">{{ ejercicio }}</h2>
    </div>

    <!-- Skeleton -->
    <div v-if="cargando" class="space-y-5">
      <div class="bg-gray-100 rounded-2xl h-28 animate-pulse"></div>
      <div class="bg-gray-100 rounded-2xl h-72 animate-pulse"></div>
      <div class="bg-gray-100 rounded-2xl h-64 animate-pulse"></div>
    </div>

    <template v-else>

      <!-- Resumen + botón -->
      <div class="bg-white rounded-2xl border border-gray-100 shadow-sm p-5 mb-5 flex items-start justify-between gap-4">
        <div class="flex gap-6 flex-wrap">

          <!-- ── barra / corporal_lastre ── -->
          <template v-if="esTipoPeso">
            <div>
              <p class="text-xs font-bold uppercase tracking-widest text-gray-400 mb-1">Último 1RM</p>
              <p class="text-4xl font-black text-gray-900 leading-none" v-if="ultimoRM">
                {{ ultimoRM }}<span class="text-lg font-semibold text-gray-400 ml-1">{{ ultimaUnidad }}</span>
              </p>
              <p v-else class="text-4xl font-black text-gray-300">—</p>
            </div>
            <div v-if="mejorRM && mejorRM !== ultimoRM">
              <p class="text-xs font-bold uppercase tracking-widest text-amber-500 mb-1">Mejor 1RM (PR)</p>
              <p class="text-4xl font-black text-amber-600 leading-none">
                {{ mejorRM }}<span class="text-lg font-semibold text-amber-400 ml-1">{{ ultimaUnidad }}</span>
              </p>
            </div>
            <div v-if="mejorRM === ultimoRM && registros.length > 0">
              <p class="text-xs font-bold uppercase tracking-widest text-amber-500 mb-1">Estado</p>
              <span class="inline-block text-xs font-black px-3 py-1.5 rounded-full bg-amber-100 text-amber-700">PR Actual</span>
            </div>
          </template>

          <!-- ── reps ── -->
          <template v-else-if="tipo === 'reps'">
            <div>
              <p class="text-xs font-bold uppercase tracking-widest text-gray-400 mb-1">Última marca</p>
              <p class="text-4xl font-black text-gray-900 leading-none" v-if="ultimaReps">
                {{ ultimaReps }}<span class="text-lg font-semibold text-gray-400 ml-1">reps</span>
              </p>
              <p v-else class="text-4xl font-black text-gray-300">—</p>
            </div>
            <div v-if="mejorReps && mejorReps !== ultimaReps">
              <p class="text-xs font-bold uppercase tracking-widest text-amber-500 mb-1">PR (max reps)</p>
              <p class="text-4xl font-black text-amber-600 leading-none">
                {{ mejorReps }}<span class="text-lg font-semibold text-amber-400 ml-1">reps</span>
              </p>
            </div>
            <div v-if="mejorReps === ultimaReps && registros.length > 0">
              <p class="text-xs font-bold uppercase tracking-widest text-amber-500 mb-1">Estado</p>
              <span class="inline-block text-xs font-black px-3 py-1.5 rounded-full bg-amber-100 text-amber-700">PR Actual</span>
            </div>
          </template>

          <!-- ── leger ── -->
          <template v-else-if="tipo === 'leger'">
            <div>
              <p class="text-xs font-bold uppercase tracking-widest text-gray-400 mb-1">Último nivel</p>
              <p class="text-4xl font-black text-gray-900 leading-none" v-if="ultimoLeger">
                {{ ultimoLeger.nivel }}<span class="text-lg font-semibold text-gray-400">.{{ ultimoLeger.palier }}</span>
              </p>
              <p v-else class="text-4xl font-black text-gray-300">—</p>
            </div>
            <div v-if="mejorLeger && (mejorLeger.nivel !== ultimoLeger?.nivel || mejorLeger.palier !== ultimoLeger?.palier)">
              <p class="text-xs font-bold uppercase tracking-widest text-amber-500 mb-1">PR</p>
              <p class="text-4xl font-black text-amber-600 leading-none">
                {{ mejorLeger.nivel }}<span class="text-lg font-semibold text-amber-400">.{{ mejorLeger.palier }}</span>
              </p>
            </div>
            <div v-if="mejorLeger && ultimoLeger && mejorLeger.nivel === ultimoLeger.nivel && mejorLeger.palier === ultimoLeger.palier">
              <p class="text-xs font-bold uppercase tracking-widest text-amber-500 mb-1">Estado</p>
              <span class="inline-block text-xs font-black px-3 py-1.5 rounded-full bg-amber-100 text-amber-700">PR Actual</span>
            </div>
          </template>

        </div>
        <button @click="abrirModal"
          class="shrink-0 flex items-center gap-2 bg-red-600 hover:bg-red-700 text-white font-bold py-3 px-5 rounded-xl shadow-sm transition-colors">
          <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M12 4v16m8-8H4"/>
          </svg>
          Registrar
        </button>
      </div>

      <!-- Gráfica -->
      <div class="bg-white rounded-2xl border border-gray-100 shadow-sm p-5 mb-5">
        <h3 class="font-bold text-gray-800 mb-4 flex items-center gap-2">
          <span class="w-3 h-3 rounded-full bg-red-400 inline-block"></span>
          {{ tituloGrafica }}
        </h3>
        <div v-if="registros.length >= 2" class="relative h-64">
          <canvas ref="chartCanvas"></canvas>
        </div>
        <div v-else class="h-28 flex flex-col items-center justify-center text-gray-400 text-sm gap-2">
          <svg xmlns="http://www.w3.org/2000/svg" class="h-8 w-8 text-gray-200" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M7 12l3-3 3 3 4-4M8 21l4-4 4 4M3 4h18M4 4h16v12a1 1 0 01-1 1H5a1 1 0 01-1-1V4z"/>
          </svg>
          <span>Agrega al menos 2 registros para ver la gráfica</span>
        </div>
      </div>

      <!-- Tabla rep-max + Comparación de fórmulas (solo barra / corporal_lastre) -->
      <template v-if="esTipoPeso && registros.length > 0">
        <div class="bg-white rounded-2xl border border-gray-100 shadow-sm overflow-hidden mb-5">
          <div class="px-6 py-4 border-b border-gray-100">
            <h3 class="font-bold text-gray-800">Peso máximo estimado por repeticiones</h3>
            <p class="text-xs text-gray-400 mt-0.5">Calculado desde tu último 1RM de {{ ultimoRM }} {{ ultimaUnidad }}</p>
          </div>
          <div class="overflow-x-auto">
            <table class="min-w-full">
              <thead class="bg-gray-50">
                <tr>
                  <th class="px-6 py-3 text-left text-xs font-bold text-gray-400 uppercase tracking-wider">Repeticiones</th>
                  <th class="px-6 py-3 text-center text-xs font-bold text-red-500 uppercase tracking-wider">Peso estimado (promedio)</th>
                </tr>
              </thead>
              <tbody class="divide-y divide-gray-50">
                <tr v-for="fila in tablaRepMax" :key="fila.reps"
                  :class="fila.reps === 1 ? 'bg-red-50' : 'hover:bg-gray-50'"
                  class="transition-colors">
                  <td class="px-6 py-3">
                    <span class="flex items-center gap-1.5">
                      <span class="text-sm font-black text-gray-900">{{ fila.reps }}</span>
                      <span v-if="fila.reps === 1" class="text-xs font-bold px-1.5 py-0.5 rounded-full bg-red-100 text-red-600">1RM</span>
                    </span>
                  </td>
                  <td class="px-6 py-3 text-center">
                    <span class="text-sm font-black text-red-600">{{ fila.promedio }}</span>
                    <span class="text-xs text-gray-400 ml-1">{{ ultimaUnidad }}</span>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>

        <div v-if="formulasUltimo" class="bg-white rounded-2xl border border-gray-100 shadow-sm overflow-hidden mb-5">
          <div class="px-6 py-4 border-b border-gray-100">
            <h3 class="font-bold text-gray-800">Comparación de fórmulas</h3>
            <p class="text-xs text-gray-400 mt-0.5">
              Basado en tu último registro: {{ formulasUltimo.peso }} {{ formulasUltimo.unidad }} × {{ formulasUltimo.reps }} reps
            </p>
          </div>
          <div v-for="f in formulasUltimo.detalle" :key="f.nombre"
            class="flex items-center justify-between px-6 py-3 border-b border-gray-50 last:border-0 hover:bg-gray-50 transition-colors">
            <span class="text-sm font-semibold text-gray-600">{{ f.nombre }}</span>
            <span class="text-sm font-black text-gray-900">{{ f.valor }} <span class="text-xs font-normal text-gray-400">{{ formulasUltimo.unidad }}</span></span>
          </div>
          <div class="px-6 py-3 bg-red-50 border-t border-red-100 flex items-center justify-between">
            <span class="text-xs font-bold text-red-500 uppercase tracking-widest">Promedio (1RM guardado)</span>
            <span class="text-xl font-black text-red-700">{{ formulasUltimo.promedio }} <span class="text-sm font-semibold text-red-400">{{ formulasUltimo.unidad }}</span></span>
          </div>
        </div>
      </template>

      <!-- Historial -->
      <div class="bg-white rounded-2xl border border-gray-100 shadow-sm overflow-hidden">
        <div class="px-6 py-4 border-b border-gray-100 flex items-center justify-between">
          <h3 class="font-bold text-gray-800">Historial</h3>
          <span class="text-xs text-gray-400">{{ registros.length }} registros</span>
        </div>
        <div v-if="registros.length === 0" class="px-6 py-12 text-center text-gray-400 text-sm">
          Sin registros. Presiona <strong>Registrar</strong> para añadir tu primera marca.
        </div>
        <div v-else class="overflow-x-auto">
          <table class="min-w-full divide-y divide-gray-100">
            <thead class="bg-gray-50">
              <tr>
                <th class="px-5 py-3 text-left text-xs font-bold text-gray-400 uppercase tracking-wider">Fecha</th>
                <th class="px-5 py-3 text-left text-xs font-bold text-gray-400 uppercase tracking-wider">{{ encabezadoMedicion }}</th>
                <th v-if="esTipoPeso" class="px-5 py-3 text-left text-xs font-bold text-gray-400 uppercase tracking-wider">1RM estimado</th>
                <th class="px-5 py-3 text-left text-xs font-bold text-gray-400 uppercase tracking-wider">Notas</th>
                <th class="px-5 py-3"></th>
              </tr>
            </thead>
            <tbody class="divide-y divide-gray-50">
              <tr v-for="r in [...registros].reverse()" :key="r.id"
                class="hover:bg-gray-50 transition-colors group">
                <td class="px-5 py-3.5 text-sm font-medium text-gray-700 whitespace-nowrap">
                  {{ formatFecha(r.fecha) }}
                </td>
                <td class="px-5 py-3.5 whitespace-nowrap">
                  <!-- barra -->
                  <template v-if="tipo === 'barra'">
                    <span class="text-sm font-bold text-gray-900">{{ r.peso }} {{ r.unidad }}</span>
                    <span class="text-gray-400 mx-1">×</span>
                    <span class="text-sm font-bold text-gray-900">{{ r.repeticiones }}</span>
                    <span class="text-xs text-gray-400 ml-1">reps</span>
                  </template>
                  <!-- corporal_lastre -->
                  <template v-else-if="tipo === 'corporal_lastre'">
                    <span class="text-sm font-bold text-gray-900">{{ r.peso }} {{ r.unidad }}</span>
                    <span v-if="r.peso_adicional" class="text-xs text-gray-500 ml-1">(+{{ r.peso_adicional }} lastre)</span>
                    <span class="text-gray-400 mx-1">×</span>
                    <span class="text-sm font-bold text-gray-900">{{ r.repeticiones }}</span>
                    <span class="text-xs text-gray-400 ml-1">reps</span>
                  </template>
                  <!-- reps -->
                  <template v-else-if="tipo === 'reps'">
                    <span class="text-sm font-bold text-gray-900">{{ r.repeticiones }}</span>
                    <span class="text-xs text-gray-400 ml-1">reps</span>
                  </template>
                  <!-- leger -->
                  <template v-else-if="tipo === 'leger'">
                    <span class="text-sm font-bold text-gray-900">Nivel {{ r.nivel }}</span>
                    <span class="text-xs text-gray-400 ml-1">· palier {{ r.palier }}</span>
                  </template>
                </td>
                <td v-if="esTipoPeso" class="px-5 py-3.5 whitespace-nowrap">
                  <span class="text-sm font-black text-red-600">{{ r.rm_calculado }} {{ r.unidad }}</span>
                  <span v-if="esRegistroPR(r)"
                    class="ml-2 text-xs font-bold px-2 py-0.5 rounded-full bg-amber-100 text-amber-700">PR</span>
                </td>
                <td class="px-5 py-3.5 text-sm text-gray-400 max-w-[180px] truncate">{{ r.notas || '—' }}</td>
                <td class="px-5 py-3.5 text-right whitespace-nowrap">
                  <button @click="eliminar(r)"
                    class="opacity-0 group-hover:opacity-100 p-1.5 text-gray-300 hover:text-red-500 hover:bg-red-50 rounded-lg transition-all">
                    <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                        d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"/>
                    </svg>
                  </button>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

    </template>

    <!-- Modal: registrar -->
    <div v-if="mostrarModal" class="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div class="bg-white rounded-2xl shadow-2xl w-full max-w-sm">
        <div class="p-5 border-b border-gray-100 flex items-center justify-between">
          <div>
            <h3 class="text-lg font-bold text-gray-800">Registrar Marca</h3>
            <p class="text-sm text-gray-500">{{ ejercicio }}</p>
          </div>
          <button @click="cerrarModal" class="p-2 rounded-lg hover:bg-gray-100 text-gray-400">
            <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/>
            </svg>
          </button>
        </div>
        <form @submit.prevent="guardar" class="p-5 space-y-4">

          <!-- ── barra: peso + unidad + reps ── -->
          <template v-if="tipo === 'barra'">
            <div class="flex gap-3">
              <div class="flex-1">
                <label class="block text-sm font-semibold text-gray-700 mb-1.5">Peso levantado</label>
                <input v-model.number="formPeso" type="number" step="0.5" min="1" required autofocus
                  placeholder="Ej: 100"
                  class="w-full px-4 py-2.5 rounded-lg border border-gray-300 focus:ring-2 focus:ring-red-500 outline-none text-xl font-black">
              </div>
              <div class="w-28">
                <label class="block text-sm font-semibold text-gray-700 mb-1.5">Unidad</label>
                <select v-model="formUnidad"
                  class="w-full px-3 py-2.5 rounded-lg border border-gray-300 focus:ring-2 focus:ring-red-500 outline-none bg-white font-semibold">
                  <option value="kg">kg</option>
                  <option value="lbs">lbs</option>
                </select>
              </div>
            </div>
            <div>
              <label class="block text-sm font-semibold text-gray-700 mb-1.5">Repeticiones realizadas</label>
              <input v-model.number="formReps" type="number" min="1" max="36" required
                placeholder="Ej: 3"
                class="w-full px-4 py-2.5 rounded-lg border border-gray-300 focus:ring-2 focus:ring-red-500 outline-none text-xl font-black">
            </div>
          </template>

          <!-- ── corporal_lastre: peso corporal (auto/manual) + adicional + reps ── -->
          <template v-else-if="tipo === 'corporal_lastre'">
            <div class="bg-gray-50 border border-gray-100 rounded-xl p-3">
              <p class="text-xs font-bold uppercase tracking-widest text-gray-400 mb-1">Peso corporal</p>
              <template v-if="pesoCorporalAuto">
                <p class="text-xl font-black text-gray-800">{{ pesoCorporalAuto }} kg</p>
                <p class="text-xs text-gray-400 mt-0.5">Tomado de Mi Salud</p>
              </template>
              <template v-else>
                <input v-model.number="formPesoCorporal" type="number" step="0.1" min="1" required
                  placeholder="Ingresa tu peso corporal en kg"
                  class="w-full px-3 py-2 rounded-lg border border-gray-300 focus:ring-2 focus:ring-red-500 outline-none font-semibold mt-1">
                <p class="text-xs text-gray-400 mt-1">Sin registros en Mi Salud — ingrésalo manualmente</p>
              </template>
            </div>

            <div>
              <label class="block text-sm font-semibold text-gray-700 mb-1.5">
                Lastre adicional <span class="text-gray-400 font-normal">(opcional)</span>
              </label>
              <div class="flex gap-3">
                <input v-model.number="formPesoAdicional" type="number" step="0.5" min="0"
                  placeholder="Ej: 10"
                  class="flex-1 px-4 py-2.5 rounded-lg border border-gray-300 focus:ring-2 focus:ring-red-500 outline-none">
                <select v-model="formUnidad"
                  class="w-28 px-3 py-2.5 rounded-lg border border-gray-300 focus:ring-2 focus:ring-red-500 outline-none bg-white font-semibold">
                  <option value="kg">kg</option>
                  <option value="lbs">lbs</option>
                </select>
              </div>
              <p class="text-xs text-gray-400 mt-1">Chaleco, disco en cinturón, etc. Déjalo en blanco si solo usas tu peso corporal.</p>
            </div>

            <div>
              <label class="block text-sm font-semibold text-gray-700 mb-1.5">Repeticiones realizadas</label>
              <input v-model.number="formReps" type="number" min="1" max="100" required
                placeholder="Ej: 5"
                class="w-full px-4 py-2.5 rounded-lg border border-gray-300 focus:ring-2 focus:ring-red-500 outline-none text-xl font-black">
            </div>

            <div v-if="totalCorporal" class="text-xs text-gray-500 -mt-2">
              Peso total estimado: <strong>{{ totalCorporal }} {{ formUnidad }}</strong>
            </div>
          </template>

          <!-- ── reps: solo repeticiones ── -->
          <template v-else-if="tipo === 'reps'">
            <div>
              <label class="block text-sm font-semibold text-gray-700 mb-1.5">Repeticiones máximas</label>
              <input v-model.number="formReps" type="number" min="1" max="500" required autofocus
                placeholder="Ej: 50"
                class="w-full px-4 py-2.5 rounded-lg border border-gray-300 focus:ring-2 focus:ring-red-500 outline-none text-xl font-black">
              <p class="text-xs text-gray-400 mt-1">Cuántas repeticiones lograste hacer sin parar.</p>
            </div>
          </template>

          <!-- ── leger: nivel + palier ── -->
          <template v-else-if="tipo === 'leger'">
            <div class="flex gap-3">
              <div class="flex-1">
                <label class="block text-sm font-semibold text-gray-700 mb-1.5">Nivel alcanzado</label>
                <input v-model.number="formNivel" type="number" min="1" max="23" required autofocus
                  placeholder="Ej: 9"
                  class="w-full px-4 py-2.5 rounded-lg border border-gray-300 focus:ring-2 focus:ring-red-500 outline-none text-xl font-black">
              </div>
              <div class="flex-1">
                <label class="block text-sm font-semibold text-gray-700 mb-1.5">Palier</label>
                <input v-model.number="formPalier" type="number" min="1" max="20" required
                  placeholder="Ej: 5"
                  class="w-full px-4 py-2.5 rounded-lg border border-gray-300 focus:ring-2 focus:ring-red-500 outline-none text-xl font-black">
              </div>
            </div>
            <p class="text-xs text-gray-400 -mt-2">El test se mide en niveles (palieres por nivel). Anota el nivel + palier final que lograste completar.</p>
          </template>

          <!-- Preview 1RM (solo barra/corporal_lastre) -->
          <div v-if="esTipoPeso && previewRM" class="bg-red-50 border border-red-100 rounded-xl p-4 text-center">
            <p class="text-xs font-bold uppercase tracking-widest text-red-400 mb-1">1RM estimado</p>
            <p class="text-3xl font-black text-red-600">{{ previewRM }} {{ formUnidad }}</p>
            <p v-if="esPR" class="text-xs font-bold text-amber-600 mt-1">¡Nuevo PR!</p>
          </div>

          <!-- Fecha -->
          <div>
            <label class="block text-sm font-semibold text-gray-700 mb-1.5">Fecha</label>
            <input v-model="formFecha" type="date" required
              class="w-full px-4 py-2.5 rounded-lg border border-gray-300 focus:ring-2 focus:ring-red-500 outline-none">
          </div>

          <!-- Notas -->
          <div>
            <label class="block text-sm font-semibold text-gray-700 mb-1.5">
              Notas <span class="text-gray-400 font-normal">(opcional)</span>
            </label>
            <textarea v-model="formNotas" rows="2" placeholder="Observaciones..."
              class="w-full px-4 py-2.5 rounded-lg border border-gray-300 focus:ring-2 focus:ring-red-500 outline-none resize-none text-sm">
            </textarea>
          </div>

          <div v-if="errorForm" class="text-sm text-red-600 bg-red-50 border border-red-100 rounded-lg p-3">
            {{ errorForm }}
          </div>

          <div class="flex gap-3 pt-1">
            <button type="button" @click="cerrarModal"
              class="flex-1 py-2.5 rounded-xl border border-gray-300 text-gray-600 font-semibold hover:bg-gray-50 transition-colors">
              Cancelar
            </button>
            <button type="submit" :disabled="guardando"
              class="flex-1 py-2.5 rounded-xl bg-red-600 hover:bg-red-700 text-white font-bold transition-colors disabled:opacity-50 flex items-center justify-center gap-2">
              <span v-if="guardando" class="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></span>
              {{ guardando ? 'Guardando...' : 'Guardar' }}
            </button>
          </div>
        </form>
      </div>
    </div>

  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted, onUnmounted, nextTick } from 'vue'
import { useRoute, useRouter, RouterLink } from 'vue-router'
import { Chart } from 'chart.js/auto'
import api from '../api'
import { tipoDe } from '../data/ejerciciosMarcas'

const route  = useRoute()
const router = useRouter()

const FORMULAS = ['Brzycki', 'Epley', 'Lander', "O'Connor", 'Lombardi', 'Mayhew', 'Wathen']

// ── Estado ─────────────────────────────────────────────────────
const registros        = ref([])
const cargando         = ref(true)
const mostrarModal     = ref(false)
const guardando        = ref(false)
const errorForm        = ref('')
const formPeso         = ref('')
const formUnidad       = ref('kg')
const formReps         = ref('')
const formPesoCorporal = ref('')
const formPesoAdicional = ref('')
const formNivel        = ref('')
const formPalier       = ref('')
const formFecha        = ref(new Date().toISOString().slice(0, 10))
const formNotas        = ref('')
const pesoCorporalAuto = ref(null)  // último peso_kg de Mi Salud (si existe)

const ejercicio = computed(() => route.params.ejercicio || null)
const tipo      = computed(() => ejercicio.value ? tipoDe(ejercicio.value) : 'barra')
const esTipoPeso = computed(() => tipo.value === 'barra' || tipo.value === 'corporal_lastre')

const tituloGrafica = computed(() => {
  if (tipo.value === 'reps')  return 'Evolución de repeticiones'
  if (tipo.value === 'leger') return 'Evolución del nivel'
  return 'Evolución del 1RM'
})

const encabezadoMedicion = computed(() => {
  if (tipo.value === 'reps')  return 'Repeticiones'
  if (tipo.value === 'leger') return 'Nivel · palier'
  return 'Peso × Reps'
})

// ── Chart ──────────────────────────────────────────────────────
const chartCanvas = ref(null)
let instanciaChart = null

function destruirChart() {
  if (instanciaChart) { instanciaChart.destroy(); instanciaChart = null }
}

function renderChart() {
  if (!chartCanvas.value || registros.value.length < 2) return
  destruirChart()

  let labels = registros.value.map(r => formatFecha(r.fecha))
  let valores, label, suffix = '', highlightIdx = null

  if (tipo.value === 'reps') {
    valores = registros.value.map(r => r.repeticiones)
    label = 'Repeticiones'
    const maxR = Math.max(...valores)
    highlightIdx = valores.map(v => v === maxR)
  } else if (tipo.value === 'leger') {
    // Convertimos a "decimal" nivel.palier para graficar progresión continua
    valores = registros.value.map(r => Number(`${r.nivel || 0}.${String(r.palier || 0).padStart(2, '0')}`))
    label = 'Nivel'
    const maxV = Math.max(...valores)
    highlightIdx = valores.map(v => v === maxV)
  } else {
    const unidad = ultimaUnidad.value
    suffix = ` ${unidad}`
    valores = registros.value.map(r => round1(normalizar(r.rm_calculado, r.unidad, unidad)))
    label = `1RM estimado (${unidad})`
    const prKg = mejorRMkg.value
    highlightIdx = registros.value.map(r => toKg(r.rm_calculado, r.unidad) === prKg)
  }

  instanciaChart = new Chart(chartCanvas.value, {
    type: 'line',
    data: {
      labels,
      datasets: [{
        label,
        data: valores,
        borderColor: '#f87171',
        backgroundColor: '#f8717118',
        borderWidth: 2.5,
        pointBackgroundColor: highlightIdx.map(h => h ? '#f59e0b' : '#f87171'),
        pointBorderColor: '#fff',
        pointBorderWidth: 2,
        pointRadius: 5,
        pointHoverRadius: 7,
        fill: true,
        tension: 0.35,
      }],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      animation: { duration: 600 },
      plugins: {
        legend: { display: false },
        tooltip: {
          mode: 'index',
          intersect: false,
          callbacks: { label: ctx => ` ${ctx.parsed.y}${suffix}` },
        },
      },
      scales: {
        x: { grid: { display: false }, ticks: { font: { size: 11 }, maxTicksLimit: 8, maxRotation: 30 } },
        y: {
          grid: { color: '#f3f4f6' },
          ticks: { font: { size: 11 }, callback: v => `${v}${suffix}` },
          suggestedMin: Math.max(0, Math.min(...valores) - (valores[0] > 10 ? 5 : 1)),
          suggestedMax: Math.max(...valores) + (valores[0] > 10 ? 5 : 1),
        },
      },
    },
  })
}

watch(registros, async (val) => {
  if (val.length < 2) { destruirChart(); return }
  await nextTick(); await nextTick()
  renderChart()
})

// ── Helpers ────────────────────────────────────────────────────
const formatFecha = (f) =>
  new Date(f + 'T12:00:00').toLocaleDateString('es-CO', { day: '2-digit', month: 'short', year: 'numeric' })

const KG_PER_LB = 2.20462

function toKg(valor, unidad) {
  return unidad === 'lbs' ? valor / KG_PER_LB : valor
}
function fromKg(valorKg, unidad) {
  return unidad === 'lbs' ? valorKg * KG_PER_LB : valorKg
}
function normalizar(valor, desde, hacia) {
  if (desde === hacia) return valor
  return fromKg(toKg(valor, desde), hacia)
}
function round1(v) { return Math.round(v * 10) / 10 }

// ── PRs por tipo ───────────────────────────────────────────────
const ultimoRM     = computed(() => registros.value.length && registros.value[registros.value.length - 1].rm_calculado)
const ultimaUnidad = computed(() => registros.value.length ? registros.value[registros.value.length - 1].unidad : 'kg')

const mejorRMkg = computed(() =>
  registros.value.length
    ? Math.max(...registros.value.filter(r => r.rm_calculado != null).map(r => toKg(r.rm_calculado, r.unidad)))
    : null
)
const mejorRM = computed(() =>
  mejorRMkg.value !== null && mejorRMkg.value !== -Infinity ? round1(fromKg(mejorRMkg.value, ultimaUnidad.value)) : null
)

const ultimaReps = computed(() => registros.value.length ? registros.value[registros.value.length - 1].repeticiones : null)
const mejorReps  = computed(() =>
  registros.value.length ? Math.max(...registros.value.map(r => r.repeticiones || 0)) : null
)

const ultimoLeger = computed(() => {
  if (!registros.value.length) return null
  const r = registros.value[registros.value.length - 1]
  return { nivel: r.nivel, palier: r.palier }
})
const mejorLeger = computed(() => {
  if (!registros.value.length) return null
  return registros.value.reduce((a, b) => {
    if ((b.nivel || 0) !== (a.nivel || 0)) return (b.nivel || 0) > (a.nivel || 0) ? b : a
    return (b.palier || 0) > (a.palier || 0) ? b : a
  })
})

function esRegistroPR(r) {
  if (!esTipoPeso.value) return false
  return mejorRMkg.value !== null && toKg(r.rm_calculado, r.unidad) === mejorRMkg.value
}

// ── Fórmulas 1RM ──────────────────────────────────────────────
function calc1RM(w, r) {
  const vals = [
    w * (36 / (37 - r)),
    w * (1 + r / 30),
    (100 * w) / (101.3 - 2.67123 * r),
    w * (1 + 0.025 * r),
    w * Math.pow(r, 0.1),
    (100 * w) / (52.2 + 41.9 * Math.exp(-0.055 * r)),
    (100 * w) / (48.8 + 53.8 * Math.exp(-0.075 * r)),
  ]
  return Math.round(vals.reduce((a, b) => a + b) / vals.length * 10) / 10
}

function calcPesoParaReps(rm, r) {
  const vals = [
    rm * (37 - r) / 36,
    rm / (1 + r / 30),
    rm * (101.3 - 2.67123 * r) / 100,
    rm / (1 + 0.025 * r),
    rm / Math.pow(r, 0.1),
    rm * (52.2 + 41.9 * Math.exp(-0.055 * r)) / 100,
    rm * (48.8 + 53.8 * Math.exp(-0.075 * r)) / 100,
  ]
  return vals.map(v => Math.round(v * 10) / 10)
}

const tablaRepMax = computed(() => {
  if (!esTipoPeso.value || !ultimoRM.value) return []
  const rm = ultimoRM.value
  return Array.from({ length: 10 }, (_, i) => {
    const r = i + 1
    const vals = calcPesoParaReps(rm, r)
    const promedio = Math.round(vals.reduce((a, b) => a + b) / vals.length * 10) / 10
    return { reps: r, promedio }
  })
})

const formulasUltimo = computed(() => {
  if (!esTipoPeso.value || !registros.value.length) return null
  const rec = registros.value[registros.value.length - 1]
  if (rec.peso == null || rec.repeticiones == null) return null
  const w = rec.peso, r = rec.repeticiones
  const vals = [
    w * (36 / (37 - r)),
    w * (1 + r / 30),
    (100 * w) / (101.3 - 2.67123 * r),
    w * (1 + 0.025 * r),
    w * Math.pow(r, 0.1),
    (100 * w) / (52.2 + 41.9 * Math.exp(-0.055 * r)),
    (100 * w) / (48.8 + 53.8 * Math.exp(-0.075 * r)),
  ]
  return {
    peso: rec.peso,
    reps: rec.repeticiones,
    unidad: rec.unidad,
    promedio: rec.rm_calculado,
    detalle: FORMULAS.map((nombre, i) => ({ nombre, valor: Math.round(vals[i] * 10) / 10 })),
  }
})

// ── Corporal lastre helpers ────────────────────────────────────
const totalCorporal = computed(() => {
  if (tipo.value !== 'corporal_lastre') return null
  const corporal = pesoCorporalAuto.value || formPesoCorporal.value
  if (!corporal) return null
  const adicional = Number(formPesoAdicional.value) || 0
  return round1(Number(corporal) + adicional)
})

// ── Preview 1RM en modal ───────────────────────────────────────
const previewRM = computed(() => {
  if (!esTipoPeso.value) return null
  if (!formReps.value || formReps.value < 1) return null
  let w = null
  if (tipo.value === 'barra') {
    if (!formPeso.value) return null
    w = Number(formPeso.value)
  } else {
    w = totalCorporal.value
  }
  if (!w || w <= 0) return null
  return calc1RM(w, Number(formReps.value))
})

const esPR = computed(() => {
  if (!previewRM.value) return false
  if (mejorRMkg.value === null) return true
  return toKg(previewRM.value, formUnidad.value) > mejorRMkg.value
})

// ── API ────────────────────────────────────────────────────────
async function cargar() {
  if (!ejercicio.value) return
  cargando.value = true
  try {
    const { data } = await api.get(`/marcas/${encodeURIComponent(ejercicio.value)}`)
    registros.value = data
  } finally {
    cargando.value = false
  }
}

async function cargarPesoCorporal() {
  if (tipo.value !== 'corporal_lastre') return
  try {
    const { data } = await api.get('/salud/peso')
    if (Array.isArray(data) && data.length) {
      // último por fecha
      const ord = [...data].sort((a, b) => (a.fecha < b.fecha ? -1 : 1))
      const ultimo = ord[ord.length - 1]
      pesoCorporalAuto.value = ultimo.peso_kg || null
    }
  } catch { /* silencioso */ }
}

function abrirModal() {
  errorForm.value = ''
  mostrarModal.value = true
}

function cerrarModal() {
  mostrarModal.value = false
  formPeso.value = ''
  formReps.value = ''
  formPesoCorporal.value = ''
  formPesoAdicional.value = ''
  formNivel.value = ''
  formPalier.value = ''
  formNotas.value = ''
  errorForm.value = ''
}

async function guardar() {
  guardando.value = true
  errorForm.value = ''
  try {
    const payload = {
      ejercicio: ejercicio.value,
      fecha: formFecha.value,
      notas: formNotas.value || null,
      unidad: formUnidad.value,
    }

    if (tipo.value === 'barra') {
      payload.peso = Number(formPeso.value)
      payload.repeticiones = Number(formReps.value)
    } else if (tipo.value === 'corporal_lastre') {
      const corporal = Number(pesoCorporalAuto.value || formPesoCorporal.value)
      const adicional = Number(formPesoAdicional.value) || 0
      payload.peso = round1(corporal + adicional)
      payload.peso_adicional = adicional > 0 ? adicional : null
      payload.repeticiones = Number(formReps.value)
    } else if (tipo.value === 'reps') {
      payload.repeticiones = Number(formReps.value)
    } else if (tipo.value === 'leger') {
      payload.nivel  = Number(formNivel.value)
      payload.palier = Number(formPalier.value)
    }

    await api.post('/marcas/', payload)
    cerrarModal()
    await cargar()
  } catch (e) {
    const d = e.response?.data?.detail
    errorForm.value = Array.isArray(d) ? d[0].msg : (d || 'Error al guardar.')
  } finally {
    guardando.value = false
  }
}

async function eliminar(r) {
  if (!confirm(`¿Eliminar el registro del ${formatFecha(r.fecha)}?`)) return
  try {
    await api.delete(`/marcas/${r.id}`)
    await cargar()
  } catch (e) {
    alert(e.response?.data?.detail || 'Error al eliminar.')
  }
}

// ── Ciclo de vida ──────────────────────────────────────────────
onMounted(() => {
  if (!ejercicio.value) { router.replace({ name: 'Marcas' }); return }
  cargar()
  cargarPesoCorporal()
})

watch(
  () => route.params.ejercicio,
  () => {
    destruirChart()
    registros.value = []
    pesoCorporalAuto.value = null
    formFecha.value = new Date().toISOString().slice(0, 10)
    cargar()
    cargarPesoCorporal()
  }
)

onUnmounted(destruirChart)
</script>

<style scoped>
.animate-fade-in-up { animation: fadeInUp 0.35s ease-out; }
@keyframes fadeInUp {
  from { opacity: 0; transform: translateY(8px); }
  to   { opacity: 1; transform: translateY(0); }
}
</style>
