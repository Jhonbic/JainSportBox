"""Reglas de vigencia de la membresía: fecha de vencimiento e ingresos restantes.

Vive aparte porque **cuatro caminos distintos aplican un plan** —`POST /pagos/`,
`POST /pagos/directo/`, `POST /usuarios/{id}/activar` y la anulación que revierte—
y si la regla de los ingresos se escribiera en cada uno, alcanzaría con olvidarse
de uno para que un socio quedara con ingresos que nadie descuenta.

Hay **dos ejes de vigencia** y se validan juntos (ver `_validar_membresia` en
`routers/asistencia.py`):

* `Usuario.fecha_vencimiento` — hasta cuándo vale la membresía. Aplica siempre.
* `Usuario.ingresos_restantes` — cuántas entradas le quedan. `None` significa
  "no aplica" (plan por tiempo); un entero, que la membresía es por ingresos.

Un plan por ingresos (`Plan.numero_ingresos`) caduca por las dos cosas: se acaban
las entradas **o** se pasa la fecha, lo que ocurra primero.

Hay además una compuerta al principio: `Usuario.membresia_inicio`. Solo se llena
cuando el admin vende una membresía que arranca en el futuro, y hasta ese día el
acceso se niega. Sin ella la fecha de inicio sería decorativa —`fecha_vencimiento`
es un único campo, así que una membresía que "arranca el 1-sep" ya dejaría entrar
hoy mismo.
"""

from datetime import date, timedelta
from typing import Optional

from models import Plan, Usuario


def extender_vencimiento(
    usuario: Usuario, dias: int, hoy: date, inicio: Optional[date] = None
) -> date:
    """Suma `dias` al vencimiento vigente, o desde hoy si ya venció.

    Renovar antes de tiempo no le quita los días que le quedaban: la base es la
    fecha de vencimiento actual mientras siga vigente.

    `inicio` es la fecha de arranque elegida a mano, y entra como un **piso**: si
    cae antes de lo que ya correspondía, se ignora. Así elegir "hoy" sobre una
    membresía vigente encola la nueva detrás de la actual en vez de pisar los días
    que quedaban, que es el mismo criterio con el que la fecha se extiende. Con
    `inicio=None` el cálculo es idéntico al de siempre.
    """
    base = (
        usuario.fecha_vencimiento
        if (usuario.fecha_vencimiento and usuario.fecha_vencimiento >= hoy)
        else hoy
    )
    if inicio and inicio > base:
        base = inicio

    usuario.fecha_vencimiento = base + timedelta(days=dias)

    # Solo se marca el arranque cuando es futuro: si no, `_validar_membresia`
    # tendría que comparar contra una fecha ya pasada en cada marcación de huella.
    if inicio and inicio > hoy:
        usuario.membresia_inicio = inicio
    else:
        usuario.membresia_inicio = None

    return usuario.fecha_vencimiento


def _aplicar_ingresos(usuario: Usuario, ingresos: Optional[int]) -> None:
    """Regla única de ingresos: con un número se suman, sin él la membresía pasa
    a ser por tiempo.

    Los ingresos se SUMAN a los que le quedaban, por el mismo criterio con el que
    la fecha se extiende en vez de pisarse: quien renueva antes de gastar su bono
    no pierde lo que ya pagó.

    El reset a `None` no es cosmético: sin él, un socio que venía de un bono
    agotado (0 ingresos) seguiría bloqueado pese a acabar de pagar una membresía
    por tiempo.
    """
    if ingresos:
        usuario.ingresos_restantes = (usuario.ingresos_restantes or 0) + ingresos
    else:
        usuario.ingresos_restantes = None


def aplicar_plan(
    usuario: Usuario, plan: Plan, hoy: date, inicio: Optional[date] = None
) -> date:
    """Aplica un plan del catálogo: extiende la vigencia y ajusta los ingresos."""
    nueva_fecha = extender_vencimiento(usuario, plan.duracion_dias, hoy, inicio)
    _aplicar_ingresos(usuario, plan.numero_ingresos if plan.por_ingresos else None)
    return nueva_fecha


def aplicar_personalizado(
    usuario: Usuario,
    dias: int,
    ingresos: Optional[int],
    hoy: date,
    inicio: Optional[date] = None,
) -> date:
    """Aplica una membresía personalizada (sin plan detrás): días y accesos sueltos.

    Comparte la regla de ingresos con `aplicar_plan` a propósito. Antes el pago
    directo no tocaba `ingresos_restantes` en absoluto, y eso dejaba colgado al
    socio con un bono agotado: le vendías 30 días por tiempo y seguía rebotando
    con `sin_ingresos` porque su contador seguía en 0.
    """
    nueva_fecha = extender_vencimiento(usuario, dias, hoy, inicio)
    _aplicar_ingresos(usuario, ingresos)
    return nueva_fecha


def revertir_plan(usuario: Usuario, dias: int, ingresos: Optional[int]) -> None:
    """Deshace lo que aplicó un pago. Lo usa la anulación.

    La fecha puede quedar en el pasado — es correcto: la membresía venció por la
    reversión. Los ingresos no bajan de 0.

    Limitación conocida: si el pago anulado era de un plano por tiempo, `aplicar_plan`
    puso `ingresos_restantes = None` y los ingresos que hubiera antes no se
    guardaron en ningún lado, así que no se pueden restaurar. Anular ese pago deja
    la membresía como "por tiempo" vencida, que es el desenlace razonable.
    """
    if usuario.fecha_vencimiento and dias:
        usuario.fecha_vencimiento = usuario.fecha_vencimiento - timedelta(days=dias)
    if ingresos and usuario.ingresos_restantes is not None:
        usuario.ingresos_restantes = max(0, usuario.ingresos_restantes - ingresos)


def descontar_ingreso(usuario: Usuario) -> None:
    """Descuenta una entrada si la membresía es por ingresos. No baja de 0."""
    if usuario.ingresos_restantes is not None:
        usuario.ingresos_restantes = max(0, usuario.ingresos_restantes - 1)
