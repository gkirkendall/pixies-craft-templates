#!/usr/bin/env python3
"""Test for Corner Logo. Free: no GPU.

  python3 effectcraft/logos/corner_logo/effectcraft-0.13/tests/run.py --effectcraft-cli PATH

Draws test logos (a wide 3:1, a tall 1:3, an empty picture) and renders single transparent frames. Checks: in each size and each
corner, the logo fits its Size box at Margin from that corner (within 2 px) and nothing is drawn outside the box; a tall logo
fits on its height; Size and Margin move the box; nothing shows one frame before Start; half-way through the fade in it is
fainter and lower than once in; once in, its opacity is Opacity; it has nearly faded out one frame before Duration; no logo
draws nothing; each Fade item shows the logo (none, full, faded) at the first, middle and last frame as it should, and where
Fade In, Steady and Fade Out clips meet the logo is identical (no jump at a cut); a Corner name that is not one of the four is
refused by tools/render.py; Duration sets the clip's length.
Results go to tests/out/ with a contact sheet.
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
FRAMES = {"16x9": (1920, 1080), "9x16": (1080, 1920)}
CORNERS = ["Top Left", "Top Right", "Bottom Right", "Bottom Left"]
SIZE, MARGIN, OPACITY, START = 180, 60, 90, 0.3
PEAK = 2.0


def run(cmd, check=True):
    r = subprocess.run([str(c) for c in cmd], capture_output=True, text=True)
    if check and r.returncode:
        sys.exit(f"failed: {' '.join(map(str, cmd))}\n{r.stderr or r.stdout}")
    return r


def logos():
    """Test logos: solid, so the fitted rectangle is the drawn one."""
    wide = Image.new("RGBA", (600, 200), (200, 40, 40, 255))
    ImageDraw.Draw(wide).rectangle((0, 0, 599, 199), outline=(255, 255, 255, 255), width=8)
    wide.save(OUT / "wide.png")
    wide.rotate(90, expand=True).save(OUT / "tall.png")
    Image.new("RGBA", (8, 8), (0, 0, 0, 0)).save(OUT / "empty.png")


EXTRA = {"16x9": (0, 0), "9x16": (1920 * 0.083, 1080 * 0.13)}   # Extra Vertical, Extra Right in pixels: 8.3 % of the height, 13 % of the width


def box(variant, corner, size=SIZE, margin=MARGIN):
    W, H = FRAMES[variant]
    right, bottom = corner in ("Top Right", "Bottom Right"), corner in ("Bottom Right", "Bottom Left")
    ev, er = EXTRA[variant]   # the 9x16 defaults keep a logo clear of a phone's controls
    x0 = W - margin - er - size if right else margin
    y0 = H - margin - ev - size if bottom else margin + ev
    return x0, y0, x0 + size, y0 + size


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--effectcraft-cli", default="effectcraft-cli")
    a = ap.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    logos()
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

    def fits(tag, variant, values, shape):
        """The drawn logo is the shape (w, h as fractions of the box) centred in its box, within 2 px."""
        alpha = frame(variant, values, PEAK, tag)
        size, margin = values["Size"] * 3.6 if "Size" in values else SIZE, values.get("Margin", MARGIN)   # Size is a percent of 360 px
        x0, y0, x1, y1 = box(variant, values.get("Corner", "Bottom Right"), size, margin)
        cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
        want = (cx - size * shape[0] / 2, cy - size * shape[1] / 2, cx + size * shape[0] / 2, cy + size * shape[1] / 2)
        got = alpha.getbbox()
        off = max(abs(g - w) for g, w in zip(got, want)) if got else float("inf")
        check(tag, off <= 2, f"drawn {got}, expected {tuple(round(v) for v in want)} (out by {off:.1f} px)")
        return alpha

    for variant in FRAMES:
        for corner in CORNERS:
            tag = f"{variant}_{corner.replace(' ', '_').lower()}"
            fits(tag, variant, {"Logo": "wide.png", "Corner": corner}, (1, 1 / 3))
            if variant == "16x9":
                img = Image.open(OUT / f"{tag}.png").convert("RGBA")
                sheet.append(img)
        fits(f"{variant}_tall", variant, {"Logo": "tall.png", "Corner": "Top Left"}, (1 / 3, 1))
    fits("16x9_size300_margin20", "16x9", {"Logo": "wide.png", "Corner": "Top Right", "Size": 83.3, "Margin": 20}, (1, 1 / 3))

    v = {"Logo": "wide.png"}
    before = frame("16x9", v, START - 1 / 24, "fade_before").getbbox()
    check("nothing before Start", before is None, f"one frame before {START} s: {before}")
    mid, peak = frame("16x9", v, START + 0.25, "fade_mid"), frame("16x9", v, PEAK, "fade_peak")
    mid_a, peak_a = mid.getextrema()[1], peak.getextrema()[1]
    check("fades and rises in", 0 < mid_a < peak_a and mid.getbbox()[1] > peak.getbbox()[1],
          f"half-way: opacity {mid_a}, top {mid.getbbox()[1]}; once in: opacity {peak_a}, top {peak.getbbox()[1]}")
    check("Opacity 90 once in", abs(peak_a - 255 * OPACITY / 100) <= 3, f"alpha {peak_a} (expected {255 * OPACITY / 100:.0f})")
    half = frame("16x9", dict(v, Opacity=50), PEAK, "opacity50").getextrema()[1]
    check("Opacity 50", abs(half - 128) <= 3, f"alpha {half} (expected 128)")
    end = frame("16x9", dict(v, Duration=4), 4 - 1 / 24, "fade_end").getextrema()[1]
    check("faded out by Duration", end < 0.2 * peak_a, f"one frame before Duration 4: alpha {end}")
    empty = frame("16x9", {"Logo": "empty.png"}, PEAK, "empty").getbbox()
    check("no logo draws nothing", empty is None, f"drawn: {empty}")

    # Fade: the logo's strength at the first, middle and last frame of a 4 s clip, and the frames either side of each cut.
    full, last = round(255 * OPACITY / 100), 4 - 1 / 24
    want = {"Fade In and Out": ("none", "full", "faded"), "Fade In": ("none", "full", "full"),
            "Steady": ("full", "full", "full"), "Fade Out": ("full", "full", "faded")}
    is_ = {"none": lambda x: x == 0, "full": lambda x: abs(x - full) <= 3, "faded": lambda x: x < 0.2 * full}
    for fade, (w0, w1, w2) in want.items():
        tag = "fade_" + fade.replace(" ", "_").lower()
        vv = dict(v, Fade=fade, Duration=4)
        got = [frame("16x9", vv, t, f"{tag}_{n}").getextrema()[1] for n, t in (("first", 0), ("mid", PEAK), ("last", last))]
        check(f"Fade {fade}", all(is_[k](g) for k, g in zip((w0, w1, w2), got)),
              f"alpha at 0 s, {PEAK} s, {last:.2f} s: {got} (expected {w0}, {w1}, {w2})")
    seams = [("fade_fade_in_last", "fade_steady_first"), ("fade_steady_last", "fade_fade_out_first")]
    for x, y in seams:
        diff = ImageChops.difference(Image.open(OUT / f"{x}.png").convert("RGBA"), Image.open(OUT / f"{y}.png").convert("RGBA"))
        worst = max(hi for lo, hi in diff.getextrema())
        check(f"no jump: {x[5:]} to {y[5:]}", worst <= 2, f"largest difference {worst} of 255")

    vfile = OUT / "bad_corner.values.json"
    vfile.write_text(json.dumps({"Corner": "Middle"}))
    r = run([sys.executable, ROOT / "tools" / "render.py", TEMPLATE, "--variant", "16x9", "--values", vfile, "--out",
             OUT / "bad.png", "--frame", "1", "--effectcraft-cli", a.effectcraft_cli], check=False)
    check("an unknown Corner is refused", r.returncode != 0 and "Top Left" in (r.stderr + r.stdout),
          (r.stderr or r.stdout).strip().splitlines()[-1] if (r.stderr or r.stdout).strip() else f"exit {r.returncode}")

    vfile = OUT / "duration.values.json"
    vfile.write_text(json.dumps({"Duration": 3}))
    clip = OUT / "duration.mov"
    run([sys.executable, ROOT / "tools" / "render.py", TEMPLATE, "--variant", "16x9", "--values", vfile, "--out", clip,
         "--effectcraft-cli", a.effectcraft_cli])
    seconds = float(run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", clip]).stdout.strip())
    check("Duration sets the clip length", abs(seconds - 3) <= 0.05, f"Duration 3 rendered {seconds:.2f} s")

    # Contact sheet: the four 16x9 corners laid over one grey frame, with each expected box outlined.
    s = Image.new("RGBA", FRAMES["16x9"], (40, 50, 60, 255))
    for img in sheet:
        s.alpha_composite(img)
    for corner in CORNERS:
        ImageDraw.Draw(s).rectangle(box("16x9", corner), outline=(255, 255, 0, 255), width=2)
    s.convert("RGB").resize((960, 540)).save(OUT / "sheet.png")
    print(f"\n{sum(results)} of {len(results)} checks pass; sheet {OUT / 'sheet.png'}")
    sys.exit(0 if all(results) else 1)


if __name__ == "__main__":
    main()
