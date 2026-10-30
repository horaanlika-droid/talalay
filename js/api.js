/**
 * Data layer.
 * Priority: live API (BotHost) → local cache → bundled data/content.json.
 * The bundled file guarantees GitHub Pages always renders a complete catalogue.
 */
import { icon } from "./icons.js";

const CONFIG = window.CE_CONFIG || {};
const API_BASE = (CONFIG.apiBase || "").replace(/\/+$/, "");
const CONTENT_KEY = "ce.content.v1";
const CACHE_MAX_AGE = 1000 * 60 * 60 * 24 * 3; // 3 days

let contentPromise = null;
let source = API_BASE ? "api" : "static";

export const state = {
  content: null,
  loading: true,
  online: false,
};

export function apiBase() {
  return API_BASE;
}

export function isStatic() {
  return !API_BASE;
}

/** Turn a stored media path into a usable URL, wherever it came from. */
export function mediaUrl(path) {
  if (!path) return "";
  if (/^(https?:)?\/\//.test(path) || path.startsWith("data:")) return path;
  if (path.startsWith("/")) {
    // Uploaded media lives on the API host.
    return API_BASE ? API_BASE + path : path;
  }
  return path;
}

function readCache() {
  try {
    const raw = localStorage.getItem(CONTENT_KEY);
    if (!raw) return null;
    const parsed = JSON.parse(raw);
    if (!parsed || !parsed.data) return null;
    if (Date.now() - parsed.at > CACHE_MAX_AGE) return null;
    return parsed.data;
  } catch {
    return null;
  }
}

function writeCache(data) {
  try {
    localStorage.setItem(CONTENT_KEY, JSON.stringify({ at: Date.now(), data }));
  } catch {
    /* quota or private mode — ignore */
  }
}

/** Normalise whatever the API or the file returns into the UI shape. */
export function normalize(raw) {
  const data = raw && raw.data ? raw.data : raw;
  if (!data || !Array.isArray(data.products)) throw new Error("Malformed content");
  const settings = data.settings || {};
  const products = data.products.map((p, i) => ({
    ...p,
    price: Number(p.price) || 0,
    images: Array.isArray(p.images) ? p.images.filter(Boolean) : p.image ? [p.image] : [],
    collectionSlugs: Array.isArray(p.collectionSlugs) ? p.collectionSlugs : [],
    specs: p.specs && typeof p.specs === "object" ? p.specs : {},
    sort: Number.isFinite(p.sort) ? p.sort : i,
    featured: !!p.featured,
    inStock: p.inStock !== false,
  }));
  const categories = (data.categories || []).map((c, i) => ({ sort: i, ...c }));
  const collections = (data.collections || []).map((c, i) => ({ sort: i, ...c }));
  return {
    settings,
    categories: categories.sort((a, b) => a.sort - b.sort),
    collections: collections.sort((a, b) => a.sort - b.sort),
    products: products.sort((a, b) => a.sort - b.sort),
  };
}

async function fetchJSON(url, options = {}) {
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), 7000);
  try {
    const res = await fetch(url, {
      ...options,
      signal: options.signal || controller.signal,
      headers: { Accept: "application/json", ...(options.headers || {}) },
    });
    if (!res.ok) throw new Error(`${url} → ${res.status}`);
    return await res.json();
  } finally {
    clearTimeout(timeout);
  }
}

export function loadContent({ force = false } = {}) {
  if (contentPromise && !force) return contentPromise;

  contentPromise = (async () => {
    // 1. Live API
    if (API_BASE) {
      try {
        const raw = await fetchJSON(`${API_BASE}/api/content`, { cache: "no-store" });
        const data = normalize(raw);
        state.content = data;
        state.online = true;
        state.loading = false;
        source = "api";
        writeCache(data);
        return data;
      } catch (err) {
        console.warn("[CE] API unavailable, falling back to static data", err);
      }
    }

    // 2. Bundled JSON
    try {
      const raw = await fetchJSON("data/content.json", { cache: "no-cache" });
      const data = normalize(raw);
      state.content = data;
      state.online = false;
      state.loading = false;
      source = "static";
      writeCache(data);
      return data;
    } catch (err) {
      console.warn("[CE] bundled data failed", err);
    }

    // 3. Cache
    const cached = readCache();
    if (cached) {
      const data = normalize(cached);
      state.content = data;
      state.online = false;
      state.loading = false;
      source = "cache";
      return data;
    }

    state.loading = false;
    throw new Error("Catalogue unavailable");
  })();

  return contentPromise;
}

export function dataSource() {
  return source;
}

/** Submit a quote/order request. Returns { ok, reference, mailto? }. */
export async function submitRequest(payload) {
  if (API_BASE) {
    try {
      const res = await fetch(`${API_BASE}/api/requests`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      if (res.ok) {
        const json = await res.json().catch(() => ({}));
        return { ok: true, reference: json.reference || json.id || "", channel: "api" };
      }
      const detail = await res.json().catch(() => ({}));
      throw new Error(detail.detail || `Request failed (${res.status})`);
    } catch (err) {
      if (err && /Request failed/.test(err.message)) {
        return { ok: false, error: err.message };
      }
      console.warn("[CE] request API unreachable, using email fallback", err);
    }
  }
  return { ok: true, reference: "", channel: "email" };
}

/* ---------- Selectors ---------- */
export const selectors = {
  productBySlug: (data, slug) => data.products.find((p) => p.slug === slug),
  categoryBySlug: (data, slug) => data.categories.find((c) => c.slug === slug),
  collectionBySlug: (data, slug) => data.collections.find((c) => c.slug === slug),
  productsByCategory: (data, slug) => data.products.filter((p) => p.categorySlug === slug),
  productsByCollection: (data, slug) =>
    data.products.filter((p) => p.collectionSlugs.includes(slug)),
  featured: (data) => data.products.filter((p) => p.featured),
  related: (data, product, limit = 4) =>
    data.products
      .filter(
        (p) =>
          p.slug !== product.slug &&
          (p.categorySlug === product.categorySlug ||
            p.collectionSlugs.some((c) => product.collectionSlugs.includes(c)))
      )
      .slice(0, limit),
  price: (data, value) => {
    const settings = data.settings || {};
    const currency = settings.currency || "EUR";
    const locale = settings.locale || "en-IE";
    try {
      return new Intl.NumberFormat(locale, {
        style: "currency",
        currency,
        maximumFractionDigits: Number.isInteger(value) ? 0 : 2,
        minimumFractionDigits: 0,
      }).format(value);
    } catch {
      return `${currency} ${value}`;
    }
  },
};

/* ---------- Small helpers reused by views ---------- */
export function placeholderMedia() {
  return `<span class="fallback">${icon("sparkle")}<span>Cocktail Embassy</span></span>`;
}
