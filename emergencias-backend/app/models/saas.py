# ============================================================
# models/saas.py
#
# Entidades Comerciales de la Arquitectura Multi-Tenant (3NF)
# ============================================================

from sqlalchemy import Column, Integer, String, Numeric, DateTime, ForeignKey, func
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
from app.database import Base


class Plan(Base):
    __tablename__ = "planes"

    id_plan           = Column(Integer, primary_key=True, index=True)
    nombre            = Column(String(100), nullable=False)
    descripcion       = Column(String(255), nullable=True)
    precio            = Column(Numeric(10, 2), nullable=False)
    limite_usuarios   = Column(Integer, nullable=True)
    limite_talleres   = Column(Integer, nullable=True)
    limite_incidentes = Column(Integer, nullable=True)

    # Relación uno-a-muchos con Tenants
    tenants           = relationship("Tenant", back_populates="plan")


class Tenant(Base):
    __tablename__ = "tenants"

    id_tenant      = Column(UUID(as_uuid=True), primary_key=True, index=True)
    plan_id        = Column(Integer, ForeignKey("planes.id_plan"), nullable=False)
    nombre         = Column(String(150), nullable=False)
    subdominio     = Column(String(100), unique=True, nullable=False)
    fecha_creacion = Column(DateTime(timezone=True), server_default=func.now())

    # Relaciones comerciales
    plan           = relationship("Plan", back_populates="tenants")
    suscripciones  = relationship("Suscripcion", back_populates="tenant", cascade="all, delete-orphan")

    # Relaciones operativas (resueltas por string diferido para evitar dependencias circulares)
    usuarios       = relationship("Usuario", back_populates="tenant")
    talleres       = relationship("Taller", back_populates="tenant")
    tecnicos       = relationship("Tecnico", back_populates="tenant")
    incidentes     = relationship("Incidente", back_populates="tenant")
    pagos          = relationship("Pago", back_populates="tenant")


class Suscripcion(Base):
    __tablename__ = "suscripciones"

    id_suscripcion    = Column(UUID(as_uuid=True), primary_key=True, index=True)
    tenant_id         = Column(UUID(as_uuid=True), ForeignKey("tenants.id_tenant", ondelete="CASCADE"), nullable=False)
    plan_id           = Column(Integer, ForeignKey("planes.id_plan"), nullable=False)
    fecha_inicio      = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    fecha_vencimiento = Column(DateTime(timezone=True), nullable=False)
    estado            = Column(String(50), default="activo", nullable=False)

    # Relaciones
    tenant            = relationship("Tenant", back_populates="suscripciones")
    plan              = relationship("Plan")
