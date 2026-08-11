import json
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from database import get_db
from models import Plan, RolUsuario, Usuario
from security import get_current_user

router = APIRouter(prefix="/planes", tags=["Planes"])


def _require_admin(current_user: Usuario = Depends(get_current_user)):
    if current_user.rol != RolUsuario.ADMIN:
        raise HTTPException(status_code=403, detail="Solo el administrador puede realizar esta acción.")
    return current_user


class PlanCreate(BaseModel):
    nombre: str = Field(..., min_length=2, max_length=80)
    precio: float = Field(..., gt=0)
    duracion_dias: int = Field(..., gt=0)
    # None → plan por tiempo. N → bono de N ingresos, que igual caduca a los
    # duracion_dias (los dos ejes se validan juntos al marcar entrada).
    numero_ingresos: Optional[int] = Field(None, gt=0, le=1000)
    beneficios: List[str] = Field(default=[])
    descripcion: Optional[str] = None
    incluye_wods_personalizados: bool = False


class PlanUpdate(BaseModel):
    nombre: Optional[str] = Field(None, min_length=2, max_length=80)
    precio: Optional[float] = Field(None, gt=0)
    duracion_dias: Optional[int] = Field(None, gt=0)
    # 0 se acepta y significa "pasar a plan por tiempo": con gt=0 no habría forma de
    # sacarle los ingresos a un plan una vez puestos.
    numero_ingresos: Optional[int] = Field(None, ge=0, le=1000)
    beneficios: Optional[List[str]] = None
    descripcion: Optional[str] = None
    incluye_wods_personalizados: Optional[bool] = None


def _serializar(p: Plan) -> dict:
    return {
        "id": p.id,
        "nombre": p.nombre,
        "precio": p.precio,
        "duracion_dias": p.duracion_dias,
        "numero_ingresos": p.numero_ingresos,
        "por_ingresos": p.por_ingresos,
        "descripcion": p.descripcion,
        "beneficios": json.loads(p.beneficios) if p.beneficios else [],
        "activo": p.activo,
        "incluye_wods_personalizados": p.incluye_wods_personalizados,
    }


@router.get("/")
def listar_planes(db: Session = Depends(get_db)):
    return [_serializar(p) for p in db.query(Plan).filter(Plan.activo == True).all()]


@router.post("/", status_code=status.HTTP_201_CREATED)
def crear_plan(
    payload: PlanCreate,
    db: Session = Depends(get_db),
    _: Usuario = Depends(_require_admin),
):
    plan = Plan(
        nombre=payload.nombre,
        precio=payload.precio,
        duracion_dias=payload.duracion_dias,
        numero_ingresos=payload.numero_ingresos,
        descripcion=payload.descripcion,
        beneficios=json.dumps(payload.beneficios, ensure_ascii=False),
        incluye_wods_personalizados=payload.incluye_wods_personalizados,
    )
    db.add(plan)
    db.commit()
    db.refresh(plan)
    return _serializar(plan)


@router.patch("/{plan_id}")
def actualizar_plan(
    plan_id: int,
    payload: PlanUpdate,
    db: Session = Depends(get_db),
    _: Usuario = Depends(_require_admin),
):
    plan = db.query(Plan).filter(Plan.id == plan_id).first()
    if not plan:
        raise HTTPException(status_code=404, detail="Plan no encontrado.")
    if payload.nombre is not None:
        plan.nombre = payload.nombre
    if payload.precio is not None:
        plan.precio = payload.precio
    if payload.duracion_dias is not None:
        plan.duracion_dias = payload.duracion_dias
    if payload.numero_ingresos is not None:
        plan.numero_ingresos = payload.numero_ingresos or None   # 0 → por tiempo
    if payload.descripcion is not None:
        plan.descripcion = payload.descripcion
    if payload.beneficios is not None:
        plan.beneficios = json.dumps(payload.beneficios, ensure_ascii=False)
    if payload.incluye_wods_personalizados is not None:
        plan.incluye_wods_personalizados = payload.incluye_wods_personalizados
    db.commit()
    db.refresh(plan)
    return _serializar(plan)


@router.delete("/{plan_id}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_plan(
    plan_id: int,
    db: Session = Depends(get_db),
    _: Usuario = Depends(_require_admin),
):
    plan = db.query(Plan).filter(Plan.id == plan_id).first()
    if not plan:
        raise HTTPException(status_code=404, detail="Plan no encontrado.")
    plan.activo = False
    db.commit()
