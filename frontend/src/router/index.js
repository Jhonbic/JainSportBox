import { createRouter, createWebHistory } from 'vue-router'
import { marcarNavegacionEnCurso, marcarNavegacionTerminada } from '../lib/navegacion'
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
const WodsPersonalizadosView = () => import('../views/WodsPersonalizadosView.vue')
const HomeView = () => import('../views/HomeView.vue')
const UsuarioPerfilView = () => import('../views/UsuarioPerfilView.vue')
const AccesoView = () => import('../views/AccesoView.vue')
const EjerciciosView = () => import('../views/EjerciciosView.vue')
const WodFormView = () => import('../views/WodFormView.vue')
const MiPerfilView = () => import('../views/MiPerfilView.vue')

const routes = [
  {
    path: '/login',
    name: 'Login',
    component: LoginView
  },
  // /acceso vive FUERA del shell de Dashboard (a diferencia del resto): es una
  // pantalla de recepción a pantalla completa, sin sidebar, para que el cliente que
  // marca su cédula no tenga por dónde entrar al panel del coach.
  {
    path: '/acceso',
    name: 'Acceso',
    component: AccesoView,
    meta: { requiresAuth: true, roles: ['admin', 'coach'] },
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
          if (rol === 'admin') return '/dashboard'
          return '/home'
        }
      },
      {
        path: 'dashboard',
        name: 'Dashboard',
        component: () => import('../views/DashboardView.vue'),
        meta: { roles: ['admin', 'coach'] }
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
import { kioscoBloqueado, desactivarKiosco } from '../composables/useKiosco'

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

  // Candado del modo kiosco: mientras esté activo, toda navegación vuelve a /acceso
  // (URL escrita a mano, botón atrás, F5). Salir exige la contraseña del staff, y eso
  // lo maneja AccesoView. Va antes de las reglas de rol para que ninguna de ellas
  // pueda sacar la pestaña del kiosco.
  if (token && kioscoBloqueado()) {
    // Un rol no-staff no puede estar en /acceso (lo rebota meta.roles más abajo).
    // Sin esta salida, el candado y el guard de roles se rebotarían en bucle.
    if (rol !== 'admin' && rol !== 'coach') desactivarKiosco()
    else if (to.path !== '/acceso') return next('/acceso')
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

// ── Indicador de navegación ──────────────────────────────────────
// Casi todas las vistas son chunks lazy: entre que se dispara la navegación y que
// la vista aparece hay una descarga, y durante ese rato el área de contenido queda
// en blanco sin que nada avise. Esto lo llena con el logo (ver `Dashboard.vue`).
router.beforeEach((to, from, next) => {
  marcarNavegacionEnCurso()
  next()
})

router.afterEach(marcarNavegacionTerminada)
// Si el chunk no baja (deploy nuevo que invalidó el hash, o se cayó la red), sin
// esto el logo se quedaría para siempre.
router.onError(marcarNavegacionTerminada)

export default router
