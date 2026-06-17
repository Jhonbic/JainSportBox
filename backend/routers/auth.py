from datetime import timedelta
from typing import Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import desc
from sqlalchemy.orm import Session

from database import get_db
from models import Pago, Plan, RolUsuario, Usuario
from security import ACCESS_TOKEN_EXPIRE_MINUTES, create_access_token, get_password_hash, verify_password, get_current_user
from storage import guardar_archivo

router = APIRouter(tags=["Auth"])

ALLOWED_TYPES = {"image/jpeg", "image/png", "image/webp"}


@router.post("/login")
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    email_norm = (form_data.username or "").strip().lower()
    usuario = db.query(Usuario).filter(Usuario.email == email_norm).first()
    if not usuario or not verify_password(form_data.password, usuario.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales incorrectas",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = create_access_token(
        data={"sub": usuario.email},
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
    )
    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/contacto")
def contacto_admin(db: Session = Depends(get_db)):
    from models import RolUsuario as _Rol
    admin = db.query(Usuario).filter(Usuario.rol == _Rol.ADMIN).first()
    return {"telefono": admin.telefono if admin else None}


@router.post("/registro", status_code=status.HTTP_201_CREATED)
def registro_publico(
    nombre: str = Form(..., min_length=2, max_length=120),
    email: str = Form(..., max_length=120),
    password: str = Form(..., min_length=6),
    documento_identidad: str = Form(..., min_length=5, max_length=20),
    genero: str = Form(...),
    telefono: str = Form(..., min_length=7, max_length=20),
    foto: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db),
):
    if genero not in ("masculino", "femenino"):
        raise HTTPException(status_code=422, detail="Género inválido.")
    email = (email or "").strip().lower()
    documento_identidad = (documento_identidad or "").strip()
    if db.query(Usuario).filter(Usuario.email == email).first():
        raise HTTPException(status_code=400, detail="Ya existe una cuenta con ese email.")
    if db.query(Usuario).filter(Usuario.documento_identidad == documento_identidad).first():
        raise HTTPException(status_code=400, detail="Ya existe una cuenta con ese documento de identidad.")

    nuevo = Usuario(
        nombre=nombre,
        email=email,
        password_hash=get_password_hash(password),
        documento_identidad=documento_identidad,
        genero=genero,
        telefono=telefono,
        rol=RolUsuario.PENDIENTE,
    )

    if foto and foto.filename:
        if foto.content_type not in ALLOWED_TYPES:
            raise HTTPException(status_code=400, detail="Formato de foto no permitido. Usa JPG, PNG o WEBP.")
        nuevo.foto_url = guardar_archivo(foto)

    db.add(nuevo)
    db.commit()
    return {"message": "Registro exitoso. Tu cuenta está pendiente de aprobación por el administrador."}


@router.get("/me")
def me(current_user: Usuario = Depends(get_current_user), db: Session = Depends(get_db)):
    incluye_wods_personalizados = False
    plan_actual = None
    if current_user.rol == RolUsuario.CLIENTE:
        ultimo_pago = (
            db.query(Pago)
            .filter(Pago.usuario_id == current_user.id)
            .order_by(desc(Pago.fecha_pago))
            .first()
        )
        if ultimo_pago:
            plan = db.query(Plan).filter(Plan.id == ultimo_pago.plan_id).first()
            if plan:
                incluye_wods_personalizados = plan.incluye_wods_personalizados
                plan_actual = {
                    "id": plan.id,
                    "nombre": plan.nombre,
                    "duracion_dias": plan.duracion_dias,
                    "precio": plan.precio,
                    "beneficios": plan.beneficios,
                    "incluye_wods_personalizados": plan.incluye_wods_personalizados,
                }
    return {
        "id": current_user.id,
        "nombre": current_user.nombre,
        "email": current_user.email,
        "rol": current_user.rol.value,
        "genero": current_user.genero,
        "fecha_vencimiento": current_user.fecha_vencimiento,
        "esta_en_gym": current_user.esta_en_gym,
        "plan_solicitado_id": current_user.plan_solicitado_id,
        "incluye_wods_personalizados": incluye_wods_personalizados,
        "plan_actual": plan_actual,
    }
