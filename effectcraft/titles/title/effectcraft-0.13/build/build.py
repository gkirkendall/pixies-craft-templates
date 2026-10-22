#!/usr/bin/env python3
"""Build the Title templates (templates/title_<variant>.ectemplate) with EffectCraft's command-line tool.

  python3 effectcraft/titles/title/effectcraft-0.13/build/build.py [--variant 16x9] [--effectcraft-cli PATH]

One title line (Inter Bold) with an optional small label over it (Inter SemiBold, capitals, spaced out), placed by a Place menu
(centre, bottom centre or a corner) Margin from the frame's edges, over transparency. Each line shrinks on its own to fit Max
Width (a percent of the frame width); an empty label closes up. It fades and rises in at Start and fades out by Duration; the Fade menu can leave out either, to
hold a title across several clips, as Corner Logo does.
"""
import argparse
import pathlib
import sys
import tempfile

HERE = pathlib.Path(__file__).resolve().parents[1]   # this version folder, e.g. <template>/effectcraft-0.13
ROOT = next(p for p in HERE.parents if (p / "tools" / "ecbuild.py").is_file())
sys.path.insert(0, str(ROOT / "tools"))
from ecbuild import Project, find_cli, hex_colour  # noqa: E402

COMP = "Title"
FPS, DURATION = 24, 60   # tools/render.py renders up to the Duration value
# Per variant: frame size, title and label font sizes, and Margin.
VARIANTS = {"16x9": ((1920, 1080), 110, 32, 96), "9x16": ((1080, 1920), 92, 30, 80)}
PLACES = ["Centre", "Bottom Centre", "Bottom Left", "Bottom Right", "Top Left", "Top Right"]
FADES = ["Fade In and Out", "Fade In", "Steady", "Fade Out"]
TITLE, LABEL = "Our Road Trip", "Australia"
COLOUR, SHADOW, START, FADE, RISE, TRACKING = "#ffffff", 50, 0.3, 0.6, 24, 240
CONTROL = 'thisComp.layer("Controls").effect("{}")("{}")'
# The layout, the same in both layers' expressions: each layer's glyph box (r), fit to Max Width (f) and whether it is empty;
# the label over the title with a gap of 0.3 × the title's font size; the block placed by Place (menu 1-6, in PLACES order).
LAYOUT = (f'var W = thisComp.width, H = thisComp.height; var pl = {CONTROL.format("Place", "Menu")}; '
          f'var mg = {CONTROL.format("Margin", "Slider")}; var mw = W * {CONTROL.format("Max Width", "Slider")} / 100; '
          'function m(n) { var l = thisComp.layer(n); var r = l.sourceRectAtTime(time, false); '
          'return {r: r, f: r.width > mw ? mw / r.width : 1, e: r.width < 1, size: l.text.sourceText.style.fontSize}; } '
          'var L = m("Label"), T = m("Title"); var lh = L.e ? 0 : L.r.height * L.f; var gap = L.e ? 0 : 0.3 * T.size * T.f; '
          'var bh = lh + gap + T.r.height * T.f; var y0 = pl == 1 ? (H - bh) / 2 : pl <= 4 ? H - mg - bh : mg; '
          'var left = pl == 3 || pl == 5, right = pl == 4 || pl == 6; '
          'function x(o) { return left ? mg - o.r.left * o.f : right ? W - mg - (o.r.left + o.r.width) * o.f '
          ': W / 2 - (o.r.left + o.r.width / 2) * o.f; } ')
# In: from Start over FADE, eased out; out: over the last 0.5 s before Duration, eased in. Fade (menu 1-4, in FADES order) leaves
# out the fade in (Steady, Fade Out: full and in place from the first frame) or the fade out (Fade In, Steady: full to the end).
EASE = (f'var t0 = {CONTROL.format("Start", "Slider")}; var d = {CONTROL.format("Duration", "Slider")}; '
        f'var a = Math.min(Math.max((time - t0) / {FADE}, 0), 1); a = 1 - Math.pow(1 - a, 2); '
        'var z = Math.min(Math.max((d - time) / 0.5, 0), 1); z = 1 - Math.pow(1 - z, 2); '
        f'var fm = {CONTROL.format("Fade", "Menu")}; if (fm == 3 || fm == 4) a = 1; if (fm == 2 || fm == 3) z = 1; ')
POSITION = {"Label": "[x(L), y0 - L.r.top * L.f + {rise}, 0]", "Title": "[x(T), y0 + lh + gap - T.r.top * T.f + {rise}, 0]"}


def build(cli, variant, workdir):
    (w, h), title_size, label_size, margin = VARIANTS[variant]
    p = Project(cli, workdir / f"title_{variant}.ecproj", COMP, w, h, FPS, DURATION)
    p.run(("layer.newText", {"text": LABEL, "name": "Label", "font": "Inter", "style": "SemiBold", "size": label_size,
                             "fill": COLOUR, "justify": "center"}),
          ("layer.newText", {"text": TITLE, "name": "Title", "font": "Inter", "style": "Bold", "size": title_size, "fill": COLOUR,
                             "justify": "center"}),
          ("layer.newNull", {"name": "Controls"}))
    path = p.add_controls("Controls", [("Place", "Dropdown Menu Control", (PLACES, PLACES[0])), ("Margin", "Slider Control", margin),
                                       ("Max Width", "Slider Control", 86),
                                       ("Colour", "Color Control", hex_colour(COLOUR)), ("Shadow", "Slider Control", SHADOW),
                                       ("Fade", "Dropdown Menu Control", (FADES, FADES[0])), ("Start", "Slider Control", START),
                                       ("Duration", "Slider Control", 5)])
    # The label in capitals, spaced out by a Tracking animator over all of it.
    p.expression("Label", "text/sourceText", "String(value).toUpperCase()")
    p.run(("layer.addTextAnimator", {"layer": "Label", "properties": ["tracking"]}))
    p.set("Label", "text/animators/animator/properties/tracking", TRACKING)
    p.run(("effect.apply", {"effect": "ec.generate.fill", "layers": ["Label", "Title"]}),
          ("effect.apply", {"effect": "ec.perspective.dropshadow", "layers": ["Label", "Title"]}))
    for name in ("Label", "Title"):
        p.expression(name, "transform/position", LAYOUT + EASE + POSITION[name].format(rise=f"{RISE} * (1 - a)"))
        p.expression(name, "transform/scale", LAYOUT + f'var f = {name[0]}.f; [f * 100, f * 100, 100]')
        p.expression(name, "transform/opacity", EASE + "100 * a * z")
        p.expression(name, "effects/#1/color", CONTROL.format("Colour", "Color"))
        p.set(name, "effects/#2/distance", 3)
        p.set(name, "effects/#2/softness", 14)
        p.expression(name, "effects/#2/opacity", CONTROL.format("Shadow", "Slider"))
    p.run(("essential.setPrimary", {"comp": COMP}),
          ("essential.addProperty", {"comp": COMP, "layer": "Title", "path": "text/sourceText", "name": "Title"}),
          ("essential.addProperty", {"comp": COMP, "layer": "Label", "path": "text/sourceText", "name": "Label"}),
          ("essential.addProperty", {"comp": COMP, "layer": "Title", "path": "text/sourceText", "name": "Title Font", "as": "font"}),
          ("essential.addProperty", {"comp": COMP, "layer": "Label", "path": "text/sourceText", "name": "Label Font", "as": "font"}),
          ("essential.addProperty", {"comp": COMP, "layer": "Controls", "path": path["Place"], "name": "Place", "as": "dropdown"}),
          *[("essential.addProperty", {"comp": COMP, "layer": "Controls", "path": path[n], "name": n})
            for n in ("Margin", "Max Width", "Colour", "Shadow")],
          ("essential.addProperty", {"comp": COMP, "layer": "Controls", "path": path["Fade"], "name": "Fade", "as": "dropdown"}),
          *[("essential.addProperty", {"comp": COMP, "layer": "Controls", "path": path[n], "name": n}) for n in ("Start", "Duration")])
    out = p.export(HERE / "templates" / f"title_{variant}.ectemplate", f"Title {variant}")
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
