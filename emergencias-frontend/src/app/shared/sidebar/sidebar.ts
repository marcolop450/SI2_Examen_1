// src/app/shared/sidebar/sidebar.ts
import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterModule, Router } from '@angular/router';

@Component({
  selector: 'app-sidebar',
  standalone: true,
  imports: [CommonModule, RouterModule],
  templateUrl: './sidebar.html',
  styleUrls: ['./sidebar.css']
})
export class Sidebar implements OnInit {
  isSidebarOpen = false;
  
  rolUsuario: string = ''; 

  // --- BANDERAS SaaS ---
  tenantId: string | null = null;
  esSuperAdmin = false;
  esTenantOwner = false;

  constructor(private router: Router) {}

  ngOnInit(): void {
    const rol = localStorage.getItem('rol') || 'taller';
    this.rolUsuario = rol.toLowerCase();

    // --- LECTURA DE SESIÓN SaaS ---
    this.tenantId = localStorage.getItem('tenant_id');
    this.esSuperAdmin = this.rolUsuario === 'admin';
    this.esTenantOwner = this.rolUsuario === 'admin_red';
  }
  
  toggleSidebar() {
    this.isSidebarOpen = !this.isSidebarOpen;
  }

  cerrarSesion() {
    localStorage.clear();
    this.rolUsuario = localStorage.getItem('rol') || 'taller';
    this.router.navigate(['/login']); 
  }
}
