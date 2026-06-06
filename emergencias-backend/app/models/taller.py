# ============================================================
# models/taller.py
#
#
# CU3: Gestión de Talleres
# ============================================================
from sqlalchemy import Column, Integer, String, Text, DECIMAL, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
from app.database import Base


class Taller(Base):
    __tablename__ = "talleres"

    id_taller         = Column(Integer, primary_key=True, index=True)
    tenant_id         = Column(UUID(as_uuid=True), ForeignKey("tenants.id_tenant", ondelete="CASCADE"), nullable=True)
    dueño_id          = Column(Integer, ForeignKey("usuarios.id_usuario"), nullable=False)

    nombre            = Column(String(150), nullable=False)
    direccion         = Column(Text)
    nit               = Column(String(50))

    latitud_decimal   = Column(DECIMAL(10, 8))
    longitud_decimal  = Column(DECIMAL(10, 8))

    dueno             = relationship("Usuario", backref="talleres")
    tecnicos          = relationship("Tecnico", back_populates="taller", cascade="all, delete")
    tenant            = relationship("Tenant", back_populates="talleres")