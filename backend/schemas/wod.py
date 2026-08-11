from datetime import date, datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class WODEjercicioItem(BaseModel):
    """Video (ejercicio del catálogo) adjuntado al WOD.

    La prescripción (reps, peso, %RM, tiempo…) va en texto libre en
    `WODCreate.descripcion` — acá solo se referencia el video a ver.
    """
    ejercicio_id: int
    orden: int = 0


class WODEjercicioResponse(BaseModel):
    # `nombre` y `video_url` salen de properties de WODEjercicio que delegan al
    # Ejercicio. Había también `descripcion`, que se fue con la columna.
    ejercicio_id: int
    nombre: Optional[str] = None
    video_url: Optional[str] = None
    orden: int

    model_config = {"from_attributes": True}


_TIPOS_WOD = r'^(For Time|AMRAP|EMOM|Por Rondas|Fuerza|Otro)$'


class WODCreate(BaseModel):
    titulo: str = Field(..., min_length=1, max_length=150)
    descripcion: str = Field("", max_length=5000)
    fecha: date
    activo: bool = True
    es_personalizado: bool = False
    genero_destino: Optional[str] = Field(None, pattern=r'^(masculino|femenino)$')
    tipo: Optional[str] = Field(None, pattern=_TIPOS_WOD)
    ejercicios: Optional[List[WODEjercicioItem]] = None


class WODUpdate(BaseModel):
    titulo: Optional[str] = Field(None, min_length=1, max_length=150)
    descripcion: Optional[str] = Field(None, max_length=5000)
    fecha: Optional[date] = None
    activo: Optional[bool] = None
    es_personalizado: Optional[bool] = None
    genero_destino: Optional[str] = Field(None, pattern=r'^(masculino|femenino)$')
    tipo: Optional[str] = Field(None, pattern=_TIPOS_WOD)
    ejercicios: Optional[List[WODEjercicioItem]] = None


class WODResponse(BaseModel):
    id: int
    titulo: str
    descripcion: str
    fecha: date
    activo: bool
    coach_id: Optional[int]
    es_personalizado: bool
    genero_destino: Optional[str]
    tipo: Optional[str]
    created_at: datetime
    ejercicios: List[WODEjercicioResponse] = []

    model_config = {"from_attributes": True}
