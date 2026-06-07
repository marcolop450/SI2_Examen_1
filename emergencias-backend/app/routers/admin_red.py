# ============================================================
# routers/admin_red.py
#
# CU16: Endpoints de Control para el Dueño de la Red SaaS (admin_red)
#
# ENDPOINTS:
#   GET /admin-red/dashboard-owner  → Datos reales de su cuota de talleres y suscripción
# ============================================================

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.usuario import Usuario, TipoRol
from app.models.saas import Plan, Suscripcion
from app.models.taller import Taller
from app.routers.auth import get_current_user
from app.routers.talleres import taller_a_schema

router = APIRouter(prefix="/admin-red", tags=["CU16 - Admin Red Dashboard"])

def require_admin_red(current_user: Usuario = Depends(get_current_user)):
    if current_user.rol != TipoRol.admin_red:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acceso denegado: se requiere rol admin_red"
        )
    return current_user

@router.get("/dashboard-owner")
def obtener_dashboard_owner(db: Session = Depends(get_db), current_user: Usuario = Depends(require_admin_red)):
    tenant_id = current_user.tenant_id
    if not tenant_id:
        raise HTTPException(status_code=400, detail="El administrador de red no tiene un tenant asignado.")

    suscripcion = db.query(Suscripcion).filter(Suscripcion.tenant_id == tenant_id).first()
    plan = db.query(Plan).filter(Plan.id_plan == suscripcion.plan_id).first() if suscripcion else None
    
    limite_talleres = plan.limite_talleres if plan and plan.limite_talleres else 9999
    nombre_plan = plan.nombre if plan else "Sin Plan"
    estado_suscripcion = suscripcion.estado if suscripcion else "inactiva"
    fecha_vencimiento = suscripcion.fecha_vencimiento if suscripcion else None

    # Contar y listar talleres
    talleres_bd = db.query(Taller).filter(Taller.tenant_id == tenant_id).all()
    talleres_creados = len(talleres_bd)

    # Actualizar la columna cantidad_actual_talleres
    if suscripcion and suscripcion.cantidad_actual_talleres != talleres_creados:
        suscripcion.cantidad_actual_talleres = talleres_creados
        db.commit()

    from sqlalchemy import func
    from app.models.pago import Pago

    talleres_list = []
    for t in talleres_bd:
        t_dict = taller_a_schema(t).model_dump()
        ingresos = db.query(func.coalesce(func.sum(Pago.monto_total_decimal), 0)).filter(
            Pago.dueño_taller_id == t.dueño_id
        ).scalar()
        t_dict["ingresos_totales"] = float(ingresos) if ingresos else 0.0
        talleres_list.append(t_dict)

    return {
        "nombre_red": current_user.tenant.nombre if current_user.tenant else "Mi Red",
        "subdominio": current_user.tenant.subdominio if current_user.tenant else "",
        "nombre_plan": nombre_plan,
        "estado_suscripcion": estado_suscripcion,
        "fecha_vencimiento": fecha_vencimiento,
        "limite_talleres": limite_talleres,
        "talleres_creados": talleres_creados,
        "talleres": talleres_list
    }
