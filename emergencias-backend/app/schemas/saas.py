# ============================================================
# schemas/saas.py
#
# Esquemas Pydantic para el Catálogo Comercial Multi-Tenant (3NF)
# ============================================================

from pydantic import BaseModel, EmailStr, ConfigDict
from typing import Optional
from decimal import Decimal
from datetime import datetime
from uuid import UUID

# -----------------------------------------------------------
# ESQUEMAS DE PLANES (planes)
# -----------------------------------------------------------
class PlanBase(BaseModel):
    nombre:            str
    descripcion:       Optional[str] = None
    precio:            Decimal
    limite_usuarios:   Optional[int] = None
    limite_talleres:   Optional[int] = None
    limite_incidentes: Optional[int] = None

class PlanCreate(PlanBase):
    pass

class PlanOut(PlanBase):
    id_plan: int

    model_config = ConfigDict(from_attributes=True)


# -----------------------------------------------------------
# ESQUEMAS DE TENANTS (tenants)
# -----------------------------------------------------------
class TenantBase(BaseModel):
    nombre:     str
    subdominio: str
    plan_id:    int

class TenantCreate(TenantBase):
    id_tenant: Optional[UUID] = None

class TenantOut(TenantBase):
    id_tenant:      UUID
    fecha_registro: datetime  # Simetría 1:1 con la BD física en Supabase

    model_config = ConfigDict(from_attributes=True)


# -----------------------------------------------------------
# ESQUEMAS DE SUSCRIPCIONES (suscripciones)
# -----------------------------------------------------------
class SuscripcionBase(BaseModel):
    tenant_id:         UUID
    plan_id:           int
    fecha_vencimiento: datetime
    estado:            str = "activo"

class SuscripcionCreate(SuscripcionBase):
    pass

class SuscripcionOut(SuscripcionBase):
    id_suscripcion: UUID
    fecha_inicio:   datetime

    model_config = ConfigDict(from_attributes=True)


# -----------------------------------------------------------
# CONTRATO COMPUESTO B2B: Registro de Organizaciones
# -----------------------------------------------------------
class TenantRegisterTenant(BaseModel):
    nombre_comercial: str
    subdominio:       str
    plan_id:          int = 1  # Por defecto Plan Básico

class TenantRegisterUser(BaseModel):
    nombre:   str
    email:    EmailStr
    password: str  # Texto plano para ser hasheado por el controlador
    telefono: Optional[str] = None

class TenantRegisterRequest(BaseModel):
    tenant:  TenantRegisterTenant
    usuario: TenantRegisterUser


# -----------------------------------------------------------
# CU16: DTO de Resumen para el Admin Cockpit
# Agregación relacional: Tenant + Plan + COUNT(Talleres) + Suscripción
# -----------------------------------------------------------
class TenantSummaryOut(BaseModel):
    id_tenant:        UUID
    nombre:           str
    subdominio:       str
    nombre_plan:      str
    precio_plan:      float
    fecha_registro:   datetime
    talleres_activos: int
    limite_talleres:  int
    estado:           str          # "activo" | "suspendido" | "sin_suscripcion"

    model_config = ConfigDict(from_attributes=True)

