# ============================================================
# models/saas.py
#
# Entidades Comerciales de la Arquitectura Multi-Tenant (3NF)
# ============================================================

from sqlalchemy import Column, Integer, String, Numeric, DateTime, ForeignKey, func
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
import uuid
from app.database import Base


class Plan(Base):
    __tablename__ = "planes"

    id_plan           = Column(Integer, primary_key=True, index=True)
    nombre            = Column(String(100), nullable=False)
    precio            = Column("precio_mensual", Numeric(10, 2), nullable=False)
    limite_talleres   = Column(Integer, nullable=True)


class Tenant(Base):
    __tablename__ = "tenants"

    id_tenant      = Column(UUID(as_uuid=True), primary_key=True, index=True, default=uuid.uuid4)
    nombre         = Column("nombre_comercial", String(150), nullable=False)
    subdominio     = Column("slug", String(100), unique=True, nullable=False)
    nit            = Column(String(50), unique=True, nullable=False)
    stripe_customer_id = Column(String(100), unique=True, nullable=True)
    fecha_creacion = Column("fecha_registro", DateTime(timezone=True), server_default=func.now())

    # Relaciones comerciales
    suscripciones  = relationship("Suscripcion", back_populates="tenant", cascade="all, delete-orphan")

    # Relaciones operativas (resueltas por string diferido para evitar dependencias circulares)
    usuarios       = relationship("Usuario", back_populates="tenant")
    talleres       = relationship("Taller", back_populates="tenant")
    tecnicos       = relationship("Tecnico", back_populates="tenant")
    incidentes     = relationship("Incidente", back_populates="tenant")
    pagos          = relationship("Pago", back_populates="tenant")


class Suscripcion(Base):
    __tablename__ = "suscripciones"

    id_suscripcion    = Column(UUID(as_uuid=True), primary_key=True, index=True, default=uuid.uuid4)
    tenant_id         = Column(UUID(as_uuid=True), ForeignKey("tenants.id_tenant", ondelete="CASCADE"), nullable=False)
    plan_id           = Column(Integer, ForeignKey("planes.id_plan"), nullable=False)
    fecha_inicio      = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    fecha_vencimiento = Column(DateTime(timezone=True), nullable=False)
    estado            = Column(String(50), default="activo", nullable=False)
    transaccion_pago_simulado = Column(String(100), nullable=True)
    cantidad_actual_talleres  = Column(Integer, default=0, nullable=False)

    # Relaciones
    tenant            = relationship("Tenant", back_populates="suscripciones")
    plan              = relationship("Plan")
