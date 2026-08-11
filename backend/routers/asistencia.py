import hmac
import os
from collections import defaultdict
from datetime import date, datetime, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy import func
from sqlalchemy.orm import Session, joinedload

from database import get_db
from fechas import a_bogota, fin_dia_utc, hoy_bogota, inicio_dia_utc
from membresia import descontar_ingreso
from models import Asistencia, RolUsuario, Usuario
from schemas.asistencia import (
    AsistenciaCreate, AsistenciaResponse,
    AsistenteBloqueItem, BloqueHorario, SesionesPorBloqueResponse,
)
from security import get_current_user

router = APIRouter(prefix="/asistencia", tags=["Asistencia"])


def _require_admin_or_coach(current_user: Usuario = Depends(get_current_user)):
    if current_user.rol not in (RolUsuario.ADMIN, RolUsuario.COACH):
        raise HTTPException(status_code=403, detail="Solo admin o coach pueden realizar esta acción.")
    return current_user


def _autorizar_bridge_o_admin(request: Request, db: Session) -> None:
    bridge_secret = os.environ.get("BRIDGE_SECRET", "")
    x_secret = request.headers.get("X-Bridge-Secret", "")
    if bridge_secret and hmac.compare_digest(x_secret, bridge_secret):
        return
    from jose import jwt as jose_jwt
    from security import ALGORITHM, SECRET_KEY
    token = request.headers.get("Authorization", "").removeprefix("Bearer ").strip()
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    try:
        payload_jwt = jose_jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email = payload_jwt.get("sub")
    except Exception:
        raise HTTPException(status_code=401, detail="Not authenticated")
    caller = db.query(Usuario).filter(Usuario.email == email).first()
    if not caller or caller.rol not in (RolUsuario.ADMIN, RolUsuario.COACH):
        raise HTTPException(status_code=403, detail="Sin permisos.")


MINUTOS_SESION = 65  # tiempo máximo de una sesión; usado por el job de reset en main.py


def _validar_membresia(usuario: Usuario) -> None:
    # El staff no tiene membresía: no paga plan ni tiene fecha_vencimiento, así que
    # validarlo le daba un 403 en cada marcación. Y como la palanquera solo se abre
    # cuando el backend responde 2xx, al equipo del box la huella no le abría nunca
    # por más que estuviera enrolado.
    if usuario.rol in (RolUsuario.ADMIN, RolUsuario.COACH):
        return

    hoy = hoy_bogota()

    # Compuerta previa: la membresía se vendió para arrancar más adelante. Va antes
    # que el resto porque `fecha_vencimiento` ya está en el futuro y los dos ejes de
    # abajo la darían por buena — sin esto, "arranca el 1-sep" dejaría entrar hoy.
    if usuario.membresia_inicio and hoy < usuario.membresia_inicio:
        raise HTTPException(
            status_code=403,
            detail={
                "codigo": "no_iniciada",
                "mensaje": f"La membresía de {usuario.nombre} arranca el {usuario.membresia_inicio.isoformat()}.",
                "inicio": usuario.membresia_inicio.isoformat(),
            },
        )

    # Toda marcación es una entrada → siempre se valida la membresía. Son DOS ejes y
    # se validan los dos: un bono de ingresos también caduca por fecha, y una
    # mensualidad vigente no consume ingresos (los tiene en NULL).
    if not usuario.fecha_vencimiento or usuario.fecha_vencimiento < hoy:
        raise HTTPException(
            status_code=403,
            detail=f"Membresía vencida o sin plan activo para {usuario.nombre}.",
        )
    if usuario.ingresos_restantes is not None and usuario.ingresos_restantes <= 0:
        # Detail estructurado (y no un string como el de arriba) para que la pantalla
        # de recepción distinga "se le acabaron los ingresos" de "se le venció la
        # fecha": los dos son 403 pero el socio tiene que hacer cosas distintas.
        raise HTTPException(
            status_code=403,
            detail={
                "codigo": "sin_ingresos",
                "mensaje": f"{usuario.nombre} no tiene ingresos disponibles en su plan.",
            },
        )


def _entrada_vigente(usuario: Usuario, db: Session) -> Optional[Asistencia]:
    """La entrada abierta del socio, si volvió a marcar dentro de la misma sesión.

    Mientras el sistema lo considera adentro del box, marcar de nuevo NO es una
    entrada nueva: es la misma persona poniendo el dedo otra vez porque la
    palanquera no giró, porque probó dos dedos, o porque está probando el lector.
    La ventana es `MINUTOS_SESION` a propósito — es el mismo corte con el que
    `_job_reset_gym` apaga `esta_en_gym`, así que "hay entrada vigente" y "está en
    el box" no pueden discrepar.

    Se mira la última marcación real y no el flag `esta_en_gym`: el flag lo apaga un
    job que corre cada 3 minutos, así que entre el vencimiento de la sesión y el
    apagado hay hasta 3 minutos en los que el flag miente.
    """
    corte = datetime.utcnow() - timedelta(minutes=MINUTOS_SESION)
    return (
        db.query(Asistencia)
        .filter(
            Asistencia.usuario_id == usuario.id,
            Asistencia.tipo == "entrada",
            Asistencia.fecha_hora >= corte,
        )
        .order_by(Asistencia.fecha_hora.desc())
        .first()
    )


def _registrar(usuario: Usuario, db: Session) -> AsistenciaResponse:
    # La palanquera solo controla la ENTRADA. No se registran salidas:
    # cada marcación de huella es una entrada y enciende esta_en_gym.
    # El flag vuelve a False solo por tiempo (job _job_reset_gym en main.py).
    #
    # Re-marcar dentro de la sesión devuelve la entrada que ya existe en vez de crear
    # otra. Sin esto cada toque del lector era una fila: un socio probando el sensor
    # dejó 19 marcaciones en una mañana, y como las tarjetas de asistencia del Resumen
    # cuentan filas (el panel de sesiones deduplica por bloque horario) los dos números
    # de la misma pantalla se contradecían. Lo caro no era el KPI sino `descontar_ingreso`:
    # con un plan por ingresos, esos 19 toques le comían 19 entradas del bono.
    #
    # Sigue respondiendo 2xx a propósito: el frontend abre la palanquera solo con
    # respuesta exitosa, y si alguien marca de nuevo es justamente porque la puerta
    # no le abrió la primera vez.
    asistencia = _entrada_vigente(usuario, db)
    if asistencia is None:
        asistencia = Asistencia(usuario_id=usuario.id, tipo="entrada")
        db.add(asistencia)
        usuario.esta_en_gym = True
        # Va acá y no en cada endpoint: los tres caminos de entrada (huella, por id y por
        # documento) pasan por esta función, y descontar en uno solo dejaría bonos que no
        # se gastan según por dónde entró el socio.
        descontar_ingreso(usuario)
        db.commit()
        db.refresh(asistencia)
    return AsistenciaResponse(
        id=asistencia.id,
        usuario_id=asistencia.usuario_id,
        tipo=asistencia.tipo,
        fecha_hora=asistencia.fecha_hora,
        nombre_usuario=usuario.nombre,
    )


@router.post("/", response_model=AsistenciaResponse, status_code=status.HTTP_201_CREATED)
def registrar_asistencia(payload: AsistenciaCreate, request: Request, db: Session = Depends(get_db)):
    _autorizar_bridge_o_admin(request, db)
    usuario = db.query(Usuario).filter(Usuario.huella_id == payload.huella_id).first()
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado con esa huella.")
    _validar_membresia(usuario)
    return _registrar(usuario, db)


@router.post("/por-usuario/{usuario_id}", response_model=AsistenciaResponse, status_code=status.HTTP_201_CREATED)
def registrar_asistencia_por_id(usuario_id: int, request: Request, db: Session = Depends(get_db)):
    """
    Registra una entrada dado el usuario_id directamente.
    Usado por el bridge DigitalPersona (X-Bridge-Secret) o por admin/coach (JWT).
    Valida que la membresía esté vigente antes de permitir el acceso.
    """
    _autorizar_bridge_o_admin(request, db)
    usuario = db.query(Usuario).filter(Usuario.id == usuario_id).first()
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado.")
    _validar_membresia(usuario)
    return _registrar(usuario, db)


@router.post("/por-documento/{documento}", status_code=status.HTTP_201_CREATED)
def registrar_asistencia_por_documento(documento: str, request: Request, db: Session = Depends(get_db)):
    """
    Acceso manual desde recepción (vista /acceso): busca al usuario por cédula/TI,
    valida la membresía y registra la entrada. El frontend abre la palanquera vía
    bridge (localhost:8001) solo si esta llamada responde 201.
    """
    _autorizar_bridge_o_admin(request, db)
    doc = (documento or "").strip()
    usuario = db.query(Usuario).filter(Usuario.documento_identidad == doc).first()
    if not usuario:
        raise HTTPException(status_code=404, detail=f"No existe un usuario con documento {doc}.")
    _validar_membresia(usuario)
    asistencia = _registrar(usuario, db)
    # El staff pasa sin membresía, así que puede no tener fecha: sin este guard, un
    # coach marcando por cédula daba un 500 al restarle hoy a un None.
    dias_restantes = (usuario.fecha_vencimiento - hoy_bogota()).days if usuario.fecha_vencimiento else None
    es_staff = usuario.rol in (RolUsuario.ADMIN, RolUsuario.COACH)
    return {
        "mensaje": f"Entrada registrada para {usuario.nombre}.",
        "usuario_id": usuario.id,
        "nombre": usuario.nombre,
        "es_staff": es_staff,
        "foto_url": usuario.foto_url,
        "fecha_vencimiento": usuario.fecha_vencimiento,
        "dias_restantes": dias_restantes,
        # Lo que le queda a partir de ahora, que es lo que tiene sentido mostrarle en
        # el cartel: ya está descontado el ingreso si esta marcación abrió una entrada
        # nueva, y sin descontar si cayó dentro de una sesión en curso. None = plan por
        # tiempo, la pantalla muestra los días en su lugar.
        "ingresos_restantes": usuario.ingresos_restantes,
        "fecha_hora": asistencia.fecha_hora,
    }


@router.get("/mi-historial")
def mi_historial(
    meses: int = Query(4, ge=1, le=12),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    hoy = hoy_bogota()
    mes = hoy.month
    anio = hoy.year
    for _ in range(meses - 1):
        mes -= 1
        if mes == 0:
            mes = 12
            anio -= 1
    desde = datetime(anio, mes, 1)

    asistencias = (
        db.query(Asistencia)
        .filter(
            Asistencia.usuario_id == current_user.id,
            Asistencia.tipo == "entrada",
            Asistencia.fecha_hora >= desde,
        )
        .order_by(Asistencia.fecha_hora)
        .all()
    )

    fechas = sorted(set(a.fecha_hora.date().isoformat() for a in asistencias))
    return {"fechas": fechas, "total": len(fechas)}


@router.get("/historial/{usuario_id}")
def historial_usuario(
    usuario_id: int,
    meses: int = Query(12, ge=1, le=24),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(_require_admin_or_coach),
):
    usuario = db.query(Usuario).filter(Usuario.id == usuario_id).first()
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado.")

    hoy = hoy_bogota()
    mes = hoy.month
    anio = hoy.year
    for _ in range(meses - 1):
        mes -= 1
        if mes == 0:
            mes = 12
            anio -= 1
    desde = datetime(anio, mes, 1)

    asistencias = (
        db.query(Asistencia)
        .filter(
            Asistencia.usuario_id == usuario_id,
            Asistencia.tipo == "entrada",
            Asistencia.fecha_hora >= desde,
        )
        .order_by(Asistencia.fecha_hora)
        .all()
    )

    fechas = sorted(set(a.fecha_hora.date().isoformat() for a in asistencias))
    return {"fechas": fechas, "total": len(fechas)}


@router.get("/en-gym")
def usuarios_en_gym(
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(_require_admin_or_coach),
):
    """Usuarios con esta_en_gym=True, con su última entrada y tiempo restante de sesión."""
    # Subconsulta: última entrada por usuario (evita el N+1 de una query por usuario).
    ultima_entrada = (
        db.query(
            Asistencia.usuario_id.label("usuario_id"),
            func.max(Asistencia.fecha_hora).label("ultima"),
        )
        .filter(Asistencia.tipo == "entrada")
        .group_by(Asistencia.usuario_id)
        .subquery()
    )
    filas = (
        db.query(Usuario, ultima_entrada.c.ultima)
        .join(ultima_entrada, ultima_entrada.c.usuario_id == Usuario.id)
        .filter(Usuario.esta_en_gym == True)
        .all()
    )

    ahora = datetime.utcnow()
    resultado = []
    for u, ultima in filas:
        if not ultima:
            continue
        minutos_transcurridos = (ahora - ultima).total_seconds() / 60
        resultado.append({
            "usuario_id": u.id,
            "nombre": u.nombre,
            "foto_url": u.foto_url,
            "entrada_desde": ultima.isoformat(),
            "minutos_transcurridos": round(minutos_transcurridos, 1),
            "minutos_restantes": round(max(0, MINUTOS_SESION - minutos_transcurridos), 1),
            "minutos_sesion": MINUTOS_SESION,
        })
    resultado.sort(key=lambda x: x["minutos_transcurridos"], reverse=True)
    return resultado


@router.get("/sesiones-por-bloque", response_model=SesionesPorBloqueResponse)
def sesiones_por_bloque(
    desde: date = Query(..., description="Fecha inicio YYYY-MM-DD"),
    hasta: date = Query(..., description="Fecha fin YYYY-MM-DD"),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(_require_admin_or_coach),
):
    if desde > hasta:
        raise HTTPException(status_code=422, detail="'desde' debe ser anterior o igual a 'hasta'.")
    if (hasta - desde).days > 31:
        raise HTTPException(status_code=422, detail="El rango no puede superar 31 días.")

    # `desde`/`hasta` son días del NEGOCIO (Bogotá), pero la columna está en UTC. Antes
    # acá se construía `datetime(desde, 00:00)` naive y se comparaba directo contra la
    # columna: eso es medianoche UTC, o sea las 19:00 de Bogotá del día anterior. La
    # ventana quedaba corrida 5 horas — arrastraba la noche del día previo al rango y
    # perdía la del último día. Con el box entrenando de 19:00 a 21:00, las entradas de
    # la noche de hoy no aparecían en el calendario hasta el día siguiente.
    desde_utc = inicio_dia_utc(desde)
    hasta_utc = fin_dia_utc(hasta)

    asistencias = (
        db.query(Asistencia)
        .options(joinedload(Asistencia.usuario))
        .filter(
            Asistencia.tipo == "entrada",
            Asistencia.fecha_hora >= desde_utc,
            Asistencia.fecha_hora <= hasta_utc,
        )
        .all()
    )

    # Ordenar por fecha_hora para conservar la primera entrada en caso de duplicado
    asistencias.sort(key=lambda a: a.fecha_hora)

    vistos: dict[tuple, set[int]] = defaultdict(set)
    bloques: dict[tuple, list[AsistenteBloqueItem]] = defaultdict(list)
    for a in asistencias:
        hora_local = a_bogota(a.fecha_hora)
        key = (hora_local.date().isoformat(), hora_local.hour)
        if a.usuario_id in vistos[key]:
            continue  # ya registrado en este bloque, ignorar entradas repetidas
        vistos[key].add(a.usuario_id)
        bloques[key].append(
            AsistenteBloqueItem(
                usuario_id=a.usuario_id,
                nombre=a.usuario.nombre,
                hora_exacta=hora_local.strftime("%H:%M"),
            )
        )

    resultado = [
        BloqueHorario(
            fecha=fecha_str,
            bloque=f"{h:02d}:00–{(h + 1) % 24:02d}:00",
            hora_inicio=h,
            total=len(v),
            asistentes=sorted(v, key=lambda x: x.hora_exacta),
        )
        for (fecha_str, h), v in sorted(bloques.items())
    ]

    return SesionesPorBloqueResponse(
        desde=desde.isoformat(),
        hasta=hasta.isoformat(),
        bloques=resultado,
    )
