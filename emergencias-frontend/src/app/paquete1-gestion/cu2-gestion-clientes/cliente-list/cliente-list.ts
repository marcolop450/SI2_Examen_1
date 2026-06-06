import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterModule } from '@angular/router';
import { FormsModule } from '@angular/forms'; // <--- 1. Importante importar esto
import { UsuarioService } from '../../../core/services/usuario';
import { Usuario } from '../../../shared/models/usuario.model';

@Component({
  selector: 'app-cliente-list',
  standalone: true,
  imports: [CommonModule, RouterModule, FormsModule],
  templateUrl: './cliente-list.html',
  styleUrl: './cliente-list.css' 
})
export class ClienteList implements OnInit {
  usuarios: Usuario[] = [];
  cargando: boolean = true;
  error: string | null = null;
  usuarioEditando: any = null; 

  constructor(private usuarioService: UsuarioService) {}

  ngOnInit(): void {
    this.cargarUsuarios();
  }

  cargarUsuarios() {
    this.usuarioService.getUsuarios().subscribe({
      next: (datos) => {
        this.usuarios = datos;
        this.cargando = false;
      },
      error: (err) => {
        this.error = "Error al cargar usuarios.";
        this.cargando = false;
      }
    });
  }

  // --- NUEVAS FUNCIONES ---

  eliminarUsuario(id: number, nombre: string) {
    
    if (confirm(`¿Estás súper seguro de eliminar a ${nombre}?`)) {
      this.usuarioService.deleteUsuario(id).subscribe({
        next: () => {
          alert('Usuario eliminado correctamente');
          this.cargarUsuarios(); 
        },
        error: (err) => alert('Error al eliminar: ' + err.error?.detail)
      });
    }
  }

  abrirEditar(user: Usuario) {
    this.usuarioEditando = { ...user };
  }

  guardarEdicion() {
    const id = this.usuarioEditando.id_usuario;
    
    const datosUpdate = {
      nombre: this.usuarioEditando.nombre,
      telefono: this.usuarioEditando.telefono,
      rol: this.usuarioEditando.rol
    };

    this.usuarioService.updateUsuario(id, datosUpdate).subscribe({
      next: () => {
        alert('Datos actualizados con éxito');
        this.usuarioEditando = null; 
        this.cargarUsuarios();
      },
      error: (err) => alert('Error al actualizar: ' + err.error?.detail)
    });
  }

  cancelarEdicion() {
    this.usuarioEditando = null;
  }
}
