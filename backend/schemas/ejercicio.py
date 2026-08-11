from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class EjercicioCreate(BaseModel):
    nombre: str = Field(..., min_length=1, max_length=150)
    video_url: Optional[str] = Field(None, max_length=500)


class EjercicioUpdate(BaseModel):
    nombre: Optional[str] = Field(None, min_length=1, max_length=150)
    video_url: Optional[str] = Field(None, max_length=500)


class EjercicioResponse(BaseModel):
    id: int
    nombre: str
    video_url: Optional[str]
    created_at: datetime

    model_config = {"from_attributes": True}
