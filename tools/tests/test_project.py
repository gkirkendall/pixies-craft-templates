#!/usr/bin/env python3
"""Test the trip-video kit, project_templates/trip_video (PLAN.md, RECIPE1 3; KIT1.md).

  python3 tools/tests/test_project.py --effectcraft-cli PATH

Needs effectcraft-cli (0.13 or later), no network. For each of "Trip Video 16x9" and "Trip Video 9x16": the project opens and lasts
as long as the demo's shots (demo/australia_trip/demo.json); in a copy of the kit folder moved away from where it was built, Check
Footage finds every file (none missing) and every footage path then lies inside the copy; every Photo_1 ... Photo_8 is used by exactly
one shot layer, in order; every title holds the generic text (and no demo text is left); every overlay of the demo is a layer of the
same template starting where the demo's overlay does; one Corner Logo layer covers the whole video; a still at each shot renders a
picture (not black, not flat).
"""
import argparse
import json
import pathlib
import shutil
import subprocess
import sys
import tempfile

from PIL import Image, ImageStat

ROOT = pathlib.Path(__file__).resolve().parents[2]
KIT = ROOT / "project_templates" / "trip_video"
DEMO = json.loads((ROOT / "demo" / "australia_trip" / "demo.json").read_text())
FADE = DEMO.get("crossfade", 0.5)
DEMO_TEXT = ["Port Campbell", "Point Ritchie", "Mushroom Rock", "Tjoritja", "Sydney Cove", "Hilda", "Australia"]


def run(cli, project, *cmds, save=False):
    args = [cli, "run"]
    for name, params in cmds:
        args += [name, json.dumps(params)]
    args += [str(project), "--json"] + (["--save"] if save else [])
    r = subprocess.run(args, capture_output=True, text=True)
    if r.returncode:
        raise RuntimeError(f"{r.stdout[:400]} {r.stderr[:400]}")
    out = json.loads(r.stdout.splitlines()[0])
    return [x["result"] for x in (out["result"] if isinstance(out, dict) else out)]   # --save wraps the list


COMP_NAMES = {"lower_thirds/basic": "Lower Third"}   # where the template's comp is named differently from the template


def template_name(path):
    path = path.removeprefix("effectcraft/")
    return COMP_NAMES.get(path) or json.loads((ROOT / "effectcraft" / path / "effectcraft-0.13" / "template.json").read_text())["name"]


def set_values(layer):
    """The values the shot's maker typed: the layer's overridden Essential Properties (the others hold the template's defaults,
    which the Title Font control keeps as its sample text)."""
    out = []
    for g in layer["props"]["children"]:
        if g["match"] == "essential":
            out += [json.dumps(c["value"]) for c in g["children"] if c["uid"] in g["kind"]["overridden"]]
    return " ".join(out)


def test_variant(cli, variant, check):
    tag = variant
    shots, start = [], 0.0   # as tools/project.py: each segment starts a crossfade before the one before it ends
    for seg in DEMO["segments"]:
        shots.append((start, seg["seconds"], seg))
        start += seg["seconds"] - FADE
    total = start + FADE
    with tempfile.TemporaryDirectory() as tmp:
        moved = pathlib.Path(tmp) / "kit"
        shutil.copytree(KIT, moved)
        project = moved / f"Trip Video {variant}.ecproj"
        text = project.read_text().replace(str(KIT), "/nonexistent/where/it/was/built")
        project.write_text(text)
        info = subprocess.run([cli, "info", str(project), "--json"], capture_output=True, text=True)
        comp = json.loads(info.stdout)["activeComp"]
        check(f"{tag}: opens, {len(shots)} shots, lasts as long as the demo's shots",
              info.returncode == 0 and abs(comp["duration"] - total) < 0.05, f"{comp['duration']} s of {total} s")
        result = run(cli, project, ("footage.check", {"wait": True}), ("footage.missing", {}), save=True)
        d = json.loads(project.read_text())
        paths = [pathlib.Path(v["kind"]["path"]) for v in d["items"].values()
                 if isinstance(v.get("kind"), dict) and v["kind"].get("type") == "Footage"]
        outside = [str(p) for p in paths if not p.is_relative_to(moved)]
        check(f"{tag}: no footage missing in the moved kit, every path inside it",
              not result[1]["missing"] and not outside and len(paths) > 20,
              f"{len(paths)} files, missing {result[1]['missing'][:2]}, outside {outside[:2]}")
        items = d["items"]
        ticks = items["1"]["kind"]["duration"] / total
        layers = items["1"]["kind"]["layers"]
        photo_ids = {int(k): v["name"] for k, v in items.items()
                     if isinstance(v.get("kind"), dict) and v["kind"].get("type") == "Footage" and v["name"].startswith("Photo_")}
        used = []
        for layer in layers:
            if layer["name"].startswith("Shot ") and "Photo_" in layer["name"]:
                media = next(c["value"]["v"] for g in layer["props"]["children"] if g["match"] == "essential"
                             for c in g["children"] if c["name"] == "Media")
                used.append((layer["name"], photo_ids.get(int(media))))
        wanted = [f"Photo_{i}.jpg" for i in range(1, 9)]
        check(f"{tag}: every Photo_N is used by exactly one shot, in order",
              [u[1] for u in sorted(used, key=lambda u: int(u[0].split()[1]))] == wanted and len(used) == 8, f"{used}")
        alltext = " ".join(set_values(layer) for layer in layers)
        generic = ["Your Trip Title", "Thanks for watching", "Place Name", "Day 1", "Day 6", "Stop 1", "Stop 6"]
        missing_text = [t for t in generic if t not in alltext]
        left = [t for t in DEMO_TEXT if t in alltext]
        check(f"{tag}: every title holds the generic text, none of the demo's is left", not missing_text and not left,
              f"missing {missing_text}, left over {left}")
        by_comp = {}
        for layer in layers:
            src = items.get(str(layer["source"].get("item")), {}) if layer["source"].get("type") == "Comp" else {}
            by_comp.setdefault(src.get("name"), []).append(layer)
        wrong = []
        for begin, secs, seg in shots:
            if seg.get("card"):
                found = [l for l in by_comp.get(template_name(seg["card"]), [])
                         if abs(l["in_point"] / ticks - begin) < 0.05]
                if not found:
                    wrong.append(f"card {seg['card']} at {begin}")
            for o in seg.get("overlays", []):
                if o["template"].endswith("corner_logo"):
                    continue
                name = template_name(o["template"])
                at = begin + o.get("at", 0)
                if not any(abs(l["in_point"] / ticks - at) < 0.05 for l in by_comp.get(name, [])):
                    wrong.append(f"{name} at {at:.1f}")
        check(f"{tag}: every overlay and map card of the demo is there, starting where the demo's does", not wrong, f"{wrong}")
        logos = by_comp.get(template_name("logos/corner_logo"), [])
        check(f"{tag}: one Corner Logo layer covers the whole video",
              len(logos) == 1 and logos[0]["in_point"] == 0 and abs(logos[0]["out_point"] / ticks - total) < 0.05, f"{len(logos)} layers")
        flat = []
        for begin, secs, seg in shots:
            png = pathlib.Path(tmp) / f"{variant}_{begin}.png"
            subprocess.run([cli, "render-frame", str(project), "--time", str(begin + min(2.5, secs - 1)), "--max-side", "320",
                            "--out", str(png)], capture_output=True)
            if not png.is_file():
                flat.append(f"{begin}: no picture")
                continue
            stat = ImageStat.Stat(Image.open(png).convert("L"))
            if stat.mean[0] < 8 or stat.stddev[0] < 5:
                flat.append(f"{begin}: mean {stat.mean[0]:.0f}, spread {stat.stddev[0]:.0f}")
        check(f"{tag}: a still at each shot is a picture", not flat, f"{flat}")


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--effectcraft-cli", required=True)
    a = ap.parse_args()
    results = []

    def check(name, ok, detail):
        results.append(ok)
        print(("PASS " if ok else "FAIL ") + name + ": " + detail.strip().replace("\n", " | "))

    for variant in ("16x9", "9x16"):
        test_variant(a.effectcraft_cli, variant, check)
    print(f"\n{sum(results)} of {len(results)} checks pass")
    sys.exit(0 if all(results) else 1)


if __name__ == "__main__":
    main()
