# #Ciclo5 CU18 - Esquemas de Cotización mejorados para el móvil
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from decimal import Decimal

class CotizacionCreate(BaseModel):
    incidente_id: int
    precio_estimado: Decimal
    tiempo_estimado_min: int
    descripcion: Optional[str] = None
    tecnico_id: Optional[int] = None  # #Ciclo5 CU18 Técnico especializado que irá


class CotizacionResponse(BaseModel):
    id_cotizacion: int
    incidente_id: int
    taller_id: int
    nombre_taller: Optional[str] = None       # #Ciclo5 CU18 JOIN con talleres para el móvil
    precio_estimado: Decimal
    tiempo_estimado_min: int
    descripcion: Optional[str]
    estado: str
    fecha_envio: datetime
    fecha_respuesta: Optional[datetime] = None
    distancia_km: Optional[float] = None      # #Ciclo5 CU18 Calculado dinámicamente
    especialidad_tecnico: Optional[str] = None # #Ciclo5 CU18 Especialidad del técnico disponible

    class Config:
        from_attributes = True