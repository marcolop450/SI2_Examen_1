// ============================================================
// src/app/core/services/incidente.ts
// Servicio para manejar el CU10 (Aceptar/Rechazar) y CU11 (Asignar)
// ============================================================
import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';

@Injectable({
  providedIn: 'root'
})
export class IncidenteService {
  private apiUrl = 'http://localhost:8000/incidentes';

  constructor(private http: HttpClient) {}

  // CU10: Traer emergencias que están buscando taller
  getPendientes(): Observable<any[]> {
    return this.http.get<any[]>(`${this.apiUrl}/pendientes`);
  }

  // CU10: El taller decide si toma o rechaza el trabajo
  responderSolicitud(idIncidente: number, accion: 'aceptar' | 'rechazar', comentario?: string): Observable<any> {
    return this.http.post(`${this.apiUrl}/${idIncidente}/accion`, { accion, comentario });
  }

  // CU11: El taller envía a uno de sus mecánicos a la emergencia
  asignarTecnico(idIncidente: number, tecnicoId: number): Observable<any> {
    return this.http.post(`${this.apiUrl}/${idIncidente}/asignar`, { tecnico_id: tecnicoId });
  }

  reportarExcepcion(id: number, datos: any): Observable<any> {
    return this.http.post(`${this.apiUrl}/${id}/excepcion`, datos);
  }
}
