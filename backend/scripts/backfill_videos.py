"""Rellena `ejercicios.video_url` en bases que ya estaban sembradas.

`seed_ejercicios()` no sirve para esto: se corta apenas la tabla tiene filas, así
que las instalaciones que ya existían (el SQLite local y el Postgres de Supabase)
se quedaron sin los videos que ahora trae EJERCICIOS_DEFAULT.

Tampoco va como bloque de arranque en main.py: eso correría en cada boot y le
devolvería el video a un ejercicio al que el coach se lo borró a propósito (el
formulario guarda el campo vacío como NULL). Esto se corre a mano, una vez.

Es idempotente: solo toca filas con video_url NULL o vacío, y matchea por nombre.

Uso (desde backend/):
    ..\\venv\\Scripts\\python.exe scripts\\backfill_videos.py

OJO: usa el DATABASE_URL del entorno. Confirmá contra qué base estás corriendo
antes de ejecutarlo — el .env local puede estar apuntando a producción.
"""
import os
import sys

# El script vive en backend/scripts/, pero los módulos (database, models) están en
# backend/: sin esto los imports fallan al correrlo directo.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import SessionLocal, engine  # noqa: E402
from models import Ejercicio  # noqa: E402
from seed import EJERCICIOS_DEFAULT  # noqa: E402


def backfill_videos() -> None:
    print(f"Base de datos: {engine.url.render_as_string(hide_password=True)}")

    db = SessionLocal()
    try:
        actualizados, ya_tenian, no_encontrados = 0, 0, []

        for nombre, video_url in EJERCICIOS_DEFAULT:
            if not video_url:
                continue
            ejercicio = db.query(Ejercicio).filter(Ejercicio.nombre == nombre).first()
            if not ejercicio:
                no_encontrados.append(nombre)
                continue
            if ejercicio.video_url:
                ya_tenian += 1
                continue
            ejercicio.video_url = video_url
            actualizados += 1
            print(f"  + {nombre}")

        db.commit()

        print(f"\n{actualizados} actualizados, {ya_tenian} ya tenían video.")
        if no_encontrados:
            print(f"{len(no_encontrados)} no están en esta base: {', '.join(no_encontrados)}")
    finally:
        db.close()


if __name__ == "__main__":
    backfill_videos()
