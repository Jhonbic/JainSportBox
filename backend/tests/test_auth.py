"""§2 de tests.md — Auth: login, registro público, /me, tokens, rate limit."""

import uuid
from datetime import date, timedelta

import models
from conftest import (
    ADMIN_EMAIL,
    ADMIN_PASSWORD,
    PASSWORD,
    PNG_BYTES,
    SessionLocal,
    auth_headers,
    token_para,
)
from security import create_access_token


def _login(client, email, password):
    return client.post("/login", data={"username": email, "password": password})


def _form_registro(**overrides):
    sufijo = uuid.uuid4().hex[:8]
    data = {
        "nombre": f"Registro {sufijo}",
        "email": f"reg{sufijo}@test.local",
        "password": "unaClaveLarga1",
        "documento_identidad": f"d{sufijo}",
        "genero": "masculino",
        "telefono": "3009998877",
        "fecha_nacimiento": "1995-05-10",
        "eps": "Nueva EPS",
        "barrio": "Centro",
        "contacto_emergencia_nombre": "Contacto Emergencia",
        "contacto_emergencia_telefono": "3111112233",
        "acepta_terminos": "true",
    }
    data.update(overrides)
    return data


def _fecha_menor():
    """Fecha de nacimiento de alguien con ~15 años."""
    hoy = date.today()
    return date(hoy.year - 15, hoy.month, hoy.day).isoformat()


# ── Login ──────────────────────────────────────────────────────


def test_login_ok(client):
    r = _login(client, ADMIN_EMAIL, ADMIN_PASSWORD)
    assert r.status_code == 200
    body = r.json()
    assert body["token_type"] == "bearer"
    assert body["access_token"]


def test_login_password_incorrecto(client):
    r = _login(client, ADMIN_EMAIL, "clave-mala")
    assert r.status_code == 401


def test_login_email_inexistente(client):
    r = _login(client, "nadie@test.local", "loquesea")
    assert r.status_code == 401


def test_login_normaliza_email(client):
    r = _login(client, f"  {ADMIN_EMAIL.upper()}  ", ADMIN_PASSWORD)
    assert r.status_code == 200


def test_login_rate_limit(client):
    # bucket "login": 10 por 5 min por IP
    for _ in range(10):
        r = _login(client, "fuerza-bruta@test.local", "x")
        assert r.status_code == 401
    r = _login(client, "fuerza-bruta@test.local", "x")
    assert r.status_code == 429
    assert "Retry-After" in r.headers


# ── Registro público ───────────────────────────────────────────


def test_registro_ok_sin_foto(client, db_session):
    data = _form_registro()
    r = client.post("/registro", data=data)
    assert r.status_code == 201
    u = db_session.query(models.Usuario).filter_by(email=data["email"]).first()
    assert u is not None
    assert u.rol == models.RolUsuario.PENDIENTE
    assert u.eps == "Nueva EPS"
    assert u.barrio == "Centro"
    assert u.contacto_emergencia_nombre == "Contacto Emergencia"
    assert u.contacto_emergencia_telefono == "3111112233"
    assert u.es_menor is False
    # Registro de la aceptación del contrato (Ley 527 de 1999)
    assert u.acepto_terminos is True
    assert u.terminos_fecha is not None
    assert u.terminos_version
    # login inmediato con la cuenta creada
    assert _login(client, data["email"], data["password"]).status_code == 200


def test_registro_con_foto(client, db_session):
    data = _form_registro()
    r = client.post(
        "/registro",
        data=data,
        files={"foto": ("perfil.png", PNG_BYTES, "image/png")},
    )
    assert r.status_code == 201
    u = db_session.query(models.Usuario).filter_by(email=data["email"]).first()
    assert u.foto_url and u.foto_url.startswith("/uploads/")


def test_registro_email_duplicado_case_insensitive(client):
    data = _form_registro()
    assert client.post("/registro", data=data).status_code == 201
    data2 = _form_registro(email=data["email"].upper())
    r = client.post("/registro", data=data2)
    assert r.status_code == 400


def test_registro_documento_duplicado(client):
    data = _form_registro()
    assert client.post("/registro", data=data).status_code == 201
    data2 = _form_registro(documento_identidad=data["documento_identidad"])
    r = client.post("/registro", data=data2)
    assert r.status_code == 400


def test_registro_como_json_falla(client):
    r = client.post("/registro", json=_form_registro())
    assert r.status_code == 422


def test_registro_genero_invalido(client):
    r = client.post("/registro", data=_form_registro(genero="otro"))
    assert r.status_code == 422


def test_registro_password_corta(client):
    r = client.post("/registro", data=_form_registro(password="corta"))
    assert r.status_code == 422


def test_registro_sin_aceptar_terminos(client):
    r = client.post("/registro", data=_form_registro(acepta_terminos="false"))
    assert r.status_code == 422


def test_registro_sin_campo_terminos(client):
    data = _form_registro()
    del data["acepta_terminos"]
    r = client.post("/registro", data=data)
    assert r.status_code == 422


def test_registro_sin_fecha_nacimiento(client):
    data = _form_registro()
    del data["fecha_nacimiento"]
    r = client.post("/registro", data=data)
    assert r.status_code == 422


def test_registro_menor_sin_casilla(client):
    # Fecha de nacimiento de menor sin marcar es_menor → 422
    r = client.post("/registro", data=_form_registro(fecha_nacimiento=_fecha_menor()))
    assert r.status_code == 422


def test_registro_menor_sin_acudiente(client):
    r = client.post("/registro", data=_form_registro(fecha_nacimiento=_fecha_menor(), es_menor="true"))
    assert r.status_code == 422


def test_registro_menor_sin_cedula_acudiente(client):
    r = client.post("/registro", data=_form_registro(
        fecha_nacimiento=_fecha_menor(),
        es_menor="true",
        acudiente_nombre="Acudiente Legal",
        acudiente_telefono="3224445566",
    ))
    assert r.status_code == 422


def test_registro_menor_con_acudiente(client, db_session):
    data = _form_registro(
        fecha_nacimiento=_fecha_menor(),
        es_menor="true",
        acudiente_nombre="Acudiente Legal",
        acudiente_telefono="3224445566",
        acudiente_documento="1098765432",
    )
    r = client.post("/registro", data=data)
    assert r.status_code == 201
    u = db_session.query(models.Usuario).filter_by(email=data["email"]).first()
    assert u.es_menor is True
    assert u.acudiente_nombre == "Acudiente Legal"
    assert u.acudiente_telefono == "3224445566"
    assert u.acudiente_documento == "1098765432"


def test_pendientes_expone_datos_acudiente(client, db_session):
    """El admin debe poder ver en /usuarios/pendientes si el registro es de un
    menor y los datos del acudiente para confirmarlos antes de activar."""
    data = _form_registro(
        fecha_nacimiento=_fecha_menor(),
        es_menor="true",
        acudiente_nombre="Acudiente Legal",
        acudiente_telefono="3224445566",
        acudiente_documento="1098765432",
    )
    assert client.post("/registro", data=data).status_code == 201

    admin_token = token_para(ADMIN_EMAIL)
    r = client.get("/usuarios/pendientes", headers=auth_headers(admin_token))
    assert r.status_code == 200
    pendiente = next(p for p in r.json() if p["email"] == data["email"])
    assert pendiente["es_menor"] is True
    assert pendiente["acudiente_nombre"] == "Acudiente Legal"
    assert pendiente["acudiente_telefono"] == "3224445566"
    assert pendiente["acudiente_documento"] == "1098765432"
    assert pendiente["eps"] == "Nueva EPS"


def test_registro_rate_limit(client):
    # bucket "registro": 5 por hora por IP
    for _ in range(5):
        assert client.post("/registro", data=_form_registro()).status_code == 201
    r = client.post("/registro", data=_form_registro())
    assert r.status_code == 429


# ── /contacto ──────────────────────────────────────────────────


def test_contacto_publico(client):
    r = client.get("/contacto")
    assert r.status_code == 200
    assert r.json()["telefono"] == "3000000000"


# ── /me ────────────────────────────────────────────────────────


def test_me_sin_token(client):
    assert client.get("/me").status_code == 401


def test_me_cliente_con_plan(client, cliente, db_session):
    plan = db_session.query(models.Plan).filter_by(nombre="1 Mes").first()
    db_session.add(models.Pago(usuario_id=cliente.user.id, plan_id=plan.id, monto=100000, metodo_pago="efectivo"))
    db_session.commit()

    r = client.get("/me", headers=cliente.headers)
    assert r.status_code == 200
    body = r.json()
    assert body["rol"] == "cliente"
    assert body["telefono"] == "3001234567"
    assert body["documento_identidad"]
    assert body["fecha_vencimiento"] == (date.today() + timedelta(days=30)).isoformat()
    assert body["plan_actual"]["nombre"] == "1 Mes"


def test_me_token_malformado(client):
    assert client.get("/me", headers=auth_headers("no-es-un-jwt")).status_code == 401


def test_me_token_expirado(client):
    token = create_access_token({"sub": ADMIN_EMAIL}, expires_delta=timedelta(minutes=-5))
    assert client.get("/me", headers=auth_headers(token)).status_code == 401


def test_me_usuario_eliminado(client, crear_usuario, db_session):
    actor = crear_usuario("cliente")
    db_session.query(models.Usuario).filter_by(id=actor.user.id).delete()
    db_session.commit()
    assert client.get("/me", headers=actor.headers).status_code == 401


# ── PATCH /me ──────────────────────────────────────────────────


def test_patch_me_datos_basicos(client, cliente):
    r = client.patch("/me", json={"nombre": "Nombre Nuevo", "telefono": "3115556677"}, headers=cliente.headers)
    assert r.status_code == 200
    body = r.json()
    assert body["nombre"] == "Nombre Nuevo"
    assert body["telefono"] == "3115556677"


def test_patch_me_email_duplicado(client, cliente, crear_usuario):
    otro = crear_usuario("cliente")
    r = client.patch("/me", json={"email": otro.user.email.upper()}, headers=cliente.headers)
    assert r.status_code == 400


def test_patch_me_cambio_password(client, crear_usuario):
    actor = crear_usuario("cliente")
    r = client.patch("/me", json={"password": "claveNueva123"}, headers=actor.headers)
    assert r.status_code == 200
    assert _login(client, actor.user.email, "claveNueva123").status_code == 200
    assert _login(client, actor.user.email, PASSWORD).status_code == 401


# ── POST /me/foto ──────────────────────────────────────────────


def test_me_foto_reemplaza_anterior(client, cliente):
    from storage import UPLOADS_DIR

    r1 = client.post("/me/foto", files={"foto": ("a.png", PNG_BYTES, "image/png")}, headers=cliente.headers)
    assert r1.status_code == 200
    url1 = r1.json()["foto_url"]
    archivo1 = UPLOADS_DIR / url1[len("/uploads/"):]
    assert archivo1.exists()

    r2 = client.post("/me/foto", files={"foto": ("b.png", PNG_BYTES, "image/png")}, headers=cliente.headers)
    assert r2.status_code == 200
    url2 = r2.json()["foto_url"]
    assert url2 != url1
    assert not archivo1.exists()  # la anterior se eliminó del disco


def test_me_foto_formato_invalido(client, cliente):
    r = client.post("/me/foto", files={"foto": ("x.txt", b"hola", "text/plain")}, headers=cliente.headers)
    assert r.status_code == 400
