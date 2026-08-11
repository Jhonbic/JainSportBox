import { ref } from 'vue'

// Estado de "se está navegando", para que el área de contenido no quede en blanco
// mientras baja el chunk de una vista lazy.
//
// Vive en su propio módulo y no en `router/index.js` a propósito: el router importa
// `Dashboard.vue` de forma estática, así que si el flag viviera ahí, el componente
// tendría que importar al router y quedaría un ciclo. Funciona —ES Modules lo
// tolera porque el ref se lee recién al instanciar el componente— pero es de esas
// cosas que se rompen al reordenar un import y cuestan una tarde de depuración.

export const cargandoRuta = ref(false)

// El retraso no es un adorno: una ruta ya descargada resuelve en milisegundos, y un
// indicador que aparece y se va en ese lapso se ve como un parpadeo — peor que no
// mostrar nada. Solo se muestra cuando la navegación de verdad tarda.
const RETRASO_MS = 150
let temporizador = null

export function marcarNavegacionEnCurso() {
  clearTimeout(temporizador)
  temporizador = setTimeout(() => { cargandoRuta.value = true }, RETRASO_MS)
}

export function marcarNavegacionTerminada() {
  clearTimeout(temporizador)
  cargandoRuta.value = false
}
