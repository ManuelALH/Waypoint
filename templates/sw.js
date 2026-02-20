// sw.js - Service Worker Básico
const CACHE_NAME = 'waypoint-v1';

// Evento de instalación
self.addEventListener('install', (event) => {
    console.log('[Service Worker] Instalando...');
    // Lógica futura para guardar archivos offline iría aquí
    self.skipWaiting();
});

// Evento de activación
self.addEventListener('activate', (event) => {
    console.log('[Service Worker] Activado y listo para controlar la app.');
    event.waitUntil(clients.claim());
});

// Evento Fetch (Intercepción de red)
self.addEventListener('fetch', (event) => {
    // Por ahora, simplemente dejamos que la petición vaya a internet normalmente
    event.respondWith(fetch(event.request));
});