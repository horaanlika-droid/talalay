/**
 * Renders every storefront view against data/content.json without a browser.
 *
 * It stubs just enough DOM for the modules to import, then calls each view and
 * asserts it produced HTML. Cheap regression net for data-shape changes:
 *
 *     node tools/render_check.mjs
 */
import { readFile } from "node:fs/promises";
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

ok("request renders", views.requestView(data).html.length > 500);
ok("info renders", views.infoView(data).html.length > 500);

let failed = 0;
for (const [name, passed] of checks) {
  if (!passed) {
    failed += 1;
    console.log(`FAIL ${name}`);
  }
}
console.log(`\n${checks.length - failed}/${checks.length} checks passed`);
process.exit(failed ? 1 : 0);
