#!/usr/bin/env python3
"""Cocktail Embassy — halo matching.

The set has to read as one shoot. The reference for that is the old `ce`
catalogue: a tight, quiet bloom behind the piece, never a big glowing oval. The
house masters were lit wider, so their halo is 30–60 % brighter in the outer
rings than the reference family.

This tool measures the brightness of concentric rings around the piece and dims
the *backdrop only* until the ring profile matches the reference median. The
glass — and every pixel that belongs to it — is left exactly as it is: the gain
is applied outside a feathered silhouette mask, so no rim, foot or etching is
touched.

    python3 tools/tone_images.py --set products            # in place
    python3 tools/tone_images.py --set products --dry-run  # measure only
    python3 tools/tone_images.py --set editorial --strength 0.8
    python3 tools/tone_images.py --on assets/products/rocks.webp --preview
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
from PIL import Image
from scipy import ndimage as ndi

ROOT = Path(__file__).resolve().parent.parent
ASSETS = ROOT / "assets"

RINGS = 14                       # radial samples from the centre to 1.2 × half-width
INNER = 0.34                     # inside this normalised radius nothing is touched
PIECE_T = 28.0                   # "this is glass", not bloom
FEATHER = 9                      # px of the mask feather, in working space
GAIN_LO, GAIN_HI = 0.40, 1.06    # never dim more than this, never amplify
WORK = (760, 950)                # analysis / mask space


def lum(a: np.ndarray) -> np.ndarray:
    return a[..., 0] * 0.2126 + a[..., 1] * 0.7152 + a[..., 2] * 0.0722


def rings_of(L: np.ndarray) -> np.ndarray:
    h, w = L.shape
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    r = np.sqrt(((xx - w / 2) / (w / 2)) ** 2 + ((yy - h / 2) / (h / 2)) ** 2)
    edges = np.linspace(0.0, 1.25, RINGS + 1)
    out = np.empty(RINGS, np.float32)
    for i in range(RINGS):
        m = (r >= edges[i]) & (r < edges[i + 1])
        out[i] = float(np.median(L[m])) if m.any() else 0.0
    return out


def load(p: Path) -> np.ndarray:
    return np.asarray(Image.open(p).convert("RGB").resize(WORK, Image.LANCZOS)).astype(np.float32)


def piece_mask(a: np.ndarray) -> np.ndarray:
    """Where the glass is — the piece plus the bloom it throws off itself.

    Everything inside this mask keeps its original light; only the wide studio
    halo outside it is re-lit. A soft, generous mask is deliberate: it means no
    rim, stem, foot or etching can ever be dimmed.
    """
    h, w, _ = a.shape
    k = max(4, min(h, w) // 12)
    bg = np.median(np.array([
        np.median(a[:k, :k].reshape(-1, 3), axis=0),
        np.median(a[:k, -k:].reshape(-1, 3), axis=0),
        np.median(a[-k:, :k].reshape(-1, 3), axis=0),
        np.median(a[-k:, -k:].reshape(-1, 3), axis=0),
    ]), axis=0)
    d = np.linalg.norm(a - bg, axis=2)
    m = d > 55.0
    m = ndi.binary_closing(m, np.ones((5, 5)))
    m = ndi.binary_fill_holes(m)
    m = ndi.binary_dilation(m, np.ones((7, 7)))
    soft = ndi.gaussian_filter(m.astype(np.float32), FEATHER)
    return np.clip(soft * 1.6, 0, 1)


def reference_profile(files: list[Path], exclude: Path | None = None) -> np.ndarray:
    profiles = []
    for p in files:
        if exclude is not None and p.resolve() == exclude.resolve():
            continue
        profiles.append(rings_of(lum(load(p))))
    if not profiles:
        raise SystemExit("no reference images")
    return np.median(np.array(profiles), axis=0)


def refs() -> list[Path]:
    out: list[Path] = []
    for folder in ("archive", "editorial"):
        out += [p for p in sorted((ASSETS / folder).rglob("*.webp"))
                if "-sm" not in p.name and "card" not in p.name and "mesh" not in p.name
                and p.parent.name != "covers"]
    return out


def match(path: Path, target: np.ndarray, dest: Path | None, *, strength=0.55,
          quality=88, report: dict | None = None) -> dict:
    src = Image.open(path).convert("RGB")
    small = load(path)
    cur = rings_of(lum(small))

    ratio = np.clip(target / np.maximum(cur, 1.0), GAIN_LO, GAIN_HI)
    ratio = ndi.uniform_filter1d(ratio, 3, mode="nearest")
    gain = 1.0 - (1.0 - ratio) * strength
    gain[:4] = 1.0                       # the piece and its own bloom are never touched

    # radial map at full resolution
    a = np.asarray(src).astype(np.float32)
    h, w, _ = a.shape
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    r = np.sqrt(((xx - w / 2) / (w / 2)) ** 2 + ((yy - h / 2) / (h / 2)) ** 2)
    edges = np.linspace(0.0, 1.25, RINGS + 1)
    gmap = np.interp(r, (edges[:-1] + edges[1:]) / 2, gain, left=gain[0], right=gain[-1])

    # leave the glass untouched: feather the gain out inside the silhouette
    mask = piece_mask(np.asarray(Image.fromarray(a.astype(np.uint8)).resize(WORK, Image.LANCZOS)).astype(np.float32))
    mask_full = np.asarray(Image.fromarray((mask * 255).astype(np.uint8)).resize((w, h), Image.BILINEAR)).astype(np.float32) / 255.0
    gmap = gmap * (1.0 - mask_full) + 1.0 * mask_full
    gmap = np.where(r < INNER, 1.0, gmap)

    out = np.clip(a * gmap[..., None], 0, 255).astype(np.uint8)
    img = Image.fromarray(out, "RGB")

    st = {"file": str(path.relative_to(ROOT)),
          "rings_before": [round(float(v), 1) for v in cur],
          "rings_gain": [round(float(v), 3) for v in gain]}
    if report is not None:
        report[path.name] = st

    if dest is not None:
        dest.mkdir(parents=True, exist_ok=True)
        img.save(dest / path.name, quality=quality, method=6)
        small_im = img.resize((840, int(round(840 * h / w))), Image.LANCZOS)
        small_im.save(dest / f"{path.stem}-sm{path.suffix}", quality=quality, method=6)
        st["out"] = str(dest / path.name)
    return st


def collect(which: str) -> list[Path]:
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


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--set", default="products",
                    choices=["products", "drinks", "editorial", "archive", "all"])
    ap.add_argument("--on", default="")
    ap.add_argument("--only", default="")
    ap.add_argument("--dest", default="")
    ap.add_argument("--strength", type=float, default=0.55,
                    help="how far to move the halo towards the reference (1 = full match)")
    ap.add_argument("--quality", type=int, default=88)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--json", default="")
    args = ap.parse_args()

    target = reference_profile(refs())
    jobs = [Path(args.on)] if args.on else collect(args.set)
    if args.only:
        jobs = [p for p in jobs if args.only in p.name]
    if not jobs:
        raise SystemExit("no images matched")

    dest = Path(args.dest) if args.dest else None
    report: dict[str, dict] = {}
    print("reference ring profile:", np.round(target, 1).tolist())
    for p in jobs:
        out_dir = dest if dest else (None if args.dry_run else p.parent)
        st = match(p, target, out_dir, strength=args.strength,
                   quality=args.quality, report=report)
        print(f"{st['file']:<42} before {st['rings_before'][2]:>6} gain "
              f"{min(st['rings_gain']):.2f}…{max(st['rings_gain']):.2f}")
    if args.json:
        Path(args.json).write_text(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
