"""Agregados para la pantalla de resumen del box (`/dashboard`).

Dos reglas transversales a todas las consultas de este módulo:

1. **Zona horaria.** `Asistencia.fecha_hora`, `Pago.fecha_pago`, `Venta.fecha_venta` y
   `MovimientoFinanciero.fecha` se guardan como datetime **naive en UTC**. Cualquier
   agrupación por día, hora o mes tiene que pasar a hora de Bogotá primero; si no, todo
   lo ocurrido después de las 19:00 locales cae en el día (o el mes) siguiente. Para el
   "hoy" del negocio se usa `hoy_bogota()`, nunca `date.today()`.
2. **Volumen acotado.** Los conteos van con `func.count`/`group_by` en SQL. Donde hace
   falta convertir la zona horaria fila por fila (heatmap, serie mensual) se traen solo
   las columnas necesarias y en una ventana de tiempo limitada.
"""

from collections import defaultdict
from datetime import date, datetime, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func
from sqlalchemy.orm import Session

from database import get_db
# Los helpers de ventana viven en `fechas` para que los use también `asistencia.py`;
# se importan con alias para no tocar las decenas de llamadas de este módulo.
from fechas import (
    hoy_bogota,
    a_bogota as _a_bogota,
    fin_dia_utc as _fin_dia_utc,
    inicio_dia_utc as _inicio_dia_utc,
)
from models import (
    Asistencia,
    MovimientoFinanciero,
    Pago,
    Plan,
    RolUsuario,
    TipoMovimiento,
    Usuario,
    Venta,
)
from routers.usuarios import query_cumpleaneros_hoy
from security import get_current_user

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


def _require_admin_or_coach(current_user: Usuario = Depends(get_current_user)):
    if current_user.rol not in (RolUsuario.ADMIN, RolUsuario.COACH):
        raise HTTPException(status_code=403, detail="Solo admin o coach pueden ver el dashboard.")
    return current_user


def _require_admin(current_user: Usuario = Depends(get_current_user)):
    if current_user.rol != RolUsuario.ADMIN:
        raise HTTPException(status_code=403, detail="Solo el administrador puede ver datos financieros.")
    return current_user


def _duracion_pago(duracion_pago: Optional[int], duracion_plan: Optional[int]) -> Optional[int]:
    """Días que cubre un pago: los del plan, o los del pago si es personalizado."""
    return duracion_pago if duracion_pago is not None else duracion_plan


# ── Renovación ────────────────────────────────────────────────


def _tasa_renovacion(db: Session, desde: date, hasta: date) -> dict:
    """Cuántas membresías vencidas en el rango volvieron a pagarse.

    IMPORTANTE — esto es una **inferencia**, no un dato guardado. No existe histórico
    de membresías: `usuarios.fecha_vencimiento` es una columna que se pisa en cada
    renovación, así que mirarla solo mostraría a los que NO renovaron. La reconstrucción
    se hace sobre `pagos`, que sí es un histórico:

      · vencimiento implícito de un pago = fecha_pago + días que cubre
      · una membresía "venció en el rango" si ese vencimiento cae dentro del rango
      · "renovó" si hay otro pago posterior, desde 7 días antes de ese vencimiento
        hasta 30 días después (adelantarse unos días o llegar tarde sigue siendo renovar)

    Sesgo conocido: quien venció hace pocos días todavía está dentro de su margen para
    renovar y cuenta como no renovado, así que el número queda algo pesimista. Por eso
    se devuelven los crudos (`vencieron` / `renovaron`) además del porcentaje.
    """
    # Ventana amplia hacia atrás: un plan largo pagado hace meses puede vencer en el rango.
    limite = _inicio_dia_utc(desde - timedelta(days=400))
    filas = (
        db.query(Pago.usuario_id, Pago.fecha_pago, Pago.duracion_dias, Plan.duracion_dias)
        .outerjoin(Plan, Pago.plan_id == Plan.id)
        .filter(Pago.fecha_pago >= limite)
        .all()
    )

    pagos_por_usuario: dict[int, list[tuple[date, Optional[int]]]] = defaultdict(list)
    for usuario_id, fecha_pago, dur_pago, dur_plan in filas:
        pagos_por_usuario[usuario_id].append(
            (_a_bogota(fecha_pago).date(), _duracion_pago(dur_pago, dur_plan))
        )

    vencieron = 0
    renovaron = 0
    for _usuario_id, pagos in pagos_por_usuario.items():
        pagos.sort()
        fechas = [f for f, _ in pagos]
        for fecha_pago, dias in pagos:
            if not dias:
                continue
            vence = fecha_pago + timedelta(days=dias)
            if not (desde <= vence <= hasta):
                continue
            vencieron += 1
            if any(fecha_pago < f <= vence + timedelta(days=30) and f >= vence - timedelta(days=7)
                   for f in fechas):
                renovaron += 1

    porcentaje = round(renovaron / vencieron * 100) if vencieron else None
    return {"vencieron": vencieron, "renovaron": renovaron, "porcentaje": porcentaje}


# ── Endpoints ─────────────────────────────────────────────────


@router.get("/resumen")
def resumen(
    db: Session = Depends(get_db),
    _: Usuario = Depends(_require_admin_or_coach),
):
    hoy = hoy_bogota()
    en_7_dias = hoy + timedelta(days=7)
    hace_30_dias = hoy - timedelta(days=30)
    inicio_mes = hoy.replace(day=1)
    inicio_mes_anterior = (inicio_mes - timedelta(days=1)).replace(day=1)

    def _contar_socios(*filtros):
        return (
            db.query(func.count(Usuario.id))
            .filter(Usuario.rol == RolUsuario.CLIENTE, *filtros)
            .scalar()
            or 0
        )

    activos = _contar_socios(Usuario.fecha_vencimiento >= hoy)

    socios = {
        "activos": activos,
        "por_vencer": _contar_socios(
            Usuario.fecha_vencimiento >= hoy, Usuario.fecha_vencimiento <= en_7_dias
        ),
        "vencidos_recuperables": _contar_socios(
            Usuario.fecha_vencimiento < hoy, Usuario.fecha_vencimiento >= hace_30_dias
        ),
        "sin_membresia": _contar_socios(Usuario.fecha_vencimiento.is_(None)),
        "pendientes": db.query(func.count(Usuario.id))
        .filter(Usuario.rol == RolUsuario.PENDIENTE)
        .scalar()
        or 0,
        "altas_mes": _contar_socios(Usuario.created_at >= _inicio_dia_utc(inicio_mes)),
        "altas_mes_anterior": _contar_socios(
            Usuario.created_at >= _inicio_dia_utc(inicio_mes_anterior),
            Usuario.created_at < _inicio_dia_utc(inicio_mes),
        ),
    }

    # ── Asistencia ──
    def _contar_entradas(desde: date, hasta: date):
        # Cuenta solo CLIENTES. El staff también marca huella (desde que se lo eximió
        # de la validación de membresía, si no la palanquera no le abría), pero un
        # coach entrando todos los días infla "asistencia de hoy" y le cambia el
        # significado al número. Participación ya filtraba por rol; esto lo alinea.
        return (
            db.query(func.count(Asistencia.id))
            .join(Usuario, Usuario.id == Asistencia.usuario_id)
            .filter(
                Asistencia.tipo == "entrada",
                Asistencia.fecha_hora >= _inicio_dia_utc(desde),
                Asistencia.fecha_hora <= _fin_dia_utc(hasta),
                Usuario.rol == RolUsuario.CLIENTE,
            )
            .scalar()
            or 0
        )

    lunes = hoy - timedelta(days=hoy.weekday())
    entradas_30_dias = _contar_entradas(hoy - timedelta(days=29), hoy)

    # Engagement: socios activos distintos que vinieron esta semana, sobre el total de activos.
    socios_semana = (
        db.query(func.count(func.distinct(Asistencia.usuario_id)))
        .join(Usuario, Usuario.id == Asistencia.usuario_id)
        .filter(
            Asistencia.tipo == "entrada",
            Asistencia.fecha_hora >= _inicio_dia_utc(lunes),
            Asistencia.fecha_hora <= _fin_dia_utc(hoy),
            Usuario.rol == RolUsuario.CLIENTE,
            Usuario.fecha_vencimiento >= hoy,
        )
        .scalar()
        or 0
    )

    asistencia = {
        "hoy": _contar_entradas(hoy, hoy),
        "semana": _contar_entradas(lunes, hoy),
        "promedio_diario": round(entradas_30_dias / 30, 1),
        "socios_semana": socios_semana,
        "engagement": round(socios_semana / activos * 100) if activos else None,
    }

    cumpleaneros = [
        {"id": u.id, "nombre": u.nombre, "telefono": u.telefono}
        for u in query_cumpleaneros_hoy(db)
    ]

    return {
        "fecha": hoy.isoformat(),
        "socios": socios,
        "asistencia": asistencia,
        # Ventana móvil de 30 días, no "del mes": el día 1 el mes corriente sería
        # una ventana de un día y el número no diría nada.
        "renovacion": _tasa_renovacion(db, hoy - timedelta(days=29), hoy),
        "cumpleaneros": cumpleaneros,
    }


@router.get("/inactivos")
def inactivos(
    dias: int = Query(14, ge=1, le=365),
    limite: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    _: Usuario = Depends(_require_admin_or_coach),
):
    """Socios con membresía vigente que no marcan entrada hace `dias` o más.

    Es la lista que anticipa el churn: pagaron, pero dejaron de venir.
    """
    hoy = hoy_bogota()
    corte = _inicio_dia_utc(hoy - timedelta(days=dias - 1))

    # Última entrada por usuario en una sola subconsulta (evita el N+1).
    ultima = (
        db.query(
            Asistencia.usuario_id.label("usuario_id"),
            func.max(Asistencia.fecha_hora).label("ultima"),
        )
        .filter(Asistencia.tipo == "entrada")
        .group_by(Asistencia.usuario_id)
        .subquery()
    )

    filas = (
        db.query(Usuario, ultima.c.ultima)
        .outerjoin(ultima, ultima.c.usuario_id == Usuario.id)
        .filter(
            Usuario.rol == RolUsuario.CLIENTE,
            Usuario.fecha_vencimiento >= hoy,
            (ultima.c.ultima.is_(None)) | (ultima.c.ultima < corte),
        )
        .all()
    )

    resultado = []
    for usuario, ultima_entrada in filas:
        dias_sin_venir = (
            (hoy - _a_bogota(ultima_entrada).date()).days if ultima_entrada else None
        )
        resultado.append({
            "id": usuario.id,
            "nombre": usuario.nombre,
            "telefono": usuario.telefono,
            "dias_sin_venir": dias_sin_venir,          # None = nunca marcó
            "fecha_vencimiento": usuario.fecha_vencimiento.isoformat(),
        })

    # Los que nunca vinieron primero, después por antigüedad de la última visita.
    resultado.sort(key=lambda r: (r["dias_sin_venir"] is not None, -(r["dias_sin_venir"] or 0)))
    return {"dias": dias, "total": len(resultado), "socios": resultado[:limite]}


@router.get("/afluencia")
def afluencia(
    semanas: int = Query(4, ge=1, le=12),
    db: Session = Depends(get_db),
    _: Usuario = Depends(_require_admin_or_coach),
):
    """Curva de gente por hora del día, separando entre semana de sábado.

    Devuelve **promedio de personas por día**, no totales: entre semana hay 5 días
    por cada sábado, así que comparar los crudos exageraría los días hábiles.

    La conversión de zona horaria es fila por fila porque no hay forma portable entre
    SQLite y Postgres de correr el timezone en SQL. Se trae solo la columna de fecha
    y la ventana está acotada por `semanas`, así que el volumen es chico.
    """
    hoy = hoy_bogota()
    desde = hoy - timedelta(weeks=semanas)

    fechas = (
        db.query(Asistencia.fecha_hora)
        .filter(
            Asistencia.tipo == "entrada",
            Asistencia.fecha_hora >= _inicio_dia_utc(desde),
            Asistencia.fecha_hora <= _fin_dia_utc(hoy),
        )
        .all()
    )

    por_hora_semana: dict[int, int] = defaultdict(int)
    por_hora_sabado: dict[int, int] = defaultdict(int)
    for (fecha_hora,) in fechas:
        local = _a_bogota(fecha_hora)
        if local.weekday() <= 4:
            por_hora_semana[local.hour] += 1
        elif local.weekday() == 5:
            por_hora_sabado[local.hour] += 1
        # Domingo se ignora: el box no abre.

    # Cuántos días hábiles y cuántos sábados hubo realmente en la ventana.
    dias = [desde + timedelta(days=i) for i in range((hoy - desde).days + 1)]
    dias_habiles = sum(1 for d in dias if d.weekday() <= 4) or 1
    dias_sabado = sum(1 for d in dias if d.weekday() == 5) or 1

    horas_con_datos = set(por_hora_semana) | set(por_hora_sabado)
    if horas_con_datos:
        rango = range(min(horas_con_datos), max(horas_con_datos) + 1)
    else:
        rango = range(0)

    # Dos decimales, no uno: el divisor de los días hábiles es grande (~21 en la ventana
    # por defecto, hasta ~60 con semanas=12), así que una sola visita en una hora daba
    # 1/21 = 0.05 y a un decimal se volvía 0.0 — la hora desaparecía del gráfico y
    # `_pico`, que descarta los ceros, no encontraba ningún pico. Con dos decimales el
    # peor caso del rango de `semanas` sigue siendo visible (1/60 = 0.02).
    horas = [
        {
            "hora": h,
            "semana": round(por_hora_semana.get(h, 0) / dias_habiles, 2),
            "sabado": round(por_hora_sabado.get(h, 0) / dias_sabado, 2),
        }
        for h in rango
    ]

    def _pico(clave: str, desde_hora: int, hasta_hora: int):
        candidatas = [h for h in horas if desde_hora <= h["hora"] <= hasta_hora and h[clave] > 0]
        if not candidatas:
            return None
        mejor = max(candidatas, key=lambda h: h[clave])
        return {"hora": mejor["hora"], "promedio": mejor[clave]}

    return {
        "desde": desde.isoformat(),
        "hasta": hoy.isoformat(),
        "dias_habiles": dias_habiles,
        "dias_sabado": dias_sabado,
        "horas": horas,
        # Los dos picos del día hábil, que es lo que decide dónde poner coach.
        "pico_manana": _pico("semana", 0, 11),
        "pico_tarde": _pico("semana", 12, 23),
    }


@router.get("/socios-mensuales")
def socios_mensuales(
    meses: int = Query(12, ge=1, le=24),
    db: Session = Depends(get_db),
    _: Usuario = Depends(_require_admin_or_coach),
):
    """Cuántos clientes tenían membresía vigente al cierre de cada mes.

    IMPORTANTE — es una **reconstrucción**, no un dato guardado, por el mismo motivo
    que `_tasa_renovacion`: `usuarios.fecha_vencimiento` se pisa en cada renovación,
    así que esa columna solo conoce el presente. `pagos` sí es un histórico, y cada
    pago define una ventana de cobertura `[fecha_pago, fecha_pago + días)`. Un cliente
    estaba activo en una fecha si alguna de sus ventanas la cubría.

    **El mes en curso no se infiere: se cuenta.** El presente sí es un dato conocido
    (`usuarios.fecha_vencimiento`), así que el último punto sale del mismo conteo que
    la tarjeta "Activos" del Resumen y coincide con ella siempre. Inferirlo también
    los desalineaba apenas hubiera un cliente vigente sin pago registrado.

    Limitación de los meses anteriores: solo ven lo que pasó por `pagos`. Un
    vencimiento cargado a mano, o los usuarios sembrados por un script de demo, no
    aparecen — y eso puede producir un escalón entre el último mes y el anterior.
    """
    hoy = hoy_bogota()
    primer_mes = (hoy.replace(day=1) - timedelta(days=31 * (meses - 1))).replace(day=1)
    # Ventana amplia hacia atrás: un plan largo pagado antes del rango todavía cubre
    # meses de adentro. Mismo margen que en _tasa_renovacion.
    limite = _inicio_dia_utc(primer_mes - timedelta(days=400))

    filas = (
        db.query(Pago.usuario_id, Pago.fecha_pago, Pago.duracion_dias, Plan.duracion_dias)
        .join(Usuario, Usuario.id == Pago.usuario_id)
        .outerjoin(Plan, Pago.plan_id == Plan.id)
        .filter(Pago.fecha_pago >= limite, Usuario.rol == RolUsuario.CLIENTE)
        .all()
    )

    # (usuario_id -> ventanas de cobertura). El bucketing se hace en Python y no con
    # extract() en SQL: las fechas están en UTC y un pago del 31 a las 20:00 locales
    # caería en el mes siguiente.
    ventanas: dict[int, list[tuple[date, date]]] = defaultdict(list)
    primer_pago: Optional[date] = None
    for usuario_id, fecha_pago, dur_pago, dur_plan in filas:
        inicio = _a_bogota(fecha_pago).date()
        primer_pago = inicio if primer_pago is None else min(primer_pago, inicio)
        dias = _duracion_pago(dur_pago, dur_plan)
        if not dias:
            continue
        ventanas[usuario_id].append((inicio, inicio + timedelta(days=dias)))

    if primer_pago is None:
        return {"meses": []}

    # La serie arranca en el mes del primer pago: dibujar en cero los meses previos a
    # que el sistema existiera mostraría una rampa de crecimiento que nunca ocurrió.
    cursor = max(primer_mes, primer_pago.replace(day=1))

    # El presente es dato, no inferencia: para el mes en curso se cuenta la columna
    # real. Así el último punto siempre coincide con la tarjeta "Activos".
    activos_hoy = (
        db.query(func.count(Usuario.id))
        .filter(Usuario.rol == RolUsuario.CLIENTE, Usuario.fecha_vencimiento >= hoy)
        .scalar()
        or 0
    )
    inicio_mes_actual = hoy.replace(day=1)

    serie = []
    while cursor <= hoy:
        fin_mes = (cursor + timedelta(days=32)).replace(day=1) - timedelta(days=1)
        corte = min(fin_mes, hoy)
        if cursor == inicio_mes_actual:
            activos = activos_hoy
        else:
            activos = sum(
                1 for v in ventanas.values() if any(ini <= corte < fin for ini, fin in v)
            )
        serie.append({
            "mes": f"{cursor.year:04d}-{cursor.month:02d}",
            "corte": corte.isoformat(),
            "activos": activos,
        })
        cursor = (cursor + timedelta(days=32)).replace(day=1)

    return {"meses": serie[-meses:]}


@router.get("/ingresos-mensuales")
def ingresos_mensuales(
    meses: int = Query(12, ge=1, le=24),
    db: Session = Depends(get_db),
    _: Usuario = Depends(_require_admin),
):
    """Serie mensual de ingresos y egresos, en meses de Bogotá.

    El bucketing se hace en Python y no con `extract()` en SQL a propósito: las fechas
    están en UTC, así que un pago del 31 a las 20:00 locales caería en el mes siguiente.
    """
    hoy = hoy_bogota()
    primer_mes = (hoy.replace(day=1) - timedelta(days=31 * (meses - 1))).replace(day=1)
    desde_utc = _inicio_dia_utc(primer_mes)

    def _clave(fecha_utc: datetime) -> str:
        local = _a_bogota(fecha_utc)
        return f"{local.year:04d}-{local.month:02d}"

    ingresos: dict[str, float] = defaultdict(float)
    egresos: dict[str, float] = defaultdict(float)

    for fecha, monto in db.query(Pago.fecha_pago, Pago.monto).filter(Pago.fecha_pago >= desde_utc):
        ingresos[_clave(fecha)] += monto or 0
    for fecha, total in db.query(Venta.fecha_venta, Venta.total).filter(Venta.fecha_venta >= desde_utc):
        ingresos[_clave(fecha)] += total or 0
    for fecha, monto, tipo in db.query(
        MovimientoFinanciero.fecha, MovimientoFinanciero.monto, MovimientoFinanciero.tipo
    ).filter(MovimientoFinanciero.fecha >= desde_utc):
        destino = ingresos if tipo == TipoMovimiento.INGRESO else egresos
        destino[_clave(fecha)] += monto or 0

    # Serie continua: los meses sin movimiento van en cero, no ausentes.
    serie = []
    cursor = primer_mes
    while cursor <= hoy:
        clave = f"{cursor.year:04d}-{cursor.month:02d}"
        serie.append({
            "mes": clave,
            "ingresos": round(ingresos.get(clave, 0), 2),
            "egresos": round(egresos.get(clave, 0), 2),
            "neto": round(ingresos.get(clave, 0) - egresos.get(clave, 0), 2),
        })
        cursor = (cursor + timedelta(days=32)).replace(day=1)

    return {"meses": serie[-meses:]}
