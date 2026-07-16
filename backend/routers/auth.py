from datetime import date, datetime, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import desc
from sqlalchemy.orm import Session

from database import get_db
from fechas import TZ_BOGOTA, hoy_bogota
from models import Pago, Plan, RolUsuario, Usuario
from schemas.usuario import UsuarioUpdate
from security import ACCESS_TOKEN_EXPIRE_MINUTES, create_access_token, get_password_hash, verify_password, get_current_user
from storage import guardar_archivo, eliminar_archivo
from ratelimit import limitar

router = APIRouter(tags=["Auth"])

ALLOWED_TYPES = {"image/jpeg", "image/png", "image/webp"}

# Versión del contrato de adhesión que acepta el usuario al registrarse.
# Mantener en sincronía con frontend/src/components/TerminosModal.vue.
TERMINOS_VERSION = "v2.0-2026"


def _calcular_edad(fecha_nacimiento: date) -> int:
    hoy = hoy_bogota()
    return hoy.year - fecha_nacimiento.year - (
        (hoy.month, hoy.day) < (fecha_nacimiento.month, fecha_nacimiento.day)
    )

# Límites por IP: mitigan fuerza bruta en login y spam de registros.
_limite_login = limitar("login", max_requests=10, window_seconds=300)     # 10 / 5 min
_limite_registro = limitar("registro", max_requests=5, window_seconds=3600)  # 5 / hora


@router.post("/login")
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
    _rl: None = Depends(_limite_login),
):
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
    password: str = Form(..., min_length=8),
    documento_identidad: str = Form(..., min_length=5, max_length=20),
    genero: str = Form(...),
    telefono: str = Form(..., min_length=7, max_length=20),
    fecha_nacimiento: date = Form(...),
    eps: str = Form(..., min_length=2, max_length=100),
    barrio: str = Form(..., min_length=2, max_length=100),
    contacto_emergencia_nombre: str = Form(..., min_length=2, max_length=120),
    contacto_emergencia_telefono: str = Form(..., min_length=7, max_length=20),
    acepta_terminos: bool = Form(...),
    es_menor: bool = Form(False),
    acudiente_nombre: Optional[str] = Form(None, max_length=120),
    acudiente_telefono: Optional[str] = Form(None, max_length=20),
    acudiente_documento: Optional[str] = Form(None, max_length=20),
    foto: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db),
    _rl: None = Depends(_limite_registro),
):
    if genero not in ("masculino", "femenino"):
        raise HTTPException(status_code=422, detail="Género inválido.")
    if not acepta_terminos:
        raise HTTPException(status_code=422, detail="Debes aceptar los Términos, Condiciones y el Consentimiento Informado.")
    if fecha_nacimiento >= hoy_bogota():
        raise HTTPException(status_code=422, detail="Fecha de nacimiento inválida.")

    edad = _calcular_edad(fecha_nacimiento)
    if edad < 18 and not es_menor:
        raise HTTPException(
            status_code=422,
            detail="Según la fecha de nacimiento el usuario es menor de edad: marca la casilla de menor de edad y registra los datos del acudiente.",
        )
    if es_menor:
        if (
            not (acudiente_nombre or "").strip()
            or not (acudiente_telefono or "").strip()
            or not (acudiente_documento or "").strip()
        ):
            raise HTTPException(status_code=422, detail="Para menores de edad se requiere nombre, teléfono y cédula del acudiente.")
        acudiente_nombre = acudiente_nombre.strip()
        acudiente_telefono = acudiente_telefono.strip()
        acudiente_documento = acudiente_documento.strip()
    else:
        acudiente_nombre = None
        acudiente_telefono = None
        acudiente_documento = None

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
        fecha_nacimiento=fecha_nacimiento,
        eps=eps.strip(),
        barrio=barrio.strip(),
        contacto_emergencia_nombre=contacto_emergencia_nombre.strip(),
        contacto_emergencia_telefono=contacto_emergencia_telefono.strip(),
        es_menor=es_menor,
        acudiente_nombre=acudiente_nombre,
        acudiente_telefono=acudiente_telefono,
        acudiente_documento=acudiente_documento,
        acepto_terminos=True,
        terminos_fecha=datetime.now(TZ_BOGOTA).replace(tzinfo=None),
        terminos_version=TERMINOS_VERSION,
        rol=RolUsuario.PENDIENTE,
    )

    if foto and foto.filename:
        if foto.content_type not in ALLOWED_TYPES:
            raise HTTPException(status_code=400, detail="Formato de foto no permitido. Usa JPG, PNG o WEBP.")
        nuevo.foto_url = guardar_archivo(foto)

    db.add(nuevo)
    db.commit()
    return {"message": "Registro exitoso. Tu cuenta está pendiente de aprobación por el administrador."}


def _serialize_me(current_user: Usuario, db: Session) -> dict:
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
        "telefono": current_user.telefono,
        "documento_identidad": current_user.documento_identidad,
        "fecha_nacimiento": current_user.fecha_nacimiento,
        "eps": current_user.eps,
        "barrio": current_user.barrio,
        "contacto_emergencia_nombre": current_user.contacto_emergencia_nombre,
        "contacto_emergencia_telefono": current_user.contacto_emergencia_telefono,
        "es_menor": current_user.es_menor,
        "acudiente_nombre": current_user.acudiente_nombre,
        "acudiente_telefono": current_user.acudiente_telefono,
        "acudiente_documento": current_user.acudiente_documento,
        "acepto_terminos": current_user.acepto_terminos,
        "terminos_fecha": current_user.terminos_fecha,
        "terminos_version": current_user.terminos_version,
        "foto_url": current_user.foto_url,
        "fecha_vencimiento": current_user.fecha_vencimiento,
        "esta_en_gym": current_user.esta_en_gym,
        "plan_solicitado_id": current_user.plan_solicitado_id,
        "incluye_wods_personalizados": incluye_wods_personalizados,
        "plan_actual": plan_actual,
    }


@router.get("/me")
def me(current_user: Usuario = Depends(get_current_user), db: Session = Depends(get_db)):
    return _serialize_me(current_user, db)


@router.patch("/me")
def actualizar_mi_perfil(
    payload: UsuarioUpdate,
    current_user: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Permite a cualquier usuario autenticado editar su propio perfil."""
    if payload.nombre is not None:
        current_user.nombre = payload.nombre

    if payload.email is not None:
        email_norm = payload.email.strip().lower()
        duplicado = (
            db.query(Usuario)
            .filter(Usuario.email == email_norm, Usuario.id != current_user.id)
            .first()
        )
        if duplicado:
            raise HTTPException(status_code=400, detail="Ya existe un usuario con ese email.")
        current_user.email = email_norm

    if payload.password is not None:
        current_user.password_hash = get_password_hash(payload.password)

    if payload.telefono is not None:
        current_user.telefono = payload.telefono

    if payload.documento_identidad is not None:
        doc_norm = payload.documento_identidad.strip()
        duplicado_doc = (
            db.query(Usuario)
            .filter(Usuario.documento_identidad == doc_norm, Usuario.id != current_user.id)
            .first()
        )
        if duplicado_doc:
            raise HTTPException(status_code=400, detail="Ya existe un usuario con ese documento de identidad.")
        current_user.documento_identidad = doc_norm

    if payload.genero is not None:
        current_user.genero = payload.genero

    if payload.fecha_nacimiento is not None:
        current_user.fecha_nacimiento = payload.fecha_nacimiento

    if payload.eps is not None:
        current_user.eps = payload.eps

    if payload.barrio is not None:
        current_user.barrio = payload.barrio

    if payload.contacto_emergencia_nombre is not None:
        current_user.contacto_emergencia_nombre = payload.contacto_emergencia_nombre

    if payload.contacto_emergencia_telefono is not None:
        current_user.contacto_emergencia_telefono = payload.contacto_emergencia_telefono

    if payload.acudiente_nombre is not None:
        current_user.acudiente_nombre = payload.acudiente_nombre

    if payload.acudiente_telefono is not None:
        current_user.acudiente_telefono = payload.acudiente_telefono

    if payload.acudiente_documento is not None:
        current_user.acudiente_documento = payload.acudiente_documento

    db.commit()
    db.refresh(current_user)
    return _serialize_me(current_user, db)


@router.post("/me/foto")
def subir_mi_foto(
    foto: UploadFile = File(...),
    current_user: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Permite a cualquier usuario autenticado cambiar su propia foto de perfil."""
    if foto.content_type not in ALLOWED_TYPES:
        raise HTTPException(status_code=400, detail="Formato no permitido. Usa JPG, PNG o WEBP.")
    if current_user.foto_url:
        eliminar_archivo(current_user.foto_url)
    current_user.foto_url = guardar_archivo(foto)
    db.commit()
    db.refresh(current_user)
    return _serialize_me(current_user, db)
