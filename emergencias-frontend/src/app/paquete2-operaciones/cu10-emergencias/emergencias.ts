import { Component, OnInit, OnDestroy } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { RouterModule } from '@angular/router'; // #Ciclo5 CU21 Para enlace a bitácora
import { interval, Subscription } from 'rxjs';
import Swal from 'sweetalert2'; 
import { IncidenteService } from '../../core/services/incidente';
import { TecnicoService } from '../../core/services/tecnico';
import { TecnicoOut } from '../../shared/models/tecnico.model';

@Component({
  selector: 'app-emergencias',
  standalone: true,
  imports: [CommonModule, FormsModule, RouterModule], // #Ciclo5 CU21 RouterModule para bitácora
  templateUrl: './emergencias.html',
  styleUrls: ['./emergencias.css']
})
export class EmergenciasComponent implements OnInit, OnDestroy {
  emergencias: any[] = [];
  cargando: boolean = true;
  tallerId: number = 0;
  tiemposRestantes: { [key: number]: string } = {};
  cronometroSub!: Subscription;
  mostrarModal: boolean = false;
  incidenteSeleccionado: any = null;
  tecnicosDisponibles: TecnicoOut[] = [];
  tecnicoSeleccionadoId: number | null = null;
  cargandoAsignacion: boolean = false;

  constructor(
    private incidenteService: IncidenteService,
    private tecnicoService: TecnicoService
  ) {}

  ngOnInit(): void {
    this.tallerId = Number(localStorage.getItem('id_entidad')) || 0; 
    this.cargarPendientes();

    this.cronometroSub = interval(1000).subscribe(() => {
      this.calcularTiempos();
    });
  }

  ngOnDestroy(): void {
    if (this.cronometroSub) this.cronometroSub.unsubscribe();
  }

  // ========================================================
  // LÓGICA DEL CRONÓMETRO Y PRIORIDADES 
  // ========================================================
  calcularTiempos(): void {
    const ahora = new Date().getTime();
    
    this.emergencias.forEach(em => {
      const fechaCreacion = new Date(em.fecha_creacion_timestamp).getTime();
      const limite = fechaCreacion + (5 * 60 * 1000); // 5 minutos de gracia
      const diff = limite - ahora;

      if (diff > 0) {
        const mins = Math.floor((diff % (1000 * 60 * 60)) / (1000 * 60));
        const secs = Math.floor((diff % (1000 * 60)) / 1000);
        this.tiemposRestantes[em.id_incidente] = `${mins}:${secs < 10 ? '0' : ''}${secs}`;
      } else {
        this.tiemposRestantes[em.id_incidente] = 'EXPIRADO';
      }
    });
  }

  esMiTurnoPrioritario(em: any): boolean {
    return em.taller_actual_id === this.tallerId;
  }

  estaExpirado(em: any): boolean {
    return this.tiemposRestantes[em.id_incidente] === 'EXPIRADO';
  }

  // ========================================================
  // CU10: CARGA Y RESPUESTA DE SOLICITUDES
  // ========================================================
  cargarPendientes(): void {
    this.cargando = true;
    this.incidenteService.getPendientes().subscribe({
      next: (data) => {
        this.emergencias = data;
        this.calcularTiempos();
        this.cargando = false;
      },
      error: (err) => {
        console.error('Error cargando emergencias:', err);
        this.cargando = false;
      }
    });
  }

  responder(incidente: any, accion: 'aceptar' | 'rechazar'): void {
    const confirmar = confirm(`¿Estás seguro de ${accion} esta emergencia?`);
    if (!confirmar) return;

    this.incidenteService.responderSolicitud(incidente.id_incidente, accion).subscribe({
      next: () => {
        this.emergencias = this.emergencias.filter(e => e.id_incidente !== incidente.id_incidente);
        if (accion === 'aceptar') {
          // Guardar ID para que el WebSocket de monitoreo se conecte a la sala correcta
          localStorage.setItem('incidente_activo_id', incidente.id_incidente.toString());
          this.abrirModalAsignacion(incidente);
        }
      },
      error: (err) => alert('Hubo un error al procesar la solicitud.')
    });
  }

  // ========================================================
  // CU8: LÓGICA PARA VER EL DIAGNÓSTICO IA, FOTO Y AUDIO REAL
  // ========================================================
  verAnalisisIA(incidente: any): void {
    if (!incidente.evidencias || incidente.evidencias.length === 0) {
      Swal.fire({
        title: 'Sin Datos Multimodales',
        text: 'El cliente no adjuntó imágenes ni audio.',
        icon: 'info',
        confirmButtonColor: '#0D1B2A'
      });
      return;
    }
    const imagen = incidente.evidencias.find((e: any) => e.tipo_enum === 'imagen');
    const audio = incidente.evidencias.find((e: any) => e.tipo_enum === 'audio');

    let htmlContent = `<div style="text-align: left;">`;

    htmlContent += `
      <p><strong>Descripción del cliente:</strong> <br>
        ${incidente.descripcion_texto || 'No proporcionada'}
      </p>
      <hr>
    `;

    const diagIA = imagen?.clasificacion_ia_texto || audio?.clasificacion_ia_texto || 'Evaluación en proceso...';
    htmlContent += `
      <p><strong>Análisis de la IA:</strong> <br>
        <span style="color: #E24B4A; font-weight: bold; font-size: 1.1em;">
          ${diagIA}
        </span>
      </p>
    `;

    if (audio && audio.url_recurso) {
      htmlContent += `
        <hr>
        <p><strong>🎤 Nota de Voz del Cliente:</strong></p>
        <audio controls style="width: 100%; margin-top: 5px; height: 35px;">
          <source src="${audio.url_recurso}" type="audio/mpeg">
          <source src="${audio.url_recurso}" type="audio/mp4">
          <source src="${audio.url_recurso}" type="audio/wav">
          Tu navegador no soporta el reproductor de audio.
        </audio>
        <p style="font-size: 0.85em; color: gray; margin-top: 5px; font-style: italic;">
          Transcripción IA: "${audio.transcripcion_audio_texto || 'Procesando transcripción...'}"
        </p>
      `;
    }

    htmlContent += `</div>`;

    Swal.fire({
      title: 'Reporte Inteligente (CU8)',
      html: htmlContent,
      imageUrl: imagen ? imagen.url_recurso : null,
      imageWidth: 400,
      imageAlt: 'Fotografía de la emergencia',
      confirmButtonText: 'Cerrar Reporte',
      confirmButtonColor: '#0D1B2A'
    });
  }

  // ========================================================
  // CU11: LÓGICA DEL MODAL DE ASIGNACIÓN
  // ========================================================
  abrirModalAsignacion(incidente: any): void {
    this.incidenteSeleccionado = incidente;
    this.tecnicoSeleccionadoId = null;
    this.mostrarModal = true;

    this.tecnicoService.getTecnicosByTaller(this.tallerId).subscribe({
      next: (data) => {
        this.tecnicosDisponibles = data.filter(t => t.disponible_boolean === true);
      },
      error: (err) => console.error('Error cargando técnicos', err)
    });
  }

  cerrarModal(): void {
    this.mostrarModal = false;
    this.incidenteSeleccionado = null;
  }

  confirmarAsignacion(): void {
    if (!this.tecnicoSeleccionadoId) {
      alert('Por favor, selecciona un técnico.');
      return;
    }

    this.cargandoAsignacion = true;
    this.incidenteService.asignarTecnico(this.incidenteSeleccionado.id_incidente, this.tecnicoSeleccionadoId)
      .subscribe({
        next: () => {
          alert('¡Técnico asignado y en ruta exitosamente!');
          this.cargandoAsignacion = false;
          this.cerrarModal();
        },
        error: (err) => {
          alert('Error al asignar el técnico.');
          this.cargandoAsignacion = false;
        }
      });
  }
  // CU20 — Variables del modal de excepción
  mostrarModalExcepcion: boolean = false;
  incidenteExcepcion: any = null;
  tipoExcepcion: string = '';
  motivoExcepcion: string = '';
  compensacionTaller: number = 0;

  abrirModalExcepcion(incidente: any): void {
    this.incidenteExcepcion = incidente;
    this.tipoExcepcion = '';
    this.motivoExcepcion = '';
    this.compensacionTaller = 0;
    this.mostrarModalExcepcion = true;
  }

  cerrarModalExcepcion(): void {
    this.mostrarModalExcepcion = false;
    this.incidenteExcepcion = null;
  }

  confirmarExcepcion(): void {
    if (!this.tipoExcepcion) return;

    const payload = {
      tipo_excepcion: this.tipoExcepcion,
      motivo: this.motivoExcepcion,
      compensacion_taller: this.compensacionTaller
    };

    this.incidenteService.reportarExcepcion(
      this.incidenteExcepcion.id_incidente,
      payload
    ).subscribe({
      next: () => {
        alert('Excepción registrada correctamente.');
        this.cerrarModalExcepcion();
        this.cargarPendientes();
      },
      error: () => alert('Error al registrar la excepción.')
    });
  }
}