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

---

## Next-session brief — photo regeneration & futuristic UI (queued 2026-10-30)

> **RU (задание владельца, дословно):** сгенерировать бокалы как в тайлах референса, но **100 % идентичные** тем, что лежат в репо, с **тончайшим стеклом**; добавить на бокалы эффект света **в духе мыльных пузырей**; фотографии с напитками перегенерировать под ту же стилистику; приложение должно выглядеть **футуристично, воздушно и интуитивно**, как референсы IMG_1429 / IMG_1430 («1419» в переписке = IMG_1429) и макет интерфейса IMG_1440. Формы бокалов не менять никогда.

Owner's request (EN): regenerate every glass photo in top quality — each glass alone on one dark background with a glow — silhouettes **100 % identical** to the pieces already in the repo, with **the thinnest possible hand-blown glass**, plus a **soap-bubble (thin-film iridescent) light effect** on the glass. Drink/editorial photos get regenerated into the same visual world. The storefront must become **futuristic, airy and intuitive**, per references `IMG_1429` / `IMG_1430` and interface mock `IMG_1440`. Glass shapes are never to be changed.

### References (all in repo)

| File | What it defines |
| --- | --- |
| `brand-source/IMG_1429.jpeg` | “Levitating” hero: deep-navy space, floating glasses, soft radial glow, elliptical shadow under each piece, ultra-thin crystal |
| `brand-source/IMG_1430.jpeg` | Product stage: single glass on navy, radial glow halo, razor-thin stem and walls |
| `brand-source/IMG_1440.png` | Full interface mock: dark-navy storefront, hero with three glasses + reflections, collection tile row, spec-driven product cards, cart panel |
| `assets/products/*.webp` (current) | **Shape donors** — the exact silhouettes to preserve |
| `brand-source/style-tests/thin-glass-*.png` | First-pass thin-glass renders (approved direction for backdrop/glow; iridescence still to be added) |

### Task 1 — product photos (10 glasses)

For each of `martini`, `goblet`, `coupe`, `highball`, `saucer`, `rocks`, `tumbler`, `footed`, `hurricane`, `cylinder`:

1. **Image-to-image edit from the current `assets/products/<name>.webp`** (shape donor). Never text-to-image: silhouette, proportions, bowl curvature, stem, foot and etched details (dot constellations on `highball` and `cylinder`) must match 100 %.
2. **Ultra-thin glass**: paper-thin transparent walls, razor-thin barely-visible rim, fine slender stem, delicate foot — walls read as almost invisible, drawn only by fine bright edge lines. No thick/chunky glass.
3. **Soap-bubble light effect**: subtle thin-film iridescence — a pearl/rainbow sheen (magenta–cyan–gold) riding the rim and highlights, like light on a soap bubble. Tasteful accent, not a sticker over the glass.
4. **One shared setting**: seamless deep-navy studio backdrop (`#101B2E → #0A1220`), cool-white radial glow halo tracing the silhouette, faint light beam from above, dark polished floor with a soft elliptical shadow + faint mirror reflection (levitating feel of 1429/1430).
5. Empty glass, spotless, no props, no text, no watermark; centered, whole glass visible, even margins.

**Progress (2026-10-30):** approved etalon + masters ready in `brand-source/generated/`:
`coupe`, `martini`, `goblet`, `highball`, `saucer`, `rocks` (QC passed: shape 1:1,
thin walls, iridescence, consistent light physics). **Remaining:** generate `tumbler`,
`footed`, `hurricane`, `cylinder` + the 4 editorial photos, then deliver webp + `-sm`
over the existing filenames (Task 3). Generation limit is 10 images per turn — plan
batches accordingly.

### Task 2 — drink / editorial photos

Regenerate `crystal-light`, `noir-coupe`, `sunlit-sour`, `red-vessel` (`assets/editorial/`) into the same navy-glow world: keep vessel shapes, drink colours and layers; replace concrete/sunlight staging with the dark navy backdrop, glow halo, iridescent highlights and soft reflection. `noir-coupe` also serves as the bitters product image.

### Task 3 — pipeline, deliverables, QC

- Masters (PNG or lossless webp) → `brand-source/generated/`.
- Deliver webp q≈82 **over the existing filenames** `assets/products/<name>.webp` and `assets/editorial/<name>.webp` (zero code changes); `-sm` thumbs = resize to 700 px wide.
- QC: overlay before/after silhouettes to prove the shape is unchanged; check thinness and etching; check one consistent backdrop tone across all cards.
- If an image-model endpoint answers 403/“flagged”, simply retry the call — it routes to another endpoint.

### Task 4 — futuristic, airy, intuitive UI

Restyle the storefront per `IMG_1440` + `IMG_1429/1430`: dark-navy theme, floating hero product with glow, collection tile row, spec-driven product cards, sticky request/cart panel, generous negative space, spring easing. Keep the static architecture, hash routing and `content.json`-driven data. Airy = fewer boxes, more light and space.

### Prompt template (product shot)

```
Two reference images. Image 1 is the exact product to photograph: keep its shape 100%
identical — <shape description> — same silhouette, proportions, stem, foot, etched
details; do not redesign or substitute it. Image 2 is ONLY a style reference for
lighting, background and glass delicacy — never copy its glass shape. Produce an
ultra-premium commercial product photograph of the glass from image 1. Critical:
ultra-thin hand-blown crystal — paper-thin transparent walls, razor-thin barely
visible rim, fine slender stem; walls almost invisible, drawn only by fine bright
edge lines; no thick, chunky or heavy glass. Add a subtle soap-bubble thin-film
iridescence: pearl/rainbow sheen (magenta-cyan-gold) on the rim and highlights.
Setting: seamless deep navy-blue studio backdrop (#101B2E → #0A1220), soft cool-white
radial glow behind the glass tracing its silhouette, gentle rim light, faint light
beam from above; glass stands on a dark polished surface with soft elliptical shadow
and faint mirror reflection. Physically consistent lighting from a single soft key
source above and slightly behind: soft elliptical contact shadow directly under the
foot/base, centered; vertical mirror reflection exactly below the contact point,
fading smoothly downward; highlights, rim light and iridescent glints all agree with
that one source — no contradictory second shadow, no offset or tilted reflection.
Centered, symmetrical, entire glass visible with generous even margins. Photorealistic,
razor sharp, high dynamic range, no props, no text, no watermark.
```
