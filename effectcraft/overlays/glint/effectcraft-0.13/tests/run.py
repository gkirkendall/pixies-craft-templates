#!/usr/bin/env python3
"""Test for Glint. Free: no GPU.

  python3 effectcraft/overlays/glint/effectcraft-0.13/tests/run.py --effectcraft-cli PATH

Renders single frames (transparent PNG) for two separately placed instances in each size, as one would stack several in a video.
Checks: empty one frame before Start and shown one frame after it (the start within one frame); at its peak the glint's centre is
on Position within 1 % of the frame and nothing is drawn away from it; gone by Start + 1.05 s; and the clip is Duration long.
Results go to tests/out/ with a contact sheet.
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
OUT = HERE / "out"
FRAMES = {"16x9": (1920, 1080), "9x16": (1080, 1920)}
CASES = {"16x9": [{"Position": [480, 300], "Start": 0.5, "Size": 50}, {"Position": [1500, 760], "Start": 1.25, "Size": 79}],
         "9x16": [{"Position": [300, 500], "Start": 0.5, "Size": 50}, {"Position": [800, 1400], "Start": 1.0, "Size": 71}]}


def run(cmd):
    r = subprocess.run([str(c) for c in cmd], capture_output=True, text=True)
    if r.returncode:
        sys.exit(f"failed: {' '.join(map(str, cmd))}\n{r.stderr or r.stdout}")
    return r.stdout


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

    for variant, cases in CASES.items():
        W, H = FRAMES[variant]
        for n, v in enumerate(cases):
            tag = f"{variant}_{n}"
            s, (px, py), size = v["Start"], v["Position"], v["Size"] * 2.8   # Size is a percent of 280 px
            before = frame(variant, v, s - 1 / 24, f"{tag}_before").getbbox()
            after = frame(variant, v, s + 1 / 24, f"{tag}_after").getbbox()
            check(f"{tag} starts at {s} s", before is None and after is not None, f"one frame before: {before}; one frame after: {after}")
            peak = frame(variant, v, s + 0.25, f"{tag}_peak")
            box = peak.getbbox()
            pts = [(x, y) for y in range(box[1], box[3]) for x in range(box[0], box[2]) if peak.getpixel((x, y)) > 128]
            cx, cy = sum(p[0] for p in pts) / len(pts), sum(p[1] for p in pts) / len(pts)
            err = max(abs(cx - px) / W, abs(cy - py) / H) * 100
            reach = max(abs(box[0] - px), abs(box[2] - px), abs(box[1] - py), abs(box[3] - py))
            check(f"{tag} at Position", err <= 1 and reach <= size * 0.8,
                  f"centre ({cx:.0f}, {cy:.0f}) vs ({px}, {py}): {err:.2f} % of the frame; drawn up to {reach} px from it (Size {size})")
            gone = frame(variant, v, s + 1.05, f"{tag}_gone").getbbox()
            check(f"{tag} gone after 1 s", gone is None, f"at {s + 1.05:.2f} s: {gone}")
            img = Image.open(OUT / f"{tag}_peak.png").convert("RGBA")
            bg = Image.new("RGBA", img.size, (40, 50, 60, 255))
            bg.alpha_composite(img)
            t = bg.convert("RGB")
            t.thumbnail((480, 480))
            sheet.append((tag, t))
    vfile = OUT / "duration.values.json"
    vfile.write_text(json.dumps({"Duration": 2.5}))
    clip = OUT / "duration.mov"
    run([sys.executable, ROOT / "tools" / "render.py", TEMPLATE, "--variant", "16x9", "--values", vfile, "--out", clip,
         "--effectcraft-cli", a.effectcraft_cli])
    seconds = float(run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", clip]).strip())
    check("Duration sets the clip length", abs(seconds - 2.5) <= 0.05, f"Duration 2.5 rendered {seconds:.2f} s")

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
