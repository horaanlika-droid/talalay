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

| Товар | Источник | Фото | h/w фото | h/w реф | Δ | Фон | Итог | Замечание |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| levitating-martini | фото | `assets/products/martini.webp` | — | — | — | black | **n/a** | h/w автоматически не сходится — смотреть пары |
| champagne-saucer | **прайс** | `assets/products/saucer.webp` | 0.75 | 0.73 | +2 % | black | **ok** | пропорция совпадает, фон чёрный |
| stemmed-tumbler | **прайс** | `assets/products/footed.webp` | — | — | — | black | **n/a** | h/w автоматически не сходится — смотреть пары |
| saucer-coupe | **прайс** | `assets/products/coupe.webp` | — | — | — | black | **n/a** | h/w автоматически не сходится — смотреть пары |
| embassy-goblet | **прайс** | `assets/products/goblet.webp` | 1.49 | — | — | black | **n/a** | h/w автоматически не сходится — смотреть пары |
| etched-highball | **прайс** | `assets/products/highball.webp` | — | — | — | black | **n/a** | h/w автоматически не сходится — смотреть пары |
| column-tumbler | **прайс** | `assets/products/cylinder.webp` | — | — | — | black | **n/a** | h/w автоматически не сходится — смотреть пары |
| basalt-rocks | **прайс** | `assets/products/rocks.webp` | 0.95 | 0.96 | -1 % | black | **ok** | пропорция совпадает, фон чёрный |
| slope-tumbler | **прайс** | `assets/products/tumbler.webp` | — | — | — | black | **n/a** | h/w автоматически не сходится — смотреть пары |
| cylinder-hurricane | **прайс** | `assets/products/hurricane.webp` | — | — | — | black | **n/a** | h/w автоматически не сходится — смотреть пары |
| levitating-super-pony | фото | `assets/products/levitating-super-pony.webp` | — | — | — | black | **n/a** | h/w автоматически не сходится — смотреть пары |
| levitating-rocks-glass | фото | `assets/products/levitating-rocks-glass.webp` | 1.06 | — | — | black | **n/a** | h/w автоматически не сходится — смотреть пары |
| levitating-highball-glass | фото | `assets/products/levitating-highball-glass.webp` | 2.88 | — | — | black | **n/a** | h/w автоматически не сходится — смотреть пары |
| retro-asia-cocktail-glass | фото | `assets/products/retro-asia-cocktail-glass.webp` | — | — | — | black | **n/a** | h/w автоматически не сходится — смотреть пары |
| retro-asia-rocks-glass | **прайс** | `assets/products/retro-asia-rocks-glass.webp` | 1.05 | 1.02 | +3 % | black | **ok** | пропорция совпадает, фон чёрный |
| retro-asia-highball-glass | фото | `assets/products/retro-asia-highball-glass.webp` | 2.20 | — | — | black | **n/a** | h/w автоматически не сходится — смотреть пары |
| retro-asia-shot-glass | фото | `assets/products/retro-asia-shot-glass.webp` | 2.49 | 2.44 | +2 % | black | **ok** | пропорция совпадает, фон чёрный |
| retro-asia-engraved-cocktail-glass | фото | `assets/products/retro-asia-engraved-cocktail-glass.webp` | — | 1.63 | — | black | **n/a** | h/w автоматически не сходится — смотреть пары |
| retro-asia-engraved-rocks-glass | фото | `assets/products/retro-asia-engraved-rocks-glass.webp` | 1.33 | — | — | black | **n/a** | h/w автоматически не сходится — смотреть пары |
| retro-asia-engraved-highball-glass | фото | `assets/products/retro-asia-engraved-highball-glass.webp` | 1.62 | 1.51 | +7 % | black | **ok** | пропорция совпадает, фон чёрный |
| bullet-chalet-glass | **прайс** | `assets/products/bullet-chalet-glass.webp` | — | — | — | black | **n/a** | h/w автоматически не сходится — смотреть пары |
| bullet-rocks-glass | фото | `assets/products/bullet-rocks-glass.webp` | — | 0.91 | — | black | **n/a** | h/w автоматически не сходится — смотреть пары |
| bullet-highball-glass | фото | `assets/products/bullet-highball-glass.webp` | 1.79 | — | — | black | **n/a** | h/w автоматически не сходится — смотреть пары |
| flowers-cocktail-glass | фото | `assets/products/flowers-cocktail-glass.webp` | 2.04 | — | — | black | **n/a** | h/w автоматически не сходится — смотреть пары |
| flowers-rocks-glass | фото | `assets/products/flowers-rocks-glass.webp` | 0.84 | — | — | black | **n/a** | h/w автоматически не сходится — смотреть пары |
| flowers-highball-glass | фото | `assets/products/flowers-highball-glass.webp` | 1.88 | 1.91 | -2 % | black | **ok** | пропорция совпадает, фон чёрный |
| coupethini-coupethini | **прайс** | `assets/products/coupethini-coupethini.webp` | — | 1.25 | — | black | **n/a** | h/w автоматически не сходится — смотреть пары |
| replicate-rocks-glass | фото | `assets/products/replicate-rocks-glass.webp` | — | 1.20 | — | black | **n/a** | h/w автоматически не сходится — смотреть пары |
| shorties-mini-martini | фото | `assets/products/shorties-mini-martini.webp` | — | — | — | black | **n/a** | h/w автоматически не сходится — смотреть пары |
| shorties-daisy-coupe | фото | `assets/products/shorties-daisy-coupe.webp` | — | — | — | black | **n/a** | h/w автоматически не сходится — смотреть пары |
| shorties-lil-nora | фото | `assets/products/shorties-lil-nora.webp` | — | — | — | black | **n/a** | h/w автоматически не сходится — смотреть пары |
| shorties-modern-margo | фото | `assets/products/shorties-modern-margo.webp` | — | 1.17 | — | black | **n/a** | h/w автоматически не сходится — смотреть пары |
| teapot-teapot | фото | `assets/products/teapot-teapot.webp` | — | — | — | black | **n/a** | h/w автоматически не сходится — смотреть пары |
| two-sips-cocktail-glass | фото | `assets/products/two-sips-cocktail-glass.webp` | — | — | — | black | **n/a** | h/w автоматически не сходится — смотреть пары |

## Что найдено

### 1. Фон — глубокий чёрный, без серого

Серое облако за предметом снято на всех кадрах, остаток дымки срезан: углы каждой
пластины `0,0,0`. Проверка — `python3 tools/master_stage.py --check`.

### 2. Форма — что было исправлено

Аудит показал двенадцать позиций, где кадр из архива был **другого бокала**, чем в прайсе.
Перерисовывать силуэт нельзя, поэтому у них взят сам прайс: нарезка
`brand-source/navy-refs/` — это наше же фото из прайс-листа, оно прогнано через
мастер-фон (`tools/masters_from_pricelist.py`). Форма, толщина стенки и дно теперь
буквально прайсовые:

`stemmed-tumbler` · `saucer-coupe` · `champagne-saucer` · `etched-highball` ·
`cylinder-hurricane` · `retro-asia-rocks-glass` · `basalt-rocks` · `slope-tumbler` ·
`bullet-chalet-glass` · `coupethini-coupethini` · `column-tumbler` · `embassy-goblet`

Что было не так: `stemmed-tumbler` стоял на высоком узком силуэте вместо низкой
стопы; `saucer-coupe` — на глубокой чаше вместо широкой; `champagne-saucer` — тоже
слишком глубокий; `etched-highball` — уже прайса; `cylinder-hurricane` — высокий
цилиндр вместо приземистого; `retro-asia-rocks` — на 17 % выше; `basalt-rocks`,
`slope-tumbler` и `bullet-chalet` — с другим наклоном стенки; `coupethini` — с более
узкой чашей и длинной ножкой; `column-tumbler` стоял тёмной колонной вместо
прозрачной стенки; `embassy-goblet` — с более широкой чашей, чем в прайсе.

### 3. Глоу

Серебряное свечение собрано только из света, который уже есть в кадре, поэтому
повторяет реальный силуэт и гаснет к краю; чёрный остаётся чёрным.

### 4. Кадр — все бокалы одного масштаба

Вторая ошибка была не в форме, а в кадре: мастера снимались в три захода, и предмет
стоял в рамке по-разному — от 43 % до 80 % высоты. В каталоге это читается как
«эти бокалы больше». Все пластины приведены к одному кадру: высота предмета 52,8 %
рамки, основание на 73,3 %, центр по 50,0 % — и только это масштабируется, силуэт
по-прежнему не тронут (`frame_piece()` в `tools/navy_to_catalog.py`).

Проверено 34 кадров: высота предмета 51.2–53.2 % рамки,
основание 72.8–73.7 %, центр 49.9–55.4 %.

### 5. Толщина стекла и дно

На позициях из прайса толщина стенки и дна — ровно прайсовые. На остальных кадрах
стенка тонкая и прозрачная, двойная линия кромки совпадает с референсом, плиты под
дном нет ни на одной пластине.

### 6. Как читать цифры

Стекло прозрачное, одна автоматическая маска врёт всегда, поэтому h/w печатается
только там, где два независимых метода сошлись; иначе «—». Приговор ставится по
паре на `docs/audit-glass-pairs.png`, цифра — поддержка.

## Итог

* n/a: 28
* ok: 6

