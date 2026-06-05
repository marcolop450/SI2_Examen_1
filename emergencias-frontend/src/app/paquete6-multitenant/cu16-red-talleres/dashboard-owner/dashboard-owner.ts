import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterModule } from '@angular/router';

@Component({
  selector: 'app-dashboard-owner',
  standalone: true,
  imports: [CommonModule, RouterModule],
  templateUrl: './dashboard-owner.html',
  styleUrls: ['./dashboard-owner.css']
})
export class DashboardOwnerComponent implements OnInit {
  // Datos del Tenant Owner (simulados para demostración)
  nombreRed = 'Norte Auxilio';
  subdominio = 'norteauxilio';
  nombrePlan = 'Profesional';
  estadoSuscripcion = 'Activo';
  fechaVencimiento = '2026-01-15';
  diasRestantes = 0;

  // Control de cuota contractual
  talleresCreados = 1;
  limiteTalleres = 2;
  porcentajeUso = 0;
  limiteAlcanzado = false;

  // Talleres de la red (simulados)
  talleres = [
    {
      id_taller: 1,
      nombre: 'Sucursal Central - El Alto',
      direccion: 'Av. Juan Pablo II #450',
      estado: 'operativo'
    }
  ];

  ngOnInit(): void {
    this.calcularMetricas();
  }

  private calcularMetricas(): void {
    // Porcentaje de uso de la cuota
    this.porcentajeUso = Math.round((this.talleresCreados / this.limiteTalleres) * 100);
    this.limiteAlcanzado = this.talleresCreados >= this.limiteTalleres;

    // Días restantes de suscripción
    const hoy = new Date();
    const vencimiento = new Date(this.fechaVencimiento);
    const diff = vencimiento.getTime() - hoy.getTime();
    this.diasRestantes = Math.max(0, Math.ceil(diff / (1000 * 60 * 60 * 24)));
  }
}
