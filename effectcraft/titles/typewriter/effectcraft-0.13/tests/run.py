#!/usr/bin/env python3
"""Test for Typewriter. Free: no GPU; reads the text back with tesseract (brew install tesseract).

  python3 effectcraft/titles/typewriter/effectcraft-0.13/tests/run.py --effectcraft-cli PATH

Renders single transparent frames, with the shadow off. Checks, in both sizes: once typed, the text reads back (OCR) exactly
and the line is centred on Position (within 1 %); part-way, OCR reads exactly the letters typed by then (Start + n / Speed), and
their left edge is where the finished line's is. In 16x9: nothing before Start without a cursor; with the Bar cursor, a bar is
drawn while typing, and once typed it is on and off in turn (on in the first half of each second, off in the second); the
Underscore cursor sits on the baseline; with Erase, the text is partly deleted near the end and gone by 0.3 s before Duration; a
long line shrinks to Max Width; Colour colours the text; Duration sets the clip's length. Results go to tests/out/ with a sheet.
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
MAX_WIDTH = {"16x9": 1651, "9x16": 929}
TEXT, START, SPEED = DEFAULTS["Text"], DEFAULTS["Start"], DEFAULTS["Speed"]
DONE = START + len(TEXT) / SPEED + 0.1


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
        return " ".join(run(["tesseract", src, "-", "--psm", "7"]).stdout.split())
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

    none = {"Cursor": "None"}
    for variant, (W, H) in FRAMES.items():
        tag = f"{variant}_typed"
        full = frame(variant, none, DONE, tag).getbbox()
        got = ocr(OUT / f"{tag}.png")
        cx, cy = (full[0] + full[2]) / 2, (full[1] + full[3]) / 2
        check(f"{tag}", got == TEXT and abs(cx - W / 2) <= W * 0.01 and abs(cy - H / 2) <= H * 0.01,
              f"read {got!r}; centre ({cx:.0f}, {cy:.0f}) vs ({W / 2:.0f}, {H / 2:.0f})")
        thumb(tag, W, H)
        for n in (4, 15):
            tag = f"{variant}_part{n}"
            part = frame(variant, none, START + (n + 0.5) / SPEED, tag).getbbox()
            got = ocr(OUT / f"{tag}.png")
            check(f"{tag}", got == TEXT[:n].strip() and abs(part[0] - full[0]) <= 2,
                  f"read {got!r} (expected {TEXT[:n].strip()!r}); left edge {part[0]} vs {full[0]} finished")
        thumb(f"{variant}_part15", W, H)

    before = frame("16x9", none, START - 1 / 24, "before").getbbox()
    check("nothing before Start (no cursor)", before is None, f"one frame before {START} s: {before}")
    text_box = frame("16x9", none, START + 10.5 / SPEED, "bar_ref").getbbox()
    typing = frame("16x9", {}, START + 10.5 / SPEED, "bar_typing").getbbox()
    check("Bar cursor drawn while typing", typing[2] > text_box[2] + 5, f"drawn to x {typing[2]} vs text to {text_box[2]}")
    on = frame("16x9", {}, 3.25, "bar_on").getbbox()
    off = frame("16x9", {}, 3.75, "bar_off").getbbox()
    done = frame("16x9", none, 3.25, "bar_none").getbbox()
    check("Bar cursor blinks once typed", on[2] > off[2] + 5 and abs(off[2] - done[2]) <= 2,
          f"right edge at 3.25 s {on[2]} (on), at 3.75 s {off[2]} (off), the text alone {done[2]}")
    thumb("bar_on", 1920, 1080)
    under = frame("16x9", {"Cursor": "Underscore"}, 3.25, "underscore")
    ub = under.crop((off[2] + 2, 0, 1920, 1080)).getbbox()
    check("Underscore cursor on the baseline", ub is not None and ub[3] - ub[1] < 20 and ub[3] >= off[3] - 30,
          f"cursor box {ub}; text bottom {off[3]}")
    erase = {"Cursor": "None", "Erase": True, "Duration": 5}
    te = 5 - 0.3 - len(TEXT) / (2 * SPEED)
    mid = frame("16x9", erase, te + 10.5 / (2 * SPEED), "erase_mid")
    got = ocr(OUT / "erase_mid.png")
    gone = frame("16x9", erase, 5 - 0.25, "erase_gone").getbbox()
    check("Erase deletes it again", got == TEXT[:len(TEXT) - 10].strip() and gone is None,
          f"part-way read {got!r} (expected {TEXT[:len(TEXT) - 10].strip()!r}); 0.25 s before Duration: {gone}")
    long = "The very long road from Port Campbell all the way around to Sydney Cove"
    lb = frame("16x9", dict(none, Text=long), START + len(long) / SPEED + 0.2, "long").getbbox()
    check("a long line fits Max Width", MAX_WIDTH["16x9"] - 40 <= lb[2] - lb[0] <= MAX_WIDTH["16x9"] + 4,
          f"width {lb[2] - lb[0]} of {MAX_WIDTH['16x9']}")
    frame("16x9", dict(none, Colour="#ffcc00"), DONE, "colour")
    im = Image.open(OUT / "colour.png").convert("RGBA")
    solid = [p[:3] for p in im.getdata() if p[3] == 255]
    mean = [sum(c[i] for c in solid) / len(solid) for i in range(3)] if solid else [0, 0, 0]
    check("Colour colours the text", all(abs(m - w) <= 6 for m, w in zip(mean, (255, 204, 0))), f"solid pixels average {[round(m) for m in mean]}")
    def still(values, tag):
        frame("16x9", values, DONE, tag)
        return Image.open(OUT / f"{tag}.png")
    for name, ok, detail in font_checks(still, {"Font": []}, {"Cursor": "None"}):
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
