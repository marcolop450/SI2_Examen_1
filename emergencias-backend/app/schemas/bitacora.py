# ============================================================
# Esquemas de la Bitácora de Trazabilidad - Ciclo 5 - CU21
# Schemas para la lectura de eventos de la bitácora
# ============================================================
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class BitacoraOut(BaseModel):
    """Evento de bitácora con nombre del usuario que lo ejecutó - Ciclo 5 - CU21"""
    id_bitacora: int
    incidente_id: int
    evento: str
    descripcion: Optional[str] = None
    usuario_id: Optional[int] = None
    usuario_nombre: Optional[str] = None  # JOIN con usuarios - Ciclo 5 - CU21
    timestamp: datetime

    class Config:
        from_attributes = True
