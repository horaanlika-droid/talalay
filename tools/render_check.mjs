/**
 * Renders every storefront view against data/content.json without a browser.
 *
 * It stubs just enough DOM for the modules to import, then calls each view and
 * asserts it produced HTML. Cheap regression net for data-shape changes:
 *
 *     node tools/render_check.mjs
 */
import { readFile, access } from "node:fs/promises";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";

const root = join(dirname(fileURLToPath(import.meta.url)), "..");

const el = () => ({
  innerHTML: "",
  dataset: {},
  style: {},
  classList: { add() {}, remove() {}, toggle() {} },
  setAttribute() {},
  appendChild() {},
  replaceChildren() {},
  focus() {},
  addEventListener() {},
  querySelector: () => null,
  querySelectorAll: () => [],
});

globalThis.window = {
  CE_CONFIG: {},
  localStorage: { getItem: () => null, setItem() {}, removeItem() {} },
  addEventListener() {},
  matchMedia: () => ({ matches: false, addEventListener() {} }),
  scrollTo() {},
};
globalThis.localStorage = window.localStorage;
globalThis.document = {
  getElementById: () => el(),
  addEventListener() {},
  querySelector: () => null,
  querySelectorAll: () => [],
  createElement: () => el(),
  body: el(),
  documentElement: el(),
};
globalThis.location = { hash: "", pathname: "/" };
globalThis.requestAnimationFrame = () => 0;

const raw = JSON.parse(await readFile(join(root, "data/content.json"), "utf8"));
// the app boots itself on import and asks for the catalogue: answer from disk
globalThis.fetch = async (url) =>
  String(url).includes("content.json")
    ? { ok: true, json: async () => raw }
    : { ok: false, status: 404, json: async () => ({}) };
const api = await import(join(root, "js/api.js"));
const views = await import(join(root, "js/views.js"));

const data = api.normalize(raw);
const checks = [];
const ok = (name, condition) => checks.push([name, !!condition]);

ok("categories", data.categories.length >= 4);
ok("products", data.products.length > 0);
ok("articles unique", new Set(data.products.map((p) => p.article)).size === data.products.length);
ok("no collectionSlugs", data.products.every((p) => !("collectionSlugs" in p)));

const home = views.homeView(data);
ok("home renders", home.html.length > 2000);
ok("home tiles = categories", (home.html.match(/class="tile spotlight"/g) || []).length === data.categories.length);

const shop = views.shopView(data, {});
ok("shop renders", shop.html.includes("data-shop-search") && shop.html.includes("data-open-filters"));
const shopFiltered = views.shopView(data, { c: "rocks", new: "1", max: "100" });
ok("shop accepts filters", shopFiltered.html.includes('id="app"') === false && shopFiltered.html.length > 500);

for (const product of data.products) {
  const view = views.productView(data, product.slug);
  ok(`product ${product.slug}`, view && view.html.includes("pdp__title"));
}

const app = await import(join(root, "js/app.js"));
const tick = app.tickerHTML(data.settings || {});
ok("ticker carries contacts", /@|\+971/.test(tick));
ok("ticker drops the country line", !/china/i.test(tick));
const heroSlides = (home.html.match(/data-hero-slide=/g) || []).length;
ok("hero carousel = slides", heroSlides === (data.settings.hero || []).length && heroSlides > 1);
ok("hero uses one plate per window", (home.html.match(/hero__slide/g) || []).length >= heroSlides);
ok("hero plates are full-bleed sources", home.html.includes("covers/hero-levitating-martini/cover.webp"));
const marquee = (home.html.match(/kinetic__row/g) || []).length;
ok("big running line present", marquee === 1);
ok("request renders", views.requestView(data).html.length > 500);
const info = views.infoView(data);
ok("info renders", info.html.length > 500);
ok("info uses cover folders", info.html.includes("covers/info-banner/cover.webp") && info.html.includes("covers/info-story/cover.webp"));
ok("faq svgs have explicit dimensions", /accordion__trigger[\s\S]*?<svg width="\d+" height="\d+"/.test(info.html));
const cssText = await readFile(join(root, "css/app.css"), "utf8");
ok("css sizes accordion trigger svg", /\.accordion__trigger svg\s*\{[^}]*width:\s*\d+px/.test(cssText));
const swText = await readFile(join(root, "sw.js"), "utf8");
ok("sw network-first for photo folders", /\(glasses\|covers\|packaging\)/.test(swText));

// Verify every product, category, hero, and site cover points to an existing folder file
const exists = async (rel) => {
  try {
    await access(join(root, String(rel).split("?")[0]));
    return true;
  } catch {
    return false;
  }
};
let allProductFilesExist = true;
for (const p of data.products) {
  const expectedPrefix =
    p.categorySlug === "acids" || p.categorySlug === "essences"
      ? `packaging/${p.slug}/`
      : `glasses/${p.slug}/`;
  if (!p.images[0]?.startsWith(expectedPrefix) || !(await exists(p.images[0]))) {
    allProductFilesExist = false;
  }
}
ok("all 52 product folders exist with photos", allProductFilesExist);

let allCoverFilesExist = true;
for (const c of data.categories) {
  if (!c.cover?.startsWith(`covers/category-${c.slug}/`) || !(await exists(c.cover))) {
    allCoverFilesExist = false;
  }
}
for (const s of data.settings.hero || []) {
  if (!s.cover?.startsWith(`covers/hero-${s.productSlug}/`) || !(await exists(s.cover))) {
    allCoverFilesExist = false;
  }
}
for (const k of ["homeCraft", "infoBanner", "infoStory", "ogShare"]) {
  if (!(await exists(data.settings.covers?.[k] || ""))) allCoverFilesExist = false;
}
ok("all category, hero, and page cover folders exist", allCoverFilesExist);

// Verify dynamic folder auto-discovery (replacing/adding files with any name or extension)
const defaults = JSON.parse(await readFile(join(root, "data/folder-defaults.json"), "utf8"));
const cloned = api.normalize(JSON.parse(JSON.stringify(raw)));
api.applyFolderFiles(
  cloned,
  [
    // User drops IMG_9999.jpg into glasses/levitating-martini WITHOUT deleting seed photo.webp
    { path: "glasses/levitating-martini/photo.webp", sha: defaults["glasses/levitating-martini/photo.webp"] },
    { path: "glasses/levitating-martini/IMG_9999.jpg", sha: "abcdef1234567890" },
    // User drops 2 angles into glasses/champagne-saucer
    { path: "glasses/champagne-saucer/1.png", sha: "1111222233334444" },
    { path: "glasses/champagne-saucer/2.png", sha: "5555666677778888" },
    // User replaces main hero cover in covers/hero-levitating-martini while leaving seed portrait.webp untouched
    { path: "covers/hero-levitating-martini/cover.webp", sha: "9999888877776666" },
    { path: "covers/hero-levitating-martini/portrait.webp", sha: defaults["covers/hero-levitating-martini/portrait.webp"] },
    // User drops custom PNG into covers/category-cocktail
    { path: "covers/category-cocktail/new-cover.png", sha: "feedface12345678" },
  ],
  defaults
);
const martiniAfter = cloned.products.find((p) => p.slug === "levitating-martini");
ok(
  "new photo in glass folder wins over untouched seed photo.webp",
  martiniAfter.images.length === 1 && martiniAfter.images[0] === "glasses/levitating-martini/IMG_9999.jpg?v=abcdef12"
);
const saucerAfter = cloned.products.find((p) => p.slug === "champagne-saucer");
const saucerPdp = views.productView(cloned, "champagne-saucer");
ok(
  "multiple photos in glass folder render gallery thumbs",
  saucerAfter.images.length === 2 && saucerPdp.html.includes("pdp__thumbs")
);
const heroAfter = cloned.settings.hero.find((s) => s.productSlug === "levitating-martini");
const homeAfter = views.homeView(cloned);
ok(
  "replacing hero cover clears untouched default portrait so mobile updates too",
  heroAfter.cover === "covers/hero-levitating-martini/cover.webp?v=99998888" &&
    !heroAfter.portraitCover &&
    !homeAfter.html.includes("covers/hero-levitating-martini/portrait.webp")
);
const cocktailCatAfter = cloned.categories.find((c) => c.slug === "cocktail");
ok(
  "new photo in category cover folder updates category cover",
  cocktailCatAfter.cover === "covers/category-cocktail/new-cover.png?v=feedface"
);

const admin = await import(join(root, "js/admin.js"));
const loginScreen = admin.adminView(data);
ok("admin shows login form without server", loginScreen.html.includes("admin__login-form") && !loginScreen.html.includes("API не настроен"));
await admin.adminLogin("embassy2026");
ok("admin login succeeds in static mode", admin.isAdmin() === true);
for (const tab of ["products", "categories", "settings", "requests", "sync"]) {
  globalThis.location.hash = `#/admin/${tab}`;
  const panel = admin.adminView(data);
  ok(`admin ${tab} renders visible body`, panel.html.includes("admin__body") && !panel.html.includes('class="admin__sheet"'));
}
admin.logout();
ok("admin logout clears session", admin.isAdmin() === false);

let failed = 0;
for (const [name, passed] of checks) {
  if (!passed) {
    failed += 1;
    console.log(`FAIL ${name}`);
  }
}
console.log(`\n${checks.length - failed}/${checks.length} checks passed`);
process.exit(failed ? 1 : 0);
