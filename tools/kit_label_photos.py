"""RECIPE1: make the kit's Photo_N.jpg from picked Pixabay photos: blur listed regions (brand signs), scale to 1920 wide, and
draw a small "Photo N" label in the top-left corner (shows what to replace; and the shipped file is no longer the Pixabay
original, as the licence's "Standalone" rule asks).

  python3 label.py --picks picks --out DIR 1b 1e …      (Photo_1 from the first pick, Photo_2 from the second, …)
"""
import argparse
import pathlib

from PIL import Image, ImageDraw, ImageFilter, ImageFont

FONT = pathlib.Path.home() / "projects/pixies-craft-templates/fonts/inter/Inter[opsz,wght].ttf"
# Regions to blur, in the 1280-wide download's pixels: readable brand signs
BLUR = {"6c": [(110, 487, 182, 509), (182, 450, 206, 474), (437, 592, 453, 636), (345, 645, 382, 672)]}


def make(src, pick, n, out):
    im = Image.open(src).convert("RGB")
    if pick in BLUR:
        # Blur under a feathered mask, so each sign turns into soft light rather than a hard-edged block
        mask = Image.new("L", im.size, 0)
        for box in BLUR[pick]:
            ImageDraw.Draw(mask).rounded_rectangle(box, radius=4, fill=255)
        im = Image.composite(im.filter(ImageFilter.GaussianBlur(5)), im, mask.filter(ImageFilter.GaussianBlur(4)))
    im = im.resize((1920, round(im.height * 1920 / im.width)), Image.LANCZOS)
    d = ImageDraw.Draw(im, "RGBA")
    font = ImageFont.truetype(str(FONT), 34)
    font.set_variation_by_axes([34, 600]) if hasattr(font, "set_variation_by_axes") else None
    text = f"Photo {n}"
    l, t, r, b = d.textbbox((0, 0), text, font=font)
    x, y, pad = 28, 24, 12
    d.rounded_rectangle((x, y, x + r - l + 2 * pad, y + b - t + 2 * pad), radius=10, fill=(0, 0, 0, 140))
    d.text((x + pad - l, y + pad - t), text, font=font, fill=(255, 255, 255, 235))
    im.save(out / f"Photo_{n}.jpg", quality=90)   # PIL writes no EXIF unless asked
    return im.size


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--picks", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("order", nargs="+")
    a = ap.parse_args()
    out = pathlib.Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    for n, pick in enumerate(a.order, 1):
        print(f"Photo_{n}.jpg <- {pick}", make(pathlib.Path(a.picks) / f"{pick}.jpg", pick, n, out))


if __name__ == "__main__":
    main()
