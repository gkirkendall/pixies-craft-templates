#!/usr/bin/env python3
"""Test for Title. Free: no GPU; reads the text back with tesseract (brew install tesseract).

  python3 effectcraft/titles/title/effectcraft-0.13/tests/run.py --effectcraft-cli PATH

Renders single transparent frames, with the shadow off, in both sizes. Checks: for every Place, the text reads back (OCR) as
supplied (the label in capitals; spaces are not compared, as the label is spaced out), there are two bands of text (label, title),
and the block sits Margin from the edges that Place names (within 12 px: the font's side bearings; a bottom block's baseline is on Margin, so a descender may hang below it) or centred (within 1 %); an
empty label closes up (one band, still Margin from the bottom); a long title shrinks to Max Width. Then: nothing before Start;
half-way through the fade in it is fainter and lower; each Fade item shows the title (none, full, faded) at the first, middle and
last frame as it should, and where Fade In, Steady and Fade Out clips meet it is identical; Colour colours the text; Shadow 50
draws a shadow; Duration sets the clip's length. Results go to tests/out/ with a contact sheet.
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
sys.path.insert(0, str(ROOT / "tools"))
from fontcheck import font_checks  # noqa: E402
OUT = HERE / "out"
MANIFEST = json.loads((TEMPLATE / "template.json").read_text())
DEFAULTS = {c["name"]: c.get("default") for c in MANIFEST["controls"]}
PLACES = next(c["options"] for c in MANIFEST["controls"] if c["name"] == "Place")
FRAMES = {"16x9": (1920, 1080), "9x16": (1080, 1920)}
MARGIN = {"16x9": 96, "9x16": 80}
MAX_WIDTH = {"16x9": 1651, "9x16": 929}
PEAK, SIDE = 2.0, 12
EXTRA = {"16x9": (0, 0), "9x16": (1920 * 0.083, 1080 * 0.13)}   # Extra Vertical, Extra Right in pixels: 8.3 % of the height, 13 % of the width
DESCENDER = 40   # a bottom block ends at the title's baseline, so a descender may hang this far below Margin


def run(cmd, check=True):
    r = subprocess.run([str(c) for c in cmd], capture_output=True, text=True)
    if check and r.returncode:
        sys.exit(f"failed: {' '.join(map(str, cmd))}\n{r.stderr or r.stdout}")
    return r


def bands(alpha):
    """Runs of rows with anything drawn: [(top, bottom)]."""
    w, h = alpha.size
    rows = [alpha.crop((0, y, w, y + 1)).getbbox() is not None for y in range(h)]
    out, start = [], None
    for y, on in enumerate(rows + [False]):
        if on and start is None:
            start = y
        elif not on and start is not None:
            out.append((start, y))
            start = None
    return out


def ocr(png):
    """The text as tesseract reads it, one band of text at a time (the small spaced-out label is missed when read with the title),
    white on transparent made black on white and enlarged."""
    im = Image.open(png).convert("RGBA")
    bg = Image.new("RGBA", im.size, (0, 0, 0, 255))
    bg.alpha_composite(im)
    alpha = im.getchannel("A")
    out = []
    for n, (top, bottom) in enumerate(bands(alpha)):
        box = alpha.crop((0, top, im.width, bottom)).getbbox()
        g = bg.convert("L").crop((box[0] - 30, top - 30, box[2] + 30, bottom + 30)).point(lambda v: 255 - v)
        k = max(2, round(120 / (bottom - top)))
        g = g.resize((g.width * k, g.height * k))
        src = png.with_suffix(f".ocr{n}.png")
        g.save(src)
        try:
            out.append(run(["tesseract", src, "-", "--psm", "7"]).stdout)
        except FileNotFoundError:
            sys.exit("tesseract is needed to read the text back: brew install tesseract (or your system's package)")
    return " ".join(out)


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
        return Image.open(out).convert("RGBA").getchannel("A")

    def placed(tag, variant, place, box):
        """Whether box sits where Place puts it: Margin from the named edges, else centred."""
        W, H = FRAMES[variant]
        m = MARGIN[variant]
        ev, er = EXTRA[variant]   # the 9x16 defaults keep a title clear of a phone's controls
        cx, cy = (box[0] + box[2]) / 2, (box[1] + box[3]) / 2
        horiz = (abs(box[0] - m) <= SIDE if "Left" in place else abs(W - m - er - box[2]) <= SIDE if "Right" in place
                 else abs(cx - W / 2) <= W * 0.01)
        vert = (abs(box[1] - m - ev) <= SIDE if "Top" in place else -SIDE <= box[3] - (H - m - ev) <= DESCENDER if "Bottom" in place
                else abs(cy - (H - ev) / 2) <= H * 0.01)
        return horiz and vert

    squash = lambda s: "".join(s.split())
    for variant, (W, H) in FRAMES.items():
        for place in PLACES:
            tag = f"{variant}_{place.replace(' ', '_').lower()}"
            alpha = frame(variant, {"Place": place, "Shadow": 0}, PEAK, tag)
            want = DEFAULTS["Label"].upper() + DEFAULTS["Title"]
            got = ocr(OUT / f"{tag}.png")
            check(f"{tag} text", squash(got) == squash(want), f"read {' '.join(got.split())!r}")
            box, found = alpha.getbbox(), bands(alpha)
            check(f"{tag} place", len(found) == 2 and placed(tag, variant, place, box),
                  f"{len(found)} bands; drawn {box} in {W}x{H}, Margin {MARGIN[variant]}")
            if variant == "16x9" or place == "Centre":
                t = Image.new("RGBA", (W, H), (60, 75, 90, 255))
                t.alpha_composite(Image.open(OUT / f"{tag}.png").convert("RGBA"))
                t = t.convert("RGB")
                t.thumbnail((480, 480))
                sheet.append((tag, t))
        tag = f"{variant}_no_label"
        alpha = frame(variant, {"Label": "", "Place": "Bottom Right", "Shadow": 0}, PEAK, tag)
        box, found = alpha.getbbox(), bands(alpha)
        check(f"{tag}", len(found) == 1 and placed(tag, variant, "Bottom Right", box)
              and squash(ocr(OUT / f"{tag}.png")) == squash(DEFAULTS["Title"]), f"{len(found)} band; drawn {box}")
        tag = f"{variant}_long"
        long = "The very long road from Port Campbell around to Sydney Cove"
        alpha = frame(variant, {"Title": long, "Shadow": 0}, PEAK, tag)
        box = alpha.getbbox()
        check(f"{tag} fits Max Width", box[2] - box[0] <= MAX_WIDTH[variant] + 4 and box[2] - box[0] >= MAX_WIDTH[variant] - 40,
              f"width {box[2] - box[0]} of {MAX_WIDTH[variant]}")

    v = {"Shadow": 0}
    before = frame("16x9", v, 0.3 - 1 / 24, "fade_before").getbbox()
    check("nothing before Start", before is None, f"one frame before 0.3 s: {before}")
    mid, peak = frame("16x9", v, 0.3 + 0.3, "fade_mid"), frame("16x9", v, PEAK, "fade_peak")
    check("fades and rises in", 0 < mid.getextrema()[1] < peak.getextrema()[1] and mid.getbbox()[1] > peak.getbbox()[1],
          f"half-way: alpha {mid.getextrema()[1]}, top {mid.getbbox()[1]}; once in: {peak.getextrema()[1]}, top {peak.getbbox()[1]}")
    last = 4 - 1 / 24
    want = {"Fade In and Out": ("none", "full", "faded"), "Fade In": ("none", "full", "full"),
            "Steady": ("full", "full", "full"), "Fade Out": ("full", "full", "faded")}
    is_ = {"none": lambda x: x == 0, "full": lambda x: x >= 250, "faded": lambda x: x < 0.2 * 255}
    for fade, kinds in want.items():
        tag = "fade_" + fade.replace(" ", "_").lower()
        got = [frame("16x9", dict(v, Fade=fade, Duration=4), t, f"{tag}_{n}").getextrema()[1]
               for n, t in (("first", 0), ("mid", PEAK), ("last", last))]
        check(f"Fade {fade}", all(is_[k](g) for k, g in zip(kinds, got)), f"alpha at 0 s, {PEAK} s, {last:.2f} s: {got} (expected {kinds})")
    for x, y in (("fade_fade_in_last", "fade_steady_first"), ("fade_steady_last", "fade_fade_out_first")):
        diff = ImageChops.difference(Image.open(OUT / f"{x}.png").convert("RGBA"), Image.open(OUT / f"{y}.png").convert("RGBA"))
        worst = max(hi for lo, hi in diff.getextrema())
        check(f"no jump: {x[5:]} to {y[5:]}", worst <= 2, f"largest difference {worst} of 255")
    frame("16x9", dict(v, Colour="#ffcc00"), PEAK, "colour")
    im = Image.open(OUT / "colour.png").convert("RGBA")
    solid = [p[:3] for p in im.getdata() if p[3] == 255]
    mean = [sum(c[i] for c in solid) / len(solid) for i in range(3)] if solid else [0, 0, 0]
    check("Colour colours the text", all(abs(m - w) <= 6 for m, w in zip(mean, (255, 204, 0))), f"solid pixels average {[round(m) for m in mean]}")
    frame("16x9", {}, PEAK, "shadow")
    im = Image.open(OUT / "shadow.png").convert("RGBA")
    dark = sum(1 for p in im.getdata() if 0 < p[3] and max(p[:3]) < 60)
    check("Shadow 50 draws a shadow", dark > 1000, f"{dark} dark pixels")
    def still(values, tag):
        frame("16x9", values, PEAK, tag)
        return Image.open(OUT / f"{tag}.png")
    for name, ok, detail in font_checks(still, {"Title Font": ["Title"], "Label Font": ["Label"]}):
        check(name, ok, detail)
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
