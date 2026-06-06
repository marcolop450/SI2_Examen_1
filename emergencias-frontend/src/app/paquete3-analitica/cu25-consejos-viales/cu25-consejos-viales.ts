// Componente de Consejos de Seguridad Vial - Ciclo 5 - CU25
// CRUD de consejos con filtro por categoría y gestión admin
import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ConsejoVialService, ConsejoVial } from '../../core/services/consejo-vial.service';

@Component({
  selector: 'app-cu25-consejos-viales',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './cu25-consejos-viales.html',
  styleUrls: ['./cu25-consejos-viales.css']
})
export class Cu25ConsejosVialesComponent implements OnInit {
  // Datos de consejos - Ciclo 5 - CU25
  consejos: ConsejoVial[] = [];
  filteredConsejos: ConsejoVial[] = [];
  isLoading = true;
  showForm = false;
  editingConsejo: ConsejoVial | null = null;
  rolUsuario: string = '';
  selectedCategoria: string = 'todos';

  // Formulario de consejo - Ciclo 5 - CU25
  formData = { categoria: 'general', titulo: '', contenido: '', icono: '💡' };

  // Categorías disponibles - Ciclo 5 - CU25
  categorias = ['todos', 'llanta', 'motor', 'bateria', 'choque', 'general', 'clima'];

  // Iconos por categoría - Ciclo 5 - CU25
  categoriaIconos: { [key: string]: string } = {
    todos: '📋', llanta: '🛞', motor: '🌡️', bateria: '🔋',
    choque: '🚗', general: '💡', clima: '🌧️'
  };

  // Colores por categoría para bordes - Ciclo 5 - CU25
  categoriaColores: { [key: string]: string } = {
    llanta: '#f97316', motor: '#ef4444', bateria: '#eab308',
    choque: '#dc2626', general: '#3b82f6', clima: '#14b8a6'
  };

  constructor(private consejoService: ConsejoVialService) {}

  ngOnInit(): void {
    this.rolUsuario = localStorage.getItem('rol') || '';
    this.cargarConsejos();
  }

  // Cargar todos los consejos - Ciclo 5 - CU25
  cargarConsejos(): void {
    this.isLoading = true;
    this.consejoService.getConsejos().subscribe({
      next: (data) => {
        this.consejos = data;
        this.filtrarPorCategoria(this.selectedCategoria);
        this.isLoading = false;
      },
      error: () => { this.isLoading = false; }
    });
  }

  // Filtrar por categoría - Ciclo 5 - CU25
  filtrarPorCategoria(cat: string): void {
    this.selectedCategoria = cat;
    this.filteredConsejos = cat === 'todos'
      ? [...this.consejos]
      : this.consejos.filter(c => c.categoria === cat);
  }

  // Obtener icono de categoría - Ciclo 5 - CU25
  getCategoriaIcon(cat: string): string {
    return this.categoriaIconos[cat] || '📋';
  }

  // Obtener color del borde - Ciclo 5 - CU25
  getCategoriaColor(cat: string): string {
    return this.categoriaColores[cat] || '#94a3b8';
  }

  // Mostrar/ocultar formulario - Ciclo 5 - CU25
  toggleForm(): void {
    this.showForm = !this.showForm;
    if (!this.showForm) {
      this.editingConsejo = null;
      this.formData = { categoria: 'general', titulo: '', contenido: '', icono: '💡' };
    }
  }

  // Editar un consejo existente - Ciclo 5 - CU25
  editarConsejo(c: ConsejoVial): void {
    this.editingConsejo = c;
    this.formData = { categoria: c.categoria, titulo: c.titulo, contenido: c.contenido, icono: c.icono };
    this.showForm = true;
  }

  // Guardar consejo (crear o actualizar) - Ciclo 5 - CU25
  guardarConsejo(): void {
    if (!this.formData.titulo.trim() || !this.formData.contenido.trim()) return;

    if (this.editingConsejo) {
      this.consejoService.actualizarConsejo(this.editingConsejo.id_consejo, this.formData).subscribe({
        next: () => { this.toggleForm(); this.cargarConsejos(); }
      });
    } else {
      this.consejoService.crearConsejo(this.formData).subscribe({
        next: () => { this.toggleForm(); this.cargarConsejos(); }
      });
    }
  }

  // Eliminar consejo - Ciclo 5 - CU25
  eliminarConsejo(id: number): void {
    if (confirm('¿Estás seguro de eliminar este consejo?')) {
      this.consejoService.eliminarConsejo(id).subscribe({
        next: () => { this.cargarConsejos(); }
      });
    }
  }
}
