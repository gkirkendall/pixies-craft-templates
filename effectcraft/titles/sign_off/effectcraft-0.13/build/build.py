#!/usr/bin/env python3
"""Build the Sign-off templates (templates/sign_off_<variant>.ectemplate) with EffectCraft's command-line tool.

  python3 effectcraft/titles/sign_off/effectcraft-0.13/build/build.py [--variant 16x9] [--effectcraft-cli PATH]

One line ("Thank you for watching", Montserrat) between two hearts in a Heart Colour, centred on Position, over transparency.
The hearts follow the text's width; the whole row shrinks to fit Max Width. The text fades and rises in at Start, the hearts pop
in just after, and all of it fades out by Duration. With Blink on, the hearts then beat: fully on and off together,
on for 60 % of each beat. One of the three end-card templates (with Corner Logo and Credits).
"""
import argparse
import pathlib
import sys
import tempfile

HERE = pathlib.Path(__file__).resolve().parents[1]   # this version folder, e.g. <template>/effectcraft-0.13
ROOT = next(p for p in HERE.parents if (p / "tools" / "ecbuild.py").is_file())
sys.path.insert(0, str(ROOT / "tools"))
from ecbuild import Project, find_cli, hex_colour  # noqa: E402

COMP = "Sign-off"
FPS, DURATION = 24, 60   # tools/render.py renders up to the Duration value
# Per variant: frame size, font size and the default Position (the row's centre).
VARIANTS = {"16x9": ((1920, 1080), 64, [960, 790]), "9x16": ((1080, 1920), 56, [540, 1160])}
TEXT, COLOUR, HEART_COLOUR, SHADOW, START, FADE, RISE = "Thank you for watching", "#ffffff", "#e5484d", 50, 0.6, 0.6, 24
# A heart 100 px wide (layer space, centred on 0, 0): from the tip round the left lobe, the dip, the right lobe, back to the tip.
HEART = {"vertices": [[0, 42], [-50, -8], [-25, -44], [0, -26], [25, -44], [50, -8]],
         "inTangents": [[22, -22], [0, 22], [-16, 0], [-4, -14], [-16, 0], [0, -20]],
         "outTangents": [[-22, -22], [0, -20], [16, 0], [4, -14], [16, 0], [0, 22]]}
CONTROL = 'thisComp.layer("Controls").effect("{}")("{}")'
# The row: the text's glyph box (r), the heart width (hs = Heart Size × the font size), the gap between them (0.45 of the font
# size), and the fit (f) that keeps text and hearts within Max Width; the text's middle sits on Position.
ROW = (f'var P = {CONTROL.format("Position", "Point")}; var mw = {CONTROL.format("Max Width", "Slider")}; '
       'var tl = thisComp.layer("Text"); var r = tl.sourceRectAtTime(time, false); var fs = tl.text.sourceText.style.fontSize; '
       f'var hs = {CONTROL.format("Heart Size", "Slider")} / 100 * fs; var gap = 0.45 * fs; '
       'var full = r.width + 2 * (gap + hs); var f = full > mw ? mw / full : 1; ')
EASE = (f'var t0 = {CONTROL.format("Start", "Slider")}; var d = {CONTROL.format("Duration", "Slider")}; '
        f'var a = Math.min(Math.max((time - t0) / {FADE}, 0), 1); a = 1 - Math.pow(1 - a, 2); '
        'var z = Math.min(Math.max((d - time) / 0.5, 0), 1); z = 1 - Math.pow(1 - z, 2); ')
# The hearts pop in 0.25 s after the text starts, overshooting a little (eased out with a back), over 0.45 s.
POP = ('var u = Math.min(Math.max((time - t0 - 0.25) / 0.45, 0), 1); var c = 1.7; '
       'var k = u <= 0 ? 0 : 1 + (c + 1) * Math.pow(u - 1, 3) + c * Math.pow(u - 1, 2); ')
# Blink: once the hearts have popped in (0.7 s after Start), on for the first 60 % of each beat and off for the rest.
BLINK = (f'var on = 1; if ({CONTROL.format("Blink", "Checkbox")} == 1 && time >= t0 + 0.7) '
         f'{{ var ph = ((time - t0 - 0.7) * {CONTROL.format("Beats per Minute", "Slider")} / 60) % 1; on = ph < 0.6 ? 1 : 0; }} ')


def build(cli, variant, workdir):
    (w, h), size, position = VARIANTS[variant]
    p = Project(cli, workdir / f"sign_off_{variant}.ecproj", COMP, w, h, FPS, DURATION)
    p.run(("layer.newText", {"text": TEXT, "name": "Text", "font": "Montserrat", "style": "Medium", "size": size, "fill": COLOUR,
                             "justify": "center"}))
    for name in ("Heart Left", "Heart Right"):
        p.run(("shape.newPath", dict(HEART, closed=True, space="layer", fill=HEART_COLOUR, stroke=False, name=name)))
    p.run(("layer.newNull", {"name": "Controls"}))
    path = p.add_controls("Controls", [("Position", "Point Control", position), ("Max Width", "Slider Control", round(w * 0.86)),
                                       ("Text Colour", "Color Control", hex_colour(COLOUR)),
                                       ("Heart Colour", "Color Control", hex_colour(HEART_COLOUR)),
                                       ("Heart Size", "Slider Control", 70), ("Shadow", "Slider Control", SHADOW),
                                       ("Blink", "Checkbox Control", False), ("Beats per Minute", "Slider Control", 70),
                                       ("Start", "Slider Control", START), ("Duration", "Slider Control", 5)])
    p.run(*[("effect.apply", {"effect": e, "layers": ["Text", "Heart Left", "Heart Right"]})
            for e in ("ec.generate.fill", "ec.perspective.dropshadow")])
    p.expression("Text", "transform/position", ROW + EASE + f"[P[0], P[1] - (r.top + r.height / 2) * f + {RISE} * (1 - a), 0]")
    p.expression("Text", "transform/scale", ROW + "[f * 100, f * 100, 100]")
    p.expression("Text", "transform/opacity", EASE + "100 * a * z")
    p.expression("Text", "effects/#1/color", CONTROL.format("Text Colour", "Color"))
    for name, side in (("Heart Left", -1), ("Heart Right", 1)):
        p.expression(name, "transform/position", ROW + EASE + f"[P[0] + {side} * (r.width / 2 + gap + hs / 2) * f, P[1] + {RISE} * (1 - a), 0]")
        p.expression(name, "transform/scale", ROW + EASE + POP + "var s = hs / 100 * f * k * 100; [s, s, 100]")
        p.expression(name, "transform/opacity", EASE + BLINK + "100 * z * on")
        p.expression(name, "effects/#1/color", CONTROL.format("Heart Colour", "Color"))
    for name in ("Text", "Heart Left", "Heart Right"):
        p.set(name, "effects/#2/distance", 3)
        p.set(name, "effects/#2/softness", 14)
        p.expression(name, "effects/#2/opacity", CONTROL.format("Shadow", "Slider"))
    p.run(("essential.setPrimary", {"comp": COMP}),
          ("essential.addProperty", {"comp": COMP, "layer": "Text", "path": "text/sourceText", "name": "Text"}),
          ("essential.addProperty", {"comp": COMP, "layer": "Text", "path": "text/sourceText", "name": "Font", "as": "font"}),
          *[("essential.addProperty", {"comp": COMP, "layer": "Controls", "path": path[n], "name": n})
            for n in ("Position", "Max Width", "Text Colour", "Heart Colour", "Heart Size", "Shadow", "Blink",
                      "Beats per Minute", "Start", "Duration")])
    out = p.export(HERE / "templates" / f"sign_off_{variant}.ectemplate", f"Sign-off {variant}")
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
