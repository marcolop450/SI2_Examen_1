import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { Usuario } from '../../shared/models/usuario.model';

@Injectable({
  providedIn: 'root'
})
export class UsuarioService {
  private apiUrl = 'http://localhost:8000/usuarios/';

  constructor(private http: HttpClient) {}

  getUsuarios(): Observable<Usuario[]> {
    return this.http.get<Usuario[]>(this.apiUrl);
  }
  deleteUsuario(id: number): Observable<any> {
    return this.http.delete(`${this.apiUrl}${id}`);
  }

  updateUsuario(id: number, datos: any): Observable<any> {
    return this.http.patch(`${this.apiUrl}${id}`, datos);
  }
}
