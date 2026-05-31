from datetime import date, datetime
from typing import Optional
from pydantic import BaseModel, Field


class MarcaRMCreate(BaseModel):
    """Payload flexible que cubre los 4 tipos de ejercicio.

    - barra:           peso + repeticiones
    - corporal_lastre: peso (corporal + adicional snapshot) + repeticiones; peso_adicional opcional
    - reps:            solo repeticiones
    - leger:           nivel + palier
    """
    ejercicio: str = Field(..., min_length=1, max_length=100)
    fecha: date
    notas: Optional[str] = None
    # barra / corporal_lastre / reps
    peso: Optional[float] = Field(None, ge=0)
    unidad: str = Field("kg", pattern="^(kg|lbs)$")
    repeticiones: Optional[int] = Field(None, ge=1, le=100)
    # corporal_lastre
    peso_adicional: Optional[float] = Field(None, ge=0)
    # leger
    nivel: Optional[int] = Field(None, ge=1, le=23)
    palier: Optional[int] = Field(None, ge=1, le=20)


class MarcaRMResponse(BaseModel):
    id: int
    usuario_id: int
    ejercicio: str
    peso: Optional[float]
    unidad: str
    repeticiones: Optional[int]
    rm_calculado: Optional[float]
    peso_adicional: Optional[float]
    nivel: Optional[int]
    palier: Optional[int]
    fecha: date
    notas: Optional[str]
    created_at: datetime

    model_config = {"from_attributes": True}
