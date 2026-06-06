// #Ciclo5 CU22 Panel de KPIs y Analítica Operacional - COMPLETO según enunciado
// Dashboard con todos los KPIs obligatorios del examen
import { Component, OnInit, ViewChild, ElementRef } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterModule, Router } from '@angular/router';
import { forkJoin } from 'rxjs';
import { KpiService, KpiResumen, IncidentesPorMes, DistribucionEstado, TallerRanking } from '../../core/services/kpi.service';

@Component({
  selector: 'app-cu22-kpis',
  standalone: true,
  imports: [CommonModule, RouterModule],
  templateUrl: './cu22-kpis.html',
  styleUrls: ['./cu22-kpis.css']
})
export class Cu22KpisComponent implements OnInit {
  // #Ciclo5 CU22 Canvas refs para gráficos nativos
  @ViewChild('barCanvas') barCanvas!: ElementRef<HTMLCanvasElement>;
  @ViewChild('donutCanvas') donutCanvas!: ElementRef<HTMLCanvasElement>;
  @ViewChild('tipoCanvas') tipoCanvas!: ElementRef<HTMLCanvasElement>;

  // #Ciclo5 CU22 Datos del dashboard
  resumen: KpiResumen = { total_incidentes: 0, incidentes_activos: 0, incidentes_finalizados: 0, tasa_exito: 0, tiempo_promedio_atencion_min: 0, ingresos_totales: 0, calificacion_promedio: 0, tecnicos_disponibles: 0, tecnicos_total: 0 };
  incidentesPorMes: IncidentesPorMes[] = [];
  porEstado: DistribucionEstado[] = [];
  talleresRanking: TallerRanking[] = [];
  isLoading = true;
  rolUsuario: string = '';

  // #Ciclo5 CU22 KPIs adicionales del enunciado
  tiempoAsignacion: any = { avg_minutos: 0, total_medidos: 0 };
  tiempoLlegada: any = { avg_minutos: 0, total_medidos: 0 };
  porTipo: any[] = [];
  zonasIncidentes: any[] = [];
  sla: any = { sla_objetivo_min: 60, total_finalizados: 0, dentro_sla: 0, fuera_sla: 0, porcentaje_cumplimiento: 0, tiempo_promedio_min: 0 };

  // #Ciclo5 CU22 Colores para gráficos
  coloresEstado: { [key: string]: string } = {
    'pendiente': '#f59e0b', 'en_proceso': '#3b82f6', 'atendido': '#22c55e',
    'cancelado': '#ef4444', 'finalizado': '#10b981', 'buscando_taller': '#8b5cf6',
    'taller_asignado': '#6366f1', 'en_camino': '#06b6d4', 'en_atencion': '#0ea5e9'
  };
  coloresTipo: string[] = ['#3b82f6', '#ef4444', '#f59e0b', '#22c55e', '#8b5cf6', '#06b6d4', '#f97316', '#ec4899'];

  constructor(private kpiService: KpiService, private router: Router) {}

  ngOnInit(): void {
    this.rolUsuario = localStorage.getItem('rol') || '';
    this.cargarDatos();
  }

  // #Ciclo5 CU22 Cargar todos los KPIs en paralelo
  cargarDatos(): void {
    this.isLoading = true;
    const calls: any = {
      resumen: this.kpiService.getResumen(),
      porMes: this.kpiService.getIncidentesPorMes(),
      porEstado: this.kpiService.getPorEstado(),
      tiempoAsignacion: this.kpiService.getTiempoAsignacion(),
      tiempoLlegada: this.kpiService.getTiempoLlegada(),
      porTipo: this.kpiService.getPorTipo(),
      zonas: this.kpiService.getZonasIncidentes(),
      sla: this.kpiService.getSla()
    };
    if (this.rolUsuario === 'admin') {
      calls['ranking'] = this.kpiService.getTalleresRanking();
    }

    forkJoin(calls).subscribe({
      next: (res: any) => {
        this.resumen = res.resumen;
        this.incidentesPorMes = res.porMes;
        this.porEstado = res.porEstado;
        this.tiempoAsignacion = res.tiempoAsignacion;
        this.tiempoLlegada = res.tiempoLlegada;
        this.porTipo = res.porTipo;
        this.zonasIncidentes = res.zonas;
        this.sla = res.sla;
        if (res.ranking) this.talleresRanking = res.ranking;
        this.isLoading = false;
        setTimeout(() => { this.renderBarChart(); this.renderDonutChart(); this.renderTipoChart(); }, 100);
      },
      error: () => { this.isLoading = false; }
    });
  }

  // #Ciclo5 CU22 Gráfico de barras: incidentes por mes
  renderBarChart(): void {
    if (!this.barCanvas || !this.incidentesPorMes.length) return;
    const canvas = this.barCanvas.nativeElement;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;
    const dpr = window.devicePixelRatio || 1;
    const rect = canvas.getBoundingClientRect();
    canvas.width = rect.width * dpr; canvas.height = rect.height * dpr;
    ctx.scale(dpr, dpr);
    const W = rect.width, H = rect.height;
    ctx.clearRect(0, 0, W, H);
    const data = this.incidentesPorMes;
    const maxVal = Math.max(...data.map(d => d.total), 1);
    const barW = Math.min(50, (W - 80) / data.length - 10);
    const chartH = H - 60; const startX = 50;
    ctx.strokeStyle = '#e2e8f0'; ctx.lineWidth = 0.5;
    for (let i = 0; i <= 4; i++) {
      const y = 20 + (chartH / 4) * i;
      ctx.beginPath(); ctx.moveTo(startX, y); ctx.lineTo(W - 10, y); ctx.stroke();
      ctx.fillStyle = '#94a3b8'; ctx.font = '11px sans-serif'; ctx.textAlign = 'right';
      ctx.fillText(String(Math.round(maxVal - (maxVal / 4) * i)), startX - 8, y + 4);
    }
    data.forEach((d, i) => {
      const barH = (d.total / maxVal) * chartH;
      const x = startX + i * ((W - startX - 10) / data.length) + ((W - startX - 10) / data.length - barW) / 2;
      const y = 20 + chartH - barH;
      const grad = ctx.createLinearGradient(x, y, x, y + barH);
      grad.addColorStop(0, '#60a5fa'); grad.addColorStop(1, '#2563eb');
      ctx.fillStyle = grad;
      ctx.beginPath(); ctx.roundRect(x, y, barW, barH, [6, 6, 0, 0]); ctx.fill();
      ctx.fillStyle = '#1e40af'; ctx.font = 'bold 12px sans-serif'; ctx.textAlign = 'center';
      ctx.fillText(String(d.total), x + barW / 2, y - 6);
      ctx.fillStyle = '#64748b'; ctx.font = '10px sans-serif';
      ctx.fillText(d.mes.split(' ')[0], x + barW / 2, H - 8);
    });
  }

  // #Ciclo5 CU22 Gráfico donut: distribución por estado
  renderDonutChart(): void {
    if (!this.donutCanvas || !this.porEstado.length) return;
    const canvas = this.donutCanvas.nativeElement;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;
    const dpr = window.devicePixelRatio || 1;
    const rect = canvas.getBoundingClientRect();
    canvas.width = rect.width * dpr; canvas.height = rect.height * dpr;
    ctx.scale(dpr, dpr);
    const W = rect.width, H = rect.height;
    ctx.clearRect(0, 0, W, H);
    const cx = W / 2, cy = H / 2 - 10;
    const outerR = Math.min(cx, cy) - 20; const innerR = outerR * 0.6;
    const total = this.porEstado.reduce((s, d) => s + d.total, 0);
    let startAngle = -Math.PI / 2;
    this.porEstado.forEach(d => {
      const sliceAngle = (d.total / total) * 2 * Math.PI;
      ctx.beginPath(); ctx.arc(cx, cy, outerR, startAngle, startAngle + sliceAngle);
      ctx.arc(cx, cy, innerR, startAngle + sliceAngle, startAngle, true);
      ctx.closePath(); ctx.fillStyle = this.coloresEstado[d.estado] || '#94a3b8'; ctx.fill();
      startAngle += sliceAngle;
    });
    ctx.beginPath(); ctx.arc(cx, cy, innerR - 2, 0, Math.PI * 2); ctx.fillStyle = 'white'; ctx.fill();
    ctx.fillStyle = '#0f172a'; ctx.font = 'bold 24px sans-serif'; ctx.textAlign = 'center';
    ctx.fillText(String(total), cx, cy + 4);
    ctx.fillStyle = '#64748b'; ctx.font = '11px sans-serif'; ctx.fillText('Total', cx, cy + 20);
  }

  // #Ciclo5 CU22 Gráfico de barras horizontales: incidentes por tipo
  renderTipoChart(): void {
    if (!this.tipoCanvas || !this.porTipo.length) return;
    const canvas = this.tipoCanvas.nativeElement;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;
    const dpr = window.devicePixelRatio || 1;
    const rect = canvas.getBoundingClientRect();
    canvas.width = rect.width * dpr; canvas.height = rect.height * dpr;
    ctx.scale(dpr, dpr);
    const W = rect.width, H = rect.height;
    ctx.clearRect(0, 0, W, H);
    const data = this.porTipo.slice(0, 6);
    const maxVal = Math.max(...data.map((d: any) => d.total), 1);
    const barH = Math.min(30, (H - 20) / data.length - 8);
    const startX = 80;
    data.forEach((d: any, i: number) => {
      const y = 10 + i * ((H - 20) / data.length);
      const barW = ((d.total / maxVal) * (W - startX - 40));
      ctx.fillStyle = '#64748b'; ctx.font = '11px sans-serif'; ctx.textAlign = 'right';
      ctx.fillText(d.tipo.toUpperCase(), startX - 8, y + barH / 2 + 4);
      const grad = ctx.createLinearGradient(startX, y, startX + barW, y);
      grad.addColorStop(0, this.coloresTipo[i % this.coloresTipo.length]);
      grad.addColorStop(1, this.coloresTipo[i % this.coloresTipo.length] + '99');
      ctx.fillStyle = grad;
      ctx.beginPath(); ctx.roundRect(startX, y, barW, barH, [0, 6, 6, 0]); ctx.fill();
      ctx.fillStyle = '#0f172a'; ctx.font = 'bold 11px sans-serif'; ctx.textAlign = 'left';
      ctx.fillText(String(d.total), startX + barW + 6, y + barH / 2 + 4);
    });
  }

  getColorEstado(estado: string): string { return this.coloresEstado[estado] || '#94a3b8'; }
  getEstrellas(n: number): number[] { return Array(Math.round(n)).fill(0); }
  verBitacora(incidenteId: number): void { this.router.navigate(['/bitacora', incidenteId]); }
  // #Ciclo5 CU22 Obtener total de cancelados de la distribución por estado
  getCancelados(): number {
    const cancelado = this.porEstado.find(e => e.estado === 'cancelado');
    return cancelado ? cancelado.total : 0;
  }
}
