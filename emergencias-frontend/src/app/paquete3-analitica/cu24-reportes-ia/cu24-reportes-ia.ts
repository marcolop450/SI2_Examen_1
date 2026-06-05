// Componente de Reportes Inteligentes con IA - Ciclo 5 - CU24
// Genera reportes ejecutivos por texto o voz usando Groq
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
  // Datos del formulario - Ciclo 5 - CU24
  prompt: string = '';
  periodoDias: number = 30;
  reporte: ReporteResponse | null = null;
  isLoading = false;
  isRecording = false;
  mostrarDatos = false;

  // MediaRecorder para grabación de voz - Ciclo 5 - CU24
  private mediaRecorder: MediaRecorder | null = null;
  private audioChunks: Blob[] = [];

  // Sugerencias de prompts predefinidos - Ciclo 5 - CU24
  sugerencias: string[] = [
    'Resumen ejecutivo del último mes',
    'Análisis de rendimiento por taller',
    'Incidentes críticos recientes',
    'Tendencias de ingresos y pagos',
    'Estado de los técnicos y disponibilidad'
  ];

  // Opciones de periodo - Ciclo 5 - CU24
  periodos = [
    { label: '7 días', value: 7 },
    { label: '15 días', value: 15 },
    { label: '30 días', value: 30 },
    { label: '90 días', value: 90 }
  ];

  constructor(private reporteService: ReporteIaService) {}

  // Usar sugerencia como prompt - Ciclo 5 - CU24
  usarSugerencia(s: string): void {
    this.prompt = s;
  }

  // Generar reporte por texto - Ciclo 5 - CU24
  generarReporte(): void {
    if (!this.prompt.trim()) return;
    this.isLoading = true;
    this.reporte = null;
    this.reporteService.generarReporte(this.prompt, this.periodoDias).subscribe({
      next: (res) => { this.reporte = res; this.isLoading = false; },
      error: () => { this.isLoading = false; }
    });
  }

  // Toggle grabación de voz - Ciclo 5 - CU24
  toggleGrabacion(): void {
    if (this.isRecording) {
      this.detenerGrabacion();
    } else {
      this.iniciarGrabacion();
    }
  }

  // Iniciar grabación con MediaRecorder - Ciclo 5 - CU24
  private iniciarGrabacion(): void {
    navigator.mediaDevices.getUserMedia({ audio: true }).then(stream => {
      this.mediaRecorder = new MediaRecorder(stream);
      this.audioChunks = [];
      this.mediaRecorder.ondataavailable = (e) => { this.audioChunks.push(e.data); };
      this.mediaRecorder.onstop = () => {
        const blob = new Blob(this.audioChunks, { type: 'audio/webm' });
        const reader = new FileReader();
        reader.onloadend = () => {
          const base64 = reader.result as string;
          this.enviarAudioReporte(base64);
        };
        reader.readAsDataURL(blob);
        stream.getTracks().forEach(t => t.stop());
      };
      this.mediaRecorder.start();
      this.isRecording = true;
    }).catch(() => {
      alert('No se pudo acceder al micrófono.');
    });
  }

  // Detener grabación - Ciclo 5 - CU24
  private detenerGrabacion(): void {
    if (this.mediaRecorder) {
      this.mediaRecorder.stop();
      this.isRecording = false;
    }
  }

  // Enviar audio para generar reporte - Ciclo 5 - CU24
  private enviarAudioReporte(audioBase64: string): void {
    this.isLoading = true;
    this.reporte = null;
    this.reporteService.generarReportePorVoz(audioBase64, this.periodoDias).subscribe({
      next: (res) => {
        this.reporte = res;
        this.prompt = res.prompt_procesado;
        this.isLoading = false;
      },
      error: () => { this.isLoading = false; }
    });
  }

  // Copiar reporte al portapapeles - Ciclo 5 - CU24
  copiarReporte(): void {
    if (this.reporte) {
      navigator.clipboard.writeText(this.reporte.reporte_markdown);
    }
  }

  // Descargar reporte como .txt - Ciclo 5 - CU24
  descargarReporte(): void {
    if (this.reporte) {
      const blob = new Blob([this.reporte.reporte_markdown], { type: 'text/plain' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `reporte_${new Date().toISOString().split('T')[0]}.txt`;
      a.click();
      URL.revokeObjectURL(url);
    }
  }

  // Toggle mostrar datos crudos - Ciclo 5 - CU24
  toggleDatos(): void {
    this.mostrarDatos = !this.mostrarDatos;
  }
}
