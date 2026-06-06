# Plataforma Inteligente de Emergencias Vehiculares

Bienvenido al repositorio del proyecto integrador de la materia Sistemas de Informacion 2 en la Universidad Autonoma Gabriel Rene Moreno (UAGRM - FICCT), Grupo 30, Segundo Parcial, Gestion 2026.

Este sistema conecta a conductores en situacion de emergencia vehicular con talleres mecanicos autorizados, mediante el analisis automatizado de incidentes usando datos multimodales como audio, imagenes y geolocalización. La plataforma integra inteligencia artificial para el diagnostico preliminar y la asignacion eficiente del servicio tecnico en tiempo real.

---

## Estructura del repositorio

```
SI2_Examen_1/
├── emergencias-backend/     # API REST desarrollada en FastAPI
└── emergencias-frontend/    # Aplicacion web desarrollada en Angular
```

La aplicacion movil (Flutter) se encuentra en un repositorio separado.

---

## Tecnologias utilizadas

### Backend (emergencias-backend)
- FastAPI — Framework principal para la API REST
- SQLAlchemy — ORM para la gestion de base de datos
- PostgreSQL (Supabase) — Base de datos relacional en la nube
- Passlib + Bcrypt — Encriptacion de contrasenas
- Python-Jose — Autenticacion con tokens JWT
- Groq API (Whisper Large V3 + Llama 3.2 Vision) — Procesamiento de audio e imagenes con IA
- APScheduler — Tareas programadas en segundo plano
- Uvicorn — Servidor ASGI para correr la aplicacion

### Frontend (emergencias-frontend)
- Angular 19 — Framework principal SPA
- TypeScript — Lenguaje de programacion
- Bootstrap 5 — Estilos y componentes visuales
- Angular CLI — Herramienta de construccion y desarrollo

---

## Requisitos previos

### Para el backend
- Python 3.11 o superior
- pip instalado
- Cuenta en Supabase con la base de datos configurada
- Credenciales de Groq API

### Para el frontend
- Node.js 18 o superior
- Angular CLI instalado globalmente
- Backend corriendo localmente o desplegado en Render

---

## Funcionalidades del sistema

- CU1 — Autenticacion con JWT para clientes, talleres y administrador
- CU2 — Gestion de clientes (CRUD)
- CU3 — Gestion de talleres (CRUD)
- CU4 — Gestion de perfil de usuario
- CU5 — Administracion de vehiculos
- CU6 — Administracion de staff tecnico
- CU7 — Registro de emergencia multimodal (audio, imagen, GPS)
- CU8 — Diagnostico y resumen inteligente con IA
- CU9 — Monitoreo de auxilio en tiempo real
- CU10 — Gestion de solicitudes y alertas
- CU11 — Asignacion de ordenes y tecnicos
- CU12 — Control de ejecucion y cierre de servicio
- CU13 — Gestion de pagos del servicio
- CU14 — Administracion de comisiones
- CU15 — Servicio de notificaciones y comunicacion

### Ciclo 4: SaaS, Resiliencia y Tiempo Real
- CU16 — Arquitectura Multi-Tenant de Red de Talleres
- CU17 — Canal de Comunicación en Tiempo Real (WebSocket)
- CU18 — Cotización y Selección de Taller por Servicio
- CU19 — Operación Offline y Sincronización (PWA)
- CU20 — Gestión de Excepciones Operativas

### Ciclo 5: Analítica Avanzada e IA Preventiva
- CU21 — Bitácora de Trazabilidad del Incidente
- CU22 — Panel de KPIs y Analítica Operacional
- CU23 — Calificación y Reputación Post-Servicio
- CU24 — Reportes Inteligentes por Voz y Texto con IA
- CU25 — Asistente IA de Seguridad Vial en Espera

---

## Equipo de desarrollo

| Nombre | Registro |
|---|---|
| Lopez Velazquez Marco Alejandro | 222008891 |
| Matienzo Flores Juan Manuel     | 222008970 |

Materia: Sistemas de Informacion 2
Docente: Ing. Angelica Garzon Cuellar
Grupo: 30 — Segundo Parcial, Semestre 1, 2026
