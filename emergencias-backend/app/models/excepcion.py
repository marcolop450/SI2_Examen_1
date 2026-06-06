# ============================================================
# CU20 — Modelo de Excepciones Operativas
# Registra cancelaciones, llegada del seguro y casos mixtos
# ============================================================
from sqlalchemy import Column, Integer, String, Text, TIMESTAMP, DECIMAL, ForeignKey, func
from app.database import Base


class ExcepcionOperativa(Base):
    __tablename__ = "excepciones_operativas"

    id_excepcion        = Column(Integer, primary_key=True, index=True)
    incidente_id        = Column(Integer, ForeignKey("incidentes.id_incidente"), nullable=False)
    tipo_excepcion      = Column(String(50), nullable=False)
    # Valores: cancelacion_cliente | llego_seguro_primero | llegaron_ambos
    motivo              = Column(Text, nullable=True)
    compensacion_taller = Column(DECIMAL(10, 2), default=0.00)
    timestamp           = Column(TIMESTAMP, server_default=func.now())