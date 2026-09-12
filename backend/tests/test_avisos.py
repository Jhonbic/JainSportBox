"""Avisos en la app: un activo por vez y "no volver a mostrar" por aviso."""

from datetime import timedelta

from fechas import hoy_bogota


def _crear(client, headers, titulo="Promo de septiembre", **extra):
    body = {"titulo": titulo, "cuerpo": "Trae un amigo y entrenan gratis.", **extra}
    return client.post("/avisos/", json=body, headers=headers)


def _mio(client, headers):
    r = client.get("/avisos/mio", headers=headers)
    assert r.status_code == 200
    return r.json()["aviso"]


def test_el_cliente_ve_el_aviso_activo(client, admin_headers, cliente):
    _crear(client, admin_headers)
    aviso = _mio(client, cliente.headers)
    assert aviso["titulo"] == "Promo de septiembre"


def test_el_pendiente_tambien_lo_ve(client, admin_headers, pendiente):
    """Es justo a quien conviene mostrarle una promo: está a un paso de pagar."""
    _crear(client, admin_headers)
    assert _mio(client, pendiente.headers) is not None


def test_el_staff_no_lo_ve(client, admin_headers, coach):
    """El cartel es para el cliente. Mezclar avisos internos en el mismo canal termina
    en que nadie lee ninguno."""
    _crear(client, admin_headers)
    assert _mio(client, coach.headers) is None
    assert _mio(client, admin_headers) is None


def test_sin_avisos_devuelve_null_y_no_404(client, cliente):
    """"No hay nada que mostrar" es el caso normal, no un error: el layout lo pide en
    cada carga de la app."""
    assert _mio(client, cliente.headers) is None


def test_marcar_visto_lo_saca_para_ese_cliente(client, admin_headers, cliente):
    aid = _crear(client, admin_headers).json()["id"]
    assert client.post(f"/avisos/{aid}/visto", headers=cliente.headers).status_code == 204
    assert _mio(client, cliente.headers) is None


def test_descartar_no_afecta_a_los_demas_clientes(client, admin_headers, cliente, crear_usuario):
    otro = crear_usuario(rol="cliente")
    aid = _crear(client, admin_headers).json()["id"]
    client.post(f"/avisos/{aid}/visto", headers=cliente.headers)
    assert _mio(client, otro.headers) is not None


def test_un_aviso_nuevo_vuelve_a_mostrarse_al_que_descarto(client, admin_headers, cliente):
    """El corazón del diseño: "no volver a mostrar" es POR AVISO, no un mute global.

    Si fuera global, la primera promo quemaría el canal para siempre — alguien la
    descarta y ya nunca se entera de que el box cierra el 24.
    """
    aid = _crear(client, admin_headers, titulo="Promo vieja").json()["id"]
    client.post(f"/avisos/{aid}/visto", headers=cliente.headers)
    assert _mio(client, cliente.headers) is None

    _crear(client, admin_headers, titulo="Cerramos el 24 y 25")
    aviso = _mio(client, cliente.headers)
    assert aviso is not None and aviso["titulo"] == "Cerramos el 24 y 25"


def test_activar_uno_apaga_los_otros(client, admin_headers):
    """De esta regla depende que un solo entero por usuario alcance para todo."""
    primero = _crear(client, admin_headers, titulo="Primero").json()["id"]
    _crear(client, admin_headers, titulo="Segundo")
    activos = [a for a in client.get("/avisos/", headers=admin_headers).json() if a["activo"]]
    assert [a["titulo"] for a in activos] == ["Segundo"]

    client.patch(f"/avisos/{primero}", json={"activo": True}, headers=admin_headers)
    activos = [a for a in client.get("/avisos/", headers=admin_headers).json() if a["activo"]]
    assert [a["titulo"] for a in activos] == ["Primero"]


def test_crear_inactivo_no_apaga_al_vigente(client, admin_headers, cliente):
    """Escribir el borrador del próximo aviso no puede bajar el que está en el aire."""
    _crear(client, admin_headers, titulo="En el aire")
    _crear(client, admin_headers, titulo="Borrador", activo=False)
    assert _mio(client, cliente.headers)["titulo"] == "En el aire"


def test_aviso_vencido_no_se_muestra(client, admin_headers, cliente):
    ayer = (hoy_bogota() - timedelta(days=1)).isoformat()
    _crear(client, admin_headers, hasta=ayer)
    assert _mio(client, cliente.headers) is None


def test_aviso_que_vence_hoy_todavia_se_muestra(client, admin_headers, cliente):
    """El corte es el día de Bogotá. Con la fecha de UTC, un aviso que vence hoy se
    apagaría a las 19:00 locales, en plena hora pico del box."""
    _crear(client, admin_headers, hasta=hoy_bogota().isoformat())
    assert _mio(client, cliente.headers) is not None


def test_apagar_el_aviso_lo_saca_de_la_pantalla(client, admin_headers, cliente):
    aid = _crear(client, admin_headers).json()["id"]
    client.patch(f"/avisos/{aid}", json={"activo": False}, headers=admin_headers)
    assert _mio(client, cliente.headers) is None


def test_boton_con_destino_peligroso_se_rechaza(client, admin_headers):
    """El destino termina en un href: un `javascript:` sería una inyección que el admin
    escribe y el cliente ejecuta."""
    r = _crear(client, admin_headers, boton_texto="Ver", boton_url="javascript:alert(1)")
    assert r.status_code == 422
    assert _crear(client, admin_headers, boton_url="/planes").status_code == 201


def test_conteo_de_descartes(client, admin_headers, cliente):
    aid = _crear(client, admin_headers).json()["id"]
    client.post(f"/avisos/{aid}/visto", headers=cliente.headers)
    fila = next(a for a in client.get("/avisos/", headers=admin_headers).json() if a["id"] == aid)
    assert fila["descartes"] == 1


def test_solo_el_admin_gestiona(client, coach, cliente):
    assert client.get("/avisos/", headers=coach.headers).status_code == 403
    assert _crear(client, coach.headers).status_code == 403
    assert _crear(client, cliente.headers).status_code == 403


def test_marcar_visto_de_un_aviso_inexistente_da_404(client, cliente):
    assert client.post("/avisos/9999/visto", headers=cliente.headers).status_code == 404
