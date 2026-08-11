// Armado de los payloads de membresía, compartido por los cuatro lugares que la
// asignan: activar un pendiente, renovar desde el listado, crear un cliente con
// plan inicial y agregar membresía desde el perfil.
//
// Vive acá y no en cada vista porque el `if personalizado` que elige entre
// `/pagos/` y `/pagos/directo/` estaba escrito cuatro veces, y fue justamente esa
// duplicación la que dejó al modal de activar sin la opción personalizada.

/** Los métodos de pago que acepta el backend (regex `efectivo|transferencia`). */
export const METODOS = [
  { value: 'efectivo', label: 'Efectivo' },
  { value: 'transferencia', label: 'Transferencia' },
]

/** Fecha de hoy en formato YYYY-MM-DD, que es lo que espera un <input type="date">. */
export function hoyISO() {
  const d = new Date()
  const mes = String(d.getMonth() + 1).padStart(2, '0')
  const dia = String(d.getDate()).padStart(2, '0')
  return `${d.getFullYear()}-${mes}-${dia}`
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
// inocuo para el cálculo (el backend la usa como piso y hoy nunca supera la base),
// pero dejaría `Pago.fecha_inicio` lleno en todos los pagos y ahí ese campo dejaría
// de significar "esta membresía se programó para otro día".
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
 * cambia, hay que tocar las dos. La fecha de inicio entra como piso: si cae antes
 * de lo que ya correspondía se ignora, así renovar antes de tiempo no descarta los
 * días que quedaban.
 *
 * Devuelve `{ arranca, vence, encolado }`, o null si falta elegir.
 */
export function previsualizar(form, planes, vencimientoActual) {
  const dias = diasDe(form, planes)
  if (!dias) return null

  const hoy = new Date(hoyISO() + 'T00:00:00')
  const vence = vencimientoActual ? new Date(vencimientoActual + 'T00:00:00') : null

  let base = vence && vence >= hoy ? vence : hoy
  const inicio = form.fechaInicio ? new Date(form.fechaInicio + 'T00:00:00') : null
  const encolado = Boolean(inicio && vence && vence >= hoy && inicio <= vence)
  if (inicio && inicio > base) base = inicio

  const fin = new Date(base)
  fin.setDate(fin.getDate() + dias)
  return { arranca: new Date(base), vence: fin, encolado }
}
