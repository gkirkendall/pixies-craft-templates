#!/usr/bin/env python3
"""Make brand/pixie.png, the Pixie picture of the page, README and reel pages (PLAN.md, BRAND1).

  python3 tools/brand/make_pixie.py --source ~/projects/pixback_launch/video/dinosaur_ad/review/pixie_candidates/pixie_C.png

The source is the PixBack ad's candidate C (turquoise costume; kept outside this repository). Its turquoise fur is recoloured to the
final costume's peach (hue 27, saturation scaled 114/173, measured on the ad's peach still), the blue fringes where purple spots
met the turquoise are moved to the costume's purple (hue 278) and the purple deepened to match; then Pixie is cut out with rembg's
BiRefNet "massive" model (needs: pip install "rembg[cpu]"; the model, about 1 GB, downloads on first use), the grey studio fringe
removed by pymatting's foreground estimation, trimmed to Pixie and saved 1200 px tall (reel pages, README), plus a 340 px wide copy for the page. The picture is PixBack's mascot, all rights
reserved: not under the templates' licence (CREDITS.md).
"""
import argparse
import pathlib

import numpy as np
from PIL import Image, ImageFilter

ROOT = pathlib.Path(__file__).resolve().parents[2]
OUT = ROOT / "brand" / "pixie.png"
WEB = ROOT / "brand" / "pixie_web.png"   # the page's copy: 340 px wide, twice its width on screen
HEIGHT, WEB_WIDTH = 1200, 340


def hsv(im):
    return [np.asarray(c, dtype=np.float32) for c in im.convert("HSV").split()]


def merge(h, s, v):
    return Image.merge("HSV", [Image.fromarray(np.clip(x, 0, 255).astype(np.uint8)) for x in (h, s, v)]).convert("RGB")


def band(deg, s, lo, hi):
    """Weight 1 inside hue lo-hi degrees, fading over 8-12 degrees outside; greys (low saturation) fade out."""
    return np.clip(1 - np.maximum(0, np.maximum(lo - deg, deg - hi)) / 10, 0, 1) * np.clip((s - 30) / 30, 0, 1)


def recolour(im):
    h, s, v = hsv(im)
    w = band(h * 360 / 255, s, 170, 215)
    w = np.asarray(Image.fromarray((w * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(1.5)), dtype=np.float32)[..., None] / 255
    peach = merge(np.full_like(h, 27 * 255 / 360), s * 114 / 173, v * 1.04)
    im = Image.fromarray((np.asarray(im, np.float32) * (1 - w) + np.asarray(peach, np.float32) * w).round().astype(np.uint8))
    h, s, v = hsv(im)
    deg = h * 360 / 255
    fringe, purple = band(deg, s, 212, 268), band(deg, s, 212, 300)
    return merge(h * (1 - fringe) + 278 * 255 / 360 * fringe, s * (1 - purple) + s * 177 / 154 * purple,
                 v * (1 - purple) + v * 127 / 166 * purple)


def cut_out(im):
    from pymatting import estimate_foreground_ml
    from rembg import new_session, remove
    mask = remove(im, session=new_session("birefnet-massive", providers=["CPUExecutionProvider"]), only_mask=True)
    alpha = np.asarray(mask, np.float64) / 255
    fg = estimate_foreground_ml(np.asarray(im, np.float64) / 255, alpha)
    rgba = np.dstack([fg, alpha]) * 255
    out = Image.fromarray(rgba.round().clip(0, 255).astype(np.uint8), "RGBA")
    return out.crop(out.split()[3].point(lambda a: 255 if a > 8 else 0).getbbox())


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--source", type=pathlib.Path, required=True, help="the ad's pixie_C.png")
    a = ap.parse_args()
    pixie = cut_out(recolour(Image.open(a.source.expanduser()).convert("RGB")))
    pixie = pixie.resize((round(pixie.width * HEIGHT / pixie.height), HEIGHT), Image.LANCZOS)
    OUT.parent.mkdir(exist_ok=True)
    pixie.save(OUT, optimize=True)
    web = pixie.resize((WEB_WIDTH, round(pixie.height * WEB_WIDTH / pixie.width)), Image.LANCZOS)
    web.save(WEB, optimize=True)
    print(f"wrote {OUT.relative_to(ROOT)} ({pixie.width}x{pixie.height}) and {WEB.relative_to(ROOT)} ({web.width}x{web.height})")


if __name__ == "__main__":
    main()
