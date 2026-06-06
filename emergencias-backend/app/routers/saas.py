# ============================================================
# routers/saas.py
#
# CU16: Endpoints de Control para el Administrador Global SaaS
#
# ENDPOINTS:
#   GET /admin/cockpit/resumen        → Resumen de todas las organizaciones
#   GET /admin/cockpit/planes-globales → Catálogo de planes disponibles
# ============================================================

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app.models.usuario import Usuario, TipoRol
from app.models.saas import Tenant, Plan, Suscripcion
from app.models.taller import Taller
from app.schemas.saas import TenantSummaryOut, PlanOut
from app.routers.auth import get_current_user

router = APIRouter(prefix="/admin/cockpit", tags=["CU16 - Admin Cockpit SaaS"])


# -------------------------------------------------------
# Función auxiliar: verifica que el usuario sea admin
# -------------------------------------------------------
def require_admin(current_user: Usuario = Depends(get_current_user)):
    if current_user.rol != TipoRol.admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acceso denegado: se requiere rol administrador"
        )
    return current_user


# -------------------------------------------------------
# GET /admin/cockpit/resumen
# PRIVADO — Solo Administrador Global
#
# Consulta relacional:
#   1. Itera sobre todos los Tenants registrados
#   2. Accede al Plan contratado vía Tenant.plan (relación eager)
#   3. Cuenta talleres reales vía query filtrada por tenant_id
#   4. Obtiene el estado de la suscripción más reciente
# -------------------------------------------------------
@router.get("/resumen", response_model=List[TenantSummaryOut])
def obtener_resumen_cockpit(db: Session = Depends(get_db), _: Usuario = Depends(require_admin)):
    tenants = db.query(Tenant).all()
    resultado = []

    for tenant in tenants:
        # Buscamos la suscripción activa para este tenant
        suscripcion = db.query(Suscripcion).filter(Suscripcion.tenant_id == tenant.id_tenant).first()
        
        # Obtenemos el plan desde la suscripción si existe
        plan = None
        if suscripcion:
            plan = db.query(Plan).filter(Plan.id_plan == suscripcion.plan_id).first()
        
        nombre_plan = plan.nombre if plan else "Sin plan"
        precio_plan = float(plan.precio) if plan else 0.0
        limite_talleres = plan.limite_talleres if plan else 5
        
        talleres_activos = db.query(Taller).filter(Taller.tenant_id == tenant.id_tenant).count()

        resultado.append(TenantSummaryOut(
            id_tenant=tenant.id_tenant,
            nombre=tenant.nombre,
            subdominio=tenant.subdominio,
            nombre_plan=nombre_plan,
            precio_plan=precio_plan,
            fecha_registro=tenant.fecha_creacion,
            talleres_activos=talleres_activos,
            limite_talleres=limite_talleres,
            estado=suscripcion.estado if suscripcion else "sin_suscripcion"
        ))
    return resultado


# -------------------------------------------------------
# GET /admin/cockpit/planes-globales
# PÚBLICO — Catálogo de planes SaaS disponibles
# -------------------------------------------------------
@router.get("/planes-globales", response_model=List[PlanOut])
def listar_todos_los_planes(
    db: Session = Depends(get_db)
):
    return db.query(Plan).all()
