"""§10 de tests.md — Alertas de membresía: generación, dedup, renovación."""

from datetime import date, timedelta

import models


def _generar(client, headers):
    return client.post("/alertas/generar", headers=headers)


def _pendientes_de(db_session, usuario_id):
    return (
        db_session.query(models.AlertaMembresia)
        .filter_by(usuario_id=usuario_id, enviada=False)
        .all()
    )


def test_genera_alerta_dentro_de_ventana(client, admin_headers, crear_usuario, db_session):
    actor = crear_usuario("cliente", fecha_vencimiento=date.today() + timedelta(days=3))
    r = _generar(client, admin_headers)
    assert r.status_code == 200
    alertas = _pendientes_de(db_session, actor.user.id)
    assert len(alertas) == 1
    assert alertas[0].dias_anticipacion == 3


def test_no_genera_fuera_de_ventana(client, admin_headers, crear_usuario, db_session):
    lejos = crear_usuario("cliente", fecha_vencimiento=date.today() + timedelta(days=20))
    vencido = crear_usuario("cliente", fecha_vencimiento=date.today() - timedelta(days=1))
    _generar(client, admin_headers)
    assert _pendientes_de(db_session, lejos.user.id) == []
    assert _pendientes_de(db_session, vencido.user.id) == []


def test_generar_dos_veces_no_duplica(client, admin_headers, crear_usuario, db_session):
    actor = crear_usuario("cliente", fecha_vencimiento=date.today() + timedelta(days=5))
    _generar(client, admin_headers)
    _generar(client, admin_headers)
    assert len(_pendientes_de(db_session, actor.user.id)) == 1


def test_renovacion_descarta_pendiente_obsoleta(client, admin_headers, crear_usuario, db_session):
    actor = crear_usuario("cliente", fecha_vencimiento=date.today() + timedelta(days=2))
    _generar(client, admin_headers)
    assert len(_pendientes_de(db_session, actor.user.id)) == 1

    # renueva: nueva fecha fuera de la ventana de 7 días
    db_session.query(models.Usuario).filter_by(id=actor.user.id).update(
        {"fecha_vencimiento": date.today() + timedelta(days=32)}
    )
    db_session.commit()
    _generar(client, admin_headers)
    assert _pendientes_de(db_session, actor.user.id) == []


def test_renovacion_dentro_de_ventana_recrea(client, admin_headers, crear_usuario, db_session):
    actor = crear_usuario("cliente", fecha_vencimiento=date.today() + timedelta(days=1))
    _generar(client, admin_headers)

    db_session.query(models.Usuario).filter_by(id=actor.user.id).update(
        {"fecha_vencimiento": date.today() + timedelta(days=6)}
    )
    db_session.commit()
    _generar(client, admin_headers)

    alertas = _pendientes_de(db_session, actor.user.id)
    assert len(alertas) == 1
    assert alertas[0].dias_anticipacion == 6
    assert alertas[0].fecha_vencimiento == date.today() + timedelta(days=6)


def test_marcar_enviada_y_listados(client, admin_headers, crear_usuario, db_session):
    actor = crear_usuario("cliente", fecha_vencimiento=date.today() + timedelta(days=4))
    _generar(client, admin_headers)
    alerta = _pendientes_de(db_session, actor.user.id)[0]

    r = client.post(f"/alertas/{alerta.id}/marcar-enviada", headers=admin_headers)
    assert r.status_code == 200

    pendientes = client.get("/alertas/", headers=admin_headers).json()
    assert alerta.id not in [a["id"] for a in pendientes]
    todas = client.get("/alertas/?solo_pendientes=false", headers=admin_headers).json()
    enviada = next(a for a in todas if a["id"] == alerta.id)
    assert enviada["enviada"] is True
    assert enviada["fecha_enviada"] is not None
    assert enviada["usuario_nombre"] == actor.user.nombre


def test_contar_pendientes(client, admin_headers, crear_usuario):
    crear_usuario("cliente", fecha_vencimiento=date.today() + timedelta(days=2))
    crear_usuario("cliente", fecha_vencimiento=date.today() + timedelta(days=5))
    _generar(client, admin_headers)
    r = client.get("/alertas/contar", headers=admin_headers)
    assert r.json()["pendientes"] == 2


def test_descartar_alerta(client, admin_headers, crear_usuario, db_session):
    actor = crear_usuario("cliente", fecha_vencimiento=date.today() + timedelta(days=2))
    _generar(client, admin_headers)
    alerta = _pendientes_de(db_session, actor.user.id)[0]
    assert client.delete(f"/alertas/{alerta.id}", headers=admin_headers).status_code == 204
    assert client.delete(f"/alertas/{alerta.id}", headers=admin_headers).status_code == 404


def test_alertas_cliente_403(client, cliente):
    assert client.get("/alertas/", headers=cliente.headers).status_code == 403
    assert client.get("/alertas/contar", headers=cliente.headers).status_code == 403
    assert client.post("/alertas/generar", headers=cliente.headers).status_code == 403
