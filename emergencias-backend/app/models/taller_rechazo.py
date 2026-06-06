from sqlalchemy import Column, Integer, Text, TIMESTAMP, ForeignKey, func
from app.database import Base


class TallerRechazo(Base):
    __tablename__ = "talleres_rechazos"
    id           = Column(Integer, primary_key=True, index=True)
    incidente_id = Column(Integer, ForeignKey("incidentes.id_incidente", ondelete="CASCADE"))
    taller_id    = Column(Integer, ForeignKey("talleres.id_taller"))
    motivo       = Column(Text, nullable=True)
    timestamp    = Column(TIMESTAMP, server_default=func.now())