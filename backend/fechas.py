"""Helpers de fecha en la zona horaria del gym (Bogotá).

El servidor de producción (Railway) corre en UTC: a partir de las 7:00 PM de
Bogotá, `date.today()` ya devuelve el día SIGUIENTE. Toda lógica de negocio
que dependa del "día de hoy" (vencimientos, validación de membresía, alertas,
rangos de historial) debe usar `hoy_bogota()` en lugar de `date.today()`.
"""

from datetime import date, datetime
from zoneinfo import ZoneInfo

TZ_BOGOTA = ZoneInfo("America/Bogota")


def hoy_bogota() -> date:
    return datetime.now(TZ_BOGOTA).date()
