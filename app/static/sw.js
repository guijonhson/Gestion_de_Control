const CACHE_VERSION = 'agrodev-v3';
const CACHE_NAME = 'agrodev-shell-' + CACHE_VERSION;

// Solo recursos estáticos y la página sin conexión. Nunca HTML autenticado.
const PRECACHE_URLS = [
    '/offline',
    '/static/vendor/bootstrap/css/bootstrap.min.css',
    '/static/vendor/bootstrap/js/bootstrap.bundle.min.js',
    '/static/vendor/bootstrap-icons/bootstrap-icons.css',
    '/static/vendor/bootstrap-icons/fonts/bootstrap-icons.woff2',
    '/static/css/responsive.css',
    '/static/img/logo.jpeg',
    '/static/img/icons/icon-192.png'
];

self.addEventListener('install', event => {
    event.waitUntil(
        caches.open(CACHE_NAME)
            .then(cache => cache.addAll(PRECACHE_URLS))
    );
});

self.addEventListener('activate', event => {
    event.waitUntil(
        caches.keys().then(nombres => Promise.all(
            nombres
                .filter(nombre => nombre !== CACHE_NAME)
                .map(nombre => caches.delete(nombre))
        )).then(() => self.clients.claim())
    );
});

self.addEventListener('message', event => {
    if (event.data && event.data.type === 'SKIP_WAITING') {
        self.skipWaiting();
    }
});

self.addEventListener('fetch', event => {
    const url = new URL(event.request.url);

    // Nunca interceptar otros orígenes ni métodos que no sean GET.
    if (url.origin !== self.location.origin || event.request.method !== 'GET') {
        return;
    }

    // Archivos estáticos: cache-first con actualización en segundo plano.
    if (url.pathname.startsWith('/static/')) {
        event.respondWith(staticoConActualizacion(event.request));
        return;
    }

    // Navegaciones HTML: red primero; nunca se guardan en caché.
    if (event.request.mode === 'navigate') {
        event.respondWith(redPrimero(event.request));
    }
});

async function staticoConActualizacion(request) {
    const cache = await caches.open(CACHE_NAME);
    // ignoreSearch permite reutilizar el precache aunque la página use ?v=.
    const guardado = await cache.match(request, { ignoreSearch: true });

    const red = fetch(request).then(response => {
        if (response && response.ok) {
            cache.put(request, response.clone());
        }
        return response;
    }).catch(() => null);

    return guardado || red || new Response('Recurso no disponible sin conexión.', {
        status: 503,
        headers: { 'Content-Type': 'text/plain; charset=utf-8' }
    });
}

async function redPrimero(request) {
    try {
        return await fetch(request);
    } catch (error) {
        const cache = await caches.open(CACHE_NAME);
        const offline = await cache.match('/offline');
        return offline || new Response('Sin conexión.', {
            status: 503,
            headers: { 'Content-Type': 'text/plain; charset=utf-8' }
        });
    }
}
