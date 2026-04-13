const CACHE_VERSION = 'v1';
const STATIC_CACHE = `waypoint-static-${CACHE_VERSION}`;
const DYNAMIC_CACHE = `waypoint-dynamic-${CACHE_VERSION}`;

// Pagina que se muestra cuando el usuario pide algo que no está en cache y no hay red
const OFFLINE_PAGE = '/offline/';

// Assets que se cachean en la instalacion del SW — siempre disponibles offline
const STATIC_ASSETS = [
    '/static/css/styles.css',
    '/static/img/favicon.ico',
    'https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css',
    'https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css',
    OFFLINE_PAGE,
];

// Se ejecuta una vez cuando el SW se instala por primera vez
self.addEventListener('install', event => {
    event.waitUntil(
        caches.open(STATIC_CACHE)
            .then(cache => cache.addAll(STATIC_ASSETS))
            .then(() => self.skipWaiting()) // Activa el nuevo SW inmediatamente
    );
});

// Limpia caches de versiones anteriores para no acumular basura
self.addEventListener('activate', event => {
    event.waitUntil(
        caches.keys().then(keys =>
            Promise.all(
                keys
                    .filter(key => key !== STATIC_CACHE && key !== DYNAMIC_CACHE)
                    .map(key => caches.delete(key))
            )
        ).then(() => self.clients.claim())
    );
});

self.addEventListener('fetch', event => {
    const { request } = event;
    const url = new URL(request.url);

    // Solo interceptamos peticiones GET — los POST (formularios) siempre van a la red
    if (request.method !== 'GET') return;

    // Ignoramos peticiones a otras APIs o dominios que no controlamos
    if (url.origin !== location.origin &&
        !url.href.includes('cdnjs.cloudflare.com') &&
        !url.href.includes('cdn.jsdelivr.net')) {
        return;
    }

    // Cache First para assets estaticos
    if (url.pathname.startsWith('/static/') ||
        url.href.includes('cdnjs.cloudflare.com') ||
        url.href.includes('cdn.jsdelivr.net')) {

        event.respondWith(
            caches.match(request).then(cached => {
                if (cached) return cached;

                // No este en cache — lo descargamos y guardamos para la proxima
                return fetch(request).then(response => {
                    const responseClone = response.clone();
                    caches.open(STATIC_CACHE)
                        .then(cache => cache.put(request, responseClone));
                    return response;
                });
            })
        );
        return;
    }

    // Network First para paginas de la app
    if (isAppPage(url.pathname)) {
        event.respondWith(
            fetch(request)
                .then(response => {
                    // Guardamos la respuesta fresca en la cache dinámica
                    const responseClone = response.clone();
                    caches.open(DYNAMIC_CACHE)
                        .then(cache => cache.put(request, responseClone));
                    return response;
                })
                .catch(() =>
                    caches.match(request).then(cached =>
                        cached || caches.match(OFFLINE_PAGE)
                    )
                )
        );
        return;
    }

    // Network Only para el resto con Red de Seguridad Global
    event.respondWith(
        fetch(request).catch(error => {
            // Si el fetch falla (no hay red) y el usuario intentaba navegar a una pagina HTML:
            if (request.mode === 'navigate') {
                return caches.match(OFFLINE_PAGE);
            }
            // Si era una peticion de una imagen o API fallida, simplemente la dejamos fallar
            throw error;
        })
    );
});

// Rutas de la app que queremos cachear para acceso offline
function isAppPage(pathname) {
    const cacheableRoutes = [
        '/characters/my_characters/',
        '/characters/view/',
        '/tables/my_tables/',
        '/tables/view/',
        '/tables/table/',
    ];
    return cacheableRoutes.some(route => pathname.startsWith(route));
}
