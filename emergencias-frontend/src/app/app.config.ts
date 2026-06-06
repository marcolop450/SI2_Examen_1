import { ApplicationConfig, ErrorHandler, Injectable, provideZoneChangeDetection } from '@angular/core';
import { provideRouter, withDebugTracing } from '@angular/router';
import { provideHttpClient, withInterceptors } from '@angular/common/http'; 

import { routes } from './app.routes';
import { authInterceptor } from './core/interceptors/auth.interceptor'; 

@Injectable()
export class GlobalErrorHandler implements ErrorHandler {
  handleError(error: any): void {
    const errorMsg = error.message ? error.message : error.toString();
    alert('ERROR FATAL EN ANGULAR:\n\n' + errorMsg + '\n\nPor favor, copia este error y envíaselo al asistente.');
    console.error('Error capturado globalmente:', error);
  }
}

export const appConfig: ApplicationConfig = {
  providers: [
    provideZoneChangeDetection({ eventCoalescing: true }),
    provideRouter(routes, withDebugTracing()),
    provideHttpClient(withInterceptors([authInterceptor])),
    { provide: ErrorHandler, useClass: GlobalErrorHandler }
  ]
};
