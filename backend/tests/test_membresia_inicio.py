"""Fecha de inicio de la membresía y membresías personalizadas con accesos.

Dos capacidades que se agregaron juntas a los cuatro caminos que asignan membresía
(`/pagos/`, `/pagos/directo/`, la activación de un pendiente y la anulación que
revierte): elegir cuándo arranca, y en las personalizadas cuántos accesos incluye.
"""

from datetime import timedelta

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


# ── La fecha de inicio como piso ────────────────────────────────


def test_inicio_futuro_sin_membresia_previa_corre_la_ventana(client, admin_headers, crear_usuario, db_session):
    """Sin nada vigente, el vencimiento se cuenta desde la fecha elegida, no desde hoy."""
    actor = crear_usuario("cliente")
    inicio = hoy_bogota() + timedelta(days=10)

    r = client.post(
        "/pagos/directo/",
        json={
            "usuario_id": actor.user.id,
            "duracion_dias": 30,
            "monto": 100,
            "metodo_pago": "efectivo",
            "fecha_inicio": inicio.isoformat(),
        },
        headers=admin_headers,
    )
    assert r.status_code == 201
    assert _refrescar(db_session, actor.user.id).fecha_vencimiento == inicio + timedelta(days=30)


def test_inicio_anterior_al_vencimiento_encola_y_no_pierde_dias(client, admin_headers, cliente, db_session):
    """El caso que motivó la regla: el socio tiene 30 días por delante y renueva hoy.

    La fecha de inicio entra como piso, no como reemplazo — si mandara, los 30 días
    que le quedaban se perderían.
    """
    vencimiento_previo = _refrescar(db_session, cliente.user.id).fecha_vencimiento

    r = client.post(
        "/pagos/directo/",
        json={
            "usuario_id": cliente.user.id,
            "duracion_dias": 30,
            "monto": 100,
            "metodo_pago": "efectivo",
            "fecha_inicio": hoy_bogota().isoformat(),
        },
        headers=admin_headers,
    )
    assert r.status_code == 201
    usuario = _refrescar(db_session, cliente.user.id)
    assert usuario.fecha_vencimiento == vencimiento_previo + timedelta(days=30)
    # Arranca detrás de la vigente, así que no hay nada que bloquear.
    assert usuario.membresia_inicio is None


def test_inicio_en_el_pasado_es_422(client, admin_headers, cliente):
    r = client.post(
        "/pagos/directo/",
        json={
            "usuario_id": cliente.user.id,
            "duracion_dias": 30,
            "monto": 100,
            "metodo_pago": "efectivo",
            "fecha_inicio": (hoy_bogota() - timedelta(days=1)).isoformat(),
        },
        headers=admin_headers,
    )
    assert r.status_code == 422


def test_plan_del_catalogo_tambien_acepta_fecha_de_inicio(client, admin_headers, crear_usuario, db_session):
    actor = crear_usuario("cliente")
    plan = _plan(db_session, nombre="Mensual")
    inicio = hoy_bogota() + timedelta(days=5)

    r = client.post(
        "/pagos/",
        json={
            "usuario_id": actor.user.id,
            "plan_id": plan.id,
            "monto": 100,
            "metodo_pago": "efectivo",
            "fecha_inicio": inicio.isoformat(),
        },
        headers=admin_headers,
    )
    assert r.status_code == 201
    assert _refrescar(db_session, actor.user.id).fecha_vencimiento == inicio + timedelta(days=30)


# ── La compuerta: no se entra antes de que arranque ─────────────


def test_membresia_que_aun_no_arranco_niega_el_acceso(client, admin_headers, crear_usuario, db_session):
    """Sin esta compuerta la fecha de inicio sería decorativa: `fecha_vencimiento`
    ya quedó en el futuro, así que los dos ejes de siempre la darían por buena."""
    actor = crear_usuario("cliente")
    inicio = hoy_bogota() + timedelta(days=7)
    client.post(
        "/pagos/directo/",
        json={
            "usuario_id": actor.user.id,
            "duracion_dias": 30,
            "monto": 100,
            "metodo_pago": "efectivo",
            "fecha_inicio": inicio.isoformat(),
        },
        headers=admin_headers,
    )

    r = client.post(f"/asistencia/por-documento/{actor.user.documento_identidad}", headers=admin_headers)
    assert r.status_code == 403
    assert r.json()["detail"]["codigo"] == "no_iniciada"
    assert r.json()["detail"]["inicio"] == inicio.isoformat()
    assert db_session.query(models.Asistencia).filter_by(usuario_id=actor.user.id).count() == 0


def test_llegado_el_dia_la_membresia_deja_entrar(client, admin_headers, crear_usuario, db_session):
    actor = crear_usuario("cliente")
    client.post(
        "/pagos/directo/",
        json={
            "usuario_id": actor.user.id,
            "duracion_dias": 30,
            "monto": 100,
            "metodo_pago": "efectivo",
            "fecha_inicio": (hoy_bogota() + timedelta(days=3)).isoformat(),
        },
        headers=admin_headers,
    )
    # Se adelanta el reloj moviendo el arranque a hoy, que es lo que pasaría solo.
    usuario = db_session.query(models.Usuario).filter_by(id=actor.user.id).one()
    usuario.membresia_inicio = hoy_bogota()
    db_session.commit()

    r = client.post(f"/asistencia/por-documento/{actor.user.documento_identidad}", headers=admin_headers)
    assert r.status_code == 201


# ── Accesos en la membresía personalizada ───────────────────────


def test_personalizado_con_accesos_los_carga(client, admin_headers, cliente, db_session):
    r = client.post(
        "/pagos/directo/",
        json={
            "usuario_id": cliente.user.id,
            "duracion_dias": 30,
            "numero_ingresos": 12,
            "monto": 100,
            "metodo_pago": "efectivo",
        },
        headers=admin_headers,
    )
    assert r.status_code == 201
    assert _refrescar(db_session, cliente.user.id).ingresos_restantes == 12


def test_anular_personalizado_devuelve_los_accesos(client, admin_headers, cliente, db_session):
    """Antes `DELETE /pagos/{id}` pasaba None fijo para los pagos sin plan, así que
    los accesos de un personalizado se quedaban cargados tras anularlo."""
    pago_id = client.post(
        "/pagos/directo/",
        json={
            "usuario_id": cliente.user.id,
            "duracion_dias": 30,
            "numero_ingresos": 10,
            "monto": 100,
            "metodo_pago": "efectivo",
        },
        headers=admin_headers,
    ).json()["id"]
    assert _refrescar(db_session, cliente.user.id).ingresos_restantes == 10

    assert client.delete(f"/pagos/{pago_id}", headers=admin_headers).status_code == 204
    assert _refrescar(db_session, cliente.user.id).ingresos_restantes == 0


def test_personalizado_sin_accesos_destraba_un_bono_agotado(client, admin_headers, cliente, db_session):
    """Regresión del agujero que tenía el pago directo: no tocaba `ingresos_restantes`
    nunca, así que venderle 30 días por tiempo a alguien con el bono en 0 lo dejaba
    igual de bloqueado."""
    usuario = db_session.query(models.Usuario).filter_by(id=cliente.user.id).one()
    usuario.ingresos_restantes = 0
    db_session.commit()

    r = client.post(
        "/pagos/directo/",
        json={"usuario_id": cliente.user.id, "duracion_dias": 30, "monto": 100, "metodo_pago": "efectivo"},
        headers=admin_headers,
    )
    assert r.status_code == 201
    assert _refrescar(db_session, cliente.user.id).ingresos_restantes is None

    assert client.post(
        f"/asistencia/por-documento/{cliente.user.documento_identidad}", headers=admin_headers
    ).status_code == 201


# ── Activación de un pendiente con membresía personalizada ──────


def test_activar_pendiente_con_dias_personalizados(client, admin_headers, crear_usuario, db_session):
    """El modal de activar era el único de los cuatro sin opción personalizada."""
    actor = crear_usuario("pendiente")

    r = client.post(
        f"/usuarios/{actor.user.id}/activar",
        json={"duracion_dias": 45, "numero_ingresos": 20, "monto": 150, "metodo_pago": "efectivo"},
        headers=admin_headers,
    )
    assert r.status_code == 200

    usuario = _refrescar(db_session, actor.user.id)
    assert usuario.rol == models.RolUsuario.CLIENTE
    assert usuario.fecha_vencimiento == hoy_bogota() + timedelta(days=45)
    assert usuario.ingresos_restantes == 20

    pago = db_session.query(models.Pago).filter_by(usuario_id=actor.user.id).one()
    assert pago.plan_id is None
    assert pago.duracion_dias == 45
    assert pago.numero_ingresos == 20


def test_activar_con_plan_y_dias_a_la_vez_es_422(client, admin_headers, crear_usuario, db_session):
    """Son excluyentes: aceptar los dos obligaría a elegir cuál gana, y cualquier
    criterio sorprendería a quien cargó el otro."""
    actor = crear_usuario("pendiente")
    plan = _plan(db_session, nombre="Mensual")

    r = client.post(
        f"/usuarios/{actor.user.id}/activar",
        json={"plan_id": plan.id, "duracion_dias": 45, "monto": 150, "metodo_pago": "efectivo"},
        headers=admin_headers,
    )
    assert r.status_code == 422


def test_activar_sin_plan_ni_dias_es_422(client, admin_headers, crear_usuario):
    actor = crear_usuario("pendiente")
    r = client.post(
        f"/usuarios/{actor.user.id}/activar",
        json={"monto": 150, "metodo_pago": "efectivo"},
        headers=admin_headers,
    )
    assert r.status_code == 422
