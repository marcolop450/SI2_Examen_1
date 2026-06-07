// src/app/shared/inicio/inicio.ts
import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterModule } from '@angular/router';

@Component({
  selector: 'app-inicio',
  standalone: true,
  imports: [CommonModule, RouterModule],
  templateUrl: './inicio.html',
  styleUrls: ['./inicio.css']
})
export class Inicio implements OnInit {
  
  rolUsuario: string = ''; 
  tenantId: string | null = null;
  esTenantOwner = false;

  constructor() {}

  ngOnInit(): void {
    const rol = localStorage.getItem('rol') || 'taller';
    this.rolUsuario = rol.toLowerCase();
    this.tenantId = localStorage.getItem('tenant_id');
    this.esTenantOwner = this.rolUsuario === 'admin_red';
  }
}
