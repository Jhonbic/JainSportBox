// Paleta del proyecto — ver la sección "Paleta de colores" en CLAUDE.md.
//
// El núcleo semántico son 4 familias de Tailwind, y se usan directas en las clases
// (no hay tokens custom en tailwind.config.js, fue una decisión consciente):
//   gray    → neutro / chrome
//   red     → marca, acción primaria, destructivo
//   emerald → éxito / vigente
//   amber   → alerta / por vencer
//
// Acá vivía además una escala categórica de 5 hues fríos (`CATEGORICOS`,
// `CATEGORIA_EJERCICIO`, `CATEGORIAS_EJERCICIO`, `puntoCategoria()`) para pintar la
// categoría del ejercicio. Se eliminó junto con la columna `ejercicios.categoria`:
// el catálogo quedó en (nombre, video_url) y esa escala se quedó sin un solo
// consumidor. Si alguna vez vuelve a hacer falta colorear datos categóricos, la regla
// era: hues fríos —nunca rojo/verde/ámbar, que ya significan otra cosa—, como punto
// sobre un badge neutro, y solo hasta 6 categorías (más arriba el color deja de
// distinguirse). Y las clases van como strings completos, nunca interpoladas
// (`bg-${x}-500`), porque el scanner de Tailwind no resuelve interpolación y purgaría
// la clase del build.

/** Badge neutro. El color, cuando hace falta, lo aporta un punto aparte. */
export const BADGE_NEUTRO = 'bg-gray-100 text-gray-700'
