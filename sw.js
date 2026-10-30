/* Cocktail Embassy — offline shell (stale-while-revalidate). */
const CACHE = "ce-shell-v6";
const SHELL = [
  "./",
  "index.html",
  "css/app.css",
  "js/app.js",
  "js/config.js",
  "js/api.js",
  "js/store.js",
  "js/ui.js",
  "js/views.js",
  "js/icons.js",
  "data/content.json",
  "manifest.webmanifest",
  "assets/brand/mark-dark.png",
  "assets/brand/ce-logo-chrome.png",
  "assets/brand/mark-chrome.png",
  "assets/brand/favicon.png",
  "assets/products/martini.webp",
  "assets/scenes/hero-levitating-martini.webp",
  "assets/scenes/hero-levitating-martini-portrait.webp",
];

self.addEventListener("install", (event) => {
  event.waitUntil(
    caches.open(CACHE).then((cache) => cache.addAll(SHELL)).then(() => self.skipWaiting())
  );
});

self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches
      .keys()
      .then((keys) => Promise.all(keys.filter((k) => k !== CACHE).map((k) => caches.delete(k))))
      .then(() => self.clients.claim())
  );
});

self.addEventListener("fetch", (event) => {
  const { request } = event;
  if (request.method !== "GET") return;
  const url = new URL(request.url);

  // Never cache the API.
  if (url.pathname.includes("/api/")) return;

  // Same-origin assets: cache-first, refresh in the background.
  if (url.origin === location.origin) {
    event.respondWith(
      caches.match(request).then((cached) => {
        const network = fetch(request)
          .then((response) => {
            if (response && response.ok) {
              const copy = response.clone();
              caches.open(CACHE).then((cache) => cache.put(request, copy));
            }
            return response;
          })
          .catch(() => cached);
        return cached || network;
      })
    );
  }
});
