"""Plantillas editables de los mensajes de WhatsApp (cobro y cumpleaños)."""

TEXTO = "Hola {nombre}! Te esperamos en el box 💪"


def _overrides(client, headers):
    """El GET devuelve `{overrides, envio_automatico}`; casi todo mira lo primero."""
    r = client.get("/mensajes/", headers=headers)
    assert r.status_code == 200
    return r.json()["overrides"]


def test_listado_arranca_vacio(client, admin_headers):
    """Sin overrides no hay filas: una clave ausente significa "usá el default del
    frontend", que es donde vive el texto de fábrica."""
    assert _overrides(client, admin_headers) == {}


def test_listado_informa_si_el_envio_automatico_esta_prendido(client, admin_headers):
    """El editor decide con esto si muestra el aviso de que la plantilla `vence` no
    aplica al envío de las 9:10. En los tests el conftest vacía las credenciales de
    Meta, así que acá siempre es False — que es también el caso del box sin la API
    configurada, donde ese aviso sería una advertencia sobre algo que no ocurre."""
    r = client.get("/mensajes/", headers=admin_headers)
    assert r.json()["envio_automatico"] is False


def test_guardar_y_leer(client, admin_headers):
    r = client.put("/mensajes/cumpleanos", json={"texto": TEXTO}, headers=admin_headers)
    assert r.status_code == 200
    assert _overrides(client, admin_headers) == {"cumpleanos": TEXTO}


def test_guardar_dos_veces_actualiza_sin_duplicar(client, admin_headers):
    """El PUT es un upsert: sin eso, editar el mismo mensaje reventaría contra el
    unique de `clave`."""
    client.put("/mensajes/vence", json={"texto": "primero"}, headers=admin_headers)
    r = client.put("/mensajes/vence", json={"texto": "segundo"}, headers=admin_headers)
    assert r.status_code == 200
    assert _overrides(client, admin_headers) == {"vence": "segundo"}


def test_restaurar_borra_la_fila(client, admin_headers):
    """Restaurar NO guarda el texto de fábrica: borra el override. Guardarlo lo
    congelaría y una mejora futura del default no le llegaría nunca."""
    client.put("/mensajes/vencida", json={"texto": TEXTO}, headers=admin_headers)
    r = client.delete("/mensajes/vencida", headers=admin_headers)
    assert r.status_code == 204
    assert _overrides(client, admin_headers) == {}


def test_restaurar_algo_nunca_editado_no_falla(client, admin_headers):
    """El botón se puede tocar dos veces seguidas; el segundo no tiene fila que borrar."""
    assert client.delete("/mensajes/sin_accesos", headers=admin_headers).status_code == 204


def test_clave_desconocida_da_404(client, admin_headers):
    """La whitelist es lo único que impide que un PUT deje filas basura en la tabla."""
    assert client.put("/mensajes/loquesea", json={"texto": TEXTO}, headers=admin_headers).status_code == 404
    assert client.delete("/mensajes/loquesea", headers=admin_headers).status_code == 404


def test_texto_vacio_se_rechaza(client, admin_headers):
    """Un mensaje vacío abriría WhatsApp sin nada escrito: peor que el default."""
    assert client.put("/mensajes/vence", json={"texto": ""}, headers=admin_headers).status_code == 422
    assert client.put("/mensajes/vence", json={"texto": "   "}, headers=admin_headers).status_code == 422


def test_coach_lee_pero_no_edita(client, admin_headers, coach):
    """El coach manda los mismos recordatorios desde el Resumen, así que necesita el
    texto personalizado; editarlo es decisión del admin."""
    client.put("/mensajes/cumpleanos", json={"texto": TEXTO}, headers=admin_headers)
    assert _overrides(client, coach.headers) == {"cumpleanos": TEXTO}
    assert client.put("/mensajes/cumpleanos", json={"texto": "otro"}, headers=coach.headers).status_code == 403
    assert client.delete("/mensajes/cumpleanos", headers=coach.headers).status_code == 403


def test_cliente_no_ve_los_mensajes(client, cliente):
    assert client.get("/mensajes/", headers=cliente.headers).status_code == 403
