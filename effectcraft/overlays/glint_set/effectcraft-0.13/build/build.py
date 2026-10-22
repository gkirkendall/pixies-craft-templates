#!/usr/bin/env python3
"""Build the Glint Set templates (templates/glint_set_<variant>.ectemplate) with EffectCraft's command-line tool.

  python3 effectcraft/overlays/glint_set/effectcraft-0.13/build/build.py [--variant 16x9] [--effectcraft-cli PATH]

Six glints already placed and timed one after another across a title-sized band about the frame's centre, ready to drop over a
title picture (Pixie, 2026-10-21: a "pre-filled" glint like the video's title). Spread scales the placement about the centre so the
set fits the title; Size, Colour and Glow apply to all six. Each glint is the Glint template's star and glow.
"""
import argparse
import pathlib
import sys
import tempfile

HERE = pathlib.Path(__file__).resolve().parents[1]   # this version folder, e.g. <template>/effectcraft-0.13
ROOT = next(p for p in HERE.parents if (p / "tools" / "ecbuild.py").is_file())
sys.path.insert(0, str(ROOT / "tools"))
from ecbuild import Project, find_cli, hex_colour  # noqa: E402

COMP = "Glint Set"
FPS, DURATION = 24, 30   # tools/render.py renders up to the Duration value
VARIANTS = {"16x9": (1920, 1080), "9x16": (1080, 1920)}
COLOUR, SIZE, GLOW = "#fff6dc", 140, 60
# Each glint: x as a fraction of 0.9 × the frame width, y as a fraction of the frame's shorter side (both from the centre, before
# Spread), its start (s) and its size relative to Size. Left and right alternate, so the eye travels across the title.
GLINTS = [(-0.30, -0.10, 0.3, 1.0), (0.22, -0.16, 0.6, 0.7), (-0.05, 0.12, 0.9, 0.55),
          (0.34, 0.08, 1.2, 0.9), (-0.22, 0.15, 1.5, 0.6), (0.05, -0.20, 1.8, 0.8)]
STAR = "contents/group/contents/star"
CONTROL = 'thisComp.layer("Controls").effect("{}")("{}")'


def where(variant, gx, gy):
    """GLINTS offsets in pixels for this frame size (the test uses the same rule)."""
    w, h = VARIANTS[variant]
    return gx * 0.9 * w, gy * min(w, h)


def build(cli, variant, workdir):
    w, h = VARIANTS[variant]
    p = Project(cli, workdir / f"glint_set_{variant}.ecproj", COMP, w, h, FPS, DURATION)
    layers = []
    for i in range(len(GLINTS)):
        layers += [("layer.newShape", {"kind": "star", "name": f"Glow {i + 1}", "size": [200, 200], "fill": COLOUR}),
                   ("layer.newShape", {"kind": "star", "name": f"Star {i + 1}", "size": [200, 200], "fill": COLOUR})]
    p.run(*layers, ("layer.newNull", {"name": "Controls"}))
    p.add_controls("Controls", [("Spread", "Slider Control", 100), ("Size", "Slider Control", 50),
                                ("Colour", "Color Control", hex_colour(COLOUR)), ("Glow", "Slider Control", GLOW),
                                ("Duration", "Slider Control", 3.5)])
    p.run(("effect.apply", {"effect": "ec.blur.gaussian", "layers": [f"Glow {i + 1}" for i in range(len(GLINTS))]}))
    size = f'({CONTROL.format("Size", "Slider")} * {SIZE} / 50)'
    for i, (gx, gy, start, rel) in enumerate(GLINTS):
        dx, dy = where(variant, gx, gy)
        life = (f'var t = time - {start}; '
                'var k = t < 0 || t > 1 ? 0 : t < 0.25 ? 1 - Math.pow(1 - t / 0.25, 2) : 1 - Math.pow((t - 0.25) / 0.75, 2); ')
        for kind, spread in (("Star", 1.0), ("Glow", 1.25)):
            layer = f"{kind} {i + 1}"
            p.set(layer, f"{STAR}/points", 4)
            p.expression(layer, f"{STAR}/outerRadius", f"{size} * {rel} / 2 * {spread}")
            p.expression(layer, f"{STAR}/innerRadius", f"{size} * {rel} / 2 * {0.11 * spread}")
            p.set(layer, f"{STAR}/innerRoundness", 60)
            p.expression(layer, "contents/group/contents/fill/color", CONTROL.format("Colour", "Color"))
            p.expression(layer, "transform/position",
                         f'var s = {CONTROL.format("Spread", "Slider")} / 100; [{w / 2} + {dx:.1f} * s, {h / 2} + {dy:.1f} * s, 0]')
            p.expression(layer, "transform/scale", life + "[100 * k, 100 * k, 100]")
            p.expression(layer, "transform/rotation", f"(time - {start}) * 60")
        p.expression(f"Glow {i + 1}", "transform/opacity", CONTROL.format("Glow", "Slider"))
        p.expression(f"Glow {i + 1}", "effects/#1/blurriness", f"{size} * {rel} / 8")
    path = {g["name"]: g["children"][0]["path"] for g in p._effects("Controls")}
    p.run(("essential.setPrimary", {"comp": COMP}),
          *[("essential.addProperty", {"comp": COMP, "layer": "Controls", "path": path[n], "name": n})
            for n in ("Spread", "Size", "Colour", "Glow", "Duration")])
    out = p.export(HERE / "templates" / f"glint_set_{variant}.ectemplate", f"Glint Set {variant}")
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
