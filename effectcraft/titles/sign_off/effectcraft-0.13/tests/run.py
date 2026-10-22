#!/usr/bin/env python3
"""Test for Sign-off. Free: no GPU; reads the text back with tesseract (brew install tesseract).

  python3 effectcraft/titles/sign_off/effectcraft-0.13/tests/run.py --effectcraft-cli PATH

Renders single transparent frames, with the shadow off, in both sizes, for the default line, a short one, a long one and a moved
Position. Text and hearts are told apart by colour. Checks for each: the text between the hearts reads back (OCR) exactly as
supplied; the two hearts are the same size, Heart Size % of the font size wide, and the same gap from the text on each side (the
hearts follow its width; the ink may sit inside the text's box by the font's side bearings); the row is centred on Position (within 1 % across, 2 % down) and within Max Width. Then: nothing before
Start; the hearts appear after the text and overshoot as they pop; nearly gone one frame before Duration; Text Colour and Heart
Colour colour each part; Shadow 50 draws a shadow; with Blink on, the hearts are drawn in the on part of a beat and
not in the off part while the text stays the same, and with Blink off they stay; Duration sets the clip's length. Results go to tests/out/ with a contact sheet.
"""
import argparse
import json
import pathlib
import subprocess
import sys

from PIL import Image, ImageDraw

HERE = pathlib.Path(__file__).resolve().parent
TEMPLATE = HERE.parent
ROOT = next(p for p in TEMPLATE.parents if (p / "tools" / "render.py").is_file())
sys.path.insert(0, str(ROOT / "tools"))
from fontcheck import font_checks  # noqa: E402
OUT = HERE / "out"
MANIFEST = json.loads((TEMPLATE / "template.json").read_text())
DEFAULT_TEXT = next(c["default"] for c in MANIFEST["controls"] if c["name"] == "Text")
FRAMES = {"16x9": (1920, 1080), "9x16": (1080, 1920)}
FONT_SIZE = {"16x9": 64, "9x16": 56}
POSITION = {"16x9": [960, 790], "9x16": [540, 1160]}
MAX_WIDTH = {"16x9": 1651, "9x16": 929}
CASES = {"default": {}, "short": {"Text": "Bye!"},
         "long": {"Text": "Thanks for watching, and see you on the next long road trip around the country"},
         "moved": {"Position": "moved"}}
START, PEAK = 0.6, 2.0


def run(cmd):
    r = subprocess.run([str(c) for c in cmd], capture_output=True, text=True)
    if r.returncode:
        sys.exit(f"failed: {' '.join(map(str, cmd))}\n{r.stderr or r.stdout}")
    return r.stdout


def parts(png):
    """Masks of the hearts (red) and the text (everything else drawn), from a frame with the default colours."""
    im = Image.open(png).convert("RGBA")
    red = Image.new("L", im.size, 0)
    text = Image.new("L", im.size, 0)
    rp, tp = red.load(), text.load()
    px = im.load()
    for y in range(im.height):
        for x in range(im.width):
            r, g, b, a = px[x, y]
            if a > 40:
                if r > 120 and g < 0.75 * r:
                    rp[x, y] = 255
                else:
                    tp[x, y] = 255
    return red, text


def split(mask, mid):
    """The left and right halves' boxes of a mask about x = mid."""
    w, h = mask.size
    left = mask.crop((0, 0, int(mid), h)).getbbox()
    right = mask.crop((int(mid), 0, w, h)).getbbox()
    return left, right and (right[0] + int(mid), right[1], right[2] + int(mid), right[3])


def ocr(png, box, side):
    """The text in box as tesseract reads it, with side px of margin left and right (kept clear of the hearts)."""
    im = Image.open(png).convert("RGBA")
    bg = Image.new("RGBA", im.size, (0, 0, 0, 255))
    bg.alpha_composite(im)
    g = bg.convert("L").crop((box[0] - side, box[1] - 20, box[2] + side, box[3] + 20)).point(lambda v: 255 - v)
    g = g.resize((g.width * 2, g.height * 2))
    src = png.with_suffix(".ocr.png")
    g.save(src)
    try:
        return run(["tesseract", src, "-", "--psm", "7"])
    except FileNotFoundError:
        sys.exit("tesseract is needed to read the text back: brew install tesseract (or your system's package)")


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--effectcraft-cli", default="effectcraft-cli")
    a = ap.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    results, sheet = [], []

    def check(name, ok, detail):
        results.append(ok)
        print(("PASS " if ok else "FAIL ") + name + ": " + detail)

    def frame(variant, values, t, tag):
        vfile = OUT / f"{tag}.values.json"
        vfile.write_text(json.dumps(values))
        out = OUT / f"{tag}.png"
        run([sys.executable, ROOT / "tools" / "render.py", TEMPLATE, "--variant", variant, "--values", vfile, "--out", out,
             "--frame", f"{t:.4f}", "--effectcraft-cli", a.effectcraft_cli])
        return out

    for variant, (W, H) in FRAMES.items():
        for case, extra in CASES.items():
            tag = f"{variant}_{case}"
            values, pos = dict(extra, Shadow=0), POSITION[variant]
            if values.get("Position") == "moved":
                pos = values["Position"] = [W * 0.4, H * 0.3]
            png = frame(variant, values, PEAK, tag)
            red, text = parts(png)
            tbox = text.getbbox()
            hl, hr = split(red, (tbox[0] + tbox[2]) / 2)
            want = values.get("Text", DEFAULT_TEXT)
            got = " ".join(ocr(png, tbox, max(2, min(20, tbox[0] - hl[2] - 3))).split())
            check(f"{tag} text", got == want, f"read {got!r}" + ("" if got == want else f", expected {want!r}"))
            row = (hl[0], min(hl[1], tbox[1], hr[1]), hr[2], max(hl[3], tbox[3], hr[3]))
            # Hearts: equal; 0.7 of the font size wide unless the row was shrunk to Max Width; each 0.45 of the font size (0.64 of a
            # heart's width) from the text's box, which the ink can sit inside by the font's side bearings (within 10 % of the font size).
            shrunk = row[2] - row[0] >= MAX_WIDTH[variant] - 2
            hw = [hl[2] - hl[0], hr[2] - hr[0]]
            gaps = [tbox[0] - hl[2], hr[0] - tbox[2]]
            heart_mid = (hl[1] + hl[3]) / 2
            fs = hw[0] / 0.7 if shrunk else FONT_SIZE[variant]   # the font size as drawn
            ok = (abs(hw[0] - hw[1]) <= 2 and (shrunk or abs(hw[0] - 0.7 * fs) <= 0.1 * 0.7 * fs + 2)
                  and all(abs(g - 0.45 / 0.7 * hw[0]) <= 0.1 * hw[0] / 0.7 + 2 for g in gaps))
            check(f"{tag} hearts", ok, f"heart widths {hw} (expected {'scaled with the row' if shrunk else f'about {0.7 * fs:.0f}'}); "
                  f"gaps to the text {gaps} (heart-relative {0.45 / 0.7 * hw[0]:.0f}, plus side bearings)")
            cx, cy = (row[0] + row[2]) / 2, heart_mid
            ok = abs(cx - pos[0]) <= W * 0.01 and abs(cy - pos[1]) <= H * 0.02 and row[2] - row[0] <= MAX_WIDTH[variant] + 2
            check(f"{tag} row", ok, f"width {row[2] - row[0]} of {MAX_WIDTH[variant]}; centre ({cx:.0f}, {cy:.0f}) vs ({pos[0]:.0f}, {pos[1]:.0f})")
            t = Image.new("RGBA", (W, H), (60, 75, 90, 255))
            t.alpha_composite(Image.open(png).convert("RGBA"))
            t = t.convert("RGB")
            t.thumbnail((480, 480))
            sheet.append((tag, t))

    v = {"Shadow": 0}
    before = Image.open(frame("16x9", v, START - 1 / 24, "before")).getchannel("A").getbbox()
    check("nothing before Start", before is None, f"one frame before {START} s: {before}")
    early_red, early_text = parts(frame("16x9", v, START + 0.2, "early"))
    pop_red, _ = parts(frame("16x9", v, START + 0.55, "pop"))
    peak_red, _ = parts(OUT / "16x9_default.png")
    widths = [(m.getbbox()[2] - m.getbbox()[0]) if m.getbbox() else 0 for m in (early_red, pop_red, peak_red)]
    check("hearts pop in after the text", early_text.getbbox() is not None and widths[0] == 0 and widths[1] > widths[2],
          f"at +0.2 s text shown {early_text.getbbox() is not None}, hearts {widths[0]} px; at +0.55 s hearts span {widths[1]} px "
          f"(overshoot) vs {widths[2]} px once in")
    end = Image.open(frame("16x9", dict(v, Duration=4), 4 - 1 / 24, "end")).getchannel("A").getextrema()[1]
    check("faded out by Duration", end < 0.2 * 255, f"one frame before Duration 4: alpha {end}")
    im = Image.open(frame("16x9", dict(v, **{"Text Colour": "#ffcc00", "Heart Colour": "#33aaff"}), PEAK, "colours")).convert("RGBA")
    solid = [p[:3] for p in im.getdata() if p[3] == 255]
    yellow = sum(1 for p in solid if p[0] > 230 and 190 < p[1] < 215 and p[2] < 20)
    blue = sum(1 for p in solid if p[0] < 70 and 150 < p[1] < 185 and p[2] > 235)
    check("Text Colour and Heart Colour", yellow > 2000 and blue > 1000 and yellow + blue >= 0.97 * len(solid),
          f"{yellow} yellow and {blue} blue of {len(solid)} solid pixels")
    im = Image.open(frame("16x9", {}, PEAK, "shadow")).convert("RGBA")
    dark = sum(1 for p in im.getdata() if 0 < p[3] and max(p[:3]) < 60)
    check("Shadow 50 draws a shadow", dark > 1000, f"{dark} dark pixels")
    # Blink at 60 beats a minute: beats from Start + 0.7 = 1.3 s, on for 0.6 s of each. 2.6 s is 0.3 into a beat (on), 3.1 s 0.8 (off).
    b = dict(v, Blink=True, **{"Beats per Minute": 60})
    on_red, on_text = parts(frame("16x9", b, 2.6, "blink_on"))
    off_red, off_text = parts(frame("16x9", b, 3.1, "blink_off"))
    still_red, _ = parts(frame("16x9", v, 3.1, "blink_none"))
    check("Blink beats the hearts", on_red.getbbox() is not None and off_red.getbbox() is None and still_red.getbbox() is not None
          and on_text.getbbox() == off_text.getbbox(),
          f"hearts at 2.6 s {on_red.getbbox()}, at 3.1 s {off_red.getbbox()}, Blink off at 3.1 s {still_red.getbbox()}; "
          f"text {on_text.getbbox()} and {off_text.getbbox()}")
    def still(values, tag):
        frame("16x9", values, PEAK, tag)
        return Image.open(OUT / f"{tag}.png")
    for name, ok, detail in font_checks(still, {"Font": []}):
        check(name, ok, detail)
    vfile = OUT / "duration.values.json"
    vfile.write_text(json.dumps({"Duration": 3}))
    clip = OUT / "duration.mov"
    run([sys.executable, ROOT / "tools" / "render.py", TEMPLATE, "--variant", "16x9", "--values", vfile, "--out", clip,
         "--effectcraft-cli", a.effectcraft_cli])
    seconds = float(run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", clip]).strip())
    check("Duration sets the clip length", abs(seconds - 3) <= 0.05, f"Duration 3 rendered {seconds:.2f} s")

    s = Image.new("RGB", (4 * 490 + 10, ((len(sheet) + 3) // 4) * 500 + 10), "white")
    for i, (tag, t) in enumerate(sheet):
        x, y = 10 + (i % 4) * 490, 10 + (i // 4) * 500
        s.paste(t, (x, y + 20))
        ImageDraw.Draw(s).text((x, y + 4), tag, fill=(0, 0, 0))
    s.save(OUT / "sheet.png")
    print(f"\n{sum(results)} of {len(results)} checks pass; sheet {OUT / 'sheet.png'}")
    sys.exit(0 if all(results) else 1)


if __name__ == "__main__":
    main()
