#!/usr/bin/env python3
"""Cocktail Embassy — re-frame the photography set to the reference crop.

The owner's reference for framing is the old `ce` catalogue: the piece is *big*
in the frame (roughly ¾ of the height), dead centre, with even margins, and the
backdrop melts unseen into the app background. The house masters were shot with
more air around the glass, so the cards read small and the set never lines up.

This tool never touches the glass itself. It only finds the piece, crops the
frame around it to a fixed share of the canvas and re-delivers at the same
size, so silhouettes stay pixel-identical:

    piece height   = PIECE_H × canvas height
    piece centre x = canvas centre
    piece baseline = BASELINE × canvas height   (the base sits on the floor line)

Edges are feathered into the shared room tone (rgb 7,12,24) so a crop can never
show its own seam.

    python3 tools/reframe_images.py --set products            # in place
    python3 tools/reframe_images.py --set products --dry      # measure only
    python3 tools/reframe_images.py --set products --dry-run --dest /tmp/out
    python3 tools/reframe_images.py --on assets/products/rocks.webp --preview
"""
from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
from PIL import Image, ImageFilter

ROOT = Path(__file__).resolve().parent.parent
ASSETS = ROOT / "assets"

ROOM = (7, 12, 24)        # the app background = the backdrop of every photo
CANVAS = (1800, 2250)     # 4:5 deliverable — the crop is native, never upscaled
SMALL_W = 840

PIECE_H = 0.775           # piece height, share of the canvas
BASELINE = 0.845          # where the foot / base rests
MASK_MIN = 60.0           # subject detection: the crystal body, not the glow
MASK_MARGIN = 0.045       # the dim last millimetre of rim / foot
SHARPEN = 0.35


def detect(img: Image.Image) -> tuple[int, int, int, int]:
    """Bounding box of the piece: the pixels that leave the flat backdrop."""
    a = np.asarray(img.convert("RGB")).astype(np.float32)
    h, w, _ = a.shape
    k = max(4, min(h, w) // 12)
    bg = np.median(np.array([
        np.median(a[:k, :k].reshape(-1, 3), axis=0),
        np.median(a[:k, -k:].reshape(-1, 3), axis=0),
        np.median(a[-k:, :k].reshape(-1, 3), axis=0),
        np.median(a[-k:, -k:].reshape(-1, 3), axis=0),
    ]), axis=0)
    d = np.linalg.norm(a - bg, axis=2)
    # The soft bloom behind the glass is as bright as the glass body, so a low
    # threshold would return the whole halo. Step up until the box is the piece:
    # the crystal is where the backdrop is *strongly* lifted.
    m = None
    for t in (MASK_MIN, MASK_MIN + 20, MASK_MIN + 45, MASK_MIN + 80):
        cand = d > t
        cand[:2, :] = cand[-2:, :] = cand[:, :2] = cand[:, -2:] = False
        if cand.sum() > 0.004 * w * h:
            m = cand
            break
    if m is None:
        return 0, 0, w, h
    ys, xs = np.where(m)
    x0, y0, x1, y1 = int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1

    # A polished floor leaves a reflection under the piece: it is narrow and dim,
    # so the true bottom is the last row that is still as wide as the body.
    widths = m.sum(axis=1).astype(np.float32)
    body_w = float(np.percentile(widths[y0:y1], 98))
    solid = np.where(widths >= 0.45 * body_w)[0]
    if solid.size:
        y1 = int(solid.max()) + 1
    # grow by a hair so the faint rim and the foot edge stay inside the piece
    mx, my = int((x1 - x0) * MASK_MARGIN), int((y1 - y0) * MASK_MARGIN)
    return max(0, x0 - mx), max(0, y0 - my), min(w, x1 + mx), min(h, y1 + my)


def reframe(path: Path, dest: Path | None, *, piece_h=PIECE_H, baseline=BASELINE,
            canvas=CANVAS, quality=88) -> dict:
    src = Image.open(path).convert("RGB")
    x0, y0, x1, y1 = detect(src)
    ph = max(1, y1 - y0)                     # piece height in source pixels
    pw = max(1, x1 - x0)
    cx = (x0 + x1) / 2

    cw, ch = canvas
    scale = (piece_h * ch) / ph              # how much the crop is blown up
    # crop window in source space, centred on the piece
    win_w = cw / scale
    win_h = ch / scale
    left = cx - win_w / 2
    top = y1 - baseline * ch / scale         # baseline of the piece → floor line

    # keep the window inside the source where possible (the crop may still need
    # padding; that padding is painted in the room tone, which is invisible)
    pad = (0, 0, 0, 0)
    if left < 0:
        pad = (int(-left), pad[1], pad[2], pad[3]); left = 0
    if top < 0:
        pad = (pad[0], int(-top), pad[2], pad[3]); top = 0
    right = left + win_w
    bottom = top + win_h
    if right > src.width:
        pad = (pad[0], pad[1], int(right - src.width), pad[3]); right = src.width
    if bottom > src.height:
        pad = (pad[0], pad[1], pad[2], int(bottom - src.height)); bottom = src.height

    box = (int(left), int(top), int(right), int(bottom))
    crop = src.crop(box)
    if any(pad):
        framed = Image.new("RGB", (int(win_w) + pad[0] + pad[2],
                                   int(win_h) + pad[1] + pad[3]), ROOM)
        framed.paste(crop, (pad[0], pad[1]))
        crop = framed

    out = crop.resize((cw, ch), Image.LANCZOS)
    # a whisper of structure after the resample, so rims stay crisp
    sharp = out.filter(ImageFilter.UnsharpMask(radius=1.4, percent=int(SHARPEN * 100), threshold=2))
    out = Image.blend(out, sharp, 0.55)

    # feather every edge into the room tone: the crop has no seam anywhere
    a = np.asarray(out).astype(np.float32)
    h, w, _ = a.shape
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    r = np.sqrt(((xx - w / 2) / (w / 2)) ** 2 + ((yy - h / 2) / (h / 2)) ** 2)
    t = np.clip((1.06 - r) / 0.14, 0, 1)
    t = t * t * (3 - 2 * t)
    room = np.array(ROOM, np.float32)
    a = room + (a - room) * t[..., None]
    out = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8), "RGB")

    try:
        rel = str(path.relative_to(ROOT))
    except ValueError:
        rel = path.name
    stats = {
        "file": rel,
        "src_piece": [pw, ph],
        "scale": round(scale, 3),
        "crop": box,
        "pad": pad,
    }

    if dest is not None:
        dest.mkdir(parents=True, exist_ok=True)
        out.save(dest / path.name, quality=quality, method=6)
        small = out.resize((SMALL_W, int(round(SMALL_W * ch / cw))), Image.LANCZOS)
        small.save(dest / f"{path.stem}-sm{path.suffix}", quality=quality, method=6)
        stats["out"] = str(dest / path.name)
    return stats


def collect(which: str) -> list[Path]:
    out: list[Path] = []
    if which in ("products", "all"):
        out += sorted(p for p in (ASSETS / "products").glob("*.webp") if "-sm" not in p.name)
    if which in ("drinks", "all"):
        out += sorted(p for p in (ASSETS / "drinks").rglob("*.webp") if "-sm" not in p.name)
    if which in ("editorial", "all"):
        out += sorted(p for p in (ASSETS / "editorial").glob("*.webp")
                      if "-sm" not in p.name and "mesh" not in p.name)
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--set", default="products",
                    choices=["products", "drinks", "editorial", "all"])
    ap.add_argument("--on", default="", help="a single file instead of a set")
    ap.add_argument("--only", default="", help="substring filter on filenames")
    ap.add_argument("--dest", default="", help="write here instead of in place")
    ap.add_argument("--src", default="", help="read the set from this folder")
    ap.add_argument("--piece-h", type=float, default=PIECE_H)
    ap.add_argument("--baseline", type=float, default=BASELINE)
    ap.add_argument("--quality", type=int, default=88)
    ap.add_argument("--dry-run", action="store_true", help="measure only, write nothing")
    args = ap.parse_args()

    if args.src:
        src_dir = Path(args.src)
        jobs = sorted(p for p in src_dir.rglob("*.webp") if "-sm" not in p.name)
    else:
        jobs = [Path(args.on)] if args.on else collect(args.set)
    if args.only:
        jobs = [p for p in jobs if args.only in p.name]
    if not jobs:
        raise SystemExit("no images matched")

    dest = Path(args.dest) if args.dest else None
    for p in jobs:
        if dest is not None:
            out_dir = dest
        elif args.dry_run:
            out_dir = None
        else:
            out_dir = Path(args.on).parent if args.on else p.parent
        st = reframe(p, out_dir, piece_h=args.piece_h, baseline=args.baseline,
                     quality=args.quality)
        print(f"{st['file']:<42} piece {st['src_piece'][0]:>4}x{st['src_piece'][1]:<4} "
              f"scale {st['scale']:<5} pad {st['pad']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
