// Servicio de Reportes Inteligentes con IA - Ciclo 5 - CU24
// Consume endpoints /reportes-ia/* para generar reportes ejecutivos
import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';

// Interfaz de respuesta del reporte IA - Ciclo 5 - CU24
export interface ReporteResponse {
  reporte_markdown: string;
  prompt_procesado: string;
  datos_periodo: any;
}

@Injectable({ providedIn: 'root' })
export class ReporteIaService {
  private api = 'https://backend-ixkv.onrender.com';
  constructor(private http: HttpClient) {}

  // Generar reporte por texto - Ciclo 5 - CU24
  generarReporte(prompt: string, periodoDias: number): Observable<ReporteResponse> {
    return this.http.post<ReporteResponse>(`${this.api}/reportes-ia/generar`, {
      prompt, periodo_dias: periodoDias
    });
  }
  // Generar reporte por voz (audio base64) - Ciclo 5 - CU24
  generarReportePorVoz(audioBase64: string, periodoDias: number): Observable<ReporteResponse> {
    return this.http.post<ReporteResponse>(`${this.api}/reportes-ia/voz`, {
      audio_base64: audioBase64, periodo_dias: periodoDias
    });
  }
}
