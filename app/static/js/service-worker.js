const CACHE_NAME = 'jantafile-cache-v1';
const urlsToCache = [
    '/',
    '/static/css/main.css',
    '/static/js/main.js',
    '/static/js/analytics.js',
    '/static/images/icon-192x192.png',
    '/static/images/icon-512x512.png',
    'https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap',
    'https://cdnjs.cloudflare.com/ajax/libs/socket.io/4.0.1/socket.io.min.js',
    'https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0-beta3/css/all.min.css'
];

// Install event: Cache essential resources
self.addEventListener('install', (event) => {
    event.waitUntil(
        caches.open(CACHE_NAME)
            .then((cache) => {
                console.log('Service Worker: Caching core assets');
                return cache.addAll(urlsToCache);
            })
            .catch(error => {
                console.error('Service Worker: Caching failed', error);
            })
    );
});

// Activate event: Clean up old caches
self.addEventListener('activate', (event) => {
    event.waitUntil(
        caches.keys().then((cacheNames) => {
            return Promise.all(
                cacheNames.map((cacheName) => {
                    if (cacheName !== CACHE_NAME) {
                        console.log('Service Worker: Removing old cache', cacheName);
                        return caches.delete(cacheName);
                    }
                })
            );
        })
    );
});

// Fetch event: Cache-first strategy
self.addEventListener('fetch', (event) => {
    if (event.request.url.startsWith('http')) {
        event.respondWith(
            caches.match(event.request)
                .then((response) => {
                    if (response) {
                        return response;
                    }
                    
                    return fetch(event.request).then((networkResponse) => {
                        if (networkResponse && 
                            networkResponse.status === 200 && 
                            networkResponse.type === 'basic') {
                            const responseToCache = networkResponse.clone();
                            caches.open(CACHE_NAME)
                                .then(cache => cache.put(event.request, responseToCache));
                        }
                        return networkResponse;
                    });
                })
                .catch(() => {
                    console.log('Service Worker: Network request failed');
                })
        );
    }
});

// Background sync (if needed in future)
// self.addEventListener('backgroundfetchsuccess', event => {
//     console.log('[Service Worker] Background fetch success', event);
// });

// Notification click handler (if needed in future)
// self.addEventListener('notificationclick', event => {
//     console.log('[Service Worker] Notification click', event);
// });

// Replace the commented out notification code with:
self.addEventListener('push', (event) => {
    const payload = event.data.json();
    const options = {
        body: payload.body,
        icon: payload.icon,
        data: { url: payload.url },
        vibrate: [200, 100, 200],
        actions: [
            { 
                action: 'view', 
                title: 'View Episode',
                icon: '/static/images/icon-episodes.png'
            }
        ]
    };

    event.waitUntil(
        self.registration.showNotification(payload.title, options)
    );
});

self.addEventListener('notificationclick', (event) => {
    event.notification.close();
    if(event.action === 'view') {
        clients.openWindow(event.notification.data.url);
    } else {
        clients.openWindow('/');
    }
});