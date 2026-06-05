import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
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
    return this.http.get<PlanOut[]>(`${this.apiUrl}/planes/`);
  }

  registrarEmpresa(payload: TenantRegisterRequest): Observable<any> {
    return this.http.post<any>(`${this.apiUrl}/auth/registrar-tenant`, payload);
  }
}
