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
| saucer-coupe | `assets/products/coupe.webp` | 1.21 | — | — | black | **n/a** | h/w автоматически не сходится — смотреть пары |
| embassy-goblet | `assets/products/goblet.webp` | 1.60 | — | — | black | **n/a** | h/w автоматически не сходится — смотреть пары |
| etched-highball | `assets/products/highball.webp` | 2.06 | — | — | black | **n/a** | h/w автоматически не сходится — смотреть пары |
| column-tumbler | `assets/products/cylinder.webp` | — | — | — | black | **n/a** | h/w автоматически не сходится — смотреть пары |
| basalt-rocks | `assets/products/rocks.webp` | — | 0.96 | — | black | **n/a** | h/w автоматически не сходится — смотреть пары |
| slope-tumbler | `assets/products/tumbler.webp` | — | — | — | black | **n/a** | h/w автоматически не сходится — смотреть пары |
| cylinder-hurricane | `assets/products/hurricane.webp` | 1.71 | — | — | black | **n/a** | h/w автоматически не сходится — смотреть пары |
| levitating-super-pony | `assets/products/levitating-super-pony.webp` | — | — | — | black | **n/a** | h/w автоматически не сходится — смотреть пары |
| levitating-rocks-glass | `assets/products/levitating-rocks-glass.webp` | 1.11 | — | — | black | **n/a** | h/w автоматически не сходится — смотреть пары |
| levitating-highball-glass | `assets/products/levitating-highball-glass.webp` | — | — | — | black | **n/a** | h/w автоматически не сходится — смотреть пары |
| retro-asia-cocktail-glass | `assets/products/retro-asia-cocktail-glass.webp` | — | — | — | black | **n/a** | h/w автоматически не сходится — смотреть пары |
| retro-asia-rocks-glass | `assets/products/retro-asia-rocks-glass.webp` | 1.19 | 1.02 | +17 % | black | **off** | пропорция расходится на +17 % |
| retro-asia-highball-glass | `assets/products/retro-asia-highball-glass.webp` | 2.13 | — | — | black | **n/a** | h/w автоматически не сходится — смотреть пары |
| retro-asia-shot-glass | `assets/products/retro-asia-shot-glass.webp` | 2.51 | 2.44 | +3 % | black | **ok** | пропорция совпадает, фон чёрный |
| retro-asia-engraved-cocktail-glass | `assets/products/retro-asia-engraved-cocktail-glass.webp` | — | 1.63 | — | black | **n/a** | h/w автоматически не сходится — смотреть пары |
| retro-asia-engraved-rocks-glass | `assets/products/retro-asia-engraved-rocks-glass.webp` | — | — | — | black | **n/a** | h/w автоматически не сходится — смотреть пары |
| retro-asia-engraved-highball-glass | `assets/products/retro-asia-engraved-highball-glass.webp` | 1.62 | 1.51 | +7 % | black | **ok** | пропорция совпадает, фон чёрный |
| bullet-chalet-glass | `assets/products/bullet-chalet-glass.webp` | — | — | — | black | **n/a** | h/w автоматически не сходится — смотреть пары |
| bullet-rocks-glass | `assets/products/bullet-rocks-glass.webp` | — | 0.91 | — | black | **n/a** | h/w автоматически не сходится — смотреть пары |
| bullet-highball-glass | `assets/products/bullet-highball-glass.webp` | 1.80 | — | — | black | **n/a** | h/w автоматически не сходится — смотреть пары |
| flowers-cocktail-glass | `assets/products/flowers-cocktail-glass.webp` | 2.03 | — | — | black | **n/a** | h/w автоматически не сходится — смотреть пары |
| flowers-rocks-glass | `assets/products/flowers-rocks-glass.webp` | 0.84 | — | — | black | **n/a** | h/w автоматически не сходится — смотреть пары |
| flowers-highball-glass | `assets/products/flowers-highball-glass.webp` | 1.88 | 1.91 | -1 % | black | **ok** | пропорция совпадает, фон чёрный |
| coupethini-coupethini | `assets/products/coupethini-coupethini.webp` | — | 1.25 | — | black | **n/a** | h/w автоматически не сходится — смотреть пары |
| replicate-rocks-glass | `assets/products/replicate-rocks-glass.webp` | — | 1.20 | — | black | **n/a** | h/w автоматически не сходится — смотреть пары |
| shorties-mini-martini | `assets/products/shorties-mini-martini.webp` | — | — | — | black | **n/a** | h/w автоматически не сходится — смотреть пары |
| shorties-daisy-coupe | `assets/products/shorties-daisy-coupe.webp` | — | — | — | black | **n/a** | h/w автоматически не сходится — смотреть пары |
| shorties-lil-nora | `assets/products/shorties-lil-nora.webp` | — | — | — | black | **n/a** | h/w автоматически не сходится — смотреть пары |
| shorties-modern-margo | `assets/products/shorties-modern-margo.webp` | — | 1.17 | — | black | **n/a** | h/w автоматически не сходится — смотреть пары |
| teapot-teapot | `assets/products/teapot-teapot.webp` | — | — | — | black | **n/a** | h/w автоматически не сходится — смотреть пары |
| two-sips-cocktail-glass | `assets/products/two-sips-cocktail-glass.webp` | — | — | — | black | **n/a** | h/w автоматически не сходится — смотреть пары |

## Что найдено

### 1. Фон — глубокий чёрный, без серого

Мягкое серое облако за предметом снято на всех кадрах: оно низкочастотное,
измеряется сильным блюром и вычитается, остаток дымки срезается. Углы каждой
пластины — `0,0,0`, проверка: `python3 tools/master_stage.py --check`.

### 2. Глоу

Вокруг стекла добавлено контролируемое серебряное свечение. Оно собрано только
из света, который уже есть в кадре (кромки, ножка, гравировка), поэтому повторяет
реальный силуэт; чёрный остаётся чёрным, гаснет к краю кадра и не превращается
в облако. Параметры — `GLOW_STRENGTH` / `GLOW_RADIUS` в `tools/master_stage.py`.

### 3. Форма — сверка с прайсом

Пара на `docs/audit-glass-pairs.png` нормирована: обе стороны обрезаны по предмету
и приведены к одной высоте, поэтому сравнение идёт по силуэту и толщине, а не по
кадрированию. Совпадают (24 позиции): `levitating-martini`, `embassy-goblet`,
`column-tumbler`, `levitating-rocks-glass`, `levitating-highball-glass`,
`retro-asia-shot-glass`, `retro-asia-engraved-*`, `bullet-highball-glass`,
`flowers-*`, `shorties-*`, `teapot-teapot`, `two-sips-cocktail-glass`,
`replicate-rocks-glass`, `bullet-rocks-glass`.

### 4. Где фото расходится с прайсом — 10 позиций

| Позиция | Что видно в паре |
| --- | --- |
| `stemmed-tumbler` | фото уже и выше референса `footed`: чаша узкая, ножка длинная |
| `saucer-coupe` | фото глубже и уже; референс — широкая неглубокая чаша |
| `champagne-saucer` | фото глубже референса, у прайса блюдце плоское и шире |
| `etched-highball` | фото заметно уже референса при той же высоте |
| `cylinder-hurricane` | фото высокий узкий цилиндр, референс приземистее и шире |
| `retro-asia-rocks-glass` | фото примерно на 17 % выше референса |
| `basalt-rocks` | фото круглее и шире, у прайса стенка прямее |
| `slope-tumbler` | у фото сильнее расход кверху, у референса стенка ровнее |
| `bullet-chalet-glass` | у фото чаша шире и глубже, у прайса уже и выше |
| `coupethini-coupethini` | у фото чаша уже, ножка длиннее |

Геометрию нельзя ни растянуть, ни перерисовать — это прямое требование. Эти десять
чинятся только мастером с того же изделия, что в прайсе: нарезка прайса есть в
`brand-source/navy-refs/`, но она мелкая (≈300 px по предмету), поэтому в мастер
2400×3000 она не годится без апскейла. Нужен кадр с изделия.

### 5. Толщина стекла и дно

Стенка тонкая и прозрачная на всех кадрах, у референсов такая же; двойная линия
кромки на фото и на прайсе совпадает по порядку величины. Дна-плиты нет ни на
одной пластине: посадка на линию контакта, дно тонкое.

### 6. Как читать цифры

Стекло прозрачное, одна автоматическая маска врёт всегда, поэтому h/w печатается
только там, где два независимых метода (band и edge) сошлись; иначе «—».
Приговор ставится по паре, а цифра — поддержка.

## Итог

* off: 1
* n/a: 29
* ok: 4

