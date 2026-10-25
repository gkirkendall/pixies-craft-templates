#!/usr/bin/env python3
"""Build the Typewriter templates (templates/typewriter_<variant>.ectemplate) with EffectCraft's command-line tool.

  python3 effectcraft/titles/typewriter/effectcraft-0.13/build/build.py [--variant 16x9] [--effectcraft-cli PATH]

The text types itself letter by letter from Start at Speed letters a second, with a cursor after it (a bar, an underscore or
none) that blinks while it waits; with Erase on, it deletes itself again before Duration. The finished line is centred on
Position and types out from its left edge, so nothing shifts as it grows. Over transparency.
"""
import argparse
import pathlib
import sys
import tempfile

HERE = pathlib.Path(__file__).resolve().parents[1]   # this version folder, e.g. <template>/effectcraft-0.13
ROOT = next(p for p in HERE.parents if (p / "tools" / "ecbuild.py").is_file())
sys.path.insert(0, str(ROOT / "tools"))
from ecbuild import Project, find_cli, hex_colour  # noqa: E402

COMP = "Typewriter"
FPS, DURATION = 24, 60   # tools/render.py renders up to the Duration value
# Per variant: frame size and font size.
# Max Width in percent of the frame width: 64 in 9x16 keeps a line left of a phone's Shorts buttons (x < 83%).
MAX_WIDTH = {"16x9": 86, "9x16": 64}
VARIANTS = {"16x9": ((1920, 1080), 84), "9x16": ((1080, 1920), 64)}
CURSORS = ["Bar", "Underscore", "None"]
TEXT, COLOUR, SHADOW, START, SPEED = "Less perfection, more travel.", "#ffffff", 40, 0.5, 14
CONTROL = 'thisComp.layer("Controls").effect("{}")("{}")'
# The letters typed by now (n of the text in Full); with Erase, deleted again at twice Speed, done 0.3 s before Duration. The
# cursor is solid while typing or deleting and blinks (on 0.5 s, off 0.5 s) while it waits.
TYPED = (f'var full = thisComp.layer("Full").text.sourceText; var s = String(full); var t0 = {CONTROL.format("Start", "Slider")}; '
         f'var sp = Math.max({CONTROL.format("Speed", "Slider")}, 0.1); var d = {CONTROL.format("Duration", "Slider")}; '
         'var n = Math.max(0, Math.min(s.length, Math.floor((time - t0) * sp))); var busy = time >= t0 && n < s.length; '
         f'if ({CONTROL.format("Erase", "Checkbox")} == 1) {{ var te = d - 0.3 - s.length / (2 * sp); '
         'if (time >= te) { n = Math.max(0, s.length - Math.floor((time - te) * 2 * sp)); busy = n > 0; } } '
         f'var cm = {CONTROL.format("Cursor", "Menu")}; var c = cm == 1 ? "|" : cm == 2 ? "_" : ""; '
         'var on = busy || Math.floor(time * 2) % 2 == 0; '
         'full.style.setText(s.slice(0, n) + (on ? c : ""))')
# Measured on Full (the whole line), so the typed text never moves: its left edge where the finished line's is, centred on
# Position, shrunk to Max Width.
PLACE = (f'var P = {CONTROL.format("Position", "Point")}; var mw = thisComp.width * {CONTROL.format("Max Width", "Slider")} / 100; '
         'var fr = thisComp.layer("Full").sourceRectAtTime(time, false); var f = fr.width > mw ? mw / fr.width : 1; ')


def build(cli, variant, workdir):
    (w, h), size = VARIANTS[variant]
    p = Project(cli, workdir / f"typewriter_{variant}.ecproj", COMP, w, h, FPS, DURATION)
    for name in ("Full", "Typed"):
        p.run(("layer.newText", {"text": TEXT, "name": name, "font": "Inter", "style": "SemiBold", "size": size, "fill": COLOUR,
                                 "justify": "left"}))
    p.run(("layer.newNull", {"name": "Controls"}))
    p.set("Full", "transform/opacity", 0)   # holds the whole text and its font, for measuring; never drawn
    path = p.add_controls("Controls", [("Speed", "Slider Control", SPEED),
                                       ("Cursor", "Dropdown Menu Control", (CURSORS, CURSORS[0])),
                                       ("Erase", "Checkbox Control", False),
                                       ("Position", "Point Control", [w / 2, h / 2]),
                                       ("Max Width", "Slider Control", MAX_WIDTH[variant]),
                                       ("Colour", "Color Control", hex_colour(COLOUR)), ("Shadow", "Slider Control", SHADOW),
                                       ("Start", "Slider Control", START), ("Duration", "Slider Control", 5)])
    p.expression("Typed", "text/sourceText", TYPED)
    p.expression("Typed", "transform/scale", PLACE + "[f * 100, f * 100, 100]")
    p.expression("Typed", "transform/position", PLACE + "[P[0] - (fr.left + fr.width / 2) * f, P[1] - (fr.top + fr.height / 2) * f, 0]")
    p.run(("effect.apply", {"effect": "ec.generate.fill", "layers": ["Typed"]}),
          ("effect.apply", {"effect": "ec.perspective.dropshadow", "layers": ["Typed"]}))
    p.expression("Typed", "effects/#1/color", CONTROL.format("Colour", "Color"))
    p.set("Typed", "effects/#2/distance", 3)
    p.set("Typed", "effects/#2/softness", 14)
    p.expression("Typed", "effects/#2/opacity", CONTROL.format("Shadow", "Slider"))
    p.run(("essential.setPrimary", {"comp": COMP}),
          ("essential.addProperty", {"comp": COMP, "layer": "Full", "path": "text/sourceText", "name": "Text"}),
          ("essential.addProperty", {"comp": COMP, "layer": "Full", "path": "text/sourceText", "name": "Font", "as": "font"}),
          ("essential.addProperty", {"comp": COMP, "layer": "Controls", "path": path["Speed"], "name": "Speed"}),
          ("essential.addProperty", {"comp": COMP, "layer": "Controls", "path": path["Cursor"], "name": "Cursor", "as": "dropdown"}),
          *[("essential.addProperty", {"comp": COMP, "layer": "Controls", "path": path[n], "name": n})
            for n in ("Erase", "Position", "Max Width", "Colour", "Shadow", "Start", "Duration")])
    out = p.export(HERE / "templates" / f"typewriter_{variant}.ectemplate", f"Typewriter {variant}")
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
