#!/usr/bin/env python3
"""Cocktail Embassy — studio masters into the catalogue.

`brand-source/black/*.png` (deep-black stage) and `brand-source/navy/*.png`
(earlier navy stage) are 2:3 studio plates; the black one wins when both exist.
The storefront wants 4:5 (2400×3000 masters, 840×1050 thumbs), so the plate is
re-framed by extending the smooth backdrop sideways — the piece is never
resampled, cropped or moved.

    python3 tools/navy_to_catalog.py            # write assets/products/*
    python3 tools/navy_to_catalog.py --preview  # contact sheet only

Also refreshes `data/image-audit.json` (contact line of every plate).
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parent.parent
NAVY = ROOT / "brand-source" / "navy"
BLACK = ROOT / "brand-source" / "black"
OUT = ROOT / "assets" / "products"
AUDIT = ROOT / "data" / "image-audit.json"

MASTER = (2400, 3000)
THUMB = (840, 1050)
CONTACT_Y = 0.80                     # base line of every plate, navy or black


def master_for(name: str) -> Path:
    """Deep-black plate wins; the navy plate is the fallback until it is re-staged."""
    black = BLACK / f"{name}.png"
    return black if black.exists() else NAVY / f"{name}.png"

# product photo  →  navy master
MAP = {
    # core ten
    "martini": "martini",
    "saucer": "saucer",
    "footed": "footed",
    "coupe": "coupe",
    "goblet": "goblet",
    "highball": "highball",
    "cylinder": "cylinder",
    "rocks": "rocks",
    "tumbler": "tumbler",
    "hurricane": "hurricane",
    # archive shapes, second pass (2026-10-31)
    "retro-asia-cocktail-glass": "retro-asia-cocktail",
    "retro-asia-rocks-glass": "retro-asia-rocks",
    "retro-asia-highball-glass": "retro-asia-highball",
    "retro-asia-shot-glass": "retro-asia-shot",
    "retro-asia-engraved-cocktail-glass": "retro-asia-engraved-cocktail",
    "retro-asia-engraved-rocks-glass": "retro-asia-engraved-rocks",
    "retro-asia-engraved-highball-glass": "retro-asia-engraved-highball",
    "bullet-rocks-glass": "bullet-rocks",
    # third pass: the archive renders staged on the master black
    "flowers-cocktail-glass": "flowers-cocktail",
    "flowers-rocks-glass": "flowers-rocks",
    "flowers-highball-glass": "flowers-highball",
    "coupethini-coupethini": "coupethini",
    "replicate-rocks-glass": "replicate-rocks",
    "shorties-mini-martini": "shorties-mini-martini",
    "shorties-daisy-coupe": "shorties-daisy-coupe",
    "shorties-modern-margo": "shorties-modern-margo",
    "shorties-lil-nora": "shorties-lil-nora",
    "teapot-teapot": "teapot",
    "two-sips-cocktail-glass": "two-sips",
    "bullet-chalet-glass": "bullet-chalet",
    "bullet-highball-glass": "bullet-highball",
    "levitating-super-pony": "levitating-super-pony",
    "levitating-rocks-glass": "levitating-rocks",
    "levitating-highball-glass": "levitating-highball",
}


def to_4x5(img: Image.Image, size=MASTER) -> Image.Image:
    w, h = size
    scale = h / img.height
    core = img.resize((max(1, int(round(img.width * scale))), h), Image.LANCZOS)
    if core.width >= w:
        left = (core.width - w) // 2
        return core.crop((left, 0, left + w, h))
    # the stage is a flat master black now, so the frame is widened with it: no
    # stretched edge column, no seam where the old plate ended, and the last
    # pixels of the plate feather into the same black the page uses
    canvas = Image.new("RGB", size, (0, 0, 0))
    pad = w - core.width
    feather = min(80, max(16, core.width // 24))
    ramp = [1.0] * (core.width - 2 * feather) + [0.0] * feather
    alpha = ramp[:feather][::-1] + ramp
    alpha = (alpha + [0.0] * (core.width - len(alpha)))[: core.width]
    mask = Image.new("L", (core.width, h))
    mask.putdata([int(v * 255) for v in alpha] * h)
    canvas.paste(core, (pad // 2, 0), mask)
    return canvas


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--preview", action="store_true")
    args = ap.parse_args()

    audit = json.loads(AUDIT.read_text())
    thumbs = []
    for name, master in MAP.items():
        source = master_for(master)
        img = Image.open(source).convert("RGB")
        plate = to_4x5(img)
        if not args.preview:
            plate.save(OUT / f"{name}.webp", "WEBP", quality=88, method=6)
            plate.resize(THUMB, Image.LANCZOS).save(
                OUT / f"{name}-sm.webp", "WEBP", quality=85, method=6
            )
            audit["products"][f"{name}.webp"] = CONTACT_Y
        thumbs.append((name, plate.resize((240, 300), Image.LANCZOS)))
        print(("preview " if args.preview else "wrote   ") + f"{name}.webp")

    audit["updatedAt"] = "2026-10-31"
    audit["_comment"] = (
        "Contact line of every catalogue photo, as a fraction of image height. "
        "Every plate (navy studio, then deep-black stage) shares one base line "
        "at 0.80; below it is the studio floor, contact shadow and reflection."
    )
    if not args.preview:
        AUDIT.write_text(json.dumps(audit, indent=2, ensure_ascii=False) + "\n")

    cols = 5
    rows = (len(thumbs) + cols - 1) // cols
    sheet = Image.new("RGB", (cols * 250, rows * 330), (8, 10, 16))
    d = ImageDraw.Draw(sheet)
    for i, (name, t) in enumerate(thumbs):
        x, y = (i % cols) * 250, (i // cols) * 330
        sheet.paste(t, (x + 5, y + 5))
        d.text((x + 8, y + 312), name, fill=(235, 235, 235))
    target = Path("/tmp") / "navy-catalog.png" if args.preview else ROOT / "docs" / "catalog-navy.png"
    target.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(target)
    print("sheet  ", target)


if __name__ == "__main__":
    main()
