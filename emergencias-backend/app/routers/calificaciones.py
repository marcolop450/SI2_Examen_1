# ============================================================
# Router de Calificaciones Post-Servicio - Ciclo 5 - CU23
# CRUD de calificaciones: cliente califica, taller consulta
# ============================================================

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List

from app.database import get_db
from app.models.calificacion import Calificacion
from app.models.incidente import Incidente, EstadoIncidente
from app.models.taller import Taller
from app.models.usuario import Usuario, TipoRol
from app.routers.auth import get_current_user
from app.schemas.calificacion import CalificacionCreate, CalificacionOut, PromedioCalificacion
from app.utils.bitacora import registrar_evento  # Bitácora - Ciclo 5 - CU21

router = APIRouter(prefix="/calificaciones", tags=["CU23 - Calificaciones Post-Servicio"])


# ===================================================================
# CU23: CLIENTE REGISTRA CALIFICACIÓN - Ciclo 5 - CU23
# Solo para incidentes finalizados, una calificación por incidente
# ===================================================================
# Descripción: Cliente registra una calificación para un incidente finalizado
# Ciclo: Ciclo 5
# CU: CU23
@router.post("/", response_model=CalificacionOut, status_code=status.HTTP_201_CREATED)
def registrar_calificacion(
    datos: CalificacionCreate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    # Verificar que el incidente existe y está finalizado - Ciclo 5 - CU23
    incidente = db.query(Incidente).filter(
        Incidente.id_incidente == datos.incidente_id
    ).first()
    if not incidente:
        raise HTTPException(status_code=404, detail="Incidente no encontrado.")

    estados_validos = [EstadoIncidente.atendido, EstadoIncidente.finalizado]
    if incidente.estado_enum not in estados_validos:
        raise HTTPException(status_code=400, detail="Solo puedes calificar incidentes finalizados.")

    # Verificar que no exista calificación previa - Ciclo 5 - CU23
    existente = db.query(Calificacion).filter(
        Calificacion.incidente_id == datos.incidente_id
    ).first()
    if existente:
        raise HTTPException(status_code=400, detail="Este incidente ya fue calificado.")

    # Crear calificación con datos del incidente - Ciclo 5 - CU23
    nueva = Calificacion(
        incidente_id=datos.incidente_id,
        cliente_id=current_user.id_usuario,
        taller_id=incidente.taller_actual_id,
        tecnico_id=incidente.tecnico_id,
        puntuacion=datos.puntuacion,
        comentario=datos.comentario
    )
    db.add(nueva)

    # Registrar en bitácora - Ciclo 5 - CU21
    registrar_evento(
        db, datos.incidente_id,
        "CALIFICACION_REGISTRADA",
        f"Cliente calificó con {datos.puntuacion} estrellas. {datos.comentario or ''}".strip(),
        current_user.id_usuario
    )

    db.commit()
    db.refresh(nueva)

    return CalificacionOut(
        id_calificacion=nueva.id_calificacion,
        incidente_id=nueva.incidente_id,
        cliente_id=nueva.cliente_id,
        taller_id=nueva.taller_id,
        tecnico_id=nueva.tecnico_id,
        puntuacion=nueva.puntuacion,
        comentario=nueva.comentario,
        fecha_calificacion=nueva.fecha_calificacion,
        cliente_nombre=current_user.nombre
    )


# ===================================================================
# CU23: TALLER VE SUS CALIFICACIONES - Ciclo 5 - CU23
# ===================================================================
# Descripción: Taller ve todas las calificaciones que le han dejado
# Ciclo: Ciclo 5
# CU: CU23
@router.get("/mis-calificaciones", response_model=List[CalificacionOut])
def mis_calificaciones(
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    # Buscar el taller del usuario - Ciclo 5 - CU23
    taller = db.query(Taller).filter(
        Taller.dueño_id == current_user.id_usuario
    ).first()
    if not taller:
        return []

    registros = (
        db.query(Calificacion, Usuario.nombre)
        .outerjoin(Usuario, Calificacion.cliente_id == Usuario.id_usuario)
        .filter(Calificacion.taller_id == taller.id_taller)
        .order_by(Calificacion.fecha_calificacion.desc())
        .all()
    )

    return [
        CalificacionOut(
            id_calificacion=c.id_calificacion,
            incidente_id=c.incidente_id,
            cliente_id=c.cliente_id,
            taller_id=c.taller_id,
            tecnico_id=c.tecnico_id,
            puntuacion=c.puntuacion,
            comentario=c.comentario,
            fecha_calificacion=c.fecha_calificacion,
            cliente_nombre=nombre
        ) for c, nombre in registros
    ]


# ===================================================================
# CU23: PROMEDIO DE CALIFICACIONES DE UN TALLER - Ciclo 5 - CU23
# ===================================================================
# Descripción: Obtiene el promedio de calificaciones y distribución de estrellas de un taller
# Ciclo: Ciclo 5
# CU: CU23
@router.get("/promedio/{taller_id}", response_model=PromedioCalificacion)
def promedio_calificaciones(
    taller_id: int,
    db: Session = Depends(get_db)
):
    avg_val = db.query(func.avg(Calificacion.puntuacion)).filter(
        Calificacion.taller_id == taller_id
    ).scalar()

    total = db.query(Calificacion).filter(
        Calificacion.taller_id == taller_id
    ).count()

    # Distribución por puntuación (1-5) - Ciclo 5 - CU23
    distribucion = {}
    for i in range(1, 6):
        count = db.query(Calificacion).filter(
            Calificacion.taller_id == taller_id,
            Calificacion.puntuacion == i
        ).count()
        distribucion[str(i)] = count

    return PromedioCalificacion(
        taller_id=taller_id,
        promedio=round(float(avg_val), 1) if avg_val else 0.0,
        total_calificaciones=total,
        distribucion=distribucion
    )


# ===================================================================
# CU23: CALIFICACIONES DE UN TALLER ESPECÍFICO - Ciclo 5 - CU23
# ===================================================================
# Descripción: Obtiene el historial de calificaciones de un taller específico
# Ciclo: Ciclo 5
# CU: CU23
@router.get("/taller/{taller_id}", response_model=List[CalificacionOut])
def calificaciones_taller(
    taller_id: int,
    db: Session = Depends(get_db)
):
    registros = (
        db.query(Calificacion, Usuario.nombre)
        .outerjoin(Usuario, Calificacion.cliente_id == Usuario.id_usuario)
        .filter(Calificacion.taller_id == taller_id)
        .order_by(Calificacion.fecha_calificacion.desc())
        .all()
    )

    return [
        CalificacionOut(
            id_calificacion=c.id_calificacion,
            incidente_id=c.incidente_id,
            cliente_id=c.cliente_id,
            taller_id=c.taller_id,
            tecnico_id=c.tecnico_id,
            puntuacion=c.puntuacion,
            comentario=c.comentario,
            fecha_calificacion=c.fecha_calificacion,
            cliente_nombre=nombre
        ) for c, nombre in registros
    ]
