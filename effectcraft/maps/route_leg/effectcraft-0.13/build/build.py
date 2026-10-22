#!/usr/bin/env python3
"""Build the Route Leg templates (templates/route_leg_<variant>.ectemplate) with EffectCraft's command-line tool.

  python3 effectcraft/maps/route_leg/effectcraft-0.13/build/build.py [--variant 16x9] [--effectcraft-cli PATH]

A map picture (from tools/maps.py route-legs) fills the frame, or a card in the top-right corner when Corner Inset is on. A line
draws itself along an arc from the From pin to the To pin, and each pin's name appears beside it. Pin positions are in the map
picture's pixels, so maps.py's values file fills them directly.
"""
import argparse
import json
import pathlib
import sys
import tempfile

HERE = pathlib.Path(__file__).resolve().parents[1]   # this version folder, e.g. <template>/effectcraft-0.13
ROOT = next(p for p in HERE.parents if (p / "tools" / "ecbuild.py").is_file())
sys.path.insert(0, str(ROOT / "tools"))
from ecbuild import Project, find_cli, find_path, hex_colour  # noqa: E402

COMP = "Route Leg"
FPS, DURATION = 24, 5
# Per variant: frame size, card scale in inset mode, and the scale of pins, line and text in inset mode.
VARIANTS = {"16x9": ((1920, 1080), 0.36, 0.6), "9x16": ((1080, 1920), 0.5, 0.7)}
MARGIN = 48       # inset card distance from the frame edge
BORDER = 8        # inset card's white border
INK, HALO = "#1b2a3a", "#ffffff"
LINE_COLOUR, PIN_COLOUR, CURVE = "#d9482b", "#d9482b", 70
# Timing (seconds): From pin and name, line draw-on, To pin and name.
FROM_IN, LINE_START, LINE_END, TO_IN, POP = 0.3, 0.6, 2.2, 2.1, 0.3


def header(w, h, k, s):
    """Shared start of every expression: inset state, card scale k and offset o, and P() from map pixels to comp pixels."""
    return (f'var W = {w}, H = {h}; var c = thisComp.layer("Controls"); var inset = c.effect("Corner Inset")("Checkbox") == 1; '
            f'var k = inset ? {k} : 1; var s = inset ? {s} : 1; var o = inset ? [W - {MARGIN} - W * k, {MARGIN}] : [0, 0]; '
            'function P(p) { return [o[0] + p[0] * k, o[1] + p[1] * k]; } ')


FIT = ('var r = sourceRectAtTime(time, false); '
       # f: the name's scale, s unless that is too wide for the map, then just narrow enough to fit.
       'var f = Math.min(s, (W * k - 32 * s) / Math.max(r.width, 1)); ')


def label_position(pin, other):
    """A name on the side of its pin away from the line (below when the other pin is higher), flipped when there is no room, and
    kept inside the map."""
    return (f'var p = P(c.effect("{pin}")("Point")); var q = P(c.effect("{other}")("Point")); ' + FIT +
            'var above = p[1] - 30 * s, below = p[1] + 34 * s - r.top * f; '
            'var y = q[1] < p[1] ? below : above; '
            'if (y == below && y + (r.top + r.height) * f > o[1] + H * k - 12 * s) y = above; '
            'if (y == above && y + r.top * f < o[1] + 12 * s) y = below; '
            'var hw = r.width / 2 * f; var x = Math.min(Math.max(p[0], o[0] + 16 * s + hw), o[0] + W * k - 16 * s - hw); '
            '[x - (r.left + r.width / 2) * f, y]')


def build(cli, variant, workdir):
    (w, h), k, s = VARIANTS[variant]
    defaults = json.loads((HERE / "assets" / f"default_map_{variant}.values.json").read_text())
    H = header(w, h, k, s)
    p = Project(cli, workdir / f"route_leg_{variant}.ecproj", COMP, w, h, FPS, DURATION)
    map_file, texture = HERE / "assets" / f"default_map_{variant}.png", HERE / "assets" / "blank_texture.png"
    p.import_files(map_file, texture)

    # Layers from the bottom up (each new layer goes on top).
    p.run(("layer.newShape", {"kind": "rect", "name": "Card Border", "size": [w, h], "fill": HALO}),
          ("layer.addItem", {"item": map_file.name}), ("layer.rename", {"layer": map_file.name, "name": "Map"}),
          ("layer.addItem", {"item": texture.name}), ("layer.rename", {"layer": texture.name, "name": "Texture"}),
          ("layer.setBlendMode", {"layers": ["Texture"], "mode": "Multiply"}),
          ("layer.newShape", {"kind": "none", "name": "Line"}),
          ("layer.addShapeItem", {"layer": "Line", "kind": "path"}),
          ("layer.addShapeItem", {"layer": "Line", "kind": "stroke"}),
          ("layer.addShapeItem", {"layer": "Line", "kind": "trim"}),
          *[("layer.newShape", {"kind": "ellipse", "name": n, "size": [30, 30], "fill": PIN_COLOUR, "stroke": HALO, "strokeWidth": 6})
            for n in ("From Pin", "To Pin")],
          *[("layer.newText", {"text": defaults[n], "name": n, "font": "Inter", "style": "Bold", "size": 54, "fill": INK,
                               "stroke": HALO, "strokeWidth": 8, "strokeOverFill": False, "justify": "center"})
            for n in ("From Name", "To Name")],
          ("layer.newText", {"text": defaults["Map Credit"], "name": "Map Credit", "font": "Inter", "style": "Regular", "size": 20,
                             "fill": "#3a3a3a", "stroke": HALO, "strokeWidth": 4, "strokeOverFill": False, "justify": "right"}),
          ("layer.newNull", {"name": "Controls"}))
    p.add_controls("Controls", [
        ("From Position", "Point Control", defaults["From Position"]),
        ("To Position", "Point Control", defaults["To Position"]),
        ("Line Colour", "Color Control", hex_colour(LINE_COLOUR)),
        ("Pin Colour", "Color Control", hex_colour(PIN_COLOUR)),
        ("Curve", "Slider Control", CURVE),
        ("Corner Inset", "Checkbox Control", False),
    ])

    # The card: the map and texture fill the frame, or the inset card with a white border.
    for layer in ("Map", "Texture"):
        p.expression(layer, "transform/position", H + "P([W / 2, H / 2])")
        p.expression(layer, "transform/scale", H + "[W / width * 100 * k, H / height * 100 * k, 100]")
    border = p.tree("Card Border")
    p.expression("Card Border", "transform/position", H + "P([W / 2, H / 2])")
    p.expression("Card Border", find_path(border, "rect/size"), H + f"[W * k + {2 * BORDER}, H * k + {2 * BORDER}]")
    p.expression("Card Border", "transform/opacity", H + "inset ? 100 : 0")

    # The line: an arc in comp space (the layer sits at 0,0), drawn on by Trim Paths.
    p.set("Line", "transform/position", [0, 0, 0])
    p.expression("Line", "contents/path/path", H + (
        'var a = P(c.effect("From Position")("Point")); var b = P(c.effect("To Position")("Point")); '
        'var d = [b[0] - a[0], b[1] - a[1]]; var cv = (c.effect("Curve")("Slider") - 50) / 100; '
        'var q = [(a[0] + b[0]) / 2 + d[1] * cv, (a[1] + b[1]) / 2 - d[0] * cv]; '
        # createPath takes plain [x, y] arrays; property values come out as [0, 0].
        'createPath([a, b], [[0, 0], [(q[0] - b[0]) * 2 / 3, (q[1] - b[1]) * 2 / 3]], '
        '[[(q[0] - a[0]) * 2 / 3, (q[1] - a[1]) * 2 / 3], [0, 0]], false)'))
    p.expression("Line", "contents/stroke/color", 'thisComp.layer("Controls").effect("Line Colour")("Color")')
    p.expression("Line", "contents/stroke/width", H + "9 * s")
    p.set("Line", "contents/stroke/cap", 1)
    p.set("Line", "contents/trim/end", 0, time=LINE_START)
    p.set("Line", "contents/trim/end", 100, time=LINE_END)

    # Pins and names.
    for pin, point, start in (("From Pin", "From Position", FROM_IN), ("To Pin", "To Position", TO_IN)):
        p.expression(pin, "transform/position", H + f'P(c.effect("{point}")("Point"))')
        p.expression(pin, find_path(p.tree(pin), "fill/color"), 'thisComp.layer("Controls").effect("Pin Colour")("Color")')
        p.set(pin, "transform/scale", [0, 0, 100], time=start)
        p.set(pin, "transform/scale", [100, 100, 100], time=start + POP)
        p.expression(pin, "transform/scale", H + "[value[0] * s, value[1] * s, 100]")
        name = pin.replace("Pin", "Name")
        other = "To Position" if point == "From Position" else "From Position"
        p.expression(name, "transform/position", H + label_position(point, other))
        p.expression(name, "transform/scale", H + FIT + "[100 * f, 100 * f, 100]")
        p.set(name, "transform/opacity", 0, time=start)
        p.set(name, "transform/opacity", 100, time=start + POP)
    # One Name Font control (on From Name) sets To Name's font too, so the names always match; their text comes from their controls.
    p.expression("To Name", "text/sourceText", 'text.sourceText.style.setFont(thisComp.layer("From Name").text.sourceText.style.font)')
    p.expression("Map Credit", "transform/position", H + "[o[0] + W * k - 14 * s, o[1] + H * k - 14 * s]")
    p.expression("Map Credit", "transform/scale", H + "[100 * s, 100 * s, 100]")
    p.run(("keys.selectAll", {}), ("keys.easyEase", {}))

    controls = p._effects("Controls")
    path = {g["name"]: g["children"][0]["path"] for g in controls}
    p.run(("essential.setPrimary", {"comp": COMP}),
          ("essential.addMedia", {"layer": "Map", "name": "Map"}),
          *[("essential.addProperty", {"comp": COMP, "layer": "Controls", "path": path[n], "name": n}) for n in ("From Position", "To Position")],
          *[("essential.addProperty", {"comp": COMP, "layer": n, "path": "text/sourceText", "name": n}) for n in ("From Name", "To Name")],
          *[("essential.addProperty", {"comp": COMP, "layer": "Controls", "path": path[n], "name": n})
            for n in ("Line Colour", "Pin Colour", "Curve", "Corner Inset")],
          ("essential.addProperty", {"comp": COMP, "layer": "Map Credit", "path": "text/sourceText", "name": "Map Credit"}),
          ("essential.addMedia", {"layer": "Texture", "name": "Texture"}),
          ("essential.addProperty", {"comp": COMP, "layer": "From Name", "path": "text/sourceText", "name": "Name Font", "as": "font"}),
          ("essential.addProperty", {"comp": COMP, "layer": "Map Credit", "path": "text/sourceText", "name": "Credit Font", "as": "font"}))
    out = p.export(HERE / "templates" / f"route_leg_{variant}.ectemplate", f"Route Leg {variant}")
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
