import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { HttpClient } from '@angular/common/http';

@Component({
  selector: 'app-perfil',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './cu4-perfil.html',
  styleUrls: ['./cu4-perfil.css']
})
export class Cu4Perfil implements OnInit {
  usuario = { 
    nombre: localStorage.getItem('nombre') || '', 
    email: '', 
    telefono: '', 
    rol: localStorage.getItem('rol') || '' 
  };
  
  cargando = false;
  mensaje = '';

  private apiUrl = 'http://127.0.0.1:8000';

  constructor(private http: HttpClient) {}

  ngOnInit() {
    // Cargamos los datos desde localStorage directamente — no necesitamos GET
    this.usuario.nombre = localStorage.getItem('nombre') || '';
    this.usuario.rol    = localStorage.getItem('rol') || '';
  }

  actualizar() {
    this.cargando = true;
    // PUT /usuarios/me — disponible para cualquier usuario autenticado
    const payload = {
      nombre:   this.usuario.nombre,
      telefono: this.usuario.telefono
    };
    this.http.put(`${this.apiUrl}/usuarios/me`, payload).subscribe({
      next: () => {
        this.cargando = false;
        this.mensaje  = '¡Perfil actualizado! ✅';
        localStorage.setItem('nombre', this.usuario.nombre);
        setTimeout(() => this.mensaje = '', 3000);
      },
      error: (err) => {
        this.cargando = false;
        console.error('Error perfil:', err);
        alert('Error al actualizar datos.');
      }
    });
  }
}
