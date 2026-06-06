// Servicio de Bitácora de Trazabilidad - Ciclo 5 - CU21
// Consume GET /bitacora/{incidenteId} para obtener la línea de tiempo
import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';

// Interfaz de evento de bitácora - Ciclo 5 - CU21
export interface BitacoraEntry {
  id_bitacora: number;
  incidente_id: number;
  evento: string;
  descripcion: string | null;
  usuario_id: number | null;
  usuario_nombre: string | null;
  timestamp: string;
}

@Injectable({ providedIn: 'root' })
export class BitacoraService {
  private api = 'https://backend-ixkv.onrender.com';
  constructor(private http: HttpClient) {}

  // Obtener bitácora completa de un incidente - Ciclo 5 - CU21
  getBitacora(incidenteId: number): Observable<BitacoraEntry[]> {
    return this.http.get<BitacoraEntry[]>(`${this.api}/bitacora/${incidenteId}`);
  }
}
