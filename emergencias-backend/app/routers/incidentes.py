import math
import requests
import base64
import json
import os
from datetime import datetime, timedelta
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
from app.models.pago import Pago
from app.database import get_db, SessionLocal
from app.models.usuario import Usuario, TipoRol
from app.models.vehiculo import Vehiculo
from app.models.taller import Taller
from app.models.tecnico import Tecnico
from app.models.incidente import Incidente, EvidenciaIA, HistorialEstado, EstadoIncidente, TipoEvidencia, PrioridadIncidente
from app.schemas.incidente import IncidenteCreate, IncidenteOut, AccionSolicitud, AsignarTecnico, ActualizarEstado
from app.routers.auth import get_current_user
from app.routers.notificaciones import crear_notificacion_interna
from app.models.taller_rechazo import TallerRechazo
from app.utils.bitacora import registrar_evento  # CU21 — helper de bitácora
from apscheduler.schedulers.background import BackgroundScheduler
from app.models.excepcion import ExcepcionOperativa

router = APIRouter(prefix="/incidentes", tags=["Gestion Inteligente de Incidentes"])

# ===================================================================
# CU8: MOTOR PROFESIONAL "GROQ" BLINDADO (Cero caídas)
# ===================================================================
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")

def transcribir_audio_groq(audio_bytes: bytes):
    """Usa Whisper Large V3 en Groq para transcribir el .m4a del celular al instante."""
    url = "https://api.groq.com/openai/v1/audio/transcriptions"
    headers = {"Authorization": f"Bearer {GROQ_API_KEY}"}
    files = {"file": ("audio.m4a", audio_bytes, "audio/m4a")}
    data = {"model": "whisper-large-v3", "response_format": "json"}
    try:
        res = requests.post(url, headers=headers, files=files, data=data, timeout=10)
        if res.status_code == 200:
            texto = res.json().get("text", "").strip()
            return texto if texto else "Audio inaudible o vacío."
        else:
            print("Error Groq Audio:", res.text)
            return "Audio recibido (No se pudo transcribir)."
    except Exception as e:
        print("Excepción Groq Audio:", e)
        return "Audio recibido. (Fallo de red al transcribir)."

def clasificador_local_seguro(descripcion: str, transcripcion: str):
    """SALVAVIDAS: Si Groq se cae por completo, Python clasifica el texto."""
    texto_total = f"{descripcion} {transcripcion}".lower()
    clasificacion = "otros"
    prioridad = "incierto"
    resumen = "Evaluación técnica requerida."
    if any(p in texto_total for p in ["llan", "pinch", "tire", "goma", "flat", "rueda"]):
        clasificacion, prioridad, resumen = "llanta", "media", "Problema de neumático detectado."
    elif any(p in texto_total for p in ["cho", "acciden", "golp", "crash", "damage"]):
        clasificacion, prioridad, resumen = "choque", "alta", "Colisión vehicular detectada."
    elif any(p in texto_total for p in ["bat", "arran", "encien", "electr", "battery"]):
        clasificacion, prioridad, resumen = "bateria", "media", "Posible descarga de batería."
    elif any(p in texto_total for p in ["mot", "hum", "calien", "radia", "engine"]):
        clasificacion, prioridad, resumen = "motor", "alta", "Falla de motor o sobrecalentamiento."
    return f"[{clasificacion.upper()}] Prioridad {prioridad.upper()}: {resumen}"[:95], prioridad

def analizar_emergencia_groq(b64_img: str, descripcion: str, transcripcion: str):
    """Usa IA Visual. Si un modelo está apagado, salta automáticamente al siguiente."""
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"}
    texto_prompt = f"""
    Eres un perito experto en vehículos. Analiza la siguiente emergencia.
    Descripción del cliente: "{descripcion}"
    Lo que el cliente dijo en el audio: "{transcripcion}"
    Devuelve ESTRICTAMENTE un JSON válido con esta estructura:
    {{
        "resumen": "Resumen clínico y profesional de 1 línea.",
        "clasificacion": "choque",
        "prioridad": "alta"
    }}
    Solo devuelve el JSON puro, sin comillas invertidas ni explicaciones.
    """
    content_array = [{"type": "text", "text": texto_prompt}]
    if b64_img:
        content_array.append({"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64_img}"}})
    modelos_activos = [
        "llama-3.2-90b-vision-preview",
        "llama-3.2-11b-vision",
        "meta-llama/llama-4-scout-17b-16e-instruct"
    ]
    for modelo in modelos_activos:
        try:
            res = requests.post(url, headers=headers, json={"model": modelo, "messages": [{"role": "user", "content": content_array}], "temperature": 0.2}, timeout=10)
            if res.status_code == 200:
                texto_ia = res.json()["choices"][0]["message"]["content"]
                dict_ia = json.loads(texto_ia.replace("```json", "").replace("```", "").strip())
                clasificacion = dict_ia.get("clasificacion", "otros").upper()
                prioridad = dict_ia.get("prioridad", "incierto").lower()
                resumen = dict_ia.get("resumen", "Análisis completado.")
                return f"[{clasificacion}] Prioridad {prioridad.upper()}: {resumen}"[:95], prioridad
            else:
                print(f"Error Groq con {modelo}: {res.text}")
        except Exception as e:
            print(f"Excepción Groq con {modelo}: {e}")
    return clasificador_local_seguro(descripcion, transcripcion)

# ===================================================================
# ENDPOINT PARA RECIBIR IMÁGENES BASE64 DESDE FLUTTER
# ===================================================================
class ImageUpload(BaseModel):
    image_data: str

@router.post("/subir-imagen")
def subir_imagen(upload: ImageUpload):
    return {"url": f"data:image/jpeg;base64,{upload.image_data}"}

# ===================================================================
# RUTEO INTELIGENTE Y CRON JOB
# ===================================================================
def calcular_distancia(lat1, lon1, lat2, lon2):
    if not all([lat1, lon1, lat2, lon2]): return float('inf')
    R = 6371.0
    dlat = math.radians(float(lat2) - float(lat1))
    dlon = math.radians(float(lon2) - float(lon1))
    a = math.sin(dlat/2)**2 + math.cos(math.radians(float(lat1))) * math.cos(math.radians(float(lat2))) * math.sin(dlon/2)**2
    return R * (2 * math.atan2(math.sqrt(a), math.sqrt(1 - a)))

def buscar_taller_disponible(db, lat_emergencia, lon_emergencia, incidente_id=None):
    excluidos_ids = []
    if incidente_id:
        rechazos = db.query(TallerRechazo.taller_id).filter(
            TallerRechazo.incidente_id == incidente_id
        ).all()
        excluidos_ids = [r[0] for r in rechazos]

    talleres = db.query(Taller).all()
    mejor_taller, dist_min = None, float('inf')

    for t in talleres:
        if t.id_taller in excluidos_ids:
            continue
        if db.query(Tecnico).filter(
            Tecnico.taller_id == t.id_taller,
            Tecnico.disponible_boolean == True
        ).first():
            d = calcular_distancia(lat_emergencia, lon_emergencia,
                                   t.latitud_decimal, t.longitud_decimal)
            if d < dist_min:
                dist_min, mejor_taller = d, t

    return mejor_taller, dist_min

def robot_reasignacion_automatica():
    """Cron job: reasigna automáticamente incidentes sin respuesta tras 5 minutos."""
    db = SessionLocal()
    try:
        ahora = datetime.now()
        estancados = db.query(Incidente).filter(
            Incidente.estado_enum == EstadoIncidente.pendiente,
            Incidente.fecha_creacion_timestamp <= ahora - timedelta(minutes=5)
        ).all()
        for inc in estancados:
            nuevo_taller, dist = buscar_taller_disponible(db, inc.latitud_emergencia, inc.longitud_emergencia, inc.id_incidente)
            if nuevo_taller:
                msg = f"Ventana expirada. Reasignado a Taller ID: {nuevo_taller.id_taller}"
                inc.taller_actual_id = nuevo_taller.id_taller
                inc.fecha_creacion_timestamp = ahora
                crear_notificacion_interna(db, nuevo_taller.dueño_id, "🚨 Alerta Reasignada", "Un taller no respondió a tiempo.")
                # CU21 — registrar reasignación automática en bitácora
                registrar_evento(db, inc.id_incidente, "REASIGNACION_AUTOMATICA", msg)
            else:
                msg = "Ventana expirada. No hay más talleres disponibles."
                inc.taller_actual_id = None
            db.add(HistorialEstado(incidente_id=inc.id_incidente, estado_enum=EstadoIncidente.pendiente, comentario_texto=msg))
            db.commit()
    finally:
        db.close()

scheduler = BackgroundScheduler()
scheduler.add_job(robot_reasignacion_automatica, 'interval', minutes=1)
scheduler.start()

class UbicacionTecnicoUpdate(BaseModel):
    latitud: float
    longitud: float

@router.put("/{id_incidente}/ubicacion-tecnico")
def actualizar_ubicacion_tecnico(id_incidente: int, datos: UbicacionTecnicoUpdate, db: Session = Depends(get_db)):
    """Actualiza la posición GPS del técnico en tiempo real."""
    incidente = db.query(Incidente).filter(Incidente.id_incidente == id_incidente).first()
    if incidente:
        incidente.latitud_tecnico = datos.latitud
        incidente.longitud_tecnico = datos.longitud
        db.commit()
    return {"status": "ok"}

# ===================================================================
# CU7: REGISTRAR EMERGENCIA — acepta audio, imagen o texto por separado
# ===================================================================
# Descripción: Registra una nueva emergencia, con soporte para sincronización offline usando uuid_offline
# Ciclo: Ciclo 4
# CU: CU19
@router.post("/", response_model=IncidenteOut, status_code=status.HTTP_201_CREATED)
def registrar_emergencia(
    datos: IncidenteCreate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    # Verificar que el vehículo pertenece al cliente
    vehiculo = db.query(Vehiculo).filter(
        Vehiculo.id_vehiculo == datos.vehiculo_id,
        Vehiculo.usuario_id == current_user.id_usuario
    ).first()
    if not vehiculo:
        raise HTTPException(status_code=403, detail="Acceso denegado al vehículo.")

    # #Ciclo5 CU19 Verificar uuid_offline para evitar duplicados de sincronización offline
    if datos.uuid_offline:
        ya_existe = db.query(Incidente).filter(Incidente.uuid_offline == datos.uuid_offline).first()
        if ya_existe:
            return ya_existe

    # #Ciclo5 CAMBIO DE LÓGICA: Ya NO auto-asignamos taller.
    # El flujo nuevo es: emergencia → notificar talleres → talleres envían cotización → cliente escoge
    nuevo_incidente = Incidente(
        cliente_id=current_user.id_usuario,
        vehiculo_id=datos.vehiculo_id,
        taller_actual_id=None,  # #Ciclo5 NO asignar taller automáticamente
        latitud_emergencia=datos.latitud_emergencia,
        longitud_emergencia=datos.longitud_emergencia,
        descripcion_texto=datos.descripcion_texto,
        estado_enum=EstadoIncidente.buscando_taller,  # #Ciclo5 Inicia en buscando_taller
        uuid_offline=datos.uuid_offline  # CU19 — sincronización offline
    )
    db.add(nuevo_incidente)
    db.flush()

    # Validar que venga al menos un canal de evidencia (texto, foto o audio)
    texto_cliente = datos.descripcion_texto or ""
    tiene_audio  = any("audio"  in str(ev.tipo_enum) for ev in datos.evidencias)
    tiene_imagen = any("imagen" in str(ev.tipo_enum) for ev in datos.evidencias)
    tiene_texto  = bool(texto_cliente.strip())

    if not tiene_texto and not tiene_audio and not tiene_imagen:
        db.rollback()
        raise HTTPException(status_code=400, detail="Debes enviar al menos una descripción, foto o audio.")

    # Procesar cada canal de evidencia de forma INDEPENDIENTE
    b64_img, audio_bytes, transcripcion = None, None, ""

    for ev in datos.evidencias:
        tipo_str = str(ev.tipo_enum.value) if hasattr(ev.tipo_enum, 'value') else str(ev.tipo_enum)
        url = ev.url_recurso

        if "imagen" in tipo_str and url.startswith("data:image"):
            try: b64_img = url.split(",")[1]
            except: b64_img = None

        elif "audio" in tipo_str and url.startswith("data:audio"):
            try: audio_bytes = base64.b64decode(url.split(",")[1])
            except: audio_bytes = None

    # Transcribir audio solo si vino audio
    if audio_bytes:
        transcripcion = transcribir_audio_groq(audio_bytes)

    # La IA analiza con lo que tenga disponible
    texto_resumen_seguro, prioridad_ia = analizar_emergencia_groq(b64_img, texto_cliente, transcripcion)

    try:
        nuevo_incidente.prioridad_enum = PrioridadIncidente(prioridad_ia)
    except ValueError:
        nuevo_incidente.prioridad_enum = PrioridadIncidente.incierto

    # Guardar evidencias en BD
    for ev in datos.evidencias:
        tipo_raw = ev.tipo_enum
        tipo_str = str(tipo_raw.value) if hasattr(tipo_raw, 'value') else str(tipo_raw)
        transcripcion_guardar = transcripcion if "audio" in tipo_str and transcripcion else None
        db.add(EvidenciaIA(
            incidente_id=nuevo_incidente.id_incidente,
            tipo_enum=tipo_raw,
            url_recurso=ev.url_recurso,
            clasificacion_ia_texto=texto_resumen_seguro,
            nivel_confianza=0.98,
            transcripcion_audio_texto=transcripcion_guardar
        ))

    # #Ciclo5 EXTRAER CATEGORÍA IA para filtrar por especialidad
    import re as _re
    categoria_detectada = "otros"
    match_cat = _re.search(r'\[(\w+)\]', texto_resumen_seguro or "")
    if match_cat:
        categoria_detectada = match_cat.group(1).lower()

    # #Ciclo5 Mapeo categoría IA → palabras clave de especialidad del técnico
    ESPECIALIDAD_MAP = {
        "llanta":  ["llant", "llanta", "neumatico", "neumático", "tire"],
        "motor":   ["mecánico", "mecanico", "motor", "mecanic"],
        "bateria": ["electric", "eléctric", "bateria", "batería"],
        "choque":  ["carrocer", "choque", "latonería", "latoneria", "pintura"],
        "otros":   [],  # cualquier técnico disponible
    }
    keywords = ESPECIALIDAD_MAP.get(categoria_detectada, [])

    def taller_tiene_especialista(db, taller_id: int, keywords: list) -> bool:
        """True si el taller tiene al menos un técnico disponible con la especialidad."""
        query = db.query(Tecnico).filter(
            Tecnico.taller_id == taller_id,
            Tecnico.disponible_boolean == True
        )
        tecnicos = query.all()
        if not tecnicos:
            return False
        if not keywords:  # categoría "otros" → cualquier técnico sirve
            return True
        for tec in tecnicos:
            esp = (tec.especialidad or "").lower()
            if any(kw in esp for kw in keywords):
                return True
        return False

    # #Ciclo5 NOTIFICAR TALLERES CERCANOS (radio 5km) CON ESPECIALISTA
    talleres_todos = db.query(Taller).all()
    talleres_notificados = 0
    for t in talleres_todos:
        d = calcular_distancia(
            datos.latitud_emergencia, datos.longitud_emergencia,
            t.latitud_decimal, t.longitud_decimal
        )
        if d <= 5.0:
            if taller_tiene_especialista(db, t.id_taller, keywords):
                crear_notificacion_interna(
                    db, t.dueño_id,
                    f"🚨 Emergencia: {categoria_detectada.upper()} cerca",
                    f"Vehículo a {d:.1f}km necesita especialista en {categoria_detectada}. ¡Cotiza ahora!"
                )
                talleres_notificados += 1

    # Fallback 1: sin especialista cerca → notificar cualquier taller con técnico en 5km
    if talleres_notificados == 0:
        for t in talleres_todos:
            d = calcular_distancia(
                datos.latitud_emergencia, datos.longitud_emergencia,
                t.latitud_decimal, t.longitud_decimal
            )
            if d <= 5.0 and taller_tiene_especialista(db, t.id_taller, []):
                crear_notificacion_interna(
                    db, t.dueño_id,
                    "🚨 Emergencia Cercana (sin especialista)",
                    f"Vehículo a {d:.1f}km. Categoría: {categoria_detectada}. ¡Puedes cotizar igual!"
                )
                talleres_notificados += 1

    # Fallback 2: ningún taller en 5km → ampliar a TODOS con especialista
    if talleres_notificados == 0:
        for t in talleres_todos:
            if taller_tiene_especialista(db, t.id_taller, keywords):
                crear_notificacion_interna(
                    db, t.dueño_id,
                    f"🚨 Emergencia {categoria_detectada.upper()} (zona ampliada)",
                    f"No hay talleres cerca. Categoría: {categoria_detectada}. ¡Cotiza!"
                )
                talleres_notificados += 1

    # Guardar historial
    comentario = f"Emergencia publicada. Categoría IA: {categoria_detectada}. {talleres_notificados} talleres notificados."
    db.add(HistorialEstado(
        incidente_id=nuevo_incidente.id_incidente,
        estado_enum=EstadoIncidente.buscando_taller,
        comentario_texto=comentario
    ))
    crear_notificacion_interna(
        db, current_user.id_usuario,
        "Emergencia Registrada",
        f"IA detectó: {categoria_detectada}. {talleres_notificados} talleres con especialista notificados."
    )

    # CU21 — registrar creación en bitácora
    registrar_evento(
        db, nuevo_incidente.id_incidente,
        "CREACION",
        f"Emergencia registrada. Categoría IA: {categoria_detectada}. Prioridad: {prioridad_ia}. {talleres_notificados} talleres notificados.",
        current_user.id_usuario
    )

    db.commit()
    db.refresh(nuevo_incidente)
    return nuevo_incidente


# ===================================================================
# CU10: LISTAR EMERGENCIAS DISPONIBLES PARA COTIZAR
# #Ciclo5 CAMBIO: Ahora muestra TODOS los incidentes en buscando_taller
# a todos los talleres (excluyendo rechazados y ya cotizados)
# ===================================================================
@router.get("/pendientes", response_model=List[IncidenteOut])
def listar_solicitudes_pendientes(
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    # Si es admin devuelve todos los pendientes y buscando_taller
    if current_user.rol.value == "admin":
        return db.query(Incidente).filter(
            Incidente.estado_enum.in_([
                EstadoIncidente.pendiente,
                EstadoIncidente.buscando_taller
            ])
        ).all()

    # Buscar el taller del usuario autenticado
    taller = db.query(Taller).filter(
        Taller.dueño_id == current_user.id_usuario
    ).first()
    if not taller:
        return []

    # #Ciclo5 Obtener IDs de incidentes que este taller ya rechazó
    rechazados = db.query(TallerRechazo.incidente_id).filter(
        TallerRechazo.taller_id == taller.id_taller
    ).all()
    ids_rechazados = [r[0] for r in rechazados]

    # #Ciclo5 Obtener incidentes ya cotizados por este taller (para no mostrar de nuevo)
    from app.models.cotizacion import Cotizacion
    ya_cotizados = db.query(Cotizacion.incidente_id).filter(
        Cotizacion.taller_id == taller.id_taller
    ).all()
    ids_ya_cotizados = [c[0] for c in ya_cotizados]

    # #Ciclo5 NUEVO: Mostrar TODOS los incidentes en buscando_taller
    # que no hayan sido rechazados ni ya cotizados por este taller
    return db.query(Incidente).filter(
        Incidente.estado_enum.in_([
            EstadoIncidente.pendiente,
            EstadoIncidente.buscando_taller
        ]),
        Incidente.id_incidente.notin_(ids_rechazados),
        Incidente.id_incidente.notin_(ids_ya_cotizados)
    ).all()
# ===================================================================
# CU10: ACEPTAR O RECHAZAR SOLICITUD (taller responde en web)
# #Ciclo5 NOTA: En el flujo nuevo, el taller usa cotizaciones (CU18).
# Este endpoint sigue disponible para compatibilidad con la web Angular.
# ===================================================================
@router.post("/{id_incidente}/accion")
def responder_solicitud(
    id_incidente: int,
    datos: AccionSolicitud,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    incidente = db.query(Incidente).filter(Incidente.id_incidente == id_incidente).first()
    # #Ciclo5 Aceptar tanto pendiente como buscando_taller
    estados_validos = [EstadoIncidente.pendiente, EstadoIncidente.buscando_taller]
    if not incidente or incidente.estado_enum not in estados_validos:
        raise HTTPException(status_code=400, detail="El incidente ya no está disponible.")

    # Verificar que el taller que responde es el asignado (si hay uno asignado)
    taller_usuario = db.query(Taller).filter(
        Taller.dueño_id == current_user.id_usuario
    ).first()

    if datos.accion == "aceptar":
        incidente.estado_enum = EstadoIncidente.en_proceso
        if taller_usuario:
            incidente.taller_actual_id = taller_usuario.id_taller
        db.add(HistorialEstado(
            incidente_id=id_incidente,
            estado_enum=EstadoIncidente.en_proceso,
            comentario_texto="Solicitud aceptada directamente por el Taller (web)."
        ))
        crear_notificacion_interna(db, incidente.cliente_id, "¡Auxilio en camino!", "Tu solicitud ha sido aceptada.")
        # CU21 — registrar aceptación en bitácora
        registrar_evento(
            db, id_incidente,
            "TALLER_ACEPTO",
            f"El taller ID {incidente.taller_actual_id} aceptó la solicitud.",
            current_user.id_usuario
        )

    elif datos.accion == "rechazar":
        if taller_usuario:
            db.add(TallerRechazo(
                incidente_id=id_incidente,
                taller_id=taller_usuario.id_taller,
                motivo=datos.comentario or "Sin motivo."
            ))
        # #Ciclo5 Mantener en buscando_taller para que otros talleres sigan cotizando
        db.add(HistorialEstado(
            incidente_id=id_incidente,
            estado_enum=EstadoIncidente.buscando_taller,
            comentario_texto=f"Taller rechazó. Siguiendo en búsqueda de talleres."
        ))
        # CU21 — registrar rechazo en bitácora
        registrar_evento(
            db, id_incidente,
            "TALLER_RECHAZO",
            datos.comentario or "El taller rechazó la solicitud.",
            current_user.id_usuario
        )

    db.commit()
    return {"status": "ok"}



# ===================================================================
# CU11: ASIGNAR TÉCNICO AL INCIDENTE
# ===================================================================
@router.post("/{id_incidente}/asignar")
def asignar_tecnico(
    id_incidente: int,
    datos: AsignarTecnico,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    # Verificar que el incidente existe antes de operar
    incidente = db.query(Incidente).filter(Incidente.id_incidente == id_incidente).first()
    if not incidente:
        raise HTTPException(status_code=404, detail="Incidente no encontrado.")

    tecnico = db.query(Tecnico).filter(Tecnico.id_tecnico == datos.tecnico_id).first()
    if not tecnico or not tecnico.disponible_boolean:
        raise HTTPException(status_code=400, detail="El técnico no está disponible.")

    incidente.tecnico_id = datos.tecnico_id
    tecnico.disponible_boolean = False
    db.add(HistorialEstado(
        incidente_id=id_incidente,
        estado_enum=EstadoIncidente.en_proceso,
        comentario_texto=f"Técnico {tecnico.nombre} despachado hacia el lugar."
    ))
    crear_notificacion_interna(db, incidente.cliente_id, "Técnico Asignado", f"El mecánico {tecnico.nombre} va en ruta.")
    # CU21 — registrar asignación de técnico en bitácora
    registrar_evento(
        db, id_incidente,
        "TECNICO_ASIGNADO",
        f"Técnico {tecnico.nombre} (ID {tecnico.id_tecnico}) asignado al incidente.",
        current_user.id_usuario
    )

    db.commit()
    return {"message": "Técnico asignado exitosamente."}


# ===================================================================
# CU12: VER MI TRABAJO ASIGNADO (técnico móvil Flutter)
# #Ciclo5 - El técnico ve el incidente que le fue asignado
# ===================================================================
@router.get("/mis-trabajos", response_model=List[IncidenteOut])
def mis_trabajos_tecnico(
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    El técnico móvil llama este endpoint para obtener el incidente
    que le fue asignado. Solo muestra incidentes activos (no finalizados).
    El técnico debe conectarse a WS /ws/incidente/{id} para recibir
    actualizaciones en tiempo real.
    """
    # Buscar el registro del técnico por su usuario
    tecnico = db.query(Tecnico).filter(
        Tecnico.usuario_id == current_user.id_usuario
    ).first()

    # Fallback: buscar por nombre si no hay usuario_id
    if not tecnico:
        tecnico = db.query(Tecnico).filter(
            Tecnico.nombre.ilike(f"%{current_user.nombre}%")
        ).first()

    if not tecnico:
        return []

    # Estados activos que el técnico debe ver
    estados_activos = [
        EstadoIncidente.taller_asignado,
        EstadoIncidente.en_proceso,
        EstadoIncidente.en_camino,
        EstadoIncidente.en_atencion,
    ]

    incidentes = db.query(Incidente).filter(
        Incidente.tecnico_id == tecnico.id_tecnico,
        Incidente.estado_enum.in_(estados_activos)
    ).order_by(Incidente.fecha_creacion_timestamp.desc()).all()

    # Enriquecer con datos del técnico y precio de cotización aceptada
    from app.models.cotizacion import Cotizacion
    resultado = []
    for inc in incidentes:
        inc_out = IncidenteOut.model_validate(inc)
        inc_out.nombre_tecnico = tecnico.nombre
        inc_out.especialidad_tecnico = tecnico.especialidad or "General"

        # #Ciclo5 - Buscar precio de la cotización aceptada para este incidente
        cot_aceptada = db.query(Cotizacion).filter(
            Cotizacion.incidente_id == inc.id_incidente,
            Cotizacion.estado == "aceptada"
        ).first()
        if cot_aceptada:
            inc_out.precio_cotizacion = float(cot_aceptada.precio_estimado)

        resultado.append(inc_out)

    return resultado


# ===================================================================
# CU17: ACTUALIZAR UBICACIÓN DEL TÉCNICO VÍA REST
# #Ciclo5 - Alternativa REST al WebSocket para enviar GPS
#           El backend reenvía la ubicación por WS a todos en la sala
# ===================================================================
# Descripción: Actualiza la ubicación en tiempo real del técnico asignado a un incidente
# Ciclo: Ciclo 4
# CU: CU17
@router.put("/{id_incidente}/ubicacion-tecnico", status_code=200)
async def actualizar_ubicacion_tecnico(
    id_incidente: int,
    datos: dict,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    El técnico móvil envía su GPS periódicamente.
    El backend guarda la ubicación en el incidente y la retransmite
    por WebSocket como mensaje tipo 'ubicacion_tecnico' a todos
    los conectados (cliente y monitoreo web).

    Body: { "latitud": -17.783, "longitud": -63.182, "eta_minutos": 5 }
    """
    incidente = db.query(Incidente).filter(
        Incidente.id_incidente == id_incidente
    ).first()
    if not incidente:
        raise HTTPException(status_code=404, detail="Incidente no encontrado.")

    lat = datos.get("latitud")
    lng = datos.get("longitud")
    eta = datos.get("eta_minutos", 0)

    if lat is None or lng is None:
        raise HTTPException(status_code=400, detail="Latitud y longitud son requeridas.")

    # #Ciclo5 CU17 - Guardar en BD y retransmitir por WS
    incidente.latitud_tecnico  = lat
    incidente.longitud_tecnico = lng

    # Guardar punto en ruta del técnico
    try:
        from app.models.ruta_tecnico import RutaTecnico
        punto = RutaTecnico(incidente_id=id_incidente, latitud=lat, longitud=lng)
        db.add(punto)
    except Exception:
        pass  # Si no existe el modelo, ignorar

    db.commit()

    # Retransmitir por WebSocket a todos en la sala del incidente
    from app.routers.websocket_incidente import gestor
    await gestor.broadcast(id_incidente, {
        "tipo": "ubicacion_tecnico",
        "latitud": lat,
        "longitud": lng,
        "eta_minutos": eta,
        "timestamp": datetime.utcnow().isoformat()
    })

    return {"ok": True, "latitud": lat, "longitud": lng, "eta_minutos": eta}

# ===================================================================
# CU12: LISTAR INCIDENTES EN PROCESO (para el técnico en Flutter)
# ===================================================================
@router.get("/en-proceso", response_model=List[IncidenteOut])
def listar_solicitudes_en_proceso(
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    # #Ciclo5 - Incluir taller_asignado y estados activos para que el monitoreo
    # muestre el incidente desde que el cliente acepta una cotización
    estados_activos = [
        EstadoIncidente.taller_asignado,
        EstadoIncidente.en_proceso,
        EstadoIncidente.en_camino,
        EstadoIncidente.en_atencion,
    ]
    query = db.query(Incidente).filter(Incidente.estado_enum.in_(estados_activos))

    # Si es taller, filtrar solo sus incidentes
    if current_user.rol.value != "admin":
        taller = db.query(Taller).filter(
            Taller.dueño_id == current_user.id_usuario
        ).first()
        if taller:
            query = query.filter(Incidente.taller_actual_id == taller.id_taller)
        else:
            return []

    incidentes = query.order_by(Incidente.fecha_creacion_timestamp.desc()).all()

    # #Ciclo5 CU18 - Enriquecer con nombre y especialidad del técnico
    resultado = []
    for inc in incidentes:
        inc_dict = IncidenteOut.model_validate(inc)
        if inc.tecnico_id:
            tec = db.query(Tecnico).filter(Tecnico.id_tecnico == inc.tecnico_id).first()
            if tec:
                inc_dict.nombre_tecnico = tec.nombre
                inc_dict.especialidad_tecnico = tec.especialidad or "General"
        resultado.append(inc_dict)

    return resultado


# ===================================================================
# CU12: ACTUALIZAR ESTADO DEL SERVICIO (técnico finaliza o avanza)
# ===================================================================
@router.put("/{id_incidente}/estado", status_code=status.HTTP_200_OK)
def actualizar_estado_servicio(
    id_incidente: int,
    datos: ActualizarEstado,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    incidente = db.query(Incidente).filter(Incidente.id_incidente == id_incidente).first()
    if not incidente:
        raise HTTPException(status_code=404, detail="Incidente no encontrado.")

    incidente.estado_enum = datos.estado_enum

    # Si el servicio fue finalizado: liberar técnico y guardar costo
    if datos.estado_enum in [EstadoIncidente.atendido, EstadoIncidente.finalizado]:
        if incidente.tecnico_id:
            tecnico = db.query(Tecnico).filter(Tecnico.id_tecnico == incidente.tecnico_id).first()
            if tecnico:
                tecnico.disponible_boolean = True
        if datos.costo_final is not None:
            incidente.costo_final_decimal = datos.costo_final

    db.add(HistorialEstado(
        incidente_id=id_incidente,
        estado_enum=datos.estado_enum,
        comentario_texto=datos.comentario or f"Servicio actualizado a {datos.estado_enum.value}."
    ))
    crear_notificacion_interna(
        db, incidente.cliente_id,
        "Actualización de Servicio",
        f"El estado de tu emergencia ahora es: {datos.estado_enum.value.upper()}"
    )
    # CU21 — registrar cambio de estado en bitácora
    registrar_evento(
        db, id_incidente,
        "CAMBIO_ESTADO",
        f"Estado actualizado a '{datos.estado_enum.value}'. {datos.comentario or ''}".strip(),
        current_user.id_usuario
    )

    db.commit()
    return {"message": "Estado actualizado correctamente", "nuevo_estado": incidente.estado_enum}

# ===================================================================
# CU20: REGISTRAR EXCEPCIÓN OPERATIVA
# Maneja cancelaciones, llegada del seguro y casos mixtos
# ===================================================================
class ExcepcionCreate(BaseModel):
    tipo_excepcion: str
    # Valores válidos:
    # "cancelacion_cliente"  → cliente cancela antes de que llegue el taller
    # "llego_seguro_primero" → el seguro llegó antes que el taller
    # "llegaron_ambos"       → llegaron taller y seguro; taller recibe compensación
    motivo: Optional[str] = None
    compensacion_taller: Optional[float] = 0.00

# Descripción: Registra una excepción operativa (falsa alarma, cliente no encontrado, falla de herramienta)
# Ciclo: Ciclo 4
# CU: CU20
@router.post("/{id_incidente}/excepcion")
def registrar_excepcion(
    id_incidente: int,
    datos: ExcepcionCreate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    # Verificar que el incidente existe y está activo
    incidente = db.query(Incidente).filter(Incidente.id_incidente == id_incidente).first()
    if not incidente:
        raise HTTPException(status_code=404, detail="Incidente no encontrado.")

    # Verificar que el incidente no esté ya cancelado o finalizado
    estados_bloqueados = [EstadoIncidente.cancelado, EstadoIncidente.finalizado, EstadoIncidente.atendido]
    if incidente.estado_enum in estados_bloqueados:
        raise HTTPException(
            status_code=400,
            detail=f"No se puede registrar una excepción en un incidente con estado '{incidente.estado_enum.value}'. Solo se puede cancelar si está activo."
        )

    # Verificar tipo de excepción válido
    tipos_validos = ["cancelacion_cliente", "llego_seguro_primero", "llegaron_ambos"]
    if datos.tipo_excepcion not in tipos_validos:
        raise HTTPException(status_code=400, detail=f"Tipo inválido. Usa: {tipos_validos}")
    
    # Insertar en excepciones_operativas
    nueva_excepcion = ExcepcionOperativa(
        incidente_id=id_incidente,
        tipo_excepcion=datos.tipo_excepcion,
        motivo=datos.motivo or "",
        compensacion_taller=datos.compensacion_taller or 0.00
    )
    db.add(nueva_excepcion)
    
    # Cancelar el incidente en todos los casos
    incidente.estado_enum = EstadoIncidente.cancelado
    
    # Liberar al técnico si estaba asignado
    if incidente.tecnico_id:
        tecnico = db.query(Tecnico).filter(
            Tecnico.id_tecnico == incidente.tecnico_id
        ).first()
        if tecnico:
            tecnico.disponible_boolean = True
            
    # Guardar historial
    db.add(HistorialEstado(
        incidente_id=id_incidente,
        estado_enum=EstadoIncidente.cancelado,
        comentario_texto=f"Excepción: {datos.tipo_excepcion}. {datos.motivo or ''}"
    ))
    
    # ============================================================
    # COMPENSACIÓN AL TALLER — solo si llegaron ambos o seguro
    # Se genera un pago especial con estado "compensacion"
    # La BD no acepta montos de 0, así que solo se crea si hay monto real
    # ============================================================
    if datos.tipo_excepcion in ["llegaron_ambos", "llego_seguro_primero"]:
        monto_compensacion = datos.compensacion_taller or 0.00
        if monto_compensacion > 0 and incidente.taller_actual_id:
            from app.models.pago import Pago, MetodoPago
            taller = db.query(Taller).filter(
                Taller.id_taller == incidente.taller_actual_id
            ).first()
            # Verificar que no exista ya un pago para este incidente
            pago_existente = db.query(Pago).filter(
                Pago.incidente_id == id_incidente
            ).first()
            if taller and not pago_existente:
                pago_compensacion = Pago(
                    incidente_id=id_incidente,
                    dueño_taller_id=taller.dueño_id,
                    monto_total_decimal=monto_compensacion,
                    metodo_enum=MetodoPago.transferencia,  # compensación interna
                    estado_pago_enum="compensacion"        # estado especial, distinto de "completado"
                )
                db.add(pago_compensacion)
                crear_notificacion_interna(
                    db, taller.dueño_id,
                    "💰 Compensación por Desplazamiento",
                    f"Recibiste {monto_compensacion} Bs. por el incidente #{id_incidente}."
                )
            # CU21 — registrar compensación en bitácora
            registrar_evento(
                db, id_incidente,
                "COMPENSACION_TALLER",
                f"Compensación de {monto_compensacion} Bs. generada para taller ID {incidente.taller_actual_id}.",
                current_user.id_usuario
            )
        else:
            # Llegaron ambos pero no se indicó monto — notificar igualmente
            if incidente.taller_actual_id:
                taller = db.query(Taller).filter(
                    Taller.id_taller == incidente.taller_actual_id
                ).first()
                if taller:
                    crear_notificacion_interna(
                        db, taller.dueño_id,
                        "ℹ️ Caso Cerrado",
                        f"El incidente #{id_incidente} fue cerrado. "
                        f"Motivo: {datos.tipo_excepcion}. Sin compensación registrada."
                    )
                    
    # Notificar al cliente según el tipo
    mensajes_cliente = {
        "cancelacion_cliente":  "Tu solicitud fue cancelada correctamente.",
        "llego_seguro_primero": "El caso fue cerrado porque llegó tu seguro primero.",
        "llegaron_ambos":       "El caso fue cerrado. El taller recibirá compensación por desplazamiento."
    }
    crear_notificacion_interna(
        db, incidente.cliente_id,
        "Servicio Cancelado",
        mensajes_cliente.get(datos.tipo_excepcion, "El servicio fue cancelado.")
    )
    
    # CU21 — registrar excepción en bitácora
    registrar_evento(
        db, id_incidente,
        "EXCEPCION",
        f"Tipo: {datos.tipo_excepcion}. Motivo: {datos.motivo or 'Sin motivo'}. "
        f"Compensación: {datos.compensacion_taller or 0} Bs.",
        current_user.id_usuario
    )
    
    db.commit()
    
    return {
        "status": "ok",
        "mensaje": "Excepción registrada. Incidente cancelado.",
        "tipo": datos.tipo_excepcion,
        "compensacion_generada": (
            datos.compensacion_taller > 0
            if datos.tipo_excepcion in ["llegaron_ambos", "llego_seguro_primero"]
            else False
        )
    }

# ===================================================================
# CU9: MONITOREO EN TIEMPO REAL DEL AUXILIO
# ===================================================================
@router.get("/{id_incidente}/monitoreo", tags=["CU9 - Monitoreo de Auxilio"])
def monitorear_auxilio(
    id_incidente: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    incidente = db.query(Incidente).filter(Incidente.id_incidente == id_incidente).first()
    if not incidente:
        raise HTTPException(status_code=404, detail="Incidente no encontrado")

    # #Ciclo5 - Buscar precio de la cotización aceptada
    from app.models.cotizacion import Cotizacion
    cot_aceptada = db.query(Cotizacion).filter(
        Cotizacion.incidente_id == id_incidente,
        Cotizacion.estado == "aceptada"
    ).first()

    respuesta = {
        "id_incidente": incidente.id_incidente,
        "estado_actual": incidente.estado_enum.value,
        "prioridad": incidente.prioridad_enum.value,
        "latitud_emergencia": float(incidente.latitud_emergencia) if incidente.latitud_emergencia else None,
        "longitud_emergencia": float(incidente.longitud_emergencia) if incidente.longitud_emergencia else None,
        "latitud_tecnico": float(incidente.latitud_tecnico) if incidente.latitud_tecnico else None,
        "longitud_tecnico": float(incidente.longitud_tecnico) if incidente.longitud_tecnico else None,
        "costo_final_decimal": float(incidente.costo_final_decimal) if incidente.costo_final_decimal else 0.0,
        "precio_cotizacion": float(cot_aceptada.precio_estimado) if cot_aceptada else None,
        "precio_cotizacion_aceptada": float(cot_aceptada.precio_estimado) if cot_aceptada else None,
        "descripcion_texto": incidente.descripcion_texto,
        "nombre_taller": None,
        "tecnico_asignado": None,
        "taller_responsable": None
    }

    # Obtener nombre del taller asignado
    if incidente.taller_actual_id:
        taller_asig = db.query(Taller).filter(Taller.id_taller == incidente.taller_actual_id).first()
        if taller_asig:
            respuesta["nombre_taller"] = taller_asig.nombre
            respuesta["taller_responsable"] = taller_asig.nombre

    if incidente.tecnico_id:
        tecnico = db.query(Tecnico).filter(Tecnico.id_tecnico == incidente.tecnico_id).first()
        if tecnico:
            respuesta["tecnico_asignado"] = {"nombre": tecnico.nombre, "especialidad": tecnico.especialidad}
            # Fallback: si no se llenó nombre_taller arriba, usar el taller del técnico
            if not respuesta["nombre_taller"]:
                taller = db.query(Taller).filter(Taller.id_taller == tecnico.taller_id).first()
                if taller:
                    respuesta["nombre_taller"] = taller.nombre
                    respuesta["taller_responsable"] = taller.nombre

    return respuesta


# ===================================================================
# CU9: RECUPERAR EMERGENCIA ACTIVA DEL CLIENTE TRAS CERRAR SESIÓN
# ===================================================================
@router.get("/cliente/activo", tags=["CU9 - Monitoreo de Auxilio"])
def obtener_emergencia_activa(
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    incidente = db.query(Incidente).filter(
        Incidente.cliente_id == current_user.id_usuario,
        Incidente.estado_enum != EstadoIncidente.cancelado
    ).order_by(Incidente.id_incidente.desc()).first()

    if incidente:
        # Si ya fue atendido y tiene pago, el ciclo está cerrado
        if incidente.estado_enum in [EstadoIncidente.atendido, EstadoIncidente.finalizado]:
            pago_existente = db.query(Pago).filter(Pago.incidente_id == incidente.id_incidente).first()
            if pago_existente:
                return {"id_incidente": None}
        return {"id_incidente": incidente.id_incidente}

    return {"id_incidente": None}

# ===================================================================
# CU12: HISTORIAL DE SERVICIOS DEL TÉCNICO (solo atendidos)
# ===================================================================
@router.get("/historial/tecnico/{id_tecnico}", tags=["CU12 - Técnico de Auxilio"])
def obtener_historial_tecnico(
    id_tecnico: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    tecnico = db.query(Tecnico).filter(Tecnico.usuario_id == current_user.id_usuario).first()
    if not tecnico:
        return []  # Usuario no es técnico — devolver vacío sin crashear

    # Solo mostrar incidentes finalizados o atendidos
    incidentes = db.query(Incidente).filter(
        Incidente.tecnico_id == tecnico.id_tecnico,
        Incidente.estado_enum.in_([EstadoIncidente.atendido, EstadoIncidente.finalizado])
    ).order_by(Incidente.fecha_creacion_timestamp.desc()).all()

    resultado = []
    for inc in incidentes:
        cliente  = db.query(Usuario).filter(Usuario.id_usuario == inc.cliente_id).first()
        vehiculo = db.query(Vehiculo).filter(Vehiculo.id_vehiculo == inc.vehiculo_id).first()
        resultado.append({
            "id_incidente":            inc.id_incidente,
            "fecha_creacion_timestamp": inc.fecha_creacion_timestamp,
            "estado_enum":             inc.estado_enum.value if hasattr(inc.estado_enum, 'value') else str(inc.estado_enum),
            "cliente_nombre":          cliente.nombre if cliente else "Cliente Anónimo",
            "vehiculo_modelo":         f"{vehiculo.marca} {vehiculo.modelo}" if vehiculo else "Sin registrar"
        })
    return resultado

