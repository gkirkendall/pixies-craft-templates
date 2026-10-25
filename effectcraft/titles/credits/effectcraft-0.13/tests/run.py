#!/usr/bin/env python3
"""Test for Credits. Free: no GPU; reads the text back with tesseract (brew install tesseract).

  python3 effectcraft/titles/credits/effectcraft-0.13/tests/run.py --effectcraft-cli PATH

Renders single transparent frames, with the shadow off so lines are cleanly apart, in both sizes, for: the defaults (three lines),
four lines, five lines, Line 1 empty, Line 2 empty, a long title and a long line, a moved Position, and no title. Checks for each: the text reads back
(OCR) exactly as supplied (a curly quote may read as straight), with the title in capitals between quotes; the bands of text are as many as the lines (no overlaps);
every line fits Max Width; the block is centred on Position (within 1 % across, 2 % down). Then: nothing before Start; half-way
through the fade in it is fainter and lower; nearly gone one frame before Duration; Colour colours the text; Shadow 50 draws a
shadow. Results go to tests/out/ with a contact sheet.
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
DEFAULTS = {c["name"]: c.get("default") for c in MANIFEST["controls"]}
FRAMES = {"16x9": (1920, 1080), "9x16": (1080, 1920)}
POSITION = {"16x9": [960, 470], "9x16": [540, 800]}
MAX_WIDTH = {"16x9": 1651, "9x16": 929}
LONG_TITLE = "The very long road from Port Campbell all the way around to Sydney Cove"
CASES = {"default": {}, "four_lines": {"Line 4": "Natural Earth"},
         "five_lines": {"Line 4": "Natural Earth", "Line 5": "Made with craft-templates · github.com/example/craft-templates"}, "no_line1": {"Line 1": ""}, "no_line2": {"Line 2": ""},
         "long": {"Title": LONG_TITLE, "Line 1": "Photos and video by someone with a rather long name, and a long line it is", "Max Width": 86},
         "moved": {"Title": "Short", "Position": "moved"}, "no_title": {"Title": ""}}
PEAK = 2.0
QUOTES = str.maketrans({"\u201c": '"', "\u201d": '"', "\u00b7": "-"})   # OCR reads · as -


def run(cmd):
    r = subprocess.run([str(c) for c in cmd], capture_output=True, text=True)
    if r.returncode:
        sys.exit(f"failed: {' '.join(map(str, cmd))}\n{r.stderr or r.stdout}")
    return r.stdout


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
    """The text as tesseract reads it, white text on black made black on white and doubled in size."""
    im = Image.open(png).convert("RGBA")
    bg = Image.new("RGBA", im.size, (0, 0, 0, 255))
    bg.alpha_composite(im)
    g = bg.convert("L").point(lambda v: 255 - v)
    g = g.resize((g.width * 2, g.height * 2))
    src = png.with_suffix(".ocr.png")
    g.save(src)
    try:
        return run(["tesseract", src, "-", "--psm", "6"])
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
        return Image.open(out).convert("RGBA").getchannel("A")

    for variant, (W, H) in FRAMES.items():
        for case, extra in CASES.items():
            tag = f"{variant}_{case}"
            values = dict(extra, Shadow=0)
            pos = POSITION[variant]
            if values.get("Position") == "moved":
                pos = [W * 0.4, H * 0.3]
                values["Position"] = pos
            alpha = frame(variant, values, PEAK, tag)
            text = {k: values.get(k, DEFAULTS[k]) for k in ("Title", "Line 1", "Line 2", "Line 3", "Line 4", "Line 5")}
            lines = [x for x in (text[f"Line {i}"] for i in range(1, 6)) if x]
            want = " ".join((["“" + text["Title"].upper() + "”"] if text["Title"] else []) + lines)
            read = ocr(OUT / f"{tag}.png")
            got = " ".join(read.split())
            same = lambda s: s.translate(QUOTES)   # OCR reads a curly quote as straight now and then, and · as -; they must still be there
            check(f"{tag} text", same(got) == same(want), f"read {got!r}" + ("" if got == want else f", expected {want!r}"))
            title_lines = 0 if not text["Title"] else 2 if len(text["Title"]) * 0.37 * (150 if variant == "16x9" else 120) > MAX_WIDTH[variant] else 1
            found = bands(alpha)
            box = alpha.getbbox()
            cx, cy = (box[0] + box[2]) / 2, (box[1] + box[3]) / 2
            ok = (len(found) == title_lines + len(lines) and box[2] - box[0] <= MAX_WIDTH[variant] + 2
                  and abs(cx - pos[0]) <= W * 0.01 and abs(cy - pos[1]) <= H * 0.02)
            check(f"{tag} layout", ok, f"{len(found)} bands of text for {title_lines} title + {len(lines)} lines; "
                  f"width {box[2] - box[0]} of {MAX_WIDTH[variant]}; centre ({cx:.0f}, {cy:.0f}) vs ({pos[0]:.0f}, {pos[1]:.0f})")
            if variant == "16x9" or case == "long":
                t = Image.new("RGBA", (W, H), (60, 75, 90, 255))
                t.alpha_composite(Image.open(OUT / f"{tag}.png").convert("RGBA"))
                t = t.convert("RGB")
                t.thumbnail((480, 480))
                sheet.append((tag, t))

    v = {"Shadow": 0}
    before = frame("16x9", v, 0.3 - 1 / 24, "fade_before").getbbox()
    check("nothing before Start", before is None, f"one frame before 0.3 s: {before}")
    mid, peak = frame("16x9", v, 0.3 + 0.3, "fade_mid"), frame("16x9", v, PEAK, "fade_peak")
    check("fades and rises in", 0 < mid.getextrema()[1] < peak.getextrema()[1] and mid.getbbox()[1] > peak.getbbox()[1],
          f"half-way: opacity {mid.getextrema()[1]}, top {mid.getbbox()[1]}; once in: {peak.getextrema()[1]}, top {peak.getbbox()[1]}")
    end = frame("16x9", dict(v, Duration=4), 4 - 1 / 24, "fade_end").getextrema()[1]
    check("faded out by Duration", end < 0.2 * 255, f"one frame before Duration 4: alpha {end}")
    frame("16x9", dict(v, Colour="#ffcc00"), PEAK, "colour")
    im = Image.open(OUT / "colour.png").convert("RGBA")
    solid = [p[:3] for p in im.getdata() if p[3] == 255]
    mean = [sum(c[i] for c in solid) / len(solid) for i in range(3)] if solid else [0, 0, 0]
    check("Colour colours the text", all(abs(m - w) <= 6 for m, w in zip(mean, (255, 204, 0))), f"solid pixels average {[round(m) for m in mean]}")
    shadow = frame("16x9", {}, PEAK, "shadow")
    im = Image.open(OUT / "shadow.png").convert("RGBA")
    dark = sum(1 for p in im.getdata() if 0 < p[3] and max(p[:3]) < 60)
    check("Shadow 50 draws a shadow", dark > 1000 and shadow.getbbox()[3] > peak.getbbox()[3], f"{dark} dark pixels; "
          f"bottom {shadow.getbbox()[3]} vs {peak.getbbox()[3]} without")
    def still(values, tag):
        frame("16x9", values, PEAK, tag)
        return Image.open(OUT / f"{tag}.png")
    for name, ok, detail in font_checks(still, {"Title Font": ["Title"], "Line Font": ["Line 1", "Line 2", "Line 3", "Line 4", "Line 5"]}):
        check(name, ok, detail)

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
