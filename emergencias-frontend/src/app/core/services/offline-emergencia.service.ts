// #Ciclo5 CU19 - Servicio de Emergencias Offline para PWA Web
// Guarda emergencias en localStorage cuando no hay conexión
// y las sincroniza automáticamente al recuperar internet
import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { BehaviorSubject, fromEvent, merge, map } from 'rxjs';

@Injectable({ providedIn: 'root' })
export class OfflineEmergenciaService {
  // #Ciclo5 CU19 - Estado de conexión reactivo
  private _online$ = new BehaviorSubject<boolean>(navigator.onLine);
  online$ = this._online$.asObservable();

  // #Ciclo5 CU19 - Contador de pendientes
  private _pendientes$ = new BehaviorSubject<number>(this.contarPendientes());
  pendientes$ = this._pendientes$.asObservable();

  private STORAGE_KEY = 'emergencias_offline_queue';
  private API_URL = 'https://backend-ixkv.onrender.com';
  private sincronizando = false;

  constructor(private http: HttpClient) {
    // #Ciclo5 CU19 - Escuchar eventos de conectividad del navegador
    merge(
      fromEvent(window, 'online').pipe(map(() => true)),
      fromEvent(window, 'offline').pipe(map(() => false))
    ).subscribe((online) => {
      this._online$.next(online);
      if (online) {
        this.sincronizarTodas();
      }
    });
  }

  // #Ciclo5 CU19 - ¿Hay conexión a internet?
  get isOnline(): boolean {
    return navigator.onLine;
  }

  // #Ciclo5 CU19 - Guardar emergencia en cola offline
  guardarOffline(emergencia: any): string {
    const uuid = this.generarUUID();
    const cola = this.obtenerCola();
    cola.push({
      ...emergencia,
      uuid_offline: uuid,
      timestamp_offline: new Date().toISOString()
    });
    localStorage.setItem(this.STORAGE_KEY, JSON.stringify(cola));
    this._pendientes$.next(cola.length);
    return uuid;
  }

  // #Ciclo5 CU19 - Obtener cola de pendientes
  obtenerCola(): any[] {
    try {
      return JSON.parse(localStorage.getItem(this.STORAGE_KEY) || '[]');
    } catch {
      return [];
    }
  }

  // #Ciclo5 CU19 - Contar pendientes
  contarPendientes(): number {
    return this.obtenerCola().length;
  }

  // #Ciclo5 CU19 - Eliminar de la cola
  eliminarDeCola(uuid: string): void {
    const cola = this.obtenerCola().filter(e => e.uuid_offline !== uuid);
    localStorage.setItem(this.STORAGE_KEY, JSON.stringify(cola));
    this._pendientes$.next(cola.length);
  }

  // #Ciclo5 CU19 - Sincronizar todas las emergencias pendientes
  async sincronizarTodas(): Promise<{ exitosas: number; fallidas: number }> {
    if (this.sincronizando || !navigator.onLine) {
      return { exitosas: 0, fallidas: 0 };
    }

    this.sincronizando = true;
    const cola = this.obtenerCola();
    let exitosas = 0;
    let fallidas = 0;

    for (const emergencia of cola) {
      try {
        const token = localStorage.getItem('auth_token') || '';
        const response = await fetch(`${this.API_URL}/incidentes/`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`
          },
          body: JSON.stringify({
            vehiculo_id: emergencia.vehiculo_id,
            latitud_emergencia: emergencia.latitud_emergencia,
            longitud_emergencia: emergencia.longitud_emergencia,
            descripcion_texto: emergencia.descripcion_texto,
            evidencias: emergencia.evidencias || [],
            uuid_offline: emergencia.uuid_offline
          })
        });

        if (response.ok || response.status === 409) {
          // 200/201 = creado, 409 = ya existe (dedup OK)
          this.eliminarDeCola(emergencia.uuid_offline);
          exitosas++;
        } else if (response.status === 400 || response.status === 422) {
          // Error de validación: no reintentar
          this.eliminarDeCola(emergencia.uuid_offline);
          fallidas++;
        } else {
          // Error del servidor: dejar en cola para reintentar
          fallidas++;
        }
      } catch {
        // Sin red: dejar en cola
        fallidas++;
      }
    }

    this.sincronizando = false;
    this._pendientes$.next(this.contarPendientes());
    return { exitosas, fallidas };
  }

  // #Ciclo5 CU19 - UUID v4 generator
  private generarUUID(): string {
    return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, (c) => {
      const r = (Math.random() * 16) | 0;
      return (c === 'x' ? r : (r & 0x3) | 0x8).toString(16);
    });
  }

  // #Ciclo5 CU19 - Registrar Service Worker
  static registrarSW(): void {
    if ('serviceWorker' in navigator) {
      window.addEventListener('load', () => {
        navigator.serviceWorker
          .register('/service-worker.js')
          .then((reg) => console.log('[PWA] Service Worker registrado:', reg.scope))
          .catch((err) => console.warn('[PWA] SW no registrado:', err));
      });
    }
  }
}
