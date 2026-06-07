import { Injectable } from '@angular/core';
import { HttpClient, HttpHeaders } from '@angular/common/http';
import { Observable } from 'rxjs';

@Injectable({
  providedIn: 'root'
})
export class PagoService {
  private apiUrl = 'http://localhost:8000/pagos';

  constructor(private http: HttpClient) {}
  private getAuthHeaders() {
    const token = localStorage.getItem('token');
    return {
      headers: new HttpHeaders({
        'Authorization': `Bearer ${token}`
      })
    };
  }

  // CU14: Para el Admin - Ve TODA la plata de la plataforma
  obtenerPagos(): Observable<any[]> {
    return this.http.get<any[]>(`${this.apiUrl}/`, this.getAuthHeaders());
  }

  // CU13: Para el Taller - Ve SOLO su plata (El backend lo sabe por el token)
  obtenerMisIngresos(): Observable<any[]> {
    return this.http.get<any[]>(`${this.apiUrl}/mis-ingresos`, this.getAuthHeaders());
  }
}
