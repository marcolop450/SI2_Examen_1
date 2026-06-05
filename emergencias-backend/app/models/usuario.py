# ============================================================
# models/usuario.py
from sqlalchemy import Column, Integer, String, Enum as SAEnum, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
from app.database import Base
import enum

class TipoRol(str, enum.Enum):
    cliente    = "cliente"
    taller     = "taller"
    tecnico    = "tecnico"
    admin      = "admin"


class Usuario(Base):
    __tablename__ = "usuarios"

    id_usuario    = Column(Integer, primary_key=True, index=True)
    tenant_id     = Column(UUID(as_uuid=True), ForeignKey("tenants.id_tenant", ondelete="CASCADE"), nullable=True)
    nombre        = Column(String(100), nullable=False)
    email         = Column(String(100), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    telefono      = Column(String(20))
    rol           = Column(SAEnum(TipoRol, name="tipo_rol"), default=TipoRol.cliente)

    tenant        = relationship("Tenant", back_populates="usuarios")