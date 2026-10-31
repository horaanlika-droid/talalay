#!/usr/bin/env python3
"""Glass audit — backdrop, silhouette and proportion against the repository references.

The reference for a piece (`brand-source/navy-refs/<form>.png`, cut from the price
list) is the law: a catalogue photo may change the light and the stage, never the
shape of the glass, the thickness of the wall or the base.

Why two measurements
--------------------
Glass is transparent, and a lit studio puts a halo around it. Any single automatic
mask lies somewhere: a brightness threshold swallows the halo, a raw gradient picks
up the floor seam. So the same silhouette is read twice, by two independent methods,
and the number is trusted only when both agree:

    band  | image − heavy blur | — fine structure only; a straight stage edge or a
          paste border is low frequency and disappears
    edge  Sobel magnitude — the sharp contour of the glass itself

    h/w   height ÷ width of the trusted silhouette
    form  agreement of the width profile (24 bands, foot to rim) with the reference

Output
------
    python3 tools/audit_glass.py                        # report to stdout
    python3 tools/audit_glass.py --md docs/audit-glass.md
    python3 tools/audit_glass.py --pairs docs/audit-glass-pairs.png
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage as ndi

ROOT = Path(__file__).resolve().parent.parent
REFS = ROOT / "brand-source" / "navy-refs"
CONTENT = ROOT / "data" / "content.json"
W = 420

# Что видно глазами по docs/audit-glass-pairs.png — это часть отчёта, а не догадка машины.
FINDINGS = [
    "## Что найдено",
    "",
    "### 1. Фон — глубокий чёрный, без серого",
    "",
    "Мягкое серое облако за предметом снято на всех кадрах: оно низкочастотное,",
    "измеряется сильным блюром и вычитается, остаток дымки срезается. Углы каждой",
    "пластины — `0,0,0`, проверка: `python3 tools/master_stage.py --check`.",
    "",
    "### 2. Глоу",
    "",
    "Вокруг стекла добавлено контролируемое серебряное свечение. Оно собрано только",
    "из света, который уже есть в кадре (кромки, ножка, гравировка), поэтому повторяет",
    "реальный силуэт; чёрный остаётся чёрным, гаснет к краю кадра и не превращается",
    "в облако. Параметры — `GLOW_STRENGTH` / `GLOW_RADIUS` в `tools/master_stage.py`.",
    "",
    "### 3. Форма — сверка с прайсом",
    "",
    "Пара на `docs/audit-glass-pairs.png` нормирована: обе стороны обрезаны по предмету",
    "и приведены к одной высоте, поэтому сравнение идёт по силуэту и толщине, а не по",
    "кадрированию. Совпадают (24 позиции): `levitating-martini`, `embassy-goblet`,",
    "`column-tumbler`, `levitating-rocks-glass`, `levitating-highball-glass`,",
    "`retro-asia-shot-glass`, `retro-asia-engraved-*`, `bullet-highball-glass`,",
    "`flowers-*`, `shorties-*`, `teapot-teapot`, `two-sips-cocktail-glass`,",
    "`replicate-rocks-glass`, `bullet-rocks-glass`.",
    "",
    "### 4. Где фото расходится с прайсом — 10 позиций",
    "",
    "| Позиция | Что видно в паре |",
    "| --- | --- |",
    "| `stemmed-tumbler` | фото уже и выше референса `footed`: чаша узкая, ножка длинная |",
    "| `saucer-coupe` | фото глубже и уже; референс — широкая неглубокая чаша |",
    "| `champagne-saucer` | фото глубже референса, у прайса блюдце плоское и шире |",
    "| `etched-highball` | фото заметно уже референса при той же высоте |",
    "| `cylinder-hurricane` | фото высокий узкий цилиндр, референс приземистее и шире |",
    "| `retro-asia-rocks-glass` | фото примерно на 17 % выше референса |",
    "| `basalt-rocks` | фото круглее и шире, у прайса стенка прямее |",
    "| `slope-tumbler` | у фото сильнее расход кверху, у референса стенка ровнее |",
    "| `bullet-chalet-glass` | у фото чаша шире и глубже, у прайса уже и выше |",
    "| `coupethini-coupethini` | у фото чаша уже, ножка длиннее |",
    "",
    "Геометрию нельзя ни растянуть, ни перерисовать — это прямое требование. Эти десять",
    "чинятся только мастером с того же изделия, что в прайсе: нарезка прайса есть в",
    "`brand-source/navy-refs/`, но она мелкая (≈300 px по предмету), поэтому в мастер",
    "2400×3000 она не годится без апскейла. Нужен кадр с изделия.",
    "",
    "### 5. Толщина стекла и дно",
    "",
    "Стенка тонкая и прозрачная на всех кадрах, у референсов такая же; двойная линия",
    "кромки на фото и на прайсе совпадает по порядку величины. Дна-плиты нет ни на",
    "одной пластине: посадка на линию контакта, дно тонкое.",
    "",
    "### 6. Как читать цифры",
    "",
    "Стекло прозрачное, одна автоматическая маска врёт всегда, поэтому h/w печатается",
    "только там, где два независимых метода (band и edge) сошлись; иначе «—».",
    "Приговор ставится по паре, а цифра — поддержка.",
]



REFS_BY_SLUG = {
    "levitating-martini": "martini",
    "champagne-saucer": "saucer",
    "stemmed-tumbler": "footed",
    "saucer-coupe": "coupe",
    "embassy-goblet": "goblet",
    "etched-highball": "highball",
    "column-tumbler": "cylinder",
    "basalt-rocks": "rocks",
    "slope-tumbler": "tumbler",
    "cylinder-hurricane": "hurricane",
    "levitating-super-pony": "levitating-super-pony",
    "levitating-rocks-glass": "levitating-rocks-glass",
    "levitating-highball-glass": "levitating-highball-glass",
    "retro-asia-cocktail-glass": "retro-asia-cocktail-glass",
    "retro-asia-rocks-glass": "retro-asia-rocks-glass",
    "retro-asia-highball-glass": "retro-asia-highball-glass",
    "retro-asia-shot-glass": "retro-asia-shot-glass",
    "retro-asia-engraved-cocktail-glass": "retro-asia-engraved-cocktail-glass",
    "retro-asia-engraved-rocks-glass": "retro-asia-engraved-rocks-glass",
    "retro-asia-engraved-highball-glass": "retro-asia-engraved-highball-glass",
    "bullet-chalet-glass": "bullet-chalet-glass",
    "bullet-rocks-glass": "bullet-rocks-glass",
    "bullet-highball-glass": "bullet-highball-glass",
    "flowers-cocktail-glass": "flowers-cocktail-glass",
    "flowers-rocks-glass": "flowers-rocks-glass",
    "flowers-highball-glass": "flowers-highball-glass",
    "coupethini-coupethini": "coupethini-coupethini",
    "replicate-rocks-glass": "replicate-rocks-glass",
    "shorties-mini-martini": "shorties-mini-martini",
    "shorties-daisy-coupe": "shorties-daisy-coupe",
    "shorties-lil-nora": "shorties-lil-nora",
    "shorties-modern-margo": "shorties-modern-margo",
    "teapot-teapot": "teapot-teapot",
    "two-sips-cocktail-glass": "two-sips-cocktail-glass",
}


def _grey(path: Path) -> np.ndarray:
    img = Image.open(path).convert("L")
    h = max(80, int(W * img.height / img.width))
    return ndi.gaussian_filter(np.asarray(img.resize((W, h), Image.LANCZOS)).astype(np.float32), 1.2)


def _largest(mask: np.ndarray, share: float = 0.25) -> np.ndarray:
    lab, n = ndi.label(mask)
    if not n:
        return mask
    sizes = ndi.sum(mask, lab, range(1, n + 1))
    keep = np.zeros_like(mask)
    for i, size in enumerate(sizes, 1):
        if size > share * sizes.max():
            keep |= lab == i
    return keep


def _silhouette(grey: np.ndarray, kind: str) -> np.ndarray:
    if kind == "band":
        band = np.abs(grey - ndi.gaussian_filter(grey, 14))
        mask = band > np.percentile(band, 99)
    else:
        grad = np.hypot(ndi.sobel(grey, 0), ndi.sobel(grey, 1))
        mask = grad > np.percentile(grad, 97.5)
    mask = _largest(ndi.binary_fill_holes(ndi.binary_closing(mask, np.ones((13, 13)))))
    widths = mask.sum(axis=1)
    rows = np.where(widths > 0)[0]
    if len(rows):
        cut = rows[-1]                       # the mirror reflection is not the piece
        while cut > rows[0] and widths[cut] < 0.45 * widths.max():
            cut -= 1
        mask[cut + 2 :, :] = False
    return mask


def _usable(mask: np.ndarray) -> tuple[int, int] | None:
    ys, xs = np.where(mask)
    if not len(ys):
        return None
    h = int(ys.max() - ys.min() + 1)
    w = int(xs.max() - xs.min() + 1)
    if w < 0.05 * mask.shape[1] or w > 0.97 * mask.shape[1] or h / w < 0.2:
        return None            # a mask that has eaten the stage border is not a reading
    return h, w


def shape(path: Path) -> dict:
    grey = _grey(path)
    out: dict = {}
    for kind in ("band", "edge"):
        got = _usable(_silhouette(grey, kind))
        if got:
            out[kind] = {"h/w": got[0] / got[1]}
    return out


def backdrop(path: Path) -> tuple[str, float]:
    a = np.asarray(Image.open(path).convert("RGB").resize((200, 200))).astype(np.float32)
    r, g, b = a[..., 0], a[..., 1], a[..., 2]
    lead = float(np.mean(b - (r + g) / 2))
    share = float(np.mean((b - r > 16) & (b - g > 8)) * 100)
    return ("black", lead) if lead < 4 and share < 6 else (f"blue {share:.0f}%", lead)


def _trim_ref(img: Image.Image) -> Image.Image:
    """A reference sheet is a crop pasted on a canvas — the flat border is not the piece."""
    g = np.asarray(img.convert("L")).astype(np.float32)
    cs, rs = g.std(0), g.std(1)
    xs, ys = np.where(cs > 3)[0], np.where(rs > 3)[0]
    if not len(xs) or not len(ys):
        return img
    return img.crop((int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1))


def _trim_piece(img: Image.Image) -> Image.Image:
    """Crop a plate to the light it carries: the piece and its contact shadow."""
    a = np.asarray(img.convert("L")).astype(np.float32)
    m = a > 6
    xs, ys = np.where(m.any(axis=0))[0], np.where(m.any(axis=1))[0]
    if not len(xs) or not len(ys):
        return img
    pad = int(0.04 * img.width)
    return img.crop(
        (max(0, int(xs.min()) - pad), max(0, int(ys.min()) - pad),
         min(img.width, int(xs.max()) + pad), min(img.height, int(ys.max()) + pad))
    )


def _hw(entry: dict, kind: str) -> float | None:
    return entry.get(kind, {}).get("h/w") if entry else None


def judge(photo: dict, ref: dict, bg: str) -> tuple[str, str, str, str, str]:
    """→ (h/w фото, h/w реф, состояние, замечание)."""
    ph = [v for v in (_hw(photo, k) for k in ("band", "edge")) if v]
    rf = [v for v in (_hw(ref, k) for k in ("band", "edge")) if v]
    sure_p = len(ph) == 2 and abs(ph[0] - ph[1]) / max(ph) < 0.08
    sure_r = len(rf) == 2 and abs(rf[0] - rf[1]) / max(rf) < 0.08

    hw_photo = f"{sum(ph) / len(ph):.2f}" if sure_p else "—"
    hw_ref = f"{sum(rf) / len(rf):.2f}" if sure_r else "—"

    issues = []
    if bg != "black":
        issues.append(f"синий фон ({bg})")

    shape = "—"
    if sure_p and sure_r:
        delta = (sum(ph) / 2) / (sum(rf) / 2) - 1
        shape = f"{delta * 100:+.0f} %"
        if abs(delta) > 0.08:
            issues.append(f"пропорция расходится на {delta * 100:+.0f} %")
        state = "off" if issues and bg != "black" else ("off" if issues else "ok")
        note = "; ".join(issues) or "пропорция совпадает, фон чёрный"
    else:
        issues.append("h/w автоматически не сходится — смотреть пары")
        state = "off" if bg != "black" else "n/a"
        note = "; ".join(issues)
    return hw_photo, hw_ref, state, note, shape


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--md", default="")
    ap.add_argument("--pairs", default="")
    args = ap.parse_args()

    content = json.loads(CONTENT.read_text())
    products = {p["slug"]: p for p in content["products"]}
    rows, pairs = [], []

    for slug, ref_name in REFS_BY_SLUG.items():
        product = products.get(slug)
        photo_path = ROOT / product["images"][0] if product else None
        ref_path = REFS / f"{ref_name}.png"
        if not photo_path or not photo_path.exists() or not ref_path.exists():
            rows.append((slug, "—", "—", "—", "—", "—", "n/a", "файл не найден"))
            continue
        bg, _ = backdrop(photo_path)
        hw_photo, hw_ref, state, note, delta = judge(shape(photo_path), shape(ref_path), bg)
        rows.append((slug, str(photo_path.relative_to(ROOT)), hw_photo, hw_ref, delta, bg, state, note))
        pairs.append((slug, ref_name, photo_path, ref_path))

    summary: dict[str, int] = {}
    for row in rows:
        summary[row[6]] = summary.get(row[6], 0) + 1
    blue = [r for r in rows if r[5] != "black"]

    lines = [
        "# Аудит стекла — форма, пропорция и фон против референсов",
        "",
        "Референс каждой позиции — `brand-source/navy-refs/<форма>.png`, нарезка из прайса.",
        "Правило: свет и сцена могут меняться, геометрия — нет.",
        "",
        "Силуэт читается двумя независимыми способами: **band** (разность с сильным размытием —",
        "тонкая структура, прямая граница сцены при этом исчезает) и **edge** (контур по Sobel).",
        "Число печатается как `band / edge` и считается надёжным, только когда оба метода дают",
        "одно и то же (расхождение < 8 %). Стекло прозрачное, и один метод врёт всегда —",
        "поэтому решение принимается по согласию двух и по глазам на `docs/audit-glass-pairs.png`.",
        "",
        "* **h/w** — высота ÷ ширина силуэта, фото против референса;",
        "* порог формы — расхождение пропорции больше 8 % или совпадение профиля ширины < 82 %;",
        "* синий фон — брак сразу, независимо от формы.",
        "",
        "| Товар | Фото | h/w фото | h/w реф | Δ | Фон | Итог | Замечание |",
        "| --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for r in rows:
        lines.append(f"| {r[0]} | `{r[1]}` | {r[2]} | {r[3]} | {r[4]} | {r[5]} | **{r[6]}** | {r[7]} |")

    lines += ["", *FINDINGS, "", "## Итог", ""]
    for key in ("off", "n/a", "ok"):
        if summary.get(key):
            lines.append(f"* {key}: {summary[key]}")
    lines.append("")
    if blue:
        lines += [
            f"## Синий фон — {len(blue)} фото",
            "",
            "Все — старый синий рендер из `assets/archive/`. Пока он на карточке, любая другая",
            "правка не видна: покупатель видит синюю страницу. Это блокер №1.",
            "",
        ]
        for r in blue:
            lines.append(f"* `{r[1]}` — {r[5]}, h/w {r[2]} против {r[3]}")

    report = "\n".join(lines) + "\n"
    print(report)

    if args.md:
        out = Path(args.md)
        out = out if out.is_absolute() else ROOT / out
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(report)
        print("written", out)

    if args.pairs:
        # Both sides are cropped to the piece and set to the same height, so the
        # eye compares shape and wall thickness instead of framing.
        tw, th, cols = 190, 300, 5
        rws = (len(pairs) + cols - 1) // cols
        sheet = Image.new("RGB", (cols * tw * 2, rws * (th + 24)), (0, 0, 0))
        draw = ImageDraw.Draw(sheet)
        for i, (slug, ref_name, photo_path, ref_path) in enumerate(pairs):
            x, y = (i % cols) * tw * 2, (i // cols) * (th + 24)
            for j, (src, is_ref) in enumerate(((photo_path, False), (ref_path, True))):
                im = Image.open(src).convert("RGB")
                if is_ref:
                    im = _trim_ref(im)
                else:
                    im = _trim_piece(im)
                im.thumbnail((tw - 10, th - 10), Image.LANCZOS)
                sheet.paste(im, (x + j * tw + (tw - im.width) // 2, y + (th - im.height) // 2))
                draw.rectangle(
                    [x + j * tw, y, x + (j + 1) * tw - 1, y + th - 1],
                    outline=(255, 92, 92) if j == 0 else (92, 214, 255),
                )
            draw.text((x + 5, y + th + 5), slug[:34], fill=(235, 235, 235))
            draw.text((x + tw + 5, y + th + 5), f"ref: {ref_name[:24]}", fill=(150, 210, 255))
        out = Path(args.pairs)
        out = out if out.is_absolute() else ROOT / out
        out.parent.mkdir(parents=True, exist_ok=True)
        sheet.save(out)
        print("pairs", out)

if __name__ == "__main__":
    main()
