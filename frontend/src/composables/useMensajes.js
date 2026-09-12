import { ref } from 'vue'
import api from '../api'
import { DEFAULTS, renderMensaje } from '../lib/mensajes'

// Los overrides guardados, cacheados a nivel de módulo: el Resumen y Clientes los
// necesitan los dos y la lista cambia una vez cada varios meses. Sin el cache, cada
// navegación entre esas dos pantallas dispararía otra petición para el mismo texto.
const overrides = ref({})
// Si el envío automático de vencimientos está prendido. Lo usa el editor para decidir
// si la plantilla `vence` necesita el aviso de "esto no cambia el mensaje de las 9:10".
const envioAutomatico = ref(false)
const cargado = ref(false)
let enVuelo = null

/**
 * Trae los mensajes personalizados. Idempotente y con deduplicación: si dos vistas la
 * llaman a la vez, comparten la misma petición.
 *
 * **Falla en silencio a propósito.** Si el endpoint no responde, `textoDe` devuelve el
 * default de `lib/mensajes.js` y el botón de WhatsApp sigue funcionando. Un panel de
 * cobro que se queda sin botón porque no cargó un texto sería mucho peor que mandar el
 * mensaje de fábrica.
 */
export function cargarMensajes({ forzar = false } = {}) {
  if (cargado.value && !forzar) return Promise.resolve()
  if (enVuelo) return enVuelo
  enVuelo = api.get('/mensajes/')
    .then(({ data }) => {
      overrides.value = data?.overrides || {}
      envioAutomatico.value = !!data?.envio_automatico
      cargado.value = true
    })
    .catch(() => { /* silencioso: se usan los defaults */ })
    .finally(() => { enVuelo = null })
  return enVuelo
}

export function useMensajes() {
  /** El texto vigente de una plantilla: el personalizado si existe, si no el default. */
  const textoDe = (clave) => overrides.value[clave] || DEFAULTS[clave] || ''

  /** El texto vigente ya con las variables reemplazadas. */
  const mensaje = (clave, vars) => renderMensaje(textoDe(clave), vars)

  return { overrides, envioAutomatico, cargado, textoDe, mensaje, cargarMensajes }
}

/** Para el editor: refresca el cache tras guardar o restaurar, así el Resumen usa el
 *  texto nuevo sin recargar la página. */
export function actualizarLocal(clave, texto) {
  const copia = { ...overrides.value }
  if (texto) copia[clave] = texto
  else delete copia[clave]
  overrides.value = copia
}
