import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterModule } from '@angular/router';
import { TenantService } from '../../../core/services/tenant.service';

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
  totalTalleres = 0;
  errorConexion = false;

  constructor(private tenantService: TenantService) {}

  ngOnInit(): void {
    this.tenantService.obtenerResumenCockpit().subscribe({
      next: (data) => {
        this.tenants = data;
        this.calcularMetricas();
        this.errorConexion = false;
      },
      error: (err) => {
        console.error('Error al recuperar el resumen SaaS real:', err);
        this.errorConexion = true;
      }
    });
  }

  private calcularMetricas(): void {
    this.totalOrganizaciones = this.tenants.length;
    this.totalTalleres = this.tenants.reduce((sum, t) => sum + t.talleres_activos, 0);
  }

  cuotaCritica(t: TenantResumen): boolean {
    return t.talleres_activos >= t.limite_talleres;
  }
}
