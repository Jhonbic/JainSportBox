import { defineConfig, loadEnv } from 'vite'
import vue from '@vitejs/plugin-vue'
import { VitePWA } from 'vite-plugin-pwa'

export default defineConfig(({ mode }) => {
  // Lee VITE_API_URL en build (NO import.meta.env: la urlPattern se serializa
  // al service worker, donde no hay closures ni import.meta). Se hornea el
  // origin como RegExp literal dentro del SW.
  const env = loadEnv(mode, process.cwd(), '')
  const apiUrl = env.VITE_API_URL || 'http://127.0.0.1:8000'
  const apiOrigin = new URL(apiUrl).origin
  const apiOriginRe = new RegExp('^' + apiOrigin.replace(/[.*+?^${}()|[\]\\]/g, '\\$&'))

  return {
    plugins: [
      vue(),
      VitePWA({
        registerType: 'autoUpdate',
        includeAssets: ['favicon.ico', 'apple-touch-icon.png'],
        manifest: {
          name: 'JainSportBox',
          short_name: 'JainBox',
          lang: 'es',
          description: 'Gestión de tu box de CrossFit: WODs, marcas, membresía y asistencia.',
          theme_color: '#dc2626',
          background_color: '#ffffff',
          display: 'standalone',
          start_url: '/',
          icons: [
            { src: 'pwa-192.png', sizes: '192x192', type: 'image/png' },
            { src: 'pwa-512.png', sizes: '512x512', type: 'image/png' },
            { src: 'pwa-512.png', sizes: '512x512', type: 'image/png', purpose: 'maskable' },
          ],
        },
        workbox: {
          navigateFallback: '/index.html',
          runtimeCaching: [
            {
              // API: red primero (token/datos frescos), nunca CacheFirst.
              // Cae al cache solo si la red falla dentro del timeout.
              urlPattern: apiOriginRe,
              handler: 'NetworkFirst',
              options: { cacheName: 'api', networkTimeoutSeconds: 5 },
            },
          ],
        },
      }),
    ],
    build: {
      rollupOptions: {
        output: {
          manualChunks: {
            // Núcleo del framework, separado del código de la app.
            vendor: ['vue', 'vue-router', 'axios'],
            // Chart.js solo lo usan 2 vistas → su propio chunk, no en el vendor.
            chart: ['chart.js'],
          },
        },
      },
    },
    server: {
      port: 5173,
      strictPort: true,
    },
  }
})
