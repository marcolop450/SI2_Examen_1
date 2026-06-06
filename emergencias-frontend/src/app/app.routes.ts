import { Routes } from '@angular/router';
import { TecnicosComponent } from './paquete2-operaciones/cu6-staff-tecnico/tecnicos';
import { LoginComponent } from './paquete1-gestion/cu1-autenticacion/login/login.component';
import { Inicio } from './shared/inicio/inicio';
import { ClienteList } from './paquete1-gestion/cu2-gestion-clientes/cliente-list/cliente-list';
import { TallerList } from './paquete1-gestion/cu3-gestion-talleres/taller-list/taller-list';
import { EmergenciasComponent } from './paquete2-operaciones/cu10-emergencias/emergencias';
import { IngresosTallerComponent } from './paquete5-finanzas/ingresos-taller/ingresos-taller';
import { Cu9Monitoreo } from './paquete2-operaciones/cu9-monitoreo/cu9-monitoreo'; // 👈 IMPORTA
import { Cu14ComisionesComponent } from './paquete5-finanzas/cu14-comisiones/cu14-comisiones'; 
import { Cu4Perfil } from './paquete1-gestion/cu4-perfil/cu4-perfil';
import { HistorialTecnico } from './paquete2-operaciones/historial-tecnico/historial-tecnico';
import { UbicacionComponent } from './paquete2-operaciones/ubicacion/ubicacion';
import { Cu18Cotizaciones } from './paquete1-arquitectura/cu18-cotizaciones/cu18-cotizaciones';
// #Ciclo5 CU21 Bitácora en Paquete 2: Resiliencia Operativa
import { Cu21BitacoraComponent } from './paquete2-operaciones/cu21-bitacora/cu21-bitacora';
// #Ciclo5 CU22-CU25 en Paquete 3: Analítica Avanzada e IA Preventiva
import { Cu22KpisComponent } from './paquete3-analitica/cu22-kpis/cu22-kpis';
import { Cu23CalificacionesComponent } from './paquete3-analitica/cu23-calificaciones/cu23-calificaciones';
import { Cu24ReportesIaComponent } from './paquete3-analitica/cu24-reportes-ia/cu24-reportes-ia';
import { Cu25ConsejosVialesComponent } from './paquete3-analitica/cu25-consejos-viales/cu25-consejos-viales';

// --- IMPORTS CU16 MULTI-TENANT ---
import { LandingPlanesComponent } from './paquete6-multitenant/cu16-red-talleres/landing-planes/landing-planes';
import { RegistroB2bComponent } from './paquete6-multitenant/cu16-red-talleres/registro-b2b/registro-b2b';
import { AdminCockpitComponent } from './paquete6-multitenant/cu16-red-talleres/admin-cockpit/admin-cockpit';
import { DashboardOwnerComponent } from './paquete6-multitenant/cu16-red-talleres/dashboard-owner/dashboard-owner';

export const routes: Routes = [
  { path: 'login', component: LoginComponent },
  { path: 'inicio', component: Inicio },
  { path: 'clientes', component: ClienteList },
  { path: 'talleres', component: TallerList },
  { path: 'tecnicos', component: TecnicosComponent },
  { path: 'solicitudes', component: EmergenciasComponent },
  { path: 'monitoreo', component: Cu9Monitoreo },
  { path: 'mis-ingresos', component: IngresosTallerComponent },
  { path: 'historial-tecnico', component: HistorialTecnico },
  { path: 'perfil', component: Cu4Perfil },
  { path: 'comisiones', component: Cu14ComisionesComponent }, 
  { path: 'mi-ubicacion', component: UbicacionComponent },
  { path: 'cotizaciones', component: Cu18Cotizaciones },

  // --- RUTAS CU16 MULTI-TENANT ---
  { path: 'planes',          component: LandingPlanesComponent },
  { path: 'registro-b2b',    component: RegistroB2bComponent },
  { path: 'admin-cockpit',   component: AdminCockpitComponent },
  { path: 'dashboard-owner', component: DashboardOwnerComponent },

  // --- COMODINES (siempre al final) ---
  { path: '', component: LandingPlanesComponent, pathMatch: 'full' },
  // Rutas del Ciclo 5 - CU21 a CU25
  { path: 'bitacora/:id', component: Cu21BitacoraComponent },        // Bitácora de Trazabilidad - Ciclo 5 - CU21
  { path: 'kpis', component: Cu22KpisComponent },                    // Panel de KPIs - Ciclo 5 - CU22
  { path: 'calificaciones', component: Cu23CalificacionesComponent }, // Calificaciones - Ciclo 5 - CU23
  { path: 'reportes-ia', component: Cu24ReportesIaComponent },        // Reportes IA - Ciclo 5 - CU24
  { path: 'consejos-viales', component: Cu25ConsejosVialesComponent },// Consejos Viales - Ciclo 5 - CU25
  { path: '**', redirectTo: 'login' }
];