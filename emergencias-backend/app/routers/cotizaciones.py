# #Ciclo5 CU18 - Router de Cotizaciones mejorado para flujo cliente-escoge-taller
# Permite a talleres enviar cotizaciones y al cliente escoger la mejor opción
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime
from typing import List
from app.database import get_db
from app.models.cotizacion import Cotizacion
from app.models.incidente import Incidente, EstadoIncidente, HistorialEstado
from app.models.taller import Taller
from app.models.tecnico import Tecnico
from app.schemas.cotizacion import CotizacionCreate, CotizacionResponse
from app.routers.websocket_incidente import gestor  # Para broadcast en tiempo real
from app.routers.auth import get_current_user
from app.models.usuario import Usuario
from app.utils.bitacora import registrar_evento  # CU21 — bitácora
import math

router = APIRouter(prefix="/cotizaciones", tags=["CU18 - Cotizaciones"])


# Descripción: Calcula distancia en km entre dos coordenadas
# Ciclo: Ciclo 4
# CU: CU18
def _calcular_distancia(lat1, lon1, lat2, lon2) -> float:
    """Calcula distancia en km entre dos coordenadas - #Ciclo5 CU18"""
    if not all([lat1, lon1, lat2, lon2]):
        return 0.0
    R = 6371.0
    dlat = math.radians(float(lat2) - float(lat1))
    dlon = math.radians(float(lon2) - float(lon1))
    a = math.sin(dlat/2)**2 + math.cos(math.radians(float(lat1))) * \
        math.cos(math.radians(float(lat2))) * math.sin(dlon/2)**2
    return round(R * (2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))), 2)


# Descripción: Agrega nombre_taller, distancia y especialidad al response
# Ciclo: Ciclo 4
# CU: CU18
def _enriquecer_cotizacion(cot: Cotizacion, db: Session, incidente: Incidente = None) -> dict:
    """#Ciclo5 CU18 - Agrega nombre_taller, distancia y especialidad al response"""
    taller = db.query(Taller).filter(Taller.id_taller == cot.taller_id).first()
    nombre_taller = taller.nombre if taller else None

    # Distancia del taller a la emergencia
    distancia_km = None
    if taller and incidente:
        distancia_km = _calcular_distancia(
            incidente.latitud_emergencia, incidente.longitud_emergencia,
            taller.latitud_decimal, taller.longitud_decimal
        )

    # Especialidad del primer técnico disponible del taller
    tecnico = db.query(Tecnico).filter(
        Tecnico.taller_id == cot.taller_id,
        Tecnico.disponible_boolean == True
    ).first()
    especialidad = tecnico.especialidad if tecnico else None

    return {
        "id_cotizacion": cot.id_cotizacion,
        "incidente_id": cot.incidente_id,
        "taller_id": cot.taller_id,
        "nombre_taller": nombre_taller,
        "precio_estimado": cot.precio_estimado,
        "tiempo_estimado_min": cot.tiempo_estimado_min,
        "descripcion": cot.descripcion,
        "estado": cot.estado,
        "fecha_envio": cot.fecha_envio,
        "fecha_respuesta": cot.fecha_respuesta,
        "distancia_km": distancia_km,
        "especialidad_tecnico": especialidad,
    }


# ===================================================================
# CU18: TALLER ENVÍA UNA COTIZACIÓN AL INCIDENTE
# #Ciclo5 - Flujo nuevo: talleres compiten con cotizaciones
# ===================================================================
# Descripción: Taller envía una cotización al incidente
# Ciclo: Ciclo 4
# CU: CU18
@router.post("/", response_model=CotizacionResponse, status_code=status.HTTP_201_CREATED)
async def crear_cotizacion(
    cotizacion: CotizacionCreate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    # Verificar que el incidente existe y aún acepta cotizaciones - #Ciclo5 CU18
    incidente = db.query(Incidente).filter(Incidente.id_incidente == cotizacion.incidente_id).first()
    if not incidente:
        raise HTTPException(status_code=404, detail="Incidente no encontrado.")

    estados_validos = [EstadoIncidente.buscando_taller, EstadoIncidente.pendiente]
    if incidente.estado_enum not in estados_validos:
        raise HTTPException(
            status_code=400,
            detail=f"El incidente ya no acepta cotizaciones (estado: {incidente.estado_enum.value})."
        )

    # #Ciclo5 CU18 - El taller_id se obtiene del usuario autenticado
    taller = db.query(Taller).filter(Taller.dueño_id == current_user.id_usuario).first()
    if not taller:
        raise HTTPException(status_code=403, detail="El usuario no tiene un taller asociado.")

    # Evitar que el mismo taller envíe dos cotizaciones al mismo incidente
    ya_cotizo = db.query(Cotizacion).filter(
        Cotizacion.incidente_id == cotizacion.incidente_id,
        Cotizacion.taller_id == taller.id_taller,
        Cotizacion.estado == "pendiente"
    ).first()
    if ya_cotizo:
        raise HTTPException(status_code=400, detail="Ya enviaste una cotización para esta emergencia.")

    # #Ciclo5 CU18 - Validar técnico si se especificó
    if cotizacion.tecnico_id:
        tecnico_cotizacion = db.query(Tecnico).filter(
            Tecnico.id_tecnico == cotizacion.tecnico_id,
            Tecnico.taller_id == taller.id_taller
        ).first()
        if not tecnico_cotizacion:
            raise HTTPException(status_code=400, detail="El técnico no pertenece a tu taller.")
        if not tecnico_cotizacion.disponible_boolean:
            raise HTTPException(status_code=400, detail="El técnico seleccionado no está disponible.")

    nueva_cotizacion = Cotizacion(
        incidente_id=cotizacion.incidente_id,
        taller_id=taller.id_taller,
        tecnico_id=cotizacion.tecnico_id,   # #Ciclo5 CU18 Guardar técnico asignado
        precio_estimado=cotizacion.precio_estimado,
        tiempo_estimado_min=cotizacion.tiempo_estimado_min,
        descripcion=cotizacion.descripcion
    )
    db.add(nueva_cotizacion)

    # CU21 — registrar envío de cotización en bitácora
    registrar_evento(
        db, cotizacion.incidente_id,
        "COTIZACION_ENVIADA",
        f"Taller '{taller.nombre}' envió cotización: {cotizacion.precio_estimado} Bs., {cotizacion.tiempo_estimado_min} min.",
        current_user.id_usuario
    )

    db.commit()
    db.refresh(nueva_cotizacion)

    # Notificar al cliente por WebSocket que llegó una nueva cotización - #Ciclo5 CU18
    await gestor.broadcast(cotizacion.incidente_id, {
        "tipo": "nueva_cotizacion",
        "taller": taller.nombre,
        "precio": str(cotizacion.precio_estimado),
        "tiempo_min": cotizacion.tiempo_estimado_min,
        "timestamp": datetime.now().isoformat()
    })

    return _enriquecer_cotizacion(nueva_cotizacion, db, incidente)


# ===================================================================
# CU18: CLIENTE VE TODAS LAS COTIZACIONES DE SU INCIDENTE
# #Ciclo5 - Accesible para cliente dueño del incidente
# ===================================================================
# Descripción: Cliente ve todas las cotizaciones de su incidente
# Ciclo: Ciclo 4
# CU: CU18
@router.get("/{incidente_id}", response_model=List[CotizacionResponse])
async def obtener_cotizaciones(
    incidente_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    incidente = db.query(Incidente).filter(
        Incidente.id_incidente == incidente_id
    ).first()
    if not incidente:
        raise HTTPException(status_code=404, detail="Incidente no encontrado.")

    # #Ciclo5 CU18 - Permitir acceso al cliente dueño, taller asociado o admin
    es_cliente_dueno = incidente.cliente_id == current_user.id_usuario
    es_admin = current_user.rol.value == "admin"
    taller_usuario = db.query(Taller).filter(
        Taller.dueño_id == current_user.id_usuario
    ).first()

    if not es_cliente_dueno and not es_admin and not taller_usuario:
        raise HTTPException(status_code=403, detail="No tienes permiso para ver estas cotizaciones.")

    cotizaciones = db.query(Cotizacion).filter(
        Cotizacion.incidente_id == incidente_id
    ).order_by(Cotizacion.precio_estimado.asc()).all()  # Ordenar por precio ASC

    return [_enriquecer_cotizacion(c, db, incidente) for c in cotizaciones]


# ===================================================================
# CU18: CLIENTE ACEPTA UNA COTIZACIÓN
# #Ciclo5 - Asigna taller y notifica por WS
# ===================================================================
@router.put("/{id}/aceptar")
async def aceptar_cotizacion(
    id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    cotizacion = db.query(Cotizacion).filter(Cotizacion.id_cotizacion == id).first()
    if not cotizacion:
        raise HTTPException(status_code=404, detail="Cotización no encontrada.")

    if cotizacion.estado != "pendiente":
        raise HTTPException(status_code=400, detail="Esta cotización ya fue procesada.")

    incidente = db.query(Incidente).filter(Incidente.id_incidente == cotizacion.incidente_id).first()
    if not incidente:
        raise HTTPException(status_code=404, detail="Incidente no encontrado.")

    # Solo el cliente dueño puede aceptar - #Ciclo5 CU18
    if incidente.cliente_id != current_user.id_usuario:
        raise HTTPException(status_code=403, detail="Solo el cliente puede aceptar cotizaciones.")

    # 1. Marcar esta cotización como aceptada
    cotizacion.estado = "aceptada"
    cotizacion.fecha_respuesta = datetime.utcnow()

    # 2. Expirar todas las demás cotizaciones del mismo incidente
    db.query(Cotizacion).filter(
        Cotizacion.incidente_id == cotizacion.incidente_id,
        Cotizacion.id_cotizacion != id
    ).update({"estado": "expirada"})

    # 3. Actualizar el incidente: estado, taller y técnico asignado - #Ciclo5 CU18
    incidente.estado_enum = EstadoIncidente.taller_asignado
    incidente.taller_actual_id = cotizacion.taller_id

    # #Ciclo5 CU18 - Asignar técnico al incidente y marcarlo como NO disponible
    if cotizacion.tecnico_id:
        incidente.tecnico_id = cotizacion.tecnico_id
        tecnico_asignado = db.query(Tecnico).filter(
            Tecnico.id_tecnico == cotizacion.tecnico_id
        ).first()
        if tecnico_asignado:
            tecnico_asignado.disponible_boolean = False  # Técnico ocupado

    # 4. Registrar historial de estado
    db.add(HistorialEstado(
        incidente_id=incidente.id_incidente,
        estado_enum=EstadoIncidente.taller_asignado,
        comentario_texto=f"Cliente aceptó cotización del taller ID {cotizacion.taller_id}. Precio: {cotizacion.precio_estimado} Bs."
    ))

    # 5. Notificar al taller ganador
    taller = db.query(Taller).filter(Taller.id_taller == cotizacion.taller_id).first()
    from app.routers.notificaciones import crear_notificacion_interna
    if taller:
        crear_notificacion_interna(
            db, taller.dueño_id,
            "✅ ¡Cotización Aceptada!",
            f"El cliente aceptó tu cotización de {cotizacion.precio_estimado} Bs. Prepara al técnico."
        )
        crear_notificacion_interna(
            db, incidente.cliente_id,
            "🔧 Taller Asignado",
            f"El taller '{taller.nombre}' atenderá tu emergencia. Tiempo estimado: {cotizacion.tiempo_estimado_min} min."
        )

    # 6. CU21 — registrar cotización aceptada en bitácora
    registrar_evento(
        db, cotizacion.incidente_id,
        "COTIZACION_ACEPTADA",
        f"Cliente aceptó cotización del taller ID {cotizacion.taller_id}. "
        f"Precio: {cotizacion.precio_estimado} Bs. Tiempo: {cotizacion.tiempo_estimado_min} min.",
        current_user.id_usuario
    )

    db.commit()

    # 7. Broadcast WebSocket — notificar a todos en la sala - #Ciclo5 CU18
    # El técnico móvil escucha este mensaje para saber que fue asignado
    tecnico_nombre = None
    if cotizacion.tecnico_id:
        tec = db.query(Tecnico).filter(Tecnico.id_tecnico == cotizacion.tecnico_id).first()
        if tec:
            tecnico_nombre = tec.nombre

    await gestor.broadcast(incidente.id_incidente, {
        "tipo": "cambio_estado",
        "estado": "taller_asignado",
        "mensaje": f"El cliente aceptó la cotización. Taller '{taller.nombre if taller else id}' asignado.",
        "taller_id": cotizacion.taller_id,
        "tecnico_id": cotizacion.tecnico_id,           # #Ciclo5 CU18 - Para el móvil del técnico
        "nombre_tecnico": tecnico_nombre,              # #Ciclo5 CU18 - Nombre para mostrar
        "precio_aceptado": str(cotizacion.precio_estimado),
        "tiempo_estimado_min": cotizacion.tiempo_estimado_min,
        "timestamp": datetime.now().isoformat()
    })

    return {
        "mensaje": "Cotización aceptada. Taller asignado al incidente.",
        "taller_id": cotizacion.taller_id,
        "nombre_taller": taller.nombre if taller else None,
        "precio": str(cotizacion.precio_estimado),
        "tiempo_estimado_min": cotizacion.tiempo_estimado_min
    }


# ===================================================================
# CU18: CLIENTE RECHAZA UNA COTIZACIÓN
# ===================================================================
# Descripción: Cliente rechaza una cotización
# Ciclo: Ciclo 4
# CU: CU18
@router.put("/{id}/rechazar")
async def rechazar_cotizacion(
    id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    cotizacion = db.query(Cotizacion).filter(Cotizacion.id_cotizacion == id).first()
    if not cotizacion:
        raise HTTPException(status_code=404, detail="Cotización no encontrada.")

    if cotizacion.estado != "pendiente":
        raise HTTPException(status_code=400, detail="Esta cotización ya fue procesada.")

    cotizacion.estado = "rechazada"
    cotizacion.fecha_respuesta = datetime.utcnow()

    # CU21 — registrar rechazo en bitácora
    registrar_evento(
        db, cotizacion.incidente_id,
        "COTIZACION_RECHAZADA",
        f"El cliente rechazó la cotización del taller ID {cotizacion.taller_id}.",
        current_user.id_usuario
    )

    db.commit()
    return {"mensaje": "Cotización rechazada."}