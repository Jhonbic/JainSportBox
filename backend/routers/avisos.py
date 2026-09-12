"""
Avisos en la app: el cartel que el box le muestra a sus clientes al entrar.

Es el único canal para hablarle a todos los clientes desde adentro del sistema; hasta
ahora solo existía WhatsApp de a uno.

**Un aviso activo por vez, y esa es la pieza que sostiene todo lo demás.** Activar uno
apaga los otros (`_apagar_los_demas`), así que "el aviso vigente" es siempre uno solo y
alcanza con guardar en el usuario **cuál fue el último que descartó**
(`Usuario.aviso_visto_id`, una columna, sin tabla de lecturas). Publicar uno nuevo le
cambia el id, así que todos lo vuelven a ver sin ninguna limpieza de por medio.

Eso también arregla el problema de fondo del "no volver a mostrar": si fuera un mute
global, el primer aviso quemaría el canal para siempre — alguien descarta una promo y ya
nunca se entera de que el box cierra el 24. Acá descartar es **por aviso**.

Y es por usuario, no por dispositivo: descartarlo en el celular también lo descarta en la
PC del gym. Es la diferencia con los cumpleaños felicitados, que viven en localStorage y
arrastran esa limitación conocida.
"""

from datetime import date, datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field, field_validator
from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from database import get_db
from fechas import hoy_bogota
from models import Aviso, RolUsuario, Usuario
from security import get_current_user

router = APIRouter(prefix="/avisos", tags=["Avisos"])

# Quiénes ven el cartel. El staff no: ya se enteró de otra forma, y mezclar avisos
# internos con los del cliente en un mismo canal termina en que nadie lee ninguno.
ROLES_DESTINATARIOS = (RolUsuario.CLIENTE, RolUsuario.PENDIENTE)


def _require_admin(current_user: Usuario = Depends(get_current_user)):
    if current_user.rol != RolUsuario.ADMIN:
        raise HTTPException(status_code=403, detail="Solo el administrador puede gestionar los avisos.")
    return current_user


class AvisoBase(BaseModel):
    titulo: str = Field(..., min_length=1, max_length=120)
    cuerpo: str = Field(..., min_length=1, max_length=1000)
    boton_texto: Optional[str] = Field(None, max_length=40)
    boton_url: Optional[str] = Field(None, max_length=300)
    activo: bool = True
    hasta: Optional[date] = None

    @field_validator("boton_url")
    @classmethod
    def _url_segura(cls, v: Optional[str]) -> Optional[str]:
        """El destino termina en un `href`, así que un `javascript:` acá sería una
        inyección que el admin escribe y el cliente ejecuta. Solo ruta interna o http(s).
        """
        if v is None:
            return None
        v = v.strip()
        if not v:
            return None
        if not (v.startswith("/") or v.startswith("http://") or v.startswith("https://")):
            raise ValueError("El destino del botón tiene que ser una ruta interna (/planes) o un link http(s).")
        return v

    @field_validator("titulo", "cuerpo")
    @classmethod
    def _sin_espacios(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("No puede quedar vacío.")
        return v


class AvisoCreate(AvisoBase):
    pass


class AvisoUpdate(BaseModel):
    titulo: Optional[str] = Field(None, min_length=1, max_length=120)
    cuerpo: Optional[str] = Field(None, min_length=1, max_length=1000)
    boton_texto: Optional[str] = Field(None, max_length=40)
    boton_url: Optional[str] = Field(None, max_length=300)
    activo: Optional[bool] = None
    hasta: Optional[date] = None

    _url_segura = field_validator("boton_url")(AvisoBase._url_segura.__func__)


def _serializar(a: Aviso, descartes: int = 0) -> dict:
    return {
        "id": a.id,
        "titulo": a.titulo,
        "cuerpo": a.cuerpo,
        "boton_texto": a.boton_texto,
        "boton_url": a.boton_url,
        "activo": a.activo,
        "hasta": a.hasta.isoformat() if a.hasta else None,
        "vencido": bool(a.hasta and a.hasta < hoy_bogota()),
        "created_at": a.created_at.isoformat() if a.created_at else None,
        "descartes": descartes,
    }


def _apagar_los_demas(db: Session, salvo_id: Optional[int]) -> None:
    """Deja como mucho un aviso activo.

    Es lo que hace que `Usuario.aviso_visto_id` (un solo entero) alcance para saber si
    hay que mostrarle algo a alguien. Sin esta regla haría falta una tabla de lecturas.
    """
    q = db.query(Aviso).filter(Aviso.activo == True)
    if salvo_id is not None:
        q = q.filter(Aviso.id != salvo_id)
    q.update({"activo": False}, synchronize_session=False)


def aviso_vigente(db: Session) -> Optional[Aviso]:
    """El aviso que corresponde mostrar hoy, sin mirar a ningún usuario.

    `hasta` se compara contra el día de **Bogotá**: con la fecha de UTC, un aviso que
    vence hoy se apagaría a las 19:00 locales, en plena hora pico del box.

    El `order_by(id.desc())` no es decorativo: si por lo que sea quedaran dos activos,
    gana el más nuevo en vez de quedar a criterio del motor.
    """
    return (
        db.query(Aviso)
        .filter(Aviso.activo == True)
        .filter(or_(Aviso.hasta.is_(None), Aviso.hasta >= hoy_bogota()))
        .order_by(Aviso.id.desc())
        .first()
    )


@router.get("/mio")
def mi_aviso(
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    """El aviso que hay que mostrarle a quien pregunta, o `{"aviso": null}`.

    Lo consulta el layout una vez al cargar la app. Devuelve `null` —y no un 404— porque
    "no hay nada que mostrar" es el caso normal, no un error.
    """
    if current_user.rol not in ROLES_DESTINATARIOS:
        return {"aviso": None}
    aviso = aviso_vigente(db)
    if not aviso or current_user.aviso_visto_id == aviso.id:
        return {"aviso": None}
    return {"aviso": _serializar(aviso)}


@router.post("/{aviso_id}/visto", status_code=status.HTTP_204_NO_CONTENT)
def marcar_visto(
    aviso_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    """"No volver a mostrar": guarda que este usuario ya descartó **este** aviso.

    Cerrar el cartel sin tildar la casilla no llama acá, a propósito: vuelve a aparecer
    la próxima vez que abra la app, que es lo que se pidió.
    """
    if not db.query(Aviso).filter(Aviso.id == aviso_id).first():
        raise HTTPException(status_code=404, detail="Ese aviso no existe.")
    current_user.aviso_visto_id = aviso_id
    db.commit()


@router.get("/")
def listar_avisos(
    db: Session = Depends(get_db),
    _: Usuario = Depends(_require_admin),
):
    """Todos los avisos, del más nuevo al más viejo, con cuántos lo descartaron."""
    avisos = db.query(Aviso).order_by(Aviso.id.desc()).all()
    # Un solo COUNT agrupado en vez de uno por aviso: son pocos, pero el N+1 acá es
    # gratis de evitar.
    conteos = dict(
        db.query(Usuario.aviso_visto_id, func.count(Usuario.id))
        .filter(Usuario.aviso_visto_id.isnot(None))
        .group_by(Usuario.aviso_visto_id)
        .all()
    )
    return [_serializar(a, conteos.get(a.id, 0)) for a in avisos]


@router.post("/", status_code=status.HTTP_201_CREATED)
def crear_aviso(
    payload: AvisoCreate,
    db: Session = Depends(get_db),
    _: Usuario = Depends(_require_admin),
):
    aviso = Aviso(
        titulo=payload.titulo,
        cuerpo=payload.cuerpo,
        boton_texto=(payload.boton_texto or "").strip() or None,
        boton_url=payload.boton_url,
        activo=payload.activo,
        hasta=payload.hasta,
    )
    db.add(aviso)
    db.flush()  # necesita id antes de apagar los demás
    if aviso.activo:
        _apagar_los_demas(db, aviso.id)
    db.commit()
    db.refresh(aviso)
    return _serializar(aviso)


@router.patch("/{aviso_id}")
def actualizar_aviso(
    aviso_id: int,
    payload: AvisoUpdate,
    db: Session = Depends(get_db),
    _: Usuario = Depends(_require_admin),
):
    aviso = db.query(Aviso).filter(Aviso.id == aviso_id).first()
    if not aviso:
        raise HTTPException(status_code=404, detail="Ese aviso no existe.")

    datos = payload.model_dump(exclude_unset=True)
    for campo in ("titulo", "cuerpo", "activo", "hasta", "boton_url"):
        if campo in datos:
            setattr(aviso, campo, datos[campo])
    if "boton_texto" in datos:
        aviso.boton_texto = (datos["boton_texto"] or "").strip() or None
    aviso.updated_at = datetime.utcnow()

    if aviso.activo:
        _apagar_los_demas(db, aviso.id)
    db.commit()
    db.refresh(aviso)
    return _serializar(aviso)


@router.delete("/{aviso_id}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_aviso(
    aviso_id: int,
    db: Session = Depends(get_db),
    _: Usuario = Depends(_require_admin),
):
    """Borra un aviso.

    Los `aviso_visto_id` que apuntaban a él quedan huérfanos y está bien: son un número
    que ya no coincide con ningún aviso vigente, así que el próximo que se publique se
    va a mostrar igual. Limpiarlos sería trabajo para no cambiar nada.
    """
    aviso = db.query(Aviso).filter(Aviso.id == aviso_id).first()
    if not aviso:
        raise HTTPException(status_code=404, detail="Ese aviso no existe.")
    db.delete(aviso)
    db.commit()
