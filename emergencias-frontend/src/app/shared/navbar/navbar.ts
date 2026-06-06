import { Component, OnInit, HostListener, Output, EventEmitter, OnDestroy } from '@angular/core';
import { CommonModule } from '@angular/common';
import { NotificacionService } from '../../core/services/notificacion';
import { RouterModule } from '@angular/router';

@Component({
  selector: 'app-navbar',
  standalone: true,
  imports: [CommonModule, RouterModule],
  templateUrl: './navbar.html',
  styleUrls: ['./navbar.css']
})
export class NavbarComponent implements OnInit, OnDestroy {
  notificaciones: any[] = [];
  cantidadNoLeidas: number = 0;
  mostrarDropdown: boolean = false;
  nombreUsuario: string = ''; 
  rolUsuario: string = '';
  tenantId: string | null = null;
  
  private pollingInterval: any; // 🔥 Guardamos el vigilante para apagarlo si salimos

  @Output() onToggle = new EventEmitter<void>();

  constructor(private notifService: NotificacionService) {}

  ngOnInit(): void {
    this.nombreUsuario = localStorage.getItem('nombre') || 'Usuario';
    const rol = localStorage.getItem('rol') || 'taller';
    this.rolUsuario = rol.charAt(0).toUpperCase() + rol.slice(1);

    // --- DETECCIÓN DE SESIÓN CORPORATIVA ---
    this.tenantId = localStorage.getItem('tenant_id');

    this.actualizarContador();

    // 🔥 MAGIA: El vigilante silencioso (Polling cada 10 segundos)
    this.pollingInterval = setInterval(() => {
      this.revisarNuevasNotificaciones();
    }, 10000); 
  }

  ngOnDestroy(): void {
    // Apagamos el vigilante si el componente se destruye
    if (this.pollingInterval) {
      clearInterval(this.pollingInterval);
    }
  }

  // 🔥 1. Consulta silenciosa para la notificación PUSH de Windows
  revisarNuevasNotificaciones() {
    this.notifService.getNoLeidas().subscribe(res => {
      const nuevasNoLeidas = res.total_no_leidas;

      // Si el número nuevo es mayor al que teníamos, significa que llegó una emergencia
      if (nuevasNoLeidas > this.cantidadNoLeidas) {
        this.lanzarAlertaEscritorio(
          '¡Nueva Emergencia! 🚨', 
          'Un conductor acaba de solicitar auxilio en tu zona.'
        );
      }

      // Actualizamos el contador visual de la campanita
      this.cantidadNoLeidas = nuevasNoLeidas;
    });
  }

  // 🔥 2. Ejecutor de la Notificación de Windows
  lanzarAlertaEscritorio(titulo: string, mensaje: string) {
    if ('Notification' in window && Notification.permission === 'granted') {
      const notificacion = new Notification(titulo, {
        body: mensaje,
        // icon: 'assets/logo.png' // Descomenta esto si tienes un logo en tu carpeta assets
      });

      // Si el dueño del taller hace clic en el recuadro negro, se abre la pestaña del sistema
      notificacion.onclick = () => {
        window.focus(); 
      };
    }
  }

  actualizarContador() {
    this.notifService.getNoLeidas().subscribe(res => {
      this.cantidadNoLeidas = res.total_no_leidas;
    });
  }

  toggleDropdown(event: Event): void {
    event.stopPropagation();
    this.mostrarDropdown = !this.mostrarDropdown;
    
    if (this.mostrarDropdown) {
      this.notifService.getMisNotificaciones().subscribe(data => {
        this.notificaciones = data;
      });
    }
  }

  marcarLeida(notif: any, event: Event): void {
    event.stopPropagation();
    if (notif.leido_boolean) return;

    this.notifService.marcarComoLeida(notif.id_notificacion).subscribe(() => {
      notif.leido_boolean = true;
      this.actualizarContador();
    });
  }

  obtenerTiempoRelativo(fechaString: string): string {
    if (!fechaString) return 'Hace un momento';
    const fechaNotif = new Date(fechaString).getTime();
    const ahora = new Date().getTime();
    const diffMins = Math.floor((ahora - fechaNotif) / 60000);

    if (diffMins < 1) return 'Hace un momento';
    if (diffMins < 60) return `Hace ${diffMins} minutos`;
    if (diffMins < 1440) return `Hace ${Math.floor(diffMins / 60)} horas`;
    return `Hace ${Math.floor(diffMins / 1440)} días`;
  }

  notificarToggle() { this.onToggle.emit(); }

  @HostListener('document:click')
  onDocumentClick() { this.mostrarDropdown = false; }
}
