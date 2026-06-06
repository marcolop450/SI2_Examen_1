import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { TecnicoOut, TecnicoCreate, TecnicoPartial } from '../../shared/models/tecnico.model';

@Injectable({
  providedIn: 'root'
})
export class TecnicoService {
  private apiUrl = 'https://backend-ixkv.onrender.com/tecnicos'; 

  constructor(private http: HttpClient) {}

  getTecnicosByTaller(tallerId: number): Observable<TecnicoOut[]> {
    return this.http.get<TecnicoOut[]>(`${this.apiUrl}/taller/${tallerId}`);
  }

  crearTecnico(tecnico: TecnicoCreate): Observable<TecnicoOut> {
    return this.http.post<TecnicoOut>(`${this.apiUrl}/`, tecnico);
  }

  updateDisponibilidad(idTecnico: number, data: TecnicoPartial): Observable<TecnicoOut> {
    return this.http.patch<TecnicoOut>(`${this.apiUrl}/${idTecnico}`, data);
  }

  deleteTecnico(idTecnico: number): Observable<any> {
    return this.http.delete(`${this.apiUrl}/${idTecnico}`);
  }
}
