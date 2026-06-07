import { Injectable } from '@angular/core';
import { HttpClient, HttpHeaders } from '@angular/common/http';
import { Observable } from 'rxjs';
import { PlanOut, TenantRegisterRequest } from '../../paquete6-multitenant/cu16-red-talleres/saas.interface';
import { environment } from '../../../environments/environment';

@Injectable({
  providedIn: 'root'
})
export class TenantService {
  private apiUrl = environment.apiUrl;

  constructor(private http: HttpClient) {}

  obtenerPlanes(): Observable<PlanOut[]> {
    return this.http.get<PlanOut[]>(`${this.apiUrl}/admin/cockpit/planes-globales`);
  }

  registrarEmpresa(payload: TenantRegisterRequest): Observable<any> {
    return this.http.post<any>(`${this.apiUrl}/auth/registrar-tenant`, payload);
  }

  // CU16: Resumen de agregación relacional para el Admin Cockpit
  obtenerResumenCockpit(): Observable<any[]> {
    const token = localStorage.getItem('token') || localStorage.getItem('auth_token') || '';
    const headers = new HttpHeaders().set('Authorization', `Bearer ${token}`);
    return this.http.get<any[]>(`${this.apiUrl}/admin/cockpit/resumen`, { headers });
  }

  // CU16: Catálogo global de planes SaaS
  obtenerPlanesGlobales(): Observable<any[]> {
    return this.http.get<any[]>(`${this.apiUrl}/admin/cockpit/planes-globales`);
  }

  // Dashboard admin-red
  obtenerDashboardOwner(): Observable<any> {
    const token = localStorage.getItem('token') || localStorage.getItem('auth_token') || '';
    const headers = new HttpHeaders().set('Authorization', `Bearer ${token}`);
    return this.http.get<any>(`${this.apiUrl}/admin-red/dashboard-owner`, { headers });
  }
}
