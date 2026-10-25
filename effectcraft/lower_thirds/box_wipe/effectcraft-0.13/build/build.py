#!/usr/bin/env python3
"""Build the Box Wipe Lower Third templates (templates/box_wipe_<variant>.ectemplate) with EffectCraft's command-line tool.

  python3 effectcraft/lower_thirds/box_wipe/effectcraft-0.13/build/build.py [--variant 16x9] [--effectcraft-cli PATH]

A thin line sweeps in along the top edge, a see-through colour box wipes open from the left, and the title (Caveat Brush by
default) and an optional subtitle fade in, the title underlined. Before Duration the box wipes shut and the line slides away.
The box fits the longer line; a title wider than Max Width wraps onto two lines, and a line still too wide shrinks. Position is the box's bottom-left corner.
"""
import argparse
import pathlib
import sys
import tempfile

HERE = pathlib.Path(__file__).resolve().parents[1]   # this version folder, e.g. <template>/effectcraft-0.13
ROOT = next(p for p in HERE.parents if (p / "tools" / "ecbuild.py").is_file())
sys.path.insert(0, str(ROOT / "tools"))
from ecbuild import Project, find_cli, hex_colour  # noqa: E402

COMP = "Box Wipe Lower Third"
FPS, DURATION = 24, 60   # tools/render.py renders up to the Duration value
# Per variant: frame size, title and subtitle font sizes, default Position (the box's bottom-left corner) and Max Width (% of the frame width).
VARIANTS = {"16x9": ((1920, 1080), 84, 44, [110, 960], 57.3), "9x16": ((1080, 1920), 72, 40, [70, 1540], 75)}   # 9x16: clear of the Shorts buttons and channel row
TITLE, SUBTITLE, FONT = "Port Campbell", "Victoria, Australia", "Caveat Brush"
BOX, BOX_OPACITY, LINE, TEXT = "#123047", 70, "#ffd166", "#ffffff"
CONTROL = 'thisComp.layer("Controls").effect("{}")("{}")'
# The layout, shared by every layer: the title (wrapped, as shown) and subtitle boxes, each shrunk by f or g if still wider than
# Max Width less the padding; padding and gaps from the title's font size (ts); the box (left L, top T, width BW, height BH) above and right of Position, the underline under the title's glyph box
# (so no descender crosses it), and the subtitle under that.
LAYOUT = (f'var P = {CONTROL.format("Position", "Point")}; var tl = thisComp.layer("Title"), sl = thisComp.layer("Subtitle"); '
          'var r0 = tl.sourceRectAtTime(time, false), r1 = sl.sourceRectAtTime(time, false); var hasSub = r1.width >= 1; '
          'var ts = tl.text.sourceText.style.fontSize; var pad = 0.4 * ts, uh = Math.max(2, 0.05 * ts), ug = 0.08 * ts, gap = 0.18 * ts; '
          f'var mw = thisComp.width * {CONTROL.format("Max Width", "Slider")} / 100 - 2 * pad; var f = Math.min(1, mw / Math.max(r0.width, 1)), '
          'g = Math.min(1, mw / Math.max(r1.width, 1)); '
          'var tr = {left: r0.left * f, top: r0.top * f, width: r0.width * f, height: r0.height * f}; '
          'var sr = {left: r1.left * g, top: r1.top * g, width: r1.width * g, height: r1.height * g}; '
          'var BW = Math.max(tr.width, hasSub ? sr.width : 0) + 2 * pad; '
          'var BH = pad + tr.height + ug + uh + (hasSub ? gap + sr.height : 0) + pad; var L = P[0], T = P[1] - BH; '
          'var ty = T + pad - tr.top, uy = T + pad + tr.height + ug, sy = uy + uh + gap - sr.top; ')
# Timing (seconds from the start; out: before Duration d): line 0-0.35, box 0.15-0.55, text 0.4-0.7, underline 0.55-0.85; out:
# text and underline d-0.7 to d-0.5, box shut d-0.6 to d-0.25, line away d-0.35 to d-0.05. e(a, b) eases 0 → 1 between a and b.
TIME = (f'var d = {CONTROL.format("Duration", "Slider")}; '
        'function e(a, b) { var x = Math.min(Math.max((time - a) / (b - a), 0), 1); return 1 - Math.pow(1 - x, 3); } '
        'function o(a, b) { var x = Math.min(Math.max((time - a) / (b - a), 0), 1); return x * x * x; } ')
RECT = "contents/group/contents/rect"


def build(cli, variant, workdir):
    (w, h), title_size, sub_size, position, max_width = VARIANTS[variant]
    p = Project(cli, workdir / f"box_wipe_{variant}.ecproj", COMP, w, h, FPS, DURATION)
    p.run(("layer.newShape", {"kind": "rect", "name": "Box", "size": [100, 100], "fill": BOX}),
          ("layer.newShape", {"kind": "rect", "name": "Line", "size": [100, 4], "fill": LINE}),
          ("layer.newShape", {"kind": "rect", "name": "Underline", "size": [100, 4], "fill": LINE}),
          ("layer.newText", {"text": TITLE, "name": "Title Text", "font": FONT, "style": "Regular", "size": title_size,
                             "fill": TEXT, "justify": "left"}),
          ("layer.newText", {"text": TITLE, "name": "Title", "font": FONT, "style": "Regular", "size": title_size, "fill": TEXT,
                             "justify": "left"}),
          ("layer.newText", {"text": SUBTITLE, "name": "Subtitle", "font": FONT, "style": "Regular", "size": sub_size, "fill": TEXT,
                             "justify": "left"}),
          ("layer.newNull", {"name": "Controls"}))
    p.set("Title Text", "transform/opacity", 0)   # holds the Title and Title Font controls (one line, for measuring); never drawn
    path = p.add_controls("Controls", [("Position", "Point Control", position), ("Max Width", "Slider Control", max_width),
                                       ("Box Colour", "Color Control", hex_colour(BOX)),
                                       ("Box Opacity", "Slider Control", BOX_OPACITY),
                                       ("Line Colour", "Color Control", hex_colour(LINE)),
                                       ("Text Colour", "Color Control", hex_colour(TEXT)), ("Duration", "Slider Control", 5)])
    # The title as shown: Title Text in its font, broken at the space nearest the middle when wider than Max Width less padding.
    p.expression("Title", "text/sourceText",
                 'var raw = thisComp.layer("Title Text"); var s = String(raw.text.sourceText); '
                 f'var mw = thisComp.width * {CONTROL.format("Max Width", "Slider")} / 100 - 0.8 * raw.text.sourceText.style.fontSize; '
                 'if (raw.sourceRectAtTime(time, false).width > mw) { var b = -1; for (var i = 0; i < s.length; i++) '
                 'if (s.charAt(i) == " " && (b < 0 || Math.abs(i - s.length / 2) < Math.abs(b - s.length / 2))) b = i; '
                 'if (b > 0) s = s.slice(0, b) + "\\r" + s.slice(b + 1); } raw.text.sourceText.style.setText(s)')
    # Shapes: their layers stay at the comp's origin; each rectangle's position (its centre) and size place it.
    p.expression("Box", f"{RECT}/size", LAYOUT + TIME + "var k = e(0.15, 0.55) * (1 - o(d - 0.6, d - 0.25)); [Math.max(BW * k, 0.01), BH]")
    p.expression("Box", f"{RECT}/position", LAYOUT + TIME + "var k = e(0.15, 0.55) * (1 - o(d - 0.6, d - 0.25)); [L + BW * k / 2, T + BH / 2]")
    p.expression("Line", f"{RECT}/size", LAYOUT + TIME + "var k = e(0, 0.35) * (1 - o(d - 0.35, d - 0.05)); [Math.max(BW * k, 0.01), uh]")
    p.expression("Line", f"{RECT}/position", LAYOUT + TIME + "var k = e(0, 0.35); var away = o(d - 0.35, d - 0.05); "
                                                             "var wk = k * (1 - away); [L + BW * (away + wk / 2), T - uh / 2 - 6]")
    p.expression("Underline", f"{RECT}/size", LAYOUT + TIME + "var k = e(0.55, 0.85) * (1 - o(d - 0.7, d - 0.5)); [Math.max(tr.width * k, 0.01), uh]")
    p.expression("Underline", f"{RECT}/position", LAYOUT + TIME + "var k = e(0.55, 0.85) * (1 - o(d - 0.7, d - 0.5)); "
                                                                  "[L + pad + tr.width * k / 2, uy + uh / 2]")
    for name in ("Box", "Line", "Underline"):
        p.expression(name, "transform/position", "[0, 0, 0]")
        p.expression(name, "transform/anchor", "[0, 0, 0]")
    p.expression("Box", "contents/group/contents/fill/color", CONTROL.format("Box Colour", "Color"))
    p.expression("Box", "transform/opacity", CONTROL.format("Box Opacity", "Slider"))
    for name in ("Line", "Underline"):
        p.expression(name, "contents/group/contents/fill/color", CONTROL.format("Line Colour", "Color"))
    p.run(("effect.apply", {"effect": "ec.generate.fill", "layers": ["Title", "Subtitle"]}))
    p.expression("Title", "transform/position", LAYOUT + TIME + "[L + pad - tr.left - 16 * (1 - e(0.4, 0.7)), ty, 0]")
    p.expression("Subtitle", "transform/position", LAYOUT + TIME + "[L + pad - sr.left - 16 * (1 - e(0.4, 0.7)), sy, 0]")
    p.expression("Title", "transform/scale", LAYOUT + "[f * 100, f * 100, 100]")
    p.expression("Subtitle", "transform/scale", LAYOUT + "[g * 100, g * 100, 100]")
    for name in ("Title", "Subtitle"):
        p.expression(name, "transform/opacity", TIME + "100 * e(0.4, 0.7) * (1 - o(d - 0.7, d - 0.5))")
        p.expression(name, "effects/#1/color", CONTROL.format("Text Colour", "Color"))
    p.run(("essential.setPrimary", {"comp": COMP}),
          ("essential.addProperty", {"comp": COMP, "layer": "Title Text", "path": "text/sourceText", "name": "Title"}),
          ("essential.addProperty", {"comp": COMP, "layer": "Subtitle", "path": "text/sourceText", "name": "Subtitle"}),
          ("essential.addProperty", {"comp": COMP, "layer": "Title Text", "path": "text/sourceText", "name": "Title Font", "as": "font"}),
          ("essential.addProperty", {"comp": COMP, "layer": "Subtitle", "path": "text/sourceText", "name": "Subtitle Font", "as": "font"}),
          *[("essential.addProperty", {"comp": COMP, "layer": "Controls", "path": path[n], "name": n})
            for n in ("Position", "Max Width", "Box Colour", "Box Opacity", "Line Colour", "Text Colour", "Duration")])
    out = p.export(HERE / "templates" / f"box_wipe_{variant}.ectemplate", f"Box Wipe Lower Third {variant}")
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
