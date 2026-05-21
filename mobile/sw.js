self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open('raptorcare-mobile-cache-v1').then((cache) => {
      return cache.addAll([
        '/mobile/index.html',
        '/mobile/app.js',
        '/mobile/manifest.json',
      ])
    })
  )
})

self.addEventListener('fetch', (event) => {
  event.respondWith(
    caches.match(event.request).then((cached) => {
      return cached || fetch(event.request)
    })
  )
})
