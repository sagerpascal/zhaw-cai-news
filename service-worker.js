


self.addEventListener('install', function(event) {
  event.waitUntil(
    caches.open('v1').then(function(cache) {
      return cache.addAll([
        'images/touch/homescreen48.png',
        'images/touch/homescreen72.png',
        'images/touch/homescreen96.png',
        'images/touch/homescreen144.png',
        'images/touch/homescreen168.png',
        'images/touch/homescreen192.png',
        'manifest.json',
        'service-worker.js',
      ]);
    })
  );
});

self.addEventListener('fetch', function(event) {
    event.respondWith(
        caches.match(event.request).then(function(response) {
        return response || fetch(event.request);
        })
    );
});