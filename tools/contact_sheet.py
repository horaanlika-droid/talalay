#!/usr/bin/env python3
"""Cocktail Embassy — QC contact sheets.

Generates need to be judged as a *set*: one backdrop tone, one scale, one light,
one glass thickness. This tool lays a folder of photographs out on the shared
room tone (rgb 7,12,24) with a label and a 100 % crop of the base, so the
owner (and the next session) can see at a glance which pieces still have a
thick base, a thick wall or an off-tone backdrop.

    python3 tools/contact_sheet.py                                   # all sets
    python3 tools/contact_sheet.py --set drinks --out /tmp/drinks.png
    python3 tools/contact_sheet.py --set products --cols 5 --cell 420
    python3 tools/contact_sheet.py --set drinks --only goblet --full   # no crop
"""
from __future__ import annotations

import argparse
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent
ASSETS = ROOT / "assets"
BG = (7, 12, 24)          # the app background = the photography backdrop
FG = (238, 243, 251)
MUTED = (140, 158, 182)


def files_of(which: str) -> list[Path]:
    out: list[Path] = []
    if which in ("products", "all"):
        out += sorted(p for p in (ASSETS / "products").glob("*.webp") if "-sm" not in p.name)
    if which in ("drinks", "all"):
        out += sorted(p for p in (ASSETS / "drinks").rglob("*.webp") if "-sm" not in p.name)
    if which in ("editorial", "all"):
        out += sorted(p for p in (ASSETS / "editorial").glob("*.webp")
                      if "-sm" not in p.name and "mesh" not in p.name)
    if which in ("archive", "all"):
        out += sorted(p for p in (ASSETS / "archive").glob("*.webp")
                      if "-sm" not in p.name and "card" not in p.name)
    return out


def font(size: int):
    for name in ("DejaVuSansMono.ttf", "DejaVuSans.ttf"):
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            continue
    return ImageFont.load_default()


def label(draw: ImageDraw.ImageDraw, xy: tuple[int, int], text: str, size: int, fill=FG):
    draw.text(xy, text, font=font(size), fill=fill)


def sheet(paths: list[Path], cols: int, cell: int, show_base: bool) -> Image.Image:
    rows = (len(paths) + cols - 1) // cols
    pad, cap = 12, 46
    W = cols * cell + pad * (cols + 1)
    H = rows * (cell + cap) + pad * (rows + 1)
    canvas = Image.new("RGB", (W, H), BG)
    draw = ImageDraw.Draw(canvas)

    for i, p in enumerate(paths):
        im = Image.open(p).convert("RGB")
        thumb = im.copy()
        thumb.thumbnail((cell, cell), Image.LANCZOS)
        x = pad + (i % cols) * (cell + pad)
        y = pad + (i // cols) * (cell + cap + pad)
        tile = Image.new("RGB", (cell, cell), BG)
        tile.paste(thumb, ((cell - thumb.width) // 2, (cell - thumb.height) // 2))
        canvas.paste(tile, (x, y))

        if show_base:
            # 100 % crop of the lower half: the base is where thick glass shows
            crop_h = im.height // 3
            crop = im.crop((0, im.height - crop_h, im.width, im.height))
            crop.thumbnail((cell, cell // 2), Image.LANCZOS)
            canvas.paste(crop, (x, y + cell - crop.height))

        label(draw, (x, y + cell + 8), p.name.rsplit(".", 1)[0], 15)
        label(draw, (x + 4, y + 6), str(i + 1), 15, MUTED)
    return canvas


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--set", default="all",
                    choices=["products", "drinks", "editorial", "archive", "all"])
    ap.add_argument("--only", default="", help="substring filter on filenames")
    ap.add_argument("--cols", type=int, default=5)
    ap.add_argument("--cell", type=int, default=360)
    ap.add_argument("--full", action="store_true", help="no base crop (plain grid)")
    ap.add_argument("--out", default="")
    args = ap.parse_args()

    paths = files_of(args.set)
    if args.only:
        paths = [p for p in paths if args.only in p.name]
    if not paths:
        raise SystemExit("no images for that set")

    img = sheet(paths, max(1, args.cols), args.cell, not args.full)
    out = Path(args.out) if args.out else ROOT / "brand-source" / "qc" / f"sheet-{args.set}.png"
    out.parent.mkdir(parents=True, exist_ok=True)
    img.save(out)
    print(f"{len(paths)} images → {out}  ({img.width}x{img.height})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
