# ============================================================
# Modelo de Calificaciones Post-Servicio - Ciclo 5 - CU23
# Permite al cliente calificar el servicio recibido (1-5 estrellas)
# ============================================================
from sqlalchemy import Column, Integer, Text, TIMESTAMP, ForeignKey, CheckConstraint
from sqlalchemy.sql import func
from app.database import Base

class Calificacion(Base):
    __tablename__ = "calificaciones"

    id_calificacion    = Column(Integer, primary_key=True, index=True)
    incidente_id       = Column(Integer, ForeignKey("incidentes.id_incidente"), unique=True, nullable=False)  # Un incidente = una calificación - Ciclo 5 - CU23
    cliente_id         = Column(Integer, ForeignKey("usuarios.id_usuario"), nullable=False)
    taller_id          = Column(Integer, ForeignKey("talleres.id_taller"), nullable=False)
    tecnico_id         = Column(Integer, ForeignKey("tecnicos.id_tecnico"), nullable=True)
    puntuacion         = Column(Integer, nullable=False)  # 1-5 estrellas - Ciclo 5 - CU23
    comentario         = Column(Text, nullable=True)
    fecha_calificacion = Column(TIMESTAMP, server_default=func.now())

    __table_args__ = (
        CheckConstraint('puntuacion >= 1 AND puntuacion <= 5', name='check_puntuacion_rango'),
    )
