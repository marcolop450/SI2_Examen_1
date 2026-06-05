# ============================================================
# Router del Panel de KPIs y Analítica Operacional - Ciclo 5 - CU22
# Dashboard de métricas para admin (global) y taller (propio)
# ============================================================

import os
from datetime import datetime, timedelta
from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func, extract, desc

from app.database import get_db
from app.models.incidente import Incidente, EstadoIncidente, HistorialEstado
from app.models.pago import Pago
from app.models.tecnico import Tecnico
from app.models.taller import Taller
from app.models.usuario import Usuario, TipoRol
from app.routers.auth import get_current_user
from app.schemas.kpi import KpiResumen, IncidentesPorMes, DistribucionEstado, DistribucionPrioridad, TallerRanking

# Importar modelo de calificaciones si existe - Ciclo 5 - CU22
try:
    from app.models.calificacion import Calificacion
except ImportError:
    Calificacion = None

router = APIRouter(prefix="/kpis", tags=["CU22 - Panel de KPIs"])

# Nombres de meses en español - Ciclo 5 - CU22
MESES_ES = {1: "Ene", 2: "Feb", 3: "Mar", 4: "Abr", 5: "May", 6: "Jun",
            7: "Jul", 8: "Ago", 9: "Sep", 10: "Oct", 11: "Nov", 12: "Dic"}

# Estados considerados activos - Ciclo 5 - CU22
ESTADOS_ACTIVOS = [
    EstadoIncidente.pendiente, EstadoIncidente.en_proceso,
    EstadoIncidente.buscando_taller, EstadoIncidente.taller_asignado,
    EstadoIncidente.en_camino, EstadoIncidente.en_atencion
]
# Estados considerados finalizados - Ciclo 5 - CU22
ESTADOS_FINALIZADOS = [EstadoIncidente.atendido, EstadoIncidente.finalizado]


def _get_taller_usuario(db: Session, user: Usuario):
    """Obtiene el taller del usuario si es rol taller - Ciclo 5 - CU22"""
    if user.rol == TipoRol.admin:
        return None  # Admin ve todo
    taller = db.query(Taller).filter(Taller.dueño_id == user.id_usuario).first()
    return taller


# ===================================================================
# CU22: RESUMEN DE KPIs PRINCIPALES - Ciclo 5 - CU22
# ===================================================================
@router.get("/resumen", response_model=KpiResumen)
def obtener_resumen_kpis(
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    taller = _get_taller_usuario(db, current_user)

    # Base query filtrada por taller si aplica - Ciclo 5 - CU22
    q_incidentes = db.query(Incidente)
    q_pagos = db.query(Pago)
    q_tecnicos = db.query(Tecnico)

    if taller:
        q_incidentes = q_incidentes.filter(Incidente.taller_actual_id == taller.id_taller)
        q_pagos = q_pagos.filter(Pago.dueño_taller_id == current_user.id_usuario)
        q_tecnicos = q_tecnicos.filter(Tecnico.taller_id == taller.id_taller)

    total = q_incidentes.count()
    activos = q_incidentes.filter(Incidente.estado_enum.in_(ESTADOS_ACTIVOS)).count()
    finalizados = q_incidentes.filter(Incidente.estado_enum.in_(ESTADOS_FINALIZADOS)).count()
    tasa = round((finalizados / total * 100), 1) if total > 0 else 0.0

    # Ingresos totales - Ciclo 5 - CU22
    ingresos = q_pagos.with_entities(func.coalesce(func.sum(Pago.monto_total_decimal), 0)).scalar()

    # Técnicos - Ciclo 5 - CU22
    tec_total = q_tecnicos.count()
    tec_disponibles = q_tecnicos.filter(Tecnico.disponible_boolean == True).count()

    # Calificación promedio - Ciclo 5 - CU22
    calif_promedio = 0.0
    if Calificacion is not None:
        q_calif = db.query(func.avg(Calificacion.puntuacion))
        if taller:
            q_calif = q_calif.filter(Calificacion.taller_id == taller.id_taller)
        avg_val = q_calif.scalar()
        calif_promedio = round(float(avg_val), 1) if avg_val else 0.0

    # Tiempo promedio de atención en minutos - Ciclo 5 - CU22
    tiempo_promedio = 0.0
    inc_finalizados = q_incidentes.filter(
        Incidente.estado_enum.in_(ESTADOS_FINALIZADOS)
    ).all()
    if inc_finalizados:
        tiempos = []
        for inc in inc_finalizados:
            ultimo = db.query(HistorialEstado).filter(
                HistorialEstado.incidente_id == inc.id_incidente,
                HistorialEstado.estado_enum.in_(ESTADOS_FINALIZADOS)
            ).order_by(HistorialEstado.fecha_hora_timestamp.desc()).first()
            if ultimo and inc.fecha_creacion_timestamp:
                diff = (ultimo.fecha_hora_timestamp - inc.fecha_creacion_timestamp).total_seconds() / 60
                if diff > 0:
                    tiempos.append(diff)
        tiempo_promedio = round(sum(tiempos) / len(tiempos), 1) if tiempos else 0.0

    return KpiResumen(
        total_incidentes=total,
        incidentes_activos=activos,
        incidentes_finalizados=finalizados,
        tasa_exito=tasa,
        tiempo_promedio_atencion_min=tiempo_promedio,
        ingresos_totales=float(ingresos),
        calificacion_promedio=calif_promedio,
        tecnicos_disponibles=tec_disponibles,
        tecnicos_total=tec_total
    )


# ===================================================================
# CU22: INCIDENTES POR MES (últimos 6 meses) - Ciclo 5 - CU22
# ===================================================================
@router.get("/incidentes-por-mes", response_model=List[IncidentesPorMes])
def incidentes_por_mes(
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    taller = _get_taller_usuario(db, current_user)
    hace_6_meses = datetime.now() - timedelta(days=180)

    q = db.query(
        extract('year', Incidente.fecha_creacion_timestamp).label('anio'),
        extract('month', Incidente.fecha_creacion_timestamp).label('mes'),
        func.count(Incidente.id_incidente).label('total')
    ).filter(Incidente.fecha_creacion_timestamp >= hace_6_meses)

    if taller:
        q = q.filter(Incidente.taller_actual_id == taller.id_taller)

    q = q.group_by('anio', 'mes').order_by('anio', 'mes')
    resultados = q.all()

    return [
        IncidentesPorMes(
            mes=f"{MESES_ES.get(int(r.mes), '?')} {int(r.anio)}",
            total=r.total
        ) for r in resultados
    ]


# ===================================================================
# CU22: DISTRIBUCIÓN POR ESTADO - Ciclo 5 - CU22
# ===================================================================
@router.get("/por-estado", response_model=List[DistribucionEstado])
def distribucion_por_estado(
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    taller = _get_taller_usuario(db, current_user)

    q = db.query(
        Incidente.estado_enum,
        func.count(Incidente.id_incidente).label('total')
    )
    if taller:
        q = q.filter(Incidente.taller_actual_id == taller.id_taller)

    q = q.group_by(Incidente.estado_enum)
    resultados = q.all()

    total_general = sum(r.total for r in resultados) or 1
    return [
        DistribucionEstado(
            estado=r.estado_enum.value if hasattr(r.estado_enum, 'value') else str(r.estado_enum),
            total=r.total,
            porcentaje=round(r.total / total_general * 100, 1)
        ) for r in resultados
    ]


# ===================================================================
# CU22: DISTRIBUCIÓN POR PRIORIDAD - Ciclo 5 - CU22
# ===================================================================
@router.get("/por-prioridad", response_model=List[DistribucionPrioridad])
def distribucion_por_prioridad(
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    taller = _get_taller_usuario(db, current_user)

    q = db.query(
        Incidente.prioridad_enum,
        func.count(Incidente.id_incidente).label('total')
    )
    if taller:
        q = q.filter(Incidente.taller_actual_id == taller.id_taller)

    q = q.group_by(Incidente.prioridad_enum)
    resultados = q.all()

    return [
        DistribucionPrioridad(
            prioridad=r.prioridad_enum.value if hasattr(r.prioridad_enum, 'value') else str(r.prioridad_enum),
            total=r.total
        ) for r in resultados
    ]


# ===================================================================
# CU22: RANKING DE TALLERES (solo admin) - Ciclo 5 - CU22
# ===================================================================
@router.get("/talleres-ranking", response_model=List[TallerRanking])
def ranking_talleres(
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    talleres = db.query(Taller).all()
    ranking = []

    for t in talleres:
        servicios = db.query(Incidente).filter(
            Incidente.taller_actual_id == t.id_taller,
            Incidente.estado_enum.in_(ESTADOS_FINALIZADOS)
        ).count()

        calif_prom = 0.0
        if Calificacion is not None:
            avg_val = db.query(func.avg(Calificacion.puntuacion)).filter(
                Calificacion.taller_id == t.id_taller
            ).scalar()
            calif_prom = round(float(avg_val), 1) if avg_val else 0.0

        ranking.append(TallerRanking(
            taller_id=t.id_taller,
            nombre=t.nombre,
            servicios_completados=servicios,
            calificacion_promedio=calif_prom
        ))

    # Ordenar por servicios completados DESC - Ciclo 5 - CU22
    ranking.sort(key=lambda x: x.servicios_completados, reverse=True)
    return ranking[:10]


# ===================================================================
# CU22: TIEMPO PROMEDIO DE RESPUESTA - Ciclo 5 - CU22
# ===================================================================
@router.get("/tiempo-respuesta")
def tiempo_respuesta(
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    taller = _get_taller_usuario(db, current_user)

    q = db.query(Incidente).filter(
        Incidente.estado_enum.in_(ESTADOS_FINALIZADOS)
    )
    if taller:
        q = q.filter(Incidente.taller_actual_id == taller.id_taller)

    incidentes = q.all()
    tiempos = []

    for inc in incidentes:
        # Buscar primer estado en_proceso - Ciclo 5 - CU22
        primer_proceso = db.query(HistorialEstado).filter(
            HistorialEstado.incidente_id == inc.id_incidente,
            HistorialEstado.estado_enum == EstadoIncidente.en_proceso
        ).order_by(HistorialEstado.fecha_hora_timestamp.asc()).first()

        if primer_proceso and inc.fecha_creacion_timestamp:
            diff = (primer_proceso.fecha_hora_timestamp - inc.fecha_creacion_timestamp).total_seconds() / 60
            if diff > 0:
                tiempos.append(diff)

    avg_min = round(sum(tiempos) / len(tiempos), 1) if tiempos else 0.0
    return {"avg_minutos": avg_min}


# ===================================================================
# #Ciclo5 CU22 TIEMPO PROMEDIO DE ASIGNACIÓN - Enunciado obligatorio
# Tiempo entre reporte y taller asignado
# ===================================================================
@router.get("/tiempo-asignacion")
def tiempo_asignacion(
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    taller = _get_taller_usuario(db, current_user)
    q = db.query(Incidente)
    if taller:
        q = q.filter(Incidente.taller_actual_id == taller.id_taller)
    incidentes = q.all()
    tiempos = []

    for inc in incidentes:
        # #Ciclo5 CU22 Buscar primer estado taller_asignado
        asignado = db.query(HistorialEstado).filter(
            HistorialEstado.incidente_id == inc.id_incidente,
            HistorialEstado.estado_enum == EstadoIncidente.taller_asignado
        ).order_by(HistorialEstado.fecha_hora_timestamp.asc()).first()
        if asignado and inc.fecha_creacion_timestamp:
            diff = (asignado.fecha_hora_timestamp - inc.fecha_creacion_timestamp).total_seconds() / 60
            if diff > 0:
                tiempos.append(diff)

    avg_min = round(sum(tiempos) / len(tiempos), 1) if tiempos else 0.0
    return {"avg_minutos": avg_min, "total_medidos": len(tiempos)}


# ===================================================================
# #Ciclo5 CU22 TIEMPO PROMEDIO DE LLEGADA - Enunciado obligatorio
# Tiempo entre taller asignado y en_atencion (llegada del técnico)
# ===================================================================
@router.get("/tiempo-llegada")
def tiempo_llegada(
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    taller = _get_taller_usuario(db, current_user)
    q = db.query(Incidente)
    if taller:
        q = q.filter(Incidente.taller_actual_id == taller.id_taller)
    incidentes = q.all()
    tiempos = []

    for inc in incidentes:
        asignado = db.query(HistorialEstado).filter(
            HistorialEstado.incidente_id == inc.id_incidente,
            HistorialEstado.estado_enum == EstadoIncidente.taller_asignado
        ).order_by(HistorialEstado.fecha_hora_timestamp.asc()).first()
        # #Ciclo5 CU22 Buscar primer estado en_atencion (llegada)
        llegada = db.query(HistorialEstado).filter(
            HistorialEstado.incidente_id == inc.id_incidente,
            HistorialEstado.estado_enum == EstadoIncidente.en_atencion
        ).order_by(HistorialEstado.fecha_hora_timestamp.asc()).first()
        if asignado and llegada:
            diff = (llegada.fecha_hora_timestamp - asignado.fecha_hora_timestamp).total_seconds() / 60
            if diff > 0:
                tiempos.append(diff)

    avg_min = round(sum(tiempos) / len(tiempos), 1) if tiempos else 0.0
    return {"avg_minutos": avg_min, "total_medidos": len(tiempos)}


# ===================================================================
# #Ciclo5 CU22 INCIDENTES POR TIPO - Enunciado obligatorio
# Batería, llanta, motor, choque, otros (de clasificación IA)
# ===================================================================
@router.get("/por-tipo")
def incidentes_por_tipo(
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    from app.models.incidente import EvidenciaIA
    import re

    taller = _get_taller_usuario(db, current_user)
    q = db.query(Incidente)
    if taller:
        q = q.filter(Incidente.taller_actual_id == taller.id_taller)
    incidentes = q.all()

    # #Ciclo5 CU22 Extraer tipo de clasificación IA [TIPO]
    tipos_count: dict = {}
    for inc in incidentes:
        evidencia = db.query(EvidenciaIA).filter(
            EvidenciaIA.incidente_id == inc.id_incidente,
            EvidenciaIA.clasificacion_ia_texto.isnot(None)
        ).first()
        tipo = "otros"
        if evidencia and evidencia.clasificacion_ia_texto:
            match = re.search(r'\[(\w+)\]', evidencia.clasificacion_ia_texto)
            if match:
                tipo = match.group(1).lower()
        tipos_count[tipo] = tipos_count.get(tipo, 0) + 1

    resultado = [{"tipo": t, "total": c} for t, c in sorted(tipos_count.items(), key=lambda x: x[1], reverse=True)]
    return resultado


# ===================================================================
# #Ciclo5 CU22 ZONAS CON MÁS INCIDENTES - Enunciado obligatorio
# Agrupa por coordenadas redondeadas para simular clusters
# ===================================================================
@router.get("/zonas-incidentes")
def zonas_incidentes(
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    taller = _get_taller_usuario(db, current_user)
    q = db.query(Incidente).filter(
        Incidente.latitud_emergencia.isnot(None),
        Incidente.longitud_emergencia.isnot(None)
    )
    if taller:
        q = q.filter(Incidente.taller_actual_id == taller.id_taller)
    incidentes = q.all()

    # #Ciclo5 CU22 Redondear coordenadas a 2 decimales para agrupar zonas
    zonas: dict = {}
    for inc in incidentes:
        lat_r = round(float(inc.latitud_emergencia), 2)
        lng_r = round(float(inc.longitud_emergencia), 2)
        key = f"{lat_r},{lng_r}"
        if key not in zonas:
            zonas[key] = {"lat": lat_r, "lng": lng_r, "total": 0, "incidentes_ids": []}
        zonas[key]["total"] += 1
        zonas[key]["incidentes_ids"].append(inc.id_incidente)

    resultado = sorted(zonas.values(), key=lambda x: x["total"], reverse=True)
    # #Ciclo5 CU22 Limitar a top 20 zonas
    return resultado[:20]


# ===================================================================
# #Ciclo5 CU22 NIVEL DE CUMPLIMIENTO SLA - Enunciado obligatorio
# % de incidentes atendidos dentro del tiempo esperado (60 min)
# ===================================================================
@router.get("/sla")
def cumplimiento_sla(
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    SLA_MINUTOS = 60  # #Ciclo5 CU22 SLA objetivo: 60 minutos

    taller = _get_taller_usuario(db, current_user)
    q = db.query(Incidente).filter(
        Incidente.estado_enum.in_(ESTADOS_FINALIZADOS)
    )
    if taller:
        q = q.filter(Incidente.taller_actual_id == taller.id_taller)
    finalizados = q.all()

    total = len(finalizados)
    dentro_sla = 0
    fuera_sla = 0
    tiempos_detalle = []

    for inc in finalizados:
        # #Ciclo5 CU22 Calcular tiempo total de resolución
        ultimo = db.query(HistorialEstado).filter(
            HistorialEstado.incidente_id == inc.id_incidente,
            HistorialEstado.estado_enum.in_(ESTADOS_FINALIZADOS)
        ).order_by(HistorialEstado.fecha_hora_timestamp.desc()).first()
        if ultimo and inc.fecha_creacion_timestamp:
            diff = (ultimo.fecha_hora_timestamp - inc.fecha_creacion_timestamp).total_seconds() / 60
            if diff <= SLA_MINUTOS:
                dentro_sla += 1
            else:
                fuera_sla += 1
            tiempos_detalle.append(round(diff, 1))

    porcentaje = round(dentro_sla / total * 100, 1) if total > 0 else 0.0
    return {
        "sla_objetivo_min": SLA_MINUTOS,
        "total_finalizados": total,
        "dentro_sla": dentro_sla,
        "fuera_sla": fuera_sla,
        "porcentaje_cumplimiento": porcentaje,
        "tiempo_promedio_min": round(sum(tiempos_detalle) / len(tiempos_detalle), 1) if tiempos_detalle else 0.0
    }
