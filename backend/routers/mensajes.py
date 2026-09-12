"""
Plantillas editables de los mensajes de WhatsApp (cobro y cumpleaños).

**Este router guarda texto opaco, no sabe qué dice el mensaje.** Los textos por defecto
viven en `frontend/src/lib/mensajes.js`, que es el único lugar donde se arman los links
de `wa.me`; acá solo se persiste lo que el admin escribió *encima* del default. Eso
evita la copia doble de copy que en este proyecto ya se pagó caro con la normalización
de teléfonos, y hace que la pantalla siga funcionando si este endpoint falla: sin
override, el frontend usa su default y el botón de WhatsApp sigue andando.

Lo que sí vive acá es la **lista de claves válidas**: son cinco identificadores cortos,
no copy, y sin ese filtro cualquier PUT dejaría filas basura que nadie volvería a mirar.

Ojo con el alcance: estas plantillas son las de los links **manuales**. El envío
automático de vencimientos usa una plantilla aprobada por Meta cuyo cuerpo vive en los
servidores de Meta y no se puede cambiar desde acá (ver `whatsapp.py`).
"""

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

import whatsapp
from database import get_db
from models import PlantillaMensaje, RolUsuario, Usuario
from security import get_current_user

router = APIRouter(prefix="/mensajes", tags=["Mensajes"])

# Las claves las conoce el frontend; acá están para rechazar cualquier otra cosa.
CLAVES = {
    "cumpleanos",      # felicitación del día (panel de cumpleaños del Resumen)
    "vence",           # "tu membresía vence en N días" (panel Por vencer)
    "vencida",         # ya venció (tab Inactivos de Clientes)
    "sin_accesos",     # se le acabaron los accesos del bono (tab Inactivos)
    "sin_membresia",   # nunca tuvo membresía (tab Inactivos)
}

# Tope generoso: el texto viaja en la URL de wa.me y un mensaje de saludo no llega ni
# cerca de esto. Está para que un pegado accidental no deje una fila enorme en la base.
MAX_LARGO = 1000


def _require_admin(current_user: Usuario = Depends(get_current_user)):
    if current_user.rol != RolUsuario.ADMIN:
        raise HTTPException(status_code=403, detail="Solo el administrador puede editar los mensajes.")
    return current_user


def _require_admin_or_coach(current_user: Usuario = Depends(get_current_user)):
    if current_user.rol not in (RolUsuario.ADMIN, RolUsuario.COACH):
        raise HTTPException(status_code=403, detail="No tienes permiso para ver esto.")
    return current_user


class PlantillaUpdate(BaseModel):
    texto: str = Field(..., min_length=1, max_length=MAX_LARGO)


def _validar_clave(clave: str) -> str:
    if clave not in CLAVES:
        raise HTTPException(status_code=404, detail="Ese mensaje no existe.")
    return clave


@router.get("/")
def listar_mensajes(
    db: Session = Depends(get_db),
    _: Usuario = Depends(_require_admin_or_coach),
):
    """Los overrides guardados en `overrides`, más si el envío automático está prendido.

    `overrides` trae **solo lo personalizado**: una clave ausente significa "usá tu
    default", no "mensaje vacío". El coach también lo lee — no puede editarlos, pero
    manda los mismos recordatorios desde el Resumen y con la lista vacía escribiría el
    texto viejo.

    `envio_automatico` es lo que decide si el editor muestra el aviso de que la plantilla
    `vence` no aplica al envío de las 9:10. Va acá y no en otra llamada porque es el dato
    que vuelve verdadera o falsa una advertencia de esa misma pantalla, y sin él el aviso
    tendría que ser permanente: en un box sin la API de Meta configurada eso es una
    advertencia sobre algo que no ocurre, que es peor que no decir nada.
    """
    filas = db.query(PlantillaMensaje).all()
    return {
        "overrides": {f.clave: f.texto for f in filas},
        "envio_automatico": whatsapp.HABILITADO,
    }


@router.put("/{clave}")
def guardar_mensaje(
    clave: str,
    payload: PlantillaUpdate,
    db: Session = Depends(get_db),
    _: Usuario = Depends(_require_admin),
):
    """Upsert del texto de una plantilla."""
    _validar_clave(clave)
    texto = payload.texto.strip()
    if not texto:
        raise HTTPException(status_code=422, detail="El mensaje no puede quedar vacío.")

    fila = db.query(PlantillaMensaje).filter(PlantillaMensaje.clave == clave).first()
    if fila:
        fila.texto = texto
        fila.updated_at = datetime.utcnow()
    else:
        db.add(PlantillaMensaje(clave=clave, texto=texto))
    db.commit()
    return {"clave": clave, "texto": texto}


@router.delete("/{clave}", status_code=status.HTTP_204_NO_CONTENT)
def restaurar_mensaje(
    clave: str,
    db: Session = Depends(get_db),
    _: Usuario = Depends(_require_admin),
):
    """Vuelve al texto por defecto: borra el override y listo.

    No guarda el default en la fila. Guardarlo lo congelaría: si algún día se mejora el
    texto de fábrica, quien "restauró" seguiría con el viejo sin entender por qué.
    """
    _validar_clave(clave)
    fila = db.query(PlantillaMensaje).filter(PlantillaMensaje.clave == clave).first()
    if fila:
        db.delete(fila)
        db.commit()
