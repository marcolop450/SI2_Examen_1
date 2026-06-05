# ============================================================
# schemas/taller.py
#
# CU3: Gestión de Talleres
#
from pydantic import BaseModel, EmailStr
from typing import Optional
from decimal import Decimal
from uuid import UUID


# -------------------------------------------------------
# CU3 - REGISTRAR TALLER
# Body que el administrador envía para crear un taller.
# También crea el usuario asociado con rol='taller'.
# -------------------------------------------------------
class TallerCreate(BaseModel):
    # Datos del usuario dueño (se crea junto con el taller)
    nombre_dueno:      str
    email:             EmailStr
    password:          str
    telefono:          Optional[str] = None

    # Datos propios del taller
    nombre_taller:     str
    direccion:         Optional[str] = None
    nit:               Optional[str] = None

    # Coordenadas geográficas (usadas en CU11 - asignación inteligente)
    latitud_decimal:   Optional[Decimal] = None
    longitud_decimal:  Optional[Decimal] = None


# -------------------------------------------------------
# CU3 - ACTUALIZAR TALLER (parcial)
# Todos los campos son opcionales.
# Solo se actualizan los campos que vengan en el body.
# -------------------------------------------------------
class TallerUpdate(BaseModel):
    nombre_taller:     Optional[str]     = None
    direccion:         Optional[str]     = None
    nit:               Optional[str]     = None
    latitud_decimal:   Optional[Decimal] = None
    longitud_decimal:  Optional[Decimal] = None

    # También se puede actualizar info del dueño
    nombre_dueno:      Optional[str]     = None
    telefono:          Optional[str]     = None


# -------------------------------------------------------
# CU3 - RESPUESTA TALLER
# Lo que se devuelve al consultar un taller.
# Incluye datos del dueño embebidos para que Angular
# no tenga que hacer una segunda llamada.
# Nunca se incluye password_hash.
# -------------------------------------------------------
class TallerOut(BaseModel):
    id_taller:         int
    tenant_id:         Optional[UUID] = None
    dueño_id:          int

    # Datos del dueño (del usuario relacionado)
    nombre_dueno:      str
    email_dueno:       str
    telefono_dueno:    Optional[str] = None

    # Datos del taller
    nombre_taller:     str
    direccion:         Optional[str]     = None
    nit:               Optional[str]     = None
    latitud_decimal:   Optional[Decimal] = None
    longitud_decimal:  Optional[Decimal] = None

    class Config:
        from_attributes = True