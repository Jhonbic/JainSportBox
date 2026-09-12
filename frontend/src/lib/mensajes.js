// Los textos de los mensajes de WhatsApp que el box le manda a un socio.
//
// **Este archivo es la fuente única del texto de fábrica.** El backend
// (`routers/mensajes.py`) guarda solo lo que el admin escribió encima; una clave sin
// override usa lo de acá. Por eso los defaults NO están duplicados en la base: si
// estuvieran, mejorar un texto no le llegaría nunca a quien ya lo tiene guardado.
//
// Consecuencia útil: si el endpoint falla, los botones de WhatsApp siguen andando con
// el default en vez de quedarse mudos.
//
// El envío **automático** de vencimientos no pasa por acá: usa una plantilla aprobada
// por Meta cuyo cuerpo vive en los servidores de Meta (ver `backend/whatsapp.py`).
// Editar el mensaje "vence" cambia el link manual del panel, no ese envío.

/** Los emojis son deliberados: son los únicos de la app y van en un saludo por
 *  WhatsApp a un socio, no en la interfaz de gestión. No los saques en una limpieza
 *  de copy. */
export const PLANTILLAS = [
  {
    clave: 'cumpleanos',
    grupo: 'Cumpleaños',
    titulo: 'Feliz cumpleaños',
    cuando: 'Botón verde del panel "Cumpleaños hoy", en el Resumen.',
    vars: ['nombre'],
    texto:
      '¡Feliz cumpleaños, {nombre}! 🎉 De parte de todo el equipo de Jain Sport Box. ' +
      'Pasa hoy por el box y te invitamos un batido. 💪',
  },
  {
    clave: 'vence',
    grupo: 'Cobro',
    titulo: 'La membresía está por vencer',
    cuando: 'Botón "Recordar" del panel "Por vencer · 7 días", en el Resumen.',
    vars: ['nombre', 'cuando', 'fecha', 'dias'],
    texto:
      'Hola {nombre}! 👋 Te recordamos que tu membresía en *Jain Sport Box* vence ' +
      '*{cuando}* ({fecha}). Para renovar contáctanos. 💪🔥',
  },
  {
    clave: 'vencida',
    grupo: 'Cobro',
    titulo: 'La membresía ya venció',
    cuando: 'Botón verde del tab Inactivos, en Clientes.',
    vars: ['nombre'],
    texto:
      'Hola {nombre}! Te recordamos que tu membresía en *Jain Sport Box* ya venció. ' +
      'Renuévala cuando quieras y te esperamos en el box.',
  },
  {
    clave: 'sin_accesos',
    grupo: 'Cobro',
    titulo: 'Se le acabaron los accesos',
    cuando: 'Tab Inactivos, cuando el bono llegó a cero pero la fecha sigue vigente.',
    vars: ['nombre'],
    texto:
      'Hola {nombre}! Te avisamos que se te acabaron los accesos de tu plan en ' +
      '*Jain Sport Box*. Pasa por recepción para recargarlo y seguimos entrenando.',
  },
  {
    clave: 'sin_membresia',
    grupo: 'Cobro',
    titulo: 'Nunca tuvo membresía',
    cuando: 'Tab Inactivos, para el cliente registrado que todavía no compró un plan.',
    vars: ['nombre'],
    texto:
      'Hola {nombre}! Vimos que todavía no tienes una membresía activa en ' +
      '*Jain Sport Box*. Pasa por recepción y te ayudamos a elegir el plan que mejor te sirva.',
  },
]

/** Qué significa cada variable. Lo muestra el editor al lado del campo: sin esto,
 *  `{cuando}` no se entiende hasta que se manda un mensaje y se ve el resultado. */
export const AYUDA_VARS = {
  nombre: 'El primer nombre del cliente',
  cuando: '"hoy", "mañana" o "en 5 días"',
  fecha: 'La fecha de vencimiento (20 sep 2026)',
  dias: 'Los días que faltan, solo el número',
}

/** Datos de ejemplo para la vista previa del editor. */
export const EJEMPLO = {
  nombre: 'Carlos',
  cuando: 'en 3 días',
  fecha: '14 sep 2026',
  dias: '3',
}

export const DEFAULTS = Object.fromEntries(PLANTILLAS.map(p => [p.clave, p.texto]))

export const plantillaDe = (clave) => PLANTILLAS.find(p => p.clave === clave)

/**
 * Reemplaza `{variable}` por su valor.
 *
 * Solo toca las variables que se le pasan: una `{cualquierCosa}` que el admin haya
 * escrito de más queda literal en el mensaje. Es a propósito — borrarla en silencio
 * escondería el error justo hasta que el socio recibe el WhatsApp; así se ve en la
 * vista previa del editor, que además la marca en rojo antes de guardar.
 */
export function renderMensaje(texto, vars = {}) {
  return String(texto ?? '').replace(/\{(\w+)\}/g, (original, clave) =>
    clave in vars ? String(vars[clave] ?? '') : original
  )
}

/** Las `{variables}` que aparecen en un texto y no son válidas para esa plantilla. */
export function varsDesconocidas(texto, permitidas) {
  const usadas = [...String(texto ?? '').matchAll(/\{(\w+)\}/g)].map(m => m[1])
  return [...new Set(usadas.filter(v => !permitidas.includes(v)))]
}

/** El primer nombre. Los mensajes tutean y saludan por el nombre de pila: "Hola Carlos
 *  Andrés Restrepo" no es cómo se le habla a alguien que va al box todos los días. */
export function primerNombre(nombre) {
  return String(nombre ?? '').trim().split(/\s+/)[0] || ''
}
