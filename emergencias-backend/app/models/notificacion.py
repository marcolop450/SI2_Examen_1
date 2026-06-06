# ============================================================
# models/notificacion.py
#
# CONTEXTO DEL PROYECTO:
#   Plataforma Inteligente de Emergencias Vehiculares
#
# TABLA QUE REPRESENTA:
#   - notificaciones → Alertas enviadas a cada actor
#
# CU15: Servicio de Notificaciones y Comunicación
#   Se crea una notificación automáticamente cuando:
#   - Un incidente cambia de estado
#   - Un técnico es asignado
#   - Un taller acepta o rechaza una solicitud
#
# ACTORES: A1, A2, A3, A4 (todos reciben notificaciones)
# ============================================================

from sqlalchemy import Column, Integer, String, Text, Boolean, ForeignKey, TIMESTAMP, func
from sqlalchemy.orm import relationship
from app.database import Base



class Notificacion(Base):
    __tablename__ = "notificaciones"

    id_notificacion          = Column(Integer, primary_key=True, index=True)
    usuario_id               = Column(Integer, ForeignKey("usuarios.id_usuario"))
    titulo                   = Column(String(100))
    mensaje                  = Column(Text)
    leido_boolean            = Column(Boolean, default=False)    # False=no leída, True=leída
    fecha_creacion_timestamp = Column(TIMESTAMP, server_default=func.now())

    usuario = relationship("Usuario")