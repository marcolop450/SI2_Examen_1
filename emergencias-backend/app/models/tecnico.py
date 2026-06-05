# ============================================================
# models/tecnico.py
#
# CU6: Administrar Staff Técnico (CRUD)
#   Actor: A2 (Taller)
#   El taller registra, edita y gestiona disponibilidad
#   de sus técnicos desde la app web Angular
# ============================================================

from sqlalchemy import Column, Integer, String, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
from app.database import Base

class Tecnico(Base):
    __tablename__ = "tecnicos"

    id_tecnico         = Column(Integer, primary_key=True, index=True)
    tenant_id          = Column(UUID(as_uuid=True), ForeignKey("tenants.id_tenant", ondelete="CASCADE"), nullable=True)
    taller_id          = Column(Integer, ForeignKey("talleres.id_taller", ondelete="CASCADE"))
    
    usuario_id         = Column(Integer, ForeignKey("usuarios.id_usuario", ondelete="CASCADE"), nullable=False)
    nombre             = Column(String(100), nullable=False) 
    
    especialidad       = Column(String(100), nullable=True)
    disponible_boolean = Column(Boolean, default=True)
    taller  = relationship("Taller", back_populates="tecnicos")
    usuario = relationship("Usuario")
    tenant  = relationship("Tenant", back_populates="tecnicos")