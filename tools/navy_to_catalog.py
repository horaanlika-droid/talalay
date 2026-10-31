#!/usr/bin/env python3
"""Cocktail Embassy — navy masters into the catalogue.

`brand-source/navy/*.png` are 2:3 studio plates shot in the 1697-1702 style.
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
SRC = ROOT / "brand-source" / "navy"
OUT = ROOT / "assets" / "products"
AUDIT = ROOT / "data" / "image-audit.json"

MASTER = (2400, 3000)
THUMB = (840, 1050)
CONTACT_Y = 0.80                     # base line of every navy plate

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
}


def to_4x5(img: Image.Image, size=MASTER) -> Image.Image:
    w, h = size
    scale = h / img.height
    core = img.resize((max(1, int(round(img.width * scale))), h), Image.LANCZOS)
    if core.width >= w:
        left = (core.width - w) // 2
        return core.crop((left, 0, left + w, h))
    canvas = Image.new("RGB", size)
    pad = w - core.width
    canvas.paste(core, (pad // 2, 0))
    # the backdrop is a smooth vertical gradient: stretch its edge columns out
    left = core.crop((0, 0, 1, h)).resize((pad // 2 + 1, h), Image.BILINEAR)
    right = core.crop((core.width - 1, 0, core.width, h)).resize(
        (pad - pad // 2 + 1, h), Image.BILINEAR
    )
    canvas.paste(left, (0, 0))
    canvas.paste(right, (w - right.width, 0))
    return canvas


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--preview", action="store_true")
    args = ap.parse_args()

    audit = json.loads(AUDIT.read_text())
    thumbs = []
    for name, master in MAP.items():
        img = Image.open(SRC / f"{master}.png").convert("RGB")
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
        "The navy-studio plates (2026-10-31) all share one base line at 0.80; "
        "below it is the studio floor, contact shadow and mirror reflection."
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
