# ============================================================
# Router de Bitácora de Trazabilidad - Ciclo 5 - CU21
# Endpoint para leer la línea de tiempo completa de un incidente
# ============================================================

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app.models.bitacora import BitacoraIncidente
from app.models.incidente import Incidente
from app.models.taller import Taller
from app.models.usuario import Usuario, TipoRol
from app.routers.auth import get_current_user
from app.schemas.bitacora import BitacoraOut

router = APIRouter(prefix="/bitacora", tags=["CU21 - Bitácora de Trazabilidad"])


# ===================================================================
# CU21: OBTENER BITÁCORA COMPLETA DE UN INCIDENTE - Ciclo 5 - CU21
# Devuelve la línea de tiempo con todos los eventos cronológicos
# ===================================================================
# Descripción: Obtener la bitácora completa de un incidente
# Ciclo: Ciclo 5
# CU: CU21
@router.get("/{incidente_id}", response_model=List[BitacoraOut])
def obtener_bitacora(
    incidente_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    # Verificar que el incidente existe - Ciclo 5 - CU21
    incidente = db.query(Incidente).filter(
        Incidente.id_incidente == incidente_id
    ).first()
    if not incidente:
        raise HTTPException(status_code=404, detail="Incidente no encontrado.")

    # Control de acceso: admin ve todo, taller solo sus incidentes - Ciclo 5 - CU21
    if current_user.rol != TipoRol.admin:
        taller = db.query(Taller).filter(
            Taller.dueño_id == current_user.id_usuario
        ).first()
        if not taller or incidente.taller_actual_id != taller.id_taller:
            raise HTTPException(status_code=403, detail="No tienes acceso a la bitácora de este incidente.")

    # Query con LEFT JOIN para obtener nombre del usuario - Ciclo 5 - CU21
    registros = (
        db.query(BitacoraIncidente, Usuario.nombre)
        .outerjoin(Usuario, BitacoraIncidente.usuario_id == Usuario.id_usuario)
        .filter(BitacoraIncidente.incidente_id == incidente_id)
        .order_by(BitacoraIncidente.timestamp.asc())
        .all()
    )

    # Construir respuesta con usuario_nombre del JOIN - Ciclo 5 - CU21
    resultado = []
    for bitacora, nombre_usuario in registros:
        resultado.append(BitacoraOut(
            id_bitacora=bitacora.id_bitacora,
            incidente_id=bitacora.incidente_id,
            evento=bitacora.evento,
            descripcion=bitacora.descripcion,
            usuario_id=bitacora.usuario_id,
            usuario_nombre=nombre_usuario,
            timestamp=bitacora.timestamp
        ))

    return resultado
