from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, field_validator

from marcas_tipos import TIPOS_MARCA


def _validar_tipo_marca(v: Optional[str]) -> Optional[str]:
    # La cadena vacía es cómo el formulario dice "este ejercicio no se mide": un
    # <select> no puede mandar None. Se normaliza a NULL en vez de guardarse.
    if v is None or v == "":
        return None
    v = v.strip()
    if v not in TIPOS_MARCA:
        raise ValueError(f"Tipo de marca inválido. Opciones: {', '.join(TIPOS_MARCA)}.")
    return v


class EjercicioCreate(BaseModel):
    nombre: str = Field(..., min_length=1, max_length=150)
    video_url: Optional[str] = Field(None, max_length=500)
    tipo_marca: Optional[str] = Field(None, max_length=20)

    _v = field_validator("tipo_marca")(_validar_tipo_marca)


class EjercicioUpdate(BaseModel):
    nombre: Optional[str] = Field(None, min_length=1, max_length=150)
    video_url: Optional[str] = Field(None, max_length=500)
    tipo_marca: Optional[str] = Field(None, max_length=20)

    _v = field_validator("tipo_marca")(_validar_tipo_marca)


class EjercicioResponse(BaseModel):
    id: int
    nombre: str
    video_url: Optional[str]
    tipo_marca: Optional[str]
    created_at: datetime

    model_config = {"from_attributes": True}


class EjercicioMedibleResponse(BaseModel):
    """Lo que Mis Marcas necesita del catálogo: sin id ni fechas.

    El video viaja porque la página de la marca lo muestra — fue el bonus de
    unificar el catálogo de marcas con el de videos de los WODs.
    """
    nombre: str
    tipo: str
    video_url: Optional[str]
