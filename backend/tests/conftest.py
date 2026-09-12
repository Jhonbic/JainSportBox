"""
Infraestructura de la suite de tests (ver tests.md en la raíz del repo).

El backend corre migraciones + seed al importar main.py, así que TODO el
entorno (DATABASE_URL a un SQLite temporal, SECRET_KEY, ADMIN_*, BRIDGE_SECRET,
TESTING=1) debe estar seteado ANTES de importar cualquier módulo de la app.
load_dotenv() no pisa variables ya presentes, por eso asignar aquí gana sobre
backend/.env.
"""

import os
import sys
import tempfile
import uuid
from datetime import timedelta
from pathlib import Path
from types import SimpleNamespace

import pytest

BACKEND_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_DIR))

_TMPDIR = Path(tempfile.mkdtemp(prefix="jsb_tests_"))

ADMIN_EMAIL = "admin@test.local"
ADMIN_PASSWORD = "AdminPass123!"
BRIDGE_SECRET = "test_bridge_secret"

os.environ["DATABASE_URL"] = f"sqlite:///{(_TMPDIR / 'test_crossfit.db').as_posix()}"
os.environ["TESTING"] = "1"
os.environ["SECRET_KEY"] = "clave_solo_para_tests_no_usar_en_prod"
os.environ["BRIDGE_SECRET"] = BRIDGE_SECRET
os.environ["ADMIN_NOMBRE"] = "Admin Test"
os.environ["ADMIN_EMAIL"] = ADMIN_EMAIL
os.environ["ADMIN_PASSWORD"] = ADMIN_PASSWORD
os.environ["ADMIN_TELEFONO"] = "3000000000"
os.environ["ADMIN_DOCUMENTO"] = "99999999"

# storage.py entra en modo S3 con la sola presencia de S3_BUCKET, y lee las seis
# variables al importarse. Si backend/.env las tiene (entorno cloud configurado),
# los tests de foto subirían archivos al bucket REAL. Se vacían para forzar el
# fallback a filesystem, que es lo que afirman los tests ("/uploads/...").
# Se asignan "" en vez de borrarlas: load_dotenv() no pisa lo ya presente, pero
# sí rellenaría una variable ausente con el valor del .env.
for _var in ("S3_BUCKET", "S3_PUBLIC_URL", "S3_ENDPOINT_URL",
             "S3_ACCESS_KEY_ID", "S3_SECRET_ACCESS_KEY", "S3_REGION"):
    os.environ[_var] = ""

# Mismo motivo con WhatsApp, y acá el daño sería peor que subir un archivo de
# más: con credenciales reales en backend/.env, un test de alertas le mandaría
# un WhatsApp de verdad a un socio. Vaciarlas deja whatsapp.HABILITADO en False,
# así el default de toda la suite es "no se puede enviar"; los tests que sí
# ejercitan el envío lo habilitan explícitamente con monkeypatch.
for _var in ("WA_PHONE_NUMBER_ID", "WA_ACCESS_TOKEN"):
    os.environ[_var] = ""

import database  # noqa: E402

database.engine.echo = False  # el engine SQLite de dev viene con echo=True

# Importar main ejecuta create_all + migraciones SQLite + seed contra la BD temporal.
from main import app  # noqa: E402
import models  # noqa: E402
import ratelimit  # noqa: E402
from database import SessionLocal  # noqa: E402
from security import create_access_token, get_password_hash  # noqa: E402

from fastapi.testclient import TestClient  # noqa: E402

# bcrypt es lento (~0.2 s por hash): un solo hash compartido por todos los
# usuarios de prueba. El flujo real de hashing se cubre en test_auth.
PASSWORD = "password-de-prueba-123"
PASSWORD_HASH = get_password_hash(PASSWORD)

SEED_PLAN_NOMBRES = ("1 Semana", "15 Días", "1 Mes")

# PNG real para los endpoints de foto. Tiene que ser decodificable, no solo tener
# los magic bytes: storage.py re-encodea toda imagen a WebP redimensionado, así que
# un header falso seguido de ceros ahora se rechaza con 400 (que es lo correcto).
def _png_de_prueba() -> bytes:
    import io

    from PIL import Image

    buf = io.BytesIO()
    Image.new("RGB", (900, 600), (200, 30, 30)).save(buf, "PNG")
    return buf.getvalue()


PNG_BYTES = _png_de_prueba()


def auth_headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def token_para(email: str) -> str:
    return create_access_token({"sub": email}, expires_delta=timedelta(hours=1))


@pytest.fixture(scope="session")
def client():
    return TestClient(app)


@pytest.fixture(autouse=True)
def _bd_limpia():
    """Deja la BD como recién sembrada después de cada test (conserva el admin
    del seed y los 3 planes default) y resetea el rate limiter en memoria."""
    yield
    db = SessionLocal()
    try:
        for model in (
            models.AlertaMembresia,
            models.Asistencia,
            models.MarcaRM,
            models.MedidaSalud,
            models.MovimientoFinanciero,
            models.Venta,
            models.ResultadoWOD,
            models.WODEjercicio,
            models.WOD,
            models.Pago,
            models.MetodoPago,
            models.PlantillaMensaje,
            models.Aviso,
            models.Producto,
            models.Ejercicio,
        ):
            db.query(model).delete(synchronize_session=False)
        db.query(models.Usuario).filter(models.Usuario.email != ADMIN_EMAIL).delete(
            synchronize_session=False
        )
        db.query(models.Plan).filter(
            models.Plan.nombre.notin_(SEED_PLAN_NOMBRES)
        ).delete(synchronize_session=False)
        db.query(models.Plan).update({"activo": True}, synchronize_session=False)
        # El admin sobrevive al borrado, así que su puntero de aviso descartado se
        # filtraría al test siguiente.
        db.query(models.Usuario).update({"aviso_visto_id": None}, synchronize_session=False)
        db.commit()
    finally:
        db.close()
    ratelimit._hits.clear()


@pytest.fixture
def db_session():
    db = SessionLocal()
    yield db
    db.close()


@pytest.fixture
def crear_usuario():
    """Factory: inserta un usuario directo en la BD (sin bcrypt por usuario) y
    devuelve SimpleNamespace(user, token, headers)."""

    def _crear(rol="cliente", fecha_vencimiento=None, genero="masculino", **kw):
        sufijo = uuid.uuid4().hex[:10]
        db = SessionLocal()
        try:
            u = models.Usuario(
                nombre=kw.pop("nombre", f"Usuario {sufijo}"),
                email=kw.pop("email", f"u{sufijo}@test.local"),
                password_hash=PASSWORD_HASH,
                documento_identidad=kw.pop("documento_identidad", sufijo),
                rol=models.RolUsuario(rol),
                genero=genero,
                telefono=kw.pop("telefono", "3001234567"),
                fecha_vencimiento=fecha_vencimiento,
                **kw,
            )
            db.add(u)
            db.commit()
            db.refresh(u)
            token = token_para(u.email)
            return SimpleNamespace(user=u, token=token, headers=auth_headers(token))
        finally:
            db.close()

    return _crear


@pytest.fixture
def admin_headers():
    return auth_headers(token_para(ADMIN_EMAIL))


@pytest.fixture
def coach(crear_usuario):
    return crear_usuario("coach")


@pytest.fixture
def cliente(crear_usuario):
    from datetime import date, timedelta as td

    return crear_usuario("cliente", fecha_vencimiento=date.today() + td(days=30))


@pytest.fixture
def cliente_vencido(crear_usuario):
    from datetime import date, timedelta as td

    return crear_usuario("cliente", fecha_vencimiento=date.today() - td(days=5))


@pytest.fixture
def pendiente(crear_usuario):
    return crear_usuario("pendiente")


@pytest.fixture
def bridge_headers():
    return {"X-Bridge-Secret": BRIDGE_SECRET}
