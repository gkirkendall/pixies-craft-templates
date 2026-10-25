#!/usr/bin/env python3
"""Build the Corner Logo templates (templates/corner_logo_<variant>.ectemplate) with EffectCraft's command-line tool.

  python3 effectcraft/logos/corner_logo/effectcraft-0.13/build/build.py [--variant 16x9] [--effectcraft-cli PATH]

A Logo picture of any shape, fitted inside a square box (as the Locator's Badge) in a chosen corner of the frame, over
transparency. It fades and rises in at Start and fades out by Duration. One of the three end-card templates (with Credits and
Sign-off), and also the logo for a corner of a commercial video.
"""
import argparse
import pathlib
import sys
import tempfile

HERE = pathlib.Path(__file__).resolve().parents[1]   # this version folder, e.g. <template>/effectcraft-0.13
ROOT = next(p for p in HERE.parents if (p / "tools" / "ecbuild.py").is_file())
sys.path.insert(0, str(ROOT / "tools"))
from ecbuild import Project, find_cli  # noqa: E402

COMP = "Corner Logo"
FPS, DURATION = 24, 60   # tools/render.py renders up to the Duration value
# Per variant: frame size, Extra Vertical (percent of the height) and Extra Right (percent of the width), which add to Margin. The 9x16 extras keep a logo clear of a phone's controls
# (YouTube Shorts: status bar on top, channel row at the bottom, buttons on the right); set both to 0 for the plain Margin.
VARIANTS = {"16x9": ((1920, 1080), 0, 0), "9x16": ((1080, 1920), 8.3, 13)}
CORNERS = ["Top Left", "Top Right", "Bottom Right", "Bottom Left"]
# Fade, per clip, so a logo can run across a whole video: fade in on the first photo, Steady between, fade out on the last.
FADES = ["Fade In and Out", "Fade In", "Steady", "Fade Out"]
CORNER, SIZE, MARGIN, OPACITY, START, FADE, RISE = "Bottom Right", 180, 60, 90, 0.3, 0.5, 24
CONTROL = 'thisComp.layer("Controls").effect("{}")("{}")'
# The box's centre: Size square, Margin from the chosen corner's two edges (the menu reads 1-4, in CORNERS order).
BOX = (f'var c = {CONTROL.format("Corner", "Menu")}; var sz = {CONTROL.format("Size", "Slider")} * {SIZE} / 50; '
       f'var mg = {CONTROL.format("Margin", "Slider")}; var ev = {CONTROL.format("Extra Vertical", "Slider")} / 100 * thisComp.height; var er = {CONTROL.format("Extra Right", "Slider")} / 100 * thisComp.width; '
       'var right = c == 2 || c == 3; var bottom = c == 3 || c == 4; '
       'var bx = right ? thisComp.width - mg - er - sz / 2 : mg + sz / 2; var by = bottom ? thisComp.height - mg - ev - sz / 2 : mg + ev + sz / 2; ')
# In: from Start over FADE, eased out; out: over the last FADE before Duration, eased in. Fade (menu 1-4, in FADES order) leaves
# out the fade in (Steady, Fade Out: full and in place from the first frame) or the fade out (Fade In, Steady: full to the end).
EASE = (f'var t0 = {CONTROL.format("Start", "Slider")}; var d = {CONTROL.format("Duration", "Slider")}; '
        f'var a = Math.min(Math.max((time - t0) / {FADE}, 0), 1); a = 1 - Math.pow(1 - a, 2); '
        f'var z = Math.min(Math.max((d - time) / {FADE}, 0), 1); z = 1 - Math.pow(1 - z, 2); '
        f'var m = {CONTROL.format("Fade", "Menu")}; if (m == 3 || m == 4) a = 1; if (m == 2 || m == 3) z = 1; ')


def build(cli, variant, workdir):
    (w, h), extra_v, extra_r = VARIANTS[variant]
    p = Project(cli, workdir / f"corner_logo_{variant}.ecproj", COMP, w, h, FPS, DURATION)
    logo = HERE / "assets" / "sample_logo.png"
    p.import_files(logo)
    p.run(("layer.addItem", {"item": logo.name}), ("layer.rename", {"layer": logo.name, "name": "Logo"}),
          ("layer.newNull", {"name": "Controls"}))
    path = p.add_controls("Controls", [("Corner", "Dropdown Menu Control", (CORNERS, CORNER)),
                                       ("Size", "Slider Control", 50), ("Margin", "Slider Control", MARGIN),
                                       ("Extra Vertical", "Slider Control", extra_v), ("Extra Right", "Slider Control", extra_r),
                                       ("Opacity", "Slider Control", OPACITY), ("Fade", "Dropdown Menu Control", (FADES, FADES[0])),
                                       ("Start", "Slider Control", START),
                                       ("Duration", "Slider Control", 5)])
    # Fitted inside the box whatever the picture's shape, centred in it; the anchor follows a swapped-in picture's own size.
    p.expression("Logo", "transform/anchor", "[width / 2, height / 2, 0]")
    p.expression("Logo", "transform/scale", f'var b = Math.min({CONTROL.format("Size", "Slider")} * {SIZE} / 50 / width, '
                                             f'{CONTROL.format("Size", "Slider")} * {SIZE} / 50 / height); [b * 100, b * 100, 100]')
    p.expression("Logo", "transform/position", BOX + EASE + f"[bx, by + {RISE} * (1 - a), 0]")
    p.expression("Logo", "transform/opacity", EASE + f'{CONTROL.format("Opacity", "Slider")} * a * z')
    p.run(("essential.setPrimary", {"comp": COMP}),
          ("essential.addMedia", {"layer": "Logo", "name": "Logo"}),
          ("essential.addProperty", {"comp": COMP, "layer": "Controls", "path": path["Corner"], "name": "Corner", "as": "dropdown"}),
          ("essential.addProperty", {"comp": COMP, "layer": "Controls", "path": path["Fade"], "name": "Fade", "as": "dropdown"}),
          *[("essential.addProperty", {"comp": COMP, "layer": "Controls", "path": path[n], "name": n})
            for n in ("Size", "Margin", "Extra Vertical", "Extra Right", "Opacity", "Start", "Duration")])
    out = p.export(HERE / "templates" / f"corner_logo_{variant}.ectemplate", f"Corner Logo {variant}")
    print(f"built {out.relative_to(ROOT)}")


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--variant", choices=sorted(VARIANTS), help="build one variant (default: all)")
    ap.add_argument("--effectcraft-cli", default="effectcraft-cli")
    a = ap.parse_args()
    cli = find_cli(a.effectcraft_cli)
    with tempfile.TemporaryDirectory() as tmp:
        for v in [a.variant] if a.variant else sorted(VARIANTS):
            build(cli, v, pathlib.Path(tmp))


if __name__ == "__main__":
    main()
