# ============================================================
# Router de Reportes Inteligentes por Voz y Texto - Ciclo 5 - CU24
# Genera reportes ejecutivos usando Groq IA con datos reales de la BD
# ============================================================

import os
import json
import base64
import requests
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
from app.routers.auth import get_current_user
from app.schemas.reporte_ia import ReporteRequest, ReporteVozRequest, ReporteResponse

# Importar calificaciones si existe - Ciclo 5 - CU24
try:
    from app.models.calificacion import Calificacion
except ImportError:
    Calificacion = None

router = APIRouter(prefix="/reportes-ia", tags=["CU24 - Reportes Inteligentes IA"])

# API Key de Groq (misma que usa el proyecto) - Ciclo 5 - CU24
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")


def _recopilar_datos_periodo(db: Session, periodo_dias: int, user: Usuario) -> dict:
    """Recopila métricas reales de la BD para el periodo especificado - Ciclo 5 - CU24"""
    fecha_inicio = datetime.now() - timedelta(days=periodo_dias)

    # Determinar filtro por taller si no es admin - Ciclo 5 - CU24
    taller = None
    if user.rol != TipoRol.admin:
        taller = db.query(Taller).filter(Taller.dueño_id == user.id_usuario).first()

    # Incidentes del periodo - Ciclo 5 - CU24
    q_inc = db.query(Incidente).filter(Incidente.fecha_creacion_timestamp >= fecha_inicio)
    if taller:
        q_inc = q_inc.filter(Incidente.taller_actual_id == taller.id_taller)

    total_incidentes = q_inc.count()
    pendientes = q_inc.filter(Incidente.estado_enum == EstadoIncidente.pendiente).count()
    en_proceso = q_inc.filter(Incidente.estado_enum == EstadoIncidente.en_proceso).count()
    finalizados = q_inc.filter(Incidente.estado_enum.in_([
        EstadoIncidente.atendido, EstadoIncidente.finalizado
    ])).count()
    cancelados = q_inc.filter(Incidente.estado_enum == EstadoIncidente.cancelado).count()

    # Pagos del periodo - Ciclo 5 - CU24
    q_pagos = db.query(Pago).filter(Pago.fecha_pago_timestamp >= fecha_inicio)
    if taller:
        q_pagos = q_pagos.filter(Pago.dueño_taller_id == user.id_usuario)
    ingresos = float(q_pagos.with_entities(func.coalesce(func.sum(Pago.monto_total_decimal), 0)).scalar())
    total_pagos = q_pagos.count()

    # Top talleres - Ciclo 5 - CU24
    top_talleres = []
    if user.rol == TipoRol.admin:
        talleres_all = db.query(Taller).all()
        for t in talleres_all:
            count = db.query(Incidente).filter(
                Incidente.taller_actual_id == t.id_taller,
                Incidente.estado_enum.in_([EstadoIncidente.atendido, EstadoIncidente.finalizado]),
                Incidente.fecha_creacion_timestamp >= fecha_inicio
            ).count()
            if count > 0:
                top_talleres.append({"nombre": t.nombre, "servicios": count})
        top_talleres.sort(key=lambda x: x["servicios"], reverse=True)
        top_talleres = top_talleres[:5]

    # Calificación promedio - Ciclo 5 - CU24
    calif_promedio = 0.0
    if Calificacion is not None:
        q_calif = db.query(func.avg(Calificacion.puntuacion))
        if taller:
            q_calif = q_calif.filter(Calificacion.taller_id == taller.id_taller)
        avg_val = q_calif.scalar()
        calif_promedio = round(float(avg_val), 1) if avg_val else 0.0

    # Excepciones del periodo - Ciclo 5 - CU24
    total_excepciones = db.query(ExcepcionOperativa).filter(
        ExcepcionOperativa.timestamp >= fecha_inicio
    ).count()

    # Técnicos - Ciclo 5 - CU24
    q_tec = db.query(Tecnico)
    if taller:
        q_tec = q_tec.filter(Tecnico.taller_id == taller.id_taller)
    total_tecnicos = q_tec.count()
    tec_disponibles = q_tec.filter(Tecnico.disponible_boolean == True).count()

    return {
        "periodo_dias": periodo_dias,
        "fecha_inicio": fecha_inicio.strftime("%Y-%m-%d"),
        "fecha_fin": datetime.now().strftime("%Y-%m-%d"),
        "total_incidentes": total_incidentes,
        "pendientes": pendientes,
        "en_proceso": en_proceso,
        "finalizados": finalizados,
        "cancelados": cancelados,
        "tasa_exito": round(finalizados / total_incidentes * 100, 1) if total_incidentes > 0 else 0,
        "ingresos_totales_bs": ingresos,
        "total_pagos": total_pagos,
        "calificacion_promedio": calif_promedio,
        "total_excepciones": total_excepciones,
        "total_tecnicos": total_tecnicos,
        "tecnicos_disponibles": tec_disponibles,
        "top_talleres": top_talleres
    }


def _generar_reporte_con_groq(prompt: str, datos: dict) -> str:
    """Envía datos reales a Groq para generar reporte ejecutivo - Ciclo 5 - CU24"""
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"}

    # Construir contexto con datos reales - Ciclo 5 - CU24
    contexto = f"""
DATOS REALES DE LA PLATAFORMA (Periodo: {datos['fecha_inicio']} al {datos['fecha_fin']}):
- Total incidentes: {datos['total_incidentes']}
- Pendientes: {datos['pendientes']} | En proceso: {datos['en_proceso']} | Finalizados: {datos['finalizados']} | Cancelados: {datos['cancelados']}
- Tasa de éxito: {datos['tasa_exito']}%
- Ingresos totales: {datos['ingresos_totales_bs']} Bs.
- Total pagos registrados: {datos['total_pagos']}
- Calificación promedio: {datos['calificacion_promedio']}/5
- Excepciones operativas: {datos['total_excepciones']}
- Técnicos: {datos['tecnicos_disponibles']} disponibles de {datos['total_tecnicos']} totales
"""
    if datos.get("top_talleres"):
        contexto += "- Top talleres:\n"
        for i, t in enumerate(datos["top_talleres"], 1):
            contexto += f"  {i}. {t['nombre']}: {t['servicios']} servicios\n"

    sistema = (
        "Eres un analista de datos de una plataforma de emergencias vehiculares. "
        "Genera un reporte ejecutivo profesional basado en los datos proporcionados. "
        "Incluye: resumen ejecutivo, métricas clave, tendencias observadas, y recomendaciones. "
        "Responde en español. Usa formato de texto plano bien estructurado con secciones claras."
    )

    body = {
        "model": "llama-3.3-70b-versatile",
        "messages": [
            {"role": "system", "content": sistema},
            {"role": "user", "content": f"Solicitud del usuario: \"{prompt}\"\n\n{contexto}"}
        ],
        "temperature": 0.3,
        "max_tokens": 2000
    }

    try:
        res = requests.post(url, headers=headers, json=body, timeout=30)
        if res.status_code == 200:
            return res.json()["choices"][0]["message"]["content"]
        else:
            print(f"Error Groq Reportes: {res.text}")
    except Exception as e:
        print(f"Excepción Groq Reportes: {e}")

    # Fallback: reporte básico sin IA - Ciclo 5 - CU24
    return (
        f"REPORTE OPERACIONAL\n"
        f"Periodo: {datos['fecha_inicio']} al {datos['fecha_fin']}\n\n"
        f"MÉTRICAS CLAVE:\n"
        f"• Total incidentes: {datos['total_incidentes']}\n"
        f"• Finalizados: {datos['finalizados']} ({datos['tasa_exito']}% éxito)\n"
        f"• Ingresos: {datos['ingresos_totales_bs']} Bs.\n"
        f"• Calificación promedio: {datos['calificacion_promedio']}/5\n"
        f"• Excepciones: {datos['total_excepciones']}\n\n"
        f"(Reporte generado sin IA — el servicio de Groq no respondió)"
    )


def _transcribir_audio_reporte(audio_bytes: bytes) -> str:
    """Transcribe audio a texto usando Groq Whisper - Ciclo 5 - CU24"""
    url = "https://api.groq.com/openai/v1/audio/transcriptions"
    headers = {"Authorization": f"Bearer {GROQ_API_KEY}"}
    files = {"file": ("audio.m4a", audio_bytes, "audio/m4a")}
    data = {"model": "whisper-large-v3", "response_format": "json"}
    try:
        res = requests.post(url, headers=headers, files=files, data=data, timeout=15)
        if res.status_code == 200:
            return res.json().get("text", "").strip() or "Audio inaudible."
    except Exception as e:
        print(f"Error transcripción reporte: {e}")
    return "No se pudo transcribir el audio."


# ===================================================================
# CU24: GENERAR REPORTE POR TEXTO - Ciclo 5 - CU24
# ===================================================================
@router.post("/generar", response_model=ReporteResponse)
def generar_reporte_texto(
    datos: ReporteRequest,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    # Recopilar datos reales de la BD - Ciclo 5 - CU24
    metricas = _recopilar_datos_periodo(db, datos.periodo_dias, current_user)

    # Generar reporte con IA - Ciclo 5 - CU24
    reporte = _generar_reporte_con_groq(datos.prompt, metricas)

    return ReporteResponse(
        reporte_markdown=reporte,
        prompt_procesado=datos.prompt,
        datos_periodo=metricas
    )


# ===================================================================
# CU24: GENERAR REPORTE POR VOZ - Ciclo 5 - CU24
# Recibe audio base64, transcribe, y genera reporte
# ===================================================================
@router.post("/voz", response_model=ReporteResponse)
def generar_reporte_voz(
    datos: ReporteVozRequest,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    # Decodificar audio base64 - Ciclo 5 - CU24
    try:
        audio_b64 = datos.audio_base64
        if "," in audio_b64:
            audio_b64 = audio_b64.split(",")[1]
        audio_bytes = base64.b64decode(audio_b64)
    except Exception:
        raise HTTPException(status_code=400, detail="Audio base64 inválido.")

    # Transcribir con Whisper - Ciclo 5 - CU24
    prompt_transcrito = _transcribir_audio_reporte(audio_bytes)

    # Recopilar datos y generar reporte - Ciclo 5 - CU24
    metricas = _recopilar_datos_periodo(db, datos.periodo_dias, current_user)
    reporte = _generar_reporte_con_groq(prompt_transcrito, metricas)

    return ReporteResponse(
        reporte_markdown=reporte,
        prompt_procesado=prompt_transcrito,
        datos_periodo=metricas
    )
