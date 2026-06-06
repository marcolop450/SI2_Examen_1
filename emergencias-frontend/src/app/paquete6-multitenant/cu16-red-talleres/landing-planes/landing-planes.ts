import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterModule, Router } from '@angular/router';
import { TenantService } from '../../../core/services/tenant.service';
import { PlanOut } from '../saas.interface';

@Component({
  selector: 'app-landing-planes',
  standalone: true,
  imports: [CommonModule, RouterModule],
  templateUrl: './landing-planes.html',
  styleUrls: ['./landing-planes.css']
})
export class LandingPlanesComponent implements OnInit {
  planes: PlanOut[] = [];
  cargando = true;
  error: string | null = null;
  isLoggedIn = false;

  constructor(
    private tenantService: TenantService,
    private router: Router
  ) {}

  ngOnInit(): void {
    this.isLoggedIn = !!(localStorage.getItem('token') || localStorage.getItem('auth_token'));
    this.tenantService.obtenerPlanes().subscribe({
      next: (data) => {
        this.planes = data;
        this.cargando = false;
      },
      error: () => {
        this.error = 'No se pudieron cargar los planes disponibles.';
        this.cargando = false;
      }
    });
  }

  seleccionarPlan(plan: PlanOut): void {
    this.router.navigate(['/registro-b2b'], {
      queryParams: { plan_id: plan.id_plan }
    });
  }

  scrollAPlanes(): void {
    const el = document.getElementById('planes-section');
    if (el) {
      el.scrollIntoView({ behavior: 'smooth' });
    }
  }
}
