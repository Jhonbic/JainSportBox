"""§8 de tests.md — Mi Salud: 6 tipos de medida, filtrado, aislamiento, IMC."""

from datetime import date

import pytest

TIPOS = {
    "peso": "peso_kg",
    "altura": "altura_cm",
    "cintura": "cintura_cm",
    "cuello": "cuello_cm",
    "cadera": "cadera_cm",
    "brazos": "brazos_cm",
}


def _payload(valor=70.5):
    return {"fecha": date.today().isoformat(), "valor": valor}


@pytest.mark.parametrize("tipo,campo", TIPOS.items())
def test_crear_y_listar_cada_tipo(client, cliente, tipo, campo):
    r = client.post(f"/salud/{tipo}", json=_payload(), headers=cliente.headers)
    assert r.status_code == 201
    body = r.json()
    assert body[campo] == 70.5
    # solo ese campo queda seteado
    otros = [c for c in TIPOS.values() if c != campo]
    assert all(body[c] is None for c in otros)

    listado = client.get(f"/salud/{tipo}", headers=cliente.headers).json()
    assert len(listado) == 1


def test_tipo_invalido_404(client, cliente):
    assert client.post("/salud/biceps", json=_payload(), headers=cliente.headers).status_code == 404
    assert client.get("/salud/biceps", headers=cliente.headers).status_code == 404


def test_valor_no_positivo_422(client, cliente):
    assert client.post("/salud/peso", json=_payload(valor=0), headers=cliente.headers).status_code == 422
    assert client.post("/salud/altura", json=_payload(valor=-170), headers=cliente.headers).status_code == 422


def test_listado_general(client, cliente):
    client.post("/salud/peso", json=_payload(80), headers=cliente.headers)
    client.post("/salud/cintura", json=_payload(85), headers=cliente.headers)
    r = client.get("/salud/", headers=cliente.headers)
    assert r.status_code == 200
    assert len(r.json()) == 2


def test_filtro_por_tipo_no_mezcla(client, cliente):
    client.post("/salud/peso", json=_payload(80), headers=cliente.headers)
    client.post("/salud/cintura", json=_payload(85), headers=cliente.headers)
    pesos = client.get("/salud/peso", headers=cliente.headers).json()
    assert len(pesos) == 1 and pesos[0]["peso_kg"] == 80


def test_imc_no_se_calcula_en_backend(client, cliente):
    """Comportamiento actual: la columna imc queda NULL — el IMC lo calcula el
    frontend (SaludView) con el último peso y la última altura. Documentado en
    tests.md § Hallazgos (CLAUDE.md decía que lo calculaba el POST)."""
    client.post("/salud/altura", json=_payload(175), headers=cliente.headers)
    r = client.post("/salud/peso", json=_payload(70), headers=cliente.headers)
    assert r.json()["imc"] is None


def test_aislamiento_entre_usuarios(client, cliente, crear_usuario):
    otro = crear_usuario("cliente")
    medida_id = client.post("/salud/peso", json=_payload(90), headers=cliente.headers).json()["id"]

    assert client.get("/salud/", headers=otro.headers).json() == []
    assert client.delete(f"/salud/{medida_id}", headers=otro.headers).status_code == 404
    assert client.delete(f"/salud/{medida_id}", headers=cliente.headers).status_code == 204


def test_salud_sin_token_401(client):
    assert client.get("/salud/").status_code == 401


def test_backend_permite_admin_aunque_frontend_lo_oculta(client, admin_headers):
    """El router no restringe por rol (la exclusión del admin es solo del
    router del frontend). Test que fija el comportamiento actual."""
    r = client.get("/salud/", headers=admin_headers)
    assert r.status_code == 200
