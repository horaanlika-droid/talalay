/** Cocktail Embassy — web admin panel (no Telegram required). ***************

Password-protected in-browser back office. Edits live settings, products,
categories and collections on the API server (SQLite). The storefront reads
the same API, so changes appear on the shop immediately — no redeploy.

Requires `window.CE_CONFIG.apiBase` to point at a running `python main.py`
server and `ADMIN_PASSWORD` set on the server.

Usage from app.js router: route `#/admin` → login → adminView(data).

    import { adminView, isAdmin, logout } from "./admin.js";

*/

import { mediaUrl, apiBase, isStatic } from "./api.js";
import { esc, attr, toast } from "./ui.js";
import { icon } from "./icons.js";

const API = (apiBase() || "").replace(/\/$/, "");
const TOKEN_KEY = "ce.admin.token";

let adminToken = "";
// restore session on page load
try {
  adminToken = localStorage.getItem(TOKEN_KEY) || "";
} catch { /* ignore */ }

/* -------------------------------------------------------------- auth API */

export function isAdmin() {
  return !!adminToken;
}

export function logout() {
  adminToken = "";
  try { localStorage.removeItem(TOKEN_KEY); } catch { /* ignore */ }
  location.hash = "#/";
  location.reload();
}

export async function adminLogin(password) {
  const res = await fetch(`${API}/api/admin/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ password }),
  });
  if (!res.ok) throw new Error(await res.text() || "login failed");
  const json = await res.json();
  adminToken = json.token;
  try { localStorage.setItem(TOKEN_KEY, adminToken); } catch { /* ignore */ }
  return adminToken;
}

function authHeaders() {
  return adminToken ? { Authorization: `Bearer ${adminToken}` } : {};
}

async function api(path, options = {}) {
  const res = await fetch(`${API}${path}`, {
    ...options,
    headers: { "Accept": "application/json", ...authHeaders(), ...(options.headers || {}) },
  });
  if (res.status === 401) {
    logout();
    throw new Error("session expired");
  }
  if (!res.ok) throw new Error(await res.text() || `request failed ${res.status}`);
  return await res.json();
}

/* -------------------------------------------------------------- sheet helpers */

let sheetEl = null;

function openSheet(el) {
  sheetEl = el;
  el.style.display = "block";
  document.body.style.overflow = "hidden";
}

function closeSheet() {
  if (sheetEl) sheetEl.style.display = "none";
  sheetEl = null;
  document.body.style.overflow = "";
}

/* -------------------------------------------------------------- UI helpers */

function input(label, name, value, type = "text", placeholder = "") {
  return `<div class="admin__field">
    <label class="admin__label">${esc(label)}</label>
    <input class="admin__input" name="${esc(name)}" type="${esc(type)}"
      value="${esc(value || "")}" placeholder="${esc(placeholder)}">
  </div>`;
}

function textarea(label, name, value, rows = 3) {
  return `<div class="admin__field">
    <label class="admin__label">${esc(label)}</label>
    <textarea class="admin__textarea" name="${esc(name)}" rows="${rows}">${esc(value || "")}</textarea>
  </div>`;
}

function btn(label, kind = "default") {
  return `<button class="admin__btn admin__btn--${esc(kind)}">${esc(label)}</button>`;
}

function card(title, body, actions = "") {
  return `<div class="admin__card">
    <div class="admin__card-head">
      <h3 class="admin__card-title">${esc(title)}</h3>
      <div class="admin__card-actions">${actions}</div>
    </div>
    <div class="admin__card-body">${body}</div>
  </div>`;
}

/* -------------------------------------------------------------- views */

function loginView() {
  return {
    title: "Вход в админку",
    html: `
      <div class="admin admin--login">
        <div class="admin__shell">
          <img src="assets/brand/mark-dark.png" alt="Cocktail Embassy" class="admin__logo">
          <h1 class="admin__h1">Админ-панель</h1>
          <p class="admin__subtitle">Редактирование каталога и настроек сайта</p>
          <form class="admin__card admin__login-form" novalidate>
            <div class="admin__card-body">
              ${input("Пароль", "password", "", "password", "введите админ-пароль")}
              <div class="admin__field" style="margin-top:14px;text-align:right">
                ${btn("Войти", "primary")}
              </div>
            </div>
          </form>
          <p class="admin__hint">Если пароля ещё нет — задайте переменную ADMIN_PASSWORD на сервере.</p>
        </div>
      </div>
    `,
    mount(main) {
      const form = main.querySelector(".admin__login-form");
      if (!form) return;
      const inp = form.querySelector('[name="password"]');
      form.addEventListener("submit", async (e) => {
        e.preventDefault();
        try {
          await adminLogin(inp.value);
          toast("Вход выполнен");
          location.hash = "#/admin";
          location.reload();
        } catch (err) {
          toast("Неверный пароль");
          console.error(err);
        }
      });
      inp.addEventListener("keydown", (e) => { if (e.key === "Enter") form.requestSubmit?.(); });
    },
  };
}

/* -------------------------------------------------------------- settings */

function selectorsPrice(data, value) {
  const s = data.settings || {};
  try {
    return new Intl.NumberFormat(s.locale || "en-AE", { style: "currency", currency: s.currency || "AED", maximumFractionDigits: 0 }).format(value);
  } catch { return `${s.currency || "AED"} ${value}`; }
}

function settingsView(data) {
  const s = data.settings || {};
  const c = s.contacts || {};
  return {
    title: "Настройки",
    html: `
      <div class="admin admin--settings">
        <header class="admin__bar">
          <h1 class="admin__h1">Настройки сайта</h1>
          <div class="admin__bar-right">${btn("Сохранить", "primary")}</div>
        </header>
        <form class="admin__form" id="admin-settings-form">
          <div class="admin__grid admin__grid--2">
            ${input("Название бренда", "brand", s.brand)}
            ${input("Валюта", "currency", s.currency || "AED")}
            ${input("Теглайн", "tagline", s.tagline)}
            ${input("Локаль", "locale", s.locale || "en-AE")}
            ${textarea("Объявление (ticker строка)", "announcement", s.announcement || "")}
            ${input("Примечание к цене", "priceNote", s.priceNote || "")}
            ${textarea("Примечание к заявке", "requestNote", s.requestNote || "")}
            ${textarea("Примечание к доставке", "shippingNote", s.shippingNote || "")}
            ${input("Бесплатная доставка от", "freeShippingFrom", s.freeShippingFrom || "", "number")}
            ${input("Стоимость доставки", "shippingCost", s.shippingCost || "", "number")}
            ${textarea("О бренде (about)", "about", s.about || "", 4)}
          </div>
          <h3 class="admin__section-title">Контакты</h3>
          <div class="admin__grid admin__grid--2">
            ${input("Email", "contacts.email", c.email || "")}
            ${input("Телефон", "contacts.phone", c.phone || "")}
            ${input("WhatsApp", "contacts.whatsapp", c.whatsapp || "")}
            ${input("Telegram", "contacts.telegram", c.telegram || "")}
            ${input("Instagram", "contacts.instagram", c.instagram || "")}
            ${input("Адрес", "contacts.address", c.address || "")}
            ${input("Часы работы", "contacts.hours", c.hours || "")}
          </div>
          <h3 class="admin__section-title">Бегущая строка (ticker)</h3>
          ${textarea("Одна строка на каждую", "ticker", Array.isArray(s.ticker) ? s.ticker.join("\n") : (s.ticker || ""), 4)}
          <h3 class="admin__section-title">Марки под герой (marquee)</h3>
          ${textarea("Одна строка на каждую (*курсив*)", "marquee", Array.isArray(s.marquee) ? s.marquee.join("\n") : (s.marquee || ""), 4)}
        </form>
      </div>
    `,
    mount(main) {
      const form = main.querySelector("#admin-settings-form");
      if (!form) return;
      form.addEventListener("submit", async (e) => {
        e.preventDefault();
        const formData = new FormData(form);
        const payload = {};
        for (const [key, value] of formData.entries()) {
          if (key.startsWith("contacts.")) {
            const inner = key.split(".")[1];
            if (!payload.contacts) payload.contacts = {};
            payload.contacts[inner] = value;
          } else if (key === "ticker" || key === "marquee") {
            payload[key] = value.split("\n").map((v) => v.trim()).filter(Boolean);
          } else if (key === "freeShippingFrom" || key === "shippingCost") {
            payload[key] = Number(value) || 0;
          } else {
            payload[key] = value;
          }
        }
        try {
          for (const [key, value] of Object.entries(payload)) {
            await api("/api/admin/settings", {
              method: "PUT",
              headers: { "Content-Type": "application/json" },
              body: JSON.stringify({ key, value }),
            });
          }
          toast("Настройки сохранены");
          window.dispatchEvent(new Event("ce-content-updated"));
        } catch (err) {
          toast("Ошибка сохранения: " + err.message);
          console.error(err);
        }
      });
    },
  };
}

/* -------------------------------------------------------------- products */

function productsView(data) {
  const products = data.products || [];
  const categories = data.categories || [];
  const catOptions = categories.map((c) => `<option value="${esc(c.slug)}">${esc(c.name)}</option>`).join("");

  const list = products.map((p) => `
    <div class="admin__product-row" data-slug="${esc(p.slug)}">
      <div class="admin__product-thumb"><img src="${attr(mediaUrl(p.images?.[0] || ""))}" alt=""></div>
      <div class="admin__product-info">
        <div class="admin__product-name">${esc(p.name)}</div>
        <div class="admin__product-meta">${esc(p.slug)} · ${selectorsPrice(data, p.price)} · ${p.categorySlug || "—"} · ${p.featured ? "★" : ""} ${p.inStock !== false ? "в наличии" : "под заказ"}</div>
      </div>
      <div class="admin__product-actions">
        <button class="admin__btn admin__btn--default admin__edit" data-slug="${esc(p.slug)}">Редактировать</button>
        <button class="admin__btn admin__btn--danger admin__delete" data-slug="${esc(p.slug)}">Удалить</button>
      </div>
    </div>
  `).join("") || `<div class="admin__empty">Товаров нет</div>`;

  return {
    title: "Товары",
    html: `
      <div class="admin admin--products">
        <header class="admin__bar">
          <h1 class="admin__h1">Товары</h1>
          <div class="admin__bar-right">${btn("Добавить товар", "primary")}</div>
        </header>
        <div class="admin__product-list">${list}</div>
        <div class="admin__sheet" id="admin-product-sheet" style="display:none">
          <div class="admin__sheet-inner">
            <button class="admin__sheet-close" data-admin-sheet-close>${icon("chevronDown")}</button>
            <form class="admin__form" id="admin-product-form">
              <input type="hidden" name="slug">
              ${input("Название", "name", "", "text")}
              ${input("Подзаголовок", "subtitle", "", "text")}
              ${textarea("Описание", "description", "", 3)}
              <div class="admin__grid admin__grid--2">
                ${input("Цена (AED)", "price", "", "number", "0")}
                ${input("Объём", "volume", "", "text", "330 ml")}
                <select class="admin__input" name="categorySlug">${catOptions}</select>
                ${input("Бейдж (NEW и т.д.)", "badge", "", "text")}
              </div>
              <div class="admin__grid admin__grid--2">
                <label class="admin__label admin__label--checkbox">
                  <input type="checkbox" name="featured"> featured
                </label>
                <label class="admin__label admin__label--checkbox">
                  <input type="checkbox" name="inStock" checked> в наличии
                </label>
              </div>
              ${textarea("Изображения (по одной на строку)", "images", "", 3)}
              ${textarea("Спецификации (JSON)", "specs", "{}", 3)}
              <div class="admin__field" style="margin-top:16px;text-align:right">
                ${btn("Сохранить товар", "primary")} ${btn("Отмена", "default")}
              </div>
            </form>
          </div>
        </div>
      </div>
    `,
    mount(main) {
      const sheet = main.querySelector("#admin-product-sheet");
      const form = main.querySelector("#admin-product-form");
      const close = main.querySelector("[data-admin-sheet-close]");
      const listEl = main.querySelector(".admin__product-list");

      close.addEventListener("click", () => closeSheet());

      listEl.addEventListener("click", async (e) => {
        const del = e.target.closest(".admin__delete");
        const edit = e.target.closest(".admin__edit");
        if (del) {
          const slug = del.dataset.slug;
          if (!confirm(`Удалить ${slug}?`)) return;
          try {
            await api(`/api/admin/products/${slug}`, { method: "DELETE" });
            toast("Удалён");
            location.reload();
          } catch (err) { toast("Ошибка: " + err.message); }
          return;
        }
        if (edit) {
          const slug = edit.dataset.slug;
          try {
            const content = await api("/api/admin/content");
            const p = content.products.find((x) => x.slug === slug);
            if (!p) return;
            form.querySelector('[name="slug"]').value = p.slug;
            form.querySelector('[name="name"]').value = p.name || "";
            form.querySelector('[name="subtitle"]').value = p.subtitle || "";
            form.querySelector('[name="description"]').value = p.description || "";
            form.querySelector('[name="price"]').value = p.price || "";
            form.querySelector('[name="volume"]').value = p.volume || "";
            form.querySelector('[name="categorySlug"]').value = p.categorySlug || "";
            form.querySelector('[name="badge"]').value = p.badge || "";
            form.querySelector('[name="featured"]').checked = !!p.featured;
            form.querySelector('[name="inStock"]').checked = p.inStock !== false;
            form.querySelector('[name="images"]').value = Array.isArray(p.images) ? p.images.join("\n") : "";
            form.querySelector('[name="specs"]').value = JSON.stringify(p.specs || {}, null, 2);
            openSheet(sheet);
          } catch (err) { toast("Ошибка загрузки товара: " + err.message); }
        }
      });

      main.querySelector(".admin__bar-right").addEventListener("click", () => {
        form.reset();
        form.querySelector('[name="slug"]').value = "";
        form.querySelector('[name="featured"]').checked = false;
        form.querySelector('[name="inStock"]').checked = true;
        form.querySelector('[name="specs"]').value = "{}";
        openSheet(sheet);
      });

      form.addEventListener("submit", async (e) => {
        e.preventDefault();
        const fd = new FormData(form);
        const payload = {};
        for (const [key, value] of fd.entries()) {
          if (key === "images") {
            payload[key] = value.split("\n").map((v) => v.trim()).filter(Boolean);
          } else if (key === "specs") {
            try { payload[key] = JSON.parse(value || "{}"); } catch { payload[key] = {}; }
          } else if (key === "price") {
            payload[key] = Number(value) || 0;
          } else if (key === "featured" || key === "inStock") {
            // checkbox presence handled below
          } else {
            payload[key] = value;
          }
        }
        payload.featured = fd.has("featured");
        payload.inStock = fd.has("inStock");
        const slug = fd.get("slug");
        try {
          if (slug) {
            await api(`/api/admin/products/${slug}`, { method: "PUT", headers: { "Content-Type": "application/json" }, body: JSON.stringify(payload) });
          } else {
            await api("/api/admin/products", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(payload) });
          }
          toast("Товар сохранён");
          closeSheet();
          location.reload();
        } catch (err) { toast("Ошибка: " + err.message); }
      });
    },
  };
}

/* -------------------------------------------------------------- categories */

function categoriesView(data) {
  const categories = data.categories || [];
  const list = categories.map((c) => `
    <div class="admin__card" style="padding:10px 14px;margin-bottom:8px;display:flex;align-items:center;gap:14px">
      <div style="flex:1">
        <div class="admin__card-title">${esc(c.name)}</div>
        <div style="font-size:11px;color:#8a8a8a">${esc(c.slug)} · sort ${c.sort}</div>
      </div>
      <div class="admin__card-actions">
        <button class="admin__btn admin__btn--default" data-cat-slug="${esc(c.slug)}">Редактировать</button>
      </div>
    </div>
  `).join("") || `<div class="admin__empty">Категорий нет</div>`;

  return {
    title: "Категории",
    html: `<div class="admin admin--categories"><header class="admin__bar"><h1 class="admin__h1">Категории</h1></header>${list}</div>`,
    mount(main) {
      main.querySelectorAll("[data-cat-slug]").forEach((el) => {
        el.addEventListener("click", async () => {
          const slug = el.dataset.catSlug;
          const name = prompt("Новое название категории:", el.closest(".admin__card").querySelector(".admin__card-title").textContent);
          if (name === null) return;
          try {
            await api(`/api/admin/categories/${slug}`, {
              method: "PUT",
              headers: { "Content-Type": "application/json" },
              body: JSON.stringify({ name, slug, blurb: "", sort: 0 }),
            });
            toast("Категория сохранена");
            location.reload();
          } catch (err) { toast("Ошибка: " + err.message); }
        });
      });
    },
  };
}

/* -------------------------------------------------------------- requests */

function requestsView() {
  return {
    title: "Заявки",
    html: `<div class="admin admin--requests"><header class="admin__bar"><h1 class="admin__h1">Заявки</h1></header><div class="admin__empty">Заявки появятся после первых оформлений</div></div>`,
  };
}

/* -------------------------------------------------------------- main admin shell */

export function adminView(data) {
  if (!isAdmin()) return loginView();
  if (isStatic()) {
    return {
      title: "Админ-панель",
      html: `
        <div class="admin admin--panel">
          <header class="admin__shell-header">
            <div class="admin__shell-brand">
              <img src="assets/brand/mark-dark.png" alt="Cocktail Embassy" class="admin__logo">
              <span class="admin__shell-title">Админ-панель</span>
            </div>
            <div class="admin__shell-actions">${btn("Выйти", "danger")}</div>
          </header>
          <div class="admin__empty">
            <h2 style="font-size:16px;margin:0 0 8px">API не настроен</h2>
            <p style="font-size:13px;color:#8a8a8a;margin:0 0 16px">
              Чтобы редактировать контент прямо на сайте, запустите сервер:
              <code style="color:#c8c8c8">cd server && python main.py</code><br>
              и укажите в <code>js/config.js</code>:<br>
              <code style="color:#c8c8c8">apiBase: "http://localhost:8080"</code>
            </p>
            ${btn("Войти", "primary")}
          </div>
        </div>
      `,
      mount(main) {
        main.querySelector(".admin__btn--danger")?.addEventListener("click", () => { logout(); });
        main.querySelector(".admin__btn--primary")?.addEventListener("click", () => { location.reload(); });
      },
    };
  }

  const active = (location.hash.match(/#\/admin\/(\w+)/) || [])[1] || "settings";
  const tabs = [
    { key: "settings", label: "Настройки" },
    { key: "products", label: "Товары" },
    { key: "categories", label: "Категории" },
    { key: "requests", label: "Заявки" },
  ];

  const tabHtml = tabs.map((t) => `
    <a href="#/admin/${t.key}" class="admin__tab${active === t.key ? " admin__tab--active" : ""}" data-admin-tab="${t.key}">${esc(t.label)}</a>
  `).join("");

  const view = active === "products" ? productsView(data)
    : active === "categories" ? categoriesView(data)
    : active === "requests" ? requestsView(data)
    : settingsView(data);

  return {
    title: view.title || "Админка",
    html: `
      <div class="admin admin--panel">
        <header class="admin__shell-header">
          <div class="admin__shell-brand">
            <img src="assets/brand/mark-dark.png" alt="Cocktail Embassy" class="admin__logo">
            <span class="admin__shell-title">Админ-панель</span>
          </div>
          <div class="admin__shell-actions">
            <a href="#/" class="admin__btn admin__btn--ghost">В магазин</a>
            ${btn("Выйти", "danger")}
          </div>
        </header>
        <nav class="admin__tabs">${tabHtml}</nav>
        <div class="admin__sheet">${view.html}</div>
      </div>
    `,
    mount(main) {
      main.querySelector(".admin__btn--danger")?.addEventListener("click", () => { logout(); });
      main.querySelectorAll("[data-admin-tab]").forEach((el) => {
        el.addEventListener("click", (e) => {
          e.preventDefault();
          location.hash = `#/admin/${el.dataset.adminTab}`;
        });
      });
      if (typeof view.mount === "function") view.mount(main.querySelector(".admin__sheet") || main, { data });
    },
  };
}
