# ============================================================
# routers/notificaciones.py
# CU15: Servicio de Notificaciones y Comunicación
#
# ENDPOINTS:
#   GET   /notificaciones/mis-notificaciones → Ver mis alertas
#   PATCH /notificaciones/{id}/leer          → Marcar como leída
#   GET   /notificaciones/no-leidas          → Contar no leídas (para badge)
#
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app.models.notificacion import Notificacion
from app.models.usuario import Usuario
from app.schemas.notificacion import NotificacionOut, MarcarLeida
from app.routers.auth import get_current_user

router = APIRouter(prefix="/notificaciones", tags=["CU15 - Notificaciones"])


# -------------------------------------------------------
# Función interna reutilizable
# La llaman otros routers (incidentes, etc.) para crear
# notificaciones automáticas sin pasar por HTTP
# -------------------------------------------------------
def crear_notificacion_interna(db: Session, usuario_id: int, titulo: str, mensaje: str):
    notif = Notificacion(
        usuario_id = usuario_id,
        titulo     = titulo,
        mensaje    = mensaje
    )
    db.add(notif)
    db.commit()      # ← AGREGAR
    db.refresh(notif)  # ← AGREGAR
    return notif

# -------------------------------------------------------
# GET /notificaciones/mis-notificaciones
# Devuelve todas las notificaciones del usuario autenticado
# Ordenadas de más reciente a más antigua
# -------------------------------------------------------
@router.get("/mis-notificaciones", response_model=List[NotificacionOut])
def mis_notificaciones(
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    return db.query(Notificacion).filter(
        Notificacion.usuario_id == current_user.id_usuario
    ).order_by(Notificacion.fecha_creacion_timestamp.desc()).all()


# -------------------------------------------------------
# GET /notificaciones/no-leidas
# Devuelve el conteo de notificaciones no leídas
# El frontend Angular lo usa para mostrar el badge en navbar
# -------------------------------------------------------
@router.get("/no-leidas")
def contar_no_leidas(
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    total = db.query(Notificacion).filter(
        Notificacion.usuario_id  == current_user.id_usuario,
        Notificacion.leido_boolean == False
    ).count()
    return {"total_no_leidas": total}


# -------------------------------------------------------
# PATCH /notificaciones/{id}/leer
# Marcar una notificación como leída
# El frontend llama esto cuando el usuario abre la alerta
# -------------------------------------------------------
@router.patch("/{id_notificacion}/leer", response_model=NotificacionOut)
def marcar_leida(
    id_notificacion: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    notif = db.query(Notificacion).filter(
        Notificacion.id_notificacion == id_notificacion,
        Notificacion.usuario_id      == current_user.id_usuario
    ).first()

    if not notif:
        raise HTTPException(status_code=404, detail="Notificación no encontrada")

    notif.leido_boolean = True
    db.commit()
    db.refresh(notif)
    return notif


# -------------------------------------------------------
# PATCH /notificaciones/leer-todas
# Marcar TODAS las notificaciones del usuario como leídas
# El móvil llama esto cuando el usuario abre el panel de alertas
# -------------------------------------------------------
@router.patch("/leer-todas")
def marcar_todas_leidas(
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    # #Ciclo5 CU15 - Marcar todas como leídas de una vez
    db.query(Notificacion).filter(
        Notificacion.usuario_id == current_user.id_usuario,
        Notificacion.leido_boolean == False
    ).update({"leido_boolean": True})
    db.commit()
    return {"mensaje": "Todas las notificaciones marcadas como leídas."}


# -------------------------------------------------------
# DELETE /notificaciones/{id}
# Eliminar una notificación individual
# -------------------------------------------------------
@router.delete("/{id_notificacion}", status_code=204)
def eliminar_notificacion(
    id_notificacion: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    notif = db.query(Notificacion).filter(
        Notificacion.id_notificacion == id_notificacion,
        Notificacion.usuario_id == current_user.id_usuario
    ).first()
    if not notif:
        raise HTTPException(status_code=404, detail="Notificación no encontrada")
    db.delete(notif)
    db.commit()