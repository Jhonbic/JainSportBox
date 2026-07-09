// Carga diferida y selectiva de Chart.js. En vez de `chart.js/auto` (que registra
// TODOS los controllers/escalas, ~150-200 kB), importamos solo lo necesario para
// gráficas de línea y lo registramos una sola vez. El import() dinámico mantiene
// Chart.js fuera del chunk de la vista hasta que realmente se dibuja una gráfica.
let _ChartPromise = null

export function getChart() {
  if (!_ChartPromise) {
    _ChartPromise = import('chart.js').then((m) => {
      const {
        Chart, LineController, LineElement, PointElement,
        BarController, BarElement,
        LinearScale, CategoryScale, Tooltip, Filler, Legend,
      } = m
      Chart.register(
        LineController, LineElement, PointElement,
        BarController, BarElement,
        LinearScale, CategoryScale, Tooltip, Filler, Legend,
      )
      return Chart
    })
  }
  return _ChartPromise
}
