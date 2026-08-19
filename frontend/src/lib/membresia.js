// Armado de los payloads de membresía, compartido por los cuatro lugares que la
// asignan: activar un pendiente, renovar desde el listado, crear un cliente con
// plan inicial y agregar membresía desde el perfil.
//
// Vive acá y no en cada vista porque el `if personalizado` que elige entre
// `/pagos/` y `/pagos/directo/` estaba escrito cuatro veces, y fue justamente esa
// duplicación la que dejó al modal de activar sin la opción personalizada.

// `aISO`/`hoyISO` vivían acá, pero Finanzas también necesita la fecha local: se
// mudaron a `lib/fechas.js`. Se re-exporta `hoyISO` para no romper a quien ya lo
// importaba desde este módulo.
import { aISO, hoyISO } from './fechas'

export { hoyISO }

/** Los métodos de pago que acepta el backend (regex `efectivo|transferencia`). */
export const METODOS = [
  { value: 'efectivo', label: 'Efectivo' },
  { value: 'transferencia', label: 'Transferencia' },
]

// Espeja MAX_DIAS_RETROACTIVOS de backend/fechas.py. El `min` del date picker no es
// la validación —esa la hace el backend— sino lo que evita que el año equivocado sea
// un click de distancia en el calendario.
export const MAX_DIAS_RETROACTIVOS = 365

export function minimoInicioISO() {
  const d = new Date()
  d.setDate(d.getDate() - MAX_DIAS_RETROACTIVOS)
  return aISO(d)
}

/** Estado inicial del formulario. `plan` es un id, 'personalizado' o 'ninguno'. */
export function nuevoFormulario(plan = null) {
  return {
    plan,
    dias: 30,
    accesos: null,
    fechaInicio: hoyISO(),
    monto: null,
    metodo: 'efectivo',
  }
}

export function planDe(form, planes) {
  return planes.find(p => p.id === form.plan) || null
}

/** El monto a cobrar: lo tipeado, o el precio del plan como sugerencia. */
function montoEfectivo(form, planes) {
  return form.monto || planDe(form, planes)?.precio || 0
}

// La fecha de inicio solo viaja si el admin la movió. Mandar "hoy" siempre sería
// inocuo para el cálculo (el backend ignora el arranque que cae entre hoy y el
// vencimiento vigente), pero dejaría `Pago.fecha_inicio` lleno en todos los pagos y
// ahí ese campo dejaría de significar "esta membresía arrancó otro día".
function inicioSiFueElegido(form) {
  return form.fechaInicio && form.fechaInicio !== hoyISO() ? form.fechaInicio : null
}

function comunes(form, planes) {
  const body = { monto: montoEfectivo(form, planes), metodo_pago: form.metodo }
  const inicio = inicioSiFueElegido(form)
  if (inicio) body.fecha_inicio = inicio
  return body
}

/**
 * Payload para registrar un pago. Devuelve la URL además del cuerpo porque el
 * endpoint cambia según sea un plan del catálogo o una membresía personalizada.
 */
export function payloadPago(form, planes, usuarioId) {
  const body = { usuario_id: usuarioId, ...comunes(form, planes) }
  if (form.plan === 'personalizado') {
    return {
      url: '/pagos/directo/',
      body: { ...body, duracion_dias: form.dias, numero_ingresos: form.accesos || null },
    }
  }
  return { url: '/pagos/', body: { ...body, plan_id: form.plan } }
}

/** Payload para `POST /usuarios/{id}/activar`, que resuelve los dos casos solo. */
export function payloadActivacion(form, planes) {
  const body = comunes(form, planes)
  if (form.plan === 'personalizado') {
    return { ...body, duracion_dias: form.dias, numero_ingresos: form.accesos || null }
  }
  return { ...body, plan_id: form.plan }
}

/** Los días que cubre la selección actual, o null si todavía no hay nada elegido. */
export function diasDe(form, planes) {
  if (form.plan === 'personalizado') return form.dias || null
  return planDe(form, planes)?.duracion_dias || null
}

/**
 * Vencimiento que va a quedar, para mostrarlo antes de confirmar.
 *
 * **Espeja `extender_vencimiento()` de `backend/membresia.py`** — si esa regla
 * cambia, hay que tocar las dos. La fecha de inicio se ignora en un solo caso: si
 * cae entre hoy y el vencimiento vigente, porque ahí no adelanta nada y respetarla
 * pisaría días ya pagos. Fuera de esa franja manda, hacia adelante (arranque
 * programado) y hacia atrás (la membresía ya venía corriendo).
 *
 * Devuelve `{ arranca, vence, encolado, retroactivo, yaVencida }`, o null si falta
 * elegir. `yaVencida` es la señal de que el retroactivo se pasó de lejos y la
 * membresía nacería vencida — la pantalla lo avisa antes de cobrar.
 */
export function previsualizar(form, planes, vencimientoActual) {
  const dias = diasDe(form, planes)
  if (!dias) return null

  const hoy = new Date(hoyISO() + 'T00:00:00')
  const vence = vencimientoActual ? new Date(vencimientoActual + 'T00:00:00') : null
  const vigente = vence && vence >= hoy ? vence : null

  let base = vigente || hoy
  const inicio = form.fechaInicio ? new Date(form.fechaInicio + 'T00:00:00') : null
  const ignorado = Boolean(inicio && inicio >= hoy && inicio <= base)
  if (inicio && !ignorado) base = inicio

  let fin = new Date(base)
  fin.setDate(fin.getDate() + dias)
  // Un retroactivo no acorta lo que ya estaba pago.
  if (vigente && fin < vigente) fin = new Date(vigente)

  return {
    arranca: new Date(base),
    vence: fin,
    encolado: ignorado && Boolean(vigente),
    retroactivo: Boolean(inicio && inicio < hoy),
    yaVencida: fin < hoy,
  }
}
