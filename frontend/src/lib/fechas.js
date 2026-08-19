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
