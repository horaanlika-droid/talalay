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
| champagne-saucer | `assets/products/saucer.webp` | — | 0.73 | — | black | **n/a** | h/w автоматически не сходится — смотреть пары |
| stemmed-tumbler | `assets/products/footed.webp` | — | — | — | black | **n/a** | h/w автоматически не сходится — смотреть пары |
| saucer-coupe | `assets/products/coupe.webp` | — | — | — | black | **n/a** | h/w автоматически не сходится — смотреть пары |
| embassy-goblet | `assets/products/goblet.webp` | 1.61 | — | — | black | **n/a** | h/w автоматически не сходится — смотреть пары |
| etched-highball | `assets/products/highball.webp` | — | — | — | black | **n/a** | h/w автоматически не сходится — смотреть пары |
| column-tumbler | `assets/products/cylinder.webp` | — | — | — | black | **n/a** | h/w автоматически не сходится — смотреть пары |
| basalt-rocks | `assets/products/rocks.webp` | — | 0.96 | — | black | **n/a** | h/w автоматически не сходится — смотреть пары |
| slope-tumbler | `assets/products/tumbler.webp` | — | — | — | black | **n/a** | h/w автоматически не сходится — смотреть пары |
| cylinder-hurricane | `assets/products/hurricane.webp` | 1.72 | — | — | black | **n/a** | h/w автоматически не сходится — смотреть пары |
| levitating-super-pony | `assets/archive/AG0020.webp` | — | — | — | blue 100% | **off** | синий фон (blue 100%); h/w автоматически не сходится — смотреть пары |
| levitating-rocks-glass | `assets/archive/AG0021.webp` | — | — | — | blue 100% | **off** | синий фон (blue 100%); h/w автоматически не сходится — смотреть пары |
| levitating-highball-glass | `assets/archive/AG0022.webp` | 2.87 | — | — | blue 100% | **off** | синий фон (blue 100%); h/w автоматически не сходится — смотреть пары |
| retro-asia-cocktail-glass | `assets/archive/AG0015.webp` | 1.92 | — | — | blue 100% | **off** | синий фон (blue 100%); h/w автоматически не сходится — смотреть пары |
| retro-asia-rocks-glass | `assets/archive/AG0016.webp` | 1.00 | 1.02 | -2 % | blue 100% | **off** | синий фон (blue 100%) |
| retro-asia-highball-glass | `assets/archive/AG0017.webp` | 1.45 | — | — | blue 100% | **off** | синий фон (blue 100%); h/w автоматически не сходится — смотреть пары |
| retro-asia-shot-glass | `assets/archive/AG0018.webp` | — | 2.44 | — | blue 100% | **off** | синий фон (blue 100%); h/w автоматически не сходится — смотреть пары |
| retro-asia-engraved-cocktail-glass | `assets/archive/AG0011.webp` | — | 1.63 | — | blue 100% | **off** | синий фон (blue 100%); h/w автоматически не сходится — смотреть пары |
| retro-asia-engraved-rocks-glass | `assets/archive/AG0012.webp` | 1.16 | — | — | blue 100% | **off** | синий фон (blue 100%); h/w автоматически не сходится — смотреть пары |
| retro-asia-engraved-highball-glass | `assets/archive/AG0013.webp` | — | 1.51 | — | blue 100% | **off** | синий фон (blue 100%); h/w автоматически не сходится — смотреть пары |
| bullet-chalet-glass | `assets/archive/AG0008.webp` | — | — | — | blue 100% | **off** | синий фон (blue 100%); h/w автоматически не сходится — смотреть пары |
| bullet-rocks-glass | `assets/archive/AG0010.webp` | 0.89 | 0.91 | -2 % | blue 100% | **off** | синий фон (blue 100%) |
| bullet-highball-glass | `assets/archive/AG0009.webp` | 1.77 | — | — | blue 100% | **off** | синий фон (blue 100%); h/w автоматически не сходится — смотреть пары |
| flowers-cocktail-glass | `assets/archive/AG0002.webp` | 2.03 | — | — | blue 100% | **off** | синий фон (blue 100%); h/w автоматически не сходится — смотреть пары |
| flowers-rocks-glass | `assets/archive/AG0003.webp` | 0.83 | — | — | blue 100% | **off** | синий фон (blue 100%); h/w автоматически не сходится — смотреть пары |
| flowers-highball-glass | `assets/archive/AG0001.webp` | 1.90 | 1.91 | -1 % | blue 100% | **off** | синий фон (blue 100%) |
| coupethini-coupethini | `assets/archive/AG0006.webp` | 2.15 | 1.25 | +71 % | blue 100% | **off** | синий фон (blue 100%); пропорция расходится на +71 % |
| replicate-rocks-glass | `assets/archive/AG0004.webp` | — | 1.20 | — | blue 100% | **off** | синий фон (blue 100%); h/w автоматически не сходится — смотреть пары |
| shorties-mini-martini | `assets/archive/AG0023.webp` | — | — | — | blue 100% | **off** | синий фон (blue 100%); h/w автоматически не сходится — смотреть пары |
| shorties-daisy-coupe | `assets/archive/AG0024.webp` | — | — | — | blue 100% | **off** | синий фон (blue 100%); h/w автоматически не сходится — смотреть пары |
| shorties-lil-nora | `assets/archive/AG0026.webp` | — | — | — | blue 100% | **off** | синий фон (blue 100%); h/w автоматически не сходится — смотреть пары |
| shorties-modern-margo | `assets/archive/AG0025.webp` | 1.21 | 1.17 | +3 % | blue 100% | **off** | синий фон (blue 100%) |
| teapot-teapot | `assets/archive/AG0027.webp` | — | — | — | blue 100% | **off** | синий фон (blue 100%); h/w автоматически не сходится — смотреть пары |
| two-sips-cocktail-glass | `assets/archive/AG0019.webp` | — | — | — | blue 100% | **off** | синий фон (blue 100%); h/w автоматически не сходится — смотреть пары |

## Что найдено

### 1. Синий фон — блокер

24 из 34 фото — старый синий рендер (`assets/archive/AG0001…AG0027`). Пока он стоит на
карточке, всё остальное не видно. Кроме товаров синие и сцены:
`assets/scenes/hero-levitating-super-pony.webp`, `hero-levitating-super-pony-portrait.webp`,
`hero-levitating-martini-portrait.webp`, `cover-signature.webp`, `banner-levitating.webp`,
`assets/archive/covers/*`.

### 2. Стенка

У синих рендеров стенка тонкая и прозрачная — как в референсе. Вред наносит не она, а
синий ореол под стеклом. При переводе на чёрный ореол убирается, стенка не утолщается:
меняется только то, что видно **сквозь** стекло (синий → угольный), контур и толщина
остаются на месте.

### 3. Дно

`flowers-rocks-glass` (AG0003), `coupethini-coupethini` (AG0006) и `shorties-mini-martini`
(AG0023) на рендере стоят на светящейся толстой плите, а референс даёт тонкое дно.
Это ровно та «массивная база», которой быть не должно: свечение под дном убрать, само дно
оставить тонким, посадка — на линию контакта, без левитации.

### 4. Форма — расхождения, которые видно без измерений

* `cylinder-hurricane` — на фото высокий узкий цилиндр, референс даёт приземистый широкий;
* `etched-highball` — фото заметно уже референса;
* `stemmed-tumbler` (ref `footed`) — фото уже, чаша у референса шире, ножка короче;
* `saucer-coupe` — фото темнее референса: стекло читается почти чёрным, свет ниже нормы
  (это свет, а не геометрия, но на чёрном фоне разница видна сильнее всего).

Совпадают по силуэту: `levitating-martini`, `embassy-goblet`, `basalt-rocks`,
`champagne-saucer`, `slope-tumbler`, `column-tumbler`, `retro-asia-*`, `bullet-*`,
`flowers-cocktail/highball`, `shorties-*`, `teapot`, `two-sips`.

### 5. Про измерение

Стекло прозрачное: автоматическая маска силуэта на нём срывается, поэтому h/w печатается
только когда оба метода дали одно и то же, иначе стоит «—». Число здесь — поддержка для
глаз, а не приговор. Приговор по сильному признаку: синий фон и расхождение пропорции
больше 8 % там, где оба метода сошлись.

### 6. Порядок исправления

1. Переложить 24 синих фото и 6 синих сцен на чёрный (замена фона, геометрия не трогается).
2. У AG0003 / AG0006 / AG0023 убрать плиту под дном и левитацию, поставить на линию контакта.
3. Выправить `cylinder-hurricane`, `etched-highball`, `stemmed-tumbler` по референсу.
4. Поднять свет на `saucer-coupe` до уровня остальных десяти чёрных пластин.
5. Перегнать аудит: цель — 0 синих, Δ ≤ 8 % у всех, у кого число считается.

## Итог

* off: 24
* n/a: 10

## Синий фон — 24 фото

Все — старый синий рендер из `assets/archive/`. Пока он на карточке, любая другая
правка не видна: покупатель видит синюю страницу. Это блокер №1.

* `assets/archive/AG0020.webp` — blue 100%, h/w — против —
* `assets/archive/AG0021.webp` — blue 100%, h/w — против —
* `assets/archive/AG0022.webp` — blue 100%, h/w 2.87 против —
* `assets/archive/AG0015.webp` — blue 100%, h/w 1.92 против —
* `assets/archive/AG0016.webp` — blue 100%, h/w 1.00 против 1.02
* `assets/archive/AG0017.webp` — blue 100%, h/w 1.45 против —
* `assets/archive/AG0018.webp` — blue 100%, h/w — против 2.44
* `assets/archive/AG0011.webp` — blue 100%, h/w — против 1.63
* `assets/archive/AG0012.webp` — blue 100%, h/w 1.16 против —
* `assets/archive/AG0013.webp` — blue 100%, h/w — против 1.51
* `assets/archive/AG0008.webp` — blue 100%, h/w — против —
* `assets/archive/AG0010.webp` — blue 100%, h/w 0.89 против 0.91
* `assets/archive/AG0009.webp` — blue 100%, h/w 1.77 против —
* `assets/archive/AG0002.webp` — blue 100%, h/w 2.03 против —
* `assets/archive/AG0003.webp` — blue 100%, h/w 0.83 против —
* `assets/archive/AG0001.webp` — blue 100%, h/w 1.90 против 1.91
* `assets/archive/AG0006.webp` — blue 100%, h/w 2.15 против 1.25
* `assets/archive/AG0004.webp` — blue 100%, h/w — против 1.20
* `assets/archive/AG0023.webp` — blue 100%, h/w — против —
* `assets/archive/AG0024.webp` — blue 100%, h/w — против —
* `assets/archive/AG0026.webp` — blue 100%, h/w — против —
* `assets/archive/AG0025.webp` — blue 100%, h/w 1.21 против 1.17
* `assets/archive/AG0027.webp` — blue 100%, h/w — против —
* `assets/archive/AG0019.webp` — blue 100%, h/w — против —
