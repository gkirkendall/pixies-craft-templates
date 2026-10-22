#!/usr/bin/env python3
"""Build the Animated Title templates (templates/animated_title_<variant>.ectemplate) with EffectCraft's command-line tool.

  python3 effectcraft/titles/animated_title/effectcraft-0.13/build/build.py [--variant 16x9] [--effectcraft-cli PATH]

A title that animates in letter by letter, word by word or line by line, in one of eight Styles (Fade Up, Slide, Scale Pop, Turn,
Blur, Spread In, Wave, Bounce), holds, and animates out the same way before Duration; the Fade menu can leave out either. Words
typed between stars (*like this*) take the Highlight Colour. Centred on Position, over transparency.
"""
import argparse
import pathlib
import sys
import tempfile

HERE = pathlib.Path(__file__).resolve().parents[1]   # this version folder, e.g. <template>/effectcraft-0.13
ROOT = next(p for p in HERE.parents if (p / "tools" / "ecbuild.py").is_file())
sys.path.insert(0, str(ROOT / "tools"))
from ecbuild import Project, find_cli, hex_colour  # noqa: E402

COMP = "Animated Title"
FPS, DURATION = 24, 60   # tools/render.py renders up to the Duration value
FONT_SIZE = 120          # the text layer's own size; the Size control scales from it
# Per variant: frame size and default Size.
VARIANTS = {"16x9": ((1920, 1080), 120), "9x16": ((1080, 1920), 96)}
STYLES = ["Fade Up", "Slide", "Scale Pop", "Turn", "Blur", "Spread In", "Wave", "Bounce"]
BY = ["Letters", "Words", "Lines"]
# One title layer per By item, as a selector's Based On and a layer's Anchor Point Grouping can be set only as values (an
# expression on either is ignored): Based On characters excluding spaces, words, lines; grouping by character, word, line.
BASED_ON, GROUPING = [1, 2, 3], [0, 1, 2]
FADES = ["Fade In and Out", "Fade In", "Steady", "Fade Out"]
TEXT, COLOUR, HIGHLIGHT, SHADOW, START = "Coast to *centre*", "#ffffff", "#ffd166", 40, 0.3
MOVE = 0.6               # seconds each letter, word or line takes to move
CONTROL = 'thisComp.layer("Controls").effect("{}")("{}")'
STYLE = CONTROL.format("Style", "Menu")
# Each unit (textIndex of textTotal) starts Stagger after the one before (less for a long text, so the move in takes at most a
# third of Duration and never meets the move out); p is how far it is through its move in, q through its
# move out (the out move ends 0.1 s before Duration). Spread In moves every letter together. The eased amount is 100 where the
# unit is fully "away" (the animator's values apply) and 0 at rest; Scale Pop and Wave overshoot (a negative amount), Bounce
# bounces. Fade (menu 1-4, in FADES order) leaves out the move in (Steady, Fade Out) or the move out (Fade In, Steady).
SELECTOR = (f'var st = {STYLE}; var n = textTotal, i = textIndex - 1; var t0 = {CONTROL.format("Start", "Slider")}; '
            f'var d = {CONTROL.format("Duration", "Slider")}; var k = 1 + {CONTROL.format("Ease", "Slider")} / 25; '
            f'var mv = st == 6 ? {MOVE} * 1.6 : {MOVE}; '
            f'var sg = st == 6 ? 0 : Math.min({CONTROL.format("Stagger", "Slider")}, Math.max((d / 3 - mv) / Math.max(n - 1, 1), 0)); '
            'var p = Math.min(Math.max((time - t0 - i * sg) / mv, 0), 1); '
            'var t1 = d - 0.1 - mv - (n - 1) * sg; var q = Math.min(Math.max((time - t1 - i * sg) / mv, 0), 1); '
            'function back(x) { var c = 1.7; return 1 + (c + 1) * Math.pow(x - 1, 3) + c * Math.pow(x - 1, 2); } '
            'function bounce(x) { var a = 7.5625, b = 2.75; if (x < 1 / b) return a * x * x; '
            'if (x < 2 / b) { x -= 1.5 / b; return a * x * x + 0.75; } if (x < 2.5 / b) { x -= 2.25 / b; return a * x * x + 0.9375; } '
            'x -= 2.625 / b; return a * x * x + 0.984375; } '
            'var e = st == 3 || st == 7 ? back(p) : st == 8 ? bounce(p) : 1 - Math.pow(1 - p, k); '
            f'var fm = {CONTROL.format("Fade", "Menu")}; var vin = fm == 3 || fm == 4 ? 0 : 100 * (1 - e); '
            'var vout = fm == 2 || fm == 3 ? 0 : 100 * Math.pow(q, k); var v = q > 0 ? vout : vin; ')
# The animator's values: where a unit is when fully "away", in the text layer's own pixels (FONT_SIZE).
S = FONT_SIZE
AWAY = {"position": f"var st = {STYLE}; st == 1 ? [0, {0.5 * S}, 0] : st == 2 ? [{-1.2 * S}, 0, 0] : st == 7 ? [0, {0.6 * S}, 0] "
                    f": st == 8 ? [0, {-1.5 * S}, 0] : st == 4 ? [0, {0.3 * S}, 0] : [0, 0, 0]",
        "scale": f"{STYLE} == 3 ? [0, 0, 100] : [100, 100, 100]",
        "rotation": f"{STYLE} == 4 ? -90 : 0",
        "opacity": "0",
        "blur": f"{STYLE} == 5 ? [{0.35 * S}, {0.35 * S}] : [0, 0]",
        "tracking": f"{STYLE} == 6 ? 600 : 0"}
# The text as shown: Raw (the Text and Font controls) without its stars, in Raw's style (its font).
SHOWN = ('var raw = thisComp.layer("Raw").text.sourceText; '
         'raw.style.setText(String(raw).split("*").join(""))')
# Highlight: the words of Raw that start with a star (based on words), and each word up to the one ending in a star.
HIGHLIGHTED = ('var w = String(thisComp.layer("Raw").text.sourceText).split(/\\s+/); var on = false, hit = 0; '
               'for (var j = 0; j < w.length && j < textIndex; j++) { if (w[j].charAt(0) == "*") on = true; '
               'hit = on ? 100 : 0; if (w[j].length > 1 && w[j].charAt(w[j].length - 1) == "*") on = false; '
               'else if (w[j] == "*" && j > 0) on = false; } [hit, hit, hit]')
# Size scales the layer from FONT_SIZE; the whole title shrinks further to fit Max Width; its middle sits on Position.
FIT = (f'var P = {CONTROL.format("Position", "Point")}; var mw = {CONTROL.format("Max Width", "Slider")}; '
       f'var r = sourceRectAtTime(time, false); var s = {CONTROL.format("Size", "Slider")} / {FONT_SIZE}; '
       'var f = r.width * s > mw ? mw / r.width : s; ')


def build(cli, variant, workdir):
    (w, h), size = VARIANTS[variant]
    p = Project(cli, workdir / f"animated_title_{variant}.ecproj", COMP, w, h, FPS, DURATION)
    p.run(("layer.newText", {"text": TEXT, "name": "Raw", "font": "Inter", "style": "Bold", "size": FONT_SIZE, "fill": COLOUR,
                             "justify": "center"}),
          ("layer.newNull", {"name": "Controls"}))
    p.set("Raw", "transform/opacity", 0)   # holds the text as typed (stars and all) and its font; never drawn
    path = p.add_controls("Controls", [("Style", "Dropdown Menu Control", (STYLES, STYLES[0])),
                                       ("By", "Dropdown Menu Control", (BY, BY[0])),
                                       ("Stagger", "Slider Control", 0.05), ("Ease", "Slider Control", 50),
                                       ("Fade", "Dropdown Menu Control", (FADES, FADES[0])),
                                       ("Position", "Point Control", [w / 2, h / 2]), ("Size", "Slider Control", size),
                                       ("Max Width", "Slider Control", round(w * 0.86)),
                                       ("Colour", "Color Control", hex_colour(COLOUR)),
                                       ("Highlight Colour", "Color Control", hex_colour(HIGHLIGHT)),
                                       ("Shadow", "Slider Control", SHADOW), ("Start", "Slider Control", START),
                                       ("Duration", "Slider Control", 4)])
    titles = [f"Title {b}" for b in BY]
    p.run(*[("layer.newText", {"text": TEXT, "name": n, "font": "Inter", "style": "Bold", "size": FONT_SIZE, "fill": COLOUR,
                               "justify": "center"}) for n in titles])
    anim = lambda n: "text/animators/animator" + ("" if n == 1 else f"#{n}")
    for k, (name, based, grouping) in enumerate(zip(titles, BASED_ON, GROUPING), start=1):
        p.expression(name, "text/sourceText", SHOWN)
        p.set(name, "text/moreOptions/anchorGrouping", grouping)
        # Animators, in order: Colour (all of it), Highlight (the starred words), Move (by this layer's unit).
        p.run(("layer.addTextAnimator", {"layer": name, "properties": ["fillColor"]}),
              ("layer.addTextAnimator", {"layer": name, "properties": ["fillColor"]}),
              ("layer.addTextAnimator", {"layer": name, "properties": list(AWAY)}))
        p.run(*[("layer.addTextSelector", {"layer": name, "animator": n, "kind": "expression"}) for n in (2, 3)])
        p.expression(name, f"{anim(1)}/properties/fillColor", CONTROL.format("Colour", "Color"))
        p.expression(name, f"{anim(2)}/properties/fillColor", CONTROL.format("Highlight Colour", "Color"))
        p.set(name, f"{anim(2)}/selectors/expressionSelector/basedOn", 2)
        p.expression(name, f"{anim(2)}/selectors/expressionSelector/amount", HIGHLIGHTED)
        for prop, code in AWAY.items():
            p.expression(name, f"{anim(3)}/properties/{prop}", code)
        p.set(name, f"{anim(3)}/selectors/expressionSelector/basedOn", based)
        p.expression(name, f"{anim(3)}/selectors/expressionSelector/amount", SELECTOR + "[v, v, v]")
        p.expression(name, "transform/opacity", f'{CONTROL.format("By", "Menu")} == {k} ? 100 : 0')   # By shows one layer
        p.expression(name, "transform/scale", FIT + "[f * 100, f * 100, 100]")
        p.expression(name, "transform/position", FIT + "[P[0] - (r.left + r.width / 2) * f, P[1] - (r.top + r.height / 2) * f, 0]")
        p.run(("effect.apply", {"effect": "ec.perspective.dropshadow", "layers": [name]}))
        p.set(name, "effects/#1/distance", 3)
        p.set(name, "effects/#1/softness", 14)
        p.expression(name, "effects/#1/opacity", CONTROL.format("Shadow", "Slider"))
    p.run(("essential.setPrimary", {"comp": COMP}),
          ("essential.addProperty", {"comp": COMP, "layer": "Raw", "path": "text/sourceText", "name": "Text"}),
          ("essential.addProperty", {"comp": COMP, "layer": "Raw", "path": "text/sourceText", "name": "Font", "as": "font"}),
          *[("essential.addProperty", {"comp": COMP, "layer": "Controls", "path": path[n], "name": n, "as": "dropdown"})
            for n in ("Style", "By")],
          *[("essential.addProperty", {"comp": COMP, "layer": "Controls", "path": path[n], "name": n}) for n in ("Stagger", "Ease")],
          ("essential.addProperty", {"comp": COMP, "layer": "Controls", "path": path["Fade"], "name": "Fade", "as": "dropdown"}),
          *[("essential.addProperty", {"comp": COMP, "layer": "Controls", "path": path[n], "name": n})
            for n in ("Position", "Size", "Max Width", "Colour", "Highlight Colour", "Shadow", "Start", "Duration")])
    out = p.export(HERE / "templates" / f"animated_title_{variant}.ectemplate", f"Animated Title {variant}")
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
