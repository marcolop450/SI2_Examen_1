# ============================================================
# CU17 — CANAL DE COMUNICACIÓN EN TIEMPO REAL (WebSocket)
# Sala por incidente: cliente, taller y técnico conectados
# ============================================================

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.incidente import Incidente, EstadoIncidente
from app.models.ruta_tecnico import RutaTecnico
from typing import Dict, List
import json
from datetime import datetime

router = APIRouter(prefix="/ws", tags=["WebSocket - Tiempo Real"])

# ============================================================
# GESTOR DE SALAS — Una sala por incidente
# Cada sala tiene todos los clientes conectados (cliente, taller, técnico)
# ============================================================
class GestorSalas:
    def __init__(self):
        # Dict: incidente_id → lista de WebSockets conectados
        self.salas: Dict[int, List[WebSocket]] = {}

    async def conectar(self, ws: WebSocket, incidente_id: int):
        await ws.accept()
        if incidente_id not in self.salas:
            self.salas[incidente_id] = []
        self.salas[incidente_id].append(ws)

    def desconectar(self, ws: WebSocket, incidente_id: int):
        if incidente_id in self.salas:
            self.salas[incidente_id].remove(ws)
            if not self.salas[incidente_id]:
                del self.salas[incidente_id]

    async def broadcast(self, incidente_id: int, mensaje: dict):
        """Enviar mensaje a TODOS los conectados en la sala del incidente"""
        if incidente_id not in self.salas:
            return
        mensaje_json = json.dumps(mensaje, ensure_ascii=False, default=str)
        desconectados = []
        for ws in self.salas[incidente_id]:
            try:
                await ws.send_text(mensaje_json)
            except Exception:
                desconectados.append(ws)
        # Limpiar conexiones caídas
        for ws in desconectados:
            self.salas[incidente_id].remove(ws)

# Instancia global del gestor (una sola para toda la app)
gestor = GestorSalas()


# ============================================================
# ENDPOINT WEBSOCKET — Sala del incidente
# URL: ws://localhost:8000/ws/incidente/{incidente_id}
# ============================================================
# Descripción: Abre una conexión de socket bidireccional para seguimiento de incidentes en tiempo real
# Ciclo: Ciclo 4
# CU: CU17
@router.websocket("/incidente/{incidente_id}")
async def sala_incidente(
    ws: WebSocket,
    incidente_id: int,
    db: Session = Depends(get_db)
):
    # Verificar que el incidente existe antes de conectar
    incidente = db.query(Incidente).filter(
        Incidente.id_incidente == incidente_id
    ).first()

    if not incidente:
        await ws.close(code=4004)
        return

    # Conectar a la sala
    await gestor.conectar(ws, incidente_id)

    # Notificar a todos que alguien se conectó
    await gestor.broadcast(incidente_id, {
        "tipo": "conexion",
        "mensaje": "Nuevo participante conectado a la sala",
        "estado_actual": incidente.estado_enum.value,
        "timestamp": datetime.now().isoformat()
    })

    try:
        while True:
            # Recibir mensaje del cliente conectado
            data_raw = await ws.receive_text()
            data = json.loads(data_raw)
            tipo = data.get("tipo", "")

            # ------------------------------------------------
            # TIPO 1: ubicacion_tecnico
            # El técnico envía su GPS cada 5 segundos
            # ------------------------------------------------
            if tipo == "ubicacion_tecnico":
                lat = data.get("latitud")
                lng = data.get("longitud")

                if lat and lng:
                    # Guardar punto en la BD para la bitácora de ruta
                    punto = RutaTecnico(
                        incidente_id=incidente_id,
                        latitud=lat,
                        longitud=lng
                    )
                    db.add(punto)

                    # Actualizar coordenadas en el incidente
                    incidente.latitud_tecnico  = lat
                    incidente.longitud_tecnico = lng
                    db.commit()

                    # Retransmitir a cliente y taller en tiempo real
                    await gestor.broadcast(incidente_id, {
                        "tipo": "ubicacion_tecnico",
                        "latitud": lat,
                        "longitud": lng,
                        "eta_minutos": data.get("eta_minutos"),
                        "timestamp": datetime.now().isoformat()
                    })

            # ------------------------------------------------
            # TIPO 2: cambio_estado
            # Taller o técnico actualiza el estado del incidente
            # ------------------------------------------------
            elif tipo == "cambio_estado":
                nuevo_estado = data.get("estado")
                estados_validos = [e.value for e in EstadoIncidente]

                if nuevo_estado in estados_validos:
                    incidente.estado_enum = nuevo_estado
                    db.commit()

                    # Notificar a todos el nuevo estado
                    await gestor.broadcast(incidente_id, {
                        "tipo": "cambio_estado",
                        "estado": nuevo_estado,
                        "mensaje": data.get("mensaje", ""),
                        "timestamp": datetime.now().isoformat()
                    })

            # ------------------------------------------------
            # TIPO 3: ping — mantener conexión viva
            # ------------------------------------------------
            elif tipo == "ping":
                await ws.send_text(json.dumps({"tipo": "pong"}))

    except WebSocketDisconnect:
        gestor.desconectar(ws, incidente_id)
        await gestor.broadcast(incidente_id, {
            "tipo": "desconexion",
            "mensaje": "Un participante se desconectó",
            "timestamp": datetime.now().isoformat()
        })