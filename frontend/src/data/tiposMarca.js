/**
 * Tipos de medición de una marca.
 *
 * La LISTA de ejercicios ya no vive acá: la administra el staff desde el catálogo
 * de Ejercicios (campo "tipo de marca") y llega por `GET /marcas/catalogo`. Lo que
 * queda fijo son las cuatro formas de medir, porque cada una tiene su propia UI y
 * su propia validación en el backend — agregar un tipo es código, no configuración.
 *
 * Espeja a `backend/marcas_tipos.py`; hay un test que exige que coincidan.
 */
export const TIPOS_MARCA = [
  {
    valor: 'barra',
    label: 'Peso levantado',
    // El `valor` sigue diciendo 'barra' porque está guardado en la base y en las
    // marcas ya cargadas, pero el tipo NO es solo de barra: es cualquier peso
    // externo. El nombre quedó de cuando la lista eran 7 levantamientos fijos y
    // todos eran con barra. Precedente del proyecto: en pantalla se dice una cosa
    // y en la API otra (ver "accesos" vs `ingresos`).
    ayuda: 'Cualquier ejercicio con peso: barra, mancuerna, kettlebell o máquina. Se anota peso + repeticiones y el sistema estima el 1RM (lo máximo que levantaría en una sola repetición).',
  },
  {
    valor: 'corporal_lastre',
    label: 'Peso corporal (+ lastre)',
    ayuda: 'Para dominadas y similares. Toma el peso del socio de Mi Salud y le suma el lastre si entrena con chaleco o disco. También estima el 1RM.',
  },
  {
    valor: 'reps',
    label: 'Repeticiones máximas',
    ayuda: 'Solo cuántas repeticiones logró, sin peso. Para flexiones, abdominales y parecidos.',
  },
  {
    valor: 'leger',
    label: 'Nivel y palier (Léger)',
    ayuda: 'Para el test de Léger: el nivel alcanzado y el palier. No usa peso ni repeticiones.',
  },
]

export function labelTipo(valor) {
  return TIPOS_MARCA.find(t => t.valor === valor)?.label || ''
}
