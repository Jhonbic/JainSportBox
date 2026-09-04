"""Planes por ingresos: carga de entradas al pagar, descuento al entrar, y los dos
ejes de vigencia (fecha Y entradas) validados juntos."""

from datetime import date, timedelta

import models
from fechas import hoy_bogota


def _plan(db_session, *, nombre, dias=30, ingresos=None):
    plan = models.Plan(
        nombre=f"{nombre} {id(db_session)}",
        precio=100.0,
        duracion_dias=dias,
        numero_ingresos=ingresos,
    )
    db_session.add(plan)
    db_session.commit()
    return plan


def _refrescar(db_session, usuario_id):
    db_session.expire_all()
    return db_session.query(models.Usuario).filter_by(id=usuario_id).one()


# ── Carga de ingresos al pagar ──────────────────────────────────


def test_pagar_plan_por_ingresos_carga_las_entradas(client, admin_headers, cliente, db_session):
    plan = _plan(db_session, nombre="Bono 10", ingresos=10)
    r = client.post(
        "/pagos/",
        json={"usuario_id": cliente.user.id, "plan_id": plan.id, "monto": 100, "metodo_pago": "efectivo"},
        headers=admin_headers,
    )
    assert r.status_code == 201
    assert _refrescar(db_session, cliente.user.id).ingresos_restantes == 10


def test_los_ingresos_no_se_acumulan(client, admin_headers, cliente, db_session):
    """Los accesos pertenecen al plan que los vendió: cada compra REEMPLAZA el saldo.

    Al revés que la fecha, que se extiende. Acá se sumaba espejando a
    `extender_vencimiento`, pero la fecha tiene corte al vencer y los accesos no lo
    tenían, así que el saldo crecía compra tras compra.
    """
    plan = _plan(db_session, nombre="Bono 8", ingresos=8)
    cuerpo = {"usuario_id": cliente.user.id, "plan_id": plan.id, "monto": 100, "metodo_pago": "efectivo"}
    client.post("/pagos/", json=cuerpo, headers=admin_headers)
    client.post("/pagos/", json=cuerpo, headers=admin_headers)
    assert _refrescar(db_session, cliente.user.id).ingresos_restantes == 8


def test_bono_vencido_no_arrastra_los_accesos_sobrantes(client, admin_headers, cliente, db_session):
    """El bug reportado: un bono de 10 con 9 sin usar y la fecha ya vencida dejaba 19
    al comprar otro bono de 10."""
    plan = _plan(db_session, nombre="Bono 10", ingresos=10)
    cuerpo = {"usuario_id": cliente.user.id, "plan_id": plan.id, "monto": 100, "metodo_pago": "efectivo"}
    client.post("/pagos/", json=cuerpo, headers=admin_headers)

    client.post(f"/asistencia/por-documento/{cliente.user.documento_identidad}", headers=admin_headers)
    assert _refrescar(db_session, cliente.user.id).ingresos_restantes == 9

    # Se le vence la membresía con 9 accesos sin gastar.
    usuario = db_session.query(models.Usuario).filter_by(id=cliente.user.id).one()
    usuario.fecha_vencimiento = date.today() - timedelta(days=1)
    db_session.commit()

    client.post("/pagos/", json=cuerpo, headers=admin_headers)
    assert _refrescar(db_session, cliente.user.id).ingresos_restantes == 10


def test_membresia_encolada_no_acumula_accesos(client, admin_headers, cliente, db_session):
    """El plan que termina se lleva sus accesos sin gastar, aunque la membresía nueva
    arranque recién cuando el anterior se acaba."""
    bono_grande = _plan(db_session, nombre="Bono 10e", dias=30, ingresos=10)
    bono_chico = _plan(db_session, nombre="Bono 4e", dias=30, ingresos=4)
    client.post(
        "/pagos/",
        json={"usuario_id": cliente.user.id, "plan_id": bono_grande.id, "monto": 100, "metodo_pago": "efectivo"},
        headers=admin_headers,
    )
    vencimiento_previo = _refrescar(db_session, cliente.user.id).fecha_vencimiento

    # Arranque "hoy" sobre una membresía vigente: el backend lo encola detrás.
    r = client.post(
        "/pagos/",
        json={
            "usuario_id": cliente.user.id,
            "plan_id": bono_chico.id,
            "monto": 40,
            "metodo_pago": "efectivo",
            "fecha_inicio": hoy_bogota().isoformat(),
        },
        headers=admin_headers,
    )
    assert r.status_code == 201

    usuario = _refrescar(db_session, cliente.user.id)
    assert usuario.fecha_vencimiento == vencimiento_previo + timedelta(days=30)  # encolada
    assert usuario.ingresos_restantes == 4  # y no 14


def test_plan_por_tiempo_sobre_bono_vigente_limpia_el_saldo(client, admin_headers, cliente, db_session):
    """La otra cara del reemplazo: pasar de un bono con accesos de sobra a una
    mensualidad deja la membresía por tiempo, sin saldo colgado."""
    bono = _plan(db_session, nombre="Bono 9", ingresos=9)
    mensual = _plan(db_session, nombre="Mensual b", dias=30)
    client.post("/pagos/", json={"usuario_id": cliente.user.id, "plan_id": bono.id, "monto": 1, "metodo_pago": "efectivo"}, headers=admin_headers)
    assert _refrescar(db_session, cliente.user.id).ingresos_restantes == 9

    client.post("/pagos/", json={"usuario_id": cliente.user.id, "plan_id": mensual.id, "monto": 1, "metodo_pago": "efectivo"}, headers=admin_headers)
    assert _refrescar(db_session, cliente.user.id).ingresos_restantes is None


def test_plan_por_tiempo_limpia_los_ingresos(client, admin_headers, cliente, db_session):
    """Sin este reset, un socio con un bono agotado (0) quedaria bloqueado pese a
    acabar de pagar la mensualidad."""
    bono = _plan(db_session, nombre="Bono 1", ingresos=1)
    mensual = _plan(db_session, nombre="Mensual", dias=30)
    client.post("/pagos/", json={"usuario_id": cliente.user.id, "plan_id": bono.id, "monto": 1, "metodo_pago": "efectivo"}, headers=admin_headers)
    assert _refrescar(db_session, cliente.user.id).ingresos_restantes == 1

    client.post("/pagos/", json={"usuario_id": cliente.user.id, "plan_id": mensual.id, "monto": 1, "metodo_pago": "efectivo"}, headers=admin_headers)
    assert _refrescar(db_session, cliente.user.id).ingresos_restantes is None


def test_activar_pendiente_con_plan_por_ingresos(client, admin_headers, crear_usuario, db_session):
    plan = _plan(db_session, nombre="Bono 5", ingresos=5)
    actor = crear_usuario("pendiente")
    r = client.post(
        f"/usuarios/{actor.user.id}/activar",
        json={"plan_id": plan.id, "monto": 100, "metodo_pago": "efectivo"},
        headers=admin_headers,
    )
    assert r.status_code == 200
    assert _refrescar(db_session, actor.user.id).ingresos_restantes == 5


# ── Descuento al entrar ─────────────────────────────────────────


def test_cada_entrada_descuenta_un_ingreso(client, admin_headers, cliente, db_session):
    plan = _plan(db_session, nombre="Bono 3", ingresos=3)
    client.post("/pagos/", json={"usuario_id": cliente.user.id, "plan_id": plan.id, "monto": 1, "metodo_pago": "efectivo"}, headers=admin_headers)

    doc = cliente.user.documento_identidad
    r = client.post(f"/asistencia/por-documento/{doc}", headers=admin_headers)
    assert r.status_code == 201
    # El cartel de recepcion muestra lo que le queda DESPUES de esta entrada.
    assert r.json()["ingresos_restantes"] == 2
    assert _refrescar(db_session, cliente.user.id).ingresos_restantes == 2


def test_remarcar_en_la_misma_sesion_no_vuelve_a_descontar(client, admin_headers, cliente, db_session):
    """El motivo caro del dedup de `_registrar`. Cada toque del lector descontaba una
    entrada del bono, así que probar el sensor tres veces le costaba tres entradas
    pagas al socio."""
    plan = _plan(db_session, nombre="Bono 3b", ingresos=3)
    client.post("/pagos/", json={"usuario_id": cliente.user.id, "plan_id": plan.id, "monto": 1, "metodo_pago": "efectivo"}, headers=admin_headers)

    doc = cliente.user.documento_identidad
    for _ in range(3):
        r = client.post(f"/asistencia/por-documento/{doc}", headers=admin_headers)
        assert r.status_code == 201
        assert r.json()["ingresos_restantes"] == 2

    assert _refrescar(db_session, cliente.user.id).ingresos_restantes == 2
    assert db_session.query(models.Asistencia).filter_by(usuario_id=cliente.user.id).count() == 1


def test_el_plan_por_tiempo_no_descuenta_nada(client, admin_headers, cliente, db_session):
    doc = cliente.user.documento_identidad
    r = client.post(f"/asistencia/por-documento/{doc}", headers=admin_headers)
    assert r.status_code == 201
    assert r.json()["ingresos_restantes"] is None
    assert _refrescar(db_session, cliente.user.id).ingresos_restantes is None


def test_sin_ingresos_niega_el_acceso_con_codigo_propio(client, admin_headers, cliente, db_session):
    """403 como el vencido, pero con detail estructurado: en el mostrador son dos
    problemas distintos ('renová' vs 'comprá más entradas')."""
    plan = _plan(db_session, nombre="Bono 1", ingresos=1)
    client.post("/pagos/", json={"usuario_id": cliente.user.id, "plan_id": plan.id, "monto": 1, "metodo_pago": "efectivo"}, headers=admin_headers)

    doc = cliente.user.documento_identidad
    assert client.post(f"/asistencia/por-documento/{doc}", headers=admin_headers).status_code == 201

    r = client.post(f"/asistencia/por-documento/{doc}", headers=admin_headers)
    assert r.status_code == 403
    assert r.json()["detail"]["codigo"] == "sin_ingresos"
    # y no se registró una segunda asistencia
    assert db_session.query(models.Asistencia).filter_by(usuario_id=cliente.user.id).count() == 1


def test_ingresos_disponibles_pero_fecha_vencida_niega(client, admin_headers, crear_usuario, db_session):
    """Los dos ejes se validan juntos: un bono con entradas de sobra igual caduca."""
    actor = crear_usuario("cliente", fecha_vencimiento=date.today() - timedelta(days=1))
    usuario = db_session.query(models.Usuario).filter_by(id=actor.user.id).one()
    usuario.ingresos_restantes = 5
    db_session.commit()

    r = client.post(f"/asistencia/por-documento/{actor.user.documento_identidad}", headers=admin_headers)
    assert r.status_code == 403
    assert "vencida" in str(r.json()["detail"]).lower()


# ── Anulación ───────────────────────────────────────────────────


def test_anular_pago_devuelve_los_ingresos(client, admin_headers, cliente, db_session):
    plan = _plan(db_session, nombre="Bono 10", ingresos=10)
    pago_id = client.post(
        "/pagos/",
        json={"usuario_id": cliente.user.id, "plan_id": plan.id, "monto": 100, "metodo_pago": "efectivo"},
        headers=admin_headers,
    ).json()["id"]
    assert _refrescar(db_session, cliente.user.id).ingresos_restantes == 10

    assert client.delete(f"/pagos/{pago_id}", headers=admin_headers).status_code == 204
    assert _refrescar(db_session, cliente.user.id).ingresos_restantes == 0


# ── CRUD del plan ───────────────────────────────────────────────


def test_crear_y_editar_plan_por_ingresos(client, admin_headers):
    r = client.post(
        "/planes/",
        json={"nombre": "Bono 12", "precio": 120000, "duracion_dias": 60, "numero_ingresos": 12},
        headers=admin_headers,
    )
    assert r.status_code == 201
    assert r.json()["numero_ingresos"] == 12 and r.json()["por_ingresos"] is True
    plan_id = r.json()["id"]

    # 0 es la unica forma de devolverlo a plan por tiempo
    r2 = client.patch(f"/planes/{plan_id}", json={"numero_ingresos": 0}, headers=admin_headers)
    assert r2.json()["numero_ingresos"] is None and r2.json()["por_ingresos"] is False
