/** App shell, router and global interactions. */
import { icon } from "./icons.js";
import { loadContent, state, mediaUrl } from "./api.js";
import { request } from "./store.js";
import { toast, esc, attr } from "./ui.js";
import {
  homeView,
  shopView,
  productView,
  collectionView,
  archiveView,
  requestView,
  infoView,
  notFoundView,
} from "./views.js";

const app = document.getElementById("app");
const NAV_ITEMS = [
  { key: "home", href: "#/", label: "Home" },
  { key: "shop", href: "#/shop", label: "Shop" },
  { key: "info", href: "#/info", label: "The Embassy" },
];

/* --------------------------------------------------------------- shell */

function shellHTML() {
  return `<a class="skip-link" href="#view">Skip to content</a>
  <header class="nav" data-nav data-theme="light">
    <div class="nav__inner">
      <a class="brand" href="#/" aria-label="Cocktail Embassy — home">
        <img src="assets/brand/mark-dark.png" alt="Cocktail Embassy">
      </a>
      <nav class="nav__links" aria-label="Primary">
        ${NAV_ITEMS.map(
          (item) => `<a class="nav__link" href="${item.href}" data-navlink="${item.key}">${item.label}</a>`
        ).join("")}
        <a class="nav__link" href="#/request" data-navlink="request">Request</a>
      </nav>
      <a class="iconbtn" href="#/request" aria-label="Open request" data-cartbtn>
        ${icon("bag")}
        <span class="cart-count" data-cart-count hidden>0</span>
      </a>
    </div>
  </header>

  <div class="scrollline" data-scrollline aria-hidden="true"></div>

  <main id="view" tabindex="-1"></main>

  <footer class="footer" data-footer></footer>

  <a class="rail" href="#/request" data-rail aria-label="Open your request">
    <span><span class="rail__count" data-rail-count>0</span> in your request</span>
    <span class="btn">Review <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M4 12h15"/><path d="m13.4 6.4 5.6 5.6-5.6 5.6"/></svg></span>
  </a>

  <nav class="tabbar" aria-label="Primary">
    <a class="tab" href="#/" data-tab="home">${icon("home")}<span>Home</span></a>
    <a class="tab" href="#/shop" data-tab="shop">${icon("shop")}<span>Shop</span></a>
    <a class="tab" href="#/request" data-tab="request">${icon("bag")}<span>Request</span><span class="tab__badge" data-tab-badge hidden>0</span></a>
    <a class="tab" href="#/info" data-tab="info">${icon("info")}<span>Info</span></a>
  </nav>`;
}

function footerHTML(data) {
  const s = data.settings || {};
  const c = s.contacts || {};
  return `<div class="footer__inner">
    <div class="footer__brand">
      <img src="assets/brand/mark-chrome.png" alt="${attr(s.brand || "Cocktail Embassy")}">
      <p>${esc(s.about || "")}</p>
    </div>
    <div class="footer__col">
      <h4>Catalogue</h4>
      ${data.categories.map((cat) => `<a href="#/shop?c=${attr(cat.slug)}">${esc(cat.name)}</a>`).join("")}
      <a href="#/shop">All pieces</a>
      <a href="#/archive">Archive</a>
    </div>
    <div class="footer__col">
      <h4>Contact</h4>
      ${c.email ? `<a href="mailto:${attr(c.email)}">${esc(c.email)}</a>` : ""}
      ${c.phone ? `<a href="tel:${attr(c.phone.replace(/\s/g, ""))}">${esc(c.phone)}</a>` : ""}
      ${c.telegram ? `<a href="${attr(c.telegram)}" target="_blank" rel="noopener">Telegram</a>` : ""}
      ${c.instagram ? `<a href="${attr(c.instagram)}" target="_blank" rel="noopener">Instagram</a>` : ""}
      <span>${esc(c.address || "")}</span>
    </div>
  </div>
  <div class="footer__base">
    <span>© ${new Date().getFullYear()} ${esc(s.brand || "Cocktail Embassy")}. All rights reserved.</span>
    <span>${esc(s.priceNote || "")}</span>
  </div>`;
}

/* ------------------------------------------------------------- router */

function parseHash() {
  const raw = (location.hash || "#/").replace(/^#/, "");
  const [pathPart, queryPart] = raw.split("?");
  const segments = pathPart.split("/").filter(Boolean);
  const params = {};
  new URLSearchParams(queryPart || "").forEach((value, key) => {
    params[key] = value;
  });
  return { segments, params, path: "/" + segments.join("/") };
}

const routeDefs = [
  { test: (s) => s.length === 0, view: (data) => homeView(data), tab: "home", nav: "home" },
  { test: (s) => s[0] === "shop", view: (data, p, params) => shopView(data, params), tab: "shop", nav: "shop" },
  {
    test: (s) => s[0] === "product" && s[1],
    view: (data, p, params, s) => productView(data, s[1]),
    tab: "shop",
    nav: "shop",
  },
  {
    test: (s) => s[0] === "collection" && s[1],
    view: (data, p, params, s) => collectionView(data, s[1]),
    tab: "shop",
    nav: "shop",
  },
  {
    test: (s) => s[0] === "archive",
    view: (data, p, params, s) => archiveView(data, s[1]),
    tab: "shop",
    nav: "shop",
  },
  { test: (s) => s[0] === "request", view: (data) => requestView(data), tab: "request", nav: "request" },
  { test: (s) => s[0] === "info", view: (data) => infoView(data), tab: "info", nav: "info" },
];

let currentRoute = null;
let currentView = { theme: "light" };

async function render() {
  const data = state.content;
  if (!data) return;

  const { segments, params } = parseHash();
  const def = routeDefs.find((r) => r.test(segments));
  let view = def ? def.view(data, params, params, segments) : null;
  if (!view) view = notFoundView(data);

  currentRoute = def || null;
  currentView = view;

  document.title = view.title || data.settings?.brand || "Cocktail Embassy";

  const main = document.getElementById("view");
  main.innerHTML = `<div class="page">${view.html}</div>`;

  if (typeof view.mount === "function") {
    try {
      view.mount(main, { data });
    } catch (err) {
      console.error("[CE] view mount failed", err);
    }
  }

  updateActiveNav(def);
  updateNavTheme(true);
  motionEngine();

  // Scroll: top for a new destination, restore for in-page updates.
  if (!location.hash.includes("?")) window.scrollTo({ top: 0, behavior: "instant" in document.documentElement.style ? "instant" : "auto" });
  document.getElementById("view")?.focus({ preventScroll: true });
}

function updateActiveNav(def) {
  const tab = def ? def.tab : "";
  document.querySelectorAll("[data-tab]").forEach((el) => {
    if (el.dataset.tab === tab) el.setAttribute("aria-current", "page");
    else el.removeAttribute("aria-current");
  });
  document.querySelectorAll("[data-navlink]").forEach((el) => {
    if (def && el.dataset.navlink === def.nav) el.setAttribute("aria-current", "page");
    else el.removeAttribute("aria-current");
  });
}

/* --------------------------------------------------------- nav styling */

function updateNavTheme(force = false) {
  const nav = document.querySelector("[data-nav]");
  if (!nav) return;
  const y = window.scrollY;
  const wantsDark = currentView.theme === "dark-top" || currentRoute?.tab === "home";
  let threshold = 260;
  if (currentRoute?.tab === "home") {
    const hero = document.querySelector("[data-hero]");
    threshold = hero ? Math.max(160, hero.offsetHeight - 96) : 340;
  }
  const solid = y > 12;
  nav.classList.toggle("is-solid", solid);
  // the whole site is one dark room: the bar only gets denser as you scroll
  nav.dataset.theme = "dark";
}

/* --------------------------------------------------------------- motion */

let revealObserver = null;

function motionEngine() {
  const line = document.querySelector("[data-scrollline]");
  const rail = document.querySelector("[data-rail]");
  const reduced = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  let ticking = false;
  const onScroll = () => {
    if (ticking) return;
    ticking = true;
    requestAnimationFrame(() => {
      ticking = false;
      const doc = document.documentElement;
      const max = Math.max(1, doc.scrollHeight - window.innerHeight);
      const p = Math.min(1, Math.max(0, window.scrollY / max));
      if (line) line.style.setProperty("--progress", p.toFixed(4));
      if (rail) rail.classList.toggle("is-in", window.scrollY > window.innerHeight * 0.7 && request.count() > 0);
    });
  };
  window.addEventListener("scroll", onScroll, { passive: true });
  window.addEventListener("resize", onScroll, { passive: true });

  // reveal sections as they come into view
  if (revealObserver) revealObserver.disconnect();
  if ("IntersectionObserver" in window && !reduced) {
    revealObserver = new IntersectionObserver(
      (entries) => {
        entries.forEach((e) => {
          if (e.isIntersecting) {
            e.target.classList.add("is-in");
            revealObserver.unobserve(e.target);
          }
        });
      },
      { rootMargin: "0px 0px -8% 0px", threshold: 0.08 }
    );
    document.querySelectorAll(".reveal:not(.is-in)").forEach((el, i) => {
      el.style.setProperty("--reveal-delay", `${Math.min(i, 6) * 60}ms`);
      revealObserver.observe(el);
    });
  } else {
    document.querySelectorAll(".reveal").forEach((el) => el.classList.add("is-in"));
  }

  // a light that follows the pointer across the glass panels
  if (!reduced) {
    document.querySelectorAll(".spotlight").forEach((el) => {
      el.addEventListener(
        "pointermove",
        (ev) => {
          const r = el.getBoundingClientRect();
          el.style.setProperty("--mx", `${ev.clientX - r.left}px`);
          el.style.setProperty("--my", `${ev.clientY - r.top}px`);
        },
        { passive: true }
      );
    });
  }
  onScroll();
}

/* -------------------------------------------------------------- badges */

function updateBadges() {
  const count = request.count();
  const railCount = document.querySelector("[data-rail-count]");
  if (railCount) railCount.textContent = String(count);
  const rail = document.querySelector("[data-rail]");
  if (rail && count === 0) rail.classList.remove("is-in");
  document.querySelectorAll("[data-cart-count], [data-tab-badge]").forEach((el) => {
    el.textContent = String(count);
    el.hidden = count === 0;
  });
}

/* ------------------------------------------------------- global events */

document.addEventListener("click", (e) => {
  const add = e.target.closest("[data-add]");
  if (add) {
    const slug = add.dataset.add;
    const qty = Math.max(1, Number(add.dataset.addQty || 1));
    const product = state.content?.products.find((p) => p.slug === slug);
    request.add(slug, qty);
    if (product) {
      toast(`${product.name} · ${qty > 1 ? `${qty} pcs · ` : ""}added to request`);
      const btn = add;
      btn.classList.add("is-added");
      setTimeout(() => btn.classList.remove("is-added"), 900);
    }
    return;
  }
});

request.subscribe(updateBadges);

window.addEventListener("scroll", () => updateNavTheme(), { passive: true });
window.addEventListener("resize", () => updateNavTheme(), { passive: true });
window.addEventListener("hashchange", render);

/* ---------------------------------------------------------------- boot */

async function boot() {
  app.innerHTML = shellHTML();
  updateBadges();

  let data;
  try {
    data = await loadContent();
  } catch (err) {
    document.getElementById("view").innerHTML = `<div class="wrap"><section class="section empty" style="min-height:60dvh;align-content:center">
      ${icon("warning")}
      <h1 class="h2" style="color:var(--ink)">Catalogue temporarily unavailable</h1>
      <p>Please refresh in a moment.</p>
      <button class="btn" onclick="location.reload()">Retry</button>
    </section></div>`;
    return;
  }

  window.__CE_DATA__ = data;
  document.querySelector("[data-footer]").innerHTML = footerHTML(data);

  // Preload key editorial imagery after first paint.
  requestAnimationFrame(() => {
    ["assets/editorial/red-vessel.webp", "assets/editorial/crystal-light.webp"].forEach((src) => {
      const img = new Image();
      img.src = src;
    });
  });

  await render();
  document.body.classList.add("is-ready");

  if ("serviceWorker" in navigator && location.protocol.startsWith("http")) {
    navigator.serviceWorker.register("sw.js").catch(() => {});
  }
}

boot();
