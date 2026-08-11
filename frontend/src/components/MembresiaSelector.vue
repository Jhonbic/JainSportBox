<template>
  <div class="space-y-4">
    <!-- Selección de plan -->
    <div>
      <p class="text-sm font-semibold text-gray-700 mb-3">{{ titulo }}</p>
      <div class="grid grid-cols-2 gap-3">
        <label v-if="permitirNinguno"
          class="flex flex-col items-center justify-center p-4 rounded-xl border-2 cursor-pointer transition-all col-span-2"
          :class="form.plan === 'ninguno' ? a.activo : 'border-gray-200 hover:border-gray-300'">
          <input type="radio" v-model="form.plan" value="ninguno" class="sr-only">
          <span class="text-sm font-bold" :class="form.plan === 'ninguno' ? a.textoFuerte : 'text-gray-600'">Sin plan por ahora</span>
        </label>

        <label v-for="plan in planes" :key="plan.id"
          class="flex flex-col items-center p-4 rounded-xl border-2 cursor-pointer transition-all"
          :class="form.plan === plan.id ? a.activo : 'border-gray-200 hover:border-gray-300'">
          <input type="radio" v-model="form.plan" :value="plan.id" class="sr-only">
          <span class="text-2xl font-black mb-0.5" :class="form.plan === plan.id ? a.texto : 'text-gray-700'">
            {{ plan.duracion_dias }}<span class="text-sm font-bold">d</span>
          </span>
          <span class="text-sm font-bold text-center" :class="form.plan === plan.id ? a.textoFuerte : 'text-gray-600'">{{ plan.nombre }}</span>
          <span class="text-xs mt-1" :class="form.plan === plan.id ? a.textoSuave : 'text-gray-400'">
            ${{ plan.precio.toLocaleString() }}<template v-if="plan.numero_ingresos"> · {{ plan.numero_ingresos }} accesos</template>
          </span>
        </label>

        <label class="flex flex-col items-center p-4 rounded-xl border-2 cursor-pointer transition-all col-span-2"
          :class="form.plan === 'personalizado' ? a.activo : 'border-gray-200 hover:border-gray-300'">
          <input type="radio" v-model="form.plan" value="personalizado" class="sr-only">
          <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5 mb-1" :class="form.plan === 'personalizado' ? a.textoSuave : 'text-gray-400'" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6V4m0 2a2 2 0 100 4m0-4a2 2 0 110 4m-6 8a2 2 0 100-4m0 4a2 2 0 110-4m0 4v2m0-6V4m6 6v10m6-2a2 2 0 100-4m0 4a2 2 0 110-4m0 4v2m0-6V4"/>
          </svg>
          <span class="text-sm font-bold" :class="form.plan === 'personalizado' ? a.textoFuerte : 'text-gray-600'">Personalizado</span>
        </label>
      </div>
    </div>

    <!-- Días y accesos del personalizado -->
    <div v-if="form.plan === 'personalizado'" class="grid grid-cols-2 gap-3">
      <div>
        <label class="block text-sm font-semibold text-gray-700 mb-1.5">Días de vigencia</label>
        <input v-model.number="form.dias" type="number" min="1" max="365"
          class="w-full px-4 py-2.5 rounded-lg border border-gray-300 outline-none focus:ring-2" :class="a.ring">
      </div>
      <div>
        <label class="block text-sm font-semibold text-gray-700 mb-1.5">
          Accesos <span class="text-gray-400 font-normal">— opcional</span>
        </label>
        <input v-model.number="form.accesos" type="number" min="1" placeholder="Sin límite"
          class="w-full px-4 py-2.5 rounded-lg border border-gray-300 outline-none focus:ring-2" :class="a.ring">
      </div>
      <p class="col-span-2 -mt-1 text-xs text-gray-400">
        Los días son la vigencia; cada acceso es una sesión. Sin accesos, la membresía vale solo por fecha.
      </p>
    </div>

    <!-- Fecha de inicio -->
    <div v-if="hayPlan">
      <label class="block text-sm font-semibold text-gray-700 mb-1.5">
        ¿Cuándo arranca?
        <span class="text-gray-400 font-normal">— puede ser un día pasado</span>
      </label>
      <input v-model="form.fechaInicio" type="date" :min="minimo"
        class="w-full px-4 py-2.5 rounded-lg border border-gray-300 outline-none focus:ring-2" :class="a.ring">
      <p v-if="preview" class="mt-1.5 text-xs"
        :class="preview.yaVencida ? 'text-amber-600' : (preview.encolado || preview.retroactivo ? 'text-gray-500' : 'text-gray-400')">
        <template v-if="preview.encolado">
          Ya tiene membresía hasta el {{ fmt(vencimientoActual) }}, así que esta arranca después y vence el
          <span class="font-semibold text-gray-700">{{ fmt(preview.vence) }}</span>.
        </template>
        <template v-else-if="preview.yaVencida">
          Arranca el {{ fmt(preview.arranca) }}, así que los {{ dias }} días ya se cumplieron:
          queda <span class="font-semibold">vencida desde el {{ fmt(preview.vence) }}</span>.
        </template>
        <template v-else-if="preview.retroactivo">
          Cuenta desde el {{ fmt(preview.arranca) }}, así que los días ya transcurridos se descuentan
          y vence el <span class="font-semibold text-gray-700">{{ fmt(preview.vence) }}</span>.
        </template>
        <template v-else>
          Arranca el {{ fmt(preview.arranca) }} y vence el
          <span class="font-semibold text-gray-700">{{ fmt(preview.vence) }}</span>.
        </template>
      </p>
    </div>

    <!-- Monto -->
    <div v-if="hayPlan">
      <label class="block text-sm font-semibold text-gray-700 mb-1.5">
        Monto cobrado ($)
        <span v-if="planActual" class="text-gray-400 font-normal">— sugerido ${{ planActual.precio.toLocaleString() }}</span>
      </label>
      <input v-model.number="form.monto" type="number" min="0" step="any"
        class="w-full px-4 py-2.5 rounded-lg border border-gray-300 outline-none focus:ring-2" :class="a.ring"
        :placeholder="planActual ? '$' + planActual.precio.toLocaleString() : ''">
    </div>

    <!-- Método de pago -->
    <div v-if="hayPlan">
      <label class="block text-sm font-semibold text-gray-700 mb-1.5">Método de pago</label>
      <div class="grid grid-cols-2 gap-2">
        <label v-for="m in METODOS" :key="m.value"
          class="flex items-center justify-center gap-1.5 p-2.5 rounded-lg border-2 cursor-pointer transition-all text-sm font-semibold"
          :class="form.metodo === m.value ? a.activoTexto : 'border-gray-200 text-gray-600 hover:border-gray-300'">
          <input type="radio" v-model="form.metodo" :value="m.value" class="sr-only">
          {{ m.label }}
        </label>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { METODOS, diasDe, minimoInicioISO, planDe, previsualizar } from '../lib/membresia'

// Las clases van como strings completos, nunca interpoladas (`border-${x}-500`):
// el scanner de content de tailwind.config.js no resuelve interpolación y purgaría
// la clase del build. Ver "Paleta de colores" en CLAUDE.md.
const ACENTOS = {
  red: {
    activo: 'border-red-500 bg-red-50',
    activoTexto: 'border-red-500 bg-red-50 text-red-700',
    texto: 'text-red-600',
    textoFuerte: 'text-red-700',
    textoSuave: 'text-red-500',
    ring: 'focus:ring-red-500',
  },
  emerald: {
    activo: 'border-emerald-500 bg-emerald-50',
    activoTexto: 'border-emerald-500 bg-emerald-50 text-emerald-700',
    texto: 'text-emerald-600',
    textoFuerte: 'text-emerald-700',
    textoSuave: 'text-emerald-500',
    ring: 'focus:ring-emerald-500',
  },
}

const props = defineProps({
  modelValue: { type: Object, required: true },
  planes: { type: Array, default: () => [] },
  acento: { type: String, default: 'red' },
  titulo: { type: String, default: 'Selecciona el plan a asignar' },
  permitirNinguno: { type: Boolean, default: false },
  vencimientoActual: { type: String, default: null },
})
defineEmits(['update:modelValue'])

const form = computed(() => props.modelValue)
const a = computed(() => ACENTOS[props.acento] || ACENTOS.red)
// El arranque acepta días pasados (el socio al que se dejó entrar antes de cobrarle).
// El `min` solo acota el error de año en el calendario; la regla la valida el backend.
const minimo = minimoInicioISO()

const hayPlan = computed(() => form.value.plan && form.value.plan !== 'ninguno')
const planActual = computed(() => planDe(form.value, props.planes))
const dias = computed(() => diasDe(form.value, props.planes))
const preview = computed(() =>
  hayPlan.value ? previsualizar(form.value, props.planes, props.vencimientoActual) : null
)

const fmt = (f) => {
  const d = f instanceof Date ? f : new Date(f + 'T00:00:00')
  return d.toLocaleDateString('es-CO', { day: 'numeric', month: 'short', year: 'numeric' })
}
</script>
