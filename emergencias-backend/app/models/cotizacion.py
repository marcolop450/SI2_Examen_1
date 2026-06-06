from sqlalchemy import Column, Integer, ForeignKey, DECIMAL, Text, String, TIMESTAMP
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base

class Cotizacion(Base):
    __tablename__ = "cotizaciones"

    id_cotizacion       = Column(Integer, primary_key=True, index=True)
    incidente_id        = Column(Integer, ForeignKey("incidentes.id_incidente"), nullable=False)
    taller_id           = Column(Integer, ForeignKey("talleres.id_taller"), nullable=False)
    tecnico_id          = Column(Integer, ForeignKey("tecnicos.id_tecnico"), nullable=True)  # #Ciclo5 CU18 Técnico especializado asignado
    precio_estimado     = Column(DECIMAL(10, 2), nullable=False)
    tiempo_estimado_min = Column(Integer, nullable=False)
    descripcion         = Column(Text, nullable=True)
    estado              = Column(String(50), default="pendiente")
    # estados posibles: pendiente, aceptada, rechazada, expirada
    fecha_envio         = Column(TIMESTAMP, server_default=func.now())
    fecha_respuesta     = Column(TIMESTAMP, nullable=True)

    incidente = relationship("Incidente", backref="cotizaciones")
    taller    = relationship("Taller", backref="cotizaciones")
    tecnico   = relationship("Tecnico", backref="cotizaciones")  # #Ciclo5 CU18