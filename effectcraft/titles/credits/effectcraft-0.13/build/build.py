#!/usr/bin/env python3
"""Build the Credits templates (templates/credits_<variant>.ectemplate) with EffectCraft's command-line tool.

  python3 effectcraft/titles/credits/effectcraft-0.13/build/build.py [--variant 16x9] [--effectcraft-cli PATH]

A title in quotes, in tall condensed capitals (League Gothic), with up to five credit lines under it (Montserrat); empty lines
close up, and the block stays centred on Position. Each line shrinks on its own to fit Max Width. It fades and rises in at
Start and fades out by Duration, over transparency, with a soft shadow so it reads over a bright clip. One of the three
end-card templates (with Corner Logo and Sign-off).
"""
import argparse
import pathlib
import sys
import tempfile

HERE = pathlib.Path(__file__).resolve().parents[1]   # this version folder, e.g. <template>/effectcraft-0.13
ROOT = next(p for p in HERE.parents if (p / "tools" / "ecbuild.py").is_file())
sys.path.insert(0, str(ROOT / "tools"))
from ecbuild import Project, find_cli, hex_colour  # noqa: E402

COMP = "Credits"
FPS, DURATION = 24, 60   # tools/render.py renders up to the Duration value
# Per variant: frame size, title and line font sizes, and the default Position (the block's centre).
VARIANTS = {"16x9": ((1920, 1080), 150, 46, [960, 470]), "9x16": ((1080, 1920), 120, 40, [540, 800])}
LINES = 5
TITLE_WIDTH = 0.37
COLOUR, SHADOW, START, FADE, RISE = "#ffffff", 50, 0.3, 0.6, 30
TITLE, CREDITS = "Our Road Trip", ["Filmed and edited by Your Name", "Music: Track Name by Artist",
                                   "Map data © OpenStreetMap contributors", "", ""]
CONTROL = 'thisComp.layer("Controls").effect("{}")("{}")'
NAMES = ["Title"] + [f"Line {i + 1}" for i in range(LINES)]
# The layout, the same in every layer's expressions: each name's fit (f), its glyph box (r) and whether it is empty; the title,
# then each non-empty line LINE_PITCH × its font size below the last; the whole block centred on Position. An empty title is
# left out (no quotes) and the lines move up.
LAYOUT = (f'var P = {CONTROL.format("Position", "Point")}; var mw = thisComp.width * {CONTROL.format("Max Width", "Slider")} / 100; '
          'var L = {}; var names = ' + str(NAMES).replace("'", '"') + '; '
          'for (var i = 0; i < names.length; i++) { var l = thisComp.layer(names[i]); var r = l.sourceRectAtTime(time, false); '
          'L[names[i]] = {r: r, f: r.width > mw ? mw / r.width : 1, empty: r.width < 1, size: l.text.sourceText.style.fontSize}; } '
          'var T = L["Title"]; var top = T.empty ? null : T.r.top * T.f; var base = {Title: 0}; '
          'var bottom = T.empty ? 0 : (T.r.top + T.r.height) * T.f; var y = 0; var first = true; '
          'for (var i = 1; i < names.length; i++) { var n = L[names[i]]; if (n.empty) { base[names[i]] = y; continue; } '
          'y = first ? (T.empty ? 0 : bottom + 0.3 * T.size * T.f + 1.0 * n.size) : y + 1.5 * n.size; first = false; '
          'base[names[i]] = y; if (top === null) top = y + n.r.top * n.f; bottom = y + 0.3 * n.size; } if (top === null) top = 0; '
          'var shift = P[1] - (top + bottom) / 2; ')
EASE = (f'var t0 = {CONTROL.format("Start", "Slider")}; var d = {CONTROL.format("Duration", "Slider")}; '
        f'var a = Math.min(Math.max((time - t0) / {FADE}, 0), 1); a = 1 - Math.pow(1 - a, 2); '
        f'var z = Math.min(Math.max((d - time) / 0.5, 0), 1); z = 1 - Math.pow(1 - z, 2); ')


def build(cli, variant, workdir):
    (w, h), title_size, line_size, position = VARIANTS[variant]
    p = Project(cli, workdir / f"credits_{variant}.ecproj", COMP, w, h, FPS, DURATION)
    p.run(("layer.newText", {"text": TITLE, "name": "Title", "font": "League Gothic", "style": "Regular", "size": title_size,
                             "fill": COLOUR, "justify": "center"}),
          *[("layer.newText", {"text": CREDITS[i] or " ", "name": f"Line {i + 1}", "font": "Montserrat", "style": "Medium",
                               "size": line_size, "fill": COLOUR, "justify": "center"}) for i in range(LINES)],
          ("layer.newNull", {"name": "Controls"}))
    path = p.add_controls("Controls", [("Position", "Point Control", position), ("Max Width", "Slider Control", 86),
                                       ("Colour", "Color Control", hex_colour(COLOUR)), ("Shadow", "Slider Control", SHADOW),
                                       ("Start", "Slider Control", START), ("Duration", "Slider Control", 6)])
    # The title is shown in capitals between curly quotes, whatever case it is typed in. A title too long for Max Width breaks at
    # the space nearest its middle (judged by its length: League Gothic capitals average about 0.37 of the font size); a title
    # still too wide then shrinks to fit, like every line.
    p.expression("Title", "text/sourceText",
                 f'var s = String(value).toUpperCase(); var mw = thisComp.width * {CONTROL.format("Max Width", "Slider")} / 100; '
                 f'if (s.length * {TITLE_WIDTH} * {title_size} > mw) {{ var b = -1; for (var i = 0; i < s.length; i++) '
                 'if (s.charAt(i) == " " && (b < 0 || Math.abs(i - s.length / 2) < Math.abs(b - s.length / 2))) b = i; '
                 'if (b > 0) s = s.slice(0, b) + "\\r" + s.slice(b + 1); } '
                 "s.replace(/\\s/g, '') == '' ? '' : '\\u201C' + s + '\\u201D'")   # an empty title: no quotes
    for i in range(2, LINES + 1):   # one Font control (on Line 1) sets every credit line's font
        p.expression(f"Line {i}", "text/sourceText", 'text.sourceText.style.setFont(thisComp.layer("Line 1").text.sourceText.style.font)')
    # Fill colours the text from the Colour control (a fill expression would clash with the title's text expression); the soft
    # shadow under it keeps white text readable over a bright clip.
    p.run(("effect.apply", {"effect": "ec.generate.fill", "layers": NAMES}),
          ("effect.apply", {"effect": "ec.perspective.dropshadow", "layers": NAMES}))
    for name in NAMES:
        p.expression(name, "transform/position", LAYOUT + EASE + f'[P[0], base["{name}"] + shift + {RISE} * (1 - a), 0]')
        p.expression(name, "transform/scale", LAYOUT + f'var f = L["{name}"].f; [f * 100, f * 100, 100]')
        p.expression(name, "transform/opacity", EASE + "100 * a * z")
        p.expression(name, "effects/#1/color", CONTROL.format("Colour", "Color"))
        p.set(name, "effects/#2/distance", 3)
        p.set(name, "effects/#2/softness", 14)
        p.expression(name, "effects/#2/opacity", CONTROL.format("Shadow", "Slider"))
    p.run(("essential.setPrimary", {"comp": COMP}),
          ("essential.addProperty", {"comp": COMP, "layer": "Title", "path": "text/sourceText", "name": "Title"}),
          *[("essential.addProperty", {"comp": COMP, "layer": f"Line {i + 1}", "path": "text/sourceText", "name": f"Line {i + 1}"})
            for i in range(LINES)],
          ("essential.addProperty", {"comp": COMP, "layer": "Title", "path": "text/sourceText", "name": "Title Font", "as": "font"}),
          ("essential.addProperty", {"comp": COMP, "layer": "Line 1", "path": "text/sourceText", "name": "Line Font", "as": "font"}),
          *[("essential.addProperty", {"comp": COMP, "layer": "Controls", "path": path[n], "name": n})
            for n in ("Position", "Max Width", "Colour", "Shadow", "Start", "Duration")])
    out = p.export(HERE / "templates" / f"credits_{variant}.ectemplate", f"Credits {variant}")
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
