"""Helpers de fecha en la zona horaria del gym (Bogotá).

El servidor de producción (Railway) corre en UTC: a partir de las 7:00 PM de
Bogotá, `date.today()` ya devuelve el día SIGUIENTE. Toda lógica de negocio
que dependa del "día de hoy" (vencimientos, validación de membresía, alertas,
rangos de historial) debe usar `hoy_bogota()` en lugar de `date.today()`.
"""

from datetime import date, datetime, time
from typing import Annotated, Optional
from zoneinfo import ZoneInfo

from pydantic import AfterValidator

TZ_BOGOTA = ZoneInfo("America/Bogota")
UTC = ZoneInfo("UTC")


def hoy_bogota() -> date:
    return datetime.now(TZ_BOGOTA).date()


def _no_esta_en_el_pasado(v: Optional[date]) -> Optional[date]:
    if v is not None and v < hoy_bogota():
        raise ValueError("La fecha de inicio no puede ser anterior a hoy.")
    return v


# Fecha de arranque de una membresía. Los tres endpoints que la aceptan
# (`/pagos/`, `/pagos/directo/` y la activación de un pendiente) comparten el tipo
# para que la regla viva en un solo lugar; escrita en cada schema, alcanzaría con
# olvidarse de uno para poder registrar una membresía retroactiva por ese camino.
FechaInicio = Annotated[Optional[date], AfterValidator(_no_esta_en_el_pasado)]


# ── Ventanas de tiempo ────────────────────────────────────────
# Las columnas de fecha_hora (`Asistencia.fecha_hora`, `Pago.fecha_pago`, …) se guardan
# como datetime NAIVE en UTC. Para filtrar "los registros del día X del negocio" no
# alcanza con `datetime(X, 00:00)`: eso es medianoche UTC, que en Bogotá son las 19:00
# del día ANTERIOR. Una ventana así se come la tarde-noche del día previo y pierde la
# del último día — justo el horario de más gente en el box.
#
# Estos helpers viven acá y no en un router porque los necesitan varios: tenerlos
# duplicados fue exactamente la causa de que `/asistencia/sesiones-por-bloque` filtrara
# en UTC mientras `/dashboard` filtraba bien.


def a_utc(dt_local: datetime) -> datetime:
    """Datetime de Bogotá → datetime naive en UTC, que es como está guardado."""
    return dt_local.replace(tzinfo=TZ_BOGOTA).astimezone(UTC).replace(tzinfo=None)


def inicio_dia_utc(dia: date) -> datetime:
    """00:00 de Bogotá de ese día, expresado en UTC naive."""
    return a_utc(datetime.combine(dia, time.min))


def fin_dia_utc(dia: date) -> datetime:
    """23:59:59.999999 de Bogotá de ese día, expresado en UTC naive."""
    return a_utc(datetime.combine(dia, time.max))


def a_bogota(dt_utc: datetime) -> datetime:
    """Datetime naive en UTC (como viene de la BD) → datetime en hora de Bogotá."""
    return dt_utc.replace(tzinfo=UTC).astimezone(TZ_BOGOTA)
