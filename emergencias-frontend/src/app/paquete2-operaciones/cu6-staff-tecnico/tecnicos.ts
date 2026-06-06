// ============================================================
// src/app/paquete2-operaciones/cu6-staff-tecnico/tecnicos.ts
//
// CU6: Administrar Staff Técnico
import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms'; 
import { TecnicoService } from '../../core/services/tecnico'; 
import { TecnicoOut } from '../../shared/models/tecnico.model';

@Component({
  selector: 'app-tecnicos',
  standalone: true,
  imports: [CommonModule, FormsModule], 
  templateUrl: './tecnicos.html',
  styleUrls: ['./tecnicos.css']
})
export class TecnicosComponent implements OnInit {
  tecnicos: TecnicoOut[] = [];
  
  cargando: boolean = false;
  mostrarModal: boolean = false;
  tallerId: number = 0;

  nuevoTecnico = {
    nombre: '',
    email: '',
    password: '',
    telefono: '',
    especialidad: 'Mecanico',
    taller_id: 0
  };

  constructor(private tecnicoService: TecnicoService) {}

  ngOnInit(): void {
    const idEntidad = localStorage.getItem('id_entidad');
    this.tallerId = Number(idEntidad) || 0;

    if (this.tallerId !== 0) {
      this.cargarTecnicos();
    } else {
      console.warn("No se encontró ID de taller en la sesión.");
    }
  }

  cargarTecnicos(): void {
    this.cargando = true;
    this.tecnicoService.getTecnicosByTaller(this.tallerId).subscribe({
      next: (data) => {
        this.tecnicos = data;
        this.cargando = false;
      },
      error: (err) => {
        console.error('Error al cargar técnicos', err);
        this.cargando = false;
      }
    });
  }

  cambiarDisponibilidad(tecnico: TecnicoOut): void {
    const nuevoEstado = !tecnico.disponible_boolean;
    
    this.tecnicoService.updateDisponibilidad(tecnico.id_tecnico, { disponible_boolean: nuevoEstado })
      .subscribe({
        next: (tecnicoActualizado) => {
          tecnico.disponible_boolean = tecnicoActualizado.disponible_boolean;
        },
        error: (err) => console.error('Error al actualizar disponibilidad', err)
      });
  }

  eliminarTecnico(id: number): void {
    if(confirm('¿Estás seguro de eliminar a este técnico? Perderá el acceso a la App Móvil.')) {
      this.tecnicoService.deleteTecnico(id).subscribe({
        next: () => {
          this.tecnicos = this.tecnicos.filter(t => t.id_tecnico !== id);
        },
        error: (err) => console.error('Error al eliminar', err)
      });
    }
  }


  abrirModalNuevo(): void {
    this.limpiarFormulario();
    this.nuevoTecnico.taller_id = this.tallerId;
    
    this.mostrarModal = true;
  }

  cerrarModal(): void {
    this.mostrarModal = false;
  }

  guardarTecnico(): void {
    this.cargando = true;
    this.tecnicoService.crearTecnico(this.nuevoTecnico).subscribe({
      next: (res) => {
        this.cargando = false;
        alert('¡Técnico contratado exitosamente! 👨‍🔧');
        this.mostrarModal = false;
        this.cargarTecnicos();
      },
      error: (err) => {
        this.cargando = false; 
        console.error("Error detallado:", err);
        const errorMsg = err.error?.detail || "Error de conexión con el servidor";
        alert('Error: ' + errorMsg);
      }
    });
  }

  private limpiarFormulario(): void {
    this.nuevoTecnico = {
      nombre: '',
      email: '',
      password: '',
      telefono: '',
      especialidad: 'Mecanico',
      taller_id: this.tallerId
    };
  }
}
