# ============================================================
# Modelo de Consejos de Seguridad Vial - Ciclo 5 - CU25
# Consejos personalizados para el cliente mientras espera auxilio
# ============================================================
from sqlalchemy import Column, Integer, String, Text, Boolean
from app.database import Base

class ConsejoSeguridad(Base):
    __tablename__ = "consejos_seguridad_vial"

    id_consejo = Column(Integer, primary_key=True, index=True)
    categoria  = Column(String(50), nullable=False)   # llanta, motor, bateria, choque, general, clima - Ciclo 5 - CU25
    titulo     = Column(String(200), nullable=False)
    contenido  = Column(Text, nullable=False)
    icono      = Column(String(10), default='💡')      # Emoji representativo - Ciclo 5 - CU25
    activo     = Column(Boolean, default=True)
