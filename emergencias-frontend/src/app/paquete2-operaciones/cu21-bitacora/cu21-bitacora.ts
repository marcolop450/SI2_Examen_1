// Componente de Bitácora de Trazabilidad - Ciclo 5 - CU21
// Timeline visual de todos los eventos de un incidente
import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ActivatedRoute, Router, RouterModule } from '@angular/router';
import { BitacoraService, BitacoraEntry } from '../../core/services/bitacora.service';

@Component({
  selector: 'app-cu21-bitacora',
  standalone: true,
  imports: [CommonModule, RouterModule],
  templateUrl: './cu21-bitacora.html',
  styleUrls: ['./cu21-bitacora.css']
})
export class Cu21BitacoraComponent implements OnInit {
  // Datos de la bitácora - Ciclo 5 - CU21
  incidenteId: number = 0;
  entradas: BitacoraEntry[] = [];
  isLoading = true;

  constructor(
    private route: ActivatedRoute,
    private router: Router,
    private bitacoraService: BitacoraService
  ) {}

  ngOnInit(): void {
    // Obtener ID del incidente desde la URL - Ciclo 5 - CU21
    this.incidenteId = Number(this.route.snapshot.paramMap.get('id'));
    this.cargarBitacora();
  }

  // Cargar eventos de la bitácora - Ciclo 5 - CU21
  cargarBitacora(): void {
    this.isLoading = true;
    this.bitacoraService.getBitacora(this.incidenteId).subscribe({
      next: (data) => { this.entradas = data; this.isLoading = false; },
      error: () => { this.isLoading = false; }
    });
  }

  // Icono según tipo de evento - Ciclo 5 - CU21
  getIcono(evento: string): string {
    const iconos: { [key: string]: string } = {
      'CREACION': '🆕', 'TALLER_ACEPTO': '✅', 'TALLER_RECHAZO': '❌',
      'COTIZACION_ENVIADA': '📋', 'COTIZACION_ACEPTADA': '✅', 'COTIZACION_RECHAZADA': '❌',
      'TECNICO_ASIGNADO': '🔧', 'CAMBIO_ESTADO': '🔄', 'PAGO_COMPLETADO': '💰',
      'EXCEPCION': '⚠️', 'COMPENSACION_TALLER': '💵', 'REASIGNACION_AUTOMATICA': '🤖',
      'CALIFICACION_REGISTRADA': '⭐', 'CANCELADO': '🚫'
    };
    return iconos[evento] || '📌';
  }

  // Color CSS según tipo de evento - Ciclo 5 - CU21
  getColorClase(evento: string): string {
    if (['TALLER_ACEPTO', 'COTIZACION_ACEPTADA', 'PAGO_COMPLETADO', 'CALIFICACION_REGISTRADA'].includes(evento)) return 'event-success';
    if (['TALLER_RECHAZO', 'COTIZACION_RECHAZADA', 'EXCEPCION', 'CANCELADO'].includes(evento)) return 'event-danger';
    if (['REASIGNACION_AUTOMATICA', 'COMPENSACION_TALLER'].includes(evento)) return 'event-warning';
    if (['CREACION'].includes(evento)) return 'event-info';
    return 'event-default';
  }

  // Formatear fecha legible - Ciclo 5 - CU21
  formatFecha(fecha: string): string {
    const d = new Date(fecha);
    return d.toLocaleDateString('es-BO', { day: '2-digit', month: 'short', year: 'numeric', hour: '2-digit', minute: '2-digit' });
  }

  // Formatear nombre del evento para mostrar - Ciclo 5 - CU21
  formatEvento(evento: string): string {
    return evento.replace(/_/g, ' ');
  }

  // Volver atrás - Ciclo 5 - CU21
  volver(): void {
    this.router.navigate(['/kpis']);
  }
}
