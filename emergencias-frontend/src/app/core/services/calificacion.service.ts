// Servicio de Calificaciones Post-Servicio - Ciclo 5 - CU23
// Consume endpoints /calificaciones/* para reseñas del servicio
import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';

// Interfaces de calificaciones - Ciclo 5 - CU23
export interface CalificacionOut {
  id_calificacion: number;
  incidente_id: number;
  cliente_id: number;
  taller_id: number;
  tecnico_id: number | null;
  puntuacion: number;
  comentario: string | null;
  fecha_calificacion: string;
  cliente_nombre: string | null;
}

export interface PromedioCalificacion {
  taller_id: number;
  promedio: number;
  total_calificaciones: number;
  distribucion: { [key: string]: number };
}

@Injectable({ providedIn: 'root' })
export class CalificacionService {
  private api = 'https://backend-ixkv.onrender.com';
  constructor(private http: HttpClient) {}

  // Obtener mis calificaciones (vista taller) - Ciclo 5 - CU23
  getMisCalificaciones(): Observable<CalificacionOut[]> {
    return this.http.get<CalificacionOut[]>(`${this.api}/calificaciones/mis-calificaciones`);
  }
  // Obtener promedio de un taller - Ciclo 5 - CU23
  getPromedio(tallerId: number): Observable<PromedioCalificacion> {
    return this.http.get<PromedioCalificacion>(`${this.api}/calificaciones/promedio/${tallerId}`);
  }
  // Obtener calificaciones de un taller específico - Ciclo 5 - CU23
  getCalificacionesTaller(tallerId: number): Observable<CalificacionOut[]> {
    return this.http.get<CalificacionOut[]>(`${this.api}/calificaciones/taller/${tallerId}`);
  }
}
