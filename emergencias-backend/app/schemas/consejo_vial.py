# ============================================================
# Esquemas de Consejos de Seguridad Vial - Ciclo 5 - CU25
# CRUD de consejos para el asistente de seguridad
# ============================================================
from pydantic import BaseModel
from typing import Optional

class ConsejoCreate(BaseModel):
    """Crear un nuevo consejo de seguridad - Ciclo 5 - CU25"""
    categoria: str
    titulo: str
    contenido: str
    icono: str = '💡'

class ConsejoUpdate(BaseModel):
    """Actualizar un consejo existente (parcial) - Ciclo 5 - CU25"""
    categoria: Optional[str] = None
    titulo: Optional[str] = None
    contenido: Optional[str] = None
    icono: Optional[str] = None
    activo: Optional[bool] = None

class ConsejoOut(BaseModel):
    """Consejo de seguridad vial - Ciclo 5 - CU25"""
    id_consejo: int
    categoria: str
    titulo: str
    contenido: str
    icono: str
    activo: bool

    class Config:
        from_attributes = True
