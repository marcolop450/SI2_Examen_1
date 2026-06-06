import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable, tap } from 'rxjs';
import { TokenResponse, TipoRol } from '../../shared/models/usuario.model';
import { environment } from '../../../environments/environment';

@Injectable({
  providedIn: 'root'
})
export class AuthService {
  private apiUrl = `${environment.apiUrl}/auth`;

  constructor(private http: HttpClient) {}

  login(datos: any): Observable<TokenResponse> {
    return this.http.post<TokenResponse>(`${this.apiUrl}/login`, datos).pipe(
      tap(res => {
        localStorage.setItem('token', res.access_token);
        localStorage.setItem('rol', res.rol);
        localStorage.setItem('nombre', res.nombre);
        
        const idParaGuardar = res.id_taller ? res.id_taller : res.id_usuario;
        localStorage.setItem('id_entidad', idParaGuardar.toString());

        // Decodificar JWT para almacenar el tenant_id de forma segura
        const claims = this.decodeToken(res.access_token);
        if (claims && claims.tenant_id) {
          localStorage.setItem('tenant_id', claims.tenant_id);
        } else {
          localStorage.removeItem('tenant_id');
        }
      })
    );
  }

  logout(): void {
    localStorage.clear();
  }

  getTenantId(): string | null {
    return localStorage.getItem('tenant_id');
  }

  // Decodificador nativo unicode-safe de JWT base64url
  private decodeToken(token: string): any {
    try {
      const base64Url = token.split('.')[1];
      const base64 = base64Url.replace(/-/g, '+').replace(/_/g, '/');
      const jsonPayload = decodeURIComponent(
        window.atob(base64)
          .split('')
          .map(c => '%' + ('00' + c.charCodeAt(0).toString(16)).slice(-2))
          .join('')
      );
      return JSON.parse(jsonPayload);
    } catch (e) {
      return null;
    }
  }
}
