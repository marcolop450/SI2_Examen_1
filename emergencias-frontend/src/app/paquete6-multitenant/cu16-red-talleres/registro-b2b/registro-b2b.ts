import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ReactiveFormsModule, FormBuilder, FormGroup, Validators } from '@angular/forms';
import { RouterModule, Router, ActivatedRoute } from '@angular/router';
import { TenantService } from '../../../core/services/tenant.service';
import { TenantRegisterRequest } from '../saas.interface';

@Component({
  selector: 'app-registro-b2b',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule, RouterModule],
  templateUrl: './registro-b2b.html',
  styleUrls: ['./registro-b2b.css']
})
export class RegistroB2bComponent implements OnInit {
  registroForm!: FormGroup;
  enviando = false;
  mensajeExito: string | null = null;
  mensajeError: string | null = null;

  constructor(
    private fb: FormBuilder,
    private tenantService: TenantService,
    private router: Router,
    private route: ActivatedRoute
  ) {}

  ngOnInit(): void {
    this.registroForm = this.fb.group({
      tenant: this.fb.group({
        nombre_comercial: ['', Validators.required],
        subdominio:       ['', [Validators.required, Validators.pattern(/^[a-z0-9-]+$/)]],
        plan_id:          [null]
      }),
      taller: this.fb.group({
        nombre:           ['', Validators.required],
        direccion:        [''],
        nit:              [''],
        latitud_decimal:  [null],
        longitud_decimal: [null]
      }),
      usuario: this.fb.group({
        nombre:   ['', Validators.required],
        email:    ['', [Validators.required, Validators.email]],
        password: ['', [Validators.required, Validators.minLength(6)]],
        telefono: ['']
      })
    });

    // Captura plan_id desde queryParams de la Landing
    this.route.queryParams.subscribe(params => {
      if (params['plan_id']) {
        this.registroForm.get('tenant.plan_id')?.setValue(+params['plan_id']);
      }
    });
  }

  onSubmit(): void {
    if (this.registroForm.invalid) {
      this.registroForm.markAllAsTouched();
      return;
    }

    this.enviando = true;
    this.mensajeError = null;

    const payload: TenantRegisterRequest = this.registroForm.value;

    this.tenantService.registrarEmpresa(payload).subscribe({
      next: () => {
        this.enviando = false;
        this.mensajeExito = '¡Empresa registrada con éxito! Redirigiendo al login...';
        setTimeout(() => this.router.navigate(['/login']), 2500);
      },
      error: (err) => {
        this.enviando = false;
        this.mensajeError = err.error?.detail || 'Error al registrar la empresa. Intente nuevamente.';
      }
    });
  }

  campoInvalido(ruta: string): boolean {
    const control = this.registroForm.get(ruta);
    return !!(control && control.invalid && control.touched);
  }
}
