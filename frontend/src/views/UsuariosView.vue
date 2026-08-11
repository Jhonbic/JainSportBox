<template>
  <div class="animate-fade-in-up">
    <!-- Header -->
    <div class="flex flex-col sm:flex-row justify-between items-start sm:items-center mb-8 gap-4">
      <div>
        <h2 class="text-3xl font-extrabold text-gray-900 tracking-tight">Clientes</h2>
        <p class="text-gray-500 mt-1">Gestiona los clientes y sus membresías</p>
      </div>
      <div class="flex flex-wrap gap-2">
        <!-- El endpoint exporta una hoja por grupo: el panel de abajo elige cuáles. -->
        <div class="relative">
          <button @click="toggleExportar" :disabled="exportando" class="bg-white border border-gray-300 hover:border-red-500 hover:text-red-700 disabled:opacity-60 text-gray-700 px-4 py-2.5 rounded-lg shadow-sm hover:shadow transition-all font-semibold flex items-center gap-2 transform active:scale-95">
            <span v-if="exportando" class="animate-spin rounded-full h-4 w-4 border-b-2 border-red-600"></span>
            <svg v-else xmlns="http://www.w3.org/2000/svg" class="h-5 w-5 text-red-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"/>
            </svg>
            {{ exportando ? 'Exportando…' : 'Exportar Excel' }}
            <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4 text-gray-400 transition-transform" :class="showExportar ? 'rotate-180' : ''" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2.5">
              <path stroke-linecap="round" stroke-linejoin="round" d="M19 9l-7 7-7-7" />
            </svg>
          </button>

          <!-- Capa transparente: un clic afuera cierra el panel. -->
          <div v-if="showExportar" class="fixed inset-0 z-30" @click="showExportar = false"></div>

          <div v-if="showExportar"
            class="absolute right-0 mt-2 w-72 bg-white rounded-xl border border-gray-200 shadow-xl z-40 p-3">
            <p class="text-xs font-bold text-gray-400 uppercase tracking-widest mb-2 px-1">Qué exportar</p>

            <label class="flex items-center gap-3 p-2.5 rounded-lg cursor-pointer transition-colors"
              :class="expClientes ? 'bg-red-50' : 'hover:bg-gray-50'">
              <input type="checkbox" v-model="expClientes" class="w-4 h-4 accent-red-600 rounded flex-shrink-0">
              <span class="min-w-0">
                <span class="block text-sm font-semibold text-gray-800">Clientes</span>
                <span class="block text-xs text-gray-500">{{ clientes.length }} registros</span>
              </span>
            </label>

            <label class="flex items-center gap-3 p-2.5 rounded-lg cursor-pointer transition-colors"
              :class="expEquipo ? 'bg-red-50' : 'hover:bg-gray-50'">
              <input type="checkbox" v-model="expEquipo" class="w-4 h-4 accent-red-600 rounded flex-shrink-0">
              <span class="min-w-0">
                <span class="block text-sm font-semibold text-gray-800">Equipo del box</span>
                <span class="block text-xs text-gray-500">{{ equipo.length }} registros</span>
              </span>
            </label>

            <p class="text-xs text-gray-400 px-1 mt-2">Cada grupo va en su propia hoja.</p>

            <button @click="exportarExcel" :disabled="exportando || (!expClientes && !expEquipo)"
              class="mt-3 w-full py-2.5 rounded-lg bg-red-600 hover:bg-red-700 disabled:opacity-40 disabled:cursor-not-allowed text-white font-bold text-sm transition-colors inline-flex items-center justify-center gap-2">
              <span v-if="exportando" class="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></span>
              {{ exportando ? 'Exportando…' : 'Descargar' }}
            </button>
          </div>
        </div>
        <!-- "Abrir palanquera" se mudó a /acceso: es el fallback de recepción. -->
        <button @click="abrirBuscarHuella" class="bg-gray-700 hover:bg-gray-800 text-white px-4 py-2.5 rounded-lg shadow-md hover:shadow-lg transition-all font-semibold flex items-center gap-2 transform active:scale-95">
          <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
            <path fill-rule="evenodd" d="M6.625 2.655A9 9 0 0119 11a1 1 0 11-2 0 7 7 0 00-9.625-6.492 1 1 0 11-.75-1.853zM4.662 4.959A1 1 0 014.75 6.37 6.97 6.97 0 003 11a1 1 0 11-2 0 8.97 8.97 0 012.25-5.953 1 1 0 011.412-.088z" clip-rule="evenodd"/>
            <path fill-rule="evenodd" d="M5 11a5 5 0 1110 0 1 1 0 11-2 0 3 3 0 10-6 0c0 1.677-.345 3.276-.968 4.729a1 1 0 11-1.838-.789A9.964 9.964 0 005 11z" clip-rule="evenodd"/>
          </svg>
          Buscar por Huella
        </button>
        <!-- Staff solo lo crea un admin (el backend ya lo exige en POST). -->
        <button v-if="vista === 'clientes' || isAdmin" @click="abrirFormulario(vista === 'equipo')"
          class="bg-red-600 hover:bg-red-700 text-white px-5 py-2.5 rounded-lg shadow-md hover:shadow-lg transition-all font-semibold flex items-center gap-2 transform active:scale-95">
          <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
            <path fill-rule="evenodd" d="M10 3a1 1 0 011 1v5h5a1 1 0 110 2h-5v5a1 1 0 11-2 0v-5H4a1 1 0 110-2h5V4a1 1 0 011-1z" clip-rule="evenodd" />
          </svg>
          {{ vista === 'equipo' ? 'Nuevo miembro' : 'Nuevo Cliente' }}
        </button>
      </div>
    </div>

    <!-- Switch de listado -->
    <div class="flex gap-2 mb-4 border-b border-gray-200">
      <button v-for="v in [{ key: 'clientes', label: 'Clientes', count: clientes.length },
                           { key: 'equipo',   label: 'Equipo del box', count: equipo.length }]"
        :key="v.key" @click="vista = v.key"
        class="flex items-center gap-2 px-1 pb-3 -mb-px text-sm font-bold border-b-2 transition-colors"
        :class="vista === v.key
          ? 'border-red-600 text-red-600'
          : 'border-transparent text-gray-400 hover:text-gray-600'">
        {{ v.label }}
        <span class="text-xs font-black px-1.5 py-0.5 rounded-full"
          :class="vista === v.key ? 'bg-red-100 text-red-700' : 'bg-gray-100 text-gray-500'">
          {{ v.count }}
        </span>
      </button>
    </div>

    <!-- Buscador -->
    <div v-if="vista === 'clientes'" class="relative mb-4">
      <svg xmlns="http://www.w3.org/2000/svg" class="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-4.35-4.35M17 11A6 6 0 1 1 5 11a6 6 0 0 1 12 0z"/>
      </svg>
      <input
        v-model="busqueda"
        type="text"
        placeholder="Buscar por nombre o documento de identidad..."
        class="w-full pl-9 pr-4 py-2.5 rounded-xl border border-gray-200 focus:ring-2 focus:ring-red-500 focus:border-red-500 outline-none text-sm transition-all"
      >
      <button v-if="busqueda" @click="busqueda = ''" class="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600">
        <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/></svg>
      </button>
    </div>

    <!-- Filtros + orden -->
    <div v-if="vista === 'clientes'" class="flex flex-wrap items-center gap-2 mb-5">
      <button v-for="tab in tabs" :key="tab.key" @click="filtroActivo = tab.key"
        class="flex items-center gap-2 px-4 py-2 rounded-xl text-sm font-semibold transition-all border"
        :class="filtroActivo === tab.key
          ? 'bg-red-600 text-white border-red-600 shadow-md'
          : 'bg-white text-gray-600 border-gray-200 hover:border-red-300 hover:text-red-600'">
        {{ tab.label }}
        <span class="text-xs font-black px-1.5 py-0.5 rounded-full"
          :class="filtroActivo === tab.key ? 'bg-white/20 text-white' : 'bg-gray-100 text-gray-500'">
          {{ tab.count }}
        </span>
      </button>

      <!-- Ordenar por -->
      <div v-if="filtroActivo !== 'pendientes'" class="flex items-center gap-2 ml-auto">
        <label for="orden-usuarios" class="text-xs font-semibold text-gray-400 uppercase tracking-widest hidden sm:block">
          Ordenar por
        </label>
        <select
          id="orden-usuarios"
          v-model="orden"
          class="px-3 py-2 rounded-xl border border-gray-200 bg-white text-sm font-semibold text-gray-600 focus:ring-2 focus:ring-red-500 focus:border-red-500 outline-none transition-all cursor-pointer"
        >
          <option v-for="o in ORDENES" :key="o.key" :value="o.key">{{ o.label }}</option>
        </select>
      </div>
    </div>

    <!-- ══════════ LISTADO: CLIENTES ══════════ -->
    <template v-if="vista === 'clientes'">

    <!-- Loading -->
    <div v-if="loading && filtroActivo !== 'pendientes'" class="flex justify-center py-16">
      <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-red-600"></div>
    </div>

    <!-- Empty -->
    <div v-else-if="filtroActivo !== 'pendientes' && usuariosFiltrados.length === 0" class="bg-white rounded-xl border border-gray-100 px-6 py-12 text-center text-gray-400">
      <svg xmlns="http://www.w3.org/2000/svg" class="h-12 w-12 mx-auto text-gray-300 mb-3" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0z"/></svg>
      {{ tabs.find(t => t.key === filtroActivo)?.emptyMsg || 'No hay clientes.' }}
    </div>

    <template v-else-if="filtroActivo !== 'pendientes'">
      <!-- ── Cards (móvil) ── -->
      <div class="sm:hidden space-y-3">
        <div v-for="user in paginaItems" :key="user.id"
          class="bg-white rounded-xl border border-gray-100 shadow-sm p-4">
          <div class="flex items-center gap-3 mb-3">
            <img loading="lazy" class="h-11 w-11 rounded-full object-cover bg-gray-100 flex-shrink-0" :src="fotoSrc(user)" alt="" />
            <div class="min-w-0 flex-1">
              <p class="font-semibold text-gray-900 truncate">{{ user.nombre }}</p>
              <p class="text-xs text-gray-500 truncate">{{ user.email }}</p>
            </div>
          </div>
          <div class="flex items-center justify-between">
            <div>
              <template v-if="user.fecha_vencimiento">
                <!-- El punto va también acá: sin él, al neutralizar el texto la card
                     móvil se quedaba sin ninguna señal de estado. -->
                <p class="text-sm font-semibold flex items-center gap-2" :class="colorTextoDias(diasRestantes(user.fecha_vencimiento))">
                  <span class="w-2 h-2 rounded-full flex-shrink-0" :class="colorPuntoDias(diasRestantes(user.fecha_vencimiento))"></span>
                  {{ etiquetaDias(diasRestantes(user.fecha_vencimiento)) }}
                </p>
                <p v-if="user.ingresos_restantes !== null && user.ingresos_restantes !== undefined"
                  class="text-xs font-semibold ml-4" :class="user.ingresos_restantes > 0 ? 'text-gray-600' : 'text-red-600'">
                  {{ user.ingresos_restantes }} {{ user.ingresos_restantes === 1 ? 'ingreso' : 'ingresos' }}
                </p>
                <p class="text-xs text-gray-400 ml-4">Vence {{ formatFecha(user.fecha_vencimiento) }}</p>
              </template>
              <span v-else class="text-sm text-gray-400 italic">Sin membresía</span>
            </div>
            <div class="flex items-center gap-2">
              <span class="flex items-center gap-1 text-xs font-semibold px-2 py-1 rounded-full border"
                :class="user.esta_en_gym ? 'bg-emerald-100 text-emerald-800 border-emerald-200' : 'bg-gray-100 text-gray-600 border-gray-200'">
                <span class="w-1.5 h-1.5 rounded-full" :class="user.esta_en_gym ? 'bg-emerald-500' : 'bg-gray-400'"></span>
                {{ user.esta_en_gym ? 'Activo' : 'Fuera' }}
              </span>
              <button @click="verUsuario(user)" class="p-2 text-gray-400 hover:text-red-600 hover:bg-red-50 rounded-lg transition-colors">
                <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"/><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z"/></svg>
              </button>
              <button @click="confirmarEliminar(user)" class="p-2 text-gray-400 hover:text-red-600 hover:bg-red-50 rounded-lg transition-colors">
                <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"/></svg>
              </button>
            </div>
          </div>
        </div>
      </div>

      <!-- ── Tabla (desktop) ── -->
      <div class="hidden sm:block bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden">
        <div class="overflow-x-auto">
          <table class="min-w-full divide-y divide-gray-200">
            <thead class="bg-gray-50">
              <tr>
                <th class="px-6 py-4 text-left text-xs font-bold text-gray-500 uppercase tracking-wider">Cliente</th>
                <th class="px-6 py-4 text-left text-xs font-bold text-gray-500 uppercase tracking-wider">Membresía</th>
                <th class="px-6 py-4 text-left text-xs font-bold text-gray-500 uppercase tracking-wider">Estado</th>
                <th class="px-6 py-4 text-left text-xs font-bold text-gray-500 uppercase tracking-wider">Acciones</th>
              </tr>
            </thead>
            <tbody class="bg-white divide-y divide-gray-100">
              <tr v-for="user in paginaItems" :key="user.id" class="hover:bg-gray-50 transition-colors group">
                <td class="px-6 py-4 whitespace-nowrap">
                  <div class="flex items-center gap-3">
                    <img loading="lazy" class="h-10 w-10 rounded-full object-cover bg-gray-100 flex-shrink-0" :src="fotoSrc(user)" alt="" />
                    <div>
                      <div class="text-sm font-semibold text-gray-900 group-hover:text-red-600 transition-colors">{{ user.nombre }}</div>
                      <div class="text-xs text-gray-500">{{ user.email }}</div>
                    </div>
                  </div>
                </td>
                <td class="px-6 py-4 whitespace-nowrap">
                  <template v-if="user.fecha_vencimiento">
                    <div class="flex items-center gap-2">
                      <span class="w-2 h-2 rounded-full flex-shrink-0" :class="colorPuntoDias(diasRestantes(user.fecha_vencimiento))"></span>
                      <div>
                        <p class="text-sm font-semibold" :class="colorTextoDias(diasRestantes(user.fecha_vencimiento))">{{ etiquetaDias(diasRestantes(user.fecha_vencimiento)) }}</p>
                        <p v-if="user.ingresos_restantes !== null && user.ingresos_restantes !== undefined"
                          class="text-xs font-semibold" :class="user.ingresos_restantes > 0 ? 'text-gray-600' : 'text-red-600'">
                          {{ user.ingresos_restantes }} {{ user.ingresos_restantes === 1 ? 'ingreso' : 'ingresos' }}
                        </p>
                        <p class="text-xs text-gray-400">Vence {{ formatFecha(user.fecha_vencimiento) }}</p>
                      </div>
                    </div>
                  </template>
                  <span v-else class="text-sm text-gray-400 italic">Sin membresía</span>
                </td>
                <td class="px-6 py-4 whitespace-nowrap">
                  <span class="px-3 py-1 inline-flex items-center gap-1.5 text-xs font-semibold rounded-full border shadow-sm"
                    :class="user.esta_en_gym ? 'bg-emerald-100 text-emerald-800 border-emerald-200' : 'bg-gray-100 text-gray-600 border-gray-200'">
                    <span class="w-2 h-2 rounded-full" :class="user.esta_en_gym ? 'bg-emerald-500' : 'bg-gray-400'"></span>
                    {{ user.esta_en_gym ? 'Activo' : 'Fuera' }}
                  </span>
                </td>
                <td class="px-6 py-4 whitespace-nowrap">
                  <div class="flex items-center gap-2">
                    <button @click="verUsuario(user)" title="Ver detalle" class="p-1.5 text-gray-400 hover:text-red-600 hover:bg-red-50 rounded-lg transition-colors">
                      <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"/><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z"/></svg>
                    </button>
                    <button @click="confirmarEliminar(user)" title="Eliminar" class="p-1.5 text-gray-400 hover:text-red-600 hover:bg-red-50 rounded-lg transition-colors">
                      <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"/></svg>
                    </button>
                  </div>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

    </template>

    <!-- ── Tab: Pendientes ── -->
    <template v-if="filtroActivo === 'pendientes'">
      <div v-if="loadingPendientes" class="flex justify-center py-16">
        <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-red-600"></div>
      </div>
      <div v-else-if="pendientes.length === 0" class="bg-white rounded-xl border border-gray-100 px-6 py-12 text-center text-gray-400">
        <svg xmlns="http://www.w3.org/2000/svg" class="h-12 w-12 mx-auto text-gray-300 mb-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"/>
        </svg>
        No hay clientes pendientes de aprobación.
      </div>
      <div v-else-if="pendientesFiltrados.length === 0" class="bg-white rounded-xl border border-gray-100 px-6 py-12 text-center text-gray-400">
        Ningún cliente pendiente coincide con la búsqueda.
      </div>

      <template v-else>
        <!-- ── Barra de selección (solo admin: el borrado masivo es suyo) ── -->
        <div v-if="isAdmin" class="mb-3 flex flex-wrap items-center gap-3">
          <button v-if="hayViejos" @click="seleccionarViejos"
            class="text-xs font-semibold text-gray-500 hover:text-red-600 underline underline-offset-2 transition-colors">
            Seleccionar los de más de {{ PENDIENTE_VIEJO_DIAS }} días ({{ pendientesViejos.length }})
          </button>
          <div v-if="seleccionados.size" class="ml-auto flex items-center gap-3">
            <span class="text-sm font-semibold text-gray-600">{{ seleccionados.size }} seleccionados</span>
            <button @click="limpiarSeleccion" class="text-xs font-semibold text-gray-400 hover:text-gray-600">Limpiar</button>
            <button @click="confirmarEliminarSeleccion"
              class="px-3 py-1.5 rounded-lg bg-red-600 hover:bg-red-700 text-white text-xs font-bold transition-colors">
              Descartar seleccionados
            </button>
          </div>
        </div>

        <!-- ── Cards (móvil) ── -->
        <div class="sm:hidden space-y-3">
          <div v-for="p in paginaItems" :key="p.id" class="bg-white rounded-xl border shadow-sm p-4"
            :class="seleccionados.has(p.id) ? 'border-red-300 bg-red-50/40' : 'border-gray-100'">
            <div class="flex items-center gap-3 mb-3">
              <input v-if="isAdmin" type="checkbox" :checked="seleccionados.has(p.id)" @change="alternarSeleccion(p.id)"
                :aria-label="`Seleccionar a ${p.nombre}`"
                class="h-4 w-4 rounded border-gray-300 text-red-600 focus:ring-red-500 cursor-pointer flex-shrink-0" />
              <img loading="lazy" class="h-11 w-11 rounded-full object-cover bg-gray-100 flex-shrink-0" :src="fotoSrc(p)" alt="" />
              <div class="min-w-0 flex-1">
                <p class="font-semibold text-gray-900 truncate">
                  {{ p.nombre }}
                  <span v-if="p.es_menor" class="align-middle ml-1 text-[10px] font-bold uppercase tracking-wide px-1.5 py-0.5 rounded-full bg-amber-100 text-amber-800 border border-amber-200">Menor</span>
                </p>
                <p class="text-xs text-gray-500 truncate">{{ p.email }}</p>
              </div>
            </div>
            <div class="grid grid-cols-2 gap-2 text-xs mb-3">
              <div class="bg-gray-50 rounded-lg px-3 py-2 min-w-0">
                <p class="text-gray-400 font-semibold uppercase tracking-wide mb-0.5">Documento</p>
                <p class="font-semibold text-gray-700 truncate">{{ p.documento_identidad || '—' }}</p>
              </div>
              <div class="bg-gray-50 rounded-lg px-3 py-2 min-w-0">
                <p class="text-gray-400 font-semibold uppercase tracking-wide mb-0.5">Teléfono</p>
                <p class="font-semibold text-gray-700 truncate">{{ p.telefono || '—' }}</p>
              </div>
            </div>
            <!-- Solo la antigüedad toma color; el plan queda neutro para no gritar toda la línea. -->
            <p class="text-xs text-gray-400 mb-3">
              {{ p.plan_solicitado?.nombre || 'Sin plan solicitado' }} · Registrado
              <span :class="colorAntiguedad(p.created_at)">{{ antiguedadPendiente(p.created_at) }}</span>
            </p>
            <PendienteDetalle v-if="detalleAbierto[p.id]" :p="p" class="mb-3" />
            <div class="flex items-center gap-2">
              <button @click="toggleDetalle(p.id)"
                class="flex items-center gap-1 px-3 py-2 rounded-lg border border-gray-200 text-xs font-semibold text-gray-500 hover:text-gray-700 hover:border-gray-400 transition-colors">
                Datos
                <svg xmlns="http://www.w3.org/2000/svg" class="h-3.5 w-3.5 transition-transform" :class="detalleAbierto[p.id] ? 'rotate-180' : ''" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M19 9l-7 7-7-7"/></svg>
              </button>
              <button @click="abrirActivar(p)"
                class="flex-1 py-2 rounded-lg bg-red-600 hover:bg-red-700 text-white font-bold text-sm transition-colors">
                Activar
              </button>
              <button @click="confirmarEliminar(p, true)" title="Eliminar registro"
                class="p-2 text-gray-400 hover:text-red-600 hover:bg-red-50 rounded-lg transition-colors">
                <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"/></svg>
              </button>
            </div>
          </div>
        </div>

        <!-- ── Tabla (desktop) ── -->
        <div class="hidden sm:block bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden">
          <div class="overflow-x-auto">
            <table class="min-w-full divide-y divide-gray-200">
              <thead class="bg-gray-50">
                <tr>
                  <th v-if="isAdmin" class="pl-6 pr-2 py-4 w-10">
                    <input type="checkbox" :checked="todosDePaginaSeleccionados" @change="alternarSeleccionPagina"
                      aria-label="Seleccionar todos los de esta página"
                      class="h-4 w-4 rounded border-gray-300 text-red-600 focus:ring-red-500 cursor-pointer" />
                  </th>
                  <th class="px-6 py-4 text-left text-xs font-bold text-gray-500 uppercase tracking-wider">Cliente</th>
                  <th class="px-6 py-4 text-left text-xs font-bold text-gray-500 uppercase tracking-wider">Contacto</th>
                  <th class="px-6 py-4 text-left text-xs font-bold text-gray-500 uppercase tracking-wider">Plan solicitado</th>
                  <th class="px-6 py-4 text-left text-xs font-bold text-gray-500 uppercase tracking-wider">Registrado</th>
                  <th class="px-6 py-4 text-right text-xs font-bold text-gray-500 uppercase tracking-wider">Acciones</th>
                </tr>
              </thead>
              <tbody class="bg-white divide-y divide-gray-100">
                <template v-for="p in paginaItems" :key="p.id">
                  <tr class="transition-colors" :class="seleccionados.has(p.id) ? 'bg-red-50/60' : 'hover:bg-gray-50'">
                    <td v-if="isAdmin" class="pl-6 pr-2 py-4">
                      <input type="checkbox" :checked="seleccionados.has(p.id)" @change="alternarSeleccion(p.id)"
                        :aria-label="`Seleccionar a ${p.nombre}`"
                        class="h-4 w-4 rounded border-gray-300 text-red-600 focus:ring-red-500 cursor-pointer" />
                    </td>
                    <td class="px-6 py-4 whitespace-nowrap">
                      <div class="flex items-center gap-3">
                        <img loading="lazy" class="h-10 w-10 rounded-full object-cover bg-gray-100 flex-shrink-0" :src="fotoSrc(p)" alt="" />
                        <div>
                          <div class="text-sm font-semibold text-gray-900 flex items-center gap-2">
                            {{ p.nombre }}
                            <!-- Ámbar, no rojo: ser menor es un aviso, no un error. -->
                            <span v-if="p.es_menor" class="text-[10px] font-bold uppercase tracking-wide px-1.5 py-0.5 rounded-full bg-amber-100 text-amber-800 border border-amber-200">Menor</span>
                          </div>
                          <div class="text-xs text-gray-500">{{ p.email }}</div>
                        </div>
                      </div>
                    </td>
                    <td class="px-6 py-4 whitespace-nowrap">
                      <p class="text-sm text-gray-700">{{ p.telefono || '—' }}</p>
                      <p class="text-xs text-gray-400">CC {{ p.documento_identidad || '—' }}</p>
                    </td>
                    <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-600">{{ p.plan_solicitado?.nombre || '—' }}</td>
                    <td class="px-6 py-4 whitespace-nowrap">
                      <p class="text-sm text-gray-600">{{ formatFechaCorta(p.created_at) }}</p>
                      <p class="text-xs" :class="colorAntiguedad(p.created_at)">
                        {{ antiguedadPendiente(p.created_at) }}
                      </p>
                    </td>
                    <td class="px-6 py-4 whitespace-nowrap">
                      <div class="flex items-center justify-end gap-2">
                        <button @click="toggleDetalle(p.id)" :title="detalleAbierto[p.id] ? 'Ocultar datos de afiliación' : 'Ver datos de afiliación'"
                          class="flex items-center gap-1 px-2.5 py-1.5 rounded-lg border border-gray-200 text-xs font-semibold text-gray-500 hover:text-gray-700 hover:border-gray-400 transition-colors">
                          Datos
                          <svg xmlns="http://www.w3.org/2000/svg" class="h-3.5 w-3.5 transition-transform" :class="detalleAbierto[p.id] ? 'rotate-180' : ''" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M19 9l-7 7-7-7"/></svg>
                        </button>
                        <button @click="abrirActivar(p)"
                          class="px-3 py-1.5 rounded-lg bg-red-600 hover:bg-red-700 text-white text-xs font-bold transition-colors">
                          Activar
                        </button>
                        <!-- Descartar el registro que nunca se presentó. -->
                        <button @click="confirmarEliminar(p, true)" title="Eliminar registro"
                          class="p-1.5 text-gray-400 hover:text-red-600 hover:bg-red-50 rounded-lg transition-colors">
                          <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"/></svg>
                        </button>
                      </div>
                    </td>
                  </tr>
                  <tr v-if="detalleAbierto[p.id]" class="bg-gray-50">
                    <td :colspan="isAdmin ? 6 : 5" class="px-6 py-4">
                      <PendienteDetalle :p="p" />
                    </td>
                  </tr>
                </template>
              </tbody>
            </table>
          </div>
        </div>
      </template>
    </template>

    <!-- ── Paginación (sirve al listado de clientes y al de pendientes) ── -->
    <div v-if="listaFiltrada.length > POR_PAGINA"
      class="mt-4 flex flex-col sm:flex-row items-center justify-between gap-3">
      <p class="text-xs text-gray-500 order-2 sm:order-1">
        Mostrando <span class="font-bold text-gray-700">{{ rangoDesde }}–{{ rangoHasta }}</span>
        de <span class="font-bold text-gray-700">{{ listaFiltrada.length }}</span>
      </p>
      <div class="flex items-center gap-1 order-1 sm:order-2">
        <button @click="irAPagina(pagina - 1)" :disabled="pagina === 1"
          class="px-2.5 py-1.5 rounded-lg border border-gray-200 text-gray-500 hover:border-gray-400 hover:text-gray-700 disabled:opacity-40 disabled:pointer-events-none transition-colors"
          aria-label="Página anterior">
          <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7"/></svg>
        </button>
        <template v-for="(p, i) in paginasVisibles" :key="`${p}-${i}`">
          <span v-if="p === '…'" class="px-1.5 text-gray-400 text-sm select-none">…</span>
          <button v-else @click="irAPagina(p)"
            class="min-w-[2rem] px-2 py-1.5 rounded-lg text-sm font-bold border transition-colors"
            :class="p === pagina
              ? 'bg-gray-800 text-white border-gray-800'
              : 'bg-white text-gray-500 border-gray-200 hover:border-gray-400 hover:text-gray-700'">
            {{ p }}
          </button>
        </template>
        <button @click="irAPagina(pagina + 1)" :disabled="pagina === totalPaginas"
          class="px-2.5 py-1.5 rounded-lg border border-gray-200 text-gray-500 hover:border-gray-400 hover:text-gray-700 disabled:opacity-40 disabled:pointer-events-none transition-colors"
          aria-label="Página siguiente">
          <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7"/></svg>
        </button>
      </div>
    </div>

    </template>
    <template v-else>
      <!-- ══════════ LISTADO: EQUIPO DEL BOX ══════════ -->
      <div v-if="loading" class="flex justify-center py-16">
        <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-red-600"></div>
      </div>

      <div v-else-if="equipo.length === 0" class="bg-white rounded-xl border border-gray-100 px-6 py-12 text-center text-gray-400">
        <svg xmlns="http://www.w3.org/2000/svg" class="h-12 w-12 mx-auto text-gray-300 mb-3" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0z"/></svg>
        No hay miembros del equipo registrados.
      </div>

      <template v-else>
        <!-- ── Cards (móvil) ── -->
        <div class="sm:hidden space-y-3">
          <div v-for="u in equipo" :key="u.id" class="bg-white rounded-xl border border-gray-100 shadow-sm p-4">
            <div class="flex items-center gap-3 mb-3">
              <img loading="lazy" class="h-11 w-11 rounded-full object-cover bg-gray-100 flex-shrink-0" :src="fotoSrc(u)" alt="" />
              <div class="min-w-0 flex-1">
                <p class="font-semibold text-gray-900 truncate">{{ u.nombre }}</p>
                <p class="text-xs text-gray-500 truncate">{{ u.email }}</p>
              </div>
            </div>
            <div class="bg-gray-50 rounded-lg px-3 py-2 text-xs mb-3">
              <p class="text-gray-400 font-semibold uppercase tracking-wide mb-0.5">Teléfono</p>
              <p class="font-semibold text-gray-700">{{ u.telefono || '—' }}</p>
            </div>
            <div class="flex items-center justify-end">
              <div class="flex items-center gap-1">
                <button @click="verUsuario(u)" title="Ver perfil" class="p-2 text-gray-400 hover:text-red-600 hover:bg-red-50 rounded-lg transition-colors">
                  <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"/><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z"/></svg>
                </button>
                <button v-if="puedeEliminarStaff(u)" @click="confirmarEliminar(u)" title="Eliminar" class="p-2 text-gray-400 hover:text-red-600 hover:bg-red-50 rounded-lg transition-colors">
                  <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"/></svg>
                </button>
              </div>
            </div>
          </div>
        </div>

        <!-- ── Tabla (desktop) ── -->
        <div class="hidden sm:block bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden">
          <div class="overflow-x-auto">
            <table class="min-w-full divide-y divide-gray-200">
              <thead class="bg-gray-50">
                <tr>
                  <th class="px-6 py-4 text-left text-xs font-bold text-gray-500 uppercase tracking-wider">Miembro</th>
                  <th class="px-6 py-4 text-left text-xs font-bold text-gray-500 uppercase tracking-wider">Contacto</th>
                  <th class="px-6 py-4 text-left text-xs font-bold text-gray-500 uppercase tracking-wider">Acciones</th>
                </tr>
              </thead>
              <tbody class="bg-white divide-y divide-gray-100">
                <tr v-for="u in equipo" :key="u.id" class="hover:bg-gray-50 transition-colors group">
                  <td class="px-6 py-4 whitespace-nowrap">
                    <div class="flex items-center gap-3">
                      <img loading="lazy" class="h-10 w-10 rounded-full object-cover bg-gray-100 flex-shrink-0" :src="fotoSrc(u)" alt="" />
                      <div>
                        <div class="text-sm font-semibold text-gray-900 group-hover:text-red-600 transition-colors">
                          {{ u.nombre }}
                          <span v-if="u.id === miId" class="ml-1 text-xs font-bold text-gray-400">(vos)</span>
                        </div>
                        <div class="text-xs text-gray-500">{{ u.email }}</div>
                      </div>
                    </div>
                  </td>
                  <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-600">{{ u.telefono || '—' }}</td>
                  <td class="px-6 py-4 whitespace-nowrap">
                    <div class="flex items-center gap-2">
                      <!-- El enrolamiento de staff vive solo en UsuarioPerfilView. -->
                      <button @click="verUsuario(u)" title="Ver perfil" class="p-1.5 text-gray-400 hover:text-red-600 hover:bg-red-50 rounded-lg transition-colors">
                        <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"/><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z"/></svg>
                      </button>
                      <button v-if="puedeEliminarStaff(u)" @click="confirmarEliminar(u)" title="Eliminar" class="p-1.5 text-gray-400 hover:text-red-600 hover:bg-red-50 rounded-lg transition-colors">
                        <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"/></svg>
                      </button>
                      <span v-else class="text-xs text-gray-300 italic">—</span>
                    </div>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </template>
    </template>

    <!-- ── Modal: Confirmar eliminación ── -->
    <div v-if="showEliminar" class="fixed inset-0 flex items-end sm:items-center justify-center bg-gray-900/60 backdrop-blur-sm z-50 p-4">
      <div class="bg-white rounded-2xl w-full max-w-md shadow-2xl overflow-hidden">
        <div class="px-6 pt-6 pb-4 flex items-start gap-4">
          <div class="w-11 h-11 rounded-full bg-red-100 flex items-center justify-center flex-shrink-0">
            <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5 text-red-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01M10.29 3.86L1.82 18a2 2 0 001.71 3h16.94a2 2 0 001.71-3L13.71 3.86a2 2 0 00-3.42 0z"/>
            </svg>
          </div>
          <div class="min-w-0">
            <h3 class="text-lg font-bold text-gray-900">
              <template v-if="eliminandoLote.length">Eliminar {{ eliminandoLote.length }} registros pendientes</template>
              <template v-else>{{ eliminandoPendiente ? 'Eliminar registro pendiente' : 'Eliminar cuenta' }}</template>
            </h3>
            <p class="text-sm text-gray-500 mt-1">
              {{ eliminandoPendiente
                ? 'Se borran las solicitudes de registro. Esas personas pueden volver a registrarse cuando quieran.'
                : 'Se borra la cuenta y su historial queda sin dueño. Esta acción no se puede deshacer.' }}
            </p>
          </div>
        </div>

        <!-- Lote: la lista completa, con scroll. Confirmar un borrado masivo a ciegas
             sobre un contador es justo donde se cuela el error. -->
        <div v-if="eliminandoLote.length" class="mx-6 mb-4 rounded-xl border border-gray-100 bg-gray-50 divide-y divide-gray-100 max-h-48 overflow-y-auto">
          <div v-for="p in eliminandoLote" :key="p.id" class="px-4 py-2 flex items-center gap-3">
            <span class="text-sm text-gray-700 truncate">{{ p.nombre }}</span>
            <span class="ml-auto flex-shrink-0 text-xs" :class="colorAntiguedad(p.created_at)">
              {{ antiguedadPendiente(p.created_at) }}
            </span>
          </div>
        </div>

        <div v-else class="mx-6 mb-4 rounded-xl border border-gray-100 bg-gray-50 px-4 py-3 flex items-center gap-3">
          <img loading="lazy" class="h-10 w-10 rounded-full object-cover bg-gray-100 flex-shrink-0" :src="fotoSrc(eliminando)" alt="" />
          <div class="min-w-0">
            <p class="text-sm font-semibold text-gray-900 truncate">{{ eliminando?.nombre }}</p>
            <p class="text-xs text-gray-500 truncate">{{ eliminando?.email }}</p>
          </div>
          <span v-if="eliminandoPendiente && eliminando?.created_at" class="ml-auto flex-shrink-0 text-xs text-gray-400">
            Registrado {{ antiguedadPendiente(eliminando.created_at) }}
          </span>
        </div>

        <p v-if="errorEliminar" class="mx-6 mb-4 text-sm text-red-600 bg-red-50 border border-red-100 rounded-lg px-3 py-2">
          {{ errorEliminar }}
        </p>

        <div class="px-6 py-4 bg-gray-50 border-t border-gray-100 flex gap-3 justify-end">
          <button @click="showEliminar = false" :disabled="borrando"
            class="px-4 py-2.5 rounded-xl border border-gray-200 text-sm font-semibold text-gray-600 hover:bg-gray-100 disabled:opacity-50 transition-colors">
            Cancelar
          </button>
          <button @click="ejecutarEliminar" :disabled="borrando"
            class="px-4 py-2.5 rounded-xl bg-red-600 hover:bg-red-700 text-white text-sm font-bold disabled:opacity-60 transition-colors">
            {{ borrando ? 'Eliminando…' : 'Eliminar' }}
          </button>
        </div>
      </div>
    </div>

    <!-- ── Modal: Activar usuario pendiente ── -->
    <div v-if="showActivar" class="fixed inset-0 flex items-end sm:items-center justify-center bg-gray-900/60 backdrop-blur-sm z-50 p-4">
      <div class="bg-white rounded-2xl w-full max-w-lg shadow-2xl max-h-[90vh] flex flex-col overflow-hidden">
        <div class="bg-gradient-to-r from-red-600 to-red-700 px-6 py-5 flex items-center gap-3 flex-shrink-0">
          <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"/>
          </svg>
          <div>
            <h3 class="text-lg font-bold text-white">Activar Cliente</h3>
            <p class="text-red-100 text-sm">{{ activarUsuario?.nombre }}</p>
          </div>
          <button @click="showActivar = false" class="ml-auto text-white/70 hover:text-white">
            <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/>
            </svg>
          </button>
        </div>

        <div class="px-6 py-5 overflow-y-auto flex-1 space-y-5">
          <MembresiaSelector v-model="activarForm" :planes="planes" acento="red" />

          <div v-if="errorActivar" class="text-sm text-red-600 bg-red-50 border border-red-100 rounded-lg p-3">{{ errorActivar }}</div>

          <div class="flex gap-3">
            <button @click="showActivar = false" class="flex-1 py-2.5 rounded-xl border border-gray-200 text-gray-600 font-semibold hover:bg-gray-50 transition-colors">Cancelar</button>
            <button @click="confirmarActivar" :disabled="guardandoActivar || !activarForm.plan"
              class="flex-1 py-2.5 rounded-xl bg-red-600 hover:bg-red-700 text-white font-bold transition-colors disabled:bg-red-300 flex items-center justify-center gap-2">
              <span v-if="guardandoActivar" class="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></span>
              {{ guardandoActivar ? 'Activando...' : 'Activar Cliente' }}
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- ── Modal: Ver detalle ── -->
    <div v-if="usuarioSeleccionado" class="fixed inset-0 flex items-end sm:items-center justify-center bg-gray-900/60 backdrop-blur-sm z-50 p-4">
      <div class="bg-white rounded-2xl w-full max-w-md shadow-2xl overflow-hidden max-h-[90vh] flex flex-col">
        <div class="bg-gradient-to-r from-red-600 to-red-700 px-5 py-5 sm:px-8 sm:py-6 flex items-center gap-4 flex-shrink-0">
          <img class="h-16 w-16 rounded-full border-4 border-white shadow-md object-cover" :src="fotoSrc(usuarioSeleccionado)" alt="" />
          <div>
            <h3 class="text-xl font-bold text-white">{{ usuarioSeleccionado.nombre }}</h3>
            <span class="inline-block mt-1 px-2.5 py-0.5 text-xs font-semibold bg-white/20 text-white rounded-full">{{ usuarioSeleccionado.rol }}</span>
          </div>
          <button @click="usuarioSeleccionado = null" class="ml-auto text-white/70 hover:text-white">
            <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/></svg>
          </button>
        </div>
        <div class="px-5 py-5 sm:px-8 sm:py-6 space-y-4 overflow-y-auto flex-1">
          <div class="grid grid-cols-2 gap-4">
            <div class="bg-gray-50 rounded-xl p-4">
              <p class="text-xs text-gray-400 font-semibold uppercase tracking-wide mb-1">Email</p>
              <p class="text-sm font-semibold text-gray-800 break-all">{{ usuarioSeleccionado.email }}</p>
            </div>
            <div class="bg-gray-50 rounded-xl p-4">
              <p class="text-xs text-gray-400 font-semibold uppercase tracking-wide mb-1">Documento</p>
              <p class="text-sm font-semibold text-gray-800">{{ usuarioSeleccionado.documento_identidad }}</p>
            </div>
            <div class="bg-gray-50 rounded-xl p-4">
              <p class="text-xs text-gray-400 font-semibold uppercase tracking-wide mb-1">Género</p>
              <span
                v-if="usuarioSeleccionado.genero"
                class="inline-block text-xs font-bold px-2.5 py-1 rounded-full"
                :class="BADGE_NEUTRO"
              >
                {{ usuarioSeleccionado.genero === 'masculino' ? 'Masculino' : 'Femenino' }}
              </span>
              <p v-else class="text-sm text-gray-400 italic">—</p>
            </div>
            <div class="bg-gray-50 rounded-xl p-4">
              <p class="text-xs text-gray-400 font-semibold uppercase tracking-wide mb-1">Huella Digital</p>
              <div class="flex items-center justify-between gap-2">
                <p class="text-sm font-semibold" :class="usuarioSeleccionado.huella_id ? 'text-emerald-700' : 'text-gray-400'">
                  {{ usuarioSeleccionado.huella_id ? 'Registrada' : 'No registrada' }}
                </p>
                <button
                  @click="abrirEnrolamiento(usuarioSeleccionado)"
                  class="text-xs px-2.5 py-1 rounded-lg bg-red-600 hover:bg-red-700 text-white font-semibold transition-colors flex items-center gap-1"
                >
                  <svg xmlns="http://www.w3.org/2000/svg" class="h-3.5 w-3.5" viewBox="0 0 20 20" fill="currentColor">
                    <path fill-rule="evenodd" d="M6.625 2.655A9 9 0 0119 11a1 1 0 11-2 0 7 7 0 00-9.625-6.492 1 1 0 11-.75-1.853zM4.662 4.959A1 1 0 014.75 6.37 6.97 6.97 0 003 11a1 1 0 11-2 0 8.97 8.97 0 012.25-5.953 1 1 0 011.412-.088z" clip-rule="evenodd"/>
                    <path fill-rule="evenodd" d="M5 11a5 5 0 1110 0 1 1 0 11-2 0 3 3 0 10-6 0c0 1.677-.345 3.276-.968 4.729a1 1 0 11-1.838-.789A9.964 9.964 0 005 11z" clip-rule="evenodd"/>
                  </svg>
                  {{ usuarioSeleccionado.huella_id ? 'Re-registrar' : 'Registrar' }}
                </button>
              </div>
            </div>
            <div class="bg-gray-50 rounded-xl p-4 col-span-2">
              <p class="text-xs text-gray-400 font-semibold uppercase tracking-wide mb-2">Membresía</p>
              <template v-if="usuarioSeleccionado.fecha_vencimiento">
                <div class="flex items-center justify-between">
                  <div>
                    <p class="text-sm font-bold" :class="colorTextoDias(diasRestantes(usuarioSeleccionado.fecha_vencimiento))">
                      {{ etiquetaDias(diasRestantes(usuarioSeleccionado.fecha_vencimiento)) }}
                    </p>
                    <p class="text-xs text-gray-500 mt-0.5">Vence el {{ formatFecha(usuarioSeleccionado.fecha_vencimiento) }}</p>
                  </div>
                  <div class="w-12 h-12 rounded-full flex items-center justify-center"
                    :class="bgCirculoDias(diasRestantes(usuarioSeleccionado.fecha_vencimiento))">
                    <span class="text-xs font-black" :class="colorTextoDias(diasRestantes(usuarioSeleccionado.fecha_vencimiento))">
                      {{ Math.abs(diasRestantes(usuarioSeleccionado.fecha_vencimiento)) }}d
                    </span>
                  </div>
                </div>
              </template>
              <p v-else class="text-sm text-gray-400">Sin membresía activa</p>
            </div>
            <div class="bg-gray-50 rounded-xl p-4">
              <p class="text-xs text-gray-400 font-semibold uppercase tracking-wide mb-1">En el box</p>
              <div class="flex items-center gap-2 mt-1">
                <span class="w-2.5 h-2.5 rounded-full" :class="usuarioSeleccionado.esta_en_gym ? 'bg-emerald-500' : 'bg-gray-300'"></span>
                <p class="text-sm font-semibold text-gray-800">{{ usuarioSeleccionado.esta_en_gym ? 'Activo' : 'Fuera' }}</p>
              </div>
            </div>
            <div class="bg-gray-50 rounded-xl p-4">
              <p class="text-xs text-gray-400 font-semibold uppercase tracking-wide mb-1">Miembro desde</p>
              <p class="text-sm font-semibold text-gray-800">{{ formatFechaCorta(usuarioSeleccionado.created_at) }}</p>
            </div>
          </div>
        </div>
        <div class="px-8 pb-6 flex gap-3">
          <button @click="usuarioSeleccionado = null" class="py-2.5 px-4 rounded-xl border border-gray-200 text-gray-600 font-semibold hover:bg-gray-50 transition-colors">Cerrar</button>
          <button @click="abrirRenovar(usuarioSeleccionado); usuarioSeleccionado = null" class="flex-1 py-2.5 rounded-xl bg-emerald-500 hover:bg-emerald-600 text-white font-semibold transition-colors">Renovar</button>
          <button @click="abrirEditar(usuarioSeleccionado); usuarioSeleccionado = null" class="flex-1 py-2.5 rounded-xl bg-amber-500 hover:bg-amber-600 text-white font-semibold transition-colors">Editar</button>
        </div>
      </div>
    </div>

    <!-- ── Modal: Renovar membresía ── -->
    <div v-if="showRenovar" class="fixed inset-0 flex items-end sm:items-center justify-center bg-gray-900/60 backdrop-blur-sm z-50 p-4">
      <div class="bg-white rounded-2xl w-full max-w-lg shadow-2xl max-h-[90vh] flex flex-col overflow-hidden">
        <div class="bg-gradient-to-r from-emerald-500 to-emerald-600 px-6 py-5 flex items-center gap-3 flex-shrink-0">
          <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"/></svg>
          <div>
            <h3 class="text-lg font-bold text-white">Renovar Membresía</h3>
            <p class="text-emerald-100 text-sm">{{ renovarUsuario?.nombre }}</p>
          </div>
          <button @click="showRenovar = false" class="ml-auto text-white/70 hover:text-white">
            <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/></svg>
          </button>
        </div>

        <div class="px-6 py-5 overflow-y-auto flex-1">
          <!-- Estado actual -->
          <div class="mb-5 p-3 rounded-xl"
            :class="renovarUsuario?.fecha_vencimiento && diasRestantes(renovarUsuario.fecha_vencimiento) > 0
              ? 'bg-emerald-50 border border-emerald-100'
              : 'bg-red-50 border border-red-100'">
            <p class="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-1">Membresía actual</p>
            <template v-if="renovarUsuario?.fecha_vencimiento">
              <p class="text-sm font-bold" :class="colorTextoDias(diasRestantes(renovarUsuario.fecha_vencimiento))">
                {{ etiquetaDias(diasRestantes(renovarUsuario.fecha_vencimiento)) }}
              </p>
              <p class="text-xs text-gray-500">Vence el {{ formatFecha(renovarUsuario.fecha_vencimiento) }} · Los días nuevos se sumarán a esa fecha.</p>
            </template>
            <p v-else class="text-sm text-gray-500">Sin membresía activa — los días contarán desde hoy.</p>
          </div>

          <MembresiaSelector v-model="renovarForm" :planes="planes" acento="emerald"
            titulo="Selecciona un plan" :vencimiento-actual="renovarUsuario?.fecha_vencimiento || null" />

          <div v-if="errorRenovar" class="mt-4 text-sm text-red-600 bg-red-50 border border-red-100 rounded-lg p-3">{{ errorRenovar }}</div>

          <div class="flex gap-3 mt-5">
            <button @click="showRenovar = false" class="flex-1 py-2.5 rounded-xl border border-gray-200 text-gray-600 font-semibold hover:bg-gray-50 transition-colors">Cancelar</button>
            <button @click="confirmarRenovacion" :disabled="guardandoRenovar || !renovarForm.plan"
              class="flex-1 py-2.5 rounded-xl bg-emerald-500 hover:bg-emerald-600 text-white font-bold transition-colors disabled:bg-emerald-200 flex items-center justify-center gap-2">
              <span v-if="guardandoRenovar" class="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></span>
              {{ guardandoRenovar ? 'Guardando...' : 'Confirmar Renovación' }}
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- ── Modal: Editar usuario ── -->
    <div v-if="showEditar" class="fixed inset-0 flex items-end sm:items-center justify-center bg-gray-900/60 backdrop-blur-sm z-50 p-4">
      <div class="bg-white rounded-2xl p-5 sm:p-8 w-full max-w-lg shadow-2xl max-h-[90vh] overflow-y-auto">
        <div class="flex justify-between items-center mb-6">
          <div>
            <h3 class="text-2xl font-bold text-gray-900">Editar Cliente</h3>
            <p class="text-sm text-gray-500 mt-0.5">{{ editando?.nombre }}</p>
          </div>
          <button @click="cerrarEditar" class="text-gray-400 hover:text-gray-600">
            <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/></svg>
          </button>
        </div>

        <!-- Foto -->
        <div class="mb-6 flex flex-col items-center">
          <div class="relative h-24 w-24 rounded-full border-4 border-dashed border-gray-200 bg-gray-50 flex items-center justify-center cursor-pointer hover:border-red-400 hover:bg-red-50 transition-all overflow-hidden"
            @click="$refs.inputFotoEdit.click()">
            <img v-if="editFotoPreview" :src="editFotoPreview" class="h-full w-full object-cover" />
            <img v-else-if="editando?.foto_url" :src="mediaUrl(editando.foto_url)" class="h-full w-full object-cover" />
            <div v-else class="flex flex-col items-center text-gray-400">
              <svg xmlns="http://www.w3.org/2000/svg" class="h-8 w-8" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M3 9a2 2 0 012-2h.93a2 2 0 001.664-.89l.812-1.22A2 2 0 0110.07 4h3.86a2 2 0 011.664.89l.812 1.22A2 2 0 0018.07 7H19a2 2 0 012 2v9a2 2 0 01-2 2H5a2 2 0 01-2-2V9z"/><path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M15 13a3 3 0 11-6 0 3 3 0 016 0z"/></svg>
            </div>
            <input ref="inputFotoEdit" type="file" accept="image/jpeg,image/png,image/webp" class="hidden" @change="onFotoEditChange" />
          </div>
          <p class="text-xs text-gray-400 mt-2">Clic para cambiar la foto</p>
        </div>

        <form @submit.prevent="guardarEdicion">
          <div class="mb-5">
            <label class="block text-gray-700 text-sm font-semibold mb-2">Email</label>
            <input v-model="editForm.email" type="email" class="w-full px-4 py-3 rounded-lg border border-gray-300 focus:ring-2 focus:ring-red-500 outline-none transition-all" required>
          </div>
          <div class="mb-5">
            <label class="block text-gray-700 text-sm font-semibold mb-2">Teléfono / WhatsApp</label>
            <input v-model="editForm.telefono" type="tel" class="w-full px-4 py-3 rounded-lg border border-gray-300 focus:ring-2 focus:ring-red-500 outline-none transition-all">
          </div>
          <div class="mb-5">
            <label class="block text-gray-700 text-sm font-semibold mb-2">Género</label>
            <div class="grid grid-cols-2 gap-3">
              <button
                type="button"
                @click="editForm.genero = 'masculino'"
                class="py-2.5 rounded-xl border-2 font-bold text-sm transition-all"
                :class="editForm.genero === 'masculino'
                  ? 'border-gray-800 bg-gray-800 text-white'
                  : 'border-gray-200 text-gray-500 hover:border-gray-400 hover:text-gray-700'"
              >
                Masculino
              </button>
              <button
                type="button"
                @click="editForm.genero = 'femenino'"
                class="py-2.5 rounded-xl border-2 font-bold text-sm transition-all"
                :class="editForm.genero === 'femenino'
                  ? 'border-gray-800 bg-gray-800 text-white'
                  : 'border-gray-200 text-gray-500 hover:border-gray-400 hover:text-gray-700'"
              >
                Femenino
              </button>
            </div>
          </div>
          <div class="mb-6">
            <label class="block text-gray-700 text-sm font-semibold mb-2">Nueva Contraseña <span class="text-gray-400 font-normal">(dejar vacío para no cambiar)</span></label>
            <InputPassword v-model="editForm.password" minlength="6" autocomplete="new-password"
              placeholder="Min. 6 caracteres" input-class="w-full px-4 py-3 rounded-lg border border-gray-300 focus:ring-2 focus:ring-red-500 outline-none transition-all" />
          </div>
          <div class="flex justify-end gap-3 pt-4 border-t border-gray-100">
            <button @click="cerrarEditar" type="button" class="px-5 py-2.5 rounded-lg text-gray-600 font-semibold hover:bg-gray-100 transition-colors">Cancelar</button>
            <button type="submit" :disabled="guardandoEdicion" class="px-5 py-2.5 rounded-lg bg-red-600 hover:bg-red-700 text-white font-semibold shadow-md inline-flex items-center gap-2 transition-all active:scale-95">
              <span v-if="guardandoEdicion" class="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></span>
              {{ guardandoEdicion ? 'Guardando...' : 'Guardar Cambios' }}
            </button>
          </div>
        </form>
      </div>
    </div>

    <!-- ── Modal: Crear usuario ── -->
    <div v-if="showForm" class="fixed inset-0 flex items-end sm:items-center justify-center bg-gray-900/60 backdrop-blur-sm z-50 p-4">
      <div class="bg-white rounded-2xl p-5 sm:p-8 w-full max-w-lg shadow-2xl max-h-[90vh] overflow-y-auto">
        <div class="flex justify-between items-center mb-6">
          <h3 class="text-2xl font-bold text-gray-900">{{ creandoStaff ? 'Nuevo miembro' : 'Registrar Cliente' }}</h3>
          <button @click="cerrarFormulario" class="text-gray-400 hover:text-gray-600">
            <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/></svg>
          </button>
        </div>

        <!-- Foto -->
        <div class="mb-6 flex flex-col items-center">
          <div class="relative h-24 w-24 rounded-full border-4 border-dashed border-gray-200 bg-gray-50 flex items-center justify-center cursor-pointer hover:border-red-400 hover:bg-red-50 transition-all overflow-hidden"
            @click="$refs.inputFoto.click()">
            <img v-if="fotoPreview" :src="fotoPreview" class="h-full w-full object-cover" />
            <div v-else class="flex flex-col items-center text-gray-400">
              <svg xmlns="http://www.w3.org/2000/svg" class="h-8 w-8" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M3 9a2 2 0 012-2h.93a2 2 0 001.664-.89l.812-1.22A2 2 0 0110.07 4h3.86a2 2 0 011.664.89l.812 1.22A2 2 0 0018.07 7H19a2 2 0 012 2v9a2 2 0 01-2 2H5a2 2 0 01-2-2V9z"/><path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M15 13a3 3 0 11-6 0 3 3 0 016 0z"/></svg>
            </div>
            <input ref="inputFoto" type="file" accept="image/jpeg,image/png,image/webp" class="hidden" @change="onFotoChange" />
          </div>
          <p class="text-xs text-gray-400 mt-2">Foto de perfil (opcional)</p>
          <button v-if="fotoArchivo" type="button" @click="quitarFoto" class="text-xs text-red-400 hover:text-red-600 mt-1">Quitar foto</button>
        </div>

        <form @submit.prevent="crearUsuario">
          <div class="mb-5">
            <label class="block text-gray-700 text-sm font-semibold mb-2">Nombre Completo <span class="text-red-500">*</span></label>
            <input v-model="nuevoUsuario.nombre" type="text" class="w-full px-4 py-3 rounded-lg border border-gray-300 focus:ring-2 focus:ring-red-500 outline-none transition-all" required>
          </div>
          <div class="mb-5">
            <label class="block text-gray-700 text-sm font-semibold mb-2">Documento de Identidad <span class="text-red-500">*</span></label>
            <input v-model="nuevoUsuario.documento_identidad" type="text" required minlength="5" maxlength="20" class="w-full px-4 py-3 rounded-lg border border-gray-300 focus:ring-2 focus:ring-red-500 outline-none transition-all">
          </div>
          <div class="mb-5">
            <label class="block text-gray-700 text-sm font-semibold mb-2">Email <span class="text-red-500">*</span></label>
            <input v-model="nuevoUsuario.email" type="email" class="w-full px-4 py-3 rounded-lg border border-gray-300 focus:ring-2 focus:ring-red-500 outline-none transition-all" required>
          </div>
          <div class="mb-5">
            <label class="block text-gray-700 text-sm font-semibold mb-2">Contraseña <span class="text-red-500">*</span></label>
            <InputPassword v-model="nuevoUsuario.password" required minlength="6" autocomplete="new-password"
              placeholder="Min. 6 caracteres" input-class="w-full px-4 py-3 rounded-lg border border-gray-300 focus:ring-2 focus:ring-red-500 outline-none transition-all" />
          </div>
          <div class="mb-5">
            <label class="block text-gray-700 text-sm font-semibold mb-2">Teléfono / WhatsApp <span class="text-red-500">*</span></label>
            <input v-model="nuevoUsuario.telefono" type="tel" required minlength="7" class="w-full px-4 py-3 rounded-lg border border-gray-300 focus:ring-2 focus:ring-red-500 outline-none transition-all">
          </div>
          <div class="mb-5">
            <label class="block text-gray-700 text-sm font-semibold mb-2">Género <span class="text-red-500">*</span></label>
            <div class="grid grid-cols-2 gap-3">
              <button
                type="button"
                @click="nuevoUsuario.genero = 'masculino'"
                class="py-3 rounded-xl border-2 font-bold text-sm transition-all"
                :class="nuevoUsuario.genero === 'masculino'
                  ? 'border-gray-800 bg-gray-800 text-white'
                  : 'border-gray-200 text-gray-500 hover:border-gray-400 hover:text-gray-700'"
              >
                Masculino
              </button>
              <button
                type="button"
                @click="nuevoUsuario.genero = 'femenino'"
                class="py-3 rounded-xl border-2 font-bold text-sm transition-all"
                :class="nuevoUsuario.genero === 'femenino'
                  ? 'border-gray-800 bg-gray-800 text-white'
                  : 'border-gray-200 text-gray-500 hover:border-gray-400 hover:text-gray-700'"
              >
                Femenino
              </button>
            </div>
          </div>
          <div class="mb-5">
            <label class="block text-gray-700 text-sm font-semibold mb-2">Fecha de nacimiento <span class="text-gray-400 font-normal">(opcional)</span></label>
            <input v-model="nuevoUsuario.fecha_nacimiento" type="date"
              class="w-full px-4 py-3 rounded-lg border border-gray-300 focus:ring-2 focus:ring-red-500 outline-none transition-all">
          </div>
          <div class="mb-5">
            <label class="block text-gray-700 text-sm font-semibold mb-2">EPS <span class="text-gray-400 font-normal">(opcional)</span></label>
            <input v-model="nuevoUsuario.eps" type="text" maxlength="100" class="w-full px-4 py-3 rounded-lg border border-gray-300 focus:ring-2 focus:ring-red-500 outline-none transition-all">
          </div>
          <div class="mb-5">
            <label class="block text-gray-700 text-sm font-semibold mb-2">Barrio <span class="text-gray-400 font-normal">(opcional)</span></label>
            <input v-model="nuevoUsuario.barrio" type="text" maxlength="100" class="w-full px-4 py-3 rounded-lg border border-gray-300 focus:ring-2 focus:ring-red-500 outline-none transition-all">
          </div>
          <div class="mb-5 grid grid-cols-2 gap-3">
            <div>
              <label class="block text-gray-700 text-sm font-semibold mb-2">Emergencia: nombre <span class="text-red-500">*</span></label>
              <input v-model="nuevoUsuario.contacto_emergencia_nombre" type="text" required minlength="2" maxlength="120" class="w-full px-4 py-3 rounded-lg border border-gray-300 focus:ring-2 focus:ring-red-500 outline-none transition-all" placeholder="Nombre">
            </div>
            <div>
              <label class="block text-gray-700 text-sm font-semibold mb-2">Emergencia: teléfono <span class="text-red-500">*</span></label>
              <input v-model="nuevoUsuario.contacto_emergencia_telefono" type="tel" required minlength="7" maxlength="20" class="w-full px-4 py-3 rounded-lg border border-gray-300 focus:ring-2 focus:ring-red-500 outline-none transition-all" placeholder="Teléfono">
            </div>
          </div>
          <div class="mb-5 border border-gray-200 rounded-xl p-4">
            <label class="flex items-center gap-2.5 cursor-pointer">
              <input type="checkbox" v-model="nuevoUsuario.es_menor" class="w-4 h-4 accent-red-600 rounded">
              <span class="text-sm font-semibold text-gray-700">Es menor de edad</span>
            </label>
            <div v-if="nuevoUsuario.es_menor" class="grid grid-cols-2 gap-3 mt-3">
              <div class="col-span-2">
                <label class="block text-gray-600 text-xs font-semibold mb-1">Acudiente: nombre <span class="text-red-500">*</span></label>
                <input v-model="nuevoUsuario.acudiente_nombre" type="text" maxlength="120" required class="w-full px-3 py-2 rounded-lg border border-gray-300 focus:ring-2 focus:ring-red-500 outline-none text-sm" placeholder="Nombre">
              </div>
              <div>
                <label class="block text-gray-600 text-xs font-semibold mb-1">Acudiente: cédula <span class="text-red-500">*</span></label>
                <input v-model="nuevoUsuario.acudiente_documento" type="text" maxlength="20" required class="w-full px-3 py-2 rounded-lg border border-gray-300 focus:ring-2 focus:ring-red-500 outline-none text-sm" placeholder="Cédula">
              </div>
              <div>
                <label class="block text-gray-600 text-xs font-semibold mb-1">Acudiente: teléfono <span class="text-red-500">*</span></label>
                <input v-model="nuevoUsuario.acudiente_telefono" type="tel" maxlength="20" required class="w-full px-3 py-2 rounded-lg border border-gray-300 focus:ring-2 focus:ring-red-500 outline-none text-sm" placeholder="Teléfono">
              </div>
            </div>
          </div>
          <!-- Sin selector de rol: lo define desde dónde se abrió el modal (Clientes →
               cliente, Equipo → coach). El admin es único y lo siembra seed.py; el
               backend rechaza con 403 cualquier intento de crear otro. -->

          <!-- Plan inicial — al staff no le aplica membresía -->
          <div v-if="!creandoStaff" class="border-t border-gray-100 pt-5 mb-6">
            <MembresiaSelector v-model="planInicial" :planes="planes" acento="red"
              titulo="Plan de Membresía (opcional)" permitir-ninguno />
          </div>

          <div class="flex justify-end gap-3 pt-4 border-t border-gray-100">
            <button @click="cerrarFormulario" type="button" class="px-5 py-2.5 rounded-lg text-gray-600 font-semibold hover:bg-gray-100 transition-colors">Cancelar</button>
            <button type="submit" :disabled="saving || !nuevoUsuario.genero" class="px-5 py-2.5 rounded-lg bg-red-600 hover:bg-red-700 text-white font-semibold shadow-md inline-flex items-center gap-2 transition-all active:scale-95 disabled:bg-red-300">
              <span v-if="saving" class="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></span>
              {{ saving ? 'Guardando...' : (creandoStaff ? 'Crear miembro' : 'Crear Cliente') }}
            </button>
          </div>
        </form>
      </div>
    </div>
  </div>

  <!-- ── Modal: Buscar por Huella ── -->
  <div v-if="showVerifyModal" class="fixed inset-0 flex items-center justify-center bg-gray-900/70 backdrop-blur-sm z-50 p-4">
    <div class="bg-white rounded-2xl w-full max-w-sm shadow-2xl overflow-hidden">
      <div class="bg-gradient-to-r from-gray-700 to-gray-800 px-6 py-5 flex items-center gap-3">
        <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6 text-white flex-shrink-0" viewBox="0 0 20 20" fill="currentColor">
          <path fill-rule="evenodd" d="M6.625 2.655A9 9 0 0119 11a1 1 0 11-2 0 7 7 0 00-9.625-6.492 1 1 0 11-.75-1.853zM4.662 4.959A1 1 0 014.75 6.37 6.97 6.97 0 003 11a1 1 0 11-2 0 8.97 8.97 0 012.25-5.953 1 1 0 011.412-.088z" clip-rule="evenodd"/>
          <path fill-rule="evenodd" d="M5 11a5 5 0 1110 0 1 1 0 11-2 0 3 3 0 10-6 0c0 1.677-.345 3.276-.968 4.729a1 1 0 11-1.838-.789A9.964 9.964 0 005 11z" clip-rule="evenodd"/>
        </svg>
        <h3 class="text-lg font-bold text-white">Buscar por Huella</h3>
        <button v-if="!verifyStatus?.espera" @click="cerrarVerify" class="ml-auto text-white/70 hover:text-white">
          <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/></svg>
        </button>
      </div>

      <div class="px-6 py-6 text-center">
        <!-- Encontrado -->
        <div v-if="verifyStatus?.encontrado && verifyStatus?.usuario" class="flex flex-col items-center gap-3">
          <div class="w-16 h-16 bg-emerald-100 rounded-full flex items-center justify-center">
            <svg xmlns="http://www.w3.org/2000/svg" class="h-8 w-8 text-emerald-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"/>
            </svg>
          </div>
          <p class="text-emerald-700 font-bold text-lg">Persona identificada</p>
          <div class="w-full bg-emerald-50 border border-emerald-200 rounded-xl p-4 text-left">
            <p class="text-xs text-gray-400 uppercase font-semibold mb-1">Nombre</p>
            <p class="font-bold text-gray-800 text-lg">{{ verifyStatus.usuario.nombre }}</p>
          </div>
          <div class="flex gap-3 w-full mt-1">
            <button @click="cerrarVerify" class="flex-1 py-2.5 rounded-xl border border-gray-200 text-gray-600 font-semibold hover:bg-gray-50 transition-colors">Cerrar</button>
            <button @click="irAlPerfil(verifyStatus.usuario.id)" class="flex-1 py-2.5 rounded-xl bg-gray-700 hover:bg-gray-800 text-white font-bold transition-colors">Ver perfil</button>
          </div>
        </div>

        <!-- No encontrado -->
        <div v-else-if="verifyStatus?.no_match" class="flex flex-col items-center gap-3">
          <div class="w-16 h-16 bg-amber-100 rounded-full flex items-center justify-center">
            <svg xmlns="http://www.w3.org/2000/svg" class="h-8 w-8 text-amber-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8.228 9c.549-1.165 2.03-2 3.772-2 2.21 0 4 1.343 4 3 0 1.4-1.278 2.575-3.006 2.907-.542.104-.994.54-.994 1.093m0 3h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"/>
            </svg>
          </div>
          <p class="text-amber-700 font-bold text-lg">Huella no reconocida</p>
          <p class="text-gray-400 text-sm">No hay nadie registrado con esta huella.</p>
          <div class="flex gap-3 w-full mt-1">
            <button @click="cerrarVerify" class="flex-1 py-2.5 rounded-xl border border-gray-200 text-gray-600 font-semibold hover:bg-gray-50">Cerrar</button>
            <button @click="reiniciarVerify" class="flex-1 py-2.5 rounded-xl bg-gray-700 hover:bg-gray-800 text-white font-bold transition-colors">Reintentar</button>
          </div>
        </div>

        <!-- Error -->
        <div v-else-if="verifyStatus?.error" class="flex flex-col items-center gap-3">
          <div class="w-16 h-16 bg-red-100 rounded-full flex items-center justify-center">
            <svg xmlns="http://www.w3.org/2000/svg" class="h-8 w-8 text-red-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"/>
            </svg>
          </div>
          <p class="text-red-600 font-bold">Error</p>
          <p class="text-gray-500 text-sm">{{ verifyStatus.mensaje }}</p>
          <div class="flex gap-3 w-full mt-1">
            <button @click="cerrarVerify" class="flex-1 py-2.5 rounded-xl border border-gray-200 text-gray-600 font-semibold hover:bg-gray-50">Cerrar</button>
            <button @click="reiniciarVerify" class="flex-1 py-2.5 rounded-xl bg-gray-700 hover:bg-gray-800 text-white font-bold transition-colors">Reintentar</button>
          </div>
        </div>

        <!-- Esperando dedo -->
        <div v-else class="flex flex-col items-center gap-4">
          <div v-if="verifyBridgeError" class="w-full p-3 bg-amber-50 border border-amber-200 rounded-xl text-amber-700 text-sm">
            <p class="font-semibold">Bridge no disponible</p>
            <p class="mt-1">Asegúrate de que el bridge esté corriendo:<br>
              <code class="text-xs bg-amber-100 px-1 rounded">dotnet run --project servicio_biometrico/HuelleroBridge.csproj</code>
            </p>
          </div>
          <template v-else>
            <div class="relative w-20 h-20">
              <div class="absolute inset-0 rounded-full bg-gray-200 animate-ping opacity-40"></div>
              <div class="relative w-20 h-20 bg-gray-100 rounded-full flex items-center justify-center border-2 border-gray-400">
                <svg xmlns="http://www.w3.org/2000/svg" class="h-10 w-10 text-gray-700" viewBox="0 0 20 20" fill="currentColor">
                  <path fill-rule="evenodd" d="M6.625 2.655A9 9 0 0119 11a1 1 0 11-2 0 7 7 0 00-9.625-6.492 1 1 0 11-.75-1.853zM4.662 4.959A1 1 0 014.75 6.37 6.97 6.97 0 003 11a1 1 0 11-2 0 8.97 8.97 0 012.25-5.953 1 1 0 011.412-.088z" clip-rule="evenodd"/>
                  <path fill-rule="evenodd" d="M5 11a5 5 0 1110 0 1 1 0 11-2 0 3 3 0 10-6 0c0 1.677-.345 3.276-.968 4.729a1 1 0 11-1.838-.789A9.964 9.964 0 005 11z" clip-rule="evenodd"/>
                </svg>
              </div>
            </div>
            <p class="text-gray-700 font-semibold">Coloca el dedo en el lector</p>
            <p class="text-gray-400 text-sm">{{ verifyStatus?.mensaje || 'Cargando templates...' }}</p>
            <button @click="cerrarVerify" class="text-sm text-red-500 hover:text-red-700 font-medium">Cancelar</button>
          </template>
        </div>
      </div>
    </div>
  </div>

  <!-- ── Modal: Enrolamiento de Huella ── -->
  <div v-if="showEnrolModal" class="fixed inset-0 flex items-center justify-center bg-gray-900/70 backdrop-blur-sm z-50 p-4">
    <div class="bg-white rounded-2xl w-full max-w-sm shadow-2xl overflow-hidden">
      <div class="bg-gradient-to-r from-red-600 to-red-700 px-6 py-5 flex items-center gap-3">
        <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6 text-white flex-shrink-0" viewBox="0 0 20 20" fill="currentColor">
          <path fill-rule="evenodd" d="M6.625 2.655A9 9 0 0119 11a1 1 0 11-2 0 7 7 0 00-9.625-6.492 1 1 0 11-.75-1.853zM4.662 4.959A1 1 0 014.75 6.37 6.97 6.97 0 003 11a1 1 0 11-2 0 8.97 8.97 0 012.25-5.953 1 1 0 011.412-.088z" clip-rule="evenodd"/>
          <path fill-rule="evenodd" d="M5 11a5 5 0 1110 0 1 1 0 11-2 0 3 3 0 10-6 0c0 1.677-.345 3.276-.968 4.729a1 1 0 11-1.838-.789A9.964 9.964 0 005 11z" clip-rule="evenodd"/>
        </svg>
        <div>
          <h3 class="text-lg font-bold text-white">Registrar Huella</h3>
          <p class="text-red-200 text-sm">{{ enrolTarget?.nombre }}</p>
        </div>
        <button v-if="!enrolStatus?.activo" @click="cerrarEnrolModal" class="ml-auto text-white/70 hover:text-white">
          <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/></svg>
        </button>
      </div>

      <div class="px-6 py-6 text-center">
        <!-- Completado -->
        <div v-if="enrolStatus?.completado" class="flex flex-col items-center gap-3">
          <div class="w-16 h-16 bg-emerald-100 rounded-full flex items-center justify-center">
            <svg xmlns="http://www.w3.org/2000/svg" class="h-8 w-8 text-emerald-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"/>
            </svg>
          </div>
          <p class="text-emerald-700 font-bold text-lg">Huella registrada</p>
          <p class="text-gray-500 text-sm">{{ enrolStatus.mensaje }}</p>
          <button @click="cerrarEnrolModal" class="mt-2 w-full py-2.5 rounded-xl bg-emerald-500 hover:bg-emerald-600 text-white font-bold transition-colors">Cerrar</button>
        </div>

        <!-- Error -->
        <div v-else-if="enrolStatus?.error" class="flex flex-col items-center gap-3">
          <div class="w-16 h-16 bg-red-100 rounded-full flex items-center justify-center">
            <svg xmlns="http://www.w3.org/2000/svg" class="h-8 w-8 text-red-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/>
            </svg>
          </div>
          <p class="text-red-600 font-bold">Error en el enrolamiento</p>
          <p class="text-gray-500 text-sm">{{ enrolStatus.error }}</p>
          <div class="flex gap-3 w-full mt-2">
            <button @click="cerrarEnrolModal" class="flex-1 py-2.5 rounded-xl border border-gray-200 text-gray-600 font-semibold hover:bg-gray-50 transition-colors">Cancelar</button>
            <button @click="iniciarEnrolamiento" class="flex-1 py-2.5 rounded-xl bg-red-600 hover:bg-red-700 text-white font-bold transition-colors">Reintentar</button>
          </div>
        </div>

        <!-- En progreso -->
        <div v-else-if="enrolStatus?.activo" class="flex flex-col items-center gap-4">
          <!-- Icono huella animado -->
          <div class="relative w-20 h-20">
            <div class="absolute inset-0 rounded-full bg-red-100 animate-ping opacity-40"></div>
            <div class="relative w-20 h-20 bg-red-50 rounded-full flex items-center justify-center border-2 border-red-300">
              <svg xmlns="http://www.w3.org/2000/svg" class="h-10 w-10 text-red-600" viewBox="0 0 20 20" fill="currentColor">
                <path fill-rule="evenodd" d="M6.625 2.655A9 9 0 0119 11a1 1 0 11-2 0 7 7 0 00-9.625-6.492 1 1 0 11-.75-1.853zM4.662 4.959A1 1 0 014.75 6.37 6.97 6.97 0 003 11a1 1 0 11-2 0 8.97 8.97 0 012.25-5.953 1 1 0 011.412-.088z" clip-rule="evenodd"/>
                <path fill-rule="evenodd" d="M5 11a5 5 0 1110 0 1 1 0 11-2 0 3 3 0 10-6 0c0 1.677-.345 3.276-.968 4.729a1 1 0 11-1.838-.789A9.964 9.964 0 005 11z" clip-rule="evenodd"/>
              </svg>
            </div>
          </div>

          <!-- Progreso pasos -->
          <div class="flex gap-2">
            <div v-for="i in enrolStatus.total" :key="i"
              class="w-8 h-8 rounded-full flex items-center justify-center text-xs font-bold transition-all"
              :class="i < enrolStatus.paso ? 'bg-emerald-500 text-white' :
                      i === enrolStatus.paso ? 'bg-red-600 text-white ring-4 ring-red-200' :
                      'bg-gray-100 text-gray-400'">
              {{ i < enrolStatus.paso ? '✓' : i }}
            </div>
          </div>

          <p class="text-gray-700 font-semibold">{{ enrolStatus.mensaje }}</p>
          <p class="text-gray-400 text-sm">Captura {{ enrolStatus.paso }} de {{ enrolStatus.total }}</p>

          <button @click="cancelarEnrolamiento" class="mt-1 text-sm text-red-500 hover:text-red-700 font-medium">Cancelar</button>
        </div>

        <!-- Inicio / bridge desconectado -->
        <div v-else class="flex flex-col items-center gap-4">
          <div v-if="enrolBridgeError" class="w-full p-3 bg-amber-50 border border-amber-200 rounded-xl text-amber-700 text-sm">
            <p class="font-semibold">Bridge no disponible</p>
            <p class="mt-1">Asegúrate de que el bridge esté corriendo:<br>
              <code class="text-xs bg-amber-100 px-1 rounded">dotnet run --project servicio_biometrico/HuelleroBridge.csproj</code>
            </p>
          </div>
          <div v-else>
            <p class="text-gray-500 text-sm mb-4">Se capturarán <strong>{{ ENROL_STEPS }} muestras</strong> del dedo de la persona.<br>Asegúrate de que el lector esté conectado.</p>
            <button @click="iniciarEnrolamiento" class="w-full py-3 rounded-xl bg-red-600 hover:bg-red-700 text-white font-bold text-lg transition-colors flex items-center justify-center gap-2">
              <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
                <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-8.707l-3-3a1 1 0 00-1.414 1.414L10.586 9H7a1 1 0 100 2h3.586l-1.293 1.293a1 1 0 101.414 1.414l3-3a1 1 0 000-1.414z" clip-rule="evenodd"/>
              </svg>
              Iniciar captura
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted, onUnmounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import api, { mediaUrl } from '../api'
import { fotoSrc } from '../lib/avatar'
import { BADGE_NEUTRO } from '../data/paleta'
import { useAuth } from '../composables/useAuth'
import { nuevoFormulario, payloadActivacion, payloadPago } from '../lib/membresia'
import PendienteDetalle from '../components/PendienteDetalle.vue'
import MembresiaSelector from '../components/MembresiaSelector.vue'

const route  = useRoute()
const router = useRouter()
const { isAdmin } = useAuth()

// Id propio: se usa para no ofrecer el botón de eliminar en la fila propia.
// No está en localStorage, así que se pide a /me (una vez, al montar).
const miId = ref(null)
const BRIDGE_URL = 'http://localhost:8001'
const ENROL_STEPS = 4

// ── En gym ───────────────────────────────────────────────────
const enGym = ref([])
let gymInterval = null

const fetchEnGym = async () => {
  try { enGym.value = (await api.get('/asistencia/en-gym')).data } catch {}
}

// ── Estado ──────────────────────────────────────────────────
const usuarios = ref([])
const pendientes = ref([])
const planes = ref([])
const loading = ref(true)
const loadingPendientes = ref(false)
const usuarioSeleccionado = ref(null)
const filtroActivo = ref('todos')
const busqueda = ref('')


// ── Verificación por huella ──────────────────────────────────
const showVerifyModal  = ref(false)
const verifyStatus     = ref(null)
const verifyBridgeError = ref(false)
let   verifyPollInterval = null

const abrirBuscarHuella = async () => {
  verifyStatus.value     = null
  verifyBridgeError.value = false
  showVerifyModal.value  = true
  try {
    await fetch(`${BRIDGE_URL}/verify/start`, { method: 'POST' })
    _iniciarPollVerify()
  } catch {
    verifyBridgeError.value = true
  }
}

const cerrarVerify = async () => {
  clearInterval(verifyPollInterval)
  verifyPollInterval = null
  try { await fetch(`${BRIDGE_URL}/verify`, { method: 'DELETE' }) } catch {}
  showVerifyModal.value = false
  verifyStatus.value    = null
}

const reiniciarVerify = async () => {
  clearInterval(verifyPollInterval)
  verifyStatus.value = null
  try {
    await fetch(`${BRIDGE_URL}/verify/start`, { method: 'POST' })
    _iniciarPollVerify()
  } catch {
    verifyBridgeError.value = true
  }
}

const irAlPerfil = (id) => {
  cerrarVerify()
  router.push(`/usuarios/${id}`)
}

const _pollVerify = async () => {
  try {
    const r    = await fetch(`${BRIDGE_URL}/status`)
    const data = await r.json()
    const v    = data.verificacion
    verifyStatus.value = v
    if (v.encontrado || v.no_match || v.error) {
      clearInterval(verifyPollInterval)
      verifyPollInterval = null
    }
  } catch {
    verifyBridgeError.value = true
    clearInterval(verifyPollInterval)
    verifyPollInterval = null
  }
}

const _iniciarPollVerify = () => {
  clearInterval(verifyPollInterval)
  _pollVerify()
  verifyPollInterval = setInterval(_pollVerify, 600)
}

// ── Enrolamiento de huella ────────────────────────────────────
const showEnrolModal = ref(false)
const enrolTarget = ref(null)
const enrolStatus = ref(null)
const enrolBridgeError = ref(false)
let enrolPollInterval = null

const abrirEnrolamiento = (usuario) => {
  enrolTarget.value = usuario
  enrolStatus.value = null
  enrolBridgeError.value = false
  showEnrolModal.value = true
  usuarioSeleccionado.value = null
}

const cerrarEnrolModal = () => {
  clearInterval(enrolPollInterval)
  enrolPollInterval = null
  showEnrolModal.value = false
  enrolTarget.value = null
  enrolStatus.value = null
  fetchUsuarios()
}

const iniciarEnrolamiento = async () => {
  if (!enrolTarget.value) return
  enrolBridgeError.value = false
  try {
    const nombre = encodeURIComponent(enrolTarget.value.nombre)
    await fetch(`${BRIDGE_URL}/enroll/${enrolTarget.value.id}?nombre=${nombre}`, { method: 'POST' })
    _iniciarPollEnrol()
  } catch {
    enrolBridgeError.value = true
  }
}

const cancelarEnrolamiento = async () => {
  try { await fetch(`${BRIDGE_URL}/enroll`, { method: 'DELETE' }) } catch {}
  clearInterval(enrolPollInterval)
  enrolPollInterval = null
  enrolStatus.value = null
}

const _pollStatus = async () => {
  try {
    const r = await fetch(`${BRIDGE_URL}/status`)
    const data = await r.json()
    const e = data.enrolamiento
    enrolStatus.value = e
    if (e.completado || (e.error && !e.activo)) {
      clearInterval(enrolPollInterval)
      enrolPollInterval = null
    }
  } catch {
    enrolBridgeError.value = true
    clearInterval(enrolPollInterval)
    enrolPollInterval = null
  }
}

const _iniciarPollEnrol = () => {
  clearInterval(enrolPollInterval)
  _pollStatus()
  enrolPollInterval = setInterval(_pollStatus, 600)
}

// ── Filtros ──────────────────────────────────────────────────
const hoy = () => { const d = new Date(); d.setHours(0,0,0,0); return d }

const tieneMembresia = (u) => {
  if (!u.fecha_vencimiento) return false
  return new Date(u.fecha_vencimiento + 'T00:00:00') >= hoy()
}

// ── Orden ────────────────────────────────────────────────────
// Los sin fecha van siempre al final, ordene como ordene: "sin membresía" no es
// ni lo más próximo a vencer ni lo más lejano.
const _sinFechaAlFinal = (campo, cmp) => (a, b) => {
  if (!a[campo] && !b[campo]) return 0
  if (!a[campo]) return 1
  if (!b[campo]) return -1
  return cmp(a[campo], b[campo])
}
const _porNombre = (a, b) => a.nombre.localeCompare(b.nombre, 'es', { sensitivity: 'base' })

const ORDENES = [
  { key: 'nombre',        label: 'Nombre (A–Z)',      cmp: _porNombre },
  { key: 'nombre_desc',   label: 'Nombre (Z–A)',      cmp: (a, b) => _porNombre(b, a) },
  { key: 'vence_pronto',  label: 'Vence primero',     cmp: _sinFechaAlFinal('fecha_vencimiento', (x, y) => x.localeCompare(y)) },
  { key: 'vence_tarde',   label: 'Vence último',      cmp: _sinFechaAlFinal('fecha_vencimiento', (x, y) => y.localeCompare(x)) },
  { key: 'reciente',      label: 'Registro reciente', cmp: _sinFechaAlFinal('created_at', (x, y) => y.localeCompare(x)) },
  { key: 'antiguo',       label: 'Registro antiguo',  cmp: _sinFechaAlFinal('created_at', (x, y) => x.localeCompare(y)) },
]
const orden = ref('nombre')

// ── Vista: clientes vs. equipo del box ───────────────────────
// Son dos poblaciones con datos distintos: al staff no le aplican membresía ni
// "en el box" (el backend no exime al staff en _validar_membresia), así que cada
// listado lleva sus propias columnas.
const vista = ref('clientes')
const clientes = computed(() => usuarios.value.filter(u => u.rol === 'cliente'))
// Espeja los guards del backend (usuarios.py eliminar_usuario): staff solo lo
// borra un admin, y nadie se borra a sí mismo.
const puedeEliminarStaff = (u) => isAdmin.value && u.id !== miId.value

const equipo = computed(() =>
  usuarios.value
    .filter(u => u.rol === 'admin' || u.rol === 'coach')
    // admin primero, después coaches por nombre
    .sort((a, b) => (a.rol === b.rol
      ? a.nombre.localeCompare(b.nombre, 'es', { sensitivity: 'base' })
      : a.rol === 'admin' ? -1 : 1))
)

const usuariosFiltrados = computed(() => {
  let lista = clientes.value
  // "Activo" = membresía vigente. El que está físicamente en el box es 'en_box'.
  if (filtroActivo.value === 'activos')   lista = lista.filter(tieneMembresia)
  if (filtroActivo.value === 'inactivos') lista = lista.filter(u => !tieneMembresia(u))
  if (filtroActivo.value === 'en_box')    lista = lista.filter(u => u.esta_en_gym)
  const q = busqueda.value.trim().toLowerCase()
  if (q) lista = lista.filter(u =>
    u.nombre.toLowerCase().includes(q) ||
    u.documento_identidad?.toLowerCase().includes(q)
  )
  // slice(): sort muta el array, y sin filtros `lista` ES usuarios.value.
  const cmp = ORDENES.find(o => o.key === orden.value)?.cmp || _porNombre
  return lista.slice().sort(cmp)
})

// Los pendientes se buscan por los mismos campos que los clientes, pero el orden es
// fijo (el más reciente primero) y por eso el selector "Ordenar por" no se muestra acá.
const pendientesFiltrados = computed(() => {
  const q = busqueda.value.trim().toLowerCase()
  const lista = q
    ? pendientes.value.filter(p =>
        p.nombre.toLowerCase().includes(q) ||
        p.documento_identidad?.toLowerCase().includes(q)
      )
    : pendientes.value
  return lista.slice().sort((a, b) => new Date(b.created_at) - new Date(a.created_at))
})

// ── Paginación (en cliente: la lista completa ya viene de GET /usuarios/) ──
// Una sola paginación para las dos listas de la vista Clientes: solo una se
// renderiza a la vez, y el watch de `filtroActivo` resetea la página al alternar.
const POR_PAGINA = 15
const pagina = ref(1)

const listaFiltrada = computed(() =>
  filtroActivo.value === 'pendientes' ? pendientesFiltrados.value : usuariosFiltrados.value
)

const totalPaginas = computed(() => Math.max(1, Math.ceil(listaFiltrada.value.length / POR_PAGINA)))
const rangoDesde   = computed(() => (pagina.value - 1) * POR_PAGINA + 1)
const rangoHasta   = computed(() => Math.min(pagina.value * POR_PAGINA, listaFiltrada.value.length))
const paginaItems  = computed(() => listaFiltrada.value.slice(rangoDesde.value - 1, rangoHasta.value))

function irAPagina(p) {
  pagina.value = Math.min(Math.max(1, p), totalPaginas.value)
  window.scrollTo({ top: 0, behavior: 'smooth' })
}

// Al filtrar o buscar, la página actual puede quedar fuera de rango (o mostrando
// resultados salteados): se vuelve a la primera.
watch([filtroActivo, busqueda, orden], () => { pagina.value = 1 })
// Si la lista se achica por otra vía (eliminar un usuario), se reencuadra.
watch(totalPaginas, (n) => { if (pagina.value > n) pagina.value = n })

/** Números a mostrar, con elipsis: 1 … 4 [5] 6 … 12 */
const paginasVisibles = computed(() => {
  const total = totalPaginas.value
  const act = pagina.value
  if (total <= 7) return Array.from({ length: total }, (_, i) => i + 1)

  const paginas = [1]
  if (act > 3) paginas.push('…')
  for (let p = Math.max(2, act - 1); p <= Math.min(total - 1, act + 1); p++) paginas.push(p)
  if (act < total - 2) paginas.push('…')
  paginas.push(total)
  return paginas
})

const tabs = computed(() => [
  { key: 'todos',      label: 'Todos',           count: clientes.value.length,                                emptyMsg: 'No hay clientes registrados.' },
  { key: 'activos',    label: 'Activos',         count: clientes.value.filter(tieneMembresia).length,         emptyMsg: 'Ningún cliente tiene membresía vigente.' },
  { key: 'inactivos',  label: 'Inactivos',       count: clientes.value.filter(u => !tieneMembresia(u)).length, emptyMsg: 'Todos los clientes tienen membresía vigente.' },
  { key: 'en_box',     label: 'En el box ahora', count: clientes.value.filter(u => u.esta_en_gym).length,     emptyMsg: 'No hay clientes en el box en este momento.' },
  { key: 'pendientes', label: 'Pendientes',      count: pendientes.value.length,                              emptyMsg: 'No hay clientes pendientes.' },
])

// ── Crear ────────────────────────────────────────────────────
const showForm = ref(false)
const saving = ref(false)
const NUEVO_USUARIO_VACIO = () => ({
  nombre: '', documento_identidad: '', email: '', password: '', rol: 'cliente', telefono: '', genero: '', fecha_nacimiento: '',
  eps: '', barrio: '', contacto_emergencia_nombre: '', contacto_emergencia_telefono: '',
  es_menor: false, acudiente_nombre: '', acudiente_telefono: '', acudiente_documento: '',
})
const nuevoUsuario = ref(NUEVO_USUARIO_VACIO())
// El modal es el mismo para cliente y staff; cambia el rol precargado, las opciones
// del select y si se muestra el bloque de plan (al staff no le aplica).
const creandoStaff = ref(false)
const planInicial = ref(nuevoFormulario('ninguno'))

function abrirFormulario(staff = false) {
  creandoStaff.value = staff
  nuevoUsuario.value = { ...NUEVO_USUARIO_VACIO(), rol: staff ? 'coach' : 'cliente' }
  planInicial.value = nuevoFormulario('ninguno')
  showForm.value = true
}
const fotoArchivo = ref(null)
const fotoPreview = ref(null)

// ── Editar ───────────────────────────────────────────────────
const showEditar = ref(false)
const guardandoEdicion = ref(false)
const editando = ref(null)
const editForm = ref({ email: '', password: '', telefono: '', genero: '' })
const editFotoArchivo = ref(null)
const editFotoPreview = ref(null)

// ── Activar pendiente ─────────────────────────────────────────
const showActivar = ref(false)
const activarUsuario = ref(null)
const activarForm = ref(nuevoFormulario())
const guardandoActivar = ref(false)
const errorActivar = ref('')

const abrirActivar = (u) => {
  activarUsuario.value = u
  // Precarga el plan que el cliente pidió al registrarse, con su precio de sugerencia.
  activarForm.value = nuevoFormulario(u.plan_solicitado_id || null)
  activarForm.value.monto = u.plan_solicitado?.precio || null
  errorActivar.value = ''
  showActivar.value = true
}

const confirmarActivar = async () => {
  if (!activarForm.value.plan) return
  guardandoActivar.value = true
  errorActivar.value = ''
  try {
    await api.post(
      `/usuarios/${activarUsuario.value.id}/activar`,
      payloadActivacion(activarForm.value, planes.value),
    )
    showActivar.value = false
    await fetchPendientes()
    await fetchUsuarios()
  } catch (e) {
    errorActivar.value = e.response?.data?.detail || 'Error al activar el cliente.'
  } finally {
    guardandoActivar.value = false
  }
}

// ── Renovar ──────────────────────────────────────────────────
const showRenovar = ref(false)
const guardandoRenovar = ref(false)
const renovarUsuario = ref(null)
const renovarForm = ref(nuevoFormulario())
const errorRenovar = ref('')

// ── Helpers ──────────────────────────────────────────────────

const formatFecha = (f) =>
  new Date(f + 'T12:00:00').toLocaleDateString('es-CO', { year: 'numeric', month: 'short', day: 'numeric' })

const formatFechaCorta = (f) =>
  new Date(f).toLocaleDateString('es-CO', { year: 'numeric', month: 'short', day: 'numeric' })

/** Días transcurridos desde una fecha ISO (created_at viene en UTC con hora). */
const diasDesde = (f) => {
  if (!f) return null
  return Math.floor((Date.now() - new Date(f)) / (1000 * 60 * 60 * 24))
}

/** Antigüedad de un pendiente en texto: el que lleva semanas sin aparecer es el
 *  candidato a borrar, así que la fila lo dice en vez de hacer restar fechas. */
const antiguedadPendiente = (f) => {
  const d = diasDesde(f)
  if (d === null) return ''
  if (d <= 0) return 'hoy'
  if (d === 1) return 'ayer'
  return `hace ${d} días`
}

// Cuánto puede llevar un registro sin activarse antes de que la fila lo señale.
// Ámbar = aviso (a la semana), rojo = candidato a descartar (a los 15 días); es la
// misma escala neutro → ámbar → rojo que usa la columna Membresía.
const PENDIENTE_AVISO_DIAS = 7
const PENDIENTE_VIEJO_DIAS = 15

const colorAntiguedad = (f) => {
  const d = diasDesde(f) ?? 0
  if (d >= PENDIENTE_VIEJO_DIAS) return 'text-red-600 font-semibold'
  if (d >= PENDIENTE_AVISO_DIAS) return 'text-amber-600 font-semibold'
  return 'text-gray-400'
}

const diasRestantes = (fecha) => {
  const hoy = new Date()
  hoy.setHours(0, 0, 0, 0)
  const vence = new Date(fecha + 'T00:00:00')
  return Math.ceil((vence - hoy) / (1000 * 60 * 60 * 24))
}

const etiquetaDias = (dias) => {
  if (dias > 1) return `${dias} días restantes`
  if (dias === 1) return 'Vence mañana'
  if (dias === 0) return 'Vence hoy'
  return `Vencida hace ${Math.abs(dias)} día${Math.abs(dias) !== 1 ? 's' : ''}`
}

// El punto (o el círculo, en el modal) ya codifica el estado: colorear además el
// texto es doble codificación, y con 15 filas en pantalla la columna se lee como
// un tablero de alarmas. Solo la vencida conserva el rojo — es la única fila que
// amerita gritar, porque significa que esa persona no puede entrar.
// El umbral es el mismo que colorPuntoDias para que punto y texto nunca discrepen.
const colorTextoDias = (dias) => (dias > 0 ? 'text-gray-900' : 'text-red-600')

const colorPuntoDias = (dias) => {
  if (dias > 7) return 'bg-emerald-500'
  if (dias > 0) return 'bg-amber-500'
  return 'bg-red-500'
}

const bgCirculoDias = (dias) => {
  if (dias > 7) return 'bg-emerald-100'
  if (dias > 0) return 'bg-amber-100'
  return 'bg-red-100'
}

// ── Fetch ────────────────────────────────────────────────────
const fetchUsuarios = async () => {
  loading.value = true
  try { usuarios.value = (await api.get('/usuarios/')).data }
  catch (e) { console.error(e) }
  finally { loading.value = false }
}

const fetchPlanes = async () => {
  try { planes.value = (await api.get('/planes/')).data }
  catch (e) { console.error(e) }
}

// ── Exportar Excel ────────────────────────────────────────────
const exportando  = ref(false)
const showExportar = ref(false)
const expClientes = ref(true)
const expEquipo   = ref(false)

// Al abrir preselecciona el grupo que estás mirando: exportar desde Equipo y
// recibir solo clientes sería sorprendente.
const toggleExportar = () => {
  if (showExportar.value) { showExportar.value = false; return }
  expClientes.value = vista.value === 'clientes'
  expEquipo.value   = vista.value === 'equipo'
  showExportar.value = true
}

const exportarExcel = async () => {
  if (!expClientes.value && !expEquipo.value) return
  exportando.value = true
  try {
    const { data } = await api.get('/usuarios/exportar-excel', {
      params: { clientes: expClientes.value, equipo: expEquipo.value },
      responseType: 'blob',
    })
    const grupo = expClientes.value && expEquipo.value
      ? 'usuarios'
      : (expClientes.value ? 'clientes' : 'equipo')
    const url = URL.createObjectURL(data)
    const a = document.createElement('a')
    a.href = url
    a.download = `${grupo}_jainsportbox_${new Date().toISOString().slice(0, 10)}.xlsx`
    document.body.appendChild(a)
    a.click()
    a.remove()
    URL.revokeObjectURL(url)
    showExportar.value = false
  } catch (e) {
    alert('Error al exportar: ' + (e.response?.data?.detail || e.message))
  } finally {
    exportando.value = false
  }
}

// Fila/bloque desplegable con los datos de afiliación de un pendiente (por id de usuario)
const detalleAbierto = ref({})
const toggleDetalle = (id) => { detalleAbierto.value[id] = !detalleAbierto.value[id] }

// ── Selección múltiple de pendientes ─────────────────────────
// Un Set en un ref: la selección sobrevive al cambio de página y a la búsqueda,
// que es lo que se quiere al limpiar decenas de registros basura. Reasignar el Set
// (en vez de mutarlo) es lo que dispara la reactividad de Vue.
const seleccionados = ref(new Set())

const alternarSeleccion = (id) => {
  const s = new Set(seleccionados.value)
  s.has(id) ? s.delete(id) : s.add(id)
  seleccionados.value = s
}

const limpiarSeleccion = () => { seleccionados.value = new Set() }

const todosDePaginaSeleccionados = computed(() =>
  paginaItems.value.length > 0 && paginaItems.value.every(p => seleccionados.value.has(p.id))
)

const alternarSeleccionPagina = () => {
  const s = new Set(seleccionados.value)
  const marcar = !todosDePaginaSeleccionados.value
  paginaItems.value.forEach(p => (marcar ? s.add(p.id) : s.delete(p.id)))
  seleccionados.value = s
}

// El umbral es el mismo que pinta la antigüedad en rojo: lo que se ve en rojo es
// exactamente lo que preselecciona esta acción.
const pendientesViejos = computed(() =>
  pendientes.value.filter(p => (diasDesde(p.created_at) ?? 0) >= PENDIENTE_VIEJO_DIAS)
)
const hayViejos = computed(() => pendientesViejos.value.length > 0)

const seleccionarViejos = () => {
  seleccionados.value = new Set(pendientesViejos.value.map(p => p.id))
}

const fetchPendientes = async () => {
  loadingPendientes.value = true
  try { pendientes.value = (await api.get('/usuarios/pendientes')).data }
  catch (e) { console.error(e) }
  finally { loadingPendientes.value = false }
}

// ── Ver ──────────────────────────────────────────────────────
const verUsuario = (u) => { router.push(`/usuarios/${u.id}`) }

// ── Renovar ──────────────────────────────────────────────────
const abrirRenovar = (user) => {
  renovarUsuario.value = user
  renovarForm.value = nuevoFormulario()
  errorRenovar.value = ''
  showRenovar.value = true
}

const confirmarRenovacion = async () => {
  if (!renovarForm.value.plan) return
  if (renovarForm.value.plan === 'personalizado' && !(renovarForm.value.dias >= 1)) {
    errorRenovar.value = 'Ingresa un número de días válido.'
    return
  }
  guardandoRenovar.value = true
  errorRenovar.value = ''
  try {
    const { url, body } = payloadPago(renovarForm.value, planes.value, renovarUsuario.value.id)
    await api.post(url, body)
    showRenovar.value = false
    await fetchUsuarios()
  } catch (e) {
    errorRenovar.value = e.response?.data?.detail || 'Error al renovar la membresía.'
  } finally {
    guardandoRenovar.value = false
  }
}

// ── Crear ────────────────────────────────────────────────────
const cerrarFormulario = () => {
  showForm.value = false
  creandoStaff.value = false
  nuevoUsuario.value = NUEVO_USUARIO_VACIO()
  planInicial.value = nuevoFormulario('ninguno')
  fotoArchivo.value = null
  fotoPreview.value = null
}

const onFotoChange = (e) => {
  const f = e.target.files[0]
  if (!f) return
  fotoArchivo.value = f
  fotoPreview.value = URL.createObjectURL(f)
}

const quitarFoto = () => { fotoArchivo.value = null; fotoPreview.value = null }

const crearUsuario = async () => {
  saving.value = true
  try {
    const payload = { ...nuevoUsuario.value }
    if (!payload.fecha_nacimiento) payload.fecha_nacimiento = null
    // Campos opcionales: no mandar strings vacíos
    for (const k of ['eps', 'barrio', 'contacto_emergencia_nombre', 'contacto_emergencia_telefono', 'acudiente_nombre', 'acudiente_telefono', 'acudiente_documento']) {
      if (!payload[k]) payload[k] = null
    }
    if (!payload.es_menor) {
      payload.acudiente_nombre = null
      payload.acudiente_telefono = null
      payload.acudiente_documento = null
    }
    const { data: nuevo } = await api.post('/usuarios/', payload)

    if (fotoArchivo.value) {
      const fd = new FormData()
      fd.append('foto', fotoArchivo.value)
      await api.post(`/usuarios/${nuevo.id}/foto`, fd, { headers: { 'Content-Type': 'multipart/form-data' } })
    }

    if (planInicial.value.plan && planInicial.value.plan !== 'ninguno') {
      const { url, body } = payloadPago(planInicial.value, planes.value, nuevo.id)
      await api.post(url, body)
    }

    cerrarFormulario()
    await fetchUsuarios()
  } catch (e) {
    const d = e.response?.data?.detail
    alert('Error: ' + (Array.isArray(d) ? d[0].msg : (d || e.message)))
  } finally {
    saving.value = false
  }
}

// ── Eliminar ─────────────────────────────────────────────────
// Un modal en vez del confirm() nativo: la acción es irreversible y conviene ver a
// quién se está borrando (foto, email, documento) antes de confirmar.
const showEliminar    = ref(false)
const eliminando      = ref(null)
const eliminandoPendiente = ref(false)
const borrando        = ref(false)
const errorEliminar   = ref('')

/** @param esPendiente el payload de /usuarios/pendientes no trae `rol`, y tras
 *  borrar hay que refrescar esa lista y no la de usuarios. */
// El mismo modal cubre el borrado de a uno y el de la selección: cambian el
// encabezado y el cuerpo, no el flujo.
const eliminandoLote = ref([])

const confirmarEliminar = (user, esPendiente = false) => {
  eliminando.value = user
  eliminandoLote.value = []
  eliminandoPendiente.value = esPendiente
  errorEliminar.value = ''
  showEliminar.value = true
}

const confirmarEliminarSeleccion = () => {
  eliminando.value = null
  eliminandoLote.value = pendientes.value.filter(p => seleccionados.value.has(p.id))
  eliminandoPendiente.value = true
  errorEliminar.value = ''
  showEliminar.value = true
}

const ejecutarEliminar = async () => {
  const lote = eliminandoLote.value
  const user = eliminando.value
  if (!lote.length && !user) return
  borrando.value = true
  errorEliminar.value = ''
  try {
    if (lote.length) {
      await api.post('/usuarios/pendientes/eliminar', { ids: lote.map(p => p.id) })
      limpiarSeleccion()
    } else {
      await api.delete(`/usuarios/${user.id}`)
    }
    usuarioSeleccionado.value = null
    showEliminar.value = false
    eliminando.value = null
    eliminandoLote.value = []
    if (eliminandoPendiente.value) await fetchPendientes()
    else await fetchUsuarios()
  } catch (e) {
    const d = e.response?.data?.detail
    errorEliminar.value = Array.isArray(d) ? d[0].msg : (d || e.message)
  } finally {
    borrando.value = false
  }
}

const abrirEditar = (user) => {
  editando.value = user
  editForm.value = { email: user.email, password: '', telefono: user.telefono || '', genero: user.genero || '' }
  editFotoArchivo.value = null
  editFotoPreview.value = null
  showEditar.value = true
}

const cerrarEditar = () => {
  showEditar.value = false
  editando.value = null
  editFotoArchivo.value = null
  editFotoPreview.value = null
}

const onFotoEditChange = (e) => {
  const f = e.target.files[0]
  if (!f) return
  editFotoArchivo.value = f
  editFotoPreview.value = URL.createObjectURL(f)
}

const guardarEdicion = async () => {
  guardandoEdicion.value = true
  try {
    const id = editando.value.id
    const payload = { email: editForm.value.email, telefono: editForm.value.telefono || null }
    if (editForm.value.password) payload.password = editForm.value.password
    if (editForm.value.genero) payload.genero = editForm.value.genero
    await api.patch(`/usuarios/${id}`, payload)

    if (editFotoArchivo.value) {
      const fd = new FormData()
      fd.append('foto', editFotoArchivo.value)
      await api.post(`/usuarios/${id}/foto`, fd, { headers: { 'Content-Type': 'multipart/form-data' } })
    }

    cerrarEditar()
    await fetchUsuarios()
  } catch (e) {
    const d = e.response?.data?.detail
    alert('Error: ' + (Array.isArray(d) ? d[0].msg : (d || e.message)))
  } finally {
    guardandoEdicion.value = false
  }
}

// ── WebSocket: actualización en tiempo real del estado en gym ──
// El bridge .NET hace broadcast de eventos "acceso_ok" cada vez que registra
// una entrada/salida. Escuchamos ese socket y patcheamos solo el usuario
// afectado en la lista local — no recargamos toda la tabla.
let accesoWS = null
let accesoReconnectTimer = null

const aplicarEventoAcceso = (data) => {
  if (data?.tipo !== 'acceso_ok' || !data.usuario_id) return
  const u = usuarios.value.find(x => x.id === data.usuario_id)
  if (u) u.esta_en_gym = data.evento === 'entrada'
}

const conectarAccesoWS = () => {
  try {
    accesoWS = new WebSocket('ws://localhost:8765')
    accesoWS.onmessage = (ev) => {
      try { aplicarEventoAcceso(JSON.parse(ev.data)) } catch {}
    }
    accesoWS.onclose = () => {
      accesoWS = null
      // Reintento suave por si el bridge se reinicia.
      accesoReconnectTimer = setTimeout(conectarAccesoWS, 4000)
    }
    accesoWS.onerror = () => { try { accesoWS?.close() } catch {} }
  } catch {
    accesoReconnectTimer = setTimeout(conectarAccesoWS, 4000)
  }
}

onMounted(() => {
  // Deep-link de tab: el Resumen enlaza a /usuarios?tab=pendientes desde su tarjeta
  // de pendientes. Cualquier otro valor cae en el default 'todos'.
  if (tabs.value.some(t => t.key === route.query.tab)) filtroActivo.value = route.query.tab
  api.get('/me').then(({ data }) => { miId.value = data.id }).catch(() => {})
  fetchUsuarios()
  fetchPlanes()
  fetchPendientes()
  conectarAccesoWS()
  fetchEnGym()
  gymInterval = setInterval(fetchEnGym, 10_000)
})
onUnmounted(() => {
  clearInterval(enrolPollInterval)
  clearInterval(gymInterval)
  clearTimeout(accesoReconnectTimer)
  try { accesoWS?.close() } catch {}
})
</script>

<style>
.animate-fade-in-up {
  animation: fadeInUp 0.4s ease-out;
}
@keyframes fadeInUp {
  from { opacity: 0; transform: translateY(10px); }
  to   { opacity: 1; transform: translateY(0); }
}
</style>
