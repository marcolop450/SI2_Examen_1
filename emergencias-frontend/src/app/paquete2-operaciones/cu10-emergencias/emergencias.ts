// Pantalla de Emergencias Entrantes - Ciclo 5 - CU10
// SOLO muestra avisos del diagnóstico IA. El flujo de cotización está en /cotizaciones
import { Component, OnInit, OnDestroy } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterModule } from '@angular/router';
import { interval, Subscription } from 'rxjs';
import Swal from 'sweetalert2';
import { IncidenteService } from '../../core/services/incidente';

@Component({
  selector: 'app-emergencias',
  standalone: true,
  imports: [CommonModule, RouterModule],
  templateUrl: './emergencias.html',
  styleUrls: ['./emergencias.css']
})
export class EmergenciasComponent implements OnInit, OnDestroy {
  emergencias: any[] = [];
  cargando = true;
  mostrarModal = false;
  htmlAnalisis = '';

  // #Ciclo5 CU10 - Auto-refresco cada 30 segundos
  private refreshSub!: Subscription;

  // Mapeo de categoría IA → estilo visual
  private CATEGORIA_CONFIG: Record<string, { clase: string; icono: string; label: string }> = {
    llanta:  { clase: 'ia-llanta',  icono: '🛞', label: 'Problema de Llanta' },
    motor:   { clase: 'ia-motor',   icono: '🔧', label: 'Falla de Motor' },
    bateria: { clase: 'ia-bateria', icono: '⚡', label: 'Batería Descargada' },
    choque:  { clase: 'ia-choque',  icono: '🚗', label: 'Choque / Colisión' },
    otros:   { clase: 'ia-otros',   icono: '🆘', label: 'Emergencia General' },
  };

  constructor(private incidenteService: IncidenteService) {}

  ngOnInit(): void {
    this.cargarPendientes();
    // #Ciclo5 CU10 - Refrescar automáticamente cada 30s para nuevas emergencias
    this.refreshSub = interval(30000).subscribe(() => this.cargarPendientes());
  }

  ngOnDestroy(): void {
    if (this.refreshSub) this.refreshSub.unsubscribe();
  }

  cargarPendientes(): void {
    this.cargando = true;
    this.incidenteService.getPendientes().subscribe({
      next: (data) => {
        this.emergencias = data;
        this.cargando = false;
      },
      error: () => { this.cargando = false; }
    });
  }

  // #Ciclo5 CU10 - Extraer categoría del texto IA
  private extraerCategoria(em: any): string {
    const texto: string = em.evidencias?.[0]?.clasificacion_ia_texto || '';
    const match = texto.match(/\[(\w+)\]/);
    return match ? match[1].toLowerCase() : 'otros';
  }

  getCategoriaClass(em: any): string {
    const cat = this.extraerCategoria(em);
    return this.CATEGORIA_CONFIG[cat]?.clase || 'ia-otros';
  }

  getCategoriaIcono(em: any): string {
    const cat = this.extraerCategoria(em);
    return this.CATEGORIA_CONFIG[cat]?.icono || '🆘';
  }

  getCategoriaTexto(em: any): string {
    const cat = this.extraerCategoria(em);
    return this.CATEGORIA_CONFIG[cat]?.label || 'Emergencia General';
  }

  // #Ciclo5 CU8 - Modal de análisis IA completo
  verAnalisisIA(em: any): void {
    if (!em.evidencias?.length) {
      Swal.fire({ title: 'Sin evidencias', text: 'El cliente no adjuntó imágenes ni audio.', icon: 'info' });
      return;
    }
    const imagen = em.evidencias.find((e: any) => e.tipo_enum === 'imagen');
    const audio  = em.evidencias.find((e: any) => e.tipo_enum === 'audio');
    const diagIA = imagen?.clasificacion_ia_texto || audio?.clasificacion_ia_texto || 'En proceso...';

    let html = `<div style="text-align:left">
      <p><strong>Descripción del cliente:</strong><br>${em.descripcion_texto || 'No proporcionada'}</p>
      <hr>
      <p><strong>Diagnóstico IA:</strong><br>
        <span style="color:#E24B4A;font-weight:bold;font-size:1.1em">${diagIA}</span>
      </p>`;

    if (audio?.url_recurso) {
      html += `<hr><p><strong>🎤 Audio del cliente:</strong></p>
        <audio controls style="width:100%;height:35px">
          <source src="${audio.url_recurso}" type="audio/mpeg">
          <source src="${audio.url_recurso}" type="audio/mp4">
        </audio>
        <p style="font-size:.85em;color:gray;font-style:italic">
          Transcripción: "${audio.transcripcion_audio_texto || 'Procesando...'}"
        </p>`;
    }
    html += '</div>';

    Swal.fire({
      title: `🤖 Análisis IA — Incidente #${em.id_incidente}`,
      html,
      imageUrl: imagen?.url_recurso || undefined,
      imageWidth: 380,
      confirmButtonText: 'Cerrar',
      confirmButtonColor: '#0D1B2A'
    });
  }

  cerrarModal(): void {
    this.mostrarModal = false;
    this.htmlAnalisis = '';
  }
}
