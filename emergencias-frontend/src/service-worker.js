// #Ciclo5 CU19 - Service Worker para PWA Offline - Ciclo 5 - CU19
// Permite guardar emergencias cuando no hay conexión y sincronizar al volver
// NOTA: Este archivo debe estar en src/ para que Angular lo copie a la raíz del build

const CACHE_NAME = 'emergencias-v1';
const OFFLINE_URL = '/offline.html';

// Assets que se cachean al instalar (app shell)
const STATIC_ASSETS = [
  '/',
  '/index.html',
  '/styles.css',
  OFFLINE_URL
];

// ── INSTALL: Cachear assets estáticos ─────────────────────────────
self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => {
      return cache.addAll(STATIC_ASSETS).catch(() => {
        // Si algún asset falla, continuar igual
        console.log('[SW] Algunos assets no se cachearon');
      });
    })
  );
  self.skipWaiting();
});

// ── ACTIVATE: Limpiar caches viejas ───────────────────────────────
self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((keys) =>
      Promise.all(
        keys.filter((k) => k !== CACHE_NAME).map((k) => caches.delete(k))
      )
    )
  );
  self.clients.claim();
});

// ── FETCH: Estrategia Network-first con fallback offline ───────────
self.addEventListener('fetch', (event) => {
  const { request } = event;
  const url = new URL(request.url);

  // Ignorar extensiones de Chrome y requests no-GET
  if (request.method !== 'GET') return;
  if (url.protocol === 'chrome-extension:') return;

  // API calls: Network-first, sin cache (datos siempre frescos)
  if (url.hostname === 'localhost' && url.port === '8000') return;
  if (url.hostname === '192.168.1.11' && url.port === '8000') return;

  // Assets estáticos: Cache-first
  event.respondWith(
    caches.match(request).then((cached) => {
      if (cached) return cached;

      return fetch(request)
        .then((response) => {
          // Cachear respuestas exitosas de assets
          if (response.ok && request.url.includes(self.location.origin)) {
            const clone = response.clone();
            caches.open(CACHE_NAME).then((cache) => cache.put(request, clone));
          }
          return response;
        })
        .catch(() => {
          // Sin conexión y sin cache → página offline
          if (request.headers.get('accept')?.includes('text/html')) {
            return caches.match(OFFLINE_URL);
          }
          return new Response('Sin conexión', { status: 503 });
        });
    })
  );
});

// ── SYNC: Sincronización en background al recuperar conexión ───────
self.addEventListener('sync', (event) => {
  if (event.tag === 'sync-emergencias') {
    event.waitUntil(sincronizarEmergenciasOffline());
  }
});

async function sincronizarEmergenciasOffline() {
  // Notificar a todos los clientes que hay sync en progreso
  const clients = await self.clients.matchAll();
  clients.forEach((client) =>
    client.postMessage({ tipo: 'sync_iniciada' })
  );
}
