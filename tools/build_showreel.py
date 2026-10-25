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
# The 9x16 showreel opens on the lower thirds (owner, 2026-10-24): the Locator and Route Leg insets would cover its heading
ORDER_9X16 = [ORDER[2], ORDER[3], ORDER[0], ORDER[1]] + ORDER[4:]
SHOWREEL_HEADING = "Showreel"   # the 9x16 reel's heading second line (demo.py "heading": shown from the first frame)
HEADER_SIZES = {24, 45}   # the 9x16 opening header's two Animated Title overlays (Size 24 and 45)


def is_header(overlay):
    v = overlay["values"]
    text = v.get("Text", "") if isinstance(v, dict) else ""
    return (overlay["template"] == "effectcraft/titles/animated_title" and v.get("Size") in HEADER_SIZES and overlay.get("at", 0) == 0
            and (text.lower().startswith("free motion templates") or text.endswith(" Template")))



WATCH_LIFT = {"title": -260, "corner_logo": -230}   # bottom-placed overlays lifted (px) to end near 82% of the height
WATCH_DROP = 110                                    # top-placed overlays and map insets lowered (px) to start near 8.5%


def pin_defaults(seg):
    """The watch page has its own safe band (8% to 85%), not the Shorts one the 9x16 templates default to: state the plain 16x9-style
    geometry in the spec (no extra margins, the older Box Wipe, Animated Title and line widths), then watch_page lifts and lowers from it."""
    for o in seg.get("overlays", []):
        v, name = o.get("values"), o["template"].rsplit("/", 1)[-1]
        if not isinstance(v, dict):
            continue
        c = v.get("set", v)
        if name in ("corner_logo", "title"):
            c["Extra Vertical"], c["Extra Right"] = 0, 0
        elif name == "box_wipe":
            c.setdefault("Position", [70, 1640])
            c["Max Width"] = 83.3
        elif name == "animated_title":
            c.setdefault("Position", [540, 960])
        elif name in ("sign_off", "typewriter", "credits"):
            c["Max Width"] = 86


def watch_page(seg):
    """The 9x16 showreel is over 3 minutes, so YouTube plays it on the watch page, which cuts the top (about 6%) and everything
    below about 85% of the height (owner, 2026-10-24): pills go to 8.5% from the top (or just above the 85% line where the top left
    is busy), bottom-placed overlays are lifted, top-placed overlays and map insets are lowered, and the credits start higher."""
    pin_defaults(seg)
    top_left, extra = False, []
    for o in list(seg.get("overlays", [])):
        v, name = o.get("values"), o["template"].rsplit("/", 1)[-1]
        if name in ("locator", "route_leg") and "card" not in seg:
            o["dy"] = WATCH_DROP   # the inset card sits in the top right
        if not isinstance(v, dict):
            continue
        place = str(v.get("Place", v.get("Corner", "")))
        if name in WATCH_LIFT and place.startswith("Top"):
            top_left = True
            o["dy"] = WATCH_DROP
        if name in WATCH_LIFT and place.startswith("Bottom"):
            o["dy"] = WATCH_LIFT[name]
        if name == "credits" and v.get("Position", [0, 0])[1] > 1500:
            v["Position"] = [v["Position"][0], 1480]
            if v.get("Title") and v.get("Line 1"):   # too tall for the blur below the photo: the title goes in the blur above it
                head = json.loads(json.dumps(o))
                head["values"].update({"Line 1": "", "Line 2": "", "Position": [v["Position"][0], 400]})
                v["Title"] = ""
                extra.append(head)
    seg.setdefault("overlays", []).extend(extra)
    seg["caption_at"] = "safe" if top_left else "upper"


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
            seg["overlays"] = [o for o in seg["overlays"] if not is_header(o)]   # the reel's own "heading" replaces them
        if seg.get("caption"):
            seg["caption"] = seg["caption"].removesuffix(" · 9x16")
        seg["label"] = name
        if size == "9x16":
            watch_page(seg)
        out.append(seg)
    return name, out, spec.get("prepare", [])


def build(size, only):
    chosen = [(k, f) for k, f in (ORDER if size == "16x9" else ORDER_9X16) if not only or k in only]
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
    if size == "9x16":
        spec["heading"] = SHOWREEL_HEADING
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
