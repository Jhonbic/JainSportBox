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

Los dos ejes se comportan distinto al comprar una membresía nueva, y es a
propósito: la fecha se **extiende** (renovar antes de tiempo no quita días
pagos), los ingresos se **reemplazan** (lo que sobró del bono anterior se pierde
con él). Ver `_aplicar_ingresos`.

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
    fecha de vencimiento actual mientras siga vigente. Con `inicio=None` el cálculo
    es exactamente ese.

    `inicio` es la fecha de arranque elegida a mano y **se ignora en un solo caso**:
    cuando cae entre hoy y el vencimiento vigente. Ahí no adelanta nada y respetarlo
    pisaría días ya pagos — es lo que hace que elegir "hoy" (el default del form)
    sobre una membresía vigente encole la nueva detrás de la actual. Fuera de esa
    franja el arranque manda, en las dos direcciones:

    * **Futuro** — la ventana corre desde ese día. `membresia_inicio` queda cargada
      para que `_validar_membresia` niegue el acceso hasta entonces.
    * **Pasado** — la membresía arrancó ese día, así que los días ya transcurridos
      cuentan y el vencimiento cae antes que si se contara desde hoy. Es el caso de
      quien entró unos días antes de que se le cobrara: contar desde hoy le regalaría
      esos días. No hace falta compuerta, el arranque ya pasó.

    Una carga retroactiva **no puede acortar una membresía vigente**: la fecha nunca
    retrocede. Un retroactivo sobre alguien que ya tenía días por delante es casi
    siempre un error de tipeo, y aceptarlo le borraría días pagos en silencio.
    """
    vigente = (
        usuario.fecha_vencimiento
        if (usuario.fecha_vencimiento and usuario.fecha_vencimiento >= hoy)
        else None
    )
    base = vigente or hoy
    if inicio is not None and not (hoy <= inicio <= base):
        base = inicio

    nueva = base + timedelta(days=dias)
    if vigente and nueva < vigente:
        nueva = vigente
    usuario.fecha_vencimiento = nueva

    # Solo se marca el arranque cuando es futuro: si no, `_validar_membresia`
    # tendría que comparar contra una fecha ya pasada en cada marcación de huella.
    if inicio and inicio > hoy:
        usuario.membresia_inicio = inicio
    else:
        usuario.membresia_inicio = None

    return usuario.fecha_vencimiento


def _aplicar_ingresos(usuario: Usuario, ingresos: Optional[int]) -> None:
    """Regla única de ingresos: cada membresía REEMPLAZA el saldo, nunca lo suma.

    Los ingresos pertenecen al plan que los vendió y mueren con él: lo que sobra
    se pierde, se haya vencido la fecha o se reemplace la membresía antes de
    tiempo. Es también lo que pasa con una membresía encolada (la que arranca
    después del vencimiento vigente): el plan que termina se lleva sus accesos sin
    gastar.

    Acá se sumaba, espejando a `extender_vencimiento`. Pero la fecha sí tiene
    corte —si ya venció, la base pasa a ser hoy y no arrastra nada— y los accesos
    no lo tenían: un bono de 10 con 4 sin usar y la fecha ya vencida dejaba 14 al
    comprar otro bono de 10, y así compra tras compra.

    No se distingue "renovó vigente" de "renovó vencido" a propósito: una sola
    regla, sin estado extra que rastrear, y la misma que aplica al encolado.

    El `or None` no es cosmético: `None` significa "membresía por tiempo", y sin
    ese reset un socio que venía de un bono agotado (0 ingresos) seguiría
    bloqueado pese a acabar de pagar una mensualidad.
    """
    usuario.ingresos_restantes = ingresos or None


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

    Con el reemplazo de `_aplicar_ingresos`, el saldo nunca supera lo que cargó el
    último pago, así que restar y poner en 0 dan lo mismo para el caso normal. Se
    resta igual porque para el caso raro —anular un pago viejo, con otro más nuevo
    encima— degrada mejor que borrar el saldo entero.

    Limitación conocida: el saldo que había ANTES del pago anulado no se guardó en
    ningún lado (lo pisó el reemplazo), así que no se puede restaurar. Anular deja
    la membresía en 0 accesos, o como "por tiempo" vencida si el pago no traía
    ingresos — el desenlace razonable en los dos casos.
    """
    if usuario.fecha_vencimiento and dias:
        usuario.fecha_vencimiento = usuario.fecha_vencimiento - timedelta(days=dias)
    if ingresos and usuario.ingresos_restantes is not None:
        usuario.ingresos_restantes = max(0, usuario.ingresos_restantes - ingresos)


def descontar_ingreso(usuario: Usuario) -> None:
    """Descuenta una entrada si la membresía es por ingresos. No baja de 0."""
    if usuario.ingresos_restantes is not None:
        usuario.ingresos_restantes = max(0, usuario.ingresos_restantes - 1)
