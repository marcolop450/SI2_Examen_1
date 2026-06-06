# ============================================================
# schemas/notificacion.py
#
# CONTEXTO DEL PROYECTO:
#   Plataforma Inteligente de Emergencias Vehiculares
#
# CU15: Servicio de Notificaciones y Comunicación
from pydantic import BaseModel
from typing import Optional
from datetime import datetime


# Respuesta de una notificación individual
class NotificacionOut(BaseModel):
    id_notificacion:          int
    usuario_id:               Optional[int] = None   # <--- NUEVO (No rompe código existente)
    titulo:                   str
    mensaje:                  str
    leido_boolean:            bool
    fecha_creacion_timestamp: datetime

    class Config:
        from_attributes = True


# Para marcar notificación como leída
class MarcarLeida(BaseModel):
    leido_boolean: bool = True