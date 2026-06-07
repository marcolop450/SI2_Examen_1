# ============================================================
# Esquemas del Panel de KPIs y Analítica - Ciclo 5 - CU22
# Métricas operacionales para dashboard de admin y taller
# ============================================================
from pydantic import BaseModel
from typing import List

class KpiResumen(BaseModel):
    """KPIs principales del dashboard - Ciclo 5 - CU22"""
    total_incidentes: int = 0
    incidentes_activos: int = 0
    incidentes_finalizados: int = 0
    tasa_exito: float = 0.0
    tiempo_promedio_atencion_min: float = 0.0
    ingresos_totales: float = 0.0
    calificacion_promedio: float = 0.0
    tecnicos_disponibles: int = 0
    tecnicos_total: int = 0

class IncidentesPorMes(BaseModel):
    """Datos para gráfico de barras mensual - Ciclo 5 - CU22"""
    mes: str
    total: int = 0

class DistribucionEstado(BaseModel):
    """Datos para gráfico donut por estado - Ciclo 5 - CU22"""
    estado: str
    total: int = 0
    porcentaje: float = 0.0

class DistribucionPrioridad(BaseModel):
    """Distribución por nivel de prioridad - Ciclo 5 - CU22"""
    prioridad: str
    total: int = 0

class TallerRanking(BaseModel):
    """Ranking de talleres por rendimiento - Ciclo 5 - CU22"""
    taller_id: int
    nombre: str
    servicios_completados: int = 0
    calificacion_promedio: float = 0.0
    ingresos_totales: float = 0.0

