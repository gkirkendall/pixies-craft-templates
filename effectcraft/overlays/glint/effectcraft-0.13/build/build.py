#!/usr/bin/env python3
"""Build the Glint templates (templates/glint_<variant>.ectemplate) with EffectCraft's command-line tool.

  python3 effectcraft/overlays/glint/effectcraft-0.13/build/build.py [--variant 16x9] [--effectcraft-cli PATH]

One four-point star that pops in at its Start time, turns a little and shrinks away over 1 s, with a soft glow behind it, over
transparency. Meant to be used many times in one video, each instance with its own Position, Start and Size (owner, 2026-10-21).
"""
import argparse
import pathlib
import sys
import tempfile

HERE = pathlib.Path(__file__).resolve().parents[1]   # this version folder, e.g. <template>/effectcraft-0.13
ROOT = next(p for p in HERE.parents if (p / "tools" / "ecbuild.py").is_file())
sys.path.insert(0, str(ROOT / "tools"))
from ecbuild import Project, find_cli, hex_colour  # noqa: E402

COMP = "Glint"
FPS, DURATION = 24, 30   # tools/render.py renders up to the Duration value
VARIANTS = {"16x9": (1920, 1080), "9x16": (1080, 1920)}
COLOUR, SIZE, GLOW, START = "#fff6dc", 140, 60, 0.5
STAR = "contents/group/contents/star"
CONTROL = 'thisComp.layer("Controls").effect("{}")("{}")'
# Life of one glint: grows over 0.25 s (eased out), then shrinks to nothing by 1 s, turning 60° a second.
LIFE = (f'var t = time - {CONTROL.format("Start", "Slider")}; '
        'var k = t < 0 || t > 1 ? 0 : t < 0.25 ? 1 - Math.pow(1 - t / 0.25, 2) : 1 - Math.pow((t - 0.25) / 0.75, 2); ')


def build(cli, variant, workdir):
    w, h = VARIANTS[variant]
    p = Project(cli, workdir / f"glint_{variant}.ecproj", COMP, w, h, FPS, DURATION)
    p.run(("layer.newShape", {"kind": "star", "name": "Glow", "size": [200, 200], "fill": COLOUR}),
          ("layer.newShape", {"kind": "star", "name": "Star", "size": [200, 200], "fill": COLOUR}),
          ("layer.newNull", {"name": "Controls"}))
    p.add_controls("Controls", [("Position", "Point Control", [w * 0.62, h * 0.38]), ("Start", "Slider Control", START),
                                ("Size", "Slider Control", SIZE), ("Colour", "Color Control", hex_colour(COLOUR)),
                                ("Glow", "Slider Control", GLOW), ("Duration", "Slider Control", 2)])
    p.run(("effect.apply", {"effect": "ec.blur.gaussian", "layers": ["Glow"]}))
    for layer, spread in (("Star", 1.0), ("Glow", 1.25)):
        p.set(layer, f"{STAR}/points", 4)
        p.expression(layer, f"{STAR}/outerRadius", f'{CONTROL.format("Size", "Slider")} / 2 * {spread}')
        p.expression(layer, f"{STAR}/innerRadius", f'{CONTROL.format("Size", "Slider")} / 2 * {0.11 * spread}')
        p.set(layer, f"{STAR}/innerRoundness", 60)
        p.expression(layer, "contents/group/contents/fill/color", CONTROL.format("Colour", "Color"))
        p.expression(layer, "transform/position", f'var q = {CONTROL.format("Position", "Point")}; [q[0], q[1], 0]')
        p.expression(layer, "transform/scale", LIFE + "[100 * k, 100 * k, 100]")
        p.expression(layer, "transform/rotation", f'(time - {CONTROL.format("Start", "Slider")}) * 60')
    p.expression("Glow", "transform/opacity", CONTROL.format("Glow", "Slider"))
    p.expression("Glow", "effects/#1/blurriness", f'{CONTROL.format("Size", "Slider")} / 8')
    path = {g["name"]: g["children"][0]["path"] for g in p._effects("Controls")}
    p.run(("essential.setPrimary", {"comp": COMP}),
          *[("essential.addProperty", {"comp": COMP, "layer": "Controls", "path": path[n], "name": n})
            for n in ("Position", "Start", "Size", "Colour", "Glow", "Duration")])
    out = p.export(HERE / "templates" / f"glint_{variant}.ectemplate", f"Glint {variant}")
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
