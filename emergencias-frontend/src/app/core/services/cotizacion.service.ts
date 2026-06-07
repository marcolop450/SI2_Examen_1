import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';

@Injectable({ providedIn: 'root' })
export class CotizacionService {
  private apiUrl = 'http://localhost:8000/cotizaciones';

  constructor(private http: HttpClient) {}

  // Taller envía una cotización
  enviarCotizacion(datos: any): Observable<any> {
    return this.http.post(`${this.apiUrl}/`, datos);
  }

  // Cliente ve las cotizaciones de su incidente
  getCotizaciones(incidenteId: number): Observable<any[]> {
    return this.http.get<any[]>(`${this.apiUrl}/${incidenteId}`);
  }

  aceptarCotizacion(id: number): Observable<any> {
    return this.http.put(`${this.apiUrl}/${id}/aceptar`, {});
  }

  rechazarCotizacion(id: number): Observable<any> {
    return this.http.put(`${this.apiUrl}/${id}/rechazar`, {});
  }
}
