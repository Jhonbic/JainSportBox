"""§7 de tests.md — Marcas RM: fórmulas 1RM, 4 tipos de ejercicio, aislamiento,
edición y sincronía backend/frontend."""

import math
import re
from datetime import date
from pathlib import Path

import pytest

from marcas_tipos import TIPOS_MARCA, TIPOS_MARCA_DEFAULT
from models import Ejercicio
from routers.marcas import _calcular_1rm, _tipo_de


def _payload(ejercicio, **kw):
    data = {"ejercicio": ejercicio, "fecha": date.today().isoformat(), "unidad": "kg"}
    data.update(kw)
    return data


# ── Unitario: _calcular_1rm ────────────────────────────────────


def test_1rm_una_rep_es_el_peso():
    assert _calcular_1rm(100, 1) == 100.0
    assert _calcular_1rm(72.5, 1) == 72.5


def test_1rm_promedio_de_7_formulas():
    w, r = 100.0, 5
    esperadas = [
        w * (36 / (37 - r)),
        w * (1 + r / 30),
        (100 * w) / (101.3 - 2.67123 * r),
        w * (1 + 0.025 * r),
        w * (r ** 0.1),
        (100 * w) / (52.2 + 41.9 * math.exp(-0.055 * r)),
        (100 * w) / (48.8 + 53.8 * math.exp(-0.075 * r)),
    ]
    assert _calcular_1rm(w, r) == pytest.approx(sum(esperadas) / 7, abs=0.1)


def test_1rm_reps_altas_no_revienta():
    # Brzycki divide por (37 - r): el clamp interno evita ÷0 y negativos
    assert _calcular_1rm(100, 37) > 0
    assert _calcular_1rm(100, 100) > 0


def test_tipo_de_desconocido_default_barra(db_session):
    # comportamiento actual: ejercicio no catalogado se trata como 'barra'
    assert _tipo_de("Ejercicio Inventado", db_session) == "barra"


def test_tipo_de_lee_el_catalogo(db_session):
    """El tipo sale de lo que configuró el staff, no de una lista fija."""
    db_session.add(Ejercicio(nombre="Sentadilla Búlgara", tipo_marca="reps"))
    db_session.commit()
    assert _tipo_de("Sentadilla Búlgara", db_session) == "reps"


def test_el_catalogo_le_gana_al_default(db_session):
    """Si el staff le cambia el tipo a un ejercicio histórico, manda el catálogo."""
    assert TIPOS_MARCA_DEFAULT["Back Squat"] == "barra"
    db_session.add(Ejercicio(nombre="Back Squat", tipo_marca="reps"))
    db_session.commit()
    assert _tipo_de("Back Squat", db_session) == "reps"


def test_ejercicio_sin_tipo_no_cuenta_como_catalogado(db_session):
    """Un ejercicio que es solo video para WODs cae al default, no rompe."""
    db_session.add(Ejercicio(nombre="Thruster", video_url="https://x", tipo_marca=None))
    db_session.commit()
    assert _tipo_de("Thruster", db_session) == "barra"


# ── Tipo barra ─────────────────────────────────────────────────


def test_barra_legacy_calcula_rm(client, cliente):
    r = client.post("/marcas/", json=_payload("Back Squat", peso=100, repeticiones=5), headers=cliente.headers)
    assert r.status_code == 201
    body = r.json()
    assert body["rm_calculado"] == pytest.approx(_calcular_1rm(100, 5), abs=0.1)
    assert body["unidad"] == "kg"


def test_barra_sin_peso_422(client, cliente):
    assert client.post("/marcas/", json=_payload("Deadlift", repeticiones=5), headers=cliente.headers).status_code == 422


def test_barra_reps_37_422(client, cliente):
    assert client.post("/marcas/", json=_payload("Deadlift", peso=100, repeticiones=37), headers=cliente.headers).status_code == 422


def test_barra_series_guarda_la_mejor(client, cliente):
    series = [
        {"peso": 80, "repeticiones": 5},
        {"peso": 100, "repeticiones": 3},
        {"peso": 90, "repeticiones": 1},
    ]
    r = client.post("/marcas/", json=_payload("Bench Press", series=series), headers=cliente.headers)
    assert r.status_code == 201
    body = r.json()
    mejor_rm = max(_calcular_1rm(s["peso"], s["repeticiones"]) for s in series)
    assert body["rm_calculado"] == pytest.approx(mejor_rm, abs=0.1)
    assert len(body["series"]) == 3
    assert all("rm_calculado" in s for s in body["series"])


def test_unidad_lbs(client, cliente):
    r = client.post("/marcas/", json=_payload("Snatch", unidad="lbs", peso=225, repeticiones=1), headers=cliente.headers)
    assert r.status_code == 201
    assert r.json()["unidad"] == "lbs"
    assert client.post("/marcas/", json=_payload("Snatch", unidad="libras", peso=1, repeticiones=1), headers=cliente.headers).status_code == 422


# ── Tipo corporal_lastre (Dominadas) ───────────────────────────


def test_dominadas_con_lastre(client, cliente):
    # peso = corporal (70) + lastre (10), snapshot enviado por el frontend
    r = client.post(
        "/marcas/",
        json=_payload("Dominadas", peso=80, peso_adicional=10, repeticiones=5),
        headers=cliente.headers,
    )
    assert r.status_code == 201
    body = r.json()
    assert body["peso_adicional"] == 10
    assert body["rm_calculado"] == pytest.approx(_calcular_1rm(80, 5), abs=0.1)


# ── Tipo reps ──────────────────────────────────────────────────


def test_reps_solo_repeticiones(client, cliente):
    r = client.post("/marcas/", json=_payload("Push Up", repeticiones=45), headers=cliente.headers)
    assert r.status_code == 201
    body = r.json()
    assert body["repeticiones"] == 45
    assert body["rm_calculado"] is None
    assert body["peso"] is None


def test_reps_sin_repeticiones_422(client, cliente):
    assert client.post("/marcas/", json=_payload("Air Squat"), headers=cliente.headers).status_code == 422


def test_reps_acepta_reps_altas(client, cliente):
    # AMRAP: hasta 1000 reps, sin el cap de 36 (que es solo para 1RM)
    assert client.post("/marcas/", json=_payload("Sit Up", repeticiones=500), headers=cliente.headers).status_code == 201


# ── Tipo leger ─────────────────────────────────────────────────


def test_leger(client, cliente):
    r = client.post("/marcas/", json=_payload("Test de Léger", nivel=9, palier=3), headers=cliente.headers)
    assert r.status_code == 201
    body = r.json()
    assert (body["nivel"], body["palier"]) == (9, 3)
    assert body["rm_calculado"] is None


def test_leger_sin_palier_422(client, cliente):
    assert client.post("/marcas/", json=_payload("Test de Léger", nivel=9), headers=cliente.headers).status_code == 422


# ── Listado y aislamiento entre usuarios ───────────────────────


def test_listar_por_ejercicio_url_encoded(client, cliente):
    client.post("/marcas/", json=_payload("Clean and Jerk", peso=60, repeticiones=3), headers=cliente.headers)
    r = client.get("/marcas/Clean%20and%20Jerk", headers=cliente.headers)
    assert r.status_code == 200
    assert len(r.json()) == 1


def test_aislamiento_entre_usuarios(client, cliente, crear_usuario):
    otro = crear_usuario("cliente")
    marca_id = client.post(
        "/marcas/", json=_payload("Back Squat", peso=100, repeticiones=1), headers=cliente.headers
    ).json()["id"]

    assert client.get("/marcas/", headers=otro.headers).json() == []
    assert client.get("/marcas/Back%20Squat", headers=otro.headers).json() == []
    # PATCH/DELETE ajenos → 404
    assert client.patch(f"/marcas/{marca_id}", json=_payload("Back Squat", peso=1, repeticiones=1), headers=otro.headers).status_code == 404
    assert client.delete(f"/marcas/{marca_id}", headers=otro.headers).status_code == 404
    # el dueño sí puede
    assert client.delete(f"/marcas/{marca_id}", headers=cliente.headers).status_code == 204


def test_patch_recalcula_rm(client, cliente):
    marca_id = client.post(
        "/marcas/", json=_payload("Press Militar", peso=50, repeticiones=5), headers=cliente.headers
    ).json()["id"]
    r = client.patch(
        f"/marcas/{marca_id}",
        json=_payload("Press Militar", peso=60, repeticiones=3),
        headers=cliente.headers,
    )
    assert r.status_code == 200
    assert r.json()["rm_calculado"] == pytest.approx(_calcular_1rm(60, 3), abs=0.1)


def test_marcas_sin_token_401(client):
    assert client.get("/marcas/").status_code == 401


# ── Sincronía backend ↔ frontend ───────────────────────────────


def test_tipos_marca_en_sync_con_frontend():
    """TIPOS_MARCA (marcas_tipos.py) debe coincidir con data/tiposMarca.js.

    La LISTA de ejercicios ya no se duplica —vive en la base—, pero los cuatro
    tipos sí: cada uno tiene su UI en el frontend y su validación en el backend.
    """
    js = (
        Path(__file__).resolve().parents[2]
        / "frontend" / "src" / "data" / "tiposMarca.js"
    ).read_text(encoding="utf-8")
    valores = re.findall(r"valor:\s*['\"]([^'\"]+)['\"]", js)
    assert valores, "no se pudo parsear tiposMarca.js"
    assert set(valores) == set(TIPOS_MARCA)


# ── Catálogo administrable (GET /marcas/catalogo) ──────────────


def test_catalogo_solo_trae_los_medibles(client, cliente, db_session):
    db_session.add_all([
        Ejercicio(nombre="Back Squat", video_url="https://v/bs", tipo_marca="barra"),
        Ejercicio(nombre="Thruster", video_url="https://v/th"),          # solo video
        Ejercicio(nombre="Push Up", tipo_marca="reps"),
    ])
    db_session.commit()

    r = client.get("/marcas/catalogo", headers=cliente.headers)
    assert r.status_code == 200
    nombres = [e["nombre"] for e in r.json()]
    assert nombres == ["Back Squat", "Push Up"]          # alfabético, sin Thruster
    assert r.json()[0]["tipo"] == "barra"
    # El video viaja: la página de la marca lo muestra como "Ver técnica".
    assert r.json()[0]["video_url"] == "https://v/bs"


def test_catalogo_no_lo_tapa_la_ruta_dinamica(client, cliente, db_session):
    """/marcas/catalogo va antes que /marcas/{ejercicio}, o la dinámica se lo come."""
    db_session.add(Ejercicio(nombre="Deadlift", tipo_marca="barra"))
    db_session.commit()
    r = client.get("/marcas/catalogo", headers=cliente.headers)
    assert r.status_code == 200
    assert isinstance(r.json(), list)
    assert r.json() and "tipo" in r.json()[0]            # no es una lista de marcas


def test_catalogo_sin_token_401(client):
    assert client.get("/marcas/catalogo").status_code == 401


def test_marca_sobre_ejercicio_creado_por_el_staff(client, admin_headers, cliente):
    """El flujo completo: el admin crea un ejercicio medible y el socio lo registra."""
    r = client.post(
        "/ejercicios/",
        json={"nombre": "Sentadilla Búlgara", "tipo_marca": "reps"},
        headers=admin_headers,
    )
    assert r.status_code == 201

    assert "Sentadilla Búlgara" in [
        e["nombre"] for e in client.get("/marcas/catalogo", headers=cliente.headers).json()
    ]

    # Se valida como 'reps': el peso se ignora y no hay 1RM.
    r = client.post(
        "/marcas/",
        json=_payload("Sentadilla Búlgara", peso=100, repeticiones=20),
        headers=cliente.headers,
    )
    assert r.status_code == 201
    assert r.json()["repeticiones"] == 20
    assert r.json()["rm_calculado"] is None
    assert r.json()["peso"] is None


def test_quitarle_el_tipo_no_borra_las_marcas(client, admin_headers, cliente):
    """Sacar un ejercicio de Mis Marcas lo esconde, no destruye el historial."""
    ej_id = client.post(
        "/ejercicios/", json={"nombre": "Remo Pendlay", "tipo_marca": "barra"},
        headers=admin_headers,
    ).json()["id"]
    client.post(
        "/marcas/", json=_payload("Remo Pendlay", peso=80, repeticiones=5),
        headers=cliente.headers,
    )

    r = client.put(f"/ejercicios/{ej_id}", json={"tipo_marca": ""}, headers=admin_headers)
    assert r.status_code == 200
    assert r.json()["tipo_marca"] is None

    assert client.get("/marcas/catalogo", headers=cliente.headers).json() == []
    # La marca sigue ahí y se puede consultar.
    assert len(client.get("/marcas/Remo Pendlay", headers=cliente.headers).json()) == 1


def test_tipo_marca_invalido_422(client, admin_headers):
    r = client.post(
        "/ejercicios/", json={"nombre": "Algo", "tipo_marca": "peso_corporal"},
        headers=admin_headers,
    )
    assert r.status_code == 422


def test_coach_puede_marcar_medible(client, coach):
    r = client.post(
        "/ejercicios/", json={"nombre": "Wall Walk", "tipo_marca": "reps"},
        headers=coach.headers,
    )
    assert r.status_code == 201
    assert r.json()["tipo_marca"] == "reps"


def test_cliente_no_puede_tocar_el_catalogo(client, cliente):
    r = client.post(
        "/ejercicios/", json={"nombre": "Lo Que Sea", "tipo_marca": "reps"},
        headers=cliente.headers,
    )
    assert r.status_code == 403
