// Offline channel: cache the shell and the data on first visit, serve from cache when offline.
// Network first for data, so a redeploy with new figures is picked up whenever there is a
// connection; cache first for the static shell.

const VERSION = 'funis-v1';
const SHELL = [
  './',
  'index.html',
  'css/styles.css',
  'manifest.webmanifest',
  'icons/icon.svg',
  'js/app.js',
  'js/ui/format.js',
  'js/ui/charts.js',
  'js/ui/state.js',
  'js/ui/dom.js',
  'js/engine/stats.js',
  'js/engine/funnel.js',
  'js/engine/attribution.js',
  'js/engine/sales.js',
  'js/engine/gates.js',
  'js/views/overview.js',
  'js/views/builder.js',
  'js/views/multichannel.js',
  'js/views/sales.js',
  'js/views/supply.js',
  'js/views/management.js',
  'js/views/ideation.js',
  'data/marketing.json',
  'data/sales.json',
  'data/supply.json',
  'data/management.json',
  'data/ideation.json',
];

self.addEventListener('install', (event) => {
  event.waitUntil(caches.open(VERSION).then((cache) => cache.addAll(SHELL)).then(() => self.skipWaiting()));
});

self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys()
      .then((keys) => Promise.all(keys.filter((k) => k !== VERSION).map((k) => caches.delete(k))))
      .then(() => self.clients.claim()),
  );
});

self.addEventListener('fetch', (event) => {
  const { request } = event;
  if (request.method !== 'GET' || new URL(request.url).origin !== self.location.origin) return;
  const isData = request.url.includes('/data/');
  if (isData) {
    event.respondWith(
      fetch(request)
        .then((response) => {
          const copy = response.clone();
          caches.open(VERSION).then((cache) => cache.put(request, copy));
          return response;
        })
        .catch(() => caches.match(request)),
    );
    return;
  }
  event.respondWith(caches.match(request, { ignoreSearch: true }).then((hit) => hit ?? fetch(request)));
});
