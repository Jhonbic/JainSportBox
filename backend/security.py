import os
from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from dotenv import load_dotenv

load_dotenv()

from database import get_db
from models import Usuario

SECRET_KEY = os.environ["SECRET_KEY"]
ALGORITHM = "HS256"
# Expiración del JWT configurable por entorno (default 7 días). Bajarla acota la
# ventana de un token robado; sin refresh-token, un valor muy corto obliga a
# re-login frecuente, por eso el default se mantiene alto.
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", str(60 * 24 * 7)))

# Costo de bcrypt. El default de passlib es 12, y en Render Starter (0.5 CPU) un
# verify con 12 rondas tarda ~600 ms medidos contra producción — cuatro veces lo
# que tarda el mismo login con un email inexistente, que ni llega a hashear.
# Cada ronda duplica el trabajo, así que 11 lo deja en ~300 ms y sigue por encima
# del piso de 10 que recomienda OWASP.
#
# No es solo comodidad: cada intento quema ese tiempo del único núcleo, así que en
# la hora pico los logins se hacen cola entre ellos y contra las marcaciones de
# huella. Si algún día el plan sube de CPU, esto puede volver a 12.
BCRYPT_ROUNDS = int(os.getenv("BCRYPT_ROUNDS", "11"))

# `max_rounds` no es redundante con `default_rounds`. passlib solo marca un hash como
# "hay que renovarlo" cuando es MÁS DÉBIL de lo configurado: bajar el default no alcanza,
# porque un hash de 12 rondas es más fuerte que uno de 11 y no hay razón de seguridad
# para tocarlo. Acá la razón es de rendimiento, así que hay que declarar el techo para
# que `verify_and_update` los reemplace. Sin esta línea la migración no ocurre y el admin
# —que es quien más entra— se queda con las 12 rondas para siempre.
pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto",
    bcrypt__default_rounds=BCRYPT_ROUNDS,
    bcrypt__max_rounds=BCRYPT_ROUNDS,
)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def verificar_y_renovar_hash(plain_password: str, hashed_password: str):
    """Verifica la contraseña y, si el hash quedó con un costo viejo, devuelve uno nuevo.

    Cambiar `BCRYPT_ROUNDS` solo afecta a los hashes que se crean de ahí en más: los
    usuarios que ya existen seguirían pagando las 12 rondas para siempre. `deprecated="auto"`
    marca esos hashes como obsoletos y passlib devuelve el reemplazo acá, así cada
    persona migra sola la próxima vez que entra bien y sin enterarse.

    Devuelve `(es_valida, hash_nuevo_o_None)`.
    """
    return pwd_context.verify_and_update(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
        email = email.strip().lower()
    except JWTError:
        raise credentials_exception

    user = db.query(Usuario).filter(Usuario.email == email).first()
    if user is None:
        raise credentials_exception
    return user
