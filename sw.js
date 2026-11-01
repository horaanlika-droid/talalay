/* Cocktail Embassy — offline shell.
   Code & catalogue JSON use network-first so deploys appear immediately;
   heavy static photography uses cache-first with background refresh. */
const CACHE = "ce-shell-v16";
const SHELL = [
  "./",
  "index.html",
  "css/app.css?v=16",
  "js/app.js?v=16",
  "js/config.js?v=16",
  "js/api.js",
  "js/admin.js",
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
    caches
      .open(CACHE)
      .then((cache) => cache.addAll(SHELL).catch(() => {}))
      .then(() => self.skipWaiting())
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
  if (url.pathname.includes("/api/") || url.pathname.includes("/media/")) return;
  if (url.origin !== location.origin) return;

  const isCodeOrData =
    request.mode === "navigate" ||
    /\.(html|css|js|mjs|json|webmanifest)$/i.test(url.pathname) ||
    url.pathname.endsWith("/");

  if (isCodeOrData) {
    // Network-first so CSS/JS/JSON updates land on the first reload.
    event.respondWith(
      fetch(request, { cache: "no-cache" })
        .then((response) => {
          if (response && response.ok) {
            const copy = response.clone();
            caches.open(CACHE).then((cache) => cache.put(request, copy));
          }
          return response;
        })
        .catch(() => caches.match(request))
    );
    return;
  }

  // Static images/assets: cache-first, refresh in the background.
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
});
