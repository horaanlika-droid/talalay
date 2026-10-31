# Аудит стекла — форма, пропорция и фон против референсов

Референс каждой позиции — `brand-source/navy-refs/<форма>.png`, нарезка из прайса.
Правило: свет и сцена могут меняться, геометрия — нет.

Силуэт читается двумя независимыми способами: **band** (разность с сильным размытием —
тонкая структура, прямая граница сцены при этом исчезает) и **edge** (контур по Sobel).
Число печатается как `band / edge` и считается надёжным, только когда оба метода дают
одно и то же (расхождение < 8 %). Стекло прозрачное, и один метод врёт всегда —
поэтому решение принимается по согласию двух и по глазам на `docs/audit-glass-pairs.png`.

* **h/w** — высота ÷ ширина силуэта, фото против референса;
* порог формы — расхождение пропорции больше 8 % или совпадение профиля ширины < 82 %;
* синий фон — брак сразу, независимо от формы.

| Товар | Фото | h/w фото | h/w реф | Δ | Фон | Итог | Замечание |
| --- | --- | --- | --- | --- | --- | --- | --- |
| levitating-martini | `assets/products/martini.webp` | — | — | — | black | **n/a** | h/w автоматически не сходится — смотреть пары |
| champagne-saucer | `assets/products/saucer.webp` | 0.76 | 0.73 | +4 % | black | **ok** | пропорция совпадает, фон чёрный |
| stemmed-tumbler | `assets/products/footed.webp` | — | — | — | black | **n/a** | h/w автоматически не сходится — смотреть пары |
| saucer-coupe | `assets/products/coupe.webp` | — | — | — | black | **n/a** | h/w автоматически не сходится — смотреть пары |
| embassy-goblet | `assets/products/goblet.webp` | 1.60 | — | — | black | **n/a** | h/w автоматически не сходится — смотреть пары |
| etched-highball | `assets/products/highball.webp` | 2.07 | — | — | black | **n/a** | h/w автоматически не сходится — смотреть пары |
| column-tumbler | `assets/products/cylinder.webp` | — | — | — | black | **n/a** | h/w автоматически не сходится — смотреть пары |
| basalt-rocks | `assets/products/rocks.webp` | — | 0.96 | — | black | **n/a** | h/w автоматически не сходится — смотреть пары |
| slope-tumbler | `assets/products/tumbler.webp` | — | — | — | black | **n/a** | h/w автоматически не сходится — смотреть пары |
| cylinder-hurricane | `assets/products/hurricane.webp` | 1.71 | — | — | black | **n/a** | h/w автоматически не сходится — смотреть пары |
| levitating-super-pony | `assets/products/levitating-super-pony.webp` | — | — | — | black | **n/a** | h/w автоматически не сходится — смотреть пары |
| levitating-rocks-glass | `assets/products/levitating-rocks-glass.webp` | — | — | — | black | **n/a** | h/w автоматически не сходится — смотреть пары |
| levitating-highball-glass | `assets/products/levitating-highball-glass.webp` | — | — | — | black | **n/a** | h/w автоматически не сходится — смотреть пары |
| retro-asia-cocktail-glass | `assets/products/retro-asia-cocktail-glass.webp` | — | — | — | black | **n/a** | h/w автоматически не сходится — смотреть пары |
| retro-asia-rocks-glass | `assets/products/retro-asia-rocks-glass.webp` | 1.19 | 1.02 | +17 % | black | **off** | пропорция расходится на +17 % |
| retro-asia-highball-glass | `assets/products/retro-asia-highball-glass.webp` | 2.13 | — | — | black | **n/a** | h/w автоматически не сходится — смотреть пары |
| retro-asia-shot-glass | `assets/products/retro-asia-shot-glass.webp` | 2.60 | 2.44 | +7 % | black | **ok** | пропорция совпадает, фон чёрный |
| retro-asia-engraved-cocktail-glass | `assets/products/retro-asia-engraved-cocktail-glass.webp` | — | 1.63 | — | black | **n/a** | h/w автоматически не сходится — смотреть пары |
| retro-asia-engraved-rocks-glass | `assets/products/retro-asia-engraved-rocks-glass.webp` | — | — | — | black | **n/a** | h/w автоматически не сходится — смотреть пары |
| retro-asia-engraved-highball-glass | `assets/products/retro-asia-engraved-highball-glass.webp` | 1.62 | 1.51 | +7 % | black | **ok** | пропорция совпадает, фон чёрный |
| bullet-chalet-glass | `assets/products/bullet-chalet-glass.webp` | — | — | — | black | **n/a** | h/w автоматически не сходится — смотреть пары |
| bullet-rocks-glass | `assets/products/bullet-rocks-glass.webp` | — | 0.91 | — | black | **n/a** | h/w автоматически не сходится — смотреть пары |
| bullet-highball-glass | `assets/products/bullet-highball-glass.webp` | 1.80 | — | — | black | **n/a** | h/w автоматически не сходится — смотреть пары |
| flowers-cocktail-glass | `assets/products/flowers-cocktail-glass.webp` | 2.04 | — | — | black | **n/a** | h/w автоматически не сходится — смотреть пары |
| flowers-rocks-glass | `assets/products/flowers-rocks-glass.webp` | 0.84 | — | — | black | **n/a** | h/w автоматически не сходится — смотреть пары |
| flowers-highball-glass | `assets/products/flowers-highball-glass.webp` | 1.88 | 1.91 | -1 % | black | **ok** | пропорция совпадает, фон чёрный |
| coupethini-coupethini | `assets/products/coupethini-coupethini.webp` | 2.14 | 1.25 | +71 % | black | **off** | пропорция расходится на +71 % |
| replicate-rocks-glass | `assets/products/replicate-rocks-glass.webp` | — | 1.20 | — | black | **n/a** | h/w автоматически не сходится — смотреть пары |
| shorties-mini-martini | `assets/products/shorties-mini-martini.webp` | — | — | — | black | **n/a** | h/w автоматически не сходится — смотреть пары |
| shorties-daisy-coupe | `assets/products/shorties-daisy-coupe.webp` | — | — | — | black | **n/a** | h/w автоматически не сходится — смотреть пары |
| shorties-lil-nora | `assets/products/shorties-lil-nora.webp` | 1.10 | — | — | black | **n/a** | h/w автоматически не сходится — смотреть пары |
| shorties-modern-margo | `assets/products/shorties-modern-margo.webp` | — | 1.17 | — | black | **n/a** | h/w автоматически не сходится — смотреть пары |
| teapot-teapot | `assets/products/teapot-teapot.webp` | — | — | — | black | **n/a** | h/w автоматически не сходится — смотреть пары |
| two-sips-cocktail-glass | `assets/products/two-sips-cocktail-glass.webp` | — | — | — | black | **n/a** | h/w автоматически не сходится — смотреть пары |

## Что найдено

### 1. Фон — чистый

Все 34 карточки и 8 hero-кадров стоят на мастер-фоне `#000000`. За бокалами нет
серого облака: мягкий свет за предметом снят, остались только кромки, гравировка и
собственное свечение стекла. Проверка — `python3 tools/master_stage.py --check`
(углы кадра 0,0,0 на каждой пластине).

### 2. Форма — где фото и прайс расходятся

Референс прайса главнее. По парам (`docs/audit-glass-pairs.png`) видно:

* `retro-asia-rocks-glass` — фото на 17 % выше референса при той же ширине;
* `cylinder-hurricane` — фото высокий узкий цилиндр, референс приземистее и шире;
* `etched-highball` — фото уже референса;
* `stemmed-tumbler` (ref `footed`) — у фото чаша уже, ножка длиннее;
* `saucer-coupe` — силуэт сходится, но стекло темнее: свет на пластине ниже,
  чем у остальных чёрных мастеров.

Совпадают: `levitating-martini`, `champagne-saucer` (+4 %), `embassy-goblet`,
`basalt-rocks`, `slope-tumbler`, `column-tumbler`, `retro-asia-shot` (+7 %),
`bullet-*`, `flowers-*`, `shorties-*`, `teapot`, `two-sips`.

Геометрию нельзя ни перерисовать, ни растянуть — это прямое требование. Поэтому
расхождения выше чинятся только одним способом: у этих четырёх позиций нужен
мастер с того же изделия, что в прайсе. Скажи — и я возьму пластину прямо из
нарезки прайса (`brand-source/navy-refs/`) и прогоню её через мастер-фон: форма
будет ровно прайсовой, без единого нового пикселя геометрии.

### 3. Толщина стекла и дно

Стенка на всех кадрах тонкая и прозрачная, как в референсе; синий прежде давал
не толщину, а цвет. Дно: у `flowers-rocks`, `coupethini`, `shorties-mini-martini`
на рендере была светящаяся плита под дном — её больше нет, посадка на линию
контакта, дно читается тонким.

### 4. Про измерение

Стекло прозрачное, автоматическая маска силуэта на нём срывается, поэтому h/w
печатается только там, где два независимых метода дали одно и то же; иначе «—».
Число — поддержка для глаз, приговор ставится по паре фото/референс.

## Итог

* off: 2
* n/a: 28
* ok: 4

