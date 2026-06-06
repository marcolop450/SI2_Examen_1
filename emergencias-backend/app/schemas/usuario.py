# ============================================================
# schemas/usuario.py
#
# CU1: LoginRequest, TokenResponse → Autenticación
# CU2: UsuarioCreate, UsuarioUpdate, UsuarioOut → CRUD Usuarios
#
# ACTORES DEL SISTEMA:
#   A1=Cliente, A2=Taller, A3=Tecnico, A4=Administrador
# ============================================================

from pydantic import BaseModel, EmailStr
from typing import Optional
from uuid import UUID
from app.models.usuario import TipoRol


# -------------------------------------------------------
# CU1 - LOGIN
# Datos que el usuario envía para iniciar sesión
# -------------------------------------------------------
class LoginRequest(BaseModel):
    email:    EmailStr
    password: str


# -------------------------------------------------------
# CU1 - RESPUESTA DEL LOGIN
# Lo que el sistema devuelve tras autenticación exitosa
# Incluye el token JWT, el rol y el nombre del usuario
# -------------------------------------------------------
class TokenResponse(BaseModel):
    access_token: str
    token_type:   str = "bearer"
    rol:          TipoRol
    nombre:       str
    # ⚡ NUEVOS CAMPOS:
    id_usuario:   int
    id_taller:    Optional[int] = None


# -------------------------------------------------------
# CU2 - REGISTRO PÚBLICO / CREAR USUARIO (Admin)
# Se usa tanto en el formulario de registro del login
# como en el CRUD interno del administrador
# El rol por defecto es 'cliente', el admin puede cambiarlo
# -------------------------------------------------------
class UsuarioCreate(BaseModel):
    nombre:   str
    email:    EmailStr
    password: str
    telefono: Optional[str] = None
    rol:      TipoRol = TipoRol.cliente


# -------------------------------------------------------
# CU2 - ACTUALIZAR USUARIO (Admin)
# Todos los campos son opcionales para permitir
# actualizaciones parciales (PATCH)
# -------------------------------------------------------
class UsuarioUpdate(BaseModel):
    nombre:   Optional[str]   = None
    email:    Optional[EmailStr] = None
    password: Optional[str]   = None
    telefono: Optional[str]   = None
    rol:      Optional[TipoRol] = None


# -------------------------------------------------------
# CU2 - RESPUESTA USUARIO
# Lo que se devuelve al consultar un usuario
# Nunca se incluye la contraseña en la respuesta
# -------------------------------------------------------
class UsuarioOut(BaseModel):
    id_usuario: int
    tenant_id:  Optional[UUID] = None
    nombre:     str
    email:      str
    telefono:   Optional[str] = None
    rol:        TipoRol

    class Config:
        from_attributes = True