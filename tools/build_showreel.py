#!/usr/bin/env python3
"""Write a showreel spec from the templates' own demo specs: every shot of every template, in order, re-rendered by demo.py.

  python3 tools/build_showreel.py --size 16x9            # demo/showreel.json
  python3 tools/build_showreel.py --size 9x16            # demo/showreel_9x16.json
  python3 tools/build_showreel.py --size 16x9 --only locator fill_frame typewriter --out /tmp/test.json
  then: python3 tools/demo.py demo/showreel.json --footage DIR --music DIR --effectcraft-cli CLI --out demo/showreel.mp4

The shots come from each template's previews/demo.json (16x9) or previews/demo_9x16.json (9x16), copied as they are: the same
footage, overlays, settings and captions, laid out the way the template's own reel lays them out. Nothing is cut from a finished
video. Each shot also gets "label": the template's name, shown in the caption's pill. The 9x16 specs' opening header (two Animated
Title overlays on the first shot that say what the reel is) is kept on the showreel's first shot only, its second line reading
"Pixie's Craft Templates Showreel", and dropped from every later template's first shot. The " · 9x16" caption suffix is dropped too. The chapters (for the video's description), one per template, are printed from the segment lengths and the crossfade.
"""
import argparse
import json
import math
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
MUSIC = "Relaxing Flute Tune-(SoundEffectsFactory.com)_.mp3"
CROSSFADE, TITLE_SECONDS = 0.5, 3
# (folder key, template folder) in showreel order. The chapters are one per template (each runs 14 s or more; YouTube wants 10 s).
ORDER = [("locator", "maps/locator"), ("route_leg", "maps/route_leg"), ("basic", "lower_thirds/basic"),
         ("box_wipe", "lower_thirds/box_wipe"), ("fill_frame", "utility/fill_frame"), ("glint", "overlays/glint"),
         ("glint_set", "overlays/glint_set"), ("corner_logo", "logos/corner_logo"), ("title", "titles/title"),
         ("animated_title", "titles/animated_title"), ("typewriter", "titles/typewriter"), ("credits", "titles/credits"),
         ("sign_off", "titles/sign_off")]
SHOWREEL_LINE = "Pixie's Craft Templates Showreel"   # the 9x16 opening header's second line
HEADER_SIZES = {24, 45}   # the 9x16 opening header's two Animated Title overlays (Size 24 and 45)


def is_header(overlay):
    v = overlay["values"]
    text = v.get("Text", "") if isinstance(v, dict) else ""
    return (overlay["template"] == "effectcraft/titles/animated_title" and v.get("Size") in HEADER_SIZES and overlay.get("at", 0) == 0
            and (text.startswith("Free motion templates") or text.endswith(" Template")))


def shots(key, folder, size, opening=False):
    """The template's segments for this size, ready for the showreel, and its prepare commands. opening: the showreel's first
    template, whose first 9x16 shot keeps the Shorts' opening header (it says what the viewer is looking at), its second line
    naming the showreel instead of the template."""
    base = ROOT / "effectcraft" / folder
    version = sorted(p for p in base.glob("effectcraft-*") if (p / "template.json").is_file())[-1]
    name = json.loads((version / "template.json").read_text())["name"]
    spec = json.loads((version / "previews" / ("demo.json" if size == "16x9" else "demo_9x16.json")).read_text())
    if spec["size"] != size:
        sys.exit(f"{key}: the spec is {spec['size']}, not {size}")
    out = []
    for i, seg in enumerate(spec["segments"]):
        if "clip" in seg:
            sys.exit(f"{key}: segment {i} is a clip of a finished video; the showreel is built from shots")
        seg = json.loads(json.dumps(seg))
        if i == 0 and size == "9x16":
            headers = [o for o in seg.get("overlays", []) if is_header(o)]
            if len(headers) != 2:
                sys.exit(f"{key}: expected the 9x16 opening header (2 overlays) on the first shot, found {len(headers)}")
            if opening:
                for o in headers:
                    if o["values"]["Size"] == 45:
                        o["values"]["Text"] = SHOWREEL_LINE
            else:
                seg["overlays"] = [o for o in seg["overlays"] if not is_header(o)]
        if seg.get("caption"):
            seg["caption"] = seg["caption"].removesuffix(" · 9x16")
        seg["label"] = name
        out.append(seg)
    return name, out, spec.get("prepare", [])


def build(size, only):
    chosen = [(k, f) for k, f in ORDER if not only or k in only]
    segments, prepare, starts, names = [], [], {}, {}
    t = TITLE_SECONDS - CROSSFADE if size == "16x9" else 0   # where the first shot starts (after the title page)
    outs = {}
    for n, (key, folder) in enumerate(chosen):
        name, segs, prep = shots(key, folder, size, opening=n == 0)
        for cmd in prep:
            dest = cmd[cmd.index("--out") + 1]
            if outs.setdefault(dest, key) != key:
                sys.exit(f"{key} and {outs[dest]} both write {dest} in the working folder")
        prepare += prep
        starts[key], names[key] = t, name
        for seg in segs:
            segments.append(seg)
            t += seg["seconds"] - CROSSFADE
    spec = {"size": size, "footage": "australia", "music": MUSIC, "crossfade": CROSSFADE, "poster_at": 10.0 if size == "16x9" else 8.0}
    if size == "16x9":
        spec["title_page"] = "collection"
    spec["end_page"] = True
    if prepare:
        spec["prepare"] = prepare
    spec["segments"] = segments
    total = t + CROSSFADE + 4 - CROSSFADE   # the end page (4 s) joins with a crossfade
    return spec, [(names[k], starts[k]) for k, _ in chosen], total


def chapters(starts):
    """One line per template: M:SS and its name. The first is 0:00 (the title page, if any, belongs to it); the others are the first
    whole second with the template's first shot fully on screen."""
    lines = []
    for name, start in starts:
        s = 0 if not lines else math.ceil(start + CROSSFADE)
        lines.append(f"{s // 60}:{s % 60:02d} {name}")
    return lines


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--size", required=True, choices=["16x9", "9x16"])
    ap.add_argument("--only", nargs="+", metavar="KEY", help="a test reel of these templates only (folder keys, e.g. locator)")
    ap.add_argument("--out", type=pathlib.Path, help="default: demo/showreel.json (demo/showreel_9x16.json for 9x16)")
    a = ap.parse_args()
    unknown = set(a.only or []) - {k for k, _ in ORDER}
    if unknown:
        sys.exit(f"unknown template keys {sorted(unknown)}; choose from {[k for k, _ in ORDER]}")
    spec, starts, total = build(a.size, a.only)
    out = a.out or ROOT / "demo" / ("showreel.json" if a.size == "16x9" else "showreel_9x16.json")
    out.write_text(json.dumps(spec, indent=2, ensure_ascii=False) + "\n")
    print(f"{out}: {len(spec['segments'])} shots, about {int(total // 60)}:{int(total % 60):02d}")
    if not a.only:
        print("Chapters (check each against the video):")
        print("\n".join(chapters(starts)))


if __name__ == "__main__":
    main()
