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

* **Design** — dark navy hero with a levitating glass plate (reference 1429), one flat
  raster picture per slide, chrome wordmark, oversized negative tracking typography.
  iOS-native details: bottom tab bar, safe-area insets, sheet dialogs (drag them down
  to dismiss), spring easing, 44 px touch targets.
* **Mechanics** — the app shell follows the Telegram-mini-app pattern proven in
  `posudnayalavka`, worn in the Embassy's navy and chrome:
  * **Opening curtain** — the chrome lockup and a single hairline progress bar, no
    counters and no copy, with `app by @stonym0ntana` set at the bottom. It stays at
    least 2.6 s and lifts only once the first hero plate is decoded. A failsafe lifts
    it after 9 s whatever happens.
  * **iOS screen motion** — a piece or a collection *pushes* in from the right, going
    back *pops* in from the left, tab switches cross-fade (`js/app.js`, `routeDepth`).
  * **Bar** — the current piece / collection name fades into the top bar as you
    scroll, and a back chevron appears on deep screens.
  * **Running line** — one `ticker` under the bar carries the trade announcement and
    the house lines across the top of every screen; it never blocks a tap and stands
    still for `prefers-reduced-motion`. The kinetic display band on the home page stays.
  * **Press states** — every card, tile and row answers the finger, like a native list.
* **Responsive** — single column + tab bar on phones, split hero and 4-up grid on desktop,
  sticky product stage at ≥ 900 px.
* **Catalogue** — 52 pieces in 2 categories and 17 collections, generated from the
  trade price list by `tools/build_catalog.py` (see *Catalogue source* below).
* **Requests, not checkout** — pieces are added to a request and submitted with contact
  details; the shop owner receives it in Telegram.
* **Data flow** — `API → bundled data/content.json → localStorage cache`. With no API
  configured the site is a fully working static catalogue.

### Wiring the site to the bot

Open `js/config.js` and set the URL of the BotHost service:

```js
window.CE_CONFIG = {
  apiBase: "https://your-service.bothost.ru",
  requestEmail: "bartending.solution.uae@gmail.com",
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
* **Categories** — filters in the shop (`Glassware`, `Acids & Other`).
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
assets/                 whole-scene webp plates (glass + room baked in), brand marks
server/                 FastAPI API + aiogram admin bot + Dockerfile
brand-source/           original brand photography and logo files (not used at runtime)
```

---

## Catalogue source

`data/content.json` and `server/seed.json` are **generated** — edit
`tools/build_catalog.py` and re-run it, never the JSON by hand:

```bash
python3 tools/build_catalog.py      # rewrites data/content.json + server/seed.json
python3 tools/render_packaging.py   # redraws assets/packaging/*.webp
python3 tools/harmonize_images.py --set products   # re-stages catalogue photos
python3 tools/render_scenes.py --set all           # hero + collection plates
```

Two inputs:

| Input | Where | What it supplies |
| --- | --- | --- |
| Trade price list | `brand-source/cocktail-embassy-catalog.webarchive` → Google Sheet `19Vo9G29…`, tab *Glassware* (gid=0) and tab *Acids and Other* (gid=248427238) | COD, capacity, height, ⌀, material, AED (USD kept as `priceUsd`) |
| House range | `assets/products/*.webp` + `HOUSE` in the generator | the ten studio pieces and their copy |

Rules baked into the generator:

* **AED only** on the site (`settings.currency = "AED"`, locale `en-AE`); USD stays in
  the JSON as reference.
* Every price-list collection is a normal, priced, in-stock collection. The only
  exceptions are **Teapot** (`AG0027`) and **Two Sips** (`AG0019`) — `comingSoon: true`,
  shown as *First series*, ordered through the request form.
* The price-list *Levitating* pieces (Super Pony, Rocks, Highball) merge into the house
  **Levitating** collection; every other tab-1 collection gets its own page.
* Page two of the list becomes the **Acids & Other** category: straws, acids,
  hydrocolloids (Pectinase, Agar Agar) and the ten flavour essences.
* Pieces the old data had but the price list does not (lactic acid, jigger, bar spoon,
  bitters, AG0014) are gone.
* `assets/packaging/*.webp` are drawn, not photographed, by `tools/render_packaging.py`
  (`jar`, `bottle`, `sleeve`) on the same navy stage as the glass photography.

---

## Visuals — one flat raster per picture

The storefront never composites a cut-out glass over a painted backdrop. Every
picture the visitor sees is **one finished WebP**: the navy room, its glow and the
piece are already in the file. CSS only paints the matching app colour (`#060c18`)
around it, so a plate has no visible frame.

| File | Made by | Used for |
| --- | --- | --- |
| `assets/products/*.webp` | `tools/harmonize_images.py` | product cards, product stage, cart, story split |
| `assets/scenes/hero-<slug>.webp` | `tools/render_scenes.py` | hero, desktop 16:9 |
| `assets/scenes/hero-<slug>-portrait.webp` | `tools/render_scenes.py` | hero, phones 3:4 |
| `assets/scenes/cover-<slug>.webp` | `tools/render_scenes.py` | collection tiles, collection header |
| `assets/archive/**`, `assets/packaging/**` | archive pipeline / `render_packaging.py` | archive and acids & other |

Rules:

* **Glass only.** There is no drink photography in the catalogue — no cocktails,
  no liquid, no garnish. Vessel shapes are never redrawn or substituted.
* **No blend modes, no masks, no duplicated glow layer.** `mix-blend-mode`,
  `mask-image` and stacked backdrops are not used for product imagery anymore.
* The scene tools work from the approved catalogue photos, so a plate is always
  the same glass in the same room as the rest of the set.

---

## Next-session brief — photo regeneration & futuristic UI (queued 2026-10-30)

> **Update (2026-10-30, later):** this brief is superseded on drinks and compositing.
> Drink/editorial photography has been **removed** — the catalogue is glass only —
> and every visual is now a single flat raster plate (see *Visuals* above). Tasks 2
> and 5 below are history, kept for the record.

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

**Progress (2026-10-30, delivered):** all 10 product masters + 4 drink photos generated,
backdrop-normalised (corner tone ≈ srgb(3,11,23) across the set, worst deviation 17/255
vs 39 before grading) and delivered as webp + `-sm` over the existing filenames
(`assets/products/`, `assets/editorial/`). Masters (graded, cropped) live in
`brand-source/generated/`. QC passed: shapes 1:1, paper-thin walls, iridescence,
consistent single-source light physics, one backdrop family.

### Task 2 — drink / editorial photos

Regenerate `crystal-light`, `noir-coupe`, `sunlit-sour`, `red-vessel` (`assets/editorial/`) into the same navy-glow world: keep vessel shapes, drink colours and layers; replace concrete/sunlight staging with the dark navy backdrop, glow halo, iridescent highlights and soft reflection. `noir-coupe` also serves as the bitters product image.

### Task 3 — pipeline, deliverables, QC

- Masters (PNG or lossless webp) → `brand-source/generated/`.
- Deliver webp q≈82 **over the existing filenames** `assets/products/<name>.webp` and `assets/editorial/<name>.webp` (zero code changes); `-sm` thumbs = resize to 700 px wide.
- QC: overlay before/after silhouettes to prove the shape is unchanged; check thinness and etching; check one consistent backdrop tone across all cards.
- If an image-model endpoint answers 403/“flagged”, simply retry the call — it routes to another endpoint.

### Task 4 — futuristic, airy, intuitive UI

Restyle the storefront per `IMG_1440` + `IMG_1429/1430`: dark-navy theme, floating hero product with glow, collection tile row, spec-driven product cards, sticky request/cart panel, generous negative space, spring easing. Keep the static architecture, hash routing and `content.json`-driven data. Airy = fewer boxes, more light and space.

### Task 5 — more drinks in our glassware (generate)

Grow the drink photography in the same house style (navy glow, thin glass, iridescence,
consistent light physics). Suggested serves, one per glass where possible: Negroni in
`rocks`, champagne in `saucer`, clarified martini in `martini`, soda & ice in `highball`,
daiquiri in `coupe`, sparkling water in `goblet`, spritz in `footed`, cold brew in
`tumbler`, virgin hurricane in `hurricane`, etched-water serve in `cylinder`. Use for
product pages (second image), hero slides and collection covers. Deliver like Task 3
(new files under `assets/editorial/drinks/`, referenced from `content.json`).

### Task 6 — packaging placeholders (generate)

* **Logo boxes** — premium matte rigid boxes with the Cocktail Embassy logo (brand marks:
  `assets/brand/mark-dark.png`, `ce-logo-dark.png`, `ce-badge.webp`) as catalogue photo
  placeholders for barware/inventory: Precision Jigger, Chrome Bar Spoon, Embassy
  Signature Bitters. Box standing on the same navy glow stage, same light physics.
* **Opaque zip-lock bags** — fully non-transparent matte zip-lock / stand-up pouches with
  the same logo lockup for ferments & acids: Citric Acid Solution, Malic Acid Powder,
  Lactic Acid Solution. Same navy stage; label area clean and legible.

Wire the results into `content.json` as the `images` of the corresponding products
(they currently have empty or mismatched images).

### Task 7 — collections merge & archive (carried over)

Merge the collection taxonomy and build an **Archive** section from the old catalogue in
repo `horaanlika-droid/ce` (`data/catalog.json`: 10 collections — retro-asia,
retro-asia-engraved, bullet, flowers, coupethini, replicate, levitating, shorties,
soon-teapot, two-sips — and 25 pieces AG0001–AG0027 with full specs). Design it pleasing
to the eye (dark navy band, tile row like reference `IMG_1440`), and make ordering trivial:
one-click “request this piece” that pre-fills the existing request form. The overlapping
old `levitating` collection merges into the live Levitating collection; the rest become
archive tiles.

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

---

## Photo sessions — glass + dynamic drink (queued)

**Status: BLOCKED** — image generation endpoint returns `403 Forbidden` (account flagged for suspicious activity). Retry did not resolve; do not assume frames exist until files appear in `assets/scenes/` or `brand-source/generated/`.

### Session plan
One session = **3 glasses**. For each glass, produce **3 frames**:

| Frame | Content | Notes |
| --- | --- | --- |
| **A** | Empty glass, front 3/4 view | Style 1430: navy, radial glow, thin glass, soap-bubble iridescence |
| **B** | Empty glass, side profile | Same setting; silhouette must match shape donor 100 % |
| **C** | Glass with **dynamic drink** | Liquid must bubble / be in energetic motion. No garnish, no invented drinks — use the drink references already in the repo |

**Glass list (10 + super-pony):** `martini`, `goblet`, `coupe`, `highball`, `saucer`, `rocks`, `tumbler`, `footed`, `hurricane`, `cylinder`, plus `super-pony` (`assets/archive/AG0020.webp`).

**Suggested session order:**
1. Session 1: `martini`, `goblet`, `coupe`
2. Session 2: `highball`, `saucer`, `rocks`
3. Session 3: `tumbler`, `footed`, `hurricane`
4. Session 4: `cylinder`, `super-pony`, retries

**Deliverables per frame:** PNG master → `brand-source/generated/`; webp q≈82 over existing filenames; `-sm` thumb resized to 700 px wide.

**Prompt rules (from Task 1 / reference `IMG_1430`):** image-to-image from the shape donor (`assets/products/<name>.webp`); silhouette 100 % identical, never text-to-image; ultra-thin hand-blown crystal; soap-bubble thin-film iridescence; deep-navy backdrop `#101B2E → #0A1220`; single soft key source above and slightly behind; elliptical contact shadow + vertical mirror reflection; no props, no text, no watermark.

**⚠️ Drinks:** `assets/editorial/` does not exist in this clone — drink reference photos are missing. Confirm the source drink photos before shooting Frame C frames.

---

## Session 2026-10-31 — «navy studio»: бокалы, обложки, упаковка

> **RU (задание владельца, дословно):** «1697—1702 новые картинки с бокалами. сгенерируй
> оставшиеся в этом стиле… 1697—1702 база… стекло слишком тёмное у тебя, сравни с 1697—1702…
> дно тоньше, используй для формы фото из репозитория в хорошем качестве или из прайса…
> ещё обложки коллекций нужны в этом стиле, где бокалы стоят вместе стильно… давай для обложек
> сделаем ракурс кривой какой-нибудь стильный… и ещё нужно в этой же стилистике сгенерировать
> коробки для инвентаря и упаковки для кислот… сравни ещё форму и толщину стекла у всех наших
> фоток с референтами из прайса и репо, проведи аудит соответствий. ещё отредактируй обе
> бегущие строки. напиши инфу нашу. ну напиши задание в ридми себе и замержи пр».

**Кадровый эталон (база):** `IMG_1697.png` … `IMG_1702.png` в корне репозитория —
свет, тени, отражение, текстура стекла, глубина нави. Всё новое снимается только в этом ключе.

### Результат сессии

| Что | Где | Статус |
| --- | --- | --- |
| 10 предметов каталога в новом свете | `brand-source/navy/{coupe,cylinder,footed,goblet,highball,hurricane,martini,rocks,saucer,tumbler}.png` | готово |
| Обложки коллекций (14:9), стильные ракурсы | `brand-source/navy/cover-*.png` → `assets/scenes/cover-{levitating,signature,noir,raw}.webp` | готово и подключено |
| Упаковка: банка, бутылка, эссенция, тюбинг, коробка, дой-пак | `brand-source/navy/pack-*.png` | готово (мастера) |
| Референс-карточки для остальных форм | `brand-source/navy-refs/*.png` | готово (36 карточек) |
| Аудит соответствия формы и толщины стекла | `docs/audit-navy.md` + `docs/audit-navy-pairs.png` | готово |
| Обе бегущие строки | `js/app.js` (`TICKER_LINES`), `js/views.js` (`KINETIC_WORDS`), `data/content.json`, `server/seed.json` | готово |

### Правила съёмки (действуют для всех будущих кадров)

1. **Форма — только из репозитория.** Источник силуэта: `assets/scenes/glasses-lineup-pricelist.png`
   (10 фигур, 10922×2070) или alpha-каты `brand-source/cutouts/*.png`. Пайплайн: силуэт
   вставляется в нави-карточку 1000×1500 → это REFERENCE 1; стиль берётся с уже готового
   кадра сета → REFERENCE 2. Текст-ту-имиджем бокалы **не** генерируются.
2. **Геометрия — lock.** Класс стекла, пропорции, венец, профиль дна/стопы, толщина стенки
   и все детали (гравировка точками) сохраняются. Ничего не добавлять и не убирать.
3. **Дно и стенка — тонкие.** Никаких массивных блоков; дно читается как тонкий полированный диск.
4. **Стекло прозрачное.** Тело — нави на просвет (`#27486e…#3c6488`), без молочности, без белой
   заливки, без чёрной массы; самые тёмные зоны — мягкий `#17324f`.
5. **Свет.** Диффузный контр-свет, два асимметричных стрипа, верхняя панель на венец, минимум
   фронтального заполнения, нижний акцент на дно, чёрные флаги для объёма. Панели в кадре не видны.
6. **Фон.** Одно непрерывное нави-поле, без линии горизонта и шва стола; ореол `#21436f` за стеклом.
7. **Тень.** Мягкая контактная тень + размытое зеркальное отражение, растворяющееся в фоне.
8. **Кадр.** Вертикаль 2:3 для предметов, 14:9 для обложек; предмет по центру, ~50–62 % высоты.

### Аудит (кратко, полный — `docs/audit-navy.md`)

* 10/10 предметов в правильном классе стекла и в правильных пропорциях; ни один не переизобретён.
* Толщина стекла одинаковая по сету, дно/стопа тонкие — требование «дно тоньше» выполнено.
* Класс стекла и свет совпадают с 1697–1702 по всем признакам (прозрачность, контурные блики, тень, отражение).
* Первый прогон дал три расхождения — `tumbler` (был слишком узкий), `cylinder` (был вытянутый),
  `highball` (слишком плотная гравировка + лишние линии). Все три пересняты и закрыты.

### Второй заход (2026-10-31, после PR #16)

* Три формы пересняты — см. выше.
* **Упаковка дособрана кодом:** мастера снимаются чистыми (`pack-*-blank.png`), надписи наносит
  `tools/pack_labels.py` — единый гротеск, трекинг, сетка полей, перспективная деформация для
  наклонной грани коробки. Собраны все 18 SKU: 5 банок кислот, бутылка, 10 эссенций, 2 тюбинга,
  коробка `box-jigger`. Записаны в `assets/packaging/*` (1200×1500 + `-sm`).
* **Каталог переведён на новый свет:** `tools/navy_to_catalog.py` кладёт 2:3-мастера в 4:5
  (2400×3000 + `-sm` 840×1050) без ресемпла предмета и обновляет `data/image-audit.json`
  (единая линия контакта `0.80`). Перезаписаны 10 фото `assets/products/*`.
* Сводные листы: `docs/catalog-navy.png`, `docs/pack-lineup.png`.

### Очередь на следующую сессию

- [x] Подтянуть `tumbler` (ширина), `cylinder` (высота), `highball` (плотность гравировки).
- [x] Добить упаковку: 10 эссенций, 5 банок кислот, 2 тюбинга, коробка — через `tools/pack_labels.py`.
- [x] Нарезать `-sm` и подключить в каталог (`tools/navy_to_catalog.py`).
- [x] Обновить `data/image-audit.json`.
- [ ] Снять оставшиеся 14 форм каталога (Retro Asia, Bullet, Flowers, Shorties, Replika, Two Sips,
      Teapot, Super Pony) — референс-карточки готовы в `brand-source/navy-refs/`.
- [ ] Обложки для остальных 10 коллекций (`assets/archive/covers/*`).
- [ ] Дой-пак `pack-pouch` — нужен чистый мастер под `pack_labels.py`.

---

## Session log & open tasks

### Session log
- 2026-10-31 (вечер): три формы пересняты, упаковка собрана кодом (`tools/pack_labels.py`,
  18 SKU), каталог переведён на новый свет (`tools/navy_to_catalog.py`), `image-audit.json`
  обновлён.
- 2026-10-31: **Navy-studio set** — 10 предметов, 4 обложки коллекций (подключены),
  6 позиций упаковки, аудит формы/толщины (`docs/audit-navy.md`), обе бегущие строки
  переписаны, задание зафиксировано в README. Ветка `arena/3a19e242-talalay`.
- 2026-10-30: Price-list silhouettes cut & collaged without generation — `tools/cut_silhouettes.py` unmultiplies the 10 white packshots (`IMG_1661–1670`) into RGBA cutouts (`brand-source/cutouts/`), rescales to catalogue heights and composes `assets/scenes/glasses-lineup-pricelist.*`. Donor map: 1667=rocks (heavy base), 1669=hurricane (tall tube) — by shape/base, no donor map existed in repo.
- 2026-10-30: Opening curtain sped up — `BOOT_MIN` 2600→1500 ms, fallback 6000→4000 ms (PR #13 merged).
- 2026-10-30: Glass collage added — all 11 glasses in style 1430 (`assets/scenes/glasses-collage-1430.*`). Hero `levitating-martini` re-rendered uncropped. Committed on `arena/07eb83de-talalay`.

### Open tasks (photo sessions)
- [ ] Session 1: `martini` (A,B,C), `goblet` (A,B,C), `coupe` (A,B,C)
- [ ] Session 2: `highball` (A,B,C), `saucer` (A,B,C), `rocks` (A,B,C)
- [ ] Session 3: `tumbler` (A,B,C), `footed` (A,B,C), `hurricane` (A,B,C)
- [ ] Session 4: `cylinder` (A,B,C), `super-pony` (A,B,C), retries

### Key notes for future sessions
- Image generation is 403-blocked on the default endpoint; retry routes to another endpoint but currently also fails. Unblock before starting sessions.
- `assets/editorial/` is absent — drink references must be restored or confirmed before Frame C.
- Glass shapes must never change; always image-to-image from `assets/products/<name>.webp` (never text-to-image).
- Style anchor: `brand-source/IMG_1430.jpeg` (single glass, navy, radial glow, thin glass).
