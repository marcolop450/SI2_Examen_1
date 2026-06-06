# ============================================================
# models/__init__.py
#
# Importación centralizada para registrar todos los modelos en Base.metadata
# y resolver relaciones por cadena en tiempo de ejecución.
# ============================================================

from app.models.saas import Plan, Tenant, Suscripcion
from app.models.usuario import Usuario, TipoRol
from app.models.taller import Taller
from app.models.tecnico import Tecnico
from app.models.incidente import (
    Incidente,
    EvidenciaIA,
    HistorialEstado,
    EstadoIncidente,
    PrioridadIncidente,
    TipoEvidencia,
)
from app.models.pago import Pago, MetodoPago
from app.models.bitacora import BitacoraIncidente
from app.models.cotizacion import Cotizacion
from app.models.excepcion import ExcepcionOperativa
from app.models.notificacion import Notificacion
from app.models.ruta_tecnico import RutaTecnico
from app.models.taller_rechazo import TallerRechazo
from app.models.vehiculo import Vehiculo
