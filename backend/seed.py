import os
from dotenv import load_dotenv

load_dotenv()

from database import SessionLocal
from models import Ejercicio, Plan, Usuario, RolUsuario
from security import get_password_hash

import json as _json

PLANES_DEFAULT = [
    {
        "nombre": "1 Semana", "precio": 35000, "duracion_dias": 7,
        "descripcion": "Acceso por 7 días",
        "beneficios": _json.dumps(["Acceso al box 7 días", "Clases grupales incluidas", "Uso de equipamiento completo"]),
    },
    {
        "nombre": "15 Días", "precio": 60000, "duracion_dias": 15,
        "descripcion": "Acceso por quince días",
        "beneficios": _json.dumps(["Acceso al box 15 días", "Clases grupales incluidas", "Uso de equipamiento completo", "Seguimiento de progreso"]),
    },
    {
        "nombre": "1 Mes", "precio": 100000, "duracion_dias": 30,
        "descripcion": "Acceso por un mes",
        "beneficios": _json.dumps(["Acceso ilimitado al box", "Clases grupales incluidas", "Uso de equipamiento completo", "Seguimiento de progreso", "Asesoría nutricional básica"]),
    },
]

# Movimientos base de CrossFit para que el box pueda armar WODs desde el primer
# arranque. Formato: (nombre, video_url) — el catalogo tiene esos dos campos y nada
# mas. Los comentarios de seccion (Olimpico / Fuerza / ...) son solo para leer la
# lista comoda; ya no existe una columna `categoria` detras.
# Los nombres que se solapan con Mis Marcas van identicos a ejerciciosMarcas.js.
#
# Los videos son demos del canal oficial de CrossFit. Se obtuvieron buscando en la
# web y verificando cada URL una por una (que la página cargue y el título
# corresponda al movimiento). NO agregar URLs de YouTube "de memoria": los IDs son
# el caso típico de dato que se inventa con seguridad y termina en link muerto o
# apuntando a otro ejercicio.
EJERCICIOS_DEFAULT = [
    # ── Olímpico ────────────────────────────────────────────────
    ("Snatch",              "https://www.youtube.com/watch?v=9xQp2sldyts"),
    ("Clean",               "https://www.youtube.com/watch?v=EKRiW9Yt3Ps"),
    ("Clean and Jerk",      "https://www.youtube.com/watch?v=PjY1rH4_MOA"),
    ("Power Clean",         "https://www.youtube.com/watch?v=qtOfbyDLAeM"),
    # ── Fuerza ──────────────────────────────────────────────────
    ("Back Squat",          "https://www.youtube.com/watch?v=ultWZbUMPL8"),
    ("Front Squat",         "https://www.youtube.com/watch?v=m4ytaCJZpl0"),
    ("Overhead Squat",      "https://www.youtube.com/watch?v=RD_vUnqwqqI"),
    ("Deadlift",            "https://www.youtube.com/watch?v=op9kVnSso6Q"),
    ("Bench Press",         "https://www.youtube.com/watch?v=XSza8hVTlmM"),
    ("Press Militar",       "https://www.youtube.com/watch?v=xe19t2_6yis"),
    ("Push Press",          "https://www.youtube.com/watch?v=X6-DMh-t4nQ"),
    ("Thruster",            "https://www.youtube.com/watch?v=aea5BGj9a8Y"),
    ("Kettlebell Swing",    "https://www.youtube.com/watch?v=vdezTMulJ-k"),
    ("Wall Ball",           "https://www.youtube.com/watch?v=EqjGKsiIMCE"),
    # ── Gimnasia ────────────────────────────────────────────────
    ("Dominadas",           "https://www.youtube.com/watch?v=aAggnpPyR6E"),
    ("Toes to Bar",         "https://www.youtube.com/watch?v=_03pCKOv4l4"),
    ("Muscle Up",           "https://www.youtube.com/watch?v=o69WaY_7k2c"),
    ("Handstand Push Up",   "https://www.youtube.com/watch?v=0wDEO6shVjc"),
    ("Burpee",              "https://www.youtube.com/watch?v=TU8QYVW0gDU"),
    ("Push Up",             "https://www.youtube.com/watch?v=_l3ySVKYVJ8"),
    ("Air Squat",           "https://www.youtube.com/watch?v=C_VtOYc6j5c"),
    ("Sit Up",              "https://www.youtube.com/watch?v=P8Bv5QY_auo"),
    ("Box Jump",            "https://www.youtube.com/watch?v=52r_Ul5k03g"),
    # ── Cardio ──────────────────────────────────────────────────
    ("Remo",                "https://www.youtube.com/watch?v=S7HEm-fd534"),
    ("Carrera",             "https://www.youtube.com/watch?v=y1wnFWIisq8"),
    ("Assault Bike",        "https://www.youtube.com/watch?v=kpoQl-POgKQ"),
    ("Double Under",        "https://www.youtube.com/watch?v=-tF3hUsPZAI"),
]


def _admin_config() -> dict:
    # El email se normaliza igual que en el resto de la app (login, registro,
    # PATCH usuarios): sin normalizar, un ADMIN_EMAIL con mayusculas crea un
    # admin que NUNCA puede loguearse, porque login busca por email en
    # minusculas. Y al arrancar en limpio no hay otra cuenta para corregirlo.
    return {
        "nombre":              os.environ["ADMIN_NOMBRE"].strip(),
        "email":               os.environ["ADMIN_EMAIL"].strip().lower(),
        "password":            os.environ["ADMIN_PASSWORD"],
        "rol":                 RolUsuario.ADMIN,
        "telefono":            os.environ["ADMIN_TELEFONO"].strip(),
        "documento_identidad": os.environ["ADMIN_DOCUMENTO"].strip(),
    }

def seed_planes():
    db = SessionLocal()
    try:
        for datos in PLANES_DEFAULT:
            plan = db.query(Plan).filter(Plan.nombre == datos["nombre"]).first()
            if not plan:
                db.add(Plan(**datos))
                print(f"  + Plan '{datos['nombre']}' creado")
            elif not plan.beneficios:
                plan.beneficios = datos["beneficios"]
                print(f"  · Plan '{datos['nombre']}' actualizado con beneficios")
            else:
                print(f"  · Plan '{datos['nombre']}' ya existe")
        db.commit()
    finally:
        db.close()


def seed_ejercicios():
    """Siembra el catálogo base, solo si la tabla está vacía.

    A diferencia de seed_planes, no reconcilia ejercicio por ejercicio: si el
    coach borra uno sembrado, no debe reaparecer en el próximo arranque.
    """
    db = SessionLocal()
    try:
        if db.query(Ejercicio).count() > 0:
            print("  · Catálogo de ejercicios ya poblado, se omite")
            return
        db.add_all(
            Ejercicio(nombre=nombre, video_url=video_url)
            for nombre, video_url in EJERCICIOS_DEFAULT
        )
        db.commit()
        print(f"  + {len(EJERCICIOS_DEFAULT)} ejercicios sembrados")
    finally:
        db.close()


def seed_admin():
    cfg = _admin_config()
    db = SessionLocal()
    try:
        admin = db.query(Usuario).filter(Usuario.email == cfg["email"]).first()
        if not admin:
            admin = Usuario(
                nombre=cfg["nombre"],
                email=cfg["email"],
                password_hash=get_password_hash(cfg["password"]),
                documento_identidad=cfg["documento_identidad"],
                rol=cfg["rol"],
                telefono=cfg["telefono"],
            )
            db.add(admin)
            db.commit()
            print(f"  + Usuario admin '{cfg['email']}' creado")
        else:
            if not admin.documento_identidad:
                admin.documento_identidad = cfg["documento_identidad"]
                db.commit()
                print("  · Admin actualizado con documento de identidad")
            else:
                print(f"  · Usuario admin '{cfg['email']}' ya existe")
    finally:
        db.close()


if __name__ == "__main__":
    print("Sembrando planes por defecto...")
    seed_planes()
    print("Sembrando usuario admin...")
    seed_admin()
    print("Sembrando catalogo de ejercicios...")
    seed_ejercicios()
    print("Listo.")
