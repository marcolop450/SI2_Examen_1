import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterModule } from '@angular/router';
import { FormBuilder, FormGroup, Validators, ReactiveFormsModule } from '@angular/forms';
import { TenantService } from '../../../core/services/tenant.service';
import { TallerService } from '../../../core/services/taller';

@Component({
  selector: 'app-dashboard-owner',
  standalone: true,
  imports: [CommonModule, RouterModule, ReactiveFormsModule],
  templateUrl: './dashboard-owner.html',
  styleUrls: ['./dashboard-owner.css']
})
export class DashboardOwnerComponent implements OnInit {
  nombreRed = '';
  subdominio = '';
  nombrePlan = '';
  estadoSuscripcion = '';
  fechaVencimiento = '';
  diasRestantes = 0;

  talleresCreados = 0;
  limiteTalleres = 0;
  porcentajeUso = 0;
  limiteAlcanzado = false;

  talleres: any[] = [];

  mostrarFormulario = false;
  tallerForm!: FormGroup;
  enviando = false;
  mensajeExito = '';
  mensajeError = '';

  constructor(
    private tenantService: TenantService,
    private tallerService: TallerService,
    private fb: FormBuilder
  ) {}

  ngOnInit(): void {
    this.cargarDatos();
    this.tallerForm = this.fb.group({
      nombre_taller: ['', Validators.required],
      direccion: [''],
      nit: [''],
      nombre_dueno: ['', Validators.required],
      email: ['', [Validators.required, Validators.email]],
      password: ['', [Validators.required, Validators.minLength(6)]],
      telefono: [''],
      latitud_decimal: [null],
      longitud_decimal: [null]
    });
  }

  cargarDatos(): void {
    this.tenantService.obtenerDashboardOwner().subscribe({
      next: (data) => {
        this.nombreRed = data.nombre_red;
        this.subdominio = data.subdominio;
        this.nombrePlan = data.nombre_plan;
        this.estadoSuscripcion = data.estado_suscripcion;
        this.fechaVencimiento = data.fecha_vencimiento;
        this.limiteTalleres = data.limite_talleres;
        this.talleresCreados = data.talleres_creados;
        this.talleres = data.talleres;
        this.calcularMetricas();
      },
      error: (err) => console.error(err)
    });
  }

  private calcularMetricas(): void {
    if (this.limiteTalleres > 0) {
      this.porcentajeUso = Math.round((this.talleresCreados / this.limiteTalleres) * 100);
      this.limiteAlcanzado = this.talleresCreados >= this.limiteTalleres;
    }

    if (this.fechaVencimiento) {
      const hoy = new Date();
      const vencimiento = new Date(this.fechaVencimiento);
      const diff = vencimiento.getTime() - hoy.getTime();
      this.diasRestantes = Math.max(0, Math.ceil(diff / (1000 * 60 * 60 * 24)));
    }
  }

  toggleFormulario(): void {
    this.mostrarFormulario = !this.mostrarFormulario;
    this.mensajeExito = '';
    this.mensajeError = '';
    if (this.mostrarFormulario) {
      this.tallerForm.reset();
    }
  }

  obtenerUbicacionGPS(): void {
    if (!navigator.geolocation) {
      alert('Tu navegador no soporta geolocalización');
      return;
    }
    navigator.geolocation.getCurrentPosition(
      (position) => {
        this.tallerForm.patchValue({
          latitud_decimal: position.coords.latitude,
          longitud_decimal: position.coords.longitude
        });
      },
      (error) => {
        alert('No se pudo obtener la ubicación.');
      }
    );
  }

  crearSucursal(): void {
    if (this.tallerForm.invalid) {
      this.tallerForm.markAllAsTouched();
      return;
    }

    if (this.limiteAlcanzado) {
      this.mensajeError = "Has alcanzado el límite de talleres de tu plan.";
      return;
    }

    this.enviando = true;
    this.mensajeError = '';
    this.mensajeExito = '';

    this.tallerService.crearTaller(this.tallerForm.value).subscribe({
      next: () => {
        this.enviando = false;
        this.mensajeExito = "Sucursal registrada con éxito.";
        this.mostrarFormulario = false;
        this.cargarDatos(); // Recargar la tabla
      },
      error: (err) => {
        this.enviando = false;
        this.mensajeError = err.error?.detail || "Ocurrió un error al crear la sucursal.";
      }
    });
  }
}
