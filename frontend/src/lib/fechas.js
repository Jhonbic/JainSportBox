// Fechas en formato YYYY-MM-DD calculadas en hora LOCAL.
//
// Existe para no volver a escribir `new Date().toISOString().slice(0, 10)`, que es la
// fecha **UTC**: en Bogotá (UTC-5), a partir de las 19:00 devuelve el día siguiente.
// Eso hacía que "Hoy" en Finanzas pidiera al backend el rango de mañana, justo en el
// horario en que el box está lleno.
//
// El backend espera días del negocio (Bogotá) y los convierte a UTC con los helpers de
// `backend/fechas.py`. Estas dos funciones son la punta del frontend de esa misma regla.

/** Una fecha (objeto Date) → "YYYY-MM-DD" en hora local. */
export function aISO(d) {
  const mes = String(d.getMonth() + 1).padStart(2, '0')
  const dia = String(d.getDate()).padStart(2, '0')
  return `${d.getFullYear()}-${mes}-${dia}`
}

/** Hoy en "YYYY-MM-DD", hora local. */
export function hoyISO() {
  return aISO(new Date())
}

const TZ = 'America/Bogota'

/**
 * Formatea lo que llega del backend, que manda DOS formas distintas y hay que tratarlas
 * distinto. Confundirlas corre la fecha un día entero.
 *
 * * **`"YYYY-MM-DD"`** — una fecha de calendario (`fecha_vencimiento`, `fecha_inicio`).
 *   No tiene hora que convertir. `new Date("2026-08-20")` la parsea como medianoche
 *   **UTC**, que en Bogotá es la tarde del 19: por eso se ancla a mediodía local.
 * * **`"YYYY-MM-DDTHH:MM:SS"` sin sufijo de zona** — un instante que el backend guarda
 *   naive en **UTC** (`fecha_pago`, `created_at`, `fecha_venta`, `fecha_enviada`,
 *   `terminos_fecha`). Sin la `Z`, JS lo parsea como hora **local** y la fecha se corre
 *   +5 h: un pago de las 20:50 del 19 aparecía como del **20**. Ese fue el bug.
 *
 * Vive acá porque había cuatro copias de esta regla en las vistas y solo una estaba
 * bien. Al agregar una pantalla que muestre fechas, usar esto y no `new Date()` pelado.
 */
export function formatearFecha(f, opts = {}) {
  if (!f) return ''
  const soloFecha = typeof f === 'string' && /^\d{4}-\d{2}-\d{2}$/.test(f)
  const d = soloFecha
    ? new Date(`${f}T12:00:00`)
    : new Date(/Z|[+-]\d{2}:?\d{2}$/.test(f) ? f : `${f}Z`)

  const base = { day: 'numeric', month: 'short', year: 'numeric' }
  // La zona se fija solo para los instantes: una fecha de calendario no tiene hora que
  // convertir, y forzarle una zona la volvería a mover si el navegador no está en Bogotá.
  return d.toLocaleDateString('es-CO', soloFecha ? { ...base, ...opts } : { ...base, timeZone: TZ, ...opts })
}
