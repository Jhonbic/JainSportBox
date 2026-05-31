import math
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from database import get_db
from models import MarcaRM, Usuario
from schemas.marcas import MarcaRMCreate, MarcaRMResponse
from security import get_current_user

router = APIRouter(prefix="/marcas", tags=["Marcas RM"])


# Clasificación por ejercicio (debe coincidir con frontend/src/data/ejerciciosMarcas.js)
TIPOS_EJERCICIO = {
    "Back Squat": "barra",
    "Deadlift": "barra",
    "Clean": "barra",
    "Clean and Jerk": "barra",
    "Snatch": "barra",
    "Bench Press": "barra",
    "Press Militar": "barra",
    "Dominadas": "corporal_lastre",
    "Push Up": "reps",
    "Air Squat": "reps",
    "Sit Up": "reps",
    "Test de Léger": "leger",
}


def _tipo_de(ejercicio: str) -> str:
    return TIPOS_EJERCICIO.get(ejercicio.strip(), "barra")


def _calcular_1rm(peso: float, reps: int) -> float:
    w, r = peso, reps
    valores = [
        w * (36 / (37 - r)),                                    # Brzycki
        w * (1 + r / 30),                                        # Epley
        (100 * w) / (101.3 - 2.67123 * r),                     # Lander
        w * (1 + 0.025 * r),                                     # O'Conner
        w * (r ** 0.1),                                          # Lombardi
        (100 * w) / (52.2 + 41.9 * math.exp(-0.055 * r)),      # Mayhew
        (100 * w) / (48.8 + 53.8 * math.exp(-0.075 * r)),      # Wathen
    ]
    return round(sum(valores) / len(valores), 2)


@router.get("/", response_model=List[MarcaRMResponse])
def listar_todas(
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    return (
        db.query(MarcaRM)
        .filter(MarcaRM.usuario_id == current_user.id)
        .order_by(MarcaRM.fecha.asc())
        .all()
    )


@router.get("/{ejercicio}", response_model=List[MarcaRMResponse])
def listar_por_ejercicio(
    ejercicio: str,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    return (
        db.query(MarcaRM)
        .filter(MarcaRM.usuario_id == current_user.id, MarcaRM.ejercicio == ejercicio)
        .order_by(MarcaRM.fecha.asc())
        .all()
    )


@router.post("/", response_model=MarcaRMResponse, status_code=status.HTTP_201_CREATED)
def crear_marca(
    payload: MarcaRMCreate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    ejercicio = payload.ejercicio.strip()
    tipo = _tipo_de(ejercicio)

    peso = None
    unidad = payload.unidad
    reps = None
    rm = None
    peso_adicional = None
    nivel = None
    palier = None

    if tipo == "barra":
        if payload.peso is None or payload.peso <= 0 or payload.repeticiones is None:
            raise HTTPException(status_code=422, detail="Este ejercicio requiere peso y repeticiones.")
        peso = payload.peso
        reps = payload.repeticiones
        rm = _calcular_1rm(peso, reps)

    elif tipo == "corporal_lastre":
        # peso = peso corporal (snapshot) + peso_adicional opcional. Reps obligatorio.
        if payload.peso is None or payload.peso <= 0 or payload.repeticiones is None:
            raise HTTPException(
                status_code=422,
                detail="Se requiere peso total (corporal + lastre) y repeticiones.",
            )
        peso = payload.peso
        reps = payload.repeticiones
        peso_adicional = payload.peso_adicional
        rm = _calcular_1rm(peso, reps)

    elif tipo == "reps":
        if payload.repeticiones is None or payload.repeticiones < 1:
            raise HTTPException(status_code=422, detail="Se requiere número de repeticiones.")
        reps = payload.repeticiones

    elif tipo == "leger":
        if payload.nivel is None or payload.palier is None:
            raise HTTPException(status_code=422, detail="Se requiere nivel y palier.")
        nivel = payload.nivel
        palier = payload.palier

    marca = MarcaRM(
        usuario_id=current_user.id,
        ejercicio=ejercicio,
        peso=peso,
        unidad=unidad,
        repeticiones=reps,
        rm_calculado=rm,
        peso_adicional=peso_adicional,
        nivel=nivel,
        palier=palier,
        fecha=payload.fecha,
        notas=payload.notas,
    )
    db.add(marca)
    db.commit()
    db.refresh(marca)
    return marca


@router.delete("/{marca_id}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_marca(
    marca_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    marca = db.query(MarcaRM).filter(
        MarcaRM.id == marca_id,
        MarcaRM.usuario_id == current_user.id,
    ).first()
    if not marca:
        raise HTTPException(status_code=404, detail="Marca no encontrada.")
    db.delete(marca)
    db.commit()
