// #Ciclo5 CU19 - App Component con PWA Offline y banner de conectividad
import { Component, HostListener, OnInit, OnDestroy } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterOutlet, Router } from '@angular/router';
import { Sidebar } from './shared/sidebar/sidebar';
import { NavbarComponent } from './shared/navbar/navbar';
import { OfflineEmergenciaService } from './core/services/offline-emergencia.service';
import { Subscription } from 'rxjs';

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [CommonModule, RouterOutlet, Sidebar, NavbarComponent],
  templateUrl: './app.html',
  styleUrls: ['./app.css']
})
export class App implements OnInit, OnDestroy {
  sidebarColapsado = window.innerWidth <= 768;

  // #Ciclo5 CU19 - Estado de conectividad para el banner
  online = true;
  pendientesOffline = 0;
  mostrarSyncOk = false;
  private subs: Subscription[] = [];

  constructor(
    public router: Router,
    public offlineService: OfflineEmergenciaService
  ) {}

  isRutaPublica(): boolean {
    const url = this.router.url.split('?')[0];
    if (url === '/login' || url === '/') {
      return true;
    }
    if (url === '/registro-b2b') {
      return true;
    }
    if (url === '/planes') {
      const logged = !!(localStorage.getItem('token') || localStorage.getItem('auth_token'));
      return !logged; // Si está logueado, NO es pública (se renderiza dentro del layout con sidebar)
    }
    return false;
  }

  // 🔥 Se ejecuta apenas carga la página web
  ngOnInit() {
    if (!this.isRutaPublica()) {
      this.solicitarPermisoWindows();
    }
  ngOnInit() {
    this.solicitarPermisoWindows();

    // #Ciclo5 CU19 - Suscribirse a cambios de conectividad
    this.subs.push(
      this.offlineService.online$.subscribe((online) => {
        const estabaOffline = !this.online;
        this.online = online;
        // Mostrar mensaje de sincronización exitosa
        if (online && estabaOffline && this.pendientesOffline > 0) {
          this.mostrarSyncOk = true;
          setTimeout(() => (this.mostrarSyncOk = false), 4000);
        }
      })
    );

    this.subs.push(
      this.offlineService.pendientes$.subscribe((n) => {
        this.pendientesOffline = n;
      })
    );
  }

  ngOnDestroy() {
    this.subs.forEach((s) => s.unsubscribe());
  }

  toggleSidebar() {
    this.sidebarColapsado = !this.sidebarColapsado;
  }

  @HostListener('window:resize')
  onResize() {
    this.sidebarColapsado = window.innerWidth <= 768;
  }

  solicitarPermisoWindows() {
    if ('Notification' in window) {
      Notification.requestPermission().then((permission) => {
        if (permission === 'granted') {
          console.log('Permiso para notificaciones concedido.');
        }
      });
    }
  }
}