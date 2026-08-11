"""
Modelos SQLAlchemy para el sistema de gestión de Jain Sport Box.
Define las tablas: Usuarios, Planes, Pagos, WODs, Resultados, Inventario y Ventas.
"""

from datetime import datetime, date
from typing import Optional, List

from sqlalchemy import (
    String,
    Integer,
    Float,
    Boolean,
    Text,
    Date,
    DateTime,
    ForeignKey,
    UniqueConstraint,
    Enum as SAEnum,
)
from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    mapped_column,
    relationship,
)
import enum


# ──────────────────────────── Enums ────────────────────────────

class RolUsuario(str, enum.Enum):
    ADMIN = "admin"
    COACH = "coach"
    CLIENTE = "cliente"
    PENDIENTE = "pendiente"


class TipoMovimiento(str, enum.Enum):
    INGRESO = "ingreso"
    EGRESO = "egreso"


# ──────────────────────────── Base ────────────────────────────

class Base(DeclarativeBase):
    pass


# ──────────────────────────── Usuarios ────────────────────────

class Usuario(Base):
    __tablename__ = "usuarios"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    nombre: Mapped[str] = mapped_column(String(120), nullable=False)
    email: Mapped[str] = mapped_column(String(120), unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(256), nullable=False)
    rol: Mapped[RolUsuario] = mapped_column(SAEnum(RolUsuario), default=RolUsuario.CLIENTE, nullable=False)
    documento_identidad: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)
    huella_id: Mapped[Optional[str]] = mapped_column(String(100), unique=True, nullable=True)
    huella_template: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    telefono: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    fecha_vencimiento: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    # NULL → la membresía es por tiempo y los ingresos no aplican.
    # int  → membresía por ingresos: entradas que le quedan (0 = agotada).
    # Se usa el NULL en vez de un 0 para no tener que mirar el último plan en cada
    # marcación: sin este centinela, un socio con mensualidad tendría 0 ingresos y
    # no habría forma de distinguirlo de un bono agotado.
    ingresos_restantes: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    esta_en_gym: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    foto_url: Mapped[Optional[str]] = mapped_column(String(300), nullable=True)
    genero: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    fecha_nacimiento: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    plan_solicitado_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    eps: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    barrio: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    contacto_emergencia_nombre: Mapped[Optional[str]] = mapped_column(String(120), nullable=True)
    contacto_emergencia_telefono: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    # Menores de edad: el registro lo hace el acudiente (cláusula 7 del contrato).
    es_menor: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    acudiente_nombre: Mapped[Optional[str]] = mapped_column(String(120), nullable=True)
    acudiente_telefono: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    acudiente_documento: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    # Aceptación del contrato de adhesión (Ley 527 de 1999): quedan fecha y versión.
    acepto_terminos: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    terminos_fecha: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    terminos_version: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # ── Relaciones ──
    pagos: Mapped[List["Pago"]] = relationship("Pago", back_populates="usuario", cascade="all, delete-orphan")
    resultados: Mapped[List["ResultadoWOD"]] = relationship("ResultadoWOD", back_populates="usuario", cascade="all, delete-orphan")
    ventas: Mapped[List["Venta"]] = relationship("Venta", back_populates="usuario", cascade="all, delete-orphan")
    asistencias: Mapped[List["Asistencia"]] = relationship("Asistencia", back_populates="usuario", cascade="all, delete-orphan")
    marcas_rm: Mapped[List["MarcaRM"]] = relationship("MarcaRM", back_populates="usuario", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<Usuario {self.id} – {self.nombre} ({self.rol.value})>"


# ──────────────────────────── Planes ──────────────────────────

class Plan(Base):
    __tablename__ = "planes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    nombre: Mapped[str] = mapped_column(String(80), nullable=False)
    precio: Mapped[float] = mapped_column(Float, nullable=False)
    duracion_dias: Mapped[int] = mapped_column(Integer, nullable=False)
    # NULL → plan por tiempo (la vigencia la da solo duracion_dias).
    # N    → plan por ingresos: N entradas, que además caducan a los duracion_dias.
    numero_ingresos: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    descripcion: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    beneficios: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON array de strings
    activo: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    incluye_wods_personalizados: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    @property
    def por_ingresos(self) -> bool:
        return bool(self.numero_ingresos)

    # ── Relaciones ──
    pagos: Mapped[List["Pago"]] = relationship("Pago", back_populates="plan")

    def __repr__(self) -> str:
        return f"<Plan {self.id} – {self.nombre} (${self.precio})>"


# ──────────────────────────── Pagos ───────────────────────────

class Pago(Base):
    __tablename__ = "pagos"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    usuario_id: Mapped[int] = mapped_column(Integer, ForeignKey("usuarios.id"), nullable=False)
    plan_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("planes.id"), nullable=True)
    duracion_dias: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)   # solo para pagos personalizados (plan_id NULL)
    fecha_pago: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    monto: Mapped[float] = mapped_column(Float, nullable=False)
    metodo_pago: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)   # efectivo, transferencia, etc.

    # ── Relaciones ──
    usuario: Mapped["Usuario"] = relationship("Usuario", back_populates="pagos")
    plan: Mapped[Optional["Plan"]] = relationship("Plan", back_populates="pagos")

    def __repr__(self) -> str:
        return f"<Pago {self.id} – Usuario {self.usuario_id} → Plan {self.plan_id}>"


# ──────────────────────────── WODs ────────────────────────────

class WOD(Base):
    """Workout Of the Day – Rutina del día."""
    __tablename__ = "wods"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    titulo: Mapped[str] = mapped_column(String(150), nullable=False)
    descripcion: Mapped[str] = mapped_column(Text, nullable=False)
    fecha: Mapped[date] = mapped_column(Date, nullable=False)
    activo: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    coach_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("usuarios.id"), nullable=True)
    es_personalizado: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    genero_destino: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)  # masculino | femenino
    tipo: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)             # For Time | AMRAP | EMOM | Por Rondas | Fuerza | Otro
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # ── Relaciones ──
    coach: Mapped[Optional["Usuario"]] = relationship("Usuario", foreign_keys=[coach_id])
    resultados: Mapped[List["ResultadoWOD"]] = relationship("ResultadoWOD", back_populates="wod", cascade="all, delete-orphan")
    ejercicios: Mapped[List["WODEjercicio"]] = relationship(
        "WODEjercicio",
        back_populates="wod",
        cascade="all, delete-orphan",
        order_by="WODEjercicio.orden",
    )

    def __repr__(self) -> str:
        return f"<WOD {self.id} – {self.titulo} ({self.fecha})>"


# ──────────────────────── Resultados WOD ──────────────────────

class ResultadoWOD(Base):
    """Resultado / marca de un cliente en un WOD específico."""
    __tablename__ = "resultados_wod"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    usuario_id: Mapped[int] = mapped_column(Integer, ForeignKey("usuarios.id"), nullable=False)
    wod_id: Mapped[int] = mapped_column(Integer, ForeignKey("wods.id"), nullable=False)
    tiempo_segundos: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)    # Para WODs "For Time"
    rondas: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)             # Para AMRAPs
    peso_kg: Mapped[Optional[float]] = mapped_column(Float, nullable=True)            # Para WODs de fuerza
    notas: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    rx: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)          # ¿Hizo RX (prescrito)?
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # ── Relaciones ──
    usuario: Mapped["Usuario"] = relationship("Usuario", back_populates="resultados")
    wod: Mapped["WOD"] = relationship("WOD", back_populates="resultados")

    def __repr__(self) -> str:
        return f"<ResultadoWOD {self.id} – Usuario {self.usuario_id} / WOD {self.wod_id}>"


# ──────────────────────── Catálogo de ejercicios ──────────────

class Ejercicio(Base):
    """Ejercicio reutilizable (nombre + video) para armar los WODs."""
    __tablename__ = "ejercicios"

    # Dos campos y nada más, a propósito. El catálogo tuvo `categoria`
    # (Cardio/Fuerza/Gimnasia/Olímpico/Otro) y `descripcion`, y se sacaron: lo que el
    # coach necesita al armar un WOD es encontrar el ejercicio por nombre y tener el
    # video a mano. Las columnas NO se borraron de la base — siguen ahí con sus datos,
    # solo que el modelo ya no las mapea, así que volver atrás es re-agregar estas dos
    # líneas. Si se decide que los datos viejos no van más, ahí sí un DROP COLUMN.
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    nombre: Mapped[str] = mapped_column(String(150), nullable=False, unique=True)
    video_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    def __repr__(self) -> str:
        return f"<Ejercicio {self.id} – {self.nombre}>"


class WODEjercicio(Base):
    """Video del catálogo adjuntado a un WOD, con su orden de aparición.

    La rutina (reps, peso, %RM, tiempo, esquema…) va en texto libre en
    `WOD.descripcion`; acá solo se referencia qué videos debe ver el cliente.
    Las columnas de prescripción (`notas`, `rep_min`, `rep_max`, `rir`,
    `porcentaje_rm`, `tiempo_segundos`, `superserie_con_anterior`) son legacy:
    se conservan por los WODs históricos, no se escriben ni se serializan.
    """
    __tablename__ = "wod_ejercicios"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    wod_id: Mapped[int] = mapped_column(Integer, ForeignKey("wods.id"), nullable=False)
    ejercicio_id: Mapped[int] = mapped_column(Integer, ForeignKey("ejercicios.id"), nullable=False)
    orden: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    # ── Legacy (ver docstring): no se escriben desde la app ──
    notas: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    rep_min: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    rep_max: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    rir: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    porcentaje_rm: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    tiempo_segundos: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    superserie_con_anterior: Mapped[bool] = mapped_column(Boolean, default=False)

    # ── Relaciones ──
    wod: Mapped["WOD"] = relationship("WOD", back_populates="ejercicios")
    ejercicio: Mapped["Ejercicio"] = relationship("Ejercicio")

    # Atajos para la serialización en WODResponse
    @property
    def nombre(self) -> Optional[str]:
        return self.ejercicio.nombre if self.ejercicio else None

    @property
    def video_url(self) -> Optional[str]:
        return self.ejercicio.video_url if self.ejercicio else None

    def __repr__(self) -> str:
        return f"<WODEjercicio WOD {self.wod_id} → Ejercicio {self.ejercicio_id}>"


# ──────────────────────────── Inventario ──────────────────────

class Producto(Base):
    """Producto de la tienda del box."""
    __tablename__ = "productos"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    nombre: Mapped[str] = mapped_column(String(150), nullable=False)
    descripcion: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    precio: Mapped[float] = mapped_column(Float, nullable=False)
    stock: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    categoria: Mapped[Optional[str]] = mapped_column(String(80), nullable=True)
    activo: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    foto_url: Mapped[Optional[str]] = mapped_column(String(300), nullable=True)

    # ── Relaciones ──
    ventas: Mapped[List["Venta"]] = relationship("Venta", back_populates="producto")

    def __repr__(self) -> str:
        return f"<Producto {self.id} – {self.nombre} (stock: {self.stock})>"


# ──────────────────────────── Ventas ──────────────────────────

class Venta(Base):
    """Registro de venta de productos de la tienda."""
    __tablename__ = "ventas"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    producto_id: Mapped[int] = mapped_column(Integer, ForeignKey("productos.id"), nullable=False)
    usuario_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("usuarios.id"), nullable=True)
    cantidad: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    precio_unitario: Mapped[float] = mapped_column(Float, nullable=False)
    total: Mapped[float] = mapped_column(Float, nullable=False)
    metodo_pago: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    fecha_venta: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # ── Relaciones ──
    producto: Mapped["Producto"] = relationship("Producto", back_populates="ventas")
    usuario: Mapped[Optional["Usuario"]] = relationship("Usuario", back_populates="ventas")

    def __repr__(self) -> str:
        return f"<Venta {self.id} – {self.cantidad}x Producto {self.producto_id}>"


# ──────────────────────────── Asistencia ──────────────────────

class Asistencia(Base):
    """Registro de entrada/salida al gym via huella."""
    __tablename__ = "asistencias"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    usuario_id: Mapped[int] = mapped_column(Integer, ForeignKey("usuarios.id"), nullable=False)
    tipo: Mapped[str] = mapped_column(String(10), nullable=False, default="entrada")  # entrada / salida
    fecha_hora: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # ── Relaciones ──
    usuario: Mapped["Usuario"] = relationship("Usuario", back_populates="asistencias")

    def __repr__(self) -> str:
        return f"<Asistencia {self.id} – Usuario {self.usuario_id} ({self.tipo})>"


# ──────────────────── Movimientos Financieros ─────────────────

class MovimientoFinanciero(Base):
    """Registro unificado de ingresos y egresos del box."""
    __tablename__ = "movimientos_financieros"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    tipo: Mapped[TipoMovimiento] = mapped_column(SAEnum(TipoMovimiento), nullable=False)
    concepto: Mapped[str] = mapped_column(String(200), nullable=False)
    categoria: Mapped[str] = mapped_column(String(80), nullable=False)
    monto: Mapped[float] = mapped_column(Float, nullable=False)
    fecha: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)
    metodo_pago: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    usuario_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("usuarios.id"), nullable=True)
    notas: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    # fuente: manual | pago_membresia | pago_directo | venta_tienda
    fuente: Mapped[str] = mapped_column(String(50), nullable=False, default="manual")
    ref_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    created_by: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("usuarios.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    usuario: Mapped[Optional["Usuario"]] = relationship("Usuario", foreign_keys=[usuario_id])
    creador: Mapped[Optional["Usuario"]] = relationship("Usuario", foreign_keys=[created_by])

    def __repr__(self) -> str:
        return f"<MovimientoFinanciero {self.id} – {self.tipo.value} ${self.monto} ({self.categoria})>"


# ──────────────────────── Medidas de Salud ────────────────────

class MedidaSalud(Base):
    """Registro de medidas corporales del cliente."""
    __tablename__ = "medidas_salud"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    usuario_id: Mapped[int] = mapped_column(Integer, ForeignKey("usuarios.id"), nullable=False)
    fecha: Mapped[date] = mapped_column(Date, nullable=False)
    peso_kg: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    altura_cm: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    imc: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    cintura_cm: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    cuello_cm: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    cadera_cm: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    brazos_cm: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    notas: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    usuario: Mapped["Usuario"] = relationship("Usuario")

    def __repr__(self) -> str:
        return f"<MedidaSalud {self.id} – Usuario {self.usuario_id} IMC:{self.imc}>"


# ──────────────────────── Marcas RM ──────────────────────────

class MarcaRM(Base):
    """Registro de marca (récord personal) calculado con fórmulas de 1RM."""
    __tablename__ = "marcas_rm"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    usuario_id: Mapped[int] = mapped_column(Integer, ForeignKey("usuarios.id"), nullable=False)
    ejercicio: Mapped[str] = mapped_column(String(100), nullable=False)
    # peso/repeticiones/rm_calculado: aplican a barra y corporal_lastre.
    # Para 'reps' solo se usa repeticiones (peso/rm null). Para 'leger' todos null.
    peso: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    unidad: Mapped[str] = mapped_column(String(5), nullable=False, default="kg")  # kg | lbs
    repeticiones: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    rm_calculado: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    # corporal_lastre: peso adicional al cuerpo (chaleco, disco). null si solo peso corporal.
    peso_adicional: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    # leger: nivel + palier alcanzados.
    nivel: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    palier: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    # JSON array de todas las series de la sesión (solo barra/corporal_lastre)
    series: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    fecha: Mapped[date] = mapped_column(Date, nullable=False)
    notas: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    usuario: Mapped["Usuario"] = relationship("Usuario", back_populates="marcas_rm")

    def __repr__(self) -> str:
        return f"<MarcaRM {self.id} – {self.ejercicio} 1RM:{self.rm_calculado}{self.unidad}>"


# ──────────────────── Alertas de Membresía ────────────────────

class AlertaMembresia(Base):
    """Alerta generada automáticamente antes del vencimiento de una membresía."""
    __tablename__ = "alertas_membresia"
    __table_args__ = (
        UniqueConstraint("usuario_id", "fecha_vencimiento", "dias_anticipacion", name="uq_alerta"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    usuario_id: Mapped[int] = mapped_column(Integer, ForeignKey("usuarios.id"), nullable=False)
    fecha_vencimiento: Mapped[date] = mapped_column(Date, nullable=False)
    # Días que faltaban al CREAR la alerta. No se actualiza después, así que a
    # los dos días ya no refleja los días restantes reales: para cualquier
    # decisión (p. ej. si toca enviar) hay que recalcular contra
    # usuario.fecha_vencimiento, no leer esta columna.
    dias_anticipacion: Mapped[int] = mapped_column(Integer, nullable=False)
    enviada: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    fecha_creacion: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    fecha_enviada: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # ── Envío por WhatsApp Cloud API ──
    # No hay columna de "estado": es derivable de lo que ya está acá.
    #   enviada=True                        → enviado
    #   enviada=False y error_envio no nulo → falló
    #   enviada=False y error_envio nulo    → todavía no se intentó
    canal: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)  # "whatsapp_api" | "manual"
    wa_message_id: Mapped[Optional[str]] = mapped_column(String(80), nullable=True)
    error_envio: Mapped[Optional[str]] = mapped_column(String(300), nullable=True)
    intentos: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    usuario: Mapped["Usuario"] = relationship("Usuario")

    def __repr__(self) -> str:
        return f"<AlertaMembresia {self.id} – Usuario {self.usuario_id} -{self.dias_anticipacion}d>"


# ────────────────────── Métodos de Pago ──────────────────────

class MetodoPago(Base):
    """Cuenta bancaria/transferencia que el admin expone a los usuarios al adquirir un plan."""
    __tablename__ = "metodos_pago"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    banco: Mapped[str] = mapped_column(String(80), nullable=False)
    tipo_cuenta: Mapped[str] = mapped_column(String(40), nullable=False)  # ahorros, corriente, nequi, daviplata, etc.
    numero_cuenta: Mapped[str] = mapped_column(String(50), nullable=False)
    orden: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    activo: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    def __repr__(self) -> str:
        return f"<MetodoPago {self.id} – {self.banco} ({self.tipo_cuenta})>"

# El esquema lo crea `main.py` al arrancar (`Base.metadata.create_all(bind=engine)`),
# contra el engine de `database.py` — que es el único que sabe leer DATABASE_URL. Acá
# vivía un `init_db()` con un `if __name__ == "__main__"` que creaba las tablas contra
# un `sqlite:///crossfit_box.db` hardcodeado: nombre parecido pero DISTINTO del real
# (`crossfit.db`), así que correr `python models.py` dejaba una base vacía paralela que
# no era la que usa la app. No re-agregar un camino alternativo de creación de tablas.
