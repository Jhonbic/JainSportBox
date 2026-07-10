# Plan de Testing y Debug — JainSportBox

Plan detallado para verificar todos los módulos y APIs del proyecto.

> **Estado (2026-07-10):** Fases 0–4 ejecutadas — suite automatizada en `backend/tests/` con **184 tests en verde** (`cd backend && ..\venv\Scripts\python.exe -m pytest tests -q`). La Fase 5 quedó cubierta parcialmente: cada corrida de la suite ejecuta el bloque de migraciones SQLite contra una BD temporal limpia (falta la verificación contra Postgres en Docker). Pendientes: Fase 5-Postgres, Fase 6 (smoke frontend), Fase 7 (bridge) y Fase 8 (producción). Bugs encontrados y su estado: ver `## Hallazgos` al final.

---

## 1. Estrategia general

| Capa | Herramienta | Alcance |
|---|---|---|
| API backend (automatizado) | `pytest` + `fastapi.testclient.TestClient` (httpx) | Todos los routers, roles, validaciones, casos borde |
| Lógica pura (unitario) | `pytest` | `_calcular_1rm`, normalización email/documento, cálculo IMC, dedup de alertas |
| Frontend (smoke manual) | Navegador (dev server) | Flujos por rol: admin, coach, cliente, pendiente, cliente vencido |
| Bridge biométrico | Manual en la PC del gym | Enrolamiento, verificación, acceso, palanquera |
| Migraciones | Script de arranque contra SQLite limpio y Postgres | Los 3 bloques de `main.py` |
| Producción | curl / navegador contra Railway + Netlify | CORS, health, mixed content |

### Infraestructura de tests propuesta

```
backend/tests/
  conftest.py          # app con SQLite en memoria (StaticPool), override de get_db, fixtures de usuarios/tokens
  test_auth.py
  test_usuarios.py
  test_pagos_planes.py
  test_asistencia.py
  test_wods.py
  test_marcas.py
  test_salud.py
  test_finanzas_ventas.py
  test_alertas.py
  test_productos_tienda.py
  test_metodos_pago.py
```

**conftest.py — fixtures clave:**
- `db`: engine `sqlite:///:memory:` con `StaticPool` + `Base.metadata.create_all` (evita tocar `crossfit.db`).
- Override de `get_db` con `app.dependency_overrides`.
- `admin_token`, `coach_token`, `cliente_token`, `pendiente_token`: usuarios creados directo en la BD + login real (o `crear_token` de `security.py`).
- `cliente_vencido`: cliente con `fecha_vencimiento` en el pasado.
- Setear env vars requeridas (`SECRET_KEY`, `ADMIN_*`, `BRIDGE_SECRET`) antes de importar `main` (usa `monkeypatch`/`os.environ` en conftest).
- ⚠️ Importar `main.py` ejecuta seed + migraciones + scheduler. Si estorba, testear montando los routers en una app FastAPI limpia, o desactivar el scheduler con una env var de test.

**Matriz transversal (aplicar a TODOS los endpoints protegidos):**
1. Sin token → `401`.
2. Token de rol insuficiente → `403` (ej. cliente llamando endpoints de admin).
3. Token válido rol correcto → `2xx`.
4. ID inexistente → `404`.
5. Payload inválido → `422`.

---

## 2. Auth (`routers/auth.py`)

| # | Caso | Esperado |
|---|---|---|
| 2.1 | `POST /login` credenciales correctas | 200, JWT válido, incluye rol |
| 2.2 | Login password incorrecto / email inexistente | 401 |
| 2.3 | Login con email en mayúsculas / espacios (`  Foo@X.com `) | 200 — normalización `.strip().lower()` |
| 2.4 | Rate limit: ráfaga de logins fallidos | 429 al superar el bucket (`ratelimit.py`) |
| 2.5 | `POST /registro` multipart con todos los campos, sin foto | 201, rol `pendiente` |
| 2.6 | Registro con foto | 201, archivo en `uploads/`, `foto_url` seteada |
| 2.7 | Registro email/documento duplicado (con distinto case) | 400/409 |
| 2.8 | Registro como JSON (no multipart) | 422 — confirma contrato `Form(...)` |
| 2.9 | `GET /me` cliente | 200 con membresía, plan, `telefono`, `documento_identidad`, `fecha_nacimiento`, `foto_url` |
| 2.10 | `PATCH /me` cambia nombre/teléfono | 200, persiste; email duplicado → error |
| 2.11 | `PATCH /me` cambio de contraseña | login con la nueva funciona, con la vieja falla |
| 2.12 | `POST /me/foto` reemplaza foto | foto anterior eliminada del disco |
| 2.13 | `GET /contacto` sin auth | 200 (público) |
| 2.14 | Token expirado / firmado con otra key / malformado | 401 |
| 2.15 | JWT de usuario luego eliminado | 401 (get_current_user no revienta con 500) |

## 3. Usuarios (`routers/usuarios.py`)

| # | Caso | Esperado |
|---|---|---|
| 3.1 | `POST /usuarios/` admin crea usuario | 201; coach → verificar regla (¿403 o permitido?); cliente → 403 |
| 3.2 | `GET /usuarios/` | 200; verificar que NO serializa `huella_template` (defer) y que password nunca sale en ninguna respuesta |
| 3.3 | `PATCH /usuarios/{id}` cambia email a uno existente | 400/409; con case distinto también rechaza |
| 3.4 | `GET /usuarios/pendientes` | solo rol `pendiente` |
| 3.5 | `GET /usuarios/cumpleanos-hoy` | usuario con `fecha_nacimiento` hoy Y membresía vigente aparece; vencido NO; **la ruta no es capturada por `/{usuario_id}`** (regresión de orden de rutas) |
| 3.6 | `GET /usuarios/{id}` con id no numérico (`/usuarios/abc`) | 422, no 500 |
| 3.7 | `POST /usuarios/{id}/activar` | rol pasa a cliente, `fecha_vencimiento` correcta |
| 3.8 | `DELETE /usuarios/{id}` | 204; verificar qué pasa con sus pagos/asistencias/marcas (¿cascade u orphans? documentar resultado) |
| 3.9 | `POST /usuarios/{id}/huella-template` con `X-Bridge-Secret` correcto | 200, guarda template y `huella_id = dp_{id}` |
| 3.10 | Ídem con secret incorrecto y sin JWT | 401/403 |
| 3.11 | `GET /usuarios/con-template/lista` con secret | 200, solo usuarios con template |
| 3.12 | `GET /usuarios/huella/{huella_id}` inexistente | 404 |
| 3.13 | `POST /usuarios/{id}/foto` | reemplaza y borra la anterior |

## 4. Planes y Pagos (`planes.py`, `pagos.py`)

| # | Caso | Esperado |
|---|---|---|
| 4.1 | `GET /planes/` autenticado (cualquier rol, incl. pendiente) | 200 |
| 4.2 | CRUD de planes solo admin | coach/cliente → 403 |
| 4.3 | `POST /planes/{id}/solicitar` como pendiente | 200/201 |
| 4.4 | `DELETE /planes/{id}` con pagos asociados | comportamiento definido (no 500) |
| 4.5 | `POST /pagos/` (plan) sobre usuario sin membresía | `fecha_vencimiento = hoy + duracion_dias` |
| 4.6 | `POST /pagos/` sobre membresía vigente (renovación) | extiende desde `fecha_vencimiento`, no desde hoy |
| 4.7 | `POST /pagos/directo/` personalizado N días | `plan_id NULL`, `duracion_dias = N`; historial muestra "Personalizado (N días)" |
| 4.8 | `PATCH /pagos/{id}` | solo cambia `monto`/`metodo_pago`; intento de cambiar plan no surte efecto |
| 4.9 | `DELETE /pagos/{id}` (anular) | resta `duracion_dias` de `fecha_vencimiento` (puede quedar en el pasado — correcto); borra el `Pago` |
| 4.10 | Anular pago personalizado | usa `pago.duracion_dias`, no plan |
| 4.11 | `GET /pagos/usuario/{id}` | ordenado, incluye método y nombre de plan |
| 4.12 | Doble efecto en finanzas | crear un pago NO crea fila en `movimientos_financieros` (regresión del bug de doble conteo) |

## 5. Asistencia (`asistencia.py`) — crítico (palanquera)

| # | Caso | Esperado |
|---|---|---|
| 5.1 | `POST /asistencia/por-usuario/{id}` con `X-Bridge-Secret`, membresía vigente | 201 tipo `entrada`, `esta_en_gym = True` |
| 5.2 | Ídem con membresía vencida | rechazo (403/400), NO crea asistencia, `esta_en_gym` no cambia |
| 5.3 | Ídem que vence HOY exactamente | permitido (borde `>=`) |
| 5.4 | Doble marcación seguida | segunda crea otra `entrada` (el cooldown vive en el bridge) — documentar, no alternar a salida |
| 5.5 | `POST /asistencia/` por `huella_id` inexistente | 404 |
| 5.6 | Sin secret ni JWT | 401 |
| 5.7 | `GET /mi-historial?meses=12` | solo registros propios, rango correcto |
| 5.8 | `GET /historial/{id}` como cliente | 403 |
| 5.9 | `GET /en-gym` | incluye `minutos_transcurridos`/`minutos_restantes` coherentes con `MINUTOS_SESION` |
| 5.10 | `GET /sesiones-por-bloque?desde=&hasta=` rango > 31 días | 400/422 |
| 5.11 | sesiones-por-bloque: usuario con 2 entradas en el mismo bloque | aparece una sola vez (la primera); zona horaria Bogotá correcta (entrada 23:30 UTC cae en el día local correcto) |
| 5.12 | Job `_job_reset_gym` (unitario: llamar la función con la sesión de test) | usuario con última entrada > `MINUTOS_SESION` pasa a `False`; reciente queda `True`; no crea registro de salida |

## 6. WODs y Ejercicios (`wods.py`, `ejercicios.py`)

| # | Caso | Esperado |
|---|---|---|
| 6.1 | `POST /wods/` admin y coach | 201; cliente → 403 |
| 6.2 | Crear WOD con ejercicios y superseries | filas consecutivas con `superserie_con_anterior=True`; **primera fila siempre `False`** (normalización `_aplicar_ejercicios`) |
| 6.3 | `PUT /wods/{id}` reordena ejercicios | grupos de superserie no quedan huérfanos; invariante primera fila se mantiene |
| 6.4 | `GET /wods/` cliente | solo `activo=True`; staff sin filtro ve todos |
| 6.5 | `GET /wods/?activo=false&skip=N&limit=M` | paginación correcta |
| 6.6 | `PATCH /wods/{id}/toggle` | alterna `activo` |
| 6.7 | `GET /wods/hoy` | solo WODs de la fecha actual |
| 6.8 | `GET /wods/personalizados` como cliente masculino | solo activos con `genero_destino="masculino"`; staff ve todos |
| 6.9 | Crear personalizado con 2 géneros (desde form) | dos WODs, uno por género |
| 6.10 | **Orden de rutas**: `GET /wods/personalizados` y `GET /wods/hoy` no capturados por rutas con path param | 200 con datos correctos |
| 6.11 | N+1: listar 50 WODs con ejercicios | número de queries acotado (eager loading `_EAGER_EJERCICIOS`) — verificar con `echo=True` o contador de eventos |
| 6.12 | CRUD ejercicios: filtro `?categoria=`, borrar ejercicio usado en un WOD | comportamiento definido, no 500 |

## 7. Marcas RM (`marcas.py`) — lógica por tipo

Unitario `_calcular_1rm`:
- 100 kg × 1 rep → 100 (todas las fórmulas coinciden en 1 rep — verificar).
- 100 kg × 5 reps → valor esperado del promedio de las 7 fórmulas (calcular a mano el fixture).
- reps=0 o negativo → error controlado, no división por cero (Brzycki con 37 reps → denominador 0: probar reps altas).

| # | Caso | Esperado |
|---|---|---|
| 7.1 | `POST /marcas/` tipo `barra` (Back Squat) con peso+reps | 201, `rm_calculado` correcto |
| 7.2 | `barra` sin peso | 422 |
| 7.3 | `corporal_lastre` (Dominadas) con `peso` (total) y `peso_adicional` | 201, RM sobre el total |
| 7.4 | `reps` (Push Up) con solo repeticiones | 201, `rm_calculado NULL`; si mandan peso → ignorado o 422 (según contrato) |
| 7.5 | `leger` con nivel+palier | 201; sin palier → 422 |
| 7.6 | Ejercicio no listado en `TIPOS_EJERCICIO` | 422/400 |
| 7.7 | `GET /marcas/{ejercicio}` con nombre URL-encoded ("Clean%20and%20Jerk") | 200 registros de ese ejercicio, solo del usuario actual |
| 7.8 | `PATCH /marcas/{id}` cambia peso/reps | `rm_calculado` recalculado; misma validación por tipo |
| 7.9 | PATCH/DELETE de una marca de OTRO usuario | 404/403 — aislamiento entre usuarios |
| 7.10 | Payload con `series: [...]` (registro directo por serie) | un registro por serie |
| 7.11 | Unidades: registro en lbs vs kg | comparación de PR normalizada a kg (1 kg = 2.20462 lbs) — verificar en frontend/preview `esPR` |
| 7.12 | Sincronía `TIPOS_EJERCICIO` (backend) vs `ejerciciosMarcas.js` (frontend) | test que compare las dos listas (leer el .js con regex o duplicar el fixture) — atrapa desincronización |

## 8. Salud (`salud.py`)

| # | Caso | Esperado |
|---|---|---|
| 8.1 | `POST /salud/{tipo}` para cada uno de los 6 tipos | 201, solo esa columna seteada |
| 8.2 | Tipo inválido (`/salud/biceps`) | 404/422 |
| 8.3 | IMC: registrar altura, luego peso | `imc` calculado cuando existen ambos; solo peso sin altura previa → `imc NULL` |
| 8.4 | `GET /salud/{tipo}` | solo registros del usuario, solo de ese tipo |
| 8.5 | `DELETE /salud/{id}` de otro usuario | 404/403 |
| 8.6 | Acceso como admin | el router: ¿permite? El frontend lo excluye por rol — documentar el comportamiento del backend |
| 8.7 | Valores absurdos (peso -5, altura 0) | validación o al menos no rompe IMC (división por cero con altura 0) |

## 9. Finanzas, Ventas, Productos (`finanzas.py`, `ventas.py`, `productos.py`)

| # | Caso | Esperado |
|---|---|---|
| 9.1 | `GET /finanzas/balance` | ingresos = pagos + ventas + movimientos manuales; **sin doble conteo** (crear 1 pago, 1 venta, 1 movimiento → balance suma exactamente los 3) |
| 9.2 | `GET /finanzas/movimientos` con filtros fecha/tipo | correcto; solo admin |
| 9.3 | `POST /finanzas/movimientos` ingreso y egreso manual | 201, afecta balance |
| 9.4 | `DELETE /finanzas/movimientos/{id}` sobre fila legacy `pago_directo` | comportamiento definido |
| 9.5 | `GET /finanzas/usuarios/buscar?q=` | busca por nombre/documento |
| 9.6 | `POST /ventas/` con stock suficiente | 201, stock decrementa, NO crea movimiento financiero espejo (regresión commit `8b8ff01`) |
| 9.7 | Venta con stock insuficiente | 400, stock intacto |
| 9.8 | Venta de producto inexistente | 404 |
| 9.9 | Venta con cantidad 0/negativa | 422 |
| 9.10 | CRUD productos solo admin/coach (según regla); foto de producto reemplaza anterior | ok |
| 9.11 | Borrar producto con ventas asociadas | historial de ventas no se rompe (no 500 al listar) |

## 10. Alertas (`alertas.py`)

| # | Caso | Esperado |
|---|---|---|
| 10.1 | `POST /alertas/generar` con usuario que vence en 3 días | crea 1 alerta pendiente |
| 10.2 | Generar dos veces seguidas | NO duplica (dedup por alerta pendiente existente) |
| 10.3 | Usuario renueva (cambia `fecha_vencimiento`) → generar | alerta pendiente vieja eliminada, nueva creada si sigue en ventana de 7 días |
| 10.4 | Usuario fuera de la ventana de 7 días | alerta pendiente eliminada |
| 10.5 | `POST /{id}/marcar-enviada` | `enviada=True`, `fecha_enviada` seteada; aparece en historial, no en pendientes |
| 10.6 | `GET /alertas/` y `/contar` como cliente | 403 |

## 11. Métodos de pago (`metodos_pago.py`)

- `GET /metodos-pago/`: cualquier autenticado; solo activos; ordenados por `orden` asc.
- `POST`: asigna `orden` al final; solo admin (coach → 403).
- `PATCH`: cambiar `activo=false` lo saca del GET.
- `DELETE`: 204; id inexistente 404.

## 12. Migraciones de arranque (`main.py`)

1. **SQLite limpio:** borrar/renombrar `crossfit.db` de prueba, arrancar → tablas creadas, seed corre (admin + planes), segundo arranque idempotente (sin errores por columnas ya existentes).
2. **SQLite viejo:** tomar un backup de BD anterior (si existe) → arranque agrega columnas nuevas vía `ALTER TABLE` y reconstruye `marcas_rm` (nullability) sin perder datos.
3. **Postgres local (docker `postgres:16`):** `DATABASE_URL=postgresql://...` → bloque `ADD COLUMN IF NOT EXISTS` corre sin error; arrancar dos veces (idempotencia); confirmar que **toda columna del modelo existe** en Postgres:
   ```sql
   -- comparar information_schema.columns vs modelos (script rápido en pytest)
   ```
   Esto atrapa el bug clase "no deja crear WODs" (columna solo en bloque SQLite).
4. **Índices:** verificar `CREATE INDEX IF NOT EXISTS` en ambos motores (`PRAGMA index_list` / `pg_indexes`).
5. **Advisory lock:** con 2 workers (`uvicorn --workers 2` vía Docker local), el job de alertas corre en uno solo (revisar logs).

## 13. Frontend — smoke manual por rol

Correr backend local + `npm run dev`. Checklist por rol:

**Pendiente:** login → forzado a `/planes`; sidebar solo muestra Planes; solicitar plan funciona; intento de URL directa a `/wods` redirige.

**Cliente vigente:** `/home` (tarjetas membresía/plan sin flash de "-999 días" — spinner de `cargandoPerfil`), calendario de asistencia con navegación de meses, WODs activos visibles (sin toggle/editar), WODs personalizados de su género si su plan lo incluye, Mi Salud (6 medidas, gráfica, alta y borrado, IMC), Mis Marcas (los 4 tipos: barra con panel de series directas, dominadas con peso corporal de Mi Salud, reps con modal, Léger nivel+palier; editar y borrar; gráfica con PRs en oro; kg/lbs), Mi Perfil (editar datos, cambiar contraseña, foto; `localStorage.userName` actualizado).

**Cliente vencido:** solo accede a `/home`, `/planes`, `/`, `/perfil`; sidebar reducido; URL directa a `/salud` bloqueada.

**Coach:** Gestión (Usuarios, Sesiones, Alertas, Ejercicios) sí; Planes y Finanzas NO (ni por URL); crear/editar WODs y personalizados; Mi Box completo.

**Admin:** todo lo de gestión + Finanzas + Planes + Tienda; NO ve Mi Salud/Mis Marcas (ni por URL directa); UsuariosView: panel cumpleaños (colapsable, WhatsApp link con `57` + dígitos), filtro "En el box ahora" (refresco 10 s), buscar por huella, activar usuario, perfil `/usuarios/:id` (editar, agregar/editar/anular membresía, calendario, huella); SesionesView (semana/mes/fecha, BloqueCard acordeón, buscador); AlertasView (pendientes/historial, generar en mount); FinanzasView (balance cuadra con seed de datos conocido); Tienda (crear producto con foto, vender, stock baja).

**Transversal frontend:**
- 401: borrar el token en localStorage a mano → siguiente request redirige a `/login`.
- Charts: entrar/salir repetidamente de `/salud/peso` y `/marcas/:ej` → sin errores "Canvas is already in use" (destruirChart) ni memory leaks visibles.
- Lazy routes: `npm run build` → verificar chunks separados (vendor, chart, vistas).
- Móvil (responsive): tabla de marcas oculta Notas, perfil no trunca nombre.

## 14. Bridge biométrico (manual, PC del gym)

Prerequisito: lector U.are.U 4500 conectado, bridge como admin, `[CONFIG] ApiBase` en el log apuntando al backend correcto (local: `JSB_API_BASE=http://localhost:8000` + reiniciar bridge).

1. `GET http://localhost:8001/status` → lector detectado.
2. **Enrolamiento:** desde UsuariosView, 4 capturas → template guardado (`huella_id = dp_{id}`), modal cierra por polling.
3. **Verificación:** "Buscar por Huella" → identifica al usuario correcto; dedo no enrolado → no match.
4. **Acceso:** dedo enrolado con membresía vigente → asistencia creada + palanquera abre (byte `'A'`, 5 s); membresía vencida → NO abre; cooldown 4 s: dos toques seguidos → una sola asistencia.
5. **Palanquera manual:** botón verde en UsuariosView → `POST /palanquera/abrir` abre sin registrar asistencia; sin Arduino → 503 y el bridge sigue vivo.
6. **Background:** bridge sin foco/minimizado → captura sigue funcionando (Priority.High).
7. **Resiliencia:** desconectar Arduino → bridge loguea `[RELE] Sin conexión` y la huella sigue; reconectar cable USB (cambia COM) → autodetección con ping `'P'`.
8. `POST /access/reload` tras enrolar a alguien nuevo → reconocido sin reiniciar.

## 15. Producción (Railway + Netlify)

- `https://web-production-ca5df.up.railway.app/docs` responde; login OK desde `https://jainsportbox.netlify.app` (CORS sin errores en consola).
- Deep-link SPA (`/usuarios` con F5) → no 404 (rewrite Netlify).
- Subir foto de perfil en prod → se sirve desde `/uploads` (⚠️ verificar persistencia: el filesystem de Railway es efímero entre deploys — documentar si las fotos sobreviven un redeploy).
- Bridge de producción apunta a Railway y registra asistencia real.
- Tras cualquier deploy con columna nueva: revisar logs de arranque de Railway (bloque Postgres corrió) y probar el INSERT afectado.

## 16. Orden de ejecución sugerido

1. **Fase 0 — infraestructura:** crear `backend/tests/conftest.py` + fixtures; agregar `pytest` y `httpx` a requirements de dev; comando: `cd backend && python -m pytest tests/ -v`.
2. **Fase 1 — auth + usuarios** (base de todo lo demás).
3. **Fase 2 — pagos/planes + asistencia** (dinero y palanquera: mayor riesgo).
4. **Fase 3 — marcas + salud** (lógica de cálculo más densa).
5. **Fase 4 — wods, finanzas/ventas, alertas, metodos-pago, productos.**
6. **Fase 5 — migraciones** (SQLite limpio + Postgres en docker).
7. **Fase 6 — smoke frontend por rol** (checklist §13).
8. **Fase 7 — bridge en la PC del gym** (§14).
9. **Fase 8 — verificación en producción** (§15).

Al terminar cada fase, registrar los bugs encontrados en una sección `## Hallazgos` al final de este archivo (fecha, endpoint, caso, comportamiento observado vs esperado) y corregirlos antes de pasar de fase.

---

## Hallazgos

### 2026-07-10 — Ejecución Fases 0–4 (suite `backend/tests/`, 184 tests)

**1. [BUG — CORREGIDO] `POST /asistencia/` (entrada por `huella_id`) no validaba membresía.**
- Observado: un usuario con membresía vencida y huella registrada podía marcar entrada por esta ruta (201, `esta_en_gym=True`); solo `/asistencia/por-usuario/{id}` validaba vigencia.
- Esperado: toda marcación valida membresía (caso 5.2 / CLAUDE.md).
- Fix: se extrajo `_validar_membresia()` en `routers/asistencia.py` y ahora ambas rutas la aplican. Test de regresión: `test_entrada_por_huella_valida_membresia`.

**2. [DOC DESACTUALIZADA — CORREGIDA] El IMC no lo calcula el backend.**
- CLAUDE.md decía que `POST /salud/{tipo}` calculaba `imc` cuando había peso y altura. En realidad la columna `imc` queda siempre NULL; el IMC lo calcula el frontend (`SaludView.imcActual`) con el último peso y la última altura. Sin impacto funcional. CLAUDE.md corregido; comportamiento fijado en `test_imc_no_se_calcula_en_backend`.

**Comportamientos documentados (no son bugs, quedan fijados por tests):**
- `DELETE /usuarios/{id}` borra en cascada pagos, asistencias, marcas, medidas y ventas del usuario (cascade `all, delete-orphan` en el modelo).
- Un ejercicio no catalogado en `TIPOS_EJERCICIO` se trata como `barra` (default de `_tipo_de`), no da 422.
- `GET /planes/` es público (sin token) — lo consume la pantalla de planes.
- El backend permite al admin acceder a `/salud` y `/marcas`; la exclusión del admin es solo del router del frontend.
- `DELETE /planes/{id}` y `DELETE /productos/{id}` son soft-delete (`activo=False`); el historial de pagos/ventas se preserva.
- La doble marcación seguida por bridge crea dos entradas: el cooldown anti-repetición vive en el bridge .NET (4 s), no en el backend.
- Sincronía `TIPOS_EJERCICIO` (backend) ↔ `ejerciciosMarcas.js` (frontend) verificada por `test_tipos_ejercicio_en_sync_con_frontend` — si se desincronizan, la suite falla.

**Infraestructura agregada:**
- `backend/tests/` (conftest + 10 archivos por dominio), `backend/requirements-dev.txt` (pytest, httpx).
- `backend/main.py`: guard `TESTING=1` para no arrancar APScheduler en tests (sin efecto en producción, verificado con arranque normal).
- La suite corre contra un SQLite temporal (nunca toca `backend/crossfit.db`) y ejecuta el arranque completo (migraciones + seed) en cada corrida.
