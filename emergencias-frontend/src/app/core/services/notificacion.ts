// ============================================================
// src/app/core/services/notificacion.ts
// CU15: Servicio de Notificaciones y Comunicación
// ============================================================
import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';

@Injectable({
  providedIn: 'root'
})
export class NotificacionService {
  private apiUrl = 'https://backend-ixkv.onrender.com/notificaciones';

  constructor(private http: HttpClient) {}

  // Obtener todas mis notificaciones
  getMisNotificaciones(): Observable<any[]> {
    return this.http.get<any[]>(`${this.apiUrl}/mis-notificaciones`);
  }

  // Obtener solo la cantidad de no leídas (para el globito rojo de la campana)
  getNoLeidas(): Observable<{total_no_leidas: number}> {
    return this.http.get<{total_no_leidas: number}>(`${this.apiUrl}/no-leidas`);
  }

  // Marcar una notificación como leída
  marcarComoLeida(idNotificacion: number): Observable<any> {
    return this.http.patch(`${this.apiUrl}/${idNotificacion}/leer`, { leido_boolean: true });
  }
}
