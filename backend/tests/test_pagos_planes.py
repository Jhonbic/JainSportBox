"""§4 de tests.md — Planes (CRUD, solicitar) y Pagos (plan, directo, editar, anular)."""

from datetime import date, timedelta

import models


def _plan_mes_id(db_session):
    return db_session.query(models.Plan).filter_by(nombre="1 Mes").first().id


def _vencimiento(db_session, usuario_id):
    u = db_session.query(models.Usuario).filter_by(id=usuario_id).first()
    db_session.refresh(u)
    return u.fecha_vencimiento


# ── Planes ─────────────────────────────────────────────────────


def test_listar_planes_cualquier_rol(client, cliente, pendiente):
    for actor in (cliente, pendiente):
        r = client.get("/planes/", headers=actor.headers)
        assert r.status_code == 200
        nombres = {p["nombre"] for p in r.json()}
        assert {"1 Semana", "15 Días", "1 Mes"} <= nombres
        assert all(isinstance(p["beneficios"], list) for p in r.json())


def test_listar_planes_sin_token(client):
    # GET /planes/ no exige token (lo consume la pantalla pública de planes)
    assert client.get("/planes/").status_code == 200


def test_crear_plan_solo_admin(client, admin_headers, coach):
    payload = {"nombre": "Trimestre", "precio": 250000, "duracion_dias": 90, "beneficios": ["Acceso 90 días"]}
    assert client.post("/planes/", json=payload, headers=coach.headers).status_code == 403
    r = client.post("/planes/", json=payload, headers=admin_headers)
    assert r.status_code == 201
    assert r.json()["beneficios"] == ["Acceso 90 días"]


def test_patch_plan(client, admin_headers, db_session):
    plan_id = _plan_mes_id(db_session)
    r = client.patch(f"/planes/{plan_id}", json={"precio": 120000}, headers=admin_headers)
    assert r.status_code == 200
    assert r.json()["precio"] == 120000
    # restaurar para no ensuciar el seed compartido
    client.patch(f"/planes/{plan_id}", json={"precio": 100000}, headers=admin_headers)


def test_eliminar_plan_es_soft_delete(client, admin_headers, cliente, db_session):
    r = client.post(
        "/planes/",
        json={"nombre": "Temporal", "precio": 1000, "duracion_dias": 1},
        headers=admin_headers,
    )
    plan_id = r.json()["id"]
    assert client.delete(f"/planes/{plan_id}", headers=admin_headers).status_code == 204
    # sigue en BD pero inactivo, y no aparece en el listado
    p = db_session.query(models.Plan).filter_by(id=plan_id).first()
    assert p is not None and p.activo is False
    assert plan_id not in [x["id"] for x in client.get("/planes/", headers=cliente.headers).json()]


def test_solicitar_plan(client, pendiente, cliente, db_session):
    plan_id = _plan_mes_id(db_session)
    assert client.post(f"/planes/{plan_id}/solicitar", headers=cliente.headers).status_code == 403
    r = client.post(f"/planes/{plan_id}/solicitar", headers=pendiente.headers)
    assert r.status_code == 200
    u = db_session.query(models.Usuario).filter_by(id=pendiente.user.id).first()
    db_session.refresh(u)
    assert u.plan_solicitado_id == plan_id


# ── Pagos con plan ─────────────────────────────────────────────


def test_pago_usuario_sin_membresia(client, admin_headers, crear_usuario, db_session):
    actor = crear_usuario("cliente")  # sin fecha_vencimiento
    r = client.post(
        "/pagos/",
        json={"usuario_id": actor.user.id, "plan_id": _plan_mes_id(db_session), "monto": 100000, "metodo_pago": "efectivo"},
        headers=admin_headers,
    )
    assert r.status_code == 201
    assert r.json()["nueva_fecha_vencimiento"] == (date.today() + timedelta(days=30)).isoformat()


def test_pago_renovacion_extiende_desde_vencimiento(client, admin_headers, cliente, db_session):
    # cliente vence en 30 días → renovar 1 Mes debe dejar hoy+60
    r = client.post(
        "/pagos/",
        json={"usuario_id": cliente.user.id, "plan_id": _plan_mes_id(db_session), "monto": 100000, "metodo_pago": "transferencia"},
        headers=admin_headers,
    )
    assert r.status_code == 201
    assert r.json()["nueva_fecha_vencimiento"] == (date.today() + timedelta(days=60)).isoformat()


def test_pago_membresia_vencida_arranca_hoy(client, admin_headers, cliente_vencido, db_session):
    r = client.post(
        "/pagos/",
        json={"usuario_id": cliente_vencido.user.id, "plan_id": _plan_mes_id(db_session), "monto": 100000, "metodo_pago": "efectivo"},
        headers=admin_headers,
    )
    assert r.status_code == 201
    assert r.json()["nueva_fecha_vencimiento"] == (date.today() + timedelta(days=30)).isoformat()


def test_pago_plan_inactivo_404(client, admin_headers, cliente, db_session):
    plan = models.Plan(nombre="Muerto", precio=1, duracion_dias=1, activo=False)
    db_session.add(plan)
    db_session.commit()
    r = client.post(
        "/pagos/",
        json={"usuario_id": cliente.user.id, "plan_id": plan.id, "monto": 1, "metodo_pago": "efectivo"},
        headers=admin_headers,
    )
    assert r.status_code == 404


def test_pago_cliente_403(client, cliente, db_session):
    r = client.post(
        "/pagos/",
        json={"usuario_id": cliente.user.id, "plan_id": _plan_mes_id(db_session), "monto": 1, "metodo_pago": "efectivo"},
        headers=cliente.headers,
    )
    assert r.status_code == 403


def test_pago_no_crea_movimiento_financiero(client, admin_headers, cliente, db_session):
    # regresión: los pagos NO se espejan en movimientos_financieros
    antes = db_session.query(models.MovimientoFinanciero).count()
    client.post(
        "/pagos/",
        json={"usuario_id": cliente.user.id, "plan_id": _plan_mes_id(db_session), "monto": 100000, "metodo_pago": "efectivo"},
        headers=admin_headers,
    )
    assert db_session.query(models.MovimientoFinanciero).count() == antes


# ── Pago directo (personalizado) ───────────────────────────────


def test_pago_directo(client, admin_headers, crear_usuario, db_session):
    actor = crear_usuario("cliente")
    r = client.post(
        "/pagos/directo/",
        json={"usuario_id": actor.user.id, "duracion_dias": 10, "monto": 40000, "metodo_pago": "efectivo"},
        headers=admin_headers,
    )
    assert r.status_code == 201
    assert r.json()["nueva_fecha_vencimiento"] == (date.today() + timedelta(days=10)).isoformat()
    pago = db_session.query(models.Pago).filter_by(usuario_id=actor.user.id).first()
    assert pago.plan_id is None
    assert pago.duracion_dias == 10


def test_pago_directo_duracion_invalida(client, admin_headers, cliente):
    for dias in (0, 366):
        r = client.post(
            "/pagos/directo/",
            json={"usuario_id": cliente.user.id, "duracion_dias": dias, "monto": 1, "metodo_pago": "efectivo"},
            headers=admin_headers,
        )
        assert r.status_code == 422


def test_historial_muestra_personalizado(client, admin_headers, crear_usuario):
    actor = crear_usuario("cliente")
    client.post(
        "/pagos/directo/",
        json={"usuario_id": actor.user.id, "duracion_dias": 15, "monto": 60000, "metodo_pago": "transferencia"},
        headers=admin_headers,
    )
    r = client.get(f"/pagos/usuario/{actor.user.id}", headers=admin_headers)
    assert r.status_code == 200
    assert r.json()[0]["plan_nombre"] == "Personalizado (15 días)"


# ── PATCH / DELETE pago ────────────────────────────────────────


def _crear_pago_plan(client, admin_headers, usuario_id, plan_id):
    r = client.post(
        "/pagos/",
        json={"usuario_id": usuario_id, "plan_id": plan_id, "monto": 100000, "metodo_pago": "efectivo"},
        headers=admin_headers,
    )
    assert r.status_code == 201
    return r.json()["id"]


def test_editar_pago_solo_monto_y_metodo(client, admin_headers, cliente, db_session):
    pago_id = _crear_pago_plan(client, admin_headers, cliente.user.id, _plan_mes_id(db_session))
    r = client.patch(
        f"/pagos/{pago_id}",
        json={"monto": 90000, "metodo_pago": "transferencia"},
        headers=admin_headers,
    )
    assert r.status_code == 200
    assert r.json()["monto"] == 90000
    assert r.json()["metodo_pago"] == "transferencia"


def test_editar_pago_metodo_invalido(client, admin_headers, cliente, db_session):
    pago_id = _crear_pago_plan(client, admin_headers, cliente.user.id, _plan_mes_id(db_session))
    assert client.patch(f"/pagos/{pago_id}", json={"metodo_pago": "cheque"}, headers=admin_headers).status_code == 422


def test_anular_pago_plan_resta_dias(client, admin_headers, cliente, db_session):
    pago_id = _crear_pago_plan(client, admin_headers, cliente.user.id, _plan_mes_id(db_session))
    assert _vencimiento(db_session, cliente.user.id) == date.today() + timedelta(days=60)
    assert client.delete(f"/pagos/{pago_id}", headers=admin_headers).status_code == 204
    assert _vencimiento(db_session, cliente.user.id) == date.today() + timedelta(days=30)
    assert db_session.query(models.Pago).filter_by(id=pago_id).first() is None


def test_anular_pago_directo_puede_dejar_fecha_pasada(client, admin_headers, crear_usuario, db_session):
    actor = crear_usuario("cliente", fecha_vencimiento=date.today() + timedelta(days=2))
    r = client.post(
        "/pagos/directo/",
        json={"usuario_id": actor.user.id, "duracion_dias": 20, "monto": 1000, "metodo_pago": "efectivo"},
        headers=admin_headers,
    )
    pago_id = r.json()["id"]
    # anular otro pago más viejo del usuario dejaría la fecha en el pasado — correcto
    assert client.delete(f"/pagos/{pago_id}", headers=admin_headers).status_code == 204
    assert _vencimiento(db_session, actor.user.id) == date.today() + timedelta(days=2)


def test_anular_pago_inexistente(client, admin_headers):
    assert client.delete("/pagos/999999", headers=admin_headers).status_code == 404


def test_historial_orden_descendente(client, admin_headers, cliente, db_session):
    plan_id = _plan_mes_id(db_session)
    _crear_pago_plan(client, admin_headers, cliente.user.id, plan_id)
    _crear_pago_plan(client, admin_headers, cliente.user.id, plan_id)
    r = client.get(f"/pagos/usuario/{cliente.user.id}", headers=admin_headers)
    fechas = [p["fecha_pago"] for p in r.json()]
    assert fechas == sorted(fechas, reverse=True)
