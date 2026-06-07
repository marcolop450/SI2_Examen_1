import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { Taller } from '../../shared/models/taller.model';

@Injectable({
  providedIn: 'root'
})
export class TallerService {
  private apiUrl = 'http://localhost:8000/talleres/';

  constructor(private http: HttpClient) {}

  getTalleres(): Observable<Taller[]> {
    return this.http.get<Taller[]>(this.apiUrl);
  }

  crearTaller(datos: any): Observable<any> {
    return this.http.post(this.apiUrl, datos);
  }

  updateTaller(id: number, datos: any): Observable<any> {
    return this.http.patch(`${this.apiUrl}${id}`, datos);
  }

  deleteTaller(id: number): Observable<any> {
    return this.http.delete(`${this.apiUrl}${id}`);
  }
}
