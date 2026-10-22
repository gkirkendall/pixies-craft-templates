#!/usr/bin/env python3
"""Test for Glint Set. Free: no GPU.

  python3 effectcraft/overlays/glint_set/effectcraft-0.13/tests/run.py --effectcraft-cli PATH

Renders single frames (transparent PNG) in each size at Spread 100 (default) and 60. For each of the six glints (where and when
build.py places them): nothing at its point one frame before its start, something one frame after (the start within one frame), and
at its peak its centre within 1 % of the frame of where it belongs. At 1.4 s, nothing is drawn away from the glints' places. Results
go to tests/out/ with a contact sheet.
"""
import argparse
import importlib.util
import json
import pathlib
import subprocess
import sys

from PIL import Image, ImageDraw

HERE = pathlib.Path(__file__).resolve().parent
TEMPLATE = HERE.parent
ROOT = next(p for p in TEMPLATE.parents if (p / "tools" / "render.py").is_file())
OUT = HERE / "out"
spec = importlib.util.spec_from_file_location("glint_set_build", TEMPLATE / "build" / "build.py")
build = importlib.util.module_from_spec(spec)
spec.loader.exec_module(build)


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

    size = build.SIZE
    for variant, (W, H) in build.VARIANTS.items():
        for spread in (100, 60):
            values = {"Spread": spread}
            places = []
            for gx, gy, start, rel in build.GLINTS:
                dx, dy = build.where(variant, gx, gy)
                places.append((W / 2 + dx * spread / 100, H / 2 + dy * spread / 100, size * rel * 0.8))
            for i, (gx, gy, start, rel) in enumerate(build.GLINTS):
                px, py, r = places[i]
                tag = f"{variant}_s{spread}_g{i + 1}"
                win = (int(px - r), int(py - r), int(px + r), int(py + r))
                # Before its start: nothing in its window, leaving out the other glints' places (they can overlap at a small Spread).
                others = Image.new("L", (W, H), 255)
                for j, (ox, oy, orad) in enumerate(places):
                    if j != i:
                        ImageDraw.Draw(others).ellipse((ox - orad, oy - orad, ox + orad, oy + orad), fill=0)
                early = frame(variant, values, start - 1 / 24, f"{tag}_before")
                before = Image.composite(early, Image.new("L", (W, H), 0), others).crop(win).getbbox()
                after = frame(variant, values, start + 1 / 24, f"{tag}_after").crop(win).getbbox()
                peak = frame(variant, values, start + 0.25, f"{tag}_peak").crop(win)
                pts = [(x, y) for y in range(peak.height) for x in range(peak.width) if peak.getpixel((x, y)) > 128]
                if pts:
                    cx, cy = win[0] + sum(p[0] for p in pts) / len(pts), win[1] + sum(p[1] for p in pts) / len(pts)
                    err = max(abs(cx - px) / W, abs(cy - py) / H) * 100
                else:
                    cx = cy = err = float("nan")
                check(f"{tag}", before is None and after is not None and err <= 1,
                      f"start {start} s: empty before {before is None}, shown after {after is not None}; "
                      f"centre ({cx:.0f}, {cy:.0f}) vs ({px:.0f}, {py:.0f}): {err:.2f} %")
            # Away from the glints' places nothing is drawn (1.4 s: four glints are showing).
            alpha = frame(variant, values, 1.4, f"{variant}_s{spread}_all")
            mask = Image.new("L", alpha.size, 255)
            for px, py, r in places:
                ImageDraw.Draw(mask).ellipse((px - r, py - r, px + r, py + r), fill=0)
            stray = Image.composite(alpha, Image.new("L", alpha.size, 0), mask).getbbox()
            check(f"{variant} Spread {spread}: transparent away from the glints", stray is None, f"drawn elsewhere: {stray}")
            img = Image.open(OUT / f"{variant}_s{spread}_all.png").convert("RGBA")
            bg = Image.new("RGBA", img.size, (40, 50, 60, 255))
            bg.alpha_composite(img)
            t = bg.convert("RGB")
            t.thumbnail((480, 480))
            sheet.append((f"{variant} Spread {spread}", t))

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
