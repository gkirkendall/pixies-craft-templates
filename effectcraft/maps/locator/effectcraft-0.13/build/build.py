#!/usr/bin/env python3
"""Build the Locator templates (templates/locator_<variant>.ectemplate) with EffectCraft's command-line tool.

  python3 effectcraft/maps/locator/effectcraft-0.13/build/build.py [--variant 16x9] [--effectcraft-cli PATH]

The map picture (from tools/maps.py locator, three times the frame size) first shows the whole country, then zooms in on the
place, which glides to the centre (held back at the map's edges). A pin pops in and the name and subtitle fade in under it. With
Corner Inset on, all of it plays in a card in the top-right corner over transparency. An optional Badge (a logo, a flag) sits in
the card's top-left corner.
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

COMP = "Locator"
FPS, DURATION = 24, 5
# Per variant: frame size, card scale in inset mode, and the scale of pin, text and badge in inset mode.
VARIANTS = {"16x9": ((1920, 1080), 0.36, 0.6), "9x16": ((1080, 1920), 0.5, 0.7)}
MARGIN, BORDER = 48, 8
INK, SUB_INK, HALO, PIN_COLOUR = "#1b2a3a", "#3d4b59", "#ffffff", "#d9482b"
BADGE_BOX = 180   # the badge fits inside this square (pixels, full frame)
# Timing (seconds): the zoom, then the pin, then the name and subtitle.
ZOOM_START, ZOOM_END, PIN_IN, TEXT_IN, POP = 0.6, 2.4, 2.3, 2.5, 0.3


def header(w, h, k, s):
    """Shared start of every expression: inset state, card scale k and offset o, and the zoom: z (map pixels to card pixels) and
    pos (where the place sits in the card)."""
    return (f'var W = {w}, H = {h}; var c = thisComp.layer("Controls"); var inset = c.effect("Corner Inset")("Checkbox") == 1; '
            f'var k = inset ? {k} : 1; var s = inset ? {s} : 1; var o = inset ? [W - {MARGIN} - W * k, {MARGIN}] : [0, 0]; '
            'var m = thisComp.layer("Map"); var mw = m.width, mh = m.height; var pl = c.effect("Place Position")("Point"); '
            f'var e = ease(time, {ZOOM_START}, {ZOOM_END}, 0, 1); var s0 = Math.max(W / mw, H / mh); '
            'var z = s0 * Math.pow(Math.max(c.effect("Zoom")("Slider"), 1), e); '
            'var pos = [pl[0] * s0 + (W / 2 - pl[0] * s0) * e, pl[1] * s0 + (H / 2 - pl[1] * s0) * e]; '
            # Keep the map covering the card: the place may not reach the centre when it lies near the map's edge.
            'pos = [Math.min(Math.max(pos[0], W - (mw - pl[0]) * z), pl[0] * z), Math.min(Math.max(pos[1], H - (mh - pl[1]) * z), pl[1] * z)]; '
            'function C(p) { return [o[0] + p[0] * k, o[1] + p[1] * k]; } ')


def text_lines():
    """Baselines of the name and the subtitle: under the pin, or above it when they would run off the card's bottom."""
    return ('var pin = C(pos); var nb = pin[1] + 74 * s, sb = nb + 48 * s; '
            'if (sb + 14 * s > o[1] + H * k - 16 * s) { sb = pin[1] - 30 * s; nb = sb - 46 * s; } ')


FIT = ('var r = sourceRectAtTime(time, false); '
       # f: the text's scale, s unless that is too wide for the card, then just narrow enough to fit.
       'var f = Math.min(s, (W * k - 32 * s) / Math.max(r.width, 1)); ')


def centred_x():
    return (FIT + 'var hw = r.width / 2 * f; '
            'var x = Math.min(Math.max(pin[0], o[0] + 16 * s + hw), o[0] + W * k - 16 * s - hw) - (r.left + r.width / 2) * f; ')


def build(cli, variant, workdir):
    (w, h), k, s = VARIANTS[variant]
    defaults = json.loads((HERE / "assets" / f"default_map_{variant}.values.json").read_text())
    H = header(w, h, k, s)
    p = Project(cli, workdir / f"locator_{variant}.ecproj", COMP, w, h, FPS, DURATION)
    map_file = HERE / "assets" / f"default_map_{variant}.png"
    texture, badge = HERE / "assets" / "blank_texture.png", HERE / "assets" / "blank_badge.png"
    p.import_files(map_file, texture, badge)

    # Layers from the bottom up (each new layer goes on top).
    p.run(("layer.newShape", {"kind": "rect", "name": "Card Border", "size": [w, h], "fill": HALO}),
          ("layer.addItem", {"item": map_file.name}), ("layer.rename", {"layer": map_file.name, "name": "Map"}),
          ("layer.newShape", {"kind": "rect", "name": "Card Mask", "size": [w, h], "fill": HALO}),
          ("layer.setTrackMatte", {"layer": "Map", "matte": "Card Mask", "kind": "alpha"}),
          ("layer.addItem", {"item": texture.name}), ("layer.rename", {"layer": texture.name, "name": "Texture"}),
          ("layer.setBlendMode", {"layers": ["Texture"], "mode": "Multiply"}),
          ("layer.newShape", {"kind": "ellipse", "name": "Pin", "size": [34, 34], "fill": PIN_COLOUR, "stroke": HALO, "strokeWidth": 7}),
          ("layer.newText", {"text": defaults["Place Name"], "name": "Place Name", "font": "Inter", "style": "Bold", "size": 64,
                             "fill": INK, "stroke": HALO, "strokeWidth": 9, "strokeOverFill": False, "justify": "center"}),
          ("layer.newText", {"text": defaults["Subtitle"], "name": "Subtitle", "font": "Inter", "style": "Medium", "size": 40,
                             "fill": SUB_INK, "stroke": HALO, "strokeWidth": 7, "strokeOverFill": False, "justify": "center"}),
          ("layer.newText", {"text": defaults["Map Credit"], "name": "Map Credit", "font": "Inter", "style": "Regular", "size": 20,
                             "fill": "#3a3a3a", "stroke": HALO, "strokeWidth": 4, "strokeOverFill": False, "justify": "right"}),
          ("layer.addItem", {"item": badge.name}), ("layer.rename", {"layer": badge.name, "name": "Badge"}),
          ("layer.newNull", {"name": "Controls"}))
    p.add_controls("Controls", [
        ("Place Position", "Point Control", defaults["Place Position"]),
        ("Zoom", "Slider Control", defaults["Zoom"]),
        ("Pin Colour", "Color Control", hex_colour(PIN_COLOUR)),
        ("Corner Inset", "Checkbox Control", False),
    ])

    # The map zooms about the place: its anchor is the place, so position and scale alone move it.
    p.expression("Map", "transform/anchor", 'var pl = thisComp.layer("Controls").effect("Place Position")("Point"); [pl[0], pl[1], 0]')
    p.expression("Map", "transform/position", H + "C(pos)")
    p.expression("Map", "transform/scale", H + "[z * 100 * k, z * 100 * k, 100]")
    p.expression("Texture", "transform/position", H + "C([W / 2, H / 2])")
    p.expression("Texture", "transform/scale", H + "[W / width * 100 * k, H / height * 100 * k, 100]")
    # The zoomed map is far bigger than the card; the Card Mask (its track matte) clips it to the card.
    p.expression("Card Mask", "transform/position", H + "C([W / 2, H / 2])")
    p.expression("Card Mask", find_path(p.tree("Card Mask"), "rect/size"), H + "[W * k, H * k]")
    p.expression("Card Border", "transform/position", H + "C([W / 2, H / 2])")
    p.expression("Card Border", find_path(p.tree("Card Border"), "rect/size"), H + f"[W * k + {2 * BORDER}, H * k + {2 * BORDER}]")
    p.expression("Card Border", "transform/opacity", H + "inset ? 100 : 0")

    p.expression("Pin", "transform/position", H + "C(pos)")
    p.expression("Pin", find_path(p.tree("Pin"), "fill/color"), 'thisComp.layer("Controls").effect("Pin Colour")("Color")')
    p.set("Pin", "transform/scale", [0, 0, 100], time=PIN_IN)
    p.set("Pin", "transform/scale", [100, 100, 100], time=PIN_IN + POP)
    p.expression("Pin", "transform/scale", H + "[value[0] * s, value[1] * s, 100]")
    for layer, line in (("Place Name", "nb"), ("Subtitle", "sb")):
        p.expression(layer, "transform/position", H + text_lines() + centred_x() + f"[x, {line}]")
        p.expression(layer, "transform/scale", H + FIT + "[100 * f, 100 * f, 100]")
        p.set(layer, "transform/opacity", 0, time=TEXT_IN)
        p.set(layer, "transform/opacity", 100, time=TEXT_IN + POP)
    p.expression("Map Credit", "transform/position", H + "[o[0] + W * k - 14 * s, o[1] + H * k - 14 * s]")
    p.expression("Map Credit", "transform/scale", H + "[100 * s, 100 * s, 100]")
    # The badge fits a square box in the card's top-left corner, whatever the picture's shape.
    p.expression("Badge", "transform/position", H + f"var b = Math.min({BADGE_BOX} / width, {BADGE_BOX} / height) * s; "
                 "[o[0] + 24 * s + width * b / 2, o[1] + 24 * s + height * b / 2]")
    p.expression("Badge", "transform/scale", H + f"var b = Math.min({BADGE_BOX} / width, {BADGE_BOX} / height) * s; [b * 100, b * 100, 100]")
    p.run(("keys.selectAll", {}), ("keys.easyEase", {}))

    path = {g["name"]: g["children"][0]["path"] for g in p._effects("Controls")}
    p.run(("essential.setPrimary", {"comp": COMP}),
          ("essential.addMedia", {"layer": "Map", "name": "Map"}),
          *[("essential.addProperty", {"comp": COMP, "layer": "Controls", "path": path[n], "name": n}) for n in ("Place Position", "Zoom")],
          *[("essential.addProperty", {"comp": COMP, "layer": n, "path": "text/sourceText", "name": n}) for n in ("Place Name", "Subtitle")],
          *[("essential.addProperty", {"comp": COMP, "layer": "Controls", "path": path[n], "name": n}) for n in ("Pin Colour", "Corner Inset")],
          ("essential.addProperty", {"comp": COMP, "layer": "Map Credit", "path": "text/sourceText", "name": "Map Credit"}),
          ("essential.addMedia", {"layer": "Texture", "name": "Texture"}),
          ("essential.addMedia", {"layer": "Badge", "name": "Badge"}),
          ("essential.addProperty", {"comp": COMP, "layer": "Place Name", "path": "text/sourceText", "name": "Name Font", "as": "font"}),
          ("essential.addProperty", {"comp": COMP, "layer": "Subtitle", "path": "text/sourceText", "name": "Subtitle Font", "as": "font"}),
          ("essential.addProperty", {"comp": COMP, "layer": "Map Credit", "path": "text/sourceText", "name": "Credit Font", "as": "font"}))
    out = p.export(HERE / "templates" / f"locator_{variant}.ectemplate", f"Locator {variant}")
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
