export interface Taller {
  id_taller?: number;
  dueño_id?: number;
  
  // Datos del dueño
  nombre_dueno: string;
  email_dueno?: string; // Es opcional en la tabla pero viene del backend
  email?: string; // Lo usamos para el formulario de creación
  password?: string; // Lo usamos para el formulario de creación
  telefono_dueno?: string;
  telefono?: string; // Lo usamos para el formulario

  // Datos del taller
  nombre_taller: string;
  direccion?: string;
  nit?: string;
  latitud_decimal?: number;
  longitud_decimal?: number;
}
