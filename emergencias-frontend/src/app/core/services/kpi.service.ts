// Servicio del Panel de KPIs y Analítica - Ciclo 5 - CU22
// Consume endpoints /kpis/* para métricas operacionales
import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';

// Interfaces de KPIs - Ciclo 5 - CU22
export interface KpiResumen {
  total_incidentes: number;
  incidentes_activos: number;
  incidentes_finalizados: number;
  tasa_exito: number;
  tiempo_promedio_atencion_min: number;
  ingresos_totales: number;
  calificacion_promedio: number;
  tecnicos_disponibles: number;
  tecnicos_total: number;
}

export interface IncidentesPorMes {
  mes: string;
  total: number;
}

export interface DistribucionEstado {
  estado: string;
  total: number;
  porcentaje: number;
}

export interface DistribucionPrioridad {
  prioridad: string;
  total: number;
}

export interface TallerRanking {
  taller_id: number;
  nombre: string;
  servicios_completados: number;
  calificacion_promedio: number;
}

@Injectable({ providedIn: 'root' })
export class KpiService {
  private api = 'http://localhost:8000';
  constructor(private http: HttpClient) {}

  // Resumen general de KPIs - Ciclo 5 - CU22
  getResumen(): Observable<KpiResumen> {
    return this.http.get<KpiResumen>(`${this.api}/kpis/resumen`);
  }
  // Incidentes agrupados por mes (últimos 6 meses) - Ciclo 5 - CU22
  getIncidentesPorMes(): Observable<IncidentesPorMes[]> {
    return this.http.get<IncidentesPorMes[]>(`${this.api}/kpis/incidentes-por-mes`);
  }
  // Distribución por estado para donut chart - Ciclo 5 - CU22
  getPorEstado(): Observable<DistribucionEstado[]> {
    return this.http.get<DistribucionEstado[]>(`${this.api}/kpis/por-estado`);
  }
  // Distribución por prioridad - Ciclo 5 - CU22
  getPorPrioridad(): Observable<DistribucionPrioridad[]> {
    return this.http.get<DistribucionPrioridad[]>(`${this.api}/kpis/por-prioridad`);
  }
  // #Ciclo5 CU22 Ranking de talleres (admin)
  getTalleresRanking(): Observable<TallerRanking[]> {
    return this.http.get<TallerRanking[]>(`${this.api}/kpis/talleres-ranking`);
  }
  // #Ciclo5 CU22 Tiempo promedio de asignación (creación → taller_asignado)
  getTiempoAsignacion(): Observable<any> {
    return this.http.get<any>(`${this.api}/kpis/tiempo-asignacion`);
  }
  // #Ciclo5 CU22 Tiempo promedio de llegada (taller_asignado → en_atencion)
  getTiempoLlegada(): Observable<any> {
    return this.http.get<any>(`${this.api}/kpis/tiempo-llegada`);
  }
  // #Ciclo5 CU22 Incidentes por tipo (batería, llanta, motor, choque)
  getPorTipo(): Observable<any[]> {
    return this.http.get<any[]>(`${this.api}/kpis/por-tipo`);
  }
  // #Ciclo5 CU22 Zonas con más incidentes (lat/lng agrupados)
  getZonasIncidentes(): Observable<any[]> {
    return this.http.get<any[]>(`${this.api}/kpis/zonas-incidentes`);
  }
  // #Ciclo5 CU22 Nivel de cumplimiento SLA
  getSla(): Observable<any> {
    return this.http.get<any>(`${this.api}/kpis/sla`);
  }
}
