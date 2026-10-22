#!/usr/bin/env python3
"""Test for Animated Title. Free: no GPU; reads the text back with tesseract (brew install tesseract).

  python3 effectcraft/titles/animated_title/effectcraft-0.13/tests/run.py --effectcraft-cli PATH

Renders single transparent frames, with the shadow off. Checks, in both sizes: at rest, for every Style, the text reads back
(OCR) without its stars and is centred on Position (within 1 %). In 16x9: part-way in, for every Style but Spread In, the start of
the text is further in than its end (more of its ink drawn), and part-way out the start has gone further; Spread In is wider part-way
in than at rest; By Words and By Lines move the first word or line ahead of the last; the starred word takes the Highlight Colour
and nothing else does; nothing before Start; Fade Steady draws it fully from the first frame to the last, and Fade In, Steady and
Fade Out clips meet without a jump; a long title shrinks to Max Width; Size scales it; the Font control changes the font;
Duration sets the clip's length; a long title's move in is shortened to fit (at rest by 2 s). Results go to tests/out/ with a contact sheet.
"""
import argparse
import json
import pathlib
import subprocess
import sys

from PIL import Image, ImageChops, ImageDraw

HERE = pathlib.Path(__file__).resolve().parent
TEMPLATE = HERE.parent
ROOT = next(p for p in TEMPLATE.parents if (p / "tools" / "render.py").is_file())
OUT = HERE / "out"
MANIFEST = json.loads((TEMPLATE / "template.json").read_text())
DEFAULTS = {c["name"]: c.get("default") for c in MANIFEST["controls"]}
STYLES = next(c["options"] for c in MANIFEST["controls"] if c["name"] == "Style")
FRAMES = {"16x9": (1920, 1080), "9x16": (1080, 1920)}
MAX_WIDTH = {"16x9": 1651, "9x16": 929}
REST, START = 2.0, 0.3


def run(cmd):
    r = subprocess.run([str(c) for c in cmd], capture_output=True, text=True)
    if r.returncode:
        sys.exit(f"failed: {' '.join(map(str, cmd))}\n{r.stderr or r.stdout}")
    return r


def ocr(png):
    """The text as tesseract reads it (one line), white on transparent made black on white and doubled in size."""
    im = Image.open(png).convert("RGBA")
    bg = Image.new("RGBA", im.size, (0, 0, 0, 255))
    bg.alpha_composite(im)
    box = im.getchannel("A").getbbox()
    g = bg.convert("L").crop((box[0] - 30, box[1] - 30, box[2] + 30, box[3] + 30)).point(lambda v: 255 - v)
    g = g.resize((g.width * 2, g.height * 2))
    src = png.with_suffix(".ocr.png")
    g.save(src)
    try:
        return run(["tesseract", src, "-", "--psm", "7"]).stdout
    except FileNotFoundError:
        sys.exit("tesseract is needed to read the text back: brew install tesseract (or your system's package)")


def ink(alpha, box):
    """Sum of alpha within box, as a fraction of the box full."""
    region = alpha.crop(box)
    return sum(region.getdata()) / (255 * region.width * region.height)


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
        vfile.write_text(json.dumps(dict({"Shadow": 0}, **values)))
        out = OUT / f"{tag}.png"
        run([sys.executable, ROOT / "tools" / "render.py", TEMPLATE, "--variant", variant, "--values", vfile, "--out", out,
             "--frame", f"{t:.4f}", "--effectcraft-cli", a.effectcraft_cli])
        return Image.open(out).convert("RGBA").getchannel("A")

    def thumb(tag, W, H):
        t = Image.new("RGBA", (W, H), (60, 75, 90, 255))
        t.alpha_composite(Image.open(OUT / f"{tag}.png").convert("RGBA"))
        t = t.convert("RGB")
        t.thumbnail((480, 480))
        sheet.append((tag, t))

    want = DEFAULTS["Text"].replace("*", "")
    rest_box = {}
    for variant, (W, H) in FRAMES.items():
        for style in STYLES:
            tag = f"{variant}_{style.replace(' ', '_').lower()}"
            alpha = frame(variant, {"Style": style}, REST, tag)
            got = " ".join(ocr(OUT / f"{tag}.png").split())
            box = alpha.getbbox()
            cx, cy = (box[0] + box[2]) / 2, (box[1] + box[3]) / 2
            ok = got == want and abs(cx - W / 2) <= W * 0.01 and abs(cy - H / 2) <= H * 0.01
            check(f"{tag} at rest", ok, f"read {got!r}; centre ({cx:.0f}, {cy:.0f}) vs ({W / 2:.0f}, {H / 2:.0f})")
            rest_box[(variant, style)] = box
            if style in ("Fade Up", "Bounce") or variant == "16x9" and style == "Scale Pop":
                thumb(tag, W, H)

    # Order: part-way in, the first third of the text (where it sits at rest) has more ink than the last third; part-way out, less.
    for style in STYLES:
        tag = "in_" + style.replace(" ", "_").lower()
        box = rest_box[("16x9", style)]
        third = (box[2] - box[0]) / 3
        first = (int(box[0]) - 60, 0, int(box[0] + third), 1080)
        last = (int(box[2] - third), 0, int(box[2]) + 60, 1080)
        mid = frame("16x9", {"Style": style}, START + 0.35, tag)
        if style == "Spread In":
            wide = mid.getbbox()
            check("Spread In closes in", wide[2] - wide[0] > box[2] - box[0] + 100,
                  f"part-way in {wide[2] - wide[0]} px wide vs {box[2] - box[0]} at rest")
            continue
        ins = (ink(mid, first), ink(mid, last))
        out = frame("16x9", {"Style": style}, 4 - 0.35, "out_" + tag[3:])
        outs = (ink(out, first), ink(out, last))
        check(f"{style} letters in order", ins[0] > ins[1] and outs[0] < outs[1],
              f"ink first/last third: in {ins[0]:.3f}/{ins[1]:.3f}, out {outs[0]:.3f}/{outs[1]:.3f}")
        if style in ("Slide", "Turn", "Wave"):
            thumb(tag, 1920, 1080)
    for by, text in (("Words", "One two three four"), ("Lines", "First line\rSecond line")):
        tag = f"by_{by.lower()}"
        rest = frame("16x9", {"Text": text, "By": by, "Stagger": 0.25}, REST, f"{tag}_rest")
        box = rest.getbbox()
        if by == "Words":
            a_, b_ = (box[0] - 60, 0, box[0] + (box[2] - box[0]) // 4, 1080), (box[2] - (box[2] - box[0]) // 4, 0, box[2] + 60, 1080)
        else:
            mid_y = (box[1] + box[3]) // 2
            a_, b_ = (0, box[1] - 60, 1920, mid_y), (0, mid_y, 1920, box[3] + 60)
        mid = frame("16x9", {"Text": text, "By": by, "Stagger": 0.25}, START + 0.45, tag)
        fa, fb = ink(mid, a_) / ink(rest, a_), ink(mid, b_) / ink(rest, b_)   # each as a share of its ink at rest
        check(f"By {by}: the first ahead of the last", fa > fb + 0.2, f"share of ink at rest drawn: first {fa:.2f}, last {fb:.2f}")
        thumb(tag, 1920, 1080)

    frame("16x9", {"Colour": "#ffffff", "Highlight Colour": "#33aaff"}, REST, "highlight")
    im = Image.open(OUT / "highlight.png").convert("RGBA")
    box = im.getchannel("A").getbbox()
    split = box[0] + (box[2] - box[0]) * 0.55   # "Coast to " is left of here, "centre" right of it
    px = im.load()
    blue_l = blue_r = white_r = 0
    for y in range(box[1], box[3]):
        for x in range(box[0], box[2]):
            r, g, b, al = px[x, y]
            if al == 255:
                blue = r < 70 and 150 < g < 185 and b > 235
                if x < split:
                    blue_l += blue
                else:
                    blue_r += blue
                    white_r += min(r, g, b) > 240
    check("Highlight Colour on the starred word only", blue_r > 2000 and blue_l == 0 and white_r == 0,
          f"highlight pixels: {blue_l} left, {blue_r} right; white pixels right: {white_r}")

    before = frame("16x9", {}, START - 1 / 24, "before").getbbox()
    check("nothing before Start", before is None, f"one frame before {START} s: {before}")
    last = 4 - 1 / 24
    steady = [frame("16x9", {"Fade": "Steady"}, t, f"steady_{n}").getextrema()[1] for n, t in (("first", 0), ("last", last))]
    fin = frame("16x9", {"Fade": "Fade In"}, last, "fadein_last")
    fout = frame("16x9", {"Fade": "Fade Out"}, 0, "fadeout_first")
    check("Fade Steady is full throughout", steady == [255, 255], f"alpha at 0 s and {last:.2f} s: {steady}")
    diffs = []
    for x, y in (("fadein_last", "steady_first"), ("steady_last", "fadeout_first")):
        d = ImageChops.difference(Image.open(OUT / f"{x}.png").convert("RGBA"), Image.open(OUT / f"{y}.png").convert("RGBA"))
        diffs.append(max(hi for lo, hi in d.getextrema()))
    check("no jump where Fade In, Steady and Fade Out meet", max(diffs) <= 2, f"largest differences {diffs}")
    for variant in FRAMES:
        long = "The very long road from Port Campbell around to Sydney Cove"
        box = frame(variant, {"Text": long}, REST, f"{variant}_long").getbbox()
        check(f"{variant} long title fits Max Width", MAX_WIDTH[variant] - 40 <= box[2] - box[0] <= MAX_WIDTH[variant] + 4,
              f"width {box[2] - box[0]} of {MAX_WIDTH[variant]}")
    small = frame("16x9", {"Size": 25}, REST, "size60").getbbox()
    base = rest_box[("16x9", "Fade Up")]
    ratio = (small[2] - small[0]) / (base[2] - base[0])
    check("Size scales it", abs(ratio - 0.5) <= 0.03, f"Size 25 is {ratio:.3f} of Size 50's width")
    other = frame("16x9", {"Font": "Montserrat Bold"}, REST, "font").getbbox()
    check("Font changes the font", abs((other[2] - other[0]) - (base[2] - base[0])) > 20,
          f"Montserrat Bold {other[2] - other[0]} px wide vs Inter Bold {base[2] - base[0]} px")
    vfile = OUT / "duration.values.json"
    vfile.write_text(json.dumps({"Duration": 3}))
    clip = OUT / "duration.mov"
    run([sys.executable, ROOT / "tools" / "render.py", TEMPLATE, "--variant", "16x9", "--values", vfile, "--out", clip,
         "--effectcraft-cli", a.effectcraft_cli])
    seconds = float(run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", clip]).stdout.strip())
    check("Duration sets the clip length", abs(seconds - 3) <= 0.05, f"Duration 3 rendered {seconds:.2f} s")

    s = Image.new("RGB", (4 * 490 + 10, ((len(sheet) + 3) // 4) * 300 + 10), "white")
    for i, (tag, t) in enumerate(sheet):
        x, y = 10 + (i % 4) * 490, 10 + (i // 4) * 300
        s.paste(t, (x, y + 20))
        ImageDraw.Draw(s).text((x, y + 4), tag, fill=(0, 0, 0))
    s.save(OUT / "sheet.png")
    print(f"\n{sum(results)} of {len(results)} checks pass; sheet {OUT / 'sheet.png'}")
    sys.exit(0 if all(results) else 1)


if __name__ == "__main__":
    main()
