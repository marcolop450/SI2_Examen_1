# ============================================================
# schemas/tecnico.py
#

# CU6: Administrar Staff Técnico (CRUD)
#   Actor: A2 (Taller)
#
from pydantic import BaseModel, EmailStr
from typing import Optional
from uuid import UUID

class TecnicoCreate(BaseModel):
    taller_id: int
    nombre: str         
    email: EmailStr     
    password: str       
    telefono: Optional[str] = None
    especialidad: Optional[str] = None
    disponible_boolean: bool = True

class TecnicoUpdate(BaseModel):
    nombre: Optional[str] = None
    especialidad: Optional[str] = None
    disponible_boolean: Optional[bool] = None

class TecnicoPartial(BaseModel):
    nombre: Optional[str] = None
    especialidad: Optional[str] = None
    disponible_boolean: Optional[bool] = None

    class Config:
        from_attributes = True

class TecnicoOut(BaseModel):
    id_tecnico: int
    tenant_id: Optional[UUID] = None
    taller_id: int
    usuario_id: int
    nombre: str        
    especialidad: Optional[str] = None
    disponible_boolean: bool

    class Config:
        from_attributes = True