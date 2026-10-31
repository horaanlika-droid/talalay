#!/usr/bin/env python3
"""Cocktail Embassy — one master stage for every plate.

The catalogue is not a set of cut-outs. Every photograph is a full frame with the
glass standing on the same stage, and that stage is the colour of the app itself,
so a plate can be dropped anywhere on the page and no edge, seam or halo shows.

This pass does three things to a plate, and nothing else — the glass keeps its
silhouette, its engraving, its wall and its base:

    stage   the light is neutralised to silver and the backdrop is crushed to the
            master black (#000000), so the whole catalogue shares one backdrop and
            one glass tone — no blue, no teal, no per-plate cast
    room    the pool of light that used to sit behind the piece is flattened out,
            so the stage behind the glass is deep black and nothing else: no halo,
            no glow, no grey cloud — only the piece and its own edges
    check   corner values are printed so a stray plate is caught

    python3 tools/master_stage.py --check                 # report, change nothing
    python3 tools/master_stage.py --glob "brand-source/black/*.png"
    python3 tools/master_stage.py --glob "assets/products/*.webp" --sheet /tmp/stage.png
"""
from __future__ import annotations

import argparse
import glob
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage as ndi

ROOT = Path(__file__).resolve().parent.parent
BLACK = ROOT / "brand-source" / "black"
MASTER_BG = (0, 0, 0)          # == --bg in css/app.css; the plate and the page are one surface
AMBIENT_CUT = 0.90             # how much of the soft pool behind the piece is removed
AMBIENT_SIGMA = 0.05           # blur used to find it, as a fraction of the frame width
DETAIL_GAIN = 1.55             # rims, engraving and edges come back brighter than they left


def _border_median(a: np.ndarray) -> np.ndarray:
    ring = np.concatenate([a[:4].reshape(-1, 3), a[-4:].reshape(-1, 3), a[:, :4].reshape(-1, 3), a[:, -4:].reshape(-1, 3)])
    return np.median(ring, axis=0)


def neutralise(a: np.ndarray) -> np.ndarray:
    """Kill the colour cast of the backdrop (the old plates read 0,2,1 — a green tint)."""
    base = _border_median(a)
    gain = np.full(3, float(base.max())) / np.maximum(base, 1.0)
    gain = np.clip(gain, 0.9, 1.1)
    return np.clip(a * gain, 0, 255)


def to_silver(a: np.ndarray) -> np.ndarray:
    """Drop the colour of the stage light: the glass is silver, the room is black.

    Colour was never part of the product — it came from the old navy backdrop
    bleeding through the glass. Luminance is kept exactly, so nothing moves and
    nothing is redrawn, only the tint of the light goes.
    """
    lum = 0.2126 * a[..., 0] + 0.7152 * a[..., 1] + 0.0722 * a[..., 2]
    return np.repeat(lum[..., None], 3, axis=2)


def flatten_ambient(a: np.ndarray, strength: float = AMBIENT_CUT, sigma: float = AMBIENT_SIGMA) -> np.ndarray:
    """Take the wide pool of light out from behind the glass — on every frame.

    The studio lit a soft grey cloud behind every piece. It is entirely low
    frequency, so it is measured with a heavy blur and subtracted from the
    luminance; the rims, engraving and edges are high frequency and are lifted
    instead of lost, so the piece still reads as bright crystal, while the room
    behind it is deep black with nothing in it.
    """
    lum = a.max(axis=2)
    veil = ndi.gaussian_filter(lum, sigma=max(8.0, sigma * a.shape[1]))
    detail = lum - veil
    lit = np.clip(detail * DETAIL_GAIN + veil * (1.0 - strength), 0, 255)
    ratio = np.where(lum > 1e-3, lit / np.maximum(lum, 1e-3), 0.0)[..., None]
    return np.clip(a * ratio, 0, 255)


def to_master(a: np.ndarray) -> np.ndarray:
    """Crush the backdrop to the exact master black, keeping the falloff above it."""
    k = float(_border_median(a).max()) + 1.0
    out = np.clip((a - k) * (255.0 / (255.0 - k)), 0, 255)
    out[a < 1.0] = 0
    return out


def process(path: Path, write: bool, silver: bool = True) -> dict:
    img = Image.open(path).convert("RGB")
    a = np.asarray(img).astype(np.float32)
    before = _border_median(a)
    if silver:
        a = to_silver(a)
    a = neutralise(a)
    a = flatten_ambient(a)
    a = to_master(a)
    out = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))
    after = _border_median(np.asarray(out).astype(np.float32))
    if write:
        if path.suffix.lower() == ".webp":
            out.save(path, "WEBP", quality=90, method=6)
        else:
            out.save(path, "PNG", optimize=True)
    return {"path": path, "before": before, "after": after, "img": out}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--glob", default="")
    ap.add_argument("--check", action="store_true", help="only report the backdrop of every plate")
    ap.add_argument("--sheet", default="")
    ap.add_argument("--no-silver", action="store_true", help="keep the original cast")
    ap.add_argument("--out", default="", help="copy the result here instead of rewriting in place")
    args = ap.parse_args()

    pattern = args.glob or "brand-source/black/*.png"
    paths = [Path(p) for p in sorted(glob.glob(str(ROOT / pattern)))]
    if not paths:
        raise SystemExit(f"nothing matched {pattern}")

    out_dir = Path(args.out) if args.out else None
    if out_dir:
        out_dir.mkdir(parents=True, exist_ok=True)
    rows = []
    for path in paths:
        row = process(path, write=False, silver=not args.no_silver)
        if out_dir:
            row["img"].save(out_dir / (path.stem + ".png"), "PNG", optimize=True)
        elif not args.check:
            row = process(path, write=True, silver=not args.no_silver)
        rows.append(row)

    for r in rows:
        mark = "ok " if max(r["after"]) <= 1 else "!! "
        print(
            f"{mark}{r['path'].relative_to(ROOT)}  backdrop "
            f"{tuple(int(v) for v in r['before'])} -> {tuple(int(v) for v in r['after'])}"
        )
    print(f"{len(rows)} plates, master stage {MASTER_BG}")

    if args.sheet:
        cols, tw, th = 5, 250, 330
        sheet_rows = (len(rows) + cols - 1) // cols
        sheet = Image.new("RGB", (cols * tw, sheet_rows * th), MASTER_BG)
        draw = ImageDraw.Draw(sheet)
        for i, r in enumerate(rows):
            x, y = (i % cols) * tw, (i // cols) * th
            thumb = r["img"].copy()
            thumb.thumbnail((tw - 10, th - 28), Image.LANCZOS)
            sheet.paste(thumb, (x + (tw - thumb.width) // 2, y + 6))
            draw.text((x + 8, y + th - 20), r["path"].stem[:32], fill=(235, 235, 235))
        target = Path(args.sheet)
        target.parent.mkdir(parents=True, exist_ok=True)
        sheet.save(target)
        print("sheet", target)


if __name__ == "__main__":
    main()
