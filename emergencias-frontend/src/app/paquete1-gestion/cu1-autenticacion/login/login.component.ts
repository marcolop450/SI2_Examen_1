// ============================================================
// login.component.ts
// CONTEXTO: CU1 (Login) y CU3 (Registro de Taller)
// ============================================================
import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ReactiveFormsModule, FormBuilder, FormGroup, Validators } from '@angular/forms';
import { Router, RouterModule } from '@angular/router';
import { AuthService } from '../../../core/services/auth.service';
import { TallerService } from '../../../core/services/taller';

@Component({
  selector: 'app-login',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule, RouterModule],
  templateUrl: './login.component.html',
  styleUrls: ['./login.component.css']
})
export class LoginComponent {
  loginForm!: FormGroup;
  isLoginMode = true;

  constructor(
    private fb: FormBuilder, 
    private authService: AuthService,
    private tallerService: TallerService,
    private router: Router
  ) {
    this.iniciarFormulario();
  }

  iniciarFormulario() {
    if (this.isLoginMode) {
      this.loginForm = this.fb.group({
        email: ['', [Validators.required, Validators.email]],
        password: ['', [Validators.required, Validators.minLength(6)]]
      });
    } else {
      this.loginForm = this.fb.group({
        nombre_dueno: ['', Validators.required],
        email: ['', [Validators.required, Validators.email]],
        password: ['', [Validators.required, Validators.minLength(6)]],
        telefono: [''],
        nombre_taller: ['', Validators.required],
        direccion: [''],
        nit: ['']
      });
    }
  }

  toggleMode() {
    this.isLoginMode = !this.isLoginMode;
    this.iniciarFormulario();
  }

  onSubmit() {
    if (this.loginForm.invalid) return;

    if (this.isLoginMode) {
      this.authService.login(this.loginForm.value).subscribe({
        next: (res: any) => {
          localStorage.setItem('token', res.access_token || res.token);
          localStorage.setItem('rol', res.rol);
          localStorage.setItem('idTaller', res.id_taller || res.id_usuario); 
          
          this.router.navigate(['/inicio']);
        },
        error: (err) => alert('Correo o contraseña incorrectos')
      });
    } else {
      if (navigator.geolocation) {
        navigator.geolocation.getCurrentPosition((position) => {
          const datosConUbicacion = {
            ...this.loginForm.value,
            latitud_decimal: position.coords.latitude,
            longitud_decimal: position.coords.longitude
          };

          this.tallerService.crearTaller(datosConUbicacion).subscribe({
            next: (res) => {
              alert('¡Taller registrado exitosamente! Ahora puedes iniciar sesión.');
              this.toggleMode(); 
            },
            error: (err) => alert('Error al registrar: ' + (err.error?.detail || 'Verifique sus datos'))
          });
        }, (error) => {
           alert("Por favor, permite la ubicación para registrar tu taller.");
        });
      } else {
        alert("Geolocalización no soportada en este navegador.");
      }
    }
  }

  irAPlanes() {
    this.router.navigate(['/']).then(success => {
      if (!success) {
        alert('El enrutador falló silenciosamente al intentar ir a /.');
      }
    }).catch(err => {
      alert('Error en el enrutador:\n' + err);
    });
  }
}