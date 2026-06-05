export interface PlanOut {
  id_plan: number;
  nombre: string;
  descripcion?: string;
  precio: number;
  limite_usuarios?: number;
  limite_talleres?: number;
  limite_incidentes?: number;
}

export interface TenantOut {
  id_tenant: string;
  nombre: string;
  subdominio: string;
  plan_id: number;
  fecha_registro: Date;
}

export interface SuscripcionOut {
  id_suscripcion: string;
  tenant_id: string;
  plan_id: number;
  fecha_inicio: Date;
  fecha_vencimiento: Date;
  estado: string;
}

export interface TenantRegisterTenant {
  nombre_comercial: string;
  subdominio: string;
  plan_id?: number;
}

export interface TenantRegisterTaller {
  nombre: string;
  direccion?: string;
  nit?: string;
  latitud_decimal?: number;
  longitud_decimal?: number;
}

export interface TenantRegisterUser {
  nombre: string;
  email: string;
  password?: string;
  telefono?: string;
}

export interface TenantRegisterRequest {
  tenant: TenantRegisterTenant;
  taller: TenantRegisterTaller;
  usuario: TenantRegisterUser;
}
