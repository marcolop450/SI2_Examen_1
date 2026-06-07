import { Component, OnInit, NgZone } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ReactiveFormsModule, FormBuilder, FormGroup, Validators } from '@angular/forms';
import { RouterModule, Router, ActivatedRoute } from '@angular/router';
import { TenantService } from '../../../core/services/tenant.service';
import { TenantRegisterRequest } from '../saas.interface';
import { loadScript } from "@paypal/paypal-js";

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
  
  mostrarPago = false;
  registroCompletado = false;
  emailRegistrado = '';
  montoPlan = '0.00'; // Se calculará según el plan

  constructor(
    private fb: FormBuilder,
    private tenantService: TenantService,
    private router: Router,
    private route: ActivatedRoute,
    private ngZone: NgZone
  ) {}

  ngOnInit(): void {
    this.registroForm = this.fb.group({
      tenant: this.fb.group({
        nombre_comercial: ['', Validators.required],
        subdominio:       ['', [Validators.required, Validators.pattern(/^[a-z0-9-]+$/)]],
        plan_id:          [null]
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
        const p_id = +params['plan_id'];
        this.registroForm.get('tenant.plan_id')?.setValue(p_id);
        // Asignamos un precio simulado según el ID del plan (para la demostración de PayPal)
        if (p_id === 1) this.montoPlan = '49.00';
        else if (p_id === 2) this.montoPlan = '99.00';
        else if (p_id === 3) this.montoPlan = '199.00';
      }
    });
  }


  continuarAlPago(): void {
    if (this.registroForm.invalid) {
      this.registroForm.markAllAsTouched();
      return;
    }
    this.mostrarPago = true;
    setTimeout(() => {
      this.inicializarPayPal();
    }, 100);
  }

  async inicializarPayPal() {
    try {
      const paypal = await loadScript({ 
          clientId: "AU_FgWBuXnOFtpiwWhbCqYePfn_zqxkNSfgNbnB1ztmHZMyP95CJo3b_s1KgRQ06WSXYYSEMTlqgAmKw",
          currency: "USD"
      });

      if (paypal && paypal.Buttons) {
          await paypal.Buttons({
              createOrder: (data: any, actions: any) => {
                  return actions.order.create({
                      purchase_units: [{ amount: { value: this.montoPlan } }]
                  });
              },
              onApprove: async (data: any, actions: any) => {
                  const details = await actions.order.capture();
                  console.log("Pago exitoso realizado por: ", details.payer.name.given_name);
                  this.ngZone.run(() => {
                      this.ejecutarRegistroEnBackend();
                  });
              },
              onError: (err: any) => {
                  console.error('PayPal Error:', err);
                  this.ngZone.run(() => {
                      this.mensajeError = "Ocurrió un error con PayPal. Intenta de nuevo.";
                  });
              }
          }).render("#paypal-button-container");
      }
    } catch (error) {
      console.error("Error cargando el script de PayPal", error);
      this.mensajeError = "Error al cargar el módulo de pagos.";
    }
  }

  ejecutarRegistroEnBackend(): void {
    this.enviando = true;
    this.mensajeError = null;

    const payload: TenantRegisterRequest = this.registroForm.value;
    this.emailRegistrado = payload.usuario.email;

    this.tenantService.registrarEmpresa(payload).subscribe({
      next: () => {
        this.enviando = false;
        this.mostrarPago = false;
        this.registroCompletado = true;
        this.mensajeExito = '¡Empresa registrada con éxito! Pago verificado.';
      },
      error: (err) => {
        this.enviando = false;
        this.mostrarPago = false;
        this.mensajeError = err.error?.detail || 'Error al registrar la empresa en nuestro sistema tras el pago.';
      }
    });
  }

  campoInvalido(ruta: string): boolean {
    const control = this.registroForm.get(ruta);
    return !!(control && control.invalid && control.touched);
  }
}

