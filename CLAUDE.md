# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

JainSportBox is a CrossFit Box Management System with a Python/FastAPI backend and Vue.js 3 frontend. It handles members, memberships, attendance (via fingerprint sensor), WODs, finances, health metrics, personal records (1RM), and a product shop.

## Development Commands

### Launcher (recomendado)

Desde la raíz del repo:
```powershell
.\start-dev.ps1                # backend + frontend + bridge en ventanas separadas
.\start-dev.ps1 -NoBridge      # si el bridge ya corre via Task Scheduler
.\start-dev.ps1 -NoFrontend    # solo backend + bridge
```
O doble-clic a `start-dev.cmd`. El launcher activa el `venv/`, detecta si el bridge ya está corriendo (no relanza) y dispara UAC solo cuando hace falta. Ver logs del bridge en vivo: `servicio_biometrico\ver-logs.cmd`.

### Estación de recepción (producción, PC del gym)

`start-estacion.ps1` sirve el build de producción del frontend localmente apuntando al backend cloud (resuelve el bloqueo *mixed content* de la PWA). Ver Capa 6 en `DEPLOYMENT.md`.
```powershell
.\start-estacion.ps1 -ApiUrl https://api.tudominio.com   # build + vite preview en http://localhost:80 + bridge
.\start-estacion.ps1 -ApiUrl https://api.tudominio.com -Port 8080 -SkipBuild
```

### Backend
```bash
# From project root
cd backend
pip install -r requirements.txt          # or: pip install -r ../requirements.txt

# Create .env from template (required before first run)
cp .env.example .env

# Start backend (auto-creates DB tables and seeds admin on startup)
uvicorn main:app --reload --port 8000

# Or fromuvicorn backend.main:app --reload --port 8000 project root:

```

### Frontend
```bash
cd frontend
npm install
npm run dev      # Dev server at http://localhost:5173 (strictPort)
npm run build    # Production build → dist/
npm run preview  # Preview production build
```

### Tests
```bash
cd backend
..\venv\Scripts\python.exe -m pytest tests -q      # 184 tests de API (SQLite temporal, no toca crossfit.db)
```
La suite (`backend/tests/`) cubre todos los routers; el plan completo y los hallazgos están en `tests.md` (raíz). El `conftest.py` setea `TESTING=1` (desactiva APScheduler) y `DATABASE_URL` a un SQLite temporal ANTES de importar `main`. Al agregar endpoints o cambiar contratos, actualizar el test del dominio correspondiente.

## Architecture

**Three-process stack:**
- Backend: FastAPI on port 8000, SQLite database (`backend/crossfit.db`)
- Frontend: Vue 3 SPA on port 5173, talks to backend via Axios
- Bridge: `servicio_biometrico/` — .NET 4.8 Windows app for DigitalPersona U.are.U 4500 fingerprint reader

**Backend layout:**
- `backend/main.py` — FastAPI app creation, CORS config, router registration. Runs startup migrations (SQLite ALTER-TABLE block + Postgres `ADD COLUMN IF NOT EXISTS` block + cross-DB index block; ver "Migraciones de arranque"). Mounts `backend/uploads/` as `/uploads` for static files (user profile photos). Starts APScheduler with two jobs: alerts job (9 AM Bogotá + on startup) and `_job_reset_gym` (every 3 minutes, resets `esta_en_gym = False` for users whose last entry exceeds `MINUTOS_SESION`).
- `backend/models.py` — All SQLAlchemy models (13 tables): `usuarios`, `planes`, `pagos`, `wods`, `resultados_wod`, `productos`, `ventas`, `asistencias`, `movimientos_financieros`, `medidas_salud`, `marcas_rm`, `alertas_membresia`, `metodos_pago`
- `backend/database.py` — SQLite session factory
- `backend/security.py` — BCrypt password hashing, JWT creation/validation (HS256, 7-day expiry)
- `backend/routers/` — One file per domain: `auth`, `usuarios`, `pagos`, `planes`, `productos`, `ventas`, `wods`, `asistencia`, `finanzas`, `salud`, `alertas`, `marcas`, `metodos_pago`
- `backend/schemas/` — Pydantic request/response models; one file per domain except `planes` (schemas defined inline in router): `asistencia`, `alerta`, `finanza`, `pago`, `producto`, `venta`, `wod`, `usuario`, `salud`, `marcas`
- `backend/seed.py` — Creates default plans and admin user (runs on app startup via `main.py`)

**Frontend layout:**
- `frontend/src/main.js` — Vue app init; Axios interceptor adds `Authorization: Bearer {token}` from `localStorage`
- `frontend/src/api.js` — Axios instance with `baseURL: http://127.0.0.1:8000`
- `frontend/src/router/index.js` — Route guards using `meta.requiresAuth` and `meta.roles`; clients default to `/home`, admin to `/usuarios`, coach to `/home`. `pendiente` → forzado a `/planes`. Clientes con membresía vencida (`membresiaVencidaFor`) solo acceden a `RUTAS_CLIENTE_VENCIDO = ['/home', '/planes', '/']`.
- `frontend/src/composables/useAuth.js` — Reactive role helpers: `isAdmin`, `isCoach`, `isCliente`, `canManage`
- `frontend/src/lib/whatsapp.js` — `telefonoWa()` / `linkWa()`: única normalización de teléfonos del frontend (ver "Teléfonos de WhatsApp").
- `frontend/src/views/` — One large SFC per page: `LoginView`, `DashboardView` (la página de resumen; no confundir con `components/Dashboard.vue`, que es el layout), `UsuariosView`, `UsuarioPerfilView`, `HomeView`, `TiendaView`, `WodsView`, `WodsPersonalizadosView`, `FinanzasView`, `PlanesView`, `SaludView`, `SaludMedidaView`, `MarcasView`, `MarcasEjercicioView`, `MiPerfilView`.
- `frontend/src/components/Dashboard.vue` — Main layout shell (sidebar + navigation). Does NOT show membership status in the sidebar — that info lives in `HomeView`. Sidebar organizado en tres secciones: **Gestión** (admin+coach), **Contenido** (todos), **Mi Box** (coach+cliente). Ver sección de sidebar más abajo.
- `frontend/src/components/InputPassword.vue` — Input de contraseña con ojito para mostrarla. **Los 7 campos de contraseña de la app lo usan**: login, registro, crear/editar cliente, Mi Perfil, perfil de cliente y el desbloqueo del kiosco. Es un componente y no markup repetido porque el SVG del ojo son 6 líneas por campo. Las clases del input las pasa quien lo usa (`input-class`): cada pantalla tiene su estilo de borde y focus. Expone `focus()` — un `ref` sobre el componente apunta a la instancia, no al `<input>`, y el modal del kiosco necesita enfocarlo al abrirse. Arranca siempre oculta.
- `frontend/src/components/BloqueCard.vue` — Acordeón reutilizable de bloque horario (usado por `SesionesPanel`). Header clicable muestra hora del bloque + badge de personas; al expandir muestra la lista completa de asistentes con hora exacta de entrada.
- `frontend/src/data/` — Shared config files: `saludTipos.js` (6 measurement configs), `ejerciciosMarcas.js` (12 fixed exercises)
- `frontend/src/lib/avatar.js` — `fotoSrc(u)`: la foto del usuario, o `AVATAR_FALLBACK` si no tiene. El fallback es una silueta blanca sobre `#dc2626` como **data: URI de SVG inline**. Reemplazó a `ui-avatars.com` (iniciales), que exigía internet —la PC del gym no siempre lo tiene y el avatar quedaba roto— y le mandaba el nombre de cada socio a un tercero. No re-introducir un servicio externo de avatares. Lo usan `UsuariosView`, `UsuarioPerfilView` y `MiPerfilView`; `AccesoView` es la excepción a propósito: sin foto muestra el check verde de "acceso permitido", que ahí es la información que importa.

## Key Patterns

**Auth flow:** POST `/login` returns a JWT → stored in `localStorage.token` → injected via Axios interceptor → backend validates via `get_current_user()` dependency → user role checked per-route.

**Role-based access:**
- Roles: `admin`, `coach`, `cliente`, `pendiente` (enum `RolUsuario` in `models.py`)
- Backend: route-level `Depends(_require_admin_or_coach)` or `Depends(_require_admin)` pattern in each router
- Frontend: `meta.roles` on routes + `useAuth` composable in components
- `pendiente` users are redirected to `/planes` by the router guard

**Rendimiento y seguridad (convenciones a mantener):**
- **Índices de BD:** se crean vía bloque `CREATE INDEX IF NOT EXISTS` en `main.py` (idempotente, corre en SQLite y Postgres, cubre bases ya desplegadas). Al agregar consultas por columnas nuevas, añadir el índice ahí.
- **Eager loading:** los listados que serializan relaciones usan `selectinload`/`joinedload` para evitar N+1 (ver `_EAGER_EJERCICIOS` en `wods.py`, `joinedload` en `finanzas.py`/`alertas.py`/`pagos.py`). El listado de usuarios usa `defer(Usuario.huella_template)` para no arrastrar la columna biométrica.
- **Rutas lazy (frontend):** `router/index.js` importa las vistas con `() => import(...)` (solo Login y Dashboard son estáticos). Mantener el patrón al agregar vistas para no engordar el bundle inicial. `vite.config.js` separa `vendor` y `chart` en chunks propios.
- **Chart.js:** NO usar `chart.js/auto`. Importar el helper `getChart()` de `src/lib/chart.js` (carga diferida + registro selectivo de los componentes de línea/barra). `renderChart` es `async` y hace `const Chart = await getChart()`.
- **Rate limiting:** endpoints públicos sensibles (login, registro) usan `Depends(limitar(bucket, max, ventana))` de `backend/ratelimit.py` (en memoria, por-worker). El bridge (asistencia por huella) NO se limita para no interferir con la palanquera.

## Defensas del registro público

`POST /registro` es el único endpoint donde un desconocido escribe en la base. **El riesgo no es de acceso sino de volumen:** una cuenta falsa entra como `PENDIENTE` y con ese rol no puede ver ni tocar nada hasta que el admin la activa. Cuatro capas, y conviene entender qué cubre cada una porque ninguna alcanza sola:

1. **Límite por IP** (`_limite_registro`, 3/hora). Primera barrera barata. **No es la que sostiene el esquema:** vive en memoria, así que se resetea en cada deploy de Render, y una IP se rota con datos móviles o VPN.
2. **Techo global `REGISTROS_MAX_HORA`** (default 20, env var). Cuenta los `Usuario.created_at` de la última hora **contra la base**, así que es común a todos los workers y sobrevive a los reinicios. Es la capa que ataja un flood distribuido. Está muy por encima de un día real de inscripciones; si alguna vez hay una jornada masiva, se sube temporalmente.
3. **Honeypot `sitio_web`.** Campo oculto por CSS en `LoginView`; si llega con contenido, el backend **responde el 201 de siempre y no crea nada** — un 422 le enseñaría al bot cuál es el campo a evitar. No se agregó la validación de "tiempo mínimo de formulario": el timestamp lo manda el cliente y falsificarlo es trivial.
4. **El registro no acepta foto.** Era el camino más barato para llenar el bucket (5 MB × N). La carga la hace después el admin desde `UsuarioPerfilView` o el socio desde `MiPerfilView`.

**Descartado por ahora, no por malo:** CAPTCHA (Turnstile), OTP por WhatsApp, bloqueo de dominios desechables. Si el spam llega igual, **Turnstile es el siguiente paso** y es el que más rinde por el trabajo que cuesta.

**Almacenamiento de imágenes — todo se normaliza a WebP.** `guardar_archivo()` en `storage.py` es el embudo de las tres subidas que quedan (foto de perfil por admin, `/me/foto`, foto de producto): redimensiona (512 px avatares, 1024 px productos) y re-encodea a WebP. El ahorro grande **no lo da el formato sino los píxeles** — una foto de celular pesa MB en cualquier formato; a 512 px queda en decenas de KB. Con el bucket de Supabase en 1 GB, guardar los originales lo llenaba en pocos cientos de subidas y ahí fallarían también las fotos legítimas.

Detalles que no son opcionales: `ImageOps.exif_transpose()` (sin eso las fotos verticales de celular salen acostadas, porque la orientación vive en el EXIF y al re-encodear se pierde) y el tope `Image.MAX_IMAGE_PIXELS` con captura de `DecompressionBombError` — al pasar a **decodificar** la imagen aparece un riesgo que antes no existía: un PNG de 200 KB puede expandirse a 30000×30000 y comerse la RAM del contenedor. Los magic bytes de `_detectar_imagen()` siguen como primer filtro barato. Las URLs viejas (`.jpg`/`.png`) se siguen sirviendo: la normalización aplica a lo que se sube de ahora en más.

**En los tests, `PNG_BYTES` tiene que ser un PNG real** (lo genera Pillow en `conftest.py`): el header falso + ceros que había antes ahora se rechaza con 400, que es el comportamiento correcto.
- **401 global:** `api.js` tiene un interceptor de respuesta que ante 401 limpia la sesión y redirige a `/login`.
- **Scheduler con multi-worker:** el Dockerfile corre `--workers 2`; APScheduler se protege con un advisory lock de Postgres (`pg_try_advisory_lock`) en `main.py` para que el job de alertas corra en un solo worker.

**Financial movements:** `FinanzasView` tiene **todo lo financiero**: el selector de período (Hoy / Esta semana / Este mes / Este año / Todo / Rango), las **5 tarjetas de balance** (Membresías, Tienda, Total ingresos, Egresos, Balance neto) atadas a ese selector, y el historial de movimientos con alta manual. El Resumen (`/dashboard`) **no** duplica nada de esto.

El modal de alta registra **ingreso o egreso** (antes solo egresos). Las categorías salen de `CATEGORIAS_POR_TIPO` y cambian con el tipo; un `watch` limpia la categoría al alternar, para no mandar un egreso categorizado como "Membresía". **`venta_tienda` no se ofrece a propósito:** las ventas se leen de la tabla `ventas`, así que cargarlas también como movimiento manual las contaría dos veces (es el mismo motivo del `DELETE … WHERE fuente='venta_tienda'` de `main.py`).

**Exportar Excel:** botón en el header → `GET /finanzas/exportar-excel?fecha_desde=&fecha_hasta=` (solo admin), con **el período seleccionado en pantalla**, no el histórico. Genera **tres hojas**: *Resumen* (período, membresías, tienda, ingresos, egresos, balance + desglose de egresos por categoría, que **se imprime siempre** — omitirlo cuando está vacío hace dudar de si no hubo gastos o si el export se rompió), *Ingresos* (pagos de membresía + ventas + ingresos manuales, con columna **Origen**) y *Egresos* (solo registros manuales, **sin** columna Origen porque diría lo mismo en todas las filas). Las dos hojas de movimientos traen **todas** las filas del período (**sin el tope de 200** del listado: un export recortado sería un export equivocado), montos **positivos** (el nombre de la hoja ya da el signo) y una fila **TOTAL** al pie. Las fechas se convierten de UTC a Bogotá para que coincidan con la pantalla.

**La partición por tipo se hace en memoria sobre una sola recolección.** Llamar a `_recolectar_movimientos(tipo="ingreso")` y después con `"egreso"` sería más corto de escribir, pero correría dos veces las consultas de pagos, ventas y movimientos.

**Datos de mentira para desarrollo:** `backend/scripts/seed_demo_finanzas.py` siembra ~57 movimientos (renta, nómina, servicios, mantenimiento, marketing, equipamiento, ingresos varios) repartidos en 12 meses, para poder mirar el módulo con algo adentro. **Aborta si la base no es SQLite** — mete plata inventada en el libro contable y en Supabase sería un desastre. Todos llevan `[demo]` en `notas`; `--limpiar` los borra sin tocar los reales, y sembrar de nuevo limpia primero (semilla fija, así dos corridas dan los mismos montos).

El endpoint y el listado comparten `_recolectar_movimientos()`, que fusiona pagos + ventas + movimientos manuales. Si esa fusión se duplicara, el Excel y la pantalla podrían divergir.

El historial pagina de a 15 en cliente sobre `movimientosFiltrados` (la petición ya trae hasta 200 del período). **Ojo con los nombres:** `rangoDesde`/`rangoHasta` son las fechas del período "Rango"; las filas visibles son `filaDesde`/`filaHasta`. `finanzas.py` surfaces income from three sources: rows in `pagos` (membership payments, both plan-based and personalizado), rows in `ventas` (shop sales), and rows in `movimientos_financieros` (manual entries + legacy `pago_directo` records). Pagos and ventas are NOT mirrored into `movimientos_financieros` — the finanzas listing reads from each table directly to avoid double-counting.

**Pago model:** `plan_id` is nullable. Personalizado payments have `plan_id = NULL` and `duracion_dias` set to the days purchased. The historial endpoint shows them as `"Personalizado (N días)"`.

**Email/document normalization:** All routes that write or look up `usuarios.email` apply `.strip().lower()` (login, registro, POST/PATCH usuarios, JWT subject in `get_current_user`). `documento_identidad` is `.strip()`-ed. The model has `unique=True` on both columns, but case normalization happens in code so `Foo@x.com` and `foo@x.com` are treated as the same account.

**Fingerprint integration:** see the dedicated section below.

**Migraciones de arranque (`backend/main.py`):** hay TRES bloques, y agregar una columna nueva exige tocar los dos primeros:
1. **Bloque SQLite** (`if engine.url.get_backend_name() == "sqlite"`): `ALTER TABLE … ADD COLUMN` en try/except + reconstrucción de tabla para cambios de nullability (rename → CREATE → INSERT → DROP, guardado por `PRAGMA table_info`). **Solo corre en SQLite (dev).**
2. **Bloque Postgres** (`if … != "sqlite"`, lista `_cols_pg`): `ALTER TABLE … ADD COLUMN IF NOT EXISTS …` (idempotente). **Imprescindible:** en Postgres `create_all` NO agrega columnas a tablas existentes, así que una columna nueva que solo esté en el bloque SQLite **faltará en producción** y romperá los INSERT (fue la causa del bug "no deja crear WODs"). Cuidado con los tipos: `BOOLEAN DEFAULT FALSE` (no `DEFAULT 0` como en SQLite).
3. **Bloque de índices** (`_indices`, cross-DB): `CREATE INDEX IF NOT EXISTS`, corre en ambos motores.

**Regla:** al agregar una columna, agregala al modelo Y a los bloques 1 y 2. Hay también limpiezas de datos puntuales (p.ej. `DELETE … WHERE fuente='venta_tienda'`) que corren cross-DB e idempotentes.

**Chart lifecycle (Vue + Chart.js):** Always call `destruirChart()` before creating a new instance. Use `watch(registros, async () => { await nextTick(); await nextTick(); renderChart() })` to ensure the canvas is in the DOM after a `v-if` renders.

**Unit normalization (1RM):** All weight comparisons (PR detection, chart, esPR preview) are done in kg using `1 kg = 2.20462 lbs`. Values are converted back to the display unit (`ultimaUnidad`) only for rendering. Never compare `rm_calculado` values from different records without normalizing first.

**Public registration:** `POST /registro` accepts `multipart/form-data` (not JSON) because it supports an optional profile photo. Use `Form(...)` for all text fields and `File(None)` for the photo. The frontend sends a `FormData` object with `Content-Type: multipart/form-data`.

**Términos y condiciones + datos de afiliación (registro):** el registro exige `acepta_terminos=true` (422 si falta) y campos obligatorios `fecha_nacimiento`, `eps`, `barrio`, `contacto_emergencia_nombre/telefono`. Al aceptar se guardan `acepto_terminos`, `terminos_fecha` (hora Bogotá) y `terminos_version` — la constante `TERMINOS_VERSION` vive en `routers/auth.py` y debe mantenerse en sincronía con `frontend/src/components/TerminosModal.vue` (modal con el texto completo del contrato de adhesión). **Menores de edad:** si la fecha de nacimiento da < 18 años, el backend exige `es_menor=true` + `acudiente_nombre/telefono/documento` (cláusula 7 del contrato: quien registra declara ser el acudiente); el frontend muestra la sección de acudiente automáticamente. `GET /usuarios/pendientes` expone `es_menor` y los datos del acudiente — la fila de pendientes en `UsuariosView` marca a los menores con un badge ámbar y muestra el bloque del acudiente (también ámbar) dentro del detalle desplegable, para que el admin confirme antes de activar. La **edad no se almacena** — se calcula de `fecha_nacimiento` (`_calcular_edad` en `auth.py`, computed `edad` en `LoginView`). Los usuarios existentes no se ven afectados (columnas nullable / default false); admin puede completar los datos desde el perfil.

## Teléfonos de WhatsApp

**Hay exactamente dos implementaciones y tienen que dar el mismo resultado:** `telefonoWa()` en `frontend/src/lib/whatsapp.js` y `normalizar_telefono()` en `backend/whatsapp.py`. Regla: **`'57'` + los últimos 10 dígitos**, `null`/`None` si no hay al menos 10. En el frontend se usa siempre `linkWa(telefono, mensaje)`, que devuelve el `wa.me` armado o `null`.

**"Últimos 10 dígitos + 57" y no "agregar 57 si falta"** — así el resultado es el mismo venga el número como `3165300987`, `+57 316 530 0987` o `57 316 530 0987`. El admin carga el teléfono a mano desde el perfil y ninguno de esos formatos es raro.

**Llegó a haber tres.** `PlanesView` hacía solo `.replace(/\D/g,'')`, sin prefijo: con un teléfono guardado como `3165300987` generaba `wa.me/3165300987`, que no es un número internacional válido y WhatsApp rechaza. Era el botón de "enviar el comprobante de pago", o sea la ruta por la que un socio nuevo paga. Al agregar un botón de WhatsApp nuevo, **importar el helper, no escribir la normalización**.

**`null` en vez de una cadena corta, y el llamador esconde el botón.** Un link a medio armar manda a WhatsApp a una pantalla de error y quien lo aprieta no sabe si falló el link o si el gym no contesta. Por eso los `v-if` preguntan por el link, no por el teléfono.

**`GET /contacto`** (público, lo consulta un `pendiente` que aún no puede autenticarse) devuelve el teléfono del admin para ese botón. Usa `order_by(Usuario.id)` antes del `.first()`: sin orden, el motor elige la fila, y si hubiera más de un ADMIN el botón podía apuntar a uno distinto en cada consulta. Devuelve **solo** el teléfono — no agregar nombre ni email.

## Paleta de colores

La fuente única de los colores categóricos es `frontend/src/data/paleta.js`. No hay tokens custom en `tailwind.config.js` (se evaluó y se descartó: convivirían con 600 usos de `red-*` ya escritos, creando dos formas válidas de decir lo mismo). La paleta es una convención documentada, no una capa de indirección.

**Núcleo semántico — 4 familias de Tailwind.** Son las que el proyecto ya usaba de facto; ninguna se usa para datos categóricos.

| Rol | Familia | Dónde |
|---|---|---|
| Neutro | `gray` | 900/800 superficies oscuras · 700/600 texto · 400 muted · 200/100 bordes · 50 fondos |
| Marca / acción primaria / destructivo | `red` | CTA, nav activo, focus ring, eliminar, **huella/enrolamiento** |
| Éxito / vigente | `emerald` | membresía activa, en el box, ingresos, asistencia |
| Alerta / por vencer | `amber` | vence pronto, menores de edad, PR destacado, IMC fuera de rango |

`green` no se usa: es `emerald`. `red` cubre marca y destructivo (no hay una quinta familia para "peligro").

**No hay escala categórica.** `paleta.js` exporta solo `BADGE_NEUTRO`. Existió una escala de 5 hues fríos (`CATEGORICOS`, `CATEGORIA_EJERCICIO`, `puntoCategoria()`) cuyo último consumidor fue `WodVideosEditor`; se eliminó junto con la columna `ejercicios.categoria`. `puntoRol()` ya se había ido antes por lo mismo.

**Si vuelve a hacer falta colorear datos categóricos**, estas eran las reglas y siguen valiendo: hues **fríos** (`sky-500`, `slate-600`, `violet-500`, `fuchsia-500`, `gray-400`), nunca rojo/verde/ámbar —que ya significan otra cosa—; como **punto** sobre un badge neutro, no como fondo; y **hasta 6 categorías**, porque por encima de eso el color deja de distinguirse y estorba. Las 10 categorías de `FinanzasView` van justamente con badge neutro y sin punto (`colorCategoria()` devuelve `BADGE_NEUTRO`): el signo del movimiento ya se lee en el color del monto.

**Chips seleccionados** (filtros, selector de género): activo `bg-gray-800 text-white`, inactivo `border-gray-200 text-gray-500`. El género **no** usa azul/violeta.

**Purge de Tailwind:** las clases en `paleta.js` van como strings completos (`'bg-sky-500'`), nunca interpoladas — el scanner de `content` no resuelve `` `bg-${hue}-500` `` y purgaría la clase. Si un punto aparece invisible en el build, es esto. Verificable con `grep -o "\.bg-sky-500" dist/assets/*.css` tras `npm run build`.

**Excepción consciente:** los botones de WhatsApp del dashboard (felicitar cumpleaños y recordar vencimiento) van en `emerald` — es el color de marca de un tercero y `emerald-500` es prácticamente el verde de WhatsApp.

**Gráficas (Chart.js):** serie principal `#f87171` (red-400), highlight de PR `#f59e0b` (amber-500), serie secundaria `#0ea5e9` (sky-500), grid `#f3f4f6` (gray-100).

## DashboardView — resumen del box

Ruta `/dashboard` (roles `admin`, `coach`), archivo `frontend/src/views/DashboardView.vue`. **Ojo con el nombre:** `components/Dashboard.vue` es el *layout* (sidebar + shell); `views/DashboardView.vue` es la *página*. Es el aterrizaje del admin tras el login (el redirect de `router/index.js`); el coach sigue cayendo en `/home`.

**Dos pestañas y solo dos: Clientes y Asistencia** (`tab` en `DashboardView`, `v-show` y no `v-if` — `SesionesPanel` trae sus datos al montarse, y con `v-if` cada ida y vuelta dispararía otro refetch). **El Resumen no tiene bloque financiero.** Se probó meter acá las 5 tarjetas de balance + una gráfica de 12 meses, en una pestaña "Finanzas", y se revirtió: lo financiero vive entero en `/finanzas`, que tiene su propio selector de período (Hoy / Semana / Mes / Año / Todo / Rango) y por lo tanto contesta cosas que un bloque fijo al mes en curso no puede. **No volver a duplicarlo acá.**

| Bloque | Contenido | Fuente |
|---|---|---|
| **Clientes** | activos (con delta contra el cierre del mes pasado), **pendientes de activación**, recuperables (vencidos <30 días), tasa de renovación, **gráfica de activos por mes**, **cumpleaños de hoy** y **membresías por vencer en 7 días** | `/dashboard/resumen` + `/dashboard/socios-mensuales` + `/alertas/` |
| **Asistencia** | hoy, semana, promedio diario (30 días), **Participación** (% de socios activos que vino esta semana; la clave del API sigue siendo `engagement`) y el **panel de sesiones por bloque horario** (`SesionesPanel`) | `/dashboard/resumen` + `/asistencia/sesiones-por-bloque` |

Cada bloque carga por separado con su propio skeleton: si un endpoint falla, el resto de la pantalla sigue viva.

**Auto-refresh — la pantalla vive abierta todo el día en recepción.** Antes todo cargaba en `onMounted` y ahí quedaba: "Hoy" no se movía mientras la gente marcaba huella y la única forma de ver datos frescos era recargar a mano. Ahora hay un `setInterval` de 60 s que refresca **solo `/dashboard/resumen`** (lo barato y lo que se mueve solo) y se saltea si `document.visibilityState !== 'visible'`. `/socios-mensuales` y `/alertas/generar` **no entran al intervalo**: el primero reconstruye la serie sobre toda la tabla `pagos` y cambia como mucho una vez al día, y el segundo es una **escritura**. Esos dos se refrescan en el `visibilitychange`, con throttle de 60 s porque cambiar de pestaña es un gesto que se repite mucho.

**`ahora` es un ref reactivo, no `new Date()` suelto.** La fecha del encabezado, los días que faltan para cada vencimiento y la clave de felicitados se derivan de él para que crucen la medianoche solos; fijados al montar, a las 00:05 el encabezado seguía diciendo ayer y `felicitados:` seguía marcando a los de la víspera. El `watch` sobre `claveFelicitados` relee el localStorage al cambiar el día.

**El watch de la gráfica observa también `sociosMensuales`, no solo `puedeGraficar`:** al refrescar, `puedeGraficar` ya está en `true` y no volvería a dispararse, así que la gráfica se quedaría con los datos viejos.

**Los días de vencimiento se derivan de `fecha_vencimiento`, nunca de `dias_anticipacion`.** Esa columna se congela cuando `generar_alertas` crea la alerta y no se actualiza nunca, así que a los dos días miente: el panel llegaba a decir "Vence en 5 días" el mismo día del vencimiento, y `whatsappAlerta()` le mandaba ese plazo equivocado al socio. El backend ya lo hace bien para el envío automático (`alertas.py` calcula contra `Usuario.fecha_vencimiento`); el helper `diasParaVencer()` alinea el camino manual. Por lo mismo, `pendientes` se reordena en el frontend por `fecha_vencimiento` — el backend ordena por la columna congelada.

**Tarjetas navegables:** en el bloque Usuarios, *Activos* y *Pendientes* son `router-link` (a `/usuarios` y a `/usuarios?tab=pendientes`) y lo señalan con una flecha → en el encabezado que se acenta y se desplaza en hover. `UsuariosView` lee `route.query.tab` al montar y preselecciona esa pestaña si la clave existe en `tabs`; cualquier otro valor cae en el default `todos`. Las otras dos tarjetas (Recuperables, Renovación) no navegan y por eso no llevan flecha — la flecha es la señal de que la tarjeta es un enlace, no decoración.

Las dos listas accionables (cumpleaños y por vencer) llevan botón de WhatsApp con mensaje pregenerado, vía `linkWa()` de `frontend/src/lib/whatsapp.js` (ver "Teléfonos de WhatsApp" más abajo). Los botones se condicionan al **link**, no al teléfono (`v-if="whatsappAlerta(a) && …"`): un número cargado incompleto generaba un botón que llevaba a un error de WhatsApp. Las dos tienen la misma estructura: pestañas *pendientes* / *enviados* y tope de 4 filas visibles con scroll (`max-h-[12.5rem]` para cumpleaños, `max-h-[14rem]` para vencimientos — las filas de vencimiento llevan dos líneas y por eso son más altas).

**Cumpleaños felicitados — se guardan en `localStorage`, no en la BD.** A diferencia de las alertas de vencimiento, los cumpleaños no tienen tabla propia: no hay dónde persistir "ya lo felicité". Se usa la clave `felicitados:YYYY-MM-DD`, que incluye la fecha para vaciarse sola al día siguiente; al montar se borran las claves de días anteriores para que no se acumulen. **Limitación conocida:** el registro es por dispositivo, así que felicitar desde el celular no se refleja en la PC del gym. Si eso llega a molestar, la solución es una tabla o una columna, no más localStorage.

**El panel "Por vencer · 7 días" reemplazó por completo a la vista `AlertasView`,** que fue borrada junto con su ruta y su enlace del sidebar. Tiene dos pestañas internas: *pendientes* y *enviados de la última semana*. Ver la sección "Alertas de membresía".

**Panel de sesiones** (`components/SesionesPanel.vue`): el contenido íntegro de la vista `/sesiones`, que se eliminó al moverla acá. Conserva los tres modos (esta semana / este mes / fecha específica), el buscador y el acordeón `BloqueCard`. Se extrajo a componente en vez de copiarlo dentro de `DashboardView` porque son ~500 líneas y la vista ya iba por 750. Trae sus propios datos al montarse, así que cambiar de pestaña y volver dispara un refetch — es barato y evita estado colgado.

**Gráfica** (clientes activos por mes, en el bloque Clientes): `getChart()` de `lib/chart.js` (carga diferida), `destruirChart()` antes de crear, y `onUnmounted(destruirChart)`. **El render se dispara con un `watch` sobre `puedeGraficar`, no al terminar el fetch.** El canvas vive dentro del bloque que espera a `/resumen`, pero los datos vienen de `/socios-mensuales`: son dos peticiones en paralelo, y renderizar al terminar la segunda deja la gráfica en blanco para siempre cuando esa gana la carrera (el canvas todavía no existe y `renderChart` sale sin hacer nada). El `watch` espera a que las dos condiciones se cumplan, con `await nextTick()` antes de dibujar. Eje Y con `ticks: { precision: 0 }` — son personas, un eje con decimales no significa nada.

### Router `/dashboard` — reglas de las agregaciones

`backend/routers/dashboard.py`. Dos reglas que valen para todo el módulo y que son la fuente de bugs sutiles:

1. **Zona horaria.** `Asistencia.fecha_hora`, `Pago.fecha_pago`, `Venta.fecha_venta` y `MovimientoFinanciero.fecha` se guardan como datetime **naive en UTC**. Todo agrupado por día, hora o mes convierte a Bogotá primero; si no, lo ocurrido después de las 19:00 locales cae en el día o el mes siguiente. Para el "hoy" del negocio, `hoy_bogota()`. Hay un test explícito de esto (`test_afluencia_agrupa_en_hora_de_bogota`).

   **Los helpers viven en `backend/fechas.py`, no en un router:** `a_bogota()`, `inicio_dia_utc()`, `fin_dia_utc()`, `a_utc()`. `dashboard.py` los importa con alias (`_a_bogota`, etc.) para no tocar sus decenas de llamadas. **No los redefinas localmente** — tenerlos duplicados fue exactamente la causa de que `/asistencia/sesiones-por-bloque` construyera su ventana con `datetime(desde, 00:00)` naive: eso es medianoche **UTC**, o sea las 19:00 de Bogotá del día anterior, así que el rango quedaba corrido 5 horas, arrastraba la noche del día previo y **perdía la del último día** (con el box entrenando de 19:00 a 21:00, las entradas de la noche no aparecían en el calendario hasta el día siguiente). Cubierto por `test_sesiones_ventana_es_el_dia_de_bogota_no_el_de_utc`, que ataca las dos puntas — el test viejo usaba las 14:00 UTC, lejos del borde, y pasaba con la ventana mal construida.

   **Regla de test:** un caso de zona horaria a mediodía no prueba nada. Poné el dato entre las 19:00 y la medianoche de Bogotá, que es donde el bug aparece.
2. **`/ingresos-mensuales` no usa `extract()` en SQL** justamente por lo anterior: agrupar por mes en UTC correría los movimientos de fin de mes. El bucketing se hace en Python sobre una ventana acotada.

| Endpoint | Rol | Notas |
|---|---|---|
| `GET /resumen` | admin, coach | KPIs de socios y asistencia, renovación y cumpleañeros |
| `GET /inactivos?dias=14&limite=20` | admin, coach | Socios vigentes que dejaron de venir. `MAX(fecha_hora)` por usuario en una subconsulta (sin N+1); `dias_sin_venir = null` significa que nunca marcó. **Hoy ninguna vista lo consume** — quedó disponible tras reemplazar ese panel por el de vencimientos |
| `GET /afluencia?semanas=4` | admin, coach | Promedio de personas por hora, separando entre semana de sábado. **Hoy ninguna vista lo consume** — quedó disponible tras reemplazar la curva por el panel de sesiones |
| `GET /socios-mensuales?meses=12` | admin, coach | Clientes con membresía vigente **al cierre de cada mes**, reconstruido desde `pagos`. Alimenta la gráfica del bloque Clientes |
| `GET /ingresos-mensuales?meses=12` | **solo admin** | serie continua: los meses sin movimiento van en cero, no ausentes. **Hoy ninguna vista lo consume** — quedó disponible tras revertir el bloque de Finanzas del Resumen |

**El delta de la tarjeta Activos compara activos, no altas.** Sale de los dos últimos puntos de `sociosMensuales` (`deltaActivos`), no de `altas_mes − altas_mes_anterior` como antes: debajo del número de activos, un delta de altas se leía como "perdí un socio" cuando en realidad decía "entró un cliente nuevo menos que el mes pasado". Es `null` con menos de dos meses de serie y la línea no se muestra — comparar contra un mes que no existe sería inventar crecimiento. Los campos `altas_mes`/`altas_mes_anterior` siguen viniendo en `/resumen`, sin consumidor por ahora.

**Activos por mes — también es una inferencia.** Misma raíz que la renovación: no hay histórico de membresías. Cada pago define una ventana `[fecha_pago, fecha_pago + días)` y un cliente estaba activo en una fecha si alguna ventana la cubría. **El mes en curso no se infiere: se cuenta** contra `usuarios.fecha_vencimiento`, igual que la tarjeta Activos, así que los dos números coinciden siempre (test: `test_socios_mensuales_ultimo_punto_coincide_con_el_resumen`). Se intentó inferirlo también y se corrigió: cualquier cliente vigente **sin pago registrado** —activado a mano, o sembrado por un script de demo— desalineaba la gráfica con la tarjeta. El presente es un dato conocido; solo el pasado hay que reconstruirlo. Los meses anteriores usan como corte el último día del mes. **La serie arranca en el mes del primer pago**, no 12 meses fijos: dibujar en cero los meses previos a que el sistema existiera mostraría una rampa de crecimiento que nunca ocurrió. Limitación: solo ve lo que pasó por `pagos` — un vencimiento estirado a mano desde el perfil no aparece.

**Tasa de renovación — es una inferencia, no un dato.** No hay histórico de membresías: `usuarios.fecha_vencimiento` se pisa en cada renovación, así que mirarla solo mostraría a los que **no** renovaron. Se reconstruye sobre `pagos`: el vencimiento implícito de un pago es `fecha_pago + días que cubre` (del plan, o `duracion_dias` si es personalizado), y cuenta como renovado si hay otro pago entre 7 días antes y 30 después de ese vencimiento. La ventana es móvil de 30 días, no "del mes": el día 1 el mes corriente sería una ventana de un día. Sesgo conocido: quien venció hace pocos días sigue dentro de su margen y cuenta como no renovado, así que el número queda algo pesimista — por eso la UI muestra el crudo ("18 de 25") junto al porcentaje.

## HomeView — client/coach home screen

Route `/home` (roles: `cliente`, `coach`). Shows:
- Membership status card + current plan card (clients only)
- Coach staff card (coaches only)
- Attendance calendar with month navigation (prev/next arrows, fetches 12 months once on mount)

**Loading state (membresía):** `cargandoPerfil` ref (inicia `true`, pasa a `false` en el `finally` del fetch). Mientras carga, las tarjetas de membresía y plan muestran un spinner. Esto evita el flash de "-999 días / Sin membresía activa": `diasRestantes` devuelve el centinela `-999` cuando `userData.fecha_vencimiento` aún no llegó, y sin el flag se renderizaba por un instante antes de la respuesta de `/me`.

**Attendance calendar pattern:**
- Fetch: `GET /asistencia/mi-historial?meses=12` on mount
- State: `mesOffset` ref (0 = current month, -1 = previous, min = -11)
- `calendarioActual` computed builds the single visible month from `attendedSet`
- Cell classes: `bg-emerald-500` attended, `bg-gray-800` today, `bg-gray-50` future, `bg-transparent` past not attended

## UsuarioPerfilView — admin user profile page

Route `/usuarios/:id` (roles: `admin`, `coach`). Three sections:

**Profile card:** Centered column layout — photo on top, name below (prevents mobile truncation). Shows email, document, phone, gender, fingerprint status, membership status. "Editar perfil" button in the header opens an edit modal.

**Edit modal:** Fields: nombre, email, teléfono, documento_identidad, género, fecha_nacimiento (opcional), optional password change (checkbox toggle + visibility toggle). Only sends changed fields to the backend (`PATCH /usuarios/:id`). Updates `usuario.value` reactively on success without page reload.

**Profile card:** Muestra `fecha_nacimiento` como "15 ene 1995 (30 años)" usando el helper `formatCumpleanos(f)` — calcula la edad en base a la fecha de hoy. Solo se muestra si el campo existe.

**Attendance calendar:** Same month-navigation pattern as `HomeView` but fetches `GET /asistencia/historial/:id?meses=12` (admin endpoint).

**Subscription history:** Table from `GET /pagos/usuario/:id` — date, plan name, amount, payment method, and per-row actions (edit/anular). The membership card has an "Agregar membresía" button (red) that opens a modal mirroring the "Activar Usuario" modal in `UsuariosView` (plan grid + "Personalizado (días)" option + monto + método). Confirmar dispatches to `POST /pagos/` (plan) or `POST /pagos/directo/` (personalizado).

**Edit/anular pago:**
- Edit (`PATCH /pagos/{id}`): only `monto` and `metodo_pago`. Plan changes are not allowed in-place — the UI tells the admin to anular and recreate.
- Anular (`DELETE /pagos/{id}`): subtracts `plan.duracion_dias` (or `pago.duracion_dias` for personalizado) from `usuario.fecha_vencimiento`, then deletes the `Pago`. The resulting fecha may land in the past — that's correct (membership expired by the reversal).

**Navigation:** The "ver" button in `UsuariosView` calls `router.push('/usuarios/${u.id}')` instead of opening a modal.

## Dashboard — estructura del sidebar

El sidebar está dividido en secciones semánticas según el rol:

**Usuario pendiente:** solo ve Planes.

**Sección "Gestión"** (`canManage` = admin + coach):
- Resumen (`/dashboard`), Usuarios, Acceso Manual, Ejercicios (admin + coach). **Sesiones y Alertas WhatsApp ya no están**: los recordatorios se atienden desde el panel "Por vencer · 7 días" del Resumen, y `/alertas` queda solo para el historial, enlazada desde ahí.
- Planes, Finanzas (solo admin)

**Sección "Contenido"** (todos los roles no pendientes):
- WODs (siempre, si membresía vigente)
- WODs Personalizados (staff o cliente con `tieneWodsPersonalizados`, si membresía vigente)
- Tienda (solo `canManage`)

**Sección "Mi Box"** (coach + cliente):
- Inicio
- Planes (solo cliente)
- Mi Salud (cliente, membresía vigente)
- Mis Marcas (coach + cliente, membresía vigente)

**Sección "Cuenta"** (todos los roles no pendientes, incluido admin):
- Mi Perfil

## MiPerfilView — autogestión de perfil

Ruta `/perfil` (roles: `admin`, `coach`, `cliente`). Permite que **cualquier usuario edite su propia cuenta** sin pasar por admin. Está en `RUTAS_CLIENTE_VENCIDO`, así que un cliente con membresía vencida también puede entrar.

Es una **página** (no modal ni cards): encabezado con foto + identidad, sección "Datos personales" con los campos editables inline (nombre, email, teléfono, documento, género, fecha de nacimiento), sección "Seguridad" (cambio de contraseña opcional), y barra de acciones (Descartar / Guardar) que se habilita solo si `hayCambios`. La foto se cambia con un botón sobre el avatar (`POST /me/foto`). Tras guardar nombre actualiza `localStorage.userName`.

**Backend (`routers/auth.py`):** la autogestión vive junto al login, no en `usuarios.py` (que exige admin/coach).
- `GET /me` — además de membresía/plan, devuelve `telefono`, `documento_identidad`, `fecha_nacimiento` y `foto_url`. Serializado por el helper `_serialize_me(current_user, db)`.
- `PATCH /me` — edita el perfil propio (mismos campos y validación de email/documento duplicado y normalización que `PATCH /usuarios/{id}`, pero con `get_current_user` en vez de admin/coach). Acepta `UsuarioUpdate`.
- `POST /me/foto` — sube/reemplaza la foto propia (multipart, campo `foto`). Borra la anterior con `eliminar_archivo`.
- `POST /me/verificar-password` — reconfirma la contraseña del usuario logueado sin emitir token nuevo; lo usa el modo kiosco de `/acceso` para desbloquear. Rate-limited (10 / 5 min por IP). Responde **403** —no 401— con contraseña incorrecta: el interceptor de `api.js` trata cualquier 401 como sesión expirada, así que con 401 un cliente tecleando cualquier cosa en el modal sacaría al staff de su sesión. **No cambiar ese status.**

## Alertas de membresía (sin vista propia)

**`AlertasView.vue` fue eliminada**, junto con su ruta `/alertas` y su enlace en el sidebar. Los recordatorios de vencimiento se atienden enteros desde el panel **"Por vencer · 7 días"** del Resumen (`/dashboard`), que tiene dos pestañas internas: *pendientes* y *enviados de la última semana*.

El router `backend/routers/alertas.py` sigue igual y es lo que alimenta ese panel:
- `POST /alertas/generar` — reconcilia antes de listar: crea las que faltan y borra las pendientes obsoletas (el usuario renovó, o salió de la ventana de 7 días). Corre también por APScheduler a las 9 AM Bogotá y al arrancar.
- `GET /alertas/?solo_pendientes=false&enviadas_ultimos_dias=7` — **una sola llamada** trae pendientes + historial de la semana; el frontend los separa con los computed `pendientes` y `enviadas`. El parámetro `enviadas_ultimos_dias` existe porque sin cota `solo_pendientes=false` devuelve el histórico completo, que crece sin techo.
- `POST /alertas/{id}/marcar-enviada` — se dispara al abrir el link de WhatsApp. El frontend no saca la fila de la lista: le pone `enviada = true`, así pasa sola de una pestaña a la otra.

- `POST /alertas/enviar-whatsapp` — dispara la tanda de envío a demanda. **No se expone como botón**: ver abajo.

**Dedup en `generar_alertas`:** antes de crear alertas nuevas, borra las pendientes (`enviada=False`) cuya `fecha_vencimiento` ya no coincide con la del usuario (o sea, renovó) o que quedaron fuera de la ventana de 7 días. Después crea una por usuario dentro de la ventana solo si no hay ya una pendiente. Esto evita acumular duplicados cuando el admin extiende una membresía.

### Envío automático por WhatsApp Cloud API

**Dos ventanas distintas, a propósito:** `VENTANA_DIAS = 7` es la del **panel** (a partir de ahí el vencimiento aparece en el Resumen); `DIAS_ENVIO_AUTOMATICO = 3` es la del **envío** (recién ahí se le escribe al socio). El admin ve la semana completa, el socio recibe un solo mensaje y cerca de la fecha. No unificarlas.

**El filtro de envío va contra `Usuario.fecha_vencimiento`, nunca contra `AlertaMembresia.dias_anticipacion`.** Esa columna se congela al crear la alerta y `generar_alertas` no la actualiza nunca, así que a los dos días ya miente. (El texto del panel sí la lee — `textoVence(a.dias_anticipacion)` — y por eso se desactualiza; bug preexistente, conocido.)

**`backend/whatsapp.py`** — sigue el patrón de `storage.py`: env vars a nivel de módulo, flag `HABILITADO`, cliente `httpx` perezoso y **degradación segura**. Si faltan `WA_PHONE_NUMBER_ID`/`WA_ACCESS_TOKEN` o `WA_ENVIO_AUTOMATICO=0`, todo sigue funcionando en modo manual. **Ninguna función levanta excepciones**: todo error vuelve en `Resultado`, porque el llamador recorre una lista de socios y reventar a la mitad dejaría media tanda sin enviar y sin registro. `normalizar_telefono()` espeja a `telefonoWa()` de `frontend/src/lib/whatsapp.js` — **mantener las dos en sincronía**, si no el link manual y el automático escriben a números distintos (ver "Teléfonos de WhatsApp").

**La ventana de 24 h de WhatsApp:** solo se puede mandar texto libre si el cliente le escribió al negocio en las últimas 24 h. Los socios nunca escriben primero, así que **el único mensaje enviable es una plantilla aprobada por Meta** (texto libre → error 131047). El cuerpo aprobado vive en los servidores de Meta y el fallback manual en `whatsappAlerta()` del `.vue`: **cambiar uno obliga a revisar el otro**, y editar la plantilla en Meta la manda de nuevo a aprobación. Los tres parámetros son posicionales (`{{1}}` nombre, `{{2}}` cuándo, `{{3}}` fecha); cruzarlos no da error, solo manda el mensaje mal.

**Job separado, sin trigger de arranque.** `_job_envio_whatsapp` corre a las **9:10** (10 min después de `_job_alertas`, para que las alertas del día existan). **No se engancha al trigger `"date"`**: `_job_alertas` sí corre en cada arranque, y Render redespliega varias veces al día — meter el envío ahí sería un WhatsApp a cada socio por cada push. Separarlos además aísla las fallas: si Meta responde 500, la generación de alertas (de la que depende el panel) no se ve afectada. **No mover el envío dentro de `_job_alertas` ni de `POST /alertas/generar`** — ese endpoint lo llama el frontend en cada montaje del dashboard.

**Idempotencia, tres capas:** (1) la fuerte ya existía — `generar_alertas` no recrea una alerta para un `(usuario, vencimiento)` que ya tiene registro aunque esté enviada, respaldado por `uq_alerta`, así que **un socio recibe un solo mensaje por ciclo** corra el job las veces que corra; (2) `enviar_pendientes` solo toca `enviada=False` y **commitea por mensaje** (con commit final, un crash en el mensaje 18 de 20 reenviaría los 20); (3) `MAX_INTENTOS = 3` frena el reintento infinito de un número que Meta rechaza permanentemente. Sin teléfono utilizable **no consume intento** — el admin puede cargar el número y el job lo toma al día siguiente.

**Columnas de `AlertaMembresia`:** `canal` (`"whatsapp_api"` | `"manual"`), `wa_message_id`, `error_envio`, `intentos`. **No hay columna de estado** porque es derivable (`enviada=True` → enviado; `enviada=False` + `error_envio` → falló; ambos nulos → no intentado). `wa_message_id` no lo lee nadie hoy: es para buscar el mensaje en el WhatsApp Manager cuando el socio dice "no me llegó".

**Panel (`DashboardView.vue`):** el botón verde "Recordar" pasó a ser **fallback** — `mostrarBotonManual()` lo muestra solo si el automático no está configurado o si esa fila falló; con el automático andando y sin errores, mostrarlo invitaría a mandar dos veces. Chips: ámbar `Envío automático falló` (con el error en el `title`), gris `Sin teléfono`, y en la pestaña Enviados `Automático`/`Manual`. Las alertas anteriores a esto tienen `canal = null` y no muestran chip, que es lo correcto: no se sabe.

**`POST /alertas/enviar-whatsapp` no va como botón en el Resumen.** Es la salida cuando el cron no corrió (`_debo_correr_scheduler()` se evalúa una sola vez al importar `main`, así que en un rolling deploy el proceso nuevo puede quedarse sin scheduler si el viejo sostiene el advisory lock). Exponerlo en la pantalla que el admin abre diez veces al día invita al doble envío.

**En los tests, `conftest.py` vacía `WA_PHONE_NUMBER_ID`/`WA_ACCESS_TOKEN`** — mismo motivo que con las `S3_*`, pero peor: con credenciales reales en `backend/.env`, un test le mandaría un WhatsApp de verdad a un socio. Los tests de envío usan `httpx.MockTransport`, **no** monkeypatch de `enviar_recordatorio` (mockear la función bajo prueba no probaría nada).

## Asistencia routers

**Modelo de acceso solo-entrada:** la palanquera solo controla el ingreso, así que el sistema **no registra salidas**. Cada marcación de huella crea una `Asistencia` con `tipo="entrada"` y pone `esta_en_gym=True`. El flag vuelve a `False` únicamente por tiempo (job `_job_reset_gym`), nunca por una marcación de salida. `_registrar()` en `asistencia.py` ya no alterna entrada/salida.

`backend/routers/asistencia.py` endpoints:
- `POST /asistencia/` — registra entrada por `huella_id` (bridge); valida membresía vigente (helper `_validar_membresia`)
- `POST /asistencia/por-usuario/{usuario_id}` — registra entrada por ID (bridge con `X-Bridge-Secret` o admin/coach JWT); valida membresía vigente en cada marcación
- `POST /asistencia/por-documento/{documento}` — acceso manual desde recepción: busca por cédula/TI, valida membresía y registra entrada; devuelve nombre, foto, `dias_restantes`. Usado por la vista `/acceso` (`AccesoView.vue`, admin/coach, enlace "Acceso Manual" en el sidebar — ver "AccesoView y modo kiosco"): tras el 201 el frontend abre la palanquera vía bridge (`POST localhost:8001/palanquera/abrir`), así que la apertura física solo funciona en la PC del gym; en otros equipos igual queda registrada la entrada. La vista incluye además la **apertura manual** como fallback al pie (ver "Apertura manual de palanquera"); el helper `abrirPalanqueraBridge()` es compartido por los dos caminos. Los códigos importan para la UI: **403** = membresía vencida, **404** = documento inexistente
- `GET /asistencia/mi-historial?meses=N` — historial propio (cualquier rol autenticado)
- `GET /asistencia/historial/{usuario_id}?meses=N` — historial de cualquier usuario (admin/coach)
- `GET /asistencia/en-gym` — usuarios con `esta_en_gym=True`, con `entrada_desde`, `minutos_transcurridos`, `minutos_restantes` y `minutos_sesion` (admin/coach)
- `GET /asistencia/sesiones-por-bloque?desde=&hasta=` — entradas agrupadas por (fecha, hora) en zona Bogotá; rango máx 31 días; deduplica por `usuario_id` dentro del mismo bloque conservando la primera entrada (admin/coach)

**El staff está exento de `_validar_membresia`.** Un admin/coach no paga plan y no tiene `fecha_vencimiento`, así que validarlo le daba un 403 en cada marcación; y como la palanquera **solo se abre cuando el backend responde 2xx**, al equipo del box la huella no le abría nunca por más que estuviera enrolado. La exención es el primer chequeo de la función. Dos consecuencias que hay que mantener:

- `dias_restantes` en `POST /por-documento` sale de `fecha_vencimiento`, que en el staff es `NULL`: va con guard, si no un coach marcando por cédula daba un 500. La respuesta trae `es_staff` para que `AccesoView` muestre "Equipo del box" en vez de "null días restantes / Invalid Date".
- **Los KPIs de asistencia de `/dashboard/resumen` cuentan solo `rol == CLIENTE`.** Hasta que existió esta exención el staff no podía marcar, así que esos números eran de clientes de facto; sin el filtro, un coach entrando a diario infla "asistencia de hoy" y le cambia el significado. Participación ya filtraba por rol. **El panel de sesiones por bloque sí los muestra**, a propósito: ahí la pregunta es quién estuvo en el box.

**Constante `MINUTOS_SESION`** (en `asistencia.py`): duración máxima de sesión usada tanto por `GET /en-gym` como por el job `_job_reset_gym` en `main.py`. Cambiar en un solo lugar.

**Auto-reset `esta_en_gym`:** el job `_job_reset_gym` (APScheduler, cada 3 min) usa un JOIN para obtener en una sola query los usuarios con `esta_en_gym=True` cuya última entrada supere `MINUTOS_SESION`, y los resetea a `False` sin crear registro de salida. Cubre el caso de usuarios que salen sin pasar por el torniquete. Implementado con subconsulta de `MAX(fecha_hora)` agrupada por `usuario_id` para evitar N+1.

## AccesoView (`/acceso`) — pantalla de recepción y modo kiosco

Ruta **top-level, fuera del shell de `Dashboard.vue`** (única excepción junto a `/login`): es la pantalla que queda abierta en la PC del mostrador con la sesión de un coach/admin, y los clientes escriben ahí su cédula. Si viviera como hija de `/` traería el sidebar y el cliente entraría al panel del staff con dos clics. Full-screen, con barra propia (logo + acciones). `meta: { requiresAuth: true, roles: ['admin','coach'] }` — al no heredar del padre, el `requiresAuth` va explícito.

**Modo kiosco (candado).** Flag `kioscoAcceso` en **`sessionStorage`**, manejado por `composables/useKiosco.js` (`kioscoActivo` ref para la UI, `kioscoBloqueado()` lee el storage directo para el guard, que corre antes de montar componentes).

**Por qué sessionStorage y no localStorage** (ya se rompió una vez así): localStorage se comparte entre todas las pestañas del mismo navegador, así que activar el kiosco en recepción bloqueaba también la pestaña donde el staff estaba trabajando. sessionStorage está aislado por pestaña → recepción queda bloqueada y el coach sigue en el panel desde otra pestaña con la misma sesión. Tampoco sirve un ref en memoria: sessionStorage **sobrevive al F5**, así que un cliente que recargue no se sale del kiosco. Lo que no sobrevive es cerrar la pestaña; se acepta a cambio del aislamiento. **No volver a localStorage.**

Mientras está activo:
- El guard de `router/index.js` devuelve a `/acceso` **toda** navegación de esa pestaña (URL a mano, botón atrás, F5).
- Se oculta "Volver al panel" y el fallback **"Abrir palanquera"** — ese botón abre la puerta *sin registrar entrada*, y a la vista de cualquier cliente sería la forma obvia de meter a un amigo.
- Salir exige la contraseña del staff logueado vía `POST /me/verificar-password`.

Activar pasa por un modal que explica las tres cosas (candado solo de esa pestaña, palanquera manual oculta, contraseña para salir). No es una confirmación de rutina: la duda "¿me bloquea todo el perfil?" es razonable y el modal la contesta antes de que aparezca.

**Sesión compartida:** el kiosco y la pestaña de trabajo usan el mismo JWT del localStorage. Si el staff **cierra sesión** en su pestaña, el token desaparece para las dos y el kiosco cae a `/login` en su próximo request. Cerrar sesión y volver a entrar exige reactivar el kiosco.

**Orden en el guard:** el bloque del kiosco va **después** del chequeo de token/login y **antes** de las reglas de rol. Si un rol no-staff queda logueado con el flag puesto, el guard lo desactiva en vez de redirigir: `meta.roles` rebotaría `/acceso` y las dos reglas se ciclarían. El flag también se limpia en el login exitoso (`LoginView`), en el logout (`Dashboard`) y en el interceptor 401 de `api.js`.

**Alcance real del candado:** frena el uso casual, que es el caso real (clientes en el mostrador). No frena a alguien que abra las devtools y saque el JWT del localStorage. La solución de fondo sería un token de kiosco con permiso solo para marcar asistencia — no está implementada.

**Cartel de resultado.** Con vigencia: foto, nombre grande y el número de días restantes en grande + fecha de vencimiento. Sin vigencia (403): solo **"Membresía vencida"** + "Acércate a recepción para renovar tu mensualidad" — **sin nombre ni fechas, a pedido explícito**; en un mostrador con fila detrás no se expone quién está en mora. Documento inexistente (404): "Documento no encontrado". El helper `_falloDesde(e)` traduce el status a ese cartel, así que **la distinción vive en el status code** y no hace falta detail estructurado en el backend. El resultado se autolimpia a los `SEGUNDOS_RESULTADO` (8 s) para que el siguiente de la fila no vea los datos del anterior.

**Deduplicación en sesiones-por-bloque:** los registros se ordenan por `fecha_hora` antes de agrupar. Si un usuario entró más de una vez en el mismo bloque (salió y volvió), solo aparece la primera entrada. Esto evita duplicados causados por re-entradas dentro del mismo bloque.

## SesionesPanel — consulta de sesiones por bloque horario

`frontend/src/components/SesionesPanel.vue`. **Ya no es una vista**: la ruta `/sesiones` y su enlace en el sidebar se eliminaron, y el panel se renderiza dentro del bloque Asistencia del Resumen (`/dashboard`).

**Layout de dos columnas** (`grid lg:grid-cols-5`, calendario `col-span-2` + sesiones `col-span-3`; apilado en móvil). **Los tres modos anteriores (esta semana / este mes / fecha específica) se eliminaron** — el calendario mensual los cubre a todos y evita tres caminos para la misma consulta. No re-introducir el selector de modo.

**Columna izquierda — calendario** (`lg:sticky lg:top-4`, sigue visible al scrollear las sesiones):
- Navegación ← → por mes (`mesOffset` ref, 0 = mes actual, no permite ir al futuro)
- Cada celda muestra número de día + badge rojo con total de asistentes (suma de `b.total` por fecha)
- Colores: hoy en negro, día seleccionado en rojo, días con datos en rojo suave, días sin datos en gris
- Pie con el total de asistencias del mes (`totalMes`)
- Estado: `bloquesMes`, `diaSeleccionado`, `cargandoMes`, `semanaMes` (computed que construye filas de 7 celdas con nulls para relleno)
- Helper `getMesInfo(offset)` devuelve `{ year, month }` para cualquier offset

**Columna derecha — sesiones del día:** grid de `BloqueCard` del día seleccionado + buscador por nombre. Si el día no tiene datos, muestra el empty state ahí mismo.

**El clic en un día siempre selecciona, nunca deselecciona** (antes alternaba): en dos columnas, deseleccionar dejaría media pantalla vacía sin ganar nada.

**Preselección al cargar un mes:** hoy si el mes visible es el actual; si no, el último día con datos. Una sola petición a `/asistencia/sesiones-por-bloque` por mes — cambiar de día filtra en cliente.

**`BloqueCard`** (`frontend/src/components/BloqueCard.vue`) — acordeón:
- Header clicable: bloque horario + badge de personas + chevron que rota al expandir
- Body (expandido): lista completa de asistentes con nombre y hora exacta (HH:MM)
- Inicia colapsado; sin límite de asistentes visibles (todos se muestran al expandir)

## UsuariosView — dos listados y paneles superiores

**Vocabulario de la UI: "cliente".** En texto visible no se dice ni "usuario" ni "socio" — el sidebar dice **Clientes**, el título de la vista también, y el bloque del Resumen igual. Rutas (`/usuarios`), endpoints, nombres de variables y de archivos siguen diciendo `usuario`: es la capa técnica y renombrarla sería un refactor sin beneficio. Al escribir copy nueva, "cliente". Dos excepciones deliberadas: los modales de **huella** dicen "persona" (se enrola también al staff, que no es cliente), y el **texto del contrato** en `TerminosModal.vue` no se toca sin bumpear `TERMINOS_VERSION`.

### Switch Clientes / Equipo del box

La vista tiene un `vista = ref('clientes')` que alterna dos listados sobre el mismo `GET /usuarios/` (una sola petición; el filtrado es en cliente vía los computed `clientes` y `equipo`). Son dos poblaciones con datos distintos: **al staff no le aplica la membresía** (no paga plan, no tiene `fecha_vencimiento`), así que esas columnas serían siempre "Sin membresía".

| | Clientes | Equipo del box |
|---|---|---|
| Filtra | `rol === 'cliente'` | `rol` admin o coach (admin primero, coaches por nombre) |
| Columnas | Usuario · Membresía · Estado · Acciones | Miembro · Contacto · Acciones |
| Buscador, filtros, orden, paginación | sí | no (son 2–5 filas) |
| Panel de cumpleaños | sí | no |
| Exportar Excel | sí | no — el endpoint exporta solo `rol == cliente` |

**Equipo no muestra Huella ni Desde.** "Desde" (`created_at`) era dato de archivo. La columna Huella se saca por espacio, no porque no sirva: **el staff sí marca huella y sí le abre la palanquera** (ver la exención en `_validar_membresia`). El enrolamiento de staff se hace desde `UsuarioPerfilView` (card "Huella digital"), que es el mismo camino que para un cliente — no hay atajo en el listado.

**Columna Membresía — el color vive en el punto, no en el texto.** `colorTextoDias()` devuelve `text-gray-900` mientras quede algún día y `text-red-600` solo cuando está vencida; el estado (verde/ámbar/rojo) lo da `colorPuntoDias()`. Colorear también el texto era doble codificación y convertía la columna en un tablero de alarmas con 15 filas en pantalla. Los dos helpers comparten el mismo umbral para que punto y texto nunca discrepen. La card móvil lleva el punto por la misma razón: sin él, con el texto neutro se quedaba sin señal de estado.

**Ningún listado muestra el rol.** En Clientes el listado ya está filtrado a `rol === 'cliente'`; en Equipo, como el admin es uno solo y todo lo demás son coaches, la columna tampoco discriminaba. `puntoRol()` de `paleta.js` quedó sin consumidores y se eliminó.

**Un solo admin — invariante del sistema.** El admin lo siembra `seed.py` desde las env vars `ADMIN_*` y es el único que existe: `POST /usuarios/` responde **403 si `rol == admin`**, sin importar quién pida (ni el propio admin). `PATCH /usuarios/{id}` no toca `rol`, así que tampoco hay ruta de promoción; la única escritura de rol fuera de la creación es `activar_pendiente`, que pone `CLIENTE`. Por eso el modal de creación **no tiene selector de rol**: el rol sale del contexto (Clientes → `cliente`, Equipo → `coach`, vía `abrirFormulario(staff)`). Cubierto por `test_nadie_puede_crear_otro_admin`.

**Tabs de Clientes:** Todos · **Activos** (membresía vigente) · **Inactivos** (vencida o sin membresía) · En el box ahora · Pendientes. Un pendiente es un cliente sin activar, por eso su tab vive acá.

**Pendientes usa el mismo patrón que el resto: tabla en desktop, cards en móvil.** Fue una grilla de tarjetas grandes con los seis datos de afiliación a la vista; con 20 o 40 registros era una pared de scroll. Ahora la fila muestra solo lo que decide (cliente, contacto, plan solicitado, fecha de registro) y el botón **Datos** despliega el resto —género, nacimiento, EPS, barrio, emergencia y, en menores, el bloque del acudiente— en `components/PendienteDetalle.vue`, compartido por la fila expandida y la card móvil. **No devolverlo a grilla de cards.**

**Descartar un pendiente:** la fila trae un botón de basurero que hace `DELETE /usuarios/{id}` — el mismo endpoint de siempre, sin ruta nueva: un pendiente no es staff, así que pasa los guards y admin y coach pueden borrarlo. Es para el registro que nunca se presentó, por eso la columna Registrado muestra también la antigüedad ("hace 42 días"), en gris hasta la semana, **ámbar** desde `PENDIENTE_AVISO_DIAS = 7` y **rojo** desde `PENDIENTE_VIEJO_DIAS = 15` (`colorAntiguedad()`): sin eso el admin tendría que restar fechas para decidir. Es la misma escala neutro → ámbar → rojo de la columna Membresía. En la card móvil el color va solo en la antigüedad, no en toda la línea. Borrar no bloquea nada — la persona puede registrarse de nuevo.

**Descartar varios de una:** `POST /usuarios/pendientes/eliminar` con `{"ids": [...]}`, **solo admin**. Filtra por `id.in_(ids)` **y** `rol == PENDIENTE`: ese `AND` es la propiedad de seguridad del endpoint — si entre los ids llega el de un cliente activo o el de un coach, se ignora en vez de borrarse, así un id equivocado no puede tumbar una cuenta real (cubierto por `test_eliminar_pendientes_ignora_a_los_que_no_son_pendientes`). En la UI: checkbox por fila, "seleccionar todo" de la página, y la acción rápida **"Seleccionar los de más de 15 días"**, que usa el mismo `PENDIENTE_VIEJO_DIAS` del color — lo que se ve en rojo es exactamente lo que se preselecciona. La selección es un `Set` en un `ref` (hay que **reasignarlo**, no mutarlo, para que Vue reaccione) y sobrevive al cambio de página. El modal de confirmación lista **todos** los seleccionados con scroll: confirmar un borrado masivo mirando solo un contador es justo donde se cuela el error.

**La confirmación de borrado es un modal, no el `confirm()` nativo** (que es lo que había): la acción es irreversible y el modal muestra foto, nombre y email de quien se va a borrar. `confirmarEliminar(user, esPendiente)` lo abre; el segundo parámetro existe porque el payload de `/usuarios/pendientes` no trae `rol` y al terminar hay que refrescar `fetchPendientes()` y no `fetchUsuarios()`. Lo usan los tres listados de la vista.

**Una sola paginación para las dos listas de la vista Clientes.** `listaFiltrada` elige entre `usuariosFiltrados` y `pendientesFiltrados` según el tab, y `paginaItems` (antes `usuariosPagina`) la rebana; el bloque de paginación vive fuera de los dos listados. Solo se renderiza uno a la vez y el `watch` de `filtroActivo` resetea a la página 1, así que no hace falta un segundo estado. El buscador ahora sí filtra pendientes (nombre y documento); el orden en ese tab es fijo —el más reciente primero— y por eso el selector "Ordenar por" sigue oculto ahí.

Ojo con las claves, porque "activo" significa dos cosas distintas en esta pantalla: `key: 'activos'` filtra por **membresía vigente** (`tieneMembresia`), mientras que el que está físicamente en el gym es `key: 'en_box'` (`esta_en_gym`). La clave `'activos'` antes era la del box y `'membresia'` la de vigencia — se intercambiaron para que el nombre del tab y el del dashboard coincidan. La columna Estado de la tabla sigue rotulando `esta_en_gym` como "Activo/Fuera", que es otro eje.

**Permisos (frontend espejando al backend):** el admin gestiona el equipo, el coach solo lo consulta. El botón "Nuevo miembro del equipo" y el de eliminar staff se muestran solo con `isAdmin`. El helper `puedeEliminarStaff(u)` refleja los guards del router.

**Modal de creación contextual:** es el mismo modal para ambos casos. Desde Clientes precarga `rol: 'cliente'` y muestra el bloque de plan; desde Equipo (`creandoStaff`) precarga `rol: 'coach'`, saca "Cliente" del select y **oculta el bloque de Plan de Membresía**. Abrirlo siempre pasa por `abrirFormulario(staff)`, nunca por `showForm = true` suelto.

**`miId`:** el id propio no está en `localStorage`, así que la vista lo pide a `GET /me` al montar. Se usa para no ofrecer el botón de eliminar en la fila propia (y para el sufijo "(vos)").

### Guards de `DELETE /usuarios/{id}`

Tres capas, en este orden (el orden importa: el de auto-borrado va primero para que un coach borrándose a sí mismo reciba 400 y no 403):
1. 404 si no existe.
2. **400 si es tu propia cuenta** — aplica también al admin, que si no podría dejar el sistema sin administración.
3. **403 si el objetivo es staff y quien pide no es admin** (`_ROLES_PRIVILEGIADOS`), mismo criterio que POST y PATCH.

Cubierto por `test_coach_no_puede_eliminar_admin`, `test_coach_no_puede_eliminar_otro_coach`, `test_coach_si_puede_eliminar_cliente`, `test_admin_puede_eliminar_coach` y `test_nadie_puede_eliminarse_a_si_mismo` en `tests/test_usuarios.py`.

### Paginación y orden (solo vista Clientes)

`POR_PAGINA = 15`, paginación en cliente sobre `usuariosFiltrados`. El control solo aparece con más de 15 resultados y colapsa con elipsis pasadas las 7 páginas. Buscar, cambiar de tab o cambiar el orden resetea a la página 1; un `watch` sobre `totalPaginas` reencuadra si la lista se achica (p. ej. al eliminar). El selector "Ordenar por" ofrece nombre A–Z/Z–A, vencimiento (primero/último) y fecha de registro (reciente/antiguo); los usuarios sin fecha van siempre al final vía el helper `_sinFechaAlFinal`. `usuariosFiltrados` hace `slice()` antes de `sort()` porque sin filtros la lista **es** `usuarios.value` y `sort` muta en sitio.

### Cumpleaños

El panel de cumpleaños **ya no vive acá**: se movió al dashboard (`/dashboard`). El endpoint `GET /usuarios/cumpleanos-hoy` se eliminó al quedar sin consumidores; el criterio (cumple hoy **y** `fecha_vencimiento >= hoy`) vive en el helper `query_cumpleaneros_hoy(db)` de `routers/usuarios.py`, que ahora usa solo `GET /dashboard/resumen`. Sus casos borde (vencido y otro día) se cubren en `test_resumen_incluye_cumpleaneros`.

### Exportar Excel

Botón "Exportar Excel" en el header de `UsuariosView` (admin/coach) → `GET /usuarios/exportar-excel` (en `usuarios.py`, declarado antes de `/{usuario_id}`). Genera un `.xlsx` con **openpyxl** (en `requirements.txt`) con todos los clientes (rol `cliente`) y sus 23 columnas: identidad, contacto, EPS/barrio, emergencia, acudiente, membresía (estado/vence/días), huella, términos y fecha de registro. El frontend lo descarga con `responseType: 'blob'` + link temporal.

### Panel "En el box ahora"

El filtro "En el box ahora" en la tabla de usuarios usa `enGym` (ref), cargado con `GET /asistencia/en-gym` al montar y refrescado cada 10 segundos via `gymInterval`. No hay panel visual separado ni countdown — el panel de chips con temporizador fue eliminado.

## Mi Salud — health metrics

Per-measurement routing: each metric has its own page at `/salud/:tipo`. **Excluida del rol `admin`** — el router restringe `/salud` y `/salud/:tipo` a `roles: ['coach', 'cliente']`. El admin no ve esta sección en el sidebar ni puede entrar por URL directa.

**Measurement types** (defined in `frontend/src/data/saludTipos.js`):
`peso`, `altura`, `cintura`, `cuello`, `cadera`, `brazos`

Agregar una medida nueva = un objeto en `saludTipos.js` (la card en `SaludView` y la página `/salud/:tipo` se generan solas vía `v-for`/`find`) + la columna en el modelo + la migración en `main.py` (**ambos** bloques: SQLite `ALTER TABLE` y Postgres `ADD COLUMN IF NOT EXISTS`, ver "Migraciones de arranque") + la entrada en `CAMPOS` (router) + el campo en `MedidaResponse` (schema).

**Backend router** (`backend/routers/salud.py`):
- `CAMPOS = { "peso": "peso_kg", "altura": "altura_cm", "cintura": "cintura_cm", "cuello": "cuello_cm", "cadera": "cadera_cm", "brazos": "brazos_cm" }`
- `GET /salud/` — all records for the current user (overview)
- `GET /salud/{tipo}` — records filtered by measurement type
- `POST /salud/{tipo}` — creates a record with only that field set
- `DELETE /salud/{medida_id}` — deletes by integer ID

**Model** (`MedidaSalud` in `backend/models.py`): all measurement columns are nullable (`Optional[float]`). La columna `imc` NO la calcula el backend (queda NULL): el IMC lo calcula el frontend (`SaludView.imcActual`) con el último peso y la última altura.

**Views:**
- `SaludView.vue` — overview; 5 RouterLink cards + IMC banner, no modal
- `SaludMedidaView.vue` — detail per tipo; Chart.js line chart, history table with delete, add modal

## Mis Marcas — personal records

Per-exercise routing: each exercise has its own page at `/marcas/:ejercicio`. **Excluida del rol `admin`** — el router restringe `/marcas` y `/marcas/:ejercicio` a `roles: ['coach', 'cliente']`.

### Tipos de ejercicio

No todo se mide igual. La lista en `frontend/src/data/ejerciciosMarcas.js` etiqueta cada ejercicio con un `tipo`, y tanto el frontend como el backend bifurcan la lógica según ese tipo. La fuente de verdad es ese archivo del frontend; el backend duplica la clasificación en `TIPOS_EJERCICIO` dentro de `routers/marcas.py` — **mantener ambos en sincronía**.

| Tipo | Ejercicios | Métrica | Campos usados |
|---|---|---|---|
| `barra` | Back Squat, Deadlift, Clean, Clean and Jerk, Snatch, Bench Press, Press Militar | 1RM (fórmulas) | `peso`, `unidad`, `repeticiones`, `rm_calculado` |
| `corporal_lastre` | Dominadas | 1RM (fórmulas) sobre peso total | `peso` (corporal + lastre, snapshot), `peso_adicional` (lastre opcional), `repeticiones`, `rm_calculado` |
| `reps` | Push Up, Air Squat, Sit Up | Max reps | solo `repeticiones` |
| `leger` | Test de Léger | Mayor nivel (desempate por palier) | `nivel`, `palier` |

**Corporal+lastre (Dominadas):** el frontend jala el último `peso_kg` de Mi Salud (`GET /salud/peso`) como peso corporal automático. Si el usuario no tiene registros de salud, lo pide manual. El total `peso_corporal + peso_adicional` se guarda en `peso` como snapshot (no se recalcula a futuro si el usuario cambia de peso). 1RM se calcula sobre ese total.

**1RM formulas** (7 usadas, promediadas, solo para `barra` y `corporal_lastre`): Brzycki, Epley, Lander, O'Connor, Lombardi, Mayhew, Wathen. El promedio se guarda en `rm_calculado`. Helper backend: `_calcular_1rm(peso, reps)` en `routers/marcas.py`.

### Backend

**Router** (`backend/routers/marcas.py`):
- `GET /marcas/` — todos los registros del usuario actual
- `GET /marcas/{ejercicio}` — registros del ejercicio (URL-encoded)
- `POST /marcas/` — payload flexible; el router despacha según `_tipo_de(ejercicio)` y valida los campos requeridos por tipo (rechaza con 422 si faltan). Calcula `rm_calculado` solo para `barra` y `corporal_lastre`.
- `PATCH /marcas/{marca_id}` — edita un registro existente del usuario; aplica la misma lógica de validación y cálculo que POST.
- `DELETE /marcas/{marca_id}`

**Modelo** (`MarcaRM` en `models.py`): `usuario_id`, `ejercicio`, `unidad` (default `"kg"`), `fecha`, `notas`, `created_at` son siempre obligatorios. Todos los demás campos son nullable y se llenan según el tipo: `peso`, `repeticiones`, `rm_calculado`, `peso_adicional`, `nivel`, `palier`. La migración en `main.py` reconstruye la tabla para hacer nullable `peso`/`repeticiones`/`rm_calculado` (antes eran NOT NULL) y agrega las columnas nuevas vía `ALTER TABLE` (recordá los **dos** bloques SQLite + Postgres, ver "Migraciones de arranque").

**Schema** (`schemas/marcas.py`): `MarcaRMCreate` tiene todos los campos de tipo opcional para soportar los 4 flujos. La validación dura sucede en el router.

### Frontend

**`MarcasView.vue`** — listado de los 12 ejercicios: **tabla en desktop, cards en móvil** (`sm:hidden` / `hidden sm:block`), mismo patrón que `EjerciciosView` y el listado de Clientes. Era un grid de cards grandes; con 12 filas fijas que nunca cambian eran tres pantallas de scroll para lo que entra en una. **No devolverlo a grid.** Columnas: Ejercicio · Mejor marca · Registros · Última. La fila entera es clicable (`@click` → `irA()`), pero el nombre va como `RouterLink` con `@click.stop` — así sigue siendo un enlace real (teclado, abrir en pestaña nueva) y el `.stop` evita la navegación duplicada.

Buscador por nombre, **sin chips de filtro por tipo**: con 12 ejercicios los chips solo esconderían filas. Los ejercicios sin registros muestran `—` en las tres columnas de datos.

El "Mejor marca" sale del computed `resumen`, **un solo recorrido de `/marcas/`** que arma un `Map` por ejercicio con `{ valor, unidad, conteo, ultima }` (antes eran funciones que filtraban la lista entera 3 veces por card):
- `barra`/`corporal_lastre`: 1RM + unidad (normalizado a kg para comparar entre kg/lbs, pero se muestra en la unidad del registro)
- `reps`: número + "reps"
- `leger`: `nivel N.P`

**`useSessionMarca` se eliminó**, junto con el badge `⏱ Ns` de "sesión en curso" del sidebar de `Dashboard.vue`. Desde que el registro pasó a ser directo por serie nadie llamaba a `iniciarSesion()`, así que no se podía crear una sesión nueva — pero el composable seguía leyendo la clave `jain_sesion_marca` del localStorage al arrancar, y a quien la tuviera guardada de la versión vieja le quedaba un chip permanente de "N series en progreso" que al clickearlo llevaba a una vista donde esas series ya no existían.

**`MarcasEjercicioView.vue`** — UI condicional según `tipo`:
- Resumen: muestra "Último vs PR" según tipo (1RM, max reps, o nivel.palier). "Último 1RM" refleja el mejor del día más reciente (via `registrosPorDia`).
- Gráfica: evolución del 1RM, repeticiones, o nivel (puntos PR resaltados en oro). Para `barra`/`corporal_lastre` usa `registrosPorDia` — un punto por día con el mejor 1RM de ese día.
- Tabla rep-max y comparación de fórmulas: solo para `barra`/`corporal_lastre`
- Historial: encabezados y formato de celda cambian por tipo. Botones **editar** (lápiz azul) y **eliminar** (basurero rojo) siempre visibles en cada fila. En móvil se oculta la columna Notas.
- **Registro para `barra`/`corporal_lastre`:** panel de adición directa (ver sección abajo).
- **Registro para `reps`/`leger`:** modal con campos específicos (`reps`: solo repeticiones; `leger`: nivel + palier).
- **Editar registro:** botón lápiz en historial abre el modal precargado con los datos del registro. `guardar()` llama `PATCH /marcas/{id}` si edita, `POST /marcas/` si es nuevo.

**Helper compartido:** `tipoDe(nombre)` en `ejerciciosMarcas.js`.

### Registro directo por serie (`barra` / `corporal_lastre`)

Para ejercicios de peso, cada serie se guarda **inmediatamente** al presionar `+`. No hay sesión persistente ni localStorage.

**Panel de adición directa (inline en `MarcasEjercicioView.vue`):**
- Siempre visible debajo del resumen.
- Toggle kg/lbs, campo peso (o lastre adicional para Dominadas), campo reps, botón `+` (o Enter).
- Para `corporal_lastre`: muestra peso corporal auto (de Mi Salud) o input manual; pesoTotal = corporal + lastre.
- Al presionar `+`: POST `/marcas/` con `{ ejercicio, fecha: hoy, unidad, series: [{ peso, repeticiones }] }`. Un registro por serie.
- Mini-lista "Hoy · N series" muestra las series ya guardadas ese día (filtradas de `registros` por fecha).

**Computed `registrosPorDia`** — agrupa los registros por fecha tomando el de mayor `rm_calculado` por día. Usado para `ultimoRM`/`ultimaUnidad` (resumen). **La gráfica NO lo usa**: plotea cada serie (registro) como punto propio ordenado por (fecha, id), para que cada peso agregado se refleje de inmediato; renderiza desde 1 solo registro. El historial sigue mostrando cada registro individual.

## WODs — módulo completo

### Modelo `WOD` — campos relevantes

| Campo | Tipo | Descripción |
|---|---|---|
| `activo` | `Boolean` (default `True`) | `True` → aparece en "WODs Activos"; `False` → aparece en "Historial de WODs" |
| `es_personalizado` | `Boolean` (default `False`) | Distingue WODs regulares de personalizados |
| `genero_destino` | `String(20)`, nullable | `"masculino"` \| `"femenino"` — solo para personalizados |
| `tipo` | `String(50)`, nullable | Formato del WOD: `"For Time"` \| `"AMRAP"` \| `"EMOM"` \| `"Por Rondas"` \| `"Fuerza"` \| `"Otro"` |

### Rutina en notas + lista de videos

**La rutina completa va en texto libre en `WOD.descripcion`** (label "Notas de la rutina" en el form): rondas, ejercicios, reps, peso, tiempos y escalas. Los `wod_ejercicios` **no** prescriben nada: son solo la **lista de videos** que el coach quiere que el cliente vea, referenciando el catálogo de `ejercicios` (nombre + `video_url` + categoría) y guardando únicamente `ejercicio_id` + `orden`.

Las columnas `notas`, `rep_min`, `rep_max`, `rir`, `porcentaje_rm`, `tiempo_segundos` y `superserie_con_anterior` de `wod_ejercicios` son **legacy**: siguen en la tabla por los WODs históricos, pero no se escriben (`_aplicar_ejercicios` no las setea) ni se serializan (`WODEjercicioResponse` no las expone). El payload de `WODEjercicioItem` las ignora si un cliente viejo las manda — hay un test que lo cubre. No re-agregarlas: el modelo de prescripción por campos se retiró a propósito porque la rutina vive en las notas.

- **Editor** (`WodVideosEditor.vue`): chips de filtro por categoría + select del catálogo + lista ordenable (subir/bajar/quitar). Los ejercicios sin `video_url` se pueden agregar pero se marcan `· sin video` en el select y con badge ámbar en la lista.
- **Render** (`WodVideosLista.vue`): lista numerada con nombre, descripción del catálogo y botón "Ver video" (solo si hay `video_url`). Prop `videos` (no `ejercicios`) y flag `dark`. Consumidores: `WodsView`, `WodsPersonalizadosView`.

### Separación activo / historial

El campo `activo` es la distinción principal entre secciones (NO la fecha):
- `activo=True` → sección **"WODs Activos"** (visible para todos los roles)
- `activo=False` → sección **"Historial de WODs"** (solo admin/coach)

Al hacer toggle, el WOD se mueve entre secciones instantáneamente en el frontend sin recargar.

**`GET /wods/`** acepta `activo: Optional[bool]` y `skip: int` para filtrar y paginar. Sin el parámetro `activo`, staff ve todos; clientes solo ven `activo=True`.

### WodsView — vista regular

Ruta `/wods` (todos los roles autenticados).

**Sección "WODs Activos":** fetch `GET /wods/?activo=true&limit=50`. Dark cards con badge del tipo (si existe). Staff ve botones de toggle (mover a historial), editar y eliminar.

**Sección "Historial de WODs":** solo staff. Fetch `GET /wods/?activo=false&limit=30`. Lista plana con "Última fecha" bajo el nombre, badge del tipo, buscador por nombre y chips de filtro por tipo. Paginado con "Cargar más" (skip/limit). El botón de toggle restaura el WOD a activos.

**Chips de filtro en historial:** Todos / For Time / AMRAP / EMOM / Por Rondas / Fuerza / Otro. Se combinan con el buscador de texto. "Cargar más" se oculta cuando hay filtro activo.

### WodsPersonalizadosView — vista personalizada

Ruta `/wods/personalizados` (roles: `admin`, `coach`, `cliente`). `GET /wods/personalizados` acepta `activo: Optional[bool]` para staff.

**Vista Staff (admin + coach):**
- Stats: conteo de WODs activos por género (masculino / femenino)
- Sección "WODs Personalizados Activos": dark cards con badge de género + badge de tipo
- Sección "Historial de Personalizados": lista plana con badge de género + badge de tipo, buscador y chips de filtro por tipo
- Botón "Nuevo WOD" visible para admin y coach

**Vista Cliente:** solo ve WODs activos filtrados por su género (el backend filtra). Sección "Tu WOD de Hoy" (fecha actual) + "Historial" (fechas anteriores).

El filtro de género en el frontend usa `localStorage.getItem('userGenero')`. El sidebar muestra el enlace a staff (admin/coach) y a clientes con plan que lo incluya.

**Backend:** `GET /wods/personalizados` retorna todos los WODs para `admin` o `coach`; para clientes filtra por género y `activo=True`. `POST /wods/` permite crear personalizados a admin y coach (antes era solo admin).

### WodFormView — formulario

Ruta `/wods/nuevo` y `/wods/:id/editar` (admin/coach). Soporta WODs regulares y personalizados vía `route.meta.personalizado`. Rutas de personalizados (`/wods/personalizados/nuevo`, `/wods/personalizados/:id/editar`) accesibles para admin y coach.

Campos del form: `titulo`, `fecha`, **`tipo`** (select con 6 opciones, opcional), `descripcion` (textarea grande, "Notas de la rutina" — acá va la rutina completa), `activo` (toggle), `ejercicios` = lista de videos (via `WodVideosEditor`). Para personalizados en modo creación: selección múltiple de género (masculino / femenino), crea un WOD por género seleccionado.

### Catálogo de ejercicios

**Modelo `Ejercicio` — dos campos y nada más: `nombre` y `video_url`.**

Tuvo también `categoria` (`Cardio`/`Fuerza`/`Gimnasia`/`Olímpico`/`Otro`) y `descripcion`, y se eliminaron: lo que el coach necesita al armar un WOD es encontrar el ejercicio por nombre y tener el video a mano. **Las columnas NO se dropearon de la base** — siguen ahí con sus datos, el modelo simplemente no las mapea, así que volver atrás es re-agregar dos líneas en `models.py`. Por eso tampoco están en los bloques de migración de `main.py`: en una base nueva no se crean, y en una existente no se tocan.

Lo que se fue con ellas: el filtro `?categoria=` de `GET /ejercicios/`, la property `WODEjercicio.descripcion` y su campo en `WODEjercicioResponse`, los chips de filtro de `EjerciciosView` y `WodEjerciciosEditor`, y la escala categórica entera de `paleta.js` (ver "Paleta de colores").

**`EjerciciosView.vue`** (admin/coach):
- **Tabla** (desktop) + cards (móvil), mismo patrón responsive que el listado de Clientes. Columnas: Ejercicio · Video · Acciones. Era un grid de cards de 3 columnas; con el catálogo pasando de 27 ejercicios se volvió scroll inútil, y esta pantalla se usa para *buscar* uno y editarlo, no para explorar.
- **Sin paginación ni selector de orden**: el buscador ya acota, y `GET /ejercicios/` devuelve ordenado por nombre (alfabético es el orden correcto para buscar). No replicar acá el `ORDENES`/paginación de `UsuariosView`.
- Sin video, la celda muestra `—`. El modal de crear/editar tiene dos campos: nombre y link del video.

**Videos del catálogo sembrado:** `EJERCICIOS_DEFAULT` en `seed.py` son tuplas de 2 (`nombre, video_url`) con demos del canal oficial de CrossFit. Los comentarios de sección (`# ── Olímpico ──`) son solo para leer la lista cómodo; ya no hay una columna detrás. **Las URLs se obtienen buscando en la web y verificando cada una** (que la página cargue y el título corresponda al movimiento); nunca de memoria — los IDs de YouTube son el caso típico de dato que se alucina y termina en link muerto o en otro ejercicio.

Para las bases **ya sembradas** hay que correr `backend/scripts/backfill_videos.py`: `seed_ejercicios()` se corta apenas la tabla tiene filas, así que no las alcanza. El script es idempotente (solo toca `video_url` vacío, matchea por nombre) y usa el `DATABASE_URL` del entorno — **confirmar contra qué base se está corriendo antes de ejecutarlo**. No se puso como bloque de arranque en `main.py` a pesar de que ahí viven otras limpiezas de datos: correría en cada boot y le devolvería el video a un ejercicio al que el coach se lo borró a propósito (el form guarda el vacío como `NULL`).

**`WodVideosEditor.vue`** (componente de selección al crear/editar un WOD): select de los videos disponibles (los ya agregados se excluyen) + reordenar y quitar. Los chips de filtro por categoría y el badge junto al nombre se eliminaron con la columna `ejercicios.categoria`; el select queda ordenado alfabéticamente, que con un catálogo de ~27 nombres alcanza para encontrar el video.

## Planes por ingresos (bonos)

Un plan puede cobrarse **por tiempo** (mensualidad de toda la vida) o **por ingresos** (bono de N entradas). Lo define `Plan.numero_ingresos`: `NULL` → por tiempo, `N` → bono de N entradas.

**Son dos ejes de vigencia y se validan los dos** (`_validar_membresia` en `asistencia.py`): un bono caduca cuando se acaban las entradas **o** cuando pasa `fecha_vencimiento`, lo que ocurra primero. `Plan.duracion_dias` sigue aplicando a los dos tipos.

**`Usuario.ingresos_restantes` usa `NULL` como centinela de "no aplica"**, no `0`. Sin ese centinela habría que mirar el último plan del socio en cada marcación para saber si descontar: un cliente con mensualidad tendría `0` ingresos y sería indistinguible de un bono agotado.

**Toda la lógica vive en `backend/membresia.py`**, no en los routers. Hay **cuatro caminos** que aplican o revierten un plan (`POST /pagos/`, `POST /pagos/directo/`, `POST /usuarios/{id}/activar` y `DELETE /pagos/{id}`); con la regla escrita en cada uno, olvidarse de uno deja socios con ingresos que nadie descuenta. Las funciones son `aplicar_plan`, `extender_vencimiento`, `revertir_plan` y `descontar_ingreso`.

| Situación | Qué pasa con `ingresos_restantes` |
|---|---|
| Paga un plan por ingresos | **Se suman** a los que le quedaban (mismo criterio que la fecha, que se extiende en vez de pisarse) |
| Paga un plan por tiempo | Vuelve a `NULL`. **Sin este reset**, un socio con un bono agotado (`0`) quedaría bloqueado pese a acabar de pagar la mensualidad |
| Pago directo (personalizado) | No los toca: no hay plan detrás que defina ingresos |
| Marca entrada | `descontar_ingreso()` resta 1, y solo si no es `NULL`. Va en `_registrar()` porque los tres caminos de entrada (huella, por id, por documento) pasan por ahí |
| Se anula el pago | Se restan los ingresos que cargó. **Limitación:** si el pago anulado era por tiempo, los ingresos previos se perdieron al ponerse en `NULL` y no se pueden restaurar |

**El acceso denegado por falta de ingresos manda `detail` estructurado** (`{"codigo": "sin_ingresos", ...}`) mientras que el vencido manda un string. Los dos son 403, pero en el mostrador son problemas distintos —"renová la fecha" vs "comprá más entradas"— y `AccesoView` los pinta distinto. Es la excepción a la regla de que la distinción vive en el status code.

**En el form de planes, `numero_ingresos: 0` significa "volver a plan por tiempo".** El `PATCH` no puede usar `null` para eso: lo interpretaría como "campo no enviado" y no lo cambiaría. Por eso `PlanUpdate` acepta `ge=0` y el router hace `payload.numero_ingresos or None`.

**Limitación conocida — el Resumen no descuenta los bonos agotados.** `/dashboard/resumen` cuenta activos por `fecha_vencimiento >= hoy`, así que un socio con 0 ingresos y fecha vigente sigue contando como activo. No se corrigió a propósito: `socios-mensuales` reconstruye el pasado desde `pagos` (donde no hay registro de cuántos ingresos se gastaron) y hay un test que exige que su último punto coincida con la tarjeta de activos. Arreglar solo la tarjeta rompería esa coincidencia; arreglar los dos requiere historial de consumo, que hoy no existe.

## Métodos de Pago

Tabla `metodos_pago` — cuentas bancarias / transferencia que el admin expone en la pantalla de planes para que los usuarios sepan a dónde pagar.

**Modelo** (`MetodoPago` en `models.py`): `banco`, `tipo_cuenta` (ahorros, corriente, nequi, daviplata…), `numero_cuenta`, `orden` (int para ordenar), `activo` (bool), `created_at`.

**Router** (`backend/routers/metodos_pago.py`, prefix `/metodos-pago`):
- `GET /metodos-pago/` — lista los activos ordenados por `orden` asc. Visible para cualquier usuario autenticado.
- `POST /metodos-pago/` — crea uno nuevo; asigna `orden` al final. Solo admin.
- `PATCH /metodos-pago/{id}` — actualiza banco, tipo_cuenta, numero_cuenta, orden o activo. Solo admin.
- `DELETE /metodos-pago/{id}` — elimina. Solo admin.

Los schemas Pydantic (`MetodoPagoCreate`, `MetodoPagoUpdate`) están definidos inline en el router (no hay archivo separado en `schemas/`).

## Servicio Biométrico (Bridge .NET)

### Arrancar el bridge

Lo más simple: usar el launcher de la raíz (`start-dev.ps1`) — lanza el bridge con UAC junto con backend y frontend.

Manual:
```powershell
# Compilar
dotnet build servicio_biometrico\HuelleroBridge.csproj

# Ejecutar — DEBE correrse como Administrador (acceso al driver USB)
Start-Process -FilePath "servicio_biometrico\bin\Debug\net48\HuelleroBridge.exe" -Verb RunAs
```

**Logs en vivo:** `servicio_biometrico\ver-logs.cmd` (tail coloreado de `bridge.log`).

**A qué backend apunta:** por defecto el bridge habla con el **backend de producción** — ver `BridgeConfig.cs`. Para apuntarlo a un backend local en dev, definir `JSB_API_BASE=http://localhost:8000` antes de arrancarlo. `ApiBase`/`BridgeSecret` son `static readonly` (se leen **una sola vez** al iniciar), así que tras cambiar la env var hay que **reiniciar el bridge**. Si el enrolamiento falla con `Excepción al guardar template: Error al enviar la solicitud` (un `HttpRequestException` de conexión, no de TLS), casi siempre es que `ApiBase` apunta a un backend que no responde — confirmar con la línea `[CONFIG] ApiBase` del log al arrancar.

### Por qué .NET y no Python

El SDK de DigitalPersona U.are.U 4500 ("One Touch for Windows .NET Edition") solo expone DLLs COM para .NET Framework x86. No hay bindings para Python.

### Requisitos críticos de arquitectura

- **`new Capture(Priority.High)`**: el SDK por defecto usa `Priority.Normal`, que solo entrega eventos cuando la ventana vinculada al hilo tiene foco. Como `BridgeForm` está oculta y nunca toma foco, con Normal **no llega ningún evento**. La propiedad `Priority` es read-only y debe pasarse por constructor (`new Capture(Priority.High)` en `FingerprintCapture.cs`). Ésta es la pieza que habilita la captura en background; sin esto ningún truco de message pump alcanza.
- **`[STAThread]` + `Application.Run(form)`**: el SDK usa COM para despachar eventos (`OnComplete`, `OnFingerTouch`, etc.) a través del message pump de Windows. Sin un hilo STA con message pump activo, los eventos nunca se entregan aunque el lector esté conectado. La solución es `[STAThread]` en `Main` y `Application.Run(new BridgeForm(...))`.
- **`BridgeForm`**: ventana invisible (off-screen a -32000,-32000, `Opacity=0`, `ShowInTaskbar=false`) que provee el HWND necesario para el message pump COM. El `FingerprintCapture` se inicializa en `OnLoad` (después de que el HWND existe). La invisibilidad es solo estética — la captura background depende de `Priority.High`, no de la posición de la ventana.
- **x86**: el proyecto está fijado a `PlatformTarget=x86` porque las DLLs del SDK son de 32 bits.

### Cosas que NO resuelven el problema de background (no agregar)

Históricamente se agregaron varios trucos buscando captura en background antes de descubrir `Priority.High`. Ya fueron eliminados de `Program.cs`. **No los re-introduzcas** salvo que tengas evidencia concreta de un problema distinto:

- `SetProcessInformation` con `PROCESS_POWER_THROTTLING_EXECUTION_SPEED` (opt-out de EcoQoS de Win11) — el throttling no era la causa.
- `Process.PriorityClass = AboveNormal` — el problema no era prioridad de proceso.
- `DeshabilitarQuickEdit` (manipular `ENABLE_QUICK_EDIT` del stdin) — irrelevante porque `FreeConsole()` libera la consola al arrancar.

Lo único conservado en `Program.cs` además del shell WinForms es `SetThreadExecutionState(ES_SYSTEM_REQUIRED)` para evitar que la PC del gym se duerma sola.

### Archivos del bridge

| Archivo | Rol |
|---|---|
| `Program.cs` | Entry point `[STAThread]`; redirige logs a `bridge.log`, suelta consola con `FreeConsole`, levanta WebSocket/HttpApi/BridgeForm. Al arrancar loguea `[CONFIG] ApiBase` y `[CONFIG] BridgeSecret` (definido/vacío) — primer log a revisar si el enrolamiento o las asistencias fallan. |
| `BridgeForm.cs` | Ventana WinForms invisible (HWND para message pump COM); crea `FingerprintCapture` en `OnLoad` |
| `BridgeConfig.cs` | Config por entorno (fuente única): `ApiBase` (env `JSB_API_BASE`, **default = backend de producción**; definir `JSB_API_BASE=http://localhost:8000` para apuntar a un backend local en dev) y `BridgeSecret` (env `BRIDGE_SECRET`, default `jain_bridge_secret_2024`). Referenciado por `FingerprintCapture` y `HttpApi`. |
| `FingerprintCapture.cs` | Implementa `DPFP.Capture.EventHandler`; instancia `new Capture(Priority.High)` para captura en background; maneja enrolamiento, verificación y acceso. Incluye cooldown de `CooldownSegundos` (4 s) por usuario en modo acceso para evitar doble-registro cuando el usuario pone el dedo varias veces seguidas. Dispara la palanquera vía `RelayController.Abrir()` cuando el backend confirma una **entrada** (no en salida). |
| `RelayController.cs` | Abre la palanquera mandando el byte `'A'` por USB-serial a un Arduino UNO. Ver sección "Palanquera (relé + Arduino)" más abajo. |
| `arduino/palanquera_rele/palanquera_rele.ino` | Sketch del Arduino UNO que controla el módulo de relé. |
| `ver-logs.ps1` / `.cmd` | Tail coloreado de `bridge.log` en vivo |
| `instalador/` | Paquete para instalar el bridge en una PC nueva: `INSTALAR.cmd`, `LEEME.txt` y `empaquetar.ps1`. Ver "Instalador del bridge" más abajo |
| `EnrollmentState.cs` | Estado compartido (thread-safe con `lock`) entre captura y HTTP API |
| `HttpApi.cs` | `HttpListener` en puerto 8001; endpoints REST consumidos por el frontend. Recibe el `RelayController` (vía `BridgeForm.Relay`) para la apertura manual de palanquera. |
| `WebSocketHub.cs` | Servidor WebSocket en puerto 8765 (Fleck); broadcast de eventos en tiempo real |
| `HuelleroBridge.csproj` | net48 x86; referencia DLLs SDK desde `C:\Program Files\DigitalPersona\One Touch SDK\.NET\Bin\` |

### Instalador del bridge (PC nueva)

`servicio_biometrico/instalador/` — versionado a propósito. **El paquete se arma con `empaquetar.ps1`, nunca a mano:** el instalador que se armaba copiando archivos quedó con un exe de un mes antes apuntando a un backend ya dado de baja, y el síntoma en la PC nueva no era un error claro sino "el lector no reconoce a nadie". El script toma el exe de `bin/Debug/net48` y **aborta si algún `.cs` es más nuevo que el binario**.

```powershell
dotnet build servicio_biometrico\HuelleroBridge.csproj
.\servicio_biometrico\instalador\empaquetar.ps1 -Zip      # → dist\HuelleroBridge-Instalador(.zip)
```

Imprime a qué backend apunta el exe, **leído del binario**, que es exactamente el dato que estuvo mal. El RTE de DigitalPersona (19 MB, redistribuible de un tercero) **no está en git**: se copia de `-RteOrigen`, que por defecto apunta al paquete viejo en `~\Downloads`. Si esa carpeta se borra, hay que pasar `-RteOrigen` a mano — conviene guardar el RTE en un lugar estable.

**`INSTALAR.cmd` — dos cosas que no son obvias:**
1. **El `BRIDGE_SECRET` es obligatorio** (bucle hasta que se ingrese; se puede saltear escribiendo `SALTAR`). La versión anterior ofrecía "Enter = usar el default", y ese default lo rechaza producción: el bridge arranca igual y solo loguea `Templates cargados: 0`, sin ningún error de auth.
2. **El primer arranque va directo al exe, no por `schtasks`.** El Task Scheduler es un servicio que puede tener cacheado el entorno viejo, así que lanzado por ahí el bridge no vería el `BRIDGE_SECRET` que `setx /M` acaba de escribir. Desde el siguiente inicio de sesión la tarea ya lo toma bien.

Al terminar consulta `/status` y avisa si `templates_en_cache` es 0, distinguiendo las dos causas (secreto que no coincide vs. nadie enrolado todavía).

**`empaquetar.ps1` va como UTF-8 con BOM.** Sin BOM, PowerShell 5.1 lo lee como CP1252 y un guion largo rompe el parseo: uno de sus bytes cae en la comilla tipográfica de cierre y termina el string antes de tiempo. Tampoco usar `<`/`>` dentro de strings, ni una variable `$zip` conviviendo con el switch `-Zip` (PowerShell no distingue mayúsculas y son la misma).

### Palanquera (relé + Arduino)

El bridge abre una palanquera/torniquete cuando un usuario válido marca **entrada**. El control físico es un **Arduino UNO** con un **módulo de relé SRD-05VDC-SL-C** (activo-bajo) conectado por USB-serial.

**División de responsabilidades — el Arduino es el dueño del tiempo de pulso:**
- El bridge solo manda un byte `'A'` cuando hay entrada aprobada. No bloquea esperando los 5 s.
- El Arduino, al recibir `'A'`, activa el relé `RELE_MS` (5000 ms) y lo cierra solo (loop no bloqueante con `millis()`). Si el bridge se cae o el PC se reinicia a mitad de pulso, la palanquera vuelve a reposo (cerrada) igual.

**Protocolo serial (9600 baud, line ending `\n`):**

| Dirección | Mensaje | Significado |
|---|---|---|
| bridge → arduino | `'A'` | Abrir palanquera (pulso de 5 s) |
| bridge → arduino | `'P'` | Ping (usado para autodetección de puerto) |
| arduino → bridge | `JSB-PALANQUERA READY` | Emitido al arrancar el sketch |
| arduino → bridge | `JSB-PALANQUERA OK` | Respuesta al ping `'P'` |

**Punto de disparo:** `FingerprintCapture.RegistrarAsistencia()` llama `_relay?.Abrir()` **solo si `tipo == "entrada"`**. En salida no se dispara. Acceso denegado (membresía vencida → HTTP no-2xx) tampoco abre.

**Detección de puerto COM:** `RelayController` lee la env var `PALANQUERA_COM` (ej. `COM3`). Si no está definida, autodetecta: abre cada puerto, manda `'P'` y toma el que responde con la firma `JSB-PALANQUERA`. Esto cubre el caso de que el número de COM cambie entre reconexiones del cable.

**Tolerante a ausencia de hardware:** si no hay Arduino conectado, el bridge arranca y registra asistencias normalmente; solo loguea `[RELE] Sin conexión al Arduino` y no abre la palanquera. La huella sigue funcionando.

**Reset-on-open del UNO:** el Arduino UNO se reinicia cada vez que se abre el puerto serial (por `DtrEnable=true`). Por eso `RelayController` espera 2 s tras abrir antes de usar el puerto, y mantiene la conexión abierta (no abre/cierra por cada acceso).

**Cableado (módulo de 1 canal):** `VCC→5V`, `GND→GND`, `IN→D7`. La palanquera va a los bornes `NO/COM` (normalmente abierto) del relé. Si tu módulo fuera activo-alto, intercambiá `RELE_ON`/`RELE_OFF` en el `.ino`.

**Subir el sketch:** abrir `arduino/palanquera_rele/palanquera_rele.ino` en el Arduino IDE, seleccionar placa "Arduino UNO" y el puerto, y cargar. El pin del relé es `PIN_RELE = 7` y el tiempo abierto `RELE_MS = 5000`.

### DLLs del SDK referenciadas

`DPFPDevNET.dll`, `DPFPEngNET.dll`, `DPFPShrNET.dll`, `DPFPVerNET.dll`
Ruta: `C:\Program Files\DigitalPersona\One Touch SDK\.NET\Bin\`

### HTTP API del bridge (`http://localhost:8001`)

| Método | Ruta | Descripción |
|---|---|---|
| `GET` | `/status` | Estado completo: lector, enrolamiento y verificación |
| `POST` | `/enroll/{id}?nombre=X` | Inicia enrolamiento para el usuario `id` |
| `DELETE` | `/enroll` | Cancela enrolamiento en curso |
| `POST` | `/verify/start` | Carga templates del backend e inicia modo verificación |
| `DELETE` | `/verify` | Cancela verificación en curso |
| `POST` | `/access/reload` | Recarga el cache de templates del modo acceso |
| `POST` | `/palanquera/abrir` | Apertura manual de la palanquera (dispara `RelayController.Abrir()`). No registra asistencia. Responde `503` si no hay relé. |

**Apertura manual de palanquera:** botón "Abrir palanquera" al pie de `AccesoView` (`/acceso`, admin/coach), que hace `POST http://localhost:8001/palanquera/abrir`. Es el **fallback** de esa pantalla: la persona no aparece por cédula, la huella no se reconoce, o entra un invitado. **No registra asistencia** — por eso va como botón secundario (borde gris) y con la leyenda explícita, para no competir con el submit rojo, que es el camino correcto porque sí deja el registro. Vivía en el header de `UsuariosView`, donde no tenía relación con la tabla que lo rodeaba. **Se oculta cuando el modo kiosco está activo** (ver "AccesoView y modo kiosco"): sin staff mirando, es el atajo obvio para meter a alguien sin registro. El `HttpApi` recibe el `RelayController` vía `BridgeForm.Relay` (expuesto en `Program.cs`). Como llama a `localhost:8001`, **solo funciona desde la PC del gym** donde corre el bridge — no desde un celular remoto.

### Flujo de enrolamiento

1. Frontend llama `POST /enroll/{usuario_id}`
2. Bridge pone `EnrollmentState.Activo = true`
3. Usuario coloca el dedo 4 veces; `OnComplete` acumula muestras en `Enrollment`
4. Al completar 4 muestras, `Enrollment.Template` está listo
5. Bridge llama `POST /usuarios/{id}/huella-template` con header `X-Bridge-Secret`
6. Backend guarda el template Base64 en `usuarios.huella_template` y `huella_id = "dp_{id}"`
7. Frontend detecta `completado=true` via polling de `/status` y cierra el modal

### Flujo de verificación

1. Frontend llama `POST /verify/start`
2. Bridge carga templates con `GET /usuarios/con-template/lista` (header `X-Bridge-Secret`)
3. Usuario coloca el dedo; `OnComplete` extrae `FeatureSet` con `DataPurpose.Verification`
4. Bridge itera todos los templates y llama `Verification.Verify(features, template, ref result)`
5. Si `result.Verified = true` → `EnrollmentState.MarcarVerifyEncontrado(usuario)`
6. Frontend detecta resultado via polling y muestra nombre + botón "Ver perfil"

### Autenticación bridge ↔ backend (`X-Bridge-Secret`)

El bridge no tiene JWT. Los endpoints `POST /usuarios/{id}/huella-template` y `GET /usuarios/con-template/lista` aceptan el header `X-Bridge-Secret: <valor>` como alternativa al JWT de admin/coach.

El secreto se define en `backend/.env` como `BRIDGE_SECRET=...`. Si el header no coincide, el backend exige JWT normal.

**El default del código (`jain_bridge_secret_2024`) sirve solo para dev local y NUNCA debe quedar en un backend alcanzable desde internet:** está escrito en `BridgeConfig.cs` y en este archivo, y `GET /usuarios/con-template/lista` devuelve **los templates biométricos de todos los socios**. Con ese valor en producción, cualquiera que lea el repo puede bajarse las huellas. En Render/producción va un valor aleatorio largo, cargado a mano en el dashboard (`render.yaml` lo declara `sync: false`).

**Los tres lugares tienen que coincidir** y es la falla más difícil de diagnosticar del bridge, porque el síntoma no es un error visible sino `[HUELLERO] Templates cargados: 0` — con el cache vacío ninguna huella coincide, así que el lector "no reconoce a nadie" y la palanquera nunca abre, sin ningún mensaje de auth en el log:
1. El backend (env var del host; en Render, el dashboard).
2. La env var `BRIDGE_SECRET` de la PC del gym (nivel máquina).
3. `backend/.env` para dev — ojo: `load_dotenv()` **no sobreescribe** variables ya existentes, así que si hay una `BRIDGE_SECRET` a nivel máquina, esa gana y el valor del `.env` se ignora en silencio.

Para verificar sin adivinar: `GET /usuarios/con-template/lista` con el header debe dar **200**; un **401** significa que el secreto no coincide (o que falta en el backend). Un error de transporte en cambio (`Error al enviar la solicitud` en el log) es que `ApiBase` no responde, que es otra cosa.

### Modelo de datos relevante (tabla `usuarios`)

| Campo | Tipo | Uso |
|---|---|---|
| `huella_id` | `String(100)`, único, nullable | Identificador de forma `dp_{usuario_id}`; se pone al registrar template |
| `huella_template` | `Text`, nullable | Template FMD en Base64 generado por el SDK |
| `esta_en_gym` | `Boolean` | `True` al marcar entrada; vuelve a `False` solo por tiempo (`_job_reset_gym`). No hay registro de salida. |
| `fecha_vencimiento` | `Date` | Validada en `POST /asistencia/por-usuario/{id}` antes de registrar entrada |
| `fecha_nacimiento` | `Date`, nullable | Cumpleaños del miembro; usada por `query_cumpleaneros_hoy` (panel del Resumen) |

### Endpoints de asistencia relevantes

- `POST /asistencia/por-usuario/{usuario_id}` — registra entrada; valida membresía vigente en cada marcación. Llamado por el bridge o admin.
- `GET /asistencia/mi-historial?meses=N` — historial propio
- `GET /asistencia/historial/{usuario_id}?meses=N` — historial de cualquier usuario (admin/coach)

### Frontend: componentes de huella

**`UsuariosView.vue`** (admin):
- Botón "Buscar por Huella" junto a "Nuevo Usuario" → modal de verificación
- Modal de enrolamiento accesible desde la tabla de usuarios

**`UsuarioPerfilView.vue`** (admin/coach):
- Card "Huella digital" muestra estado (`Registrada` / `No registrada`)
- Botón "Registrar" / "Reemplazar" al lado del estado → mismo modal de enrolamiento
- Al completar, refresca el usuario vía `GET /usuarios/{id}` sin recargar página

**Polling pattern (frontend):**
```js
const _pollStatus = async () => {
  const r    = await fetch('http://localhost:8001/status')
  const data = await r.json()
  // usar data.enrolamiento o data.verificacion según el modo
}
const _iniciarPoll = () => {
  _pollStatus()                          // primer fetch inmediato (sin esperar el delay)
  intervalo = setInterval(_pollStatus, 600)
}
```
Ejecutar `_pollStatus()` inmediatamente antes del `setInterval` es importante: sin esto la UI tarda 600 ms en reflejar el estado activo.

## Environment Variables

Copy `backend/.env.example` to `backend/.env`. Required keys:
```
SECRET_KEY=
ADMIN_NOMBRE=
ADMIN_EMAIL=
ADMIN_PASSWORD=
ADMIN_TELEFONO=
ADMIN_DOCUMENTO=
BRIDGE_SECRET=          # Clave compartida con el bridge .NET para autenticarse sin JWT
```

Opcionales (producción):
```
DATABASE_URL=           # Postgres; si falta, usa SQLite local (sqlite:///crossfit.db)
CORS_ORIGINS=           # Coma-separado; si falta, usa los puertos de Vite local
```

`SECRET_KEY` se lee con `os.environ["SECRET_KEY"]` en `security.py` (revienta si falta — siempre debe estar seteada en el host).

Frontend (`frontend/.env.example`):
```
VITE_API_URL=           # URL del backend; si falta, usa http://127.0.0.1:8000 (dev)
```

## CORS

Los orígenes se leen de la env var `CORS_ORIGINS` (coma-separado) en `backend/main.py`. Si no está definida, el default son los puertos de Vite (`localhost:5173/5174`, `127.0.0.1:5173/5174`). En producción hay que setear el dominio del frontend (ej. `CORS_ORIGINS=https://jainsportbox.netlify.app`, **sin barra final**).

## Deployment (Render backend + Supabase datos + Netlify frontend)

El detalle completo va en `DEPLOYMENT.md`. Setup: **backend en Render Starter**, **Postgres y Storage en Supabase (plan free)**, **frontend en Netlify** (`https://jainsportbox.netlify.app`). Costo total ~$7/mes.

**Por qué no Railway:** el sistema se vende a un gimnasio y el plan Hobby de Railway es explícitamente **no-comercial**; Pro son $20/mes con crédito que no se acumula. Los planes free que suspenden el proceso (Render free) tampoco sirven: la primera huella del día esperaría el cold start y la palanquera no abriría a tiempo.

**Backend (Render):**
- Config en `render.yaml`: `runtime: docker`, `plan: starter`, `dockerfilePath: ./Dockerfile`, `healthCheckPath: /`. Todas las env vars con `sync: false` (se cargan en el dashboard, nunca en git).
- Dockerfile explícito porque el repo es mixto Python/.NET y el autodetector intentaba `dotnet restore`. El start command sale del `CMD` (`uvicorn … --workers 1`).
- **1 worker**: Starter da 0.5 CPU / 512 MB. Además mantiene chico el pool contra Supabase y evita duplicar los jobs de APScheduler.
- Variables: las 7 de arriba (`SECRET_KEY`, `ADMIN_*`, `BRIDGE_SECRET`) + `DATABASE_URL` + `CORS_ORIGINS=https://jainsportbox.netlify.app` + las 6 de `S3_*`.

**Datos (Supabase, plan free — permite uso comercial):**
- **Usar el session pooler (puerto 5432), NO el transaction pooler (6543).** `_debo_correr_scheduler()` en `main.py` toma un `pg_try_advisory_lock` a nivel de sesión sobre una conexión persistente; el modo transaction lo liberaría al terminar cada consulta y además rompe los prepared statements de psycopg3.
- Pool dimensionado para el free tier: `DB_POOL_SIZE=3`, `DB_MAX_OVERFLOW=2` (env vars), `pool_recycle=300`.
- Storage vía protocolo S3: `backend/storage.py` funciona sin cambios de código. El bucket debe ser **público** y `S3_REGION` la región real del proyecto (`"auto"` era de R2).
- El proyecto free se pausa a los 7 días sin actividad; `_job_reset_gym` (cada 3 min) lo mantiene despierto mientras el backend corra.
- **Sin PITR:** el respaldo propio es `backup-db.ps1` (raíz), agendado diario en la PC del gym → OneDrive, retención 14.

**Frontend (Netlify):**
- Config en `netlify.toml`: `base = "frontend"`, `command = "npm run build"`, `publish = "dist"` (relativo a base — **no** `frontend/dist`, daría `frontend/frontend/dist`). Rewrite SPA `/* → /index.html`.
- Variable en Netlify: `VITE_API_URL` = URL de Render (sin barra final).
- `frontend/node_modules` **no** debe estar trackeado en git: sus binarios (`vite`) commiteados desde Windows pierden el bit de ejecución y Netlify falla con `vite: Permission denied`. Está en `.gitignore`; Netlify hace su propio `npm install`.

**Gotchas de dependencias (diferencias dev local vs. imagen limpia):**
- `database.py` reescribe la URL de Postgres a `postgresql+psycopg://` para usar psycopg v3 (lo que está en `requirements.txt`), porque psycopg2 no está instalado. Maneja tanto `postgres://` como `postgresql://`. También fuerza `sslmode=require` (el default de psycopg es `prefer`, que aceptaría texto plano).
- `bcrypt` está fijado a `4.0.1` en `requirements.txt`: passlib 1.7.4 revienta con bcrypt ≥ 4.1 (`ValueError: password cannot be longer than 72 bytes` en la detección de backend).
