"""§11 de tests.md — Métodos de pago: orden, activo, permisos."""


def _crear(client, headers, banco="Bancolombia", tipo="ahorros", numero="123-456"):
    return client.post(
        "/metodos-pago/",
        json={"banco": banco, "tipo_cuenta": tipo, "numero_cuenta": numero},
        headers=headers,
    )


def test_crear_asigna_orden_incremental(client, admin_headers):
    r1 = _crear(client, admin_headers, banco="Banco A")
    r2 = _crear(client, admin_headers, banco="Banco B")
    assert r1.status_code == 201 and r2.status_code == 201
    assert r2.json()["orden"] == r1.json()["orden"] + 1


def test_listado_ordenado_y_visible_para_cliente(client, admin_headers, cliente):
    _crear(client, admin_headers, banco="Primero")
    _crear(client, admin_headers, banco="Segundo")
    r = client.get("/metodos-pago/", headers=cliente.headers)
    assert r.status_code == 200
    bancos = [m["banco"] for m in r.json()]
    assert bancos == ["Primero", "Segundo"]


def test_patch_orden_reordena(client, admin_headers):
    id_a = _crear(client, admin_headers, banco="A").json()["id"]
    _crear(client, admin_headers, banco="B")
    client.patch(f"/metodos-pago/{id_a}", json={"orden": 99}, headers=admin_headers)
    bancos = [m["banco"] for m in client.get("/metodos-pago/", headers=admin_headers).json()]
    assert bancos == ["B", "A"]


def test_desactivar_lo_saca_del_listado(client, admin_headers):
    mid = _crear(client, admin_headers).json()["id"]
    client.patch(f"/metodos-pago/{mid}", json={"activo": False}, headers=admin_headers)
    ids = [m["id"] for m in client.get("/metodos-pago/", headers=admin_headers).json()]
    assert mid not in ids


def test_eliminar(client, admin_headers):
    mid = _crear(client, admin_headers).json()["id"]
    assert client.delete(f"/metodos-pago/{mid}", headers=admin_headers).status_code == 204
    assert client.delete(f"/metodos-pago/{mid}", headers=admin_headers).status_code == 404


def test_solo_admin_gestiona(client, coach, cliente):
    assert _crear(client, coach.headers).status_code == 403
    assert _crear(client, cliente.headers).status_code == 403
    assert client.patch("/metodos-pago/1", json={"orden": 1}, headers=coach.headers).status_code == 403
    assert client.delete("/metodos-pago/1", headers=coach.headers).status_code == 403


def test_listado_requiere_token(client):
    assert client.get("/metodos-pago/").status_code == 401
