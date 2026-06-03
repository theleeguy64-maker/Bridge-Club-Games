// Service worker — network-first for the page, so updates appear on every refresh.
// Bumped automatically by the generator on every regen.
<<<<<<< HEAD
<<<<<<< HEAD
const VERSION = '20260603-210036';
=======
const VERSION = '20260603-210002';
>>>>>>> 059da91 (endorse: NYP marker for on-trial games; drop Fri Oakingham)
=======
const VERSION = '20260603-205410';
>>>>>>> fa504e3 (endorse: add 8 games incl. Oakingham (fills Wed gap))
const CACHE = `bcg-${VERSION}`;

self.addEventListener('install', e => {
  self.skipWaiting();
});

self.addEventListener('activate', e => {
  e.waitUntil(
    caches.keys()
      .then(keys => Promise.all(keys.filter(k => k !== CACHE).map(k => caches.delete(k))))
      .then(() => self.clients.claim())
      .then(() => self.clients.matchAll({ type: 'window' }))
      .then(clients => clients.forEach(c => c.postMessage({ type: 'SW_UPDATED', version: VERSION })))
  );
});

self.addEventListener('fetch', e => {
  // Network-first: try fresh, fall back to cache when offline.
  e.respondWith(
    fetch(e.request)
      .then(resp => {
        if (resp && resp.status === 200 && e.request.method === 'GET') {
          const clone = resp.clone();
          caches.open(CACHE).then(c => c.put(e.request, clone));
        }
        return resp;
      })
      .catch(() => caches.match(e.request))
  );
});
