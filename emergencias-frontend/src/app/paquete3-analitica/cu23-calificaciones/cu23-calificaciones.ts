// Componente de Calificaciones y Reputación - Ciclo 5 - CU23
// Vista del taller para ver sus reseñas y promedio
import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { CalificacionService, CalificacionOut, PromedioCalificacion } from '../../core/services/calificacion.service';

@Component({
  selector: 'app-cu23-calificaciones',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './cu23-calificaciones.html',
  styleUrls: ['./cu23-calificaciones.css']
})
export class Cu23CalificacionesComponent implements OnInit {
  // Datos de calificaciones - Ciclo 5 - CU23
  calificaciones: CalificacionOut[] = [];
  promedio: PromedioCalificacion = { taller_id: 0, promedio: 0, total_calificaciones: 0, distribucion: {} };
  isLoading = true;

  constructor(private calificacionService: CalificacionService) {}

  ngOnInit(): void {
    this.cargarDatos();
  }

  // Cargar calificaciones y promedio - Ciclo 5 - CU23
  cargarDatos(): void {
    this.isLoading = true;
    this.calificacionService.getMisCalificaciones().subscribe({
      next: (data) => {
        this.calificaciones = data;
        // Obtener taller_id de la primera calificación para el promedio - Ciclo 5 - CU23
        if (data.length > 0) {
          this.calificacionService.getPromedio(data[0].taller_id).subscribe({
            next: (p) => { this.promedio = p; this.isLoading = false; },
            error: () => { this.isLoading = false; }
          });
        } else {
          this.isLoading = false;
        }
      },
      error: () => { this.isLoading = false; }
    });
  }

  // Generar array de estrellas llenas - Ciclo 5 - CU23
  getEstrellas(n: number): number[] { return Array(Math.round(n)).fill(0); }
  // Generar array de estrellas vacías - Ciclo 5 - CU23
  getEstrellasVacias(n: number): number[] { return Array(5 - Math.round(n)).fill(0); }

  // Porcentaje de distribución para barras - Ciclo 5 - CU23
  getPorcentaje(puntuacion: number): number {
    const count = this.promedio.distribucion[String(puntuacion)] || 0;
    return this.promedio.total_calificaciones > 0 ? Math.round((count / this.promedio.total_calificaciones) * 100) : 0;
  }

  // Obtener conteo por puntuación - Ciclo 5 - CU23
  getConteo(puntuacion: number): number {
    return this.promedio.distribucion[String(puntuacion)] || 0;
  }

  // Formatear fecha - Ciclo 5 - CU23
  formatFecha(fecha: string): string {
    return new Date(fecha).toLocaleDateString('es-BO', { day: '2-digit', month: 'short', year: 'numeric' });
  }

  // Inicial del nombre para avatar - Ciclo 5 - CU23
  getInicial(nombre: string | null): string {
    return nombre ? nombre.charAt(0).toUpperCase() : '?';
  }

  // Color del borde según puntuación - Ciclo 5 - CU23
  getBorderColor(puntuacion: number): string {
    const colores: { [key: number]: string } = { 5: '#22c55e', 4: '#3b82f6', 3: '#f59e0b', 2: '#f97316', 1: '#ef4444' };
    return colores[puntuacion] || '#94a3b8';
  }
}
