import { Component, OnInit, OnDestroy } from '@angular/core';
import { CommonModule } from '@angular/common';
import { HttpClient } from '@angular/common/http';
import { RouterModule } from '@angular/router'; // #Ciclo5 CU21 Para enlace a bitácora
import { DomSanitizer, SafeResourceUrl } from '@angular/platform-browser';

@Component({
  selector: 'app-cu9-monitoreo',
  standalone: true,
  imports: [CommonModule, RouterModule], // #Ciclo5 CU21 RouterModule para bitácora
  templateUrl: './cu9-monitoreo.html',
  styleUrls: ['./cu9-monitoreo.css']
})
export class Cu9Monitoreo implements OnInit, OnDestroy {
  serviciosActivos: any[] = [];
  cargando = true;

  // Diccionario para manejar múltiples conexiones WS simultáneas por ID de incidente
  private wsConnections: { [key: number]: WebSocket } = {};
  private pingInterval: any;

  constructor(
    private http: HttpClient,
    private sanitizer: DomSanitizer
  ) {}

  ngOnInit() {
    this.cargarSeguimientoInicial();
    this.iniciarPingWebSockets();
  }

  ngOnDestroy() {
    // Limpiar el intervalo y cerrar TODAS las conexiones WS al salir de la pantalla
    clearInterval(this.pingInterval);
    Object.values(this.wsConnections).forEach(ws => ws.close());
  }

  // =========================================================
  // 1. Carga inicial vía HTTP (Reemplaza el Polling de 10s)
  // =========================================================
  cargarSeguimientoInicial() {
    this.http.get<any[]>('http://localhost:8000/incidentes/en-proceso').subscribe({
      next: (data) => {
        this.serviciosActivos = data;
        this.cargando = false;
        
        // 2. Por cada servicio en proceso, abrimos su canal WebSocket
        this.serviciosActivos.forEach(servicio => {
          this.conectarWebSocket(servicio.id_incidente);
        });
      },
      error: (err) => {
        console.error('Error cargando monitoreo inicial:', err);
        this.cargando = false;
      }
    });
  }

  // =========================================================
  // 3. Lógica de WebSockets (Tiempo Real por Incidente)
  // =========================================================
  conectarWebSocket(incidenteId: number): void {
    // Evitar abrir una conexión si ya existe una activa para este incidente
    if (this.wsConnections[incidenteId]) return;

    const url = `ws://localhost:8000/ws/incidente/${incidenteId}`;
    const ws = new WebSocket(url);

    ws.onopen = () => console.log(`WS Conectado para incidente #${incidenteId}`);

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      // Buscar el índice del servicio que envió la actualización
      const index = this.serviciosActivos.findIndex(s => s.id_incidente === incidenteId);
      
      if (index === -1) return;

      // Reflejar la nueva ubicación del técnico en la vista
      if (data.tipo === 'ubicacion_tecnico') {
        this.serviciosActivos[index].latitud_tecnico = data.latitud;
        this.serviciosActivos[index].longitud_tecnico = data.longitud;
        this.serviciosActivos[index].eta_minutos = data.eta_minutos;
      }

      // Si el técnico cambia el estado desde la App Móvil
      if (data.tipo === 'cambio_estado') {
        this.serviciosActivos[index].estado_enum = data.estado;
        
        if (data.estado === 'finalizado') {
           // Si terminó, cerramos su conexión específica y recargamos la lista
           ws.close();
           delete this.wsConnections[incidenteId];
           this.cargarSeguimientoInicial(); 
        }
      }
    };

    ws.onerror = () => {
      console.error(`Error en WS incidente #${incidenteId}. Reconectando en 3s...`);
      setTimeout(() => this.conectarWebSocket(incidenteId), 3000);
    };

    ws.onclose = () => {
      // Solo intentar reconectar si el servicio sigue activo en nuestro arreglo
      const sigueActivo = this.serviciosActivos.some(s => s.id_incidente === incidenteId);
      if (sigueActivo) {
        setTimeout(() => this.conectarWebSocket(incidenteId), 3000);
      } else {
        delete this.wsConnections[incidenteId];
      }
    };

    // Guardar la conexión en el diccionario
    this.wsConnections[incidenteId] = ws;
  }

  // Mantiene vivos todos los WebSockets abiertos
  private iniciarPingWebSockets(): void {
    this.pingInterval = setInterval(() => {
      Object.values(this.wsConnections).forEach(ws => {
        if (ws.readyState === WebSocket.OPEN) {
          ws.send(JSON.stringify({ tipo: 'ping' }));
        }
      });
    }, 30000); // Cada 30 segundos
  }

  // =========================================================
  // Métodos de la Interfaz Web
  // =========================================================
  getMapaUrl(incidente: any): SafeResourceUrl {
    const latCli = incidente.latitud_emergencia;
    const lngCli = incidente.longitud_emergencia;
    const latTec = incidente.latitud_tecnico;
    const lngTec = incidente.longitud_tecnico;

    let url = '';
    
    // Corrección de sintaxis para URL embed de Google Maps
    if (latTec && lngTec) {
      url = `https://maps.google.com/maps?saddr=${latTec},${lngTec}&daddr=${latCli},${lngCli}&output=embed`;
    } else {
      url = `https://maps.google.com/maps?q=${latCli},${lngCli}&z=15&output=embed`;
    }
    
    return this.sanitizer.bypassSecurityTrustResourceUrl(url);
  }

  finalizarServicio(id: number) {
    if (!confirm('¿Confirmas que el servicio ha sido finalizado con éxito?')) return;

    this.http.put(`http://localhost:8000/incidentes/${id}/estado`, {
      estado_enum: 'atendido',
      comentario: 'Servicio cerrado desde panel web.'
    }).subscribe(() => {
      alert('Servicio finalizado. El técnico ahora está disponible.');
      
      // Matar la conexión WS de este incidente antes de recargar la lista
      if (this.wsConnections[id]) {
        this.wsConnections[id].close();
        delete this.wsConnections[id];
      }
      
      this.cargarSeguimientoInicial();
    });
  }
}