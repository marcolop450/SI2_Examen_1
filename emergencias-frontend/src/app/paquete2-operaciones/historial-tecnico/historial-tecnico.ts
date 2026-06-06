import { Component, OnInit, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { HttpClient, HttpHeaders } from '@angular/common/http';

@Component({
  selector: 'app-historial-tecnico',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './historial-tecnico.html',
  styleUrls: ['./historial-tecnico.css']
})
export class HistorialTecnico implements OnInit {
  private http = inject(HttpClient);
  
  historial: any[] = [];
  cargando = true;
  idTecnico: number = 0;

  ngOnInit(): void {
    this.idTecnico = Number(localStorage.getItem('id_entidad')) || 0;
    
    if (this.idTecnico === 0) {
      this.cargando = false;
      return;
    }
    
    this.cargarHistorial();
  }

  cargarHistorial(): void {
    const token = localStorage.getItem('token');
    const headers = new HttpHeaders({
      'Authorization': `Bearer ${token}`
    });

    this.http.get<any[]>(`https://backend-ixkv.onrender.com/incidentes/historial/tecnico/${this.idTecnico}`, { headers }).subscribe({
      next: (data) => {
        this.historial = data;
        this.cargando = false;
      },
      error: () => {
        this.cargando = false;
      }
    });
  }
}
