"""§9 de tests.md — Finanzas (balance sin doble conteo, movimientos), Ventas
(stock) y Productos (CRUD, soft delete)."""

from datetime import date, datetime, timedelta

import models


def _crear_producto(client, admin_headers, precio=20000, stock=10, **kw):
    payload = {"nombre": kw.pop("nombre", "Batido Test"), "precio": precio, "stock": stock}
    payload.update(kw)
    r = client.post("/productos/", json=payload, headers=admin_headers)
    assert r.status_code == 201
    return r.json()


def _vender(client, headers, producto_id, cantidad=1):
    return client.post(
        "/ventas/",
        json={"producto_id": producto_id, "cantidad": cantidad, "metodo_pago": "efectivo"},
        headers=headers,
    )


def _mov(client, admin_headers, tipo, monto, categoria="ingreso_varios"):
    return client.post(
        "/finanzas/movimientos",
        json={
            "tipo": tipo,
            "concepto": f"{tipo} test",
            "categoria": categoria,
            "monto": monto,
            "fecha": datetime.utcnow().isoformat(),
        },
        headers=admin_headers,
    )


# ── Productos ──────────────────────────────────────────────────


def test_producto_crud_y_soft_delete(client, admin_headers, cliente):
    prod = _crear_producto(client, admin_headers)

    # editar
    r = client.put(f"/productos/{prod['id']}", json={"precio": 25000}, headers=admin_headers)
    assert r.status_code == 200 and r.json()["precio"] == 25000

    # delete = soft (activo False), el cliente deja de verlo
    assert client.delete(f"/productos/{prod['id']}", headers=admin_headers).status_code == 204
    ids_cliente = [p["id"] for p in client.get("/productos/", headers=cliente.headers).json()]
    assert prod["id"] not in ids_cliente
    # staff lo sigue viendo con solo_activos=false
    ids_staff = [p["id"] for p in client.get("/productos/?solo_activos=false", headers=admin_headers).json()]
    assert prod["id"] in ids_staff


def test_cliente_siempre_ve_solo_activos(client, admin_headers, cliente):
    prod = _crear_producto(client, admin_headers)
    client.delete(f"/productos/{prod['id']}", headers=admin_headers)
    # aunque pida solo_activos=false, al cliente se le fuerza activos
    ids = [p["id"] for p in client.get("/productos/?solo_activos=false", headers=cliente.headers).json()]
    assert prod["id"] not in ids


def test_crear_producto_cliente_403(client, cliente):
    r = client.post("/productos/", json={"nombre": "X", "precio": 1, "stock": 1}, headers=cliente.headers)
    assert r.status_code == 403


# ── Ventas ─────────────────────────────────────────────────────


def test_venta_descuenta_stock_y_no_espeja_movimiento(client, admin_headers, db_session):
    prod = _crear_producto(client, admin_headers, precio=20000, stock=10)
    antes_mov = db_session.query(models.MovimientoFinanciero).count()

    r = _vender(client, admin_headers, prod["id"], cantidad=3)
    assert r.status_code == 201
    body = r.json()
    assert body["total"] == 60000
    assert body["precio_unitario"] == 20000

    p = db_session.query(models.Producto).filter_by(id=prod["id"]).first()
    assert p.stock == 7
    # regresión commit 8b8ff01: la venta NO crea MovimientoFinanciero
    assert db_session.query(models.MovimientoFinanciero).count() == antes_mov


def test_venta_stock_insuficiente_400(client, admin_headers, db_session):
    prod = _crear_producto(client, admin_headers, stock=2)
    assert _vender(client, admin_headers, prod["id"], cantidad=3).status_code == 400
    p = db_session.query(models.Producto).filter_by(id=prod["id"]).first()
    assert p.stock == 2  # intacto


def test_venta_producto_inactivo_400(client, admin_headers):
    prod = _crear_producto(client, admin_headers)
    client.delete(f"/productos/{prod['id']}", headers=admin_headers)
    assert _vender(client, admin_headers, prod["id"]).status_code == 400


def test_venta_producto_inexistente_404(client, admin_headers):
    assert _vender(client, admin_headers, 999999).status_code == 404


def test_venta_cantidad_invalida_422(client, admin_headers):
    prod = _crear_producto(client, admin_headers)
    assert _vender(client, admin_headers, prod["id"], cantidad=0).status_code == 422


def test_venta_cliente_403(client, admin_headers, cliente):
    prod = _crear_producto(client, admin_headers)
    assert _vender(client, cliente.headers, prod["id"]).status_code == 403


def test_listar_ventas(client, admin_headers):
    prod = _crear_producto(client, admin_headers)
    _vender(client, admin_headers, prod["id"])
    r = client.get("/ventas/", headers=admin_headers)
    assert r.status_code == 200 and len(r.json()) == 1


# ── Balance ────────────────────────────────────────────────────


def test_balance_sin_doble_conteo(client, admin_headers, cliente, db_session):
    # 1 pago de membresía (100k) + 1 venta (20k) + 1 ingreso manual (10k) + 1 egreso (5k)
    plan = db_session.query(models.Plan).filter_by(nombre="1 Mes").first()
    client.post(
        "/pagos/",
        json={"usuario_id": cliente.user.id, "plan_id": plan.id, "monto": 100000, "metodo_pago": "efectivo"},
        headers=admin_headers,
    )
    prod = _crear_producto(client, admin_headers, precio=20000, stock=5)
    _vender(client, admin_headers, prod["id"])
    assert _mov(client, admin_headers, "ingreso", 10000).status_code == 201
    assert _mov(client, admin_headers, "egreso", 5000, categoria="servicios").status_code == 201

    r = client.get("/finanzas/balance", headers=admin_headers)
    assert r.status_code == 200
    b = r.json()
    assert b["ingresos_total"] == 130000  # exactamente la suma, sin espejos
    assert b["total_membresias"] == 100000
    assert b["total_tienda"] == 20000
    assert b["egresos_total"] == 5000
    assert b["balance_neto"] == 125000
    assert b["ingresos_por_categoria"]["ingreso_varios"] == 10000
    assert b["egresos_por_categoria"]["servicios"] == 5000


def test_balance_filtro_fechas_excluye(client, admin_headers):
    _mov(client, admin_headers, "ingreso", 10000)
    manana = (date.today() + timedelta(days=1)).isoformat()
    r = client.get(f"/finanzas/balance?fecha_desde={manana}", headers=admin_headers)
    assert r.json()["ingresos_total"] == 0


def test_balance_solo_admin(client, coach, cliente):
    assert client.get("/finanzas/balance", headers=coach.headers).status_code == 403
    assert client.get("/finanzas/balance", headers=cliente.headers).status_code == 403


# ── Movimientos ────────────────────────────────────────────────


def test_movimientos_unifica_tres_fuentes(client, admin_headers, cliente, db_session):
    plan = db_session.query(models.Plan).filter_by(nombre="1 Semana").first()
    client.post(
        "/pagos/",
        json={"usuario_id": cliente.user.id, "plan_id": plan.id, "monto": 35000, "metodo_pago": "efectivo"},
        headers=admin_headers,
    )
    prod = _crear_producto(client, admin_headers)
    _vender(client, admin_headers, prod["id"])
    _mov(client, admin_headers, "egreso", 1000, categoria="servicios")

    r = client.get("/finanzas/movimientos", headers=admin_headers)
    assert r.status_code == 200
    items = r.json()
    prefijos = {i["id"].split("_")[0] for i in items}
    assert prefijos == {"pago", "venta", "mov"}
    # solo los manuales son eliminables
    for i in items:
        assert i["es_eliminable"] == i["id"].startswith("mov_")


def test_movimientos_filtro_egreso(client, admin_headers, cliente, db_session):
    plan = db_session.query(models.Plan).first()
    client.post(
        "/pagos/",
        json={"usuario_id": cliente.user.id, "plan_id": plan.id, "monto": 35000, "metodo_pago": "efectivo"},
        headers=admin_headers,
    )
    _mov(client, admin_headers, "egreso", 1000, categoria="servicios")
    items = client.get("/finanzas/movimientos?tipo=egreso", headers=admin_headers).json()
    assert len(items) == 1 and items[0]["tipo"] == "egreso"


def test_eliminar_movimiento_manual(client, admin_headers, db_session):
    _mov(client, admin_headers, "ingreso", 500)
    mov = db_session.query(models.MovimientoFinanciero).first()
    assert client.delete(f"/finanzas/movimientos/{mov.id}", headers=admin_headers).status_code == 204


def test_eliminar_movimiento_no_manual_404(client, admin_headers, db_session):
    db_session.add(models.MovimientoFinanciero(
        tipo=models.TipoMovimiento.INGRESO, concepto="legacy", categoria="mensualidad",
        monto=100, fecha=datetime.utcnow(), fuente="pago_directo",
    ))
    db_session.commit()
    mov = db_session.query(models.MovimientoFinanciero).first()
    assert client.delete(f"/finanzas/movimientos/{mov.id}", headers=admin_headers).status_code == 404


def test_movimiento_monto_invalido_422(client, admin_headers):
    assert _mov(client, admin_headers, "ingreso", 0).status_code == 422
    assert _mov(client, admin_headers, "regalo", 100).status_code == 422


def test_buscar_usuarios(client, admin_headers, crear_usuario):
    actor = crear_usuario("cliente", nombre="Fulanito Buscable")
    r = client.get("/finanzas/usuarios/buscar?q=Buscable", headers=admin_headers)
    assert r.status_code == 200
    assert [u["id"] for u in r.json()] == [actor.user.id]
