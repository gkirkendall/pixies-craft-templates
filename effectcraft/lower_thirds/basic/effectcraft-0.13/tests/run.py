#!/usr/bin/env python3
"""Test for Basic Lower Third. Free: no GPU.

  python3 effectcraft/lower_thirds/basic/effectcraft-0.13/tests/run.py --effectcraft-cli PATH

Renders the default and the long example in both sizes as ProRes 4444 and checks: transparent outside the bar; empty at the first
and last frames; in place by frame 12 (0.5 s) and unchanged from there to frame 84 (3.5 s); the bar holds both lines with its
padding and stays inside the frame. Results go to tests/out/ with a contact sheet; names are checked by eye there.
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
CASES = {"default": None, "long": TEMPLATE / "examples" / "long.values.json"}


def run(cmd):
    r = subprocess.run([str(c) for c in cmd], capture_output=True, text=True)
    if r.returncode:
        sys.exit(f"failed: {' '.join(map(str, cmd))}\n{r.stderr or r.stdout}")


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--effectcraft-cli", default="effectcraft-cli")
    a = ap.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    results, sheet = [], []

    def check(name, ok, detail):
        results.append(ok)
        print(("PASS " if ok else "FAIL ") + name + ": " + detail)

    for variant in ("16x9", "9x16"):
        for case, values in CASES.items():
            tag = f"{case}_{variant}"
            mov = OUT / f"{tag}.mov"
            cmd = [sys.executable, ROOT / "tools" / "render.py", TEMPLATE, "--variant", variant, "--out", mov, "--effectcraft-cli", a.effectcraft_cli]
            run(cmd + (["--values", values] if values else []))
            frames = OUT / tag
            frames.mkdir(exist_ok=True)
            run(["ffmpeg", "-v", "error", "-y", "-i", mov, "-pix_fmt", "rgba", frames / "%03d.png"])
            f = lambda n: Image.open(frames / f"{n + 1:03d}.png").convert("RGBA")
            last = len(list(frames.glob("*.png"))) - 1
            empty = [n for n in (0, last) if f(n).getchannel("A").getbbox() is None]
            check(f"{tag} empty at start and end", empty == [0, last], f"frames {empty} of 0 and {last} empty")
            held = ImageChops.difference(f(12), f(84)).getbbox() is None
            moving = ImageChops.difference(f(11), f(12)).getbbox() is not None
            check(f"{tag} timing", held and moving, f"frame 12 = frame 84: {held}; frame 11 still moving: {moving}")
            hold = f(48)
            alpha = hold.getchannel("A")
            box = alpha.point(lambda v: 255 if v > 200 else 0).getbbox()   # the bar (85 % opaque) and the text on it
            bar_only = alpha.point(lambda v: 255 if v > 0 else 0).getbbox()
            w, h = hold.size
            # Text: the white and light pixels of both lines must lie inside the bar with at least 40 px to spare at each end.
            px = hold.load()
            light = [(x, y) for y in range(box[1], box[3]) for x in range(box[0], box[2]) if px[x, y][3] > 200 and min(px[x, y][:3]) > 150]
            tx0, tx1 = min(p[0] for p in light), max(p[0] for p in light)
            check(f"{tag} bar holds the text", tx0 - box[0] >= 40 and box[2] - tx1 >= 40 and all(abs(i - j) <= 1 for i, j in zip(bar_only, box)) and box[2] <= w,
                  f"bar x {box[0]}–{box[2]} of {w}, text x {tx0}–{tx1}; nothing outside the bar (1 px edge allowed): {all(abs(i - j) <= 1 for i, j in zip(bar_only, box))}")
            bg = Image.new("RGBA", hold.size, (90, 110, 90, 255))
            bg.alpha_composite(hold)
            t = bg.convert("RGB")
            t.thumbnail((640, 640))
            sheet.append((tag, t))
    def still(values, tag):
        vfile = OUT / f"{tag}.values.json"
        vfile.write_text(json.dumps(values))
        run([sys.executable, ROOT / "tools" / "render.py", TEMPLATE, "--variant", "16x9", "--values", vfile, "--out", OUT / f"{tag}.png",
             "--frame", "2.0", "--effectcraft-cli", a.effectcraft_cli])
        return Image.open(OUT / f"{tag}.png")
    for name, ok, detail in font_checks(still, {"Title Font": ["Title"], "Subtitle Font": ["Subtitle"]}):
        check(name, ok, detail)
    s = Image.new("RGB", (sum(t.width for _, t in sheet) + 10 * (len(sheet) + 1), max(t.height for _, t in sheet) + 40), "white")
    x = 10
    for tag, t in sheet:
        s.paste(t, (x, 30))
        ImageDraw.Draw(s).text((x, 8), tag, fill=(0, 0, 0))
        x += t.width + 10
    s.save(OUT / "sheet.png")
    print(f"\n{sum(results)} of {len(results)} checks pass; sheet {OUT / 'sheet.png'}")
    sys.exit(0 if all(results) else 1)


if __name__ == "__main__":
    main()
