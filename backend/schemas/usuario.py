from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, Field

from models import RolUsuario


class UsuarioCreate(BaseModel):
    nombre: str = Field(..., min_length=2, max_length=120)
    email: str = Field(..., max_length=120)
    password: str = Field(..., min_length=8)
    documento_identidad: str = Field(..., min_length=5, max_length=20)
    genero: str = Field(..., pattern=r'^(masculino|femenino)$')
    rol: RolUsuario = RolUsuario.CLIENTE
    huella_id: Optional[str] = None
    telefono: str = Field(..., min_length=7, max_length=20)
    fecha_nacimiento: Optional[date] = None
    eps: Optional[str] = Field(None, max_length=100)
    barrio: Optional[str] = Field(None, max_length=100)
    contacto_emergencia_nombre: Optional[str] = Field(None, max_length=120)
    contacto_emergencia_telefono: Optional[str] = Field(None, max_length=20)
    es_menor: bool = False
    acudiente_nombre: Optional[str] = Field(None, max_length=120)
    acudiente_telefono: Optional[str] = Field(None, max_length=20)
    acudiente_documento: Optional[str] = Field(None, max_length=20)


class UsuarioUpdate(BaseModel):
    nombre: Optional[str] = Field(None, min_length=2, max_length=120)
    email: Optional[str] = Field(None, max_length=120)
    password: Optional[str] = Field(None, min_length=8)
    telefono: Optional[str] = Field(None, max_length=20)
    documento_identidad: Optional[str] = Field(None, min_length=5, max_length=20)
    genero: Optional[str] = Field(None, pattern=r'^(masculino|femenino)$')
    fecha_nacimiento: Optional[date] = None
    eps: Optional[str] = Field(None, max_length=100)
    barrio: Optional[str] = Field(None, max_length=100)
    contacto_emergencia_nombre: Optional[str] = Field(None, max_length=120)
    contacto_emergencia_telefono: Optional[str] = Field(None, max_length=20)
    es_menor: Optional[bool] = None
    acudiente_nombre: Optional[str] = Field(None, max_length=120)
    acudiente_telefono: Optional[str] = Field(None, max_length=20)
    acudiente_documento: Optional[str] = Field(None, max_length=20)


class UsuarioResponse(BaseModel):
    id: int
    nombre: str
    email: str
    documento_identidad: Optional[str] = None
    rol: RolUsuario
    huella_id: Optional[str]
    telefono: Optional[str]
    fecha_vencimiento: Optional[date]
    esta_en_gym: bool
    foto_url: Optional[str]
    genero: Optional[str]
    fecha_nacimiento: Optional[date] = None
    eps: Optional[str] = None
    barrio: Optional[str] = None
    contacto_emergencia_nombre: Optional[str] = None
    contacto_emergencia_telefono: Optional[str] = None
    es_menor: bool = False
    acudiente_nombre: Optional[str] = None
    acudiente_telefono: Optional[str] = None
    acudiente_documento: Optional[str] = None
    acepto_terminos: bool = False
    terminos_fecha: Optional[datetime] = None
    terminos_version: Optional[str] = None
    plan_solicitado_id: Optional[int]
    created_at: datetime

    model_config = {"from_attributes": True}
