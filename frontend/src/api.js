import axios from 'axios'

// Base del backend por entorno. Local (default): backend en 127.0.0.1:8000.
// Producción: VITE_API_URL=https://api.tudominio.com (ver .env.production).
export const API_BASE = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000'

// Resuelve la URL de un archivo subido (foto de perfil/producto).
// Las fotos en object storage (R2/S3) ya vienen como URL absoluta → se usan
// tal cual. Las locales son rutas relativas "/uploads/..." → se les antepone
// la base del backend.
export function mediaUrl(path) {
  if (!path) return ''
  return /^https?:\/\//i.test(path) ? path : `${API_BASE}${path}`
}

const api = axios.create({
  baseURL: API_BASE,
})

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// Manejo global de sesión expirada: ante un 401 se limpia la sesión y se manda a
// login (evita que las vistas queden en blanco con el token vencido). No aplica a
// la propia pantalla de login (un 401 ahí es "credenciales inválidas", lo maneja
// LoginView) ni si ya estamos en /login.
api.interceptors.response.use(
  (response) => response,
  (error) => {
    const status = error?.response?.status
    const url = error?.config?.url || ''
    const esLogin = url.includes('/login')
    if (status === 401 && !esLogin && window.location.pathname !== '/login') {
      localStorage.removeItem('token')
      localStorage.removeItem('userRol')
      localStorage.removeItem('userName')
      localStorage.removeItem('userGenero')
      localStorage.removeItem('fechaVencimiento')
      window.location.href = '/login'
    }
    return Promise.reject(error)
  }
)

export default api
