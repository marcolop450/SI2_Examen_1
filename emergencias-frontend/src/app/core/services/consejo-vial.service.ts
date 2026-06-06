// Servicio de Consejos de Seguridad Vial - Ciclo 5 - CU25
// Consume endpoints /consejos-viales/* para gestión de consejos
import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';

// Interfaz de consejo de seguridad - Ciclo 5 - CU25
export interface ConsejoVial {
  id_consejo: number;
  categoria: string;
  titulo: string;
  contenido: string;
  icono: string;
  activo: boolean;
}

@Injectable({ providedIn: 'root' })
export class ConsejoVialService {
  private api = 'https://backend-ixkv.onrender.com';
  constructor(private http: HttpClient) {}

  // Listar todos los consejos activos - Ciclo 5 - CU25
  getConsejos(): Observable<ConsejoVial[]> {
    return this.http.get<ConsejoVial[]>(`${this.api}/consejos-viales/`);
  }
  // Filtrar por categoría - Ciclo 5 - CU25
  getPorCategoria(categoria: string): Observable<ConsejoVial[]> {
    return this.http.get<ConsejoVial[]>(`${this.api}/consejos-viales/por-categoria/${categoria}`);
  }
  // Consejos personalizados para un incidente - Ciclo 5 - CU25
  getParaIncidente(incidenteId: number): Observable<ConsejoVial[]> {
    return this.http.get<ConsejoVial[]>(`${this.api}/consejos-viales/para-incidente/${incidenteId}`);
  }
  // Crear nuevo consejo (admin) - Ciclo 5 - CU25
  crearConsejo(datos: any): Observable<ConsejoVial> {
    return this.http.post<ConsejoVial>(`${this.api}/consejos-viales/`, datos);
  }
  // Generar consejos con IA para un incidente - Ciclo 5 - CU25
  generarConIA(incidenteId: number): Observable<any> {
    return this.http.post<any>(`${this.api}/consejos-viales/generar-ia/${incidenteId}`, {});
  }
  // Actualizar consejo (admin) - Ciclo 5 - CU25
  actualizarConsejo(id: number, datos: any): Observable<ConsejoVial> {
    return this.http.put<ConsejoVial>(`${this.api}/consejos-viales/${id}`, datos);
  }
  // Eliminar consejo (admin) - Ciclo 5 - CU25
  eliminarConsejo(id: number): Observable<any> {
    return this.http.delete(`${this.api}/consejos-viales/${id}`);
  }
}
