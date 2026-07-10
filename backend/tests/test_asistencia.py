"""§5 de tests.md — Asistencia: entrada por bridge, membresía, historiales,
en-gym, sesiones-por-bloque y job de reset."""

from datetime import date, datetime, timedelta

import models
from conftest import SessionLocal


def _marcar(client, headers, usuario_id):
    return client.post(f"/asistencia/por-usuario/{usuario_id}", headers=headers)


def _usuario_db(db_session, usuario_id):
    u = db_session.query(models.Usuario).filter_by(id=usuario_id).first()
    db_session.refresh(u)
    return u


# ── POST /asistencia/por-usuario/{id} ──────────────────────────


def test_entrada_bridge_membresia_vigente(client, bridge_headers, cliente, db_session):
    r = _marcar(client, bridge_headers, cliente.user.id)
    assert r.status_code == 201
    body = r.json()
    assert body["tipo"] == "entrada"
    assert body["nombre_usuario"] == cliente.user.nombre
    assert _usuario_db(db_session, cliente.user.id).esta_en_gym is True


def test_entrada_membresia_vencida_403(client, bridge_headers, cliente_vencido, db_session):
    r = _marcar(client, bridge_headers, cliente_vencido.user.id)
    assert r.status_code == 403
    assert db_session.query(models.Asistencia).filter_by(usuario_id=cliente_vencido.user.id).count() == 0
    assert _usuario_db(db_session, cliente_vencido.user.id).esta_en_gym is False


def test_entrada_vence_hoy_permitida(client, bridge_headers, crear_usuario):
    actor = crear_usuario("cliente", fecha_vencimiento=date.today())
    assert _marcar(client, bridge_headers, actor.user.id).status_code == 201


def test_entrada_sin_vencimiento_403(client, bridge_headers, crear_usuario):
    actor = crear_usuario("cliente")  # fecha_vencimiento = None
    assert _marcar(client, bridge_headers, actor.user.id).status_code == 403


def test_doble_marcacion_crea_dos_entradas(client, bridge_headers, cliente, db_session):
    assert _marcar(client, bridge_headers, cliente.user.id).status_code == 201
    assert _marcar(client, bridge_headers, cliente.user.id).status_code == 201
    # el cooldown anti doble-registro vive en el bridge .NET, no en el backend
    regs = db_session.query(models.Asistencia).filter_by(usuario_id=cliente.user.id).all()
    assert len(regs) == 2
    assert all(a.tipo == "entrada" for a in regs)


def test_entrada_usuario_inexistente_404(client, bridge_headers):
    assert _marcar(client, bridge_headers, 999999).status_code == 404


def test_entrada_sin_auth_401(client, cliente):
    assert _marcar(client, {}, cliente.user.id).status_code == 401
    assert _marcar(client, {"X-Bridge-Secret": "malo"}, cliente.user.id).status_code == 401


def test_entrada_jwt_cliente_403(client, cliente):
    assert _marcar(client, cliente.headers, cliente.user.id).status_code == 403


def test_entrada_jwt_admin_ok(client, admin_headers, cliente):
    assert _marcar(client, admin_headers, cliente.user.id).status_code == 201


# ── POST /asistencia/ (por huella_id) ──────────────────────────


def test_entrada_por_huella(client, bridge_headers, cliente, db_session):
    db_session.query(models.Usuario).filter_by(id=cliente.user.id).update(
        {"huella_id": f"dp_{cliente.user.id}"}
    )
    db_session.commit()
    r = client.post(
        "/asistencia/",
        json={"huella_id": f"dp_{cliente.user.id}"},
        headers=bridge_headers,
    )
    assert r.status_code == 201


def test_entrada_por_huella_inexistente_404(client, bridge_headers):
    r = client.post("/asistencia/", json={"huella_id": "dp_999999"}, headers=bridge_headers)
    assert r.status_code == 404


def test_entrada_por_huella_valida_membresia(client, bridge_headers, cliente_vencido, db_session):
    """La ruta por huella_id debe rechazar membresías vencidas igual que /por-usuario."""
    db_session.query(models.Usuario).filter_by(id=cliente_vencido.user.id).update(
        {"huella_id": f"dp_{cliente_vencido.user.id}"}
    )
    db_session.commit()
    r = client.post(
        "/asistencia/",
        json={"huella_id": f"dp_{cliente_vencido.user.id}"},
        headers=bridge_headers,
    )
    assert r.status_code == 403
    assert db_session.query(models.Asistencia).filter_by(usuario_id=cliente_vencido.user.id).count() == 0


# ── Historiales ────────────────────────────────────────────────


def test_mi_historial(client, bridge_headers, cliente, db_session):
    _marcar(client, bridge_headers, cliente.user.id)
    db_session.add(
        models.Asistencia(
            usuario_id=cliente.user.id,
            tipo="entrada",
            fecha_hora=datetime.utcnow() - timedelta(days=2),
        )
    )
    db_session.commit()
    r = client.get("/asistencia/mi-historial?meses=12", headers=cliente.headers)
    assert r.status_code == 200
    body = r.json()
    assert body["total"] == 2
    assert len(body["fechas"]) == 2


def test_mi_historial_solo_propio(client, bridge_headers, cliente, crear_usuario):
    otro = crear_usuario("cliente", fecha_vencimiento=date.today() + timedelta(days=5))
    _marcar(client, bridge_headers, otro.user.id)
    r = client.get("/asistencia/mi-historial", headers=cliente.headers)
    assert r.json()["total"] == 0


def test_historial_admin_de_otro_usuario(client, admin_headers, bridge_headers, cliente):
    _marcar(client, bridge_headers, cliente.user.id)
    r = client.get(f"/asistencia/historial/{cliente.user.id}?meses=6", headers=admin_headers)
    assert r.status_code == 200
    assert r.json()["total"] == 1


def test_historial_cliente_403(client, cliente):
    assert client.get(f"/asistencia/historial/{cliente.user.id}", headers=cliente.headers).status_code == 403


def test_historial_usuario_inexistente_404(client, admin_headers):
    assert client.get("/asistencia/historial/999999", headers=admin_headers).status_code == 404


# ── GET /asistencia/en-gym ─────────────────────────────────────


def test_en_gym(client, admin_headers, bridge_headers, cliente):
    _marcar(client, bridge_headers, cliente.user.id)
    r = client.get("/asistencia/en-gym", headers=admin_headers)
    assert r.status_code == 200
    fila = next(x for x in r.json() if x["usuario_id"] == cliente.user.id)
    assert fila["minutos_sesion"] == 65
    assert 0 <= fila["minutos_transcurridos"] < 5
    assert fila["minutos_restantes"] > 60
    assert fila["entrada_desde"]


def test_en_gym_cliente_403(client, cliente):
    assert client.get("/asistencia/en-gym", headers=cliente.headers).status_code == 403


# ── GET /asistencia/sesiones-por-bloque ────────────────────────


def test_sesiones_rango_invalido(client, admin_headers):
    hoy = date.today().isoformat()
    lejos = (date.today() + timedelta(days=40)).isoformat()
    ayer = (date.today() - timedelta(days=1)).isoformat()
    assert client.get(f"/asistencia/sesiones-por-bloque?desde={hoy}&hasta={lejos}", headers=admin_headers).status_code == 422
    assert client.get(f"/asistencia/sesiones-por-bloque?desde={hoy}&hasta={ayer}", headers=admin_headers).status_code == 422


def test_sesiones_dedup_y_zona_horaria(client, admin_headers, cliente, crear_usuario, db_session):
    otro = crear_usuario("cliente", fecha_vencimiento=date.today() + timedelta(days=5))
    hoy = date.today()
    # 14:00 UTC = 09:00 Bogotá — dos entradas del mismo usuario en el mismo bloque
    base = datetime(hoy.year, hoy.month, hoy.day, 14, 5)
    db_session.add_all([
        models.Asistencia(usuario_id=cliente.user.id, tipo="entrada", fecha_hora=base),
        models.Asistencia(usuario_id=cliente.user.id, tipo="entrada", fecha_hora=base + timedelta(minutes=20)),
        models.Asistencia(usuario_id=otro.user.id, tipo="entrada", fecha_hora=base + timedelta(minutes=10)),
    ])
    db_session.commit()

    r = client.get(
        f"/asistencia/sesiones-por-bloque?desde={hoy.isoformat()}&hasta={hoy.isoformat()}",
        headers=admin_headers,
    )
    assert r.status_code == 200
    bloques = r.json()["bloques"]
    bloque9 = next(b for b in bloques if b["hora_inicio"] == 9)
    assert bloque9["total"] == 2  # deduplica al cliente repetido
    horas = {a["usuario_id"]: a["hora_exacta"] for a in bloque9["asistentes"]}
    assert horas[cliente.user.id] == "09:05"  # conserva la PRIMERA entrada, en hora Bogotá


def test_sesiones_cliente_403(client, cliente):
    hoy = date.today().isoformat()
    assert client.get(f"/asistencia/sesiones-por-bloque?desde={hoy}&hasta={hoy}", headers=cliente.headers).status_code == 403


# ── Job _job_reset_gym (unitario) ──────────────────────────────


def test_job_reset_gym(cliente, crear_usuario, db_session):
    from main import _job_reset_gym

    reciente = crear_usuario("cliente", fecha_vencimiento=date.today() + timedelta(days=5))
    viejo_id, reciente_id = cliente.user.id, reciente.user.id

    db_session.add_all([
        models.Asistencia(usuario_id=viejo_id, tipo="entrada", fecha_hora=datetime.utcnow() - timedelta(minutes=120)),
        models.Asistencia(usuario_id=reciente_id, tipo="entrada", fecha_hora=datetime.utcnow() - timedelta(minutes=5)),
    ])
    db_session.query(models.Usuario).filter(models.Usuario.id.in_([viejo_id, reciente_id])).update(
        {"esta_en_gym": True}, synchronize_session=False
    )
    db_session.commit()

    _job_reset_gym()

    db = SessionLocal()
    try:
        assert db.query(models.Usuario).filter_by(id=viejo_id).first().esta_en_gym is False
        assert db.query(models.Usuario).filter_by(id=reciente_id).first().esta_en_gym is True
        # no crea registros de salida
        assert db.query(models.Asistencia).filter_by(tipo="salida").count() == 0
    finally:
        db.close()
