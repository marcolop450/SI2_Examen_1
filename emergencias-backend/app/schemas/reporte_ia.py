# ============================================================
# Esquemas de Reportes Inteligentes con IA - Ciclo 5 - CU24
# Permite generar reportes ejecutivos por texto o voz
# ============================================================
from pydantic import BaseModel
from typing import Optional

class ReporteRequest(BaseModel):
    """Solicitud de reporte por texto - Ciclo 5 - CU24"""
    prompt: str
    periodo_dias: int = 30

class ReporteVozRequest(BaseModel):
    """Solicitud de reporte por audio (base64) - Ciclo 5 - CU24"""
    audio_base64: str
    periodo_dias: int = 30

class ReporteResponse(BaseModel):
    """Respuesta del reporte generado por IA - Ciclo 5 - CU24"""
    reporte_markdown: str
    prompt_procesado: str
    datos_periodo: dict = {}
