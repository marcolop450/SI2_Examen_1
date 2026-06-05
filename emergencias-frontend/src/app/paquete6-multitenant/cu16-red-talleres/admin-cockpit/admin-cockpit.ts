import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterModule } from '@angular/router';

interface TenantResumen {
  id_tenant: string;
  nombre: string;
  subdominio: string;
  nombre_plan: string;
  precio_plan: number;
  fecha_registro: string;
  talleres_activos: number;
  limite_talleres: number;
  estado: string;
}

@Component({
  selector: 'app-admin-cockpit',
  standalone: true,
  imports: [CommonModule, RouterModule],
  templateUrl: './admin-cockpit.html',
  styleUrls: ['./admin-cockpit.css']
})
export class AdminCockpitComponent implements OnInit {
  tenants: TenantResumen[] = [];

  totalOrganizaciones = 0;
  mrr = 0;
  totalTalleres = 0;

  ngOnInit(): void {
    this.tenants = [
      {
        id_tenant: 'a1b2c3d4-e5f6-7890-abcd-ef1234567890',
        nombre: 'AutoServicio Express',
        subdominio: 'autoexpress',
        nombre_plan: 'Profesional',
        precio_plan: 299,
        fecha_registro: '2025-03-15',
        talleres_activos: 4,
        limite_talleres: 5,
        estado: 'activo'
      },
      {
        id_tenant: 'b2c3d4e5-f6a7-8901-bcde-f12345678901',
        nombre: 'MegaTaller Bolivia',
        subdominio: 'megataller',
        nombre_plan: 'Enterprise',
        precio_plan: 599,
        fecha_registro: '2025-01-20',
        talleres_activos: 12,
        limite_talleres: 50,
        estado: 'activo'
      },
      {
        id_tenant: 'c3d4e5f6-a7b8-9012-cdef-123456789012',
        nombre: 'Quick Fix SRL',
        subdominio: 'quickfix',
        nombre_plan: 'Starter',
        precio_plan: 99,
        fecha_registro: '2025-06-01',
        talleres_activos: 1,
        limite_talleres: 1,
        estado: 'activo'
      },
      {
        id_tenant: 'd4e5f6a7-b8c9-0123-defa-234567890123',
        nombre: 'Red Mecánica Nacional',
        subdominio: 'redmecanica',
        nombre_plan: 'Profesional',
        precio_plan: 299,
        fecha_registro: '2024-11-10',
        talleres_activos: 5,
        limite_talleres: 5,
        estado: 'activo'
      },
      {
        id_tenant: 'e5f6a7b8-c9d0-1234-efab-345678901234',
        nombre: 'TallerNet Oruro',
        subdominio: 'tallernet',
        nombre_plan: 'Starter',
        precio_plan: 99,
        fecha_registro: '2025-05-20',
        talleres_activos: 1,
        limite_talleres: 1,
        estado: 'suspendido'
      }
    ];

    this.calcularMetricas();
  }

  private calcularMetricas(): void {
    this.totalOrganizaciones = this.tenants.length;
    this.mrr = this.tenants
      .filter(t => t.estado === 'activo')
      .reduce((sum, t) => sum + t.precio_plan, 0);
    this.totalTalleres = this.tenants.reduce((sum, t) => sum + t.talleres_activos, 0);
  }

  cuotaCritica(t: TenantResumen): boolean {
    return t.talleres_activos >= t.limite_talleres;
  }
}
