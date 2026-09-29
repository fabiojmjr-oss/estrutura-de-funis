// Offline channel: cache the page and its data, serve from cache only when the network fails.
//
// Network first for everything. An earlier version served the shell cache-first under a fixed
// cache name, which meant a returning visitor kept the old JavaScript after every redeploy while
// the data (network-first) moved on: two versions of the app mixed in one tab. The deploy
// workflow now also stamps VERSION with the commit, so each release gets a fresh cache.

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
  event.respondWith(
    fetch(request)
      .then((response) => {
        if (response.ok) {
          const copy = response.clone();
          caches.open(VERSION).then((cache) => cache.put(request, copy));
        }
        return response;
      })
      .catch(() => caches.match(request, { ignoreSearch: true })),
  );
});
