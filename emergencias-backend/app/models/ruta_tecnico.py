# ============================================================
# MODELO — Tabla ruta_tecnico (ya creada en la BD)
# ============================================================
from sqlalchemy import Column, Integer, Numeric, TIMESTAMP, ForeignKey, func
from app.database import Base


class RutaTecnico(Base):
    __tablename__ = "ruta_tecnico"

    id_ruta         = Column(Integer, primary_key=True, index=True)
    incidente_id    = Column(Integer, ForeignKey("incidentes.id_incidente"), nullable=False)
    latitud         = Column(Numeric(12, 8), nullable=False)
    longitud        = Column(Numeric(12, 8), nullable=False)
    timestamp_punto = Column(TIMESTAMP, server_default=func.now())