/**
 * Refleja el Enum TipoRol de tus modelos de Python
 */
export enum TipoRol {
  cliente = 'cliente',
  taller = 'taller',
  admin = 'admin',
  tecnico = 'tecnico'
}

/**
 * Interfaz principal del Usuario (basado en UsuarioOut de FastAPI)
 */
export interface Usuario {
  id_usuario?: number;
  nombre: string;
  email: string;
  telefono: string;
  rol: TipoRol;
}

/**
 * Lo que Angular envía al backend para iniciar sesión
 */
export interface LoginRequest {
  email: string;
  password: string;
}

/**
 * Lo que el backend responde en /auth/login (TokenResponse)
 */
export interface TokenResponse {
  access_token: string;
  token_type: string;
  rol: TipoRol;
  nombre: string;
  id_usuario: number;     
  id_taller?: number;
}
