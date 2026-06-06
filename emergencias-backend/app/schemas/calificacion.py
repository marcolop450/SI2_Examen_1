# ============================================================
# Esquemas de Calificación Post-Servicio - Ciclo 5 - CU23
# Entrada y salida para el sistema de reseñas
# ============================================================
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class CalificacionCreate(BaseModel):
    """Datos para registrar una calificación del cliente - Ciclo 5 - CU23"""
    incidente_id: int
    puntuacion: int = Field(..., ge=1, le=5, description="Calificación de 1 a 5 estrellas")
    comentario: Optional[str] = None

class CalificacionOut(BaseModel):
    """Calificación completa con datos del cliente - Ciclo 5 - CU23"""
    id_calificacion: int
    incidente_id: int
    cliente_id: int
    taller_id: int
    tecnico_id: Optional[int] = None
    puntuacion: int
    comentario: Optional[str] = None
    fecha_calificacion: datetime
    cliente_nombre: Optional[str] = None  # Se llena via JOIN - Ciclo 5 - CU23

    class Config:
        from_attributes = True

class PromedioCalificacion(BaseModel):
    """Promedio y distribución de calificaciones de un taller - Ciclo 5 - CU23"""
    taller_id: int
    promedio: float = 0.0
    total_calificaciones: int = 0
    distribucion: dict = {}  # {"5": 10, "4": 5, "3": 2, "2": 1, "1": 0}
