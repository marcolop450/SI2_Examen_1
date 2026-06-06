import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { HttpClient, HttpHeaders } from '@angular/common/http';
import { DomSanitizer, SafeResourceUrl } from '@angular/platform-browser';

@Component({
  selector: 'app-ubicacion',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './ubicacion.html',
  styleUrls: ['./ubicacion.css']
})
export class UbicacionComponent implements OnInit {
  cargandoInicial = true; 
  cargandoGPS = false;    
  
  tieneUbicacion = false;
  latitudActual: number | null = null;
  longitudActual: number | null = null;
  
  mapaUrlSegura: SafeResourceUrl | null = null;
  mensajeExito = '';
  mensajeError = '';

  constructor(private http: HttpClient, private sanitizer: DomSanitizer) {}

  ngOnInit() {
    this.cargarDatosTaller();
  }

  cargarDatosTaller() {
    const token = localStorage.getItem('token');
    const headers = new HttpHeaders({ 'Authorization': `Bearer ${token}` });

    this.http.get<any>('https://backend-ixkv.onrender.com/talleres/mi-taller/perfil', { headers }).subscribe({
      next: (taller) => {
        if (taller.latitud_decimal && taller.longitud_decimal) {
          this.tieneUbicacion = true;
          this.latitudActual = taller.latitud_decimal;
          this.longitudActual = taller.longitud_decimal;
          this.generarMapa(this.latitudActual!, this.longitudActual!);
        }
        this.cargandoInicial = false;
      },
      error: () => {
        this.cargandoInicial = false;
        this.mensajeError = 'No se pudo cargar la información del taller.';
      }
    });
  }

  actualizarGPS() {
    this.cargandoGPS = true;
    this.mensajeExito = '';
    this.mensajeError = '';

    if (navigator.geolocation) {
      navigator.geolocation.getCurrentPosition(
        (position) => {
          const lat = position.coords.latitude;
          const lng = position.coords.longitude;
          const payload = { latitud_decimal: lat, longitud_decimal: lng };

          const token = localStorage.getItem('token');
          const headers = new HttpHeaders({ 'Authorization': `Bearer ${token}` });

          this.http.patch('https://backend-ixkv.onrender.com/talleres/mi-ubicacion/actualizar', payload, { headers }).subscribe({
            next: () => {
              this.latitudActual = lat;
              this.longitudActual = lng;
              this.tieneUbicacion = true;
              this.generarMapa(lat, lng);
              
              this.cargandoGPS = false;
              this.mensajeExito = '¡Coordenadas actualizadas con éxito!';
            },
            error: (err) => {
              this.cargandoGPS = false;
              this.mensajeError = err.error?.detail || 'Error de conexión.';
            }
          });
        },
        (error) => {
          this.cargandoGPS = false;
          this.mensajeError = 'Debes permitir el acceso a la ubicación en tu navegador.';
        },
        { enableHighAccuracy: true, timeout: 10000, maximumAge: 0 }
      );
    } else {
      this.cargandoGPS = false;
      this.mensajeError = 'Tu navegador no soporta geolocalización.';
    }
  }

  generarMapa(lat: number, lng: number) {
    const urlBruta = `https://maps.google.com/maps?q=${lat},${lng}&z=16&output=embed`;
    this.mapaUrlSegura = this.sanitizer.bypassSecurityTrustResourceUrl(urlBruta);
  }
}
