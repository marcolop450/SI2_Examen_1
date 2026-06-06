export interface TecnicoOut {
  id_tecnico: number;
  taller_id: number;
  usuario_id: number;
  nombre: string;
  especialidad?: string;
  disponible_boolean: boolean;
}

export interface TecnicoCreate {
  taller_id: number;
  nombre: string;
  email: string;      // 👈 Importante para el Login
  password: string;   // 👈 Importante para el Login
  telefono?: string;
  especialidad?: string;
}

export interface TecnicoPartial {
  nombre?: string;
  especialidad?: string;
  disponible_boolean?: boolean;
}
