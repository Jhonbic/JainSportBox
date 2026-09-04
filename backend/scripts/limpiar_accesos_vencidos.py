"""Pone en 0 los accesos de las membresías que ya vencieron.

Los accesos pertenecen al plan que los vendió y mueren con él (ver
`_aplicar_ingresos` en `backend/membresia.py`). Esa regla se corrigió después de
que el sistema estuviera en producción: hasta entonces el saldo sobrevivía al
vencimiento y cada compra nueva lo sumaba encima, así que hay socios arrastrando
accesos de bonos que caducaron hace meses.

La regla nueva ya no los acumula, así que la base se corregiría sola en la próxima
renovación de cada socio. Esto lo adelanta para que el perfil deje de mostrar hoy
un saldo que ya no vale.

Se pone en **0** y no en NULL: NULL significa "membresía por tiempo" y convertiría
un bono agotado en una mensualidad. 0 es lo que deja `revertir_plan` y lo que hace
que `_validar_membresia` responda `sin_ingresos`.

Es idempotente: solo toca filas con saldo > 0 y fecha ya vencida.

Uso (desde backend/):
    ..\\venv\\Scripts\\python.exe scripts\\limpiar_accesos_vencidos.py --dry-run
    ..\\venv\\Scripts\\python.exe scripts\\limpiar_accesos_vencidos.py

OJO: usa el DATABASE_URL del entorno. Confirmá contra qué base estás corriendo
antes de ejecutarlo — el .env local puede estar apuntando a producción. Corré
primero con --dry-run y revisá la lista.
"""
import argparse
import os
import sys

# El script vive en backend/scripts/, pero los módulos (database, models) están en
# backend/: sin esto los imports fallan al correrlo directo.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import SessionLocal, engine  # noqa: E402
from fechas import hoy_bogota  # noqa: E402
from models import RolUsuario, Usuario  # noqa: E402


def limpiar_accesos_vencidos(dry_run: bool = False) -> None:
    print(f"Base de datos: {engine.url.render_as_string(hide_password=True)}")
    if dry_run:
        print("Modo --dry-run: no se escribe nada.\n")

    hoy = hoy_bogota()
    db = SessionLocal()
    try:
        vencidos = (
            db.query(Usuario)
            .filter(
                Usuario.rol == RolUsuario.CLIENTE,
                Usuario.ingresos_restantes > 0,
                Usuario.fecha_vencimiento.isnot(None),
                Usuario.fecha_vencimiento < hoy,
            )
            .order_by(Usuario.fecha_vencimiento)
            .all()
        )

        if not vencidos:
            print("Nada que limpiar: ningún cliente vencido tiene accesos sin gastar.")
            return

        # Se imprime todo ANTES de escribir: es plata que el socio pagó, y el admin
        # tiene que poder reclamarle a alguien si el número no cuadra.
        print(f"{len(vencidos)} cliente(s) con accesos de una membresía vencida:\n")
        total = 0
        for u in vencidos:
            dias = (hoy - u.fecha_vencimiento).days
            print(
                f"  {u.nombre} (id {u.id}) — {u.ingresos_restantes} acceso(s), "
                f"venció el {u.fecha_vencimiento.isoformat()} (hace {dias} días)"
            )
            total += u.ingresos_restantes

        if dry_run:
            print(f"\n{total} acceso(s) en total quedarían en 0. No se escribió nada.")
            return

        for u in vencidos:
            u.ingresos_restantes = 0
        db.commit()
        print(f"\nListo: {len(vencidos)} cliente(s), {total} acceso(s) puestos en 0.")
    finally:
        db.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Muestra a quién tocaría y sale sin escribir.",
    )
    limpiar_accesos_vencidos(dry_run=parser.parse_args().dry_run)
