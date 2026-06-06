// Componente de Cotizaciones - Ciclo 5 - CU18
// Taller ve emergencias, selecciona técnico especializado y envía cotización
import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { RouterModule } from '@angular/router';
import { CotizacionService } from '../../core/services/cotizacion.service';
import { IncidenteService } from '../../core/services/incidente';
import { TecnicoService } from '../../core/services/tecnico';
import Swal from 'sweetalert2';

@Component({
  selector: 'app-cu18-cotizaciones',
  standalone: true,
  imports: [CommonModule, FormsModule, RouterModule],
  templateUrl: './cu18-cotizaciones.html',
  styleUrls: ['./cu18-cotizaciones.css']
})
export class Cu18Cotizaciones implements OnInit {
  incidentesPendientes: any[] = [];
  cargando = false;
  tallerId = 0;

  // #Ciclo5 CU18 - Técnicos disponibles del taller (para seleccionar en la cotización)
  tecnicosDisponibles: any[] = [];
  tecnicosFiltrados: { [incidenteId: number]: any[] } = {}; // Técnicos filtrados por especialidad

  // Un formulario independiente por incidente
  formularios: { [incidenteId: number]: any } = {};

  // #Ciclo5 CU18 - Mapeo categoría IA → especialidades del técnico
  private ESPECIALIDAD_MAP: Record<string, string[]> = {
    llanta:  ['llant', 'llanta', 'neumatico', 'neumático', 'tire'],
    motor:   ['mecánico', 'mecanico', 'motor', 'mecanic'],
    bateria: ['electric', 'eléctric', 'bateria', 'batería'],
    choque:  ['carrocer', 'choque', 'latonería', 'latoneria', 'pintura'],
    otros:   [],
  };

  // #Ciclo5 CU18 - Iconos y etiquetas para las categorías de emergencia
  CATEGORIA_ICONOS: Record<string, string> = {
    llanta: '🛞', motor: '🔧', bateria: '⚡', choque: '🚗', otros: '🆘'
  };

  constructor(
    private cotizacionService: CotizacionService,
    private incidenteService: IncidenteService,
    private tecnicoService: TecnicoService
  ) {}

  ngOnInit() {
    this.tallerId = Number(localStorage.getItem('id_entidad')) || 0;
    this.cargarIncidentes();
    if (this.tallerId) {
      this.cargarTecnicos();
    }
  }

  // #Ciclo5 CU18 - Cargar técnicos disponibles del taller
  cargarTecnicos(): void {
    this.tecnicoService.getTecnicosByTaller(this.tallerId).subscribe({
      next: (data) => {
        this.tecnicosDisponibles = data.filter((t: any) => t.disponible_boolean === true);
        // Re-filtrar si ya hay incidentes cargados
        this.incidentesPendientes.forEach(inc => {
          this.filtrarTecnicosParaIncidente(inc);
        });
      },
      error: () => {}
    });
  }

  cargarIncidentes() {
    this.cargando = true;
    this.incidenteService.getPendientes().subscribe({
      next: (data) => {
        this.incidentesPendientes = data;
        data.forEach((inc: any) => {
          if (!this.formularios[inc.id_incidente]) {
            this.formularios[inc.id_incidente] = {
              precio_estimado: null,
              tiempo_estimado_min: null,
              descripcion: '',
              tecnico_id: null
            };
          }
          // #Ciclo5 CU18 - Filtrar técnicos con la especialidad correcta para esta emergencia
          this.filtrarTecnicosParaIncidente(inc);
        });
        this.cargando = false;
      },
      error: () => { this.cargando = false; }
    });
  }

  // #Ciclo5 CU18 - Filtrar técnicos disponibles según la categoría IA del incidente
  filtrarTecnicosParaIncidente(inc: any): void {
    const categoria = this.extraerCategoria(inc);
    const keywords = this.ESPECIALIDAD_MAP[categoria] || [];

    if (keywords.length === 0) {
      // Categoría "otros" → cualquier técnico disponible sirve
      this.tecnicosFiltrados[inc.id_incidente] = this.tecnicosDisponibles;
      return;
    }

    const especialistas = this.tecnicosDisponibles.filter((tec: any) => {
      const esp = (tec.especialidad || '').toLowerCase();
      return keywords.some(kw => esp.includes(kw));
    });

    // Si hay especialistas, mostrar solo ellos. Si no, mostrar todos (aviso al usuario)
    this.tecnicosFiltrados[inc.id_incidente] = especialistas.length > 0
      ? especialistas
      : this.tecnicosDisponibles;
  }

  // #Ciclo5 CU18 - Extraer categoría del diagnóstico IA
  extraerCategoria(inc: any): string {
    const texto: string = inc.evidencias?.[0]?.clasificacion_ia_texto || '';
    const match = texto.match(/\[(\w+)\]/);
    return match ? match[1].toLowerCase() : 'otros';
  }

  getCategoriaIcono(inc: any): string {
    return this.CATEGORIA_ICONOS[this.extraerCategoria(inc)] || '🆘';
  }

  // #Ciclo5 CU18 - ¿El taller tiene técnico especializado para esta categoría?
  tieneEspecialista(inc: any): boolean {
    const categoria = this.extraerCategoria(inc);
    const keywords = this.ESPECIALIDAD_MAP[categoria] || [];
    if (keywords.length === 0) return true;
    return this.tecnicosDisponibles.some((tec: any) => {
      const esp = (tec.especialidad || '').toLowerCase();
      return keywords.some(kw => esp.includes(kw));
    });
  }

  // #Ciclo5 CU18 - Nombre del técnico seleccionado para mostrar en el formulario
  getNombreTecnico(incidenteId: number): string {
    const tecId = this.formularios[incidenteId]?.tecnico_id;
    if (!tecId) return '';
    const tec = this.tecnicosDisponibles.find((t: any) => t.id_tecnico === tecId);
    return tec ? `${tec.nombre} (${tec.especialidad || 'General'})` : '';
  }

  // #Ciclo5 CU18 - Enviar cotización con técnico seleccionado
  enviarCotizacion(incidenteId: number) {
    const form = this.formularios[incidenteId];

    if (!form?.precio_estimado || form.precio_estimado <= 0) {
      Swal.fire('Error', 'Ingresá un precio estimado válido (mayor a 0).', 'warning');
      return;
    }
    if (!form?.tiempo_estimado_min || form.tiempo_estimado_min <= 0) {
      Swal.fire('Error', 'Ingresá un tiempo estimado válido.', 'warning');
      return;
    }
    if (!form?.tecnico_id) {
      Swal.fire('Técnico requerido', 'Debes seleccionar un técnico antes de cotizar.', 'warning');
      return;
    }

    const payload = {
      incidente_id: incidenteId,
      precio_estimado: form.precio_estimado,
      tiempo_estimado_min: form.tiempo_estimado_min,
      descripcion: form.descripcion || '',
      tecnico_id: form.tecnico_id   // #Ciclo5 CU18 - Técnico especializado seleccionado
    };

    this.cotizacionService.enviarCotizacion(payload).subscribe({
      next: () => {
        Swal.fire({
          icon: 'success',
          title: '✅ Cotización enviada',
          text: `Tu propuesta fue enviada al cliente. Técnico asignado: ${this.getNombreTecnico(incidenteId)}`,
          confirmButtonColor: '#10b981'
        });
        // Limpiar formulario y quitar de la lista
        this.formularios[incidenteId] = { precio_estimado: null, tiempo_estimado_min: null, descripcion: '', tecnico_id: null };
        this.incidentesPendientes = this.incidentesPendientes.filter(i => i.id_incidente !== incidenteId);
      },
      error: (err) => {
        const msg = err?.error?.detail || 'Error al enviar la cotización.';
        Swal.fire('Error', msg, 'error');
      }
    });
  }
}
