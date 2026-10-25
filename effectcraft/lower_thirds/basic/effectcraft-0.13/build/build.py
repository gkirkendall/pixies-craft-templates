#!/usr/bin/env python3
"""Build the Basic Lower Third templates (templates/basic_<variant>.ectemplate) with EffectCraft's command-line tool.

  python3 effectcraft/lower_thirds/basic/effectcraft-0.13/build/build.py [--variant 16x9] [--effectcraft-cli PATH]

A dark bar with a title and a subtitle slides in from the left over 0.5 s, holds, and fades out from 3.5 s. The bar sizes itself
to the longer line. First made as MPT's T-E1 test (tests/e1/build.sh), rebuilt here in Python with Inter and a font control per line.
"""
import argparse
import pathlib
import sys
import tempfile

HERE = pathlib.Path(__file__).resolve().parents[1]   # this version folder, e.g. <template>/effectcraft-0.13
ROOT = next(p for p in HERE.parents if (p / "tools" / "ecbuild.py").is_file())
sys.path.insert(0, str(ROOT / "tools"))
from ecbuild import Project, find_cli  # noqa: E402

COMP = "Lower Third"
FPS, DURATION = 24, 4
# Per variant: frame size, bar position (left edge, centre line) and the text baselines' offsets from it.
VARIANTS = {"16x9": ((1920, 1080), (150, 900)), "9x16": ((1080, 1920), (60, 1505))}
TITLE, SUBTITLE = "Port Campbell National Park", "Victoria, Australia"
IN, FADE_START, FADE_END = 0.5, 3.5, 3.95
PAD = 60   # space between the text and the bar's ends


def build(cli, variant, workdir):
    (w, h), (bx, by) = VARIANTS[variant]
    p = Project(cli, workdir / f"basic_{variant}.ecproj", COMP, w, h, FPS, DURATION)
    p.run(("layer.newShape", {"kind": "rect", "name": "Bar", "size": [1100, 190], "fill": "#1b2a3a", "fillOpacity": 85}),
          ("layer.newText", {"text": TITLE, "name": "Title", "font": "Inter", "style": "Bold", "size": 64, "fill": "#ffffff",
                             "justify": "left"}),
          ("layer.newText", {"text": SUBTITLE, "name": "Subtitle", "font": "Inter", "style": "Regular", "size": 40,
                             "fill": "#d8e2ec", "justify": "left"}))
    # The bar's left edge sits at the layer position; its width follows the longer line plus PAD at each end.
    avail = w - bx - 2 * PAD - 40   # widest a line may be: to the frame's right edge, less the bar's ends and a margin
    fitted = lambda layer: (f'var r{layer[0]} = thisComp.layer("{layer}").sourceRectAtTime(time, false).width; '
                            f'var f{layer[0]} = Math.min(1, {avail} / Math.max(r{layer[0]}, 1)); ')
    width = fitted("Title") + fitted("Subtitle") + f'var w = Math.max(rT * fT, rS * fS) + {2 * PAD}; '
    p.expression("Bar", "contents/group/contents/rect/size", width + "[w, 190]")
    p.expression("Bar", "contents/group/contents/rect/position", width + "[w / 2, 0]")
    for layer, x, y in (("Bar", bx, by), ("Title", bx + PAD, by - 10), ("Subtitle", bx + PAD, by + 58)):
        # Start a full frame width to the left: past the widest bar the fit rule allows, so frame 0 is empty.
        p.set(layer, "transform/position", [x - w, y, 0], time=0)
        p.set(layer, "transform/position", [x, y, 0], time=IN)
        p.set(layer, "transform/opacity", 100, time=FADE_START)
        p.set(layer, "transform/opacity", 0, time=FADE_END)
    # A line too wide for the frame shrinks until it fits; the other line keeps its size.
    for layer in ("Title", "Subtitle"):
        p.expression(layer, "transform/scale", fitted(layer) + f"[100 * f{layer[0]}, 100 * f{layer[0]}, 100]")
    p.run(("keys.selectAll", {}), ("keys.easyEase", {}),
          ("essential.setPrimary", {"comp": COMP}),
          ("essential.addProperty", {"comp": COMP, "layer": "Title", "path": "text/sourceText", "name": "Title"}),
          ("essential.addProperty", {"comp": COMP, "layer": "Subtitle", "path": "text/sourceText", "name": "Subtitle"}),
          ("essential.addProperty", {"comp": COMP, "layer": "Title", "path": "text/sourceText", "name": "Title Font", "as": "font"}),
          ("essential.addProperty", {"comp": COMP, "layer": "Subtitle", "path": "text/sourceText", "name": "Subtitle Font", "as": "font"}))
    out = p.export(HERE / "templates" / f"basic_{variant}.ectemplate", f"Basic Lower Third {variant}")
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
