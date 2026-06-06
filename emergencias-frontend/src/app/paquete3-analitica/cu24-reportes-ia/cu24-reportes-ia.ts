// Componente de Reportes Inteligentes con IA - Ciclo 5 - CU24
// La IA detecta tipo y período, devuelve tablas reales. Exporta PDF y Excel.
import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ReporteIaService, ReporteResponse } from '../../core/services/reporte-ia.service';

@Component({
  selector: 'app-cu24-reportes-ia',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './cu24-reportes-ia.html',
  styleUrls: ['./cu24-reportes-ia.css']
})
export class Cu24ReportesIaComponent {
  prompt = '';
  periodoDias = 30;
  reporte: ReporteResponse | null = null;
  isLoading = false;
  isRecording = false;
  errorMsg = '';

  // Grabación de voz
  private mediaRecorder: MediaRecorder | null = null;
  private audioChunks: Blob[] = [];

  // Filtros manuales sobre la tabla
  filtroTexto = '';

  sugerencias = [
    'Talleres de hoy',
    'Comisiones del mes',
    'Técnicos disponibles',
    'Clientes activos esta semana',
    'Resumen general del trimestre'
  ];

  TITULOS: Record<string, string> = {
    comisiones: '💰 Reporte de Comisiones y Pagos',
    talleres:   '🏪 Reporte de Talleres',
    tecnicos:   '🔧 Reporte de Técnicos',
    clientes:   '👥 Reporte de Clientes',
    general:    '📊 Resumen General'
  };

  HEADERS: Record<string, Record<string, string>> = {
    comisiones: { taller: 'Taller', total_pagos: 'N° Pagos', monto_bs: 'Monto (Bs.)' },
    talleres:   { taller: 'Taller', total: 'Total', finalizados: 'Finalizados', cancelados: 'Cancelados', 'exito_%': 'Éxito %', calificacion: '⭐ Calif.', tecnicos: 'Técnicos' },
    tecnicos:   { nombre: 'Técnico', especialidad: 'Especialidad', taller: 'Taller', estado: 'Estado', servicios_periodo: 'Servicios' },
    clientes:   { cliente: 'Cliente', email: 'Email', incidentes: 'Incidentes', finalizados: 'Finalizados' },
    general:    {}
  };

  constructor(private reporteService: ReporteIaService) {}

  // #Ciclo5 CU24 - Usar sugerencia directamente
  usarSugerencia(s: string): void {
    this.prompt = s;
    this.generarReporte();
  }

  // #Ciclo5 CU24 - Generar por texto
  generarReporte(): void {
    if (!this.prompt.trim()) return;
    this.isLoading = true;
    this.reporte = null;
    this.errorMsg = '';
    this.filtroTexto = '';
    this.reporteService.generarReporte(this.prompt, this.periodoDias).subscribe({
      next: (res) => { this.reporte = res; this.isLoading = false; },
      error: () => { this.isLoading = false; this.errorMsg = 'Error al generar el reporte.'; }
    });
  }

  // #Ciclo5 CU24 - Grabación de voz
  toggleGrabacion(): void {
    this.isRecording ? this.detenerGrabacion() : this.iniciarGrabacion();
  }

  private iniciarGrabacion(): void {
    navigator.mediaDevices.getUserMedia({ audio: true }).then(stream => {
      this.mediaRecorder = new MediaRecorder(stream);
      this.audioChunks = [];
      this.mediaRecorder.ondataavailable = (e) => this.audioChunks.push(e.data);
      this.mediaRecorder.onstop = () => {
        const blob = new Blob(this.audioChunks, { type: 'audio/webm' });
        const reader = new FileReader();
        reader.onloadend = () => this.enviarAudioReporte(reader.result as string);
        reader.readAsDataURL(blob);
        stream.getTracks().forEach(t => t.stop());
      };
      this.mediaRecorder.start();
      this.isRecording = true;
    }).catch(() => this.errorMsg = 'No se pudo acceder al micrófono.');
  }

  private detenerGrabacion(): void {
    this.mediaRecorder?.stop();
    this.isRecording = false;
  }

  private enviarAudioReporte(audioBase64: string): void {
    this.isLoading = true;
    this.reporte = null;
    this.errorMsg = '';
    this.filtroTexto = '';
    this.reporteService.generarReportePorVoz(audioBase64, this.periodoDias).subscribe({
      next: (res) => {
        this.reporte = res;
        this.prompt = res.prompt_procesado;
        this.isLoading = false;
      },
      error: () => { this.isLoading = false; this.errorMsg = 'Error al procesar el audio.'; }
    });
  }

  // ── TABLA ──────────────────────────────────────────────
  getTipo(): string {
    return this.reporte?.datos_periodo?.['tipo'] || 'general';
  }

  getColumnas(): string[] {
    return this.reporte?.datos_periodo?.['columnas'] || [];
  }

  getHeaderLabel(col: string): string {
    const tipo = this.getTipo();
    return this.HEADERS[tipo]?.[col] || col;
  }

  getFilas(): any[] {
    const filas: any[] = this.reporte?.datos_periodo?.['filas'] || [];
    if (!this.filtroTexto.trim()) return filas;
    const f = this.filtroTexto.toLowerCase();
    return filas.filter(row =>
      Object.values(row).some(v => String(v).toLowerCase().includes(f))
    );
  }

  // ── EXPORTAR PDF ────────────────────────────────────────
  exportarPDF(): void {
    if (!this.reporte) return;
    const datos = this.reporte.datos_periodo;
    const tipo = datos?.['tipo'] || 'general';
    const filas: any[] = datos?.['filas'] || [];
    const cols = this.getColumnas();
    const titulo = this.TITULOS[tipo] || 'Reporte';
    const fecha = `${datos?.['fecha_inicio']} al ${datos?.['fecha_fin']}`;

    // Construir HTML del PDF
    let tablaHtml = '';
    if (cols.length && filas.length) {
      const headers = cols.map(c => `<th>${this.getHeaderLabel(c)}</th>`).join('');
      const rows = filas.map(f =>
        `<tr>${cols.map(c => `<td>${f[c] ?? ''}</td>`).join('')}</tr>`
      ).join('');
      tablaHtml = `<table border="1" cellpadding="6" cellspacing="0" style="border-collapse:collapse;width:100%;font-size:13px">
        <thead style="background:#1e3a5f;color:white"><tr>${headers}</tr></thead>
        <tbody>${rows}</tbody>
      </table>`;
    }

    const html = `<!DOCTYPE html><html><head><meta charset="UTF-8">
      <title>${titulo}</title>
      <style>body{font-family:Arial,sans-serif;padding:24px;color:#1e293b}
        h1{color:#1e3a5f;font-size:20px;margin-bottom:4px}
        .meta{color:#64748b;font-size:13px;margin-bottom:20px}
        .resumen{background:#f8fafc;border-left:4px solid #3b82f6;padding:14px;margin-bottom:20px;font-size:14px;line-height:1.6}
        th{text-align:left;padding:8px}td{padding:8px}tr:nth-child(even){background:#f1f5f9}
      </style></head><body>
      <h1>${titulo}</h1>
      <p class="meta">Período: ${fecha}</p>
      <div class="resumen">${(this.reporte.reporte_markdown || '').replace(/\n/g, '<br>')}</div>
      ${tablaHtml}
      <p style="margin-top:20px;font-size:11px;color:#94a3b8">
        Generado por Sistema de Emergencias Vehiculares — ${new Date().toLocaleString()}
      </p>
    </body></html>`;

    const win = window.open('', '_blank');
    if (win) {
      win.document.write(html);
      win.document.close();
      win.focus();
      setTimeout(() => { win.print(); win.close(); }, 500);
    }
  }

  // ── EXPORTAR EXCEL (CSV) ────────────────────────────────
  exportarExcel(): void {
    if (!this.reporte) return;
    const datos = this.reporte.datos_periodo;
    const tipo = datos?.['tipo'] || 'general';
    const filas: any[] = datos?.['filas'] || [];
    const cols = this.getColumnas();

    if (!cols.length || !filas.length) {
      alert('No hay datos tabulares para exportar.');
      return;
    }

    // BOM para UTF-8 en Excel
    const BOM = '\uFEFF';
    const headers = cols.map(c => `"${this.getHeaderLabel(c)}"`).join(';');
    const rows = filas.map(f =>
      cols.map(c => `"${String(f[c] ?? '').replace(/"/g, '""')}"`).join(';')
    ).join('\n');

    const csv = BOM + `${headers}\n${rows}`;
    const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `reporte_${tipo}_${datos?.['fecha_inicio']}.csv`;
    a.click();
    URL.revokeObjectURL(url);
  }

  // ── STATS RÁPIDAS ───────────────────────────────────────
  getStatsRapidas(): { label: string; valor: any; color: string }[] {
    const d = this.reporte?.datos_periodo;
    if (!d) return [];
    const tipo = d['tipo'];
    if (tipo === 'comisiones') return [
      { label: 'Total Pagos', valor: d['total_pagos'], color: 'blue' },
      { label: 'Ingresos Bs.', valor: (d['ingresos_totales_bs'] as number).toFixed(2), color: 'green' }
    ];
    if (tipo === 'talleres') return [
      { label: 'Talleres', valor: d['total_talleres'], color: 'blue' }
    ];
    if (tipo === 'tecnicos') return [
      { label: 'Total Técnicos', valor: d['total_tecnicos'], color: 'blue' },
      { label: 'Disponibles', valor: d['disponibles'], color: 'green' }
    ];
    if (tipo === 'clientes') return [
      { label: 'Clientes Activos', valor: d['total_clientes'], color: 'purple' }
    ];
    return [
      { label: 'Incidentes', valor: d['total_incidentes'], color: 'blue' },
      { label: 'Finalizados', valor: d['finalizados'], color: 'green' },
      { label: 'Tasa Éxito', valor: `${d['tasa_exito']}%`, color: 'purple' },
      { label: 'Ingresos Bs.', valor: d['ingresos_totales_bs'], color: 'gold' }
    ];
  }

  esNumero(val: any): boolean {
    return typeof val === 'number';
  }
}


