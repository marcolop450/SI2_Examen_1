# ============================================================
# CU21 — Bitácora de Trazabilidad del Incidente
# Registro inmutable de todos los eventos de una emergencia
# ============================================================
from sqlalchemy import Column, Integer, String, Text, TIMESTAMP, ForeignKey, func
from app.database import Base


class BitacoraIncidente(Base):
    __tablename__ = "bitacora_incidente"

    id_bitacora  = Column(Integer, primary_key=True, index=True)
    incidente_id = Column(Integer, ForeignKey("incidentes.id_incidente", ondelete="CASCADE"))
    evento       = Column(String(80), nullable=False)
    # Eventos posibles:
    # CREACION, TALLER_ACEPTO, TALLER_RECHAZO, COTIZACION_ENVIADA,
    # COTIZACION_ACEPTADA, TECNICO_ASIGNADO, TECNICO_EN_CAMINO,
    # SERVICIO_INICIADO, SERVICIO_FINALIZADO, PAGO_COMPLETADO,
    # EXCEPCION, CANCELADO
    descripcion  = Column(Text, nullable=True)
    usuario_id   = Column(Integer, ForeignKey("usuarios.id_usuario"), nullable=True)
    timestamp    = Column(TIMESTAMP, server_default=func.now())