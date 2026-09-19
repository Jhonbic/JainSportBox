import { ref } from 'vue'
import api from '../api'

/**
 * Catálogo de ejercicios medibles, compartido por las dos vistas de Mis Marcas.
 *
 * Es un módulo y no un fetch por vista porque `MarcasView` y `MarcasEjercicioView`
 * lo necesitan en el mismo viaje —se navega de una a la otra— y volver a pedirlo
 * dejaría la pantalla de detalle sin saber cómo se mide el ejercicio hasta que
 * responda el servidor, o sea mostrando el formulario equivocado por un instante.
 *
 * El cache es de módulo, así que vive lo que vive la pestaña. Se refresca con
 * `cargarCatalogo({ forzar: true })` cuando hace falta (no hoy: el socio no edita
 * el catálogo, y el staff lo hace desde otra vista que se monta aparte).
 */
const catalogo = ref([])
let promesaEnVuelo = null

export function usarCatalogoMarcas() {
  return catalogo
}

export async function cargarCatalogo({ forzar = false } = {}) {
  if (!forzar && catalogo.value.length) return catalogo.value
  // Sin esto, montar las dos vistas juntas dispara dos veces la misma petición.
  if (!forzar && promesaEnVuelo) return promesaEnVuelo

  promesaEnVuelo = api.get('/marcas/catalogo')
    .then(({ data }) => {
      catalogo.value = Array.isArray(data) ? data : []
      return catalogo.value
    })
    .finally(() => { promesaEnVuelo = null })

  return promesaEnVuelo
}

export function ejercicioDe(nombre) {
  return catalogo.value.find(e => e.nombre === nombre) || null
}

/**
 * Cómo se mide un ejercicio. El default 'barra' espeja al del backend: cubre a la
 * marca cuyo ejercicio el staff sacó del catálogo, que sigue existiendo en la base
 * y tiene que poder verse.
 */
export function tipoDe(nombre) {
  return ejercicioDe(nombre)?.tipo || 'barra'
}
