import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterModule } from '@angular/router';
import { FormsModule } from '@angular/forms';
import { TallerService } from '../../../core/services/taller';
import { Taller } from '../../../shared/models/taller.model';

@Component({
  selector: 'app-taller-list',
  standalone: true,
  imports: [CommonModule, RouterModule, FormsModule],
  templateUrl: './taller-list.html',
  styleUrls: ['./taller-list.css'] // opcional
})
export class TallerList implements OnInit {
  talleres: Taller[] = [];
  cargando: boolean = true;
  error: string | null = null;
  
  // Variables para el formulario
  mostrarFormulario: boolean = false;
  modoEdicion: boolean = false;
  tallerActual: any = {}; 

  constructor(private tallerService: TallerService) {}

  ngOnInit(): void {
    this.cargarTalleres();
  }

  cargarTalleres() {
    this.cargando = true;
    this.tallerService.getTalleres().subscribe({
      next: (datos) => {
        this.talleres = datos;
        this.cargando = false;
      },
      error: (err) => {
        this.error = "Error al cargar los talleres.";
        this.cargando = false;
      }
    });
  }

  abrirNuevoTaller() {
    this.modoEdicion = false;
    this.tallerActual = {}; // Limpia el formulario
    this.mostrarFormulario = true;
  }

  abrirEditar(taller: Taller) {
    this.modoEdicion = true;
    // Pre-llenamos el formulario con los datos mapeados a lo que espera el backend
    this.tallerActual = {
      id_taller: taller.id_taller,
      nombre_dueno: taller.nombre_dueno,
      telefono: taller.telefono_dueno,
      nombre_taller: taller.nombre_taller,
      direccion: taller.direccion,
      nit: taller.nit
    };
    this.mostrarFormulario = true;
  }

  guardarTaller() {
    if (this.modoEdicion) {
      // PATCH (Editar)
      const id = this.tallerActual.id_taller;
      this.tallerService.updateTaller(id, this.tallerActual).subscribe({
        next: () => {
          alert('Taller actualizado exitosamente');
          this.mostrarFormulario = false;
          this.cargarTalleres();
        },
        error: (err) => alert('Error al actualizar: ' + err.error?.detail)
      });
    } else {
      // POST (Crear)
      this.tallerService.crearTaller(this.tallerActual).subscribe({
        next: () => {
          alert('Taller creado exitosamente');
          this.mostrarFormulario = false;
          this.cargarTalleres();
        },
        error: (err) => alert('Error al crear: ' + err.error?.detail)
      });
    }
  }

  eliminarTaller(id: number, nombre: string) {
    if (confirm(`¿Estás seguro de eliminar el taller '${nombre}' y a su dueño?`)) {
      this.tallerService.deleteTaller(id).subscribe({
        next: () => {
          alert('Taller eliminado correctamente');
          this.cargarTalleres();
        },
        error: (err) => alert('Error al eliminar: ' + err.error?.detail)
      });
    }
  }

  cancelar() {
    this.mostrarFormulario = false;
  }
  // ✨ NUEVO: Función para abrir Google Maps
  abrirMapa(lat: number | null | undefined, lng: number | null | undefined, nombreTaller: string) {
    if (lat && lng) {
      // Abre una nueva pestaña de Google Maps con un pin en esas coordenadas
      const url = `https://www.google.com/maps/search/?api=1&query=${lat},${lng}`;
      window.open(url, '_blank');
    } else {
      alert(`El taller '${nombreTaller}' aún no ha registrado sus coordenadas GPS.`);
    }
  }
}
