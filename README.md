# Cocktail Embassy

A production-ready catalogue web app for **Cocktail Embassy** — hand-blown glassware
and cocktail acids for bars, hotels and studios.

| Part | Where it runs | What it does |
| --- | --- | --- |
| **Storefront** (`index.html`, `css/`, `js/`, `assets/`, `data/`) | GitHub Pages | iOS-style catalogue: hero carousel, shop with search/filters, product pages, collections, request form |
| **Back office** (`server/`) | BotHost | REST API + Telegram admin bot. Everything on the site is edited from the bot |

Live site: **https://horaanlika-droid.github.io/talalay/**

---

## The storefront

Plain static files — no build step, no dependencies. Hash routing (`#/shop`, `#/product/…`)
means it works identically on Pages, on BotHost, or from a local folder.

* **Design** — dark navy hero with levitating product photography (reference 1429),
  chrome wordmark, cream paper background, oversized negative tracking typography.
  iOS-native details: bottom tab bar, safe-area insets, sheet dialogs, spring easing,
  44 px touch targets.
* **Responsive** — single column + tab bar on phones, split hero and 4-up grid on desktop,
  sticky product stage at ≥ 900 px.
* **Catalogue** — 16 seeded pieces, 3 categories, 4 collections.
* **Requests, not checkout** — pieces are added to a request and submitted with contact
  details; the shop owner receives it in Telegram.
* **Data flow** — `API → bundled data/content.json → localStorage cache`. With no API
  configured the site is a fully working static catalogue.

### Wiring the site to the bot

Open `js/config.js` and set the URL of the BotHost service:

```js
window.CE_CONFIG = {
  apiBase: "https://your-service.bothost.ru",
  requestEmail: "orders@cocktailembassy.com",
};
```

With `apiBase` set, the catalogue and every request come from the bot/API.
Leave it empty and the site keeps running on its bundled data.

---

## The Telegram back office

Everything the storefront shows is editable from the bot — no code, no redeploy.

* **Products** — name, subtitle, description, price, volume, badge, category,
  collections, featured flag, in-stock flag, photos (send a photo to upload).
* **Collections** — the four tiles on the home page, each with a cover photo.
* **Categories** — filters in the shop (`Glassware`, `Barware`, `Acids & Other`).
* **Site & content** — brand, tagline, announcement bar, about paragraph, price note,
  request note, shipping and returns copy, currency, locale, all contact details,
  and the hero slides (which piece, headline, kicker, copy).
* **Requests** — new website requests arrive as messages with accept / in-progress /
  done / cancel actions, item list, totals and a reply link.
* **Staff access** — the owner ID is always signed in; colleagues enter the password
  once and stay signed in for `AUTH_TTL_HOURS` (72 h by default), revocable from the bot.

### Bot commands

`/start` · `/menu` · `/login` · `/logout` · `/cancel` · `/id`

`/id` shows the numeric Telegram ID — that is the value for `ADMIN_ID`.

---

## Deploying on BotHost

1. Create a service from this repository with the working directory **`server`**
   (runtime: Python, or Docker — a `Dockerfile` is included).
2. Start command: `python main.py` (or `./start.sh`).
3. Set the variables:

| Variable | Required | Meaning |
| --- | --- | --- |
| `TELEGRAM_BOT_TOKEN` | ✅ | token from @BotFather |
| `ADMIN_ID` | ✅ | your numeric Telegram ID (`/id` in the bot, or @userinfobot) |
| `ADMIN_PASSWORD` | ✅ | password for staff/second editors |
| `PUBLIC_API_URL` | auto | public service URL; detected automatically when the host exposes it |
| `STOREFRONT_URL` | auto | site URL used in bot messages |
| `PORT`, `DB_PATH`, `MEDIA_DIR`, `CORS_ORIGINS`, `AUTH_TTL_HOURS` | auto | sensible defaults |

The SQLite database and the uploaded photos live in `server/data/` and `server/media/`.
Attach a persistent volume to those two paths so content survives redeploys.

4. Open the bot → `/start` → sign in with the password → edit the catalogue.
5. Copy the service URL into `js/config.js` (`apiBase`) and push — the site is now live-wired.

API surface: `GET /api/content`, `GET /api/health`, `POST /api/requests`, `GET /media/<file>`.

---

## Local development

```bash
# storefront (no build)
python3 -m http.server 4173

# back office
cd server
python3 -m venv .venv && . .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env      # fill in the token + admin id
python main.py            # API on :8080, bot polling in the same process
```

---

## Repository layout

```
index.html              storefront entry (GitHub Pages root)
manifest.webmanifest    PWA manifest
sw.js                   offline shell
css/app.css             design tokens + all components
js/                     config, api, store, views, router, icons
data/content.json       seed catalogue (also seeds the bot database)
assets/                 optimised webp product shots, editorial photos, brand marks
server/                 FastAPI API + aiogram admin bot + Dockerfile
brand-source/           original brand photography and logo files (not used at runtime)
```
