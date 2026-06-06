from pydantic import BaseModel, Field
from decimal import Decimal
from datetime import datetime
from typing import Optional
from uuid import UUID
from app.models.pago import MetodoPago

class PagoCreate(BaseModel):
    incidente_id: int
    monto_total_decimal: Decimal = Field(..., gt=0, description="Costo total del rescate cobrado al cliente")
    metodo_enum: MetodoPago

class PagoOut(BaseModel):
    id_pago:                    int
    tenant_id:                  Optional[UUID] = None
    incidente_id:               int
    dueño_taller_id:            int
    monto_total_decimal:        Decimal
    comision_plataforma_decimal: Decimal
    metodo_enum:                MetodoPago
    estado_pago_enum:           str  # "completado" o "compensacion"
    fecha_pago_timestamp:       datetime

    class Config:
        from_attributes = True