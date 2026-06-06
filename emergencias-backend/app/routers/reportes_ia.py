# ============================================================
# Router de Reportes con Búsqueda Inteligente - Ciclo 5 - CU24
# La VOZ se transcribe con Whisper. El texto detecta tipo/período
# por keywords. NO genera narrativa IA - solo datos reales en tabla.
# ============================================================

import os, base64, re, requests
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.database import get_db
from app.models.usuario import Usuario, TipoRol
from app.models.incidente import Incidente, EstadoIncidente
from app.models.pago import Pago
from app.models.taller import Taller
from app.models.tecnico import Tecnico
from app.models.excepcion import ExcepcionOperativa
from app.models.cotizacion import Cotizacion
from app.routers.auth import get_current_user
from app.schemas.reporte_ia import ReporteRequest, ReporteVozRequest, ReporteResponse

try:
    from app.models.calificacion import Calificacion
except ImportError:
    Calificacion = None

router = APIRouter(prefix="/reportes-ia", tags=["CU24 - Reportes Inteligentes IA"])
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")


# ===================================================================
# DETECCIÓN POR KEYWORDS — Sin llamada a IA, rápido y confiable
# #Ciclo5 CU24 - La IA solo se usa para TRANSCRIPCIÓN de voz
# ===================================================================
def _detectar_tipo_y_periodo(prompt: str) -> dict:
    """
    Detecta el tipo de reporte y período por palabras clave.
    NO usa IA — es instantáneo y confiable.
    """
    p = prompt.lower()

    # — Tipo de reporte —
    tipo = "general"
    if any(k in p for k in ["comision", "comisión", "pago", "ingreso", "cobro", "factura"]):
        tipo = "comisiones"
    elif any(k in p for k in ["taller", "talleres", "mecanic", "mecánic", "automotriz"]):
        tipo = "talleres"
    elif any(k in p for k in ["tecnico", "técnico", "tecnicos", "técnicos", "staff", "mecanico", "mecánico"]):
        tipo = "tecnicos"
    elif any(k in p for k in ["cliente", "clientes", "usuario", "usuarios"]):
        tipo = "clientes"

    # — Período —
    periodo = 30  # default: último mes
    if any(k in p for k in ["hoy", "del día", "del dia", "de hoy", "diario"]):
        periodo = 1
    elif any(k in p for k in ["semana", "semanal", "últimos 7", "ultimos 7"]):
        periodo = 7
    elif any(k in p for k in ["quincena", "15 días", "15 dias"]):
        periodo = 15
    elif any(k in p for k in ["mes", "mensual", "último mes", "ultimo mes"]):
        periodo = 30
    elif any(k in p for k in ["trimestre", "3 meses", "90 días", "90 dias"]):
        periodo = 90
    elif any(k in p for k in ["año", "anual", "365"]):
        periodo = 365

    return {"tipo_reporte": tipo, "periodo_dias": periodo}


# ===================================================================
# TRANSCRIPCIÓN DE VOZ con Whisper — Solo para el endpoint /voz
# #Ciclo5 CU24
# ===================================================================
def _transcribir_audio(audio_bytes: bytes) -> str:
    if not GROQ_API_KEY:
        return "Sin clave Groq para transcripción."
    url = "https://api.groq.com/openai/v1/audio/transcriptions"
    headers = {"Authorization": f"Bearer {GROQ_API_KEY}"}
    files = {"file": ("audio.m4a", audio_bytes, "audio/m4a")}
    data = {"model": "whisper-large-v3", "response_format": "json", "language": "es"}
    try:
        res = requests.post(url, headers=headers, files=files, data=data, timeout=15)
        if res.status_code == 200:
            return res.json().get("text", "").strip() or "Audio inaudible."
        print(f"Whisper error: {res.status_code} {res.text}")
    except Exception as e:
        print(f"Error transcripción: {e}")
    return "No se pudo transcribir el audio."


# ===================================================================
# RECOPILADORES DE DATOS REALES POR TIPO - #Ciclo5 CU24
# ===================================================================
def _datos_comisiones(db: Session, fecha_inicio: datetime, user: Usuario) -> dict:
    """Pagos y comisiones por taller"""
    q = db.query(Pago).filter(Pago.fecha_pago_timestamp >= fecha_inicio)
    if user.rol != TipoRol.admin:
        q = q.filter(Pago.dueño_taller_id == user.id_usuario)

    pagos = q.all()
    total = sum(float(p.monto_total_decimal or 0) for p in pagos)

    # Agrupar por taller
    por_taller: dict = {}
    for p in pagos:
        t = db.query(Taller).filter(Taller.dueño_id == p.dueño_taller_id).first()
        nombre = t.nombre if t else f"Usuario #{p.dueño_taller_id}"
        if nombre not in por_taller:
            por_taller[nombre] = {"total_pagos": 0, "monto_bs": 0.0}
        por_taller[nombre]["total_pagos"] += 1
        por_taller[nombre]["monto_bs"] = round(por_taller[nombre]["monto_bs"] + float(p.monto_total_decimal or 0), 2)

    filas = [{"taller": k, **v} for k, v in por_taller.items()]
    filas.sort(key=lambda x: x["monto_bs"], reverse=True)

    return {
        "tipo": "comisiones",
        "titulo": "Comisiones y Pagos por Taller",
        "total_pagos": len(pagos),
        "ingresos_totales_bs": round(total, 2),
        "filas": filas,
        "columnas": ["taller", "total_pagos", "monto_bs"]
    }


def _datos_talleres(db: Session, fecha_inicio: datetime, user: Usuario) -> dict:
    """Rendimiento por taller"""
    if user.rol == TipoRol.admin:
        talleres = db.query(Taller).all()
    else:
        talleres = db.query(Taller).filter(Taller.dueño_id == user.id_usuario).all()

    filas = []
    for t in talleres:
        total = db.query(Incidente).filter(
            Incidente.taller_actual_id == t.id_taller,
            Incidente.fecha_creacion_timestamp >= fecha_inicio
        ).count()
        finalizados = db.query(Incidente).filter(
            Incidente.taller_actual_id == t.id_taller,
            Incidente.estado_enum.in_([EstadoIncidente.atendido, EstadoIncidente.finalizado]),
            Incidente.fecha_creacion_timestamp >= fecha_inicio
        ).count()
        cancelados = db.query(Incidente).filter(
            Incidente.taller_actual_id == t.id_taller,
            Incidente.estado_enum == EstadoIncidente.cancelado,
            Incidente.fecha_creacion_timestamp >= fecha_inicio
        ).count()
        tecnicos = db.query(Tecnico).filter(Tecnico.taller_id == t.id_taller).count()
        calif = 0.0
        if Calificacion:
            avg = db.query(func.avg(Calificacion.puntuacion)).filter(
                Calificacion.taller_id == t.id_taller
            ).scalar()
            calif = round(float(avg), 1) if avg else 0.0
        filas.append({
            "taller": t.nombre,
            "total": total,
            "finalizados": finalizados,
            "cancelados": cancelados,
            "exito_%": round(finalizados / total * 100, 1) if total > 0 else 0.0,
            "calificacion": calif,
            "tecnicos": tecnicos
        })

    filas.sort(key=lambda x: x["total"], reverse=True)
    return {
        "tipo": "talleres",
        "titulo": "Rendimiento por Taller",
        "total_talleres": len(talleres),
        "filas": filas,
        "columnas": ["taller", "total", "finalizados", "cancelados", "exito_%", "calificacion", "tecnicos"]
    }


def _datos_tecnicos(db: Session, fecha_inicio: datetime, user: Usuario) -> dict:
    """Lista y rendimiento de técnicos"""
    q = db.query(Tecnico)
    if user.rol != TipoRol.admin:
        taller = db.query(Taller).filter(Taller.dueño_id == user.id_usuario).first()
        if taller:
            q = q.filter(Tecnico.taller_id == taller.id_taller)

    tecnicos = q.all()
    filas = []
    for tec in tecnicos:
        servicios = db.query(Incidente).filter(
            Incidente.tecnico_id == tec.id_tecnico,
            Incidente.fecha_creacion_timestamp >= fecha_inicio
        ).count()
        taller_obj = db.query(Taller).filter(Taller.id_taller == tec.taller_id).first()
        filas.append({
            "nombre": tec.nombre,
            "especialidad": tec.especialidad or "General",
            "taller": taller_obj.nombre if taller_obj else "—",
            "estado": "Disponible" if tec.disponible_boolean else "Ocupado",
            "servicios_periodo": servicios
        })

    filas.sort(key=lambda x: x["servicios_periodo"], reverse=True)
    disponibles = sum(1 for t in tecnicos if t.disponible_boolean)
    return {
        "tipo": "tecnicos",
        "titulo": "Listado de Técnicos",
        "total_tecnicos": len(tecnicos),
        "disponibles": disponibles,
        "ocupados": len(tecnicos) - disponibles,
        "filas": filas,
        "columnas": ["nombre", "especialidad", "taller", "estado", "servicios_periodo"]
    }


def _datos_clientes(db: Session, fecha_inicio: datetime, user: Usuario) -> dict:
    """Clientes con actividad"""
    clientes = db.query(Usuario).filter(Usuario.rol == TipoRol.cliente).all()
    filas = []
    for c in clientes:
        total_inc = db.query(Incidente).filter(
            Incidente.cliente_id == c.id_usuario,
            Incidente.fecha_creacion_timestamp >= fecha_inicio
        ).count()
        if total_inc > 0:
            finalizados = db.query(Incidente).filter(
                Incidente.cliente_id == c.id_usuario,
                Incidente.estado_enum.in_([EstadoIncidente.atendido, EstadoIncidente.finalizado]),
                Incidente.fecha_creacion_timestamp >= fecha_inicio
            ).count()
            filas.append({
                "cliente": c.nombre,
                "email": c.email,
                "incidentes": total_inc,
                "finalizados": finalizados
            })

    filas.sort(key=lambda x: x["incidentes"], reverse=True)
    return {
        "tipo": "clientes",
        "titulo": "Clientes con Actividad",
        "total_clientes": len(filas),
        "filas": filas,
        "columnas": ["cliente", "email", "incidentes", "finalizados"]
    }


def _datos_general(db: Session, fecha_inicio: datetime, user: Usuario) -> dict:
    """Resumen general"""
    taller = None
    if user.rol != TipoRol.admin:
        taller = db.query(Taller).filter(Taller.dueño_id == user.id_usuario).first()

    q = db.query(Incidente).filter(Incidente.fecha_creacion_timestamp >= fecha_inicio)
    if taller:
        q = q.filter(Incidente.taller_actual_id == taller.id_taller)

    total = q.count()
    finalizados = db.query(Incidente).filter(
        Incidente.fecha_creacion_timestamp >= fecha_inicio,
        Incidente.estado_enum.in_([EstadoIncidente.atendido, EstadoIncidente.finalizado])
    ).count() if not taller else q.filter(
        Incidente.estado_enum.in_([EstadoIncidente.atendido, EstadoIncidente.finalizado])
    ).count()

    q_pagos = db.query(Pago).filter(Pago.fecha_pago_timestamp >= fecha_inicio)
    ingresos = float(db.query(func.coalesce(func.sum(Pago.monto_total_decimal), 0))
                     .filter(Pago.fecha_pago_timestamp >= fecha_inicio).scalar())

    tecnicos = db.query(Tecnico)
    if taller:
        tecnicos = tecnicos.filter(Tecnico.taller_id == taller.id_taller)
    total_tec = tecnicos.count()
    disp_tec = tecnicos.filter(Tecnico.disponible_boolean == True).count()

    return {
        "tipo": "general",
        "titulo": "Resumen General",
        "total_incidentes": total,
        "finalizados": finalizados,
        "tasa_exito": round(finalizados / total * 100, 1) if total > 0 else 0.0,
        "ingresos_totales_bs": round(ingresos, 2),
        "tecnicos_disponibles": disp_tec,
        "total_tecnicos": total_tec,
        "filas": [],
        "columnas": []
    }


def _recopilar_datos(db: Session, tipo: str, periodo_dias: int, user: Usuario) -> dict:
    """Centraliza la llamada al recopilador correcto según tipo detectado"""
    fecha_inicio = datetime.now() - timedelta(days=periodo_dias)
    if tipo == "comisiones":
        datos = _datos_comisiones(db, fecha_inicio, user)
    elif tipo == "talleres":
        datos = _datos_talleres(db, fecha_inicio, user)
    elif tipo == "tecnicos":
        datos = _datos_tecnicos(db, fecha_inicio, user)
    elif tipo == "clientes":
        datos = _datos_clientes(db, fecha_inicio, user)
    else:
        datos = _datos_general(db, fecha_inicio, user)

    datos["periodo_dias"] = periodo_dias
    datos["fecha_inicio"] = fecha_inicio.strftime("%Y-%m-%d")
    datos["fecha_fin"] = datetime.now().strftime("%Y-%m-%d")
    return datos


# ===================================================================
# ENDPOINT: GENERAR POR TEXTO - #Ciclo5 CU24
# 1. Detecta tipo y período por keywords (sin IA)
# 2. Consulta BD con datos reales
# 3. Devuelve tabla estructurada — SIN narrativa IA
# ===================================================================
# Descripción: Analiza una frase escrita, detecta el reporte deseado y lo genera en una tabla
# Ciclo: Ciclo 5
# CU: CU24
@router.post("/generar", response_model=ReporteResponse)
def generar_reporte_texto(
    datos: ReporteRequest,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    # Detectar tipo y período por keywords - #Ciclo5 CU24
    deteccion = _detectar_tipo_y_periodo(datos.prompt)
    tipo = deteccion["tipo_reporte"]
    periodo = deteccion["periodo_dias"]

    # Consultar BD con datos reales - #Ciclo5 CU24
    metricas = _recopilar_datos(db, tipo, periodo, current_user)

    return ReporteResponse(
        reporte_markdown="",          # Sin narrativa IA — los datos están en datos_periodo
        prompt_procesado=datos.prompt,
        datos_periodo=metricas
    )


# ===================================================================
# ENDPOINT: GENERAR POR VOZ - #Ciclo5 CU24
# 1. Whisper transcribe el audio a texto
# 2. Detecta tipo y período por keywords del texto transcrito
# 3. Consulta BD y devuelve tabla real
# ===================================================================
@router.post("/voz", response_model=ReporteResponse)
def generar_reporte_voz(
    datos: ReporteVozRequest,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    # Decodificar audio - #Ciclo5 CU24
    try:
        audio_b64 = datos.audio_base64
        if "," in audio_b64:
            audio_b64 = audio_b64.split(",")[1]
        audio_bytes = base64.b64decode(audio_b64)
    except Exception:
        raise HTTPException(status_code=400, detail="Audio base64 inválido.")

    # Whisper transcribe — ÚNICA llamada a IA - #Ciclo5 CU24
    prompt_transcrito = _transcribir_audio(audio_bytes)

    # Detectar tipo y período por keywords del texto transcrito
    deteccion = _detectar_tipo_y_periodo(prompt_transcrito)
    tipo = deteccion["tipo_reporte"]
    periodo = deteccion["periodo_dias"]

    # Consultar BD con datos reales
    metricas = _recopilar_datos(db, tipo, periodo, current_user)

    return ReporteResponse(
        reporte_markdown="",           # Sin narrativa IA
        prompt_procesado=prompt_transcrito,
        datos_periodo=metricas
    )
