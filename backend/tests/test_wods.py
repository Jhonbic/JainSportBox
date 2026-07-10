"""§6 de tests.md — WODs (roles, superseries, activo/historial, personalizados)
y catálogo de ejercicios."""

from datetime import date, timedelta

import models


def _crear_ejercicios(db_session, n=3, categoria=None):
    ejercicios = []
    for i in range(n):
        e = models.Ejercicio(nombre=f"Ejercicio Test {i} {id(db_session)}", categoria=categoria)
        db_session.add(e)
        ejercicios.append(e)
    db_session.commit()
    return [e.id for e in ejercicios]


def _payload_wod(ejercicio_ids=None, **overrides):
    data = {
        "titulo": "WOD de prueba",
        "descripcion": "5 rondas",
        "fecha": date.today().isoformat(),
        "tipo": "For Time",
    }
    if ejercicio_ids:
        data["ejercicios"] = [
            {"ejercicio_id": eid, "orden": i} for i, eid in enumerate(ejercicio_ids)
        ]
    data.update(overrides)
    return data


# ── Crear / roles ──────────────────────────────────────────────


def test_crear_wod_admin_y_coach(client, admin_headers, coach):
    assert client.post("/wods/", json=_payload_wod(), headers=admin_headers).status_code == 201
    assert client.post("/wods/", json=_payload_wod(), headers=coach.headers).status_code == 201


def test_crear_wod_cliente_403(client, cliente):
    assert client.post("/wods/", json=_payload_wod(), headers=cliente.headers).status_code == 403


def test_crear_wod_tipo_invalido_422(client, admin_headers):
    assert client.post("/wods/", json=_payload_wod(tipo="Tabata"), headers=admin_headers).status_code == 422


def test_crear_wod_ejercicio_inexistente_422(client, admin_headers):
    r = client.post(
        "/wods/",
        json=_payload_wod(ejercicios=[{"ejercicio_id": 999999, "orden": 0}]),
        headers=admin_headers,
    )
    assert r.status_code == 422


# ── Superseries ────────────────────────────────────────────────


def test_superserie_primera_fila_normalizada(client, admin_headers, db_session):
    ids = _crear_ejercicios(db_session, 3)
    payload = _payload_wod()
    payload["ejercicios"] = [
        {"ejercicio_id": ids[0], "orden": 0, "superserie_con_anterior": True},  # inválido: primera fila
        {"ejercicio_id": ids[1], "orden": 1, "superserie_con_anterior": True},
        {"ejercicio_id": ids[2], "orden": 2, "superserie_con_anterior": False},
    ]
    r = client.post("/wods/", json=payload, headers=admin_headers)
    assert r.status_code == 201
    flags = [e["superserie_con_anterior"] for e in r.json()["ejercicios"]]
    assert flags == [False, True, False]  # la primera siempre False


def test_superserie_sobrevive_reordenado(client, admin_headers, db_session):
    ids = _crear_ejercicios(db_session, 3)
    payload = _payload_wod()
    payload["ejercicios"] = [
        {"ejercicio_id": ids[0], "orden": 0},
        {"ejercicio_id": ids[1], "orden": 1, "superserie_con_anterior": True},
        {"ejercicio_id": ids[2], "orden": 2},
    ]
    wod_id = client.post("/wods/", json=payload, headers=admin_headers).json()["id"]

    # reordenar: el que era superserie pasa a primera fila
    r = client.put(
        f"/wods/{wod_id}",
        json={"ejercicios": [
            {"ejercicio_id": ids[1], "orden": 0, "superserie_con_anterior": True},
            {"ejercicio_id": ids[0], "orden": 1},
            {"ejercicio_id": ids[2], "orden": 2, "superserie_con_anterior": True},
        ]},
        headers=admin_headers,
    )
    assert r.status_code == 200
    flags = [e["superserie_con_anterior"] for e in r.json()["ejercicios"]]
    assert flags == [False, False, True]


# ── Listado, activo/historial, paginación ──────────────────────


def test_cliente_solo_ve_activos(client, admin_headers, cliente):
    activo_id = client.post("/wods/", json=_payload_wod(), headers=admin_headers).json()["id"]
    inactivo_id = client.post("/wods/", json=_payload_wod(activo=False), headers=admin_headers).json()["id"]

    ids_cliente = [w["id"] for w in client.get("/wods/", headers=cliente.headers).json()]
    assert activo_id in ids_cliente and inactivo_id not in ids_cliente

    ids_staff = [w["id"] for w in client.get("/wods/", headers=admin_headers).json()]
    assert activo_id in ids_staff and inactivo_id in ids_staff


def test_filtro_activo_y_paginacion(client, admin_headers):
    creados = [
        client.post("/wods/", json=_payload_wod(activo=False, titulo=f"Hist {i}"), headers=admin_headers).json()["id"]
        for i in range(5)
    ]
    r = client.get("/wods/?activo=false&limit=2", headers=admin_headers)
    pagina1 = [w["id"] for w in r.json()]
    assert len(pagina1) == 2
    r2 = client.get("/wods/?activo=false&limit=2&skip=2", headers=admin_headers)
    pagina2 = [w["id"] for w in r2.json()]
    assert len(pagina2) == 2
    assert not set(pagina1) & set(pagina2)
    assert set(pagina1 + pagina2) <= set(creados)


def test_toggle(client, admin_headers):
    wod_id = client.post("/wods/", json=_payload_wod(), headers=admin_headers).json()["id"]
    assert client.patch(f"/wods/{wod_id}/toggle", headers=admin_headers).json()["activo"] is False
    assert client.patch(f"/wods/{wod_id}/toggle", headers=admin_headers).json()["activo"] is True


def test_wods_hoy(client, admin_headers, cliente):
    hoy_id = client.post("/wods/", json=_payload_wod(), headers=admin_headers).json()["id"]
    ayer = (date.today() - timedelta(days=1)).isoformat()
    ayer_id = client.post("/wods/", json=_payload_wod(fecha=ayer), headers=admin_headers).json()["id"]
    ids = [w["id"] for w in client.get("/wods/hoy", headers=cliente.headers).json()]
    assert hoy_id in ids and ayer_id not in ids


def test_eliminar_wod(client, admin_headers, db_session):
    ids = _crear_ejercicios(db_session, 1)
    wod_id = client.post("/wods/", json=_payload_wod(ejercicio_ids=ids), headers=admin_headers).json()["id"]
    assert client.delete(f"/wods/{wod_id}", headers=admin_headers).status_code == 204
    assert db_session.query(models.WODEjercicio).filter_by(wod_id=wod_id).count() == 0


# ── Personalizados ─────────────────────────────────────────────


def _plan_personalizado(db_session):
    plan = models.Plan(nombre="Premium Perso", precio=1, duracion_dias=30, incluye_wods_personalizados=True)
    db_session.add(plan)
    db_session.commit()
    return plan


def _dar_plan(db_session, usuario_id, plan_id):
    db_session.add(models.Pago(usuario_id=usuario_id, plan_id=plan_id, monto=1, metodo_pago="efectivo"))
    db_session.commit()


def test_personalizado_requiere_genero_destino(client, admin_headers):
    r = client.post("/wods/", json=_payload_wod(es_personalizado=True), headers=admin_headers)
    assert r.status_code == 422


def test_personalizados_filtra_por_genero_y_activo(client, admin_headers, crear_usuario, db_session):
    masc_id = client.post("/wods/", json=_payload_wod(es_personalizado=True, genero_destino="masculino"), headers=admin_headers).json()["id"]
    fem_id = client.post("/wods/", json=_payload_wod(es_personalizado=True, genero_destino="femenino"), headers=admin_headers).json()["id"]
    masc_inactivo_id = client.post(
        "/wods/", json=_payload_wod(es_personalizado=True, genero_destino="masculino", activo=False), headers=admin_headers
    ).json()["id"]

    plan = _plan_personalizado(db_session)
    actor = crear_usuario("cliente", genero="masculino", fecha_vencimiento=date.today() + timedelta(days=30))
    _dar_plan(db_session, actor.user.id, plan.id)

    r = client.get("/wods/personalizados", headers=actor.headers)
    assert r.status_code == 200
    ids = [w["id"] for w in r.json()]
    assert masc_id in ids
    assert fem_id not in ids
    assert masc_inactivo_id not in ids

    # staff ve todos, incluidos inactivos
    ids_staff = [w["id"] for w in client.get("/wods/personalizados", headers=admin_headers).json()]
    assert {masc_id, fem_id, masc_inactivo_id} <= set(ids_staff)


def test_personalizados_sin_plan_403(client, cliente):
    assert client.get("/wods/personalizados", headers=cliente.headers).status_code == 403


def test_personalizados_no_salen_en_listado_regular(client, admin_headers):
    perso_id = client.post(
        "/wods/", json=_payload_wod(es_personalizado=True, genero_destino="masculino"), headers=admin_headers
    ).json()["id"]
    ids = [w["id"] for w in client.get("/wods/", headers=admin_headers).json()]
    assert perso_id not in ids


# ── Catálogo de ejercicios ─────────────────────────────────────


def test_ejercicios_crud(client, admin_headers, cliente):
    r = client.post(
        "/ejercicios/",
        json={"nombre": "Burpee Test", "categoria": "Cardio"},
        headers=admin_headers,
    )
    assert r.status_code == 201
    eid = r.json()["id"]

    # duplicado (case-insensitive) → 409
    assert client.post("/ejercicios/", json={"nombre": "burpee test"}, headers=admin_headers).status_code == 409

    # filtro por categoría
    ids = [e["id"] for e in client.get("/ejercicios/?categoria=Cardio", headers=cliente.headers).json()]
    assert eid in ids
    ids_fuerza = [e["id"] for e in client.get("/ejercicios/?categoria=Fuerza", headers=cliente.headers).json()]
    assert eid not in ids_fuerza

    # update
    r = client.put(f"/ejercicios/{eid}", json={"categoria": "Gimnasia"}, headers=admin_headers)
    assert r.json()["categoria"] == "Gimnasia"

    # cliente no puede crear/editar
    assert client.post("/ejercicios/", json={"nombre": "Otro"}, headers=cliente.headers).status_code == 403


def test_eliminar_ejercicio_usado_en_wod_409(client, admin_headers, db_session):
    ids = _crear_ejercicios(db_session, 1)
    client.post("/wods/", json=_payload_wod(ejercicio_ids=ids), headers=admin_headers)
    assert client.delete(f"/ejercicios/{ids[0]}", headers=admin_headers).status_code == 409


def test_eliminar_ejercicio_libre_204(client, admin_headers, db_session):
    ids = _crear_ejercicios(db_session, 1)
    assert client.delete(f"/ejercicios/{ids[0]}", headers=admin_headers).status_code == 204
