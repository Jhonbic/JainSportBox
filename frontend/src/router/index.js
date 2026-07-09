import { createRouter, createWebHistory } from 'vue-router'
// Login y Dashboard son el shell inicial → estáticos. El resto se carga on-demand
// (import dinámico) para que cada vista sea su propio chunk y no engorde el bundle
// inicial que descarga alguien que solo entra a /home.
import Dashboard from '../components/Dashboard.vue'
import LoginView from '../views/LoginView.vue'

const UsuariosView = () => import('../views/UsuariosView.vue')
const PlanesView = () => import('../views/PlanesView.vue')
const TiendaView = () => import('../views/TiendaView.vue')
const WodsView = () => import('../views/WodsView.vue')
const FinanzasView = () => import('../views/FinanzasView.vue')
const SaludView = () => import('../views/SaludView.vue')
const SaludMedidaView = () => import('../views/SaludMedidaView.vue')
const MarcasView = () => import('../views/MarcasView.vue')
const MarcasEjercicioView = () => import('../views/MarcasEjercicioView.vue')
const AlertasView = () => import('../views/AlertasView.vue')
const WodsPersonalizadosView = () => import('../views/WodsPersonalizadosView.vue')
const HomeView = () => import('../views/HomeView.vue')
const UsuarioPerfilView = () => import('../views/UsuarioPerfilView.vue')
const SesionesView = () => import('../views/SesionesView.vue')
const EjerciciosView = () => import('../views/EjerciciosView.vue')
const WodFormView = () => import('../views/WodFormView.vue')
const MiPerfilView = () => import('../views/MiPerfilView.vue')

const routes = [
  {
    path: '/login',
    name: 'Login',
    component: LoginView
  },
  {
    path: '/',
    component: Dashboard,
    meta: { requiresAuth: true },
    children: [
      {
        path: '',
        redirect: () => {
          const rol = localStorage.getItem('userRol') || 'cliente'
          if (rol === 'pendiente') return '/planes'
          if (rol === 'admin') return '/usuarios'
          return '/home'
        }
      },
      {
        path: 'usuarios',
        name: 'Usuarios',
        component: UsuariosView,
        meta: { roles: ['admin', 'coach'] }
      },
      {
        path: 'usuarios/:id',
        name: 'UsuarioPerfil',
        component: UsuarioPerfilView,
        meta: { roles: ['admin', 'coach'] }
      },
      {
        path: 'planes',
        name: 'Planes',
        component: PlanesView,
        meta: { roles: ['admin', 'coach', 'cliente', 'pendiente'] }
      },
      {
        path: 'tienda',
        name: 'Tienda',
        component: TiendaView,
        meta: { roles: ['admin', 'coach'] }
      },
      {
        path: 'wods',
        name: 'WODs',
        component: WodsView
      },
      {
        path: 'wods/nuevo',
        name: 'WodNuevo',
        component: WodFormView,
        meta: { roles: ['admin', 'coach'], personalizado: false },
      },
      {
        path: 'wods/:id/editar',
        name: 'WodEditar',
        component: WodFormView,
        meta: { roles: ['admin', 'coach'], personalizado: false },
      },
      {
        path: 'wods/personalizados/nuevo',
        name: 'WodPersonalizadoNuevo',
        component: WodFormView,
        meta: { roles: ['admin', 'coach'], personalizado: true },
      },
      {
        path: 'wods/personalizados/:id/editar',
        name: 'WodPersonalizadoEditar',
        component: WodFormView,
        meta: { roles: ['admin', 'coach'], personalizado: true },
      },
      {
        path: 'finanzas',
        name: 'Finanzas',
        component: FinanzasView,
        meta: { roles: ['admin'] }
      },
      {
        path: 'salud',
        name: 'Salud',
        component: SaludView,
        meta: { roles: ['coach', 'cliente'] },
      },
      {
        path: 'salud/:tipo',
        name: 'SaludMedida',
        component: SaludMedidaView,
        meta: { roles: ['coach', 'cliente'] },
      },
      {
        path: 'marcas',
        name: 'Marcas',
        component: MarcasView,
        meta: { roles: ['coach', 'cliente'] },
      },
      {
        path: 'marcas/:ejercicio',
        name: 'MarcasEjercicio',
        component: MarcasEjercicioView,
        meta: { roles: ['coach', 'cliente'] },
      },
      {
        path: 'alertas',
        name: 'Alertas',
        component: AlertasView,
        meta: { roles: ['admin', 'coach'] },
      },
      {
        path: 'wods/personalizados',
        name: 'WodsPersonalizados',
        component: WodsPersonalizadosView,
        meta: { roles: ['admin', 'coach', 'cliente'] },
      },
      {
        path: 'home',
        name: 'Home',
        component: HomeView,
        meta: { roles: ['cliente', 'coach'] },
      },
      {
        path: 'sesiones',
        name: 'Sesiones',
        component: SesionesView,
        meta: { roles: ['admin', 'coach'] },
      },
      {
        path: 'ejercicios',
        name: 'Ejercicios',
        component: EjerciciosView,
        meta: { roles: ['admin', 'coach'] },
      },
      {
        path: 'perfil',
        name: 'MiPerfil',
        component: MiPerfilView,
        meta: { roles: ['admin', 'coach', 'cliente'] },
      }
    ]
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

import { membresiaVencidaFor } from '../composables/useAuth'

// Rutas permitidas para clientes con membresía vencida
const RUTAS_CLIENTE_VENCIDO = ['/home', '/planes', '/perfil', '/']

router.beforeEach((to, from, next) => {
  const token = localStorage.getItem('token')
  const rol = localStorage.getItem('userRol') || 'cliente'

  if (to.meta.requiresAuth && !token) {
    return next('/login')
  }

  if (to.path === '/login' && token) {
    return next('/')
  }

  // Usuarios pendientes solo pueden ver /planes
  if (rol === 'pendiente' && to.path !== '/planes' && to.path !== '/') {
    return next('/planes')
  }

  // Clientes con membresía vencida solo ven /home y /planes.
  // OJO: solo aplica si HAY token — sin token, el rol "cliente" es solo un default
  // de localStorage y no debe activar la restricción (evita bucle hacia /login).
  if (token && rol === 'cliente') {
    const fechaVenc = localStorage.getItem('fechaVencimiento') || ''
    if (membresiaVencidaFor(fechaVenc) && !RUTAS_CLIENTE_VENCIDO.includes(to.path)) {
      return next('/home')
    }
  }

  if (to.meta.roles && !to.meta.roles.includes(rol)) {
    return next(rol === 'admin' ? '/usuarios' : '/home')
  }

  next()
})

export default router
