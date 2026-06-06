import { Component, HostListener, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterOutlet, Router } from '@angular/router';
import { Sidebar } from './shared/sidebar/sidebar'; 
import { NavbarComponent } from './shared/navbar/navbar'; 

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [CommonModule, RouterOutlet, Sidebar, NavbarComponent],
  templateUrl: './app.html',
  styleUrls: ['./app.css']
})
export class App implements OnInit { 
  sidebarColapsado = window.innerWidth <= 768; 

  constructor(public router: Router) {}

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
      Notification.requestPermission().then(permission => {
        if (permission === 'granted') {
          console.log("¡Permiso para notificaciones de Windows concedido!");
        }
      });
    }
  }
}