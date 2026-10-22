#!/usr/bin/env python3
"""Build the Fill the Frame templates (templates/fill_frame_<variant>.ectemplate) with EffectCraft's command-line tool.

  python3 effectcraft/utility/fill_frame/effectcraft-0.13/build/build.py [--variant 16x9] [--effectcraft-cli PATH]

Shows a picture or clip of any shape whole, fitted inside the frame, over a blurred, darkened copy of itself scaled to cover the
frame, instead of black bars. Nothing of the picture is cut off.

How: one Media layer (a media control swaps only the layer it is attached to, so there cannot be a second copy), fitted inside
the frame. Above it an adjustment layer scales what is below up to cover the frame (Transform), blurs and darkens it, and CC
Composite puts the sharp original back in front.
"""
import argparse
import pathlib
import sys
import tempfile

HERE = pathlib.Path(__file__).resolve().parents[1]   # this version folder, e.g. <template>/effectcraft-0.13
ROOT = next(p for p in HERE.parents if (p / "tools" / "ecbuild.py").is_file())
sys.path.insert(0, str(ROOT / "tools"))
from ecbuild import Project, find_cli  # noqa: E402

COMP = "Fill the Frame"
FPS, DURATION = 24, 60   # the longest clip; tools/render.py renders up to the Duration value
VARIANTS = {"16x9": (1920, 1080), "9x16": (1080, 1920)}
BLUR, DARKEN = 60, 30
# Fit inside the frame (f) and cover it (c), from the Media layer's own size, so any swapped-in picture is measured afresh.
FIT = ('var m = thisComp.layer("Media"); '
       'var f = Math.min(thisComp.width / m.width, thisComp.height / m.height); '
       'var c = Math.max(thisComp.width / m.width, thisComp.height / m.height); ')
CONTROL = 'thisComp.layer("Controls").effect("{}")("Slider")'


def build(cli, variant, workdir):
    w, h = VARIANTS[variant]
    p = Project(cli, workdir / f"fill_frame_{variant}.ecproj", COMP, w, h, FPS, DURATION)
    media = HERE / "assets" / "sample_4x3.png"
    p.import_files(media)
    p.run(("layer.addItem", {"item": media.name}), ("layer.rename", {"layer": media.name, "name": "Media"}),
          ("layer.newAdjustment", {"name": "Fill"}),
          *[("effect.apply", {"effect": e, "layers": ["Fill"]})
            for e in ("ec.distort.transform", "ec.blur.gaussian", "ec.color.exposure", "ec.channel.cccomposite")],
          ("layer.newNull", {"name": "Controls"}))
    path = p.add_controls("Controls", [("Blur", "Slider Control", BLUR), ("Darken", "Slider Control", DARKEN),
                                       ("Duration", "Slider Control", 5), ("Clip Length", "Slider Control", 0)])
    # A clip shorter than Duration plays again from the start (owner, 2026-10-21: "loop for longer videos"); a still is unaffected.
    # Clip Length (filled by tools/render.py from ffprobe) wins over source.duration, which EffectCraft 0.13 reads from the MP4
    # track header without its edit list: one frame too long for most H.264 clips, so each loop would hold the last frame.
    p.run(("layer.enableTimeRemap", {"layers": ["Media"]}))
    p.expression("Media", "timeRemap", f'var c = {CONTROL.format("Clip Length")}; '
                                       'var d = c > 0 ? c : thisLayer.source.duration; d > 0 ? time % d : 0')
    p.expression("Media", "transform/anchor", "[width / 2, height / 2, 0]")
    p.set("Media", "transform/position", [w / 2, h / 2, 0])
    p.expression("Media", "transform/scale", FIT + "[f * 100, f * 100, 100]")
    # Transform scales the fitted picture about the frame's centre until it covers the frame; 5 % more hides the blur's soft edge.
    p.set("Fill", "effects/#1/uniform", True)
    p.expression("Fill", "effects/#1/scaleHeight", FIT + "c / f * 105")
    p.set("Fill", "effects/#2/repeatEdge", True)
    p.expression("Fill", "effects/#2/blurriness", CONTROL.format("Blur"))
    # Darken 0–100: 0 leaves the copy as it is, 100 takes it down 4 stops (near black).
    p.expression("Fill", "effects/#3/master/exposure", f'-{CONTROL.format("Darken")} / 25')
    p.set("Fill", "effects/#4/compositeOriginal", 0)   # "In Front": the sharp picture over the blurred copy
    p.run(("essential.setPrimary", {"comp": COMP}),
          ("essential.addMedia", {"layer": "Media", "name": "Media"}),
          *[("essential.addProperty", {"comp": COMP, "layer": "Controls", "path": path[n], "name": n})
            for n in ("Blur", "Darken", "Duration", "Clip Length")])
    out = p.export(HERE / "templates" / f"fill_frame_{variant}.ectemplate", f"Fill the Frame {variant}")
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
