#!/usr/bin/env python3
"""Build the trip-video kit: an EffectCraft project with the trip demo's shots, generic text and Pixabay photos (PLAN.md, RECIPE1;
KIT1.md).

  python3 tools/project.py --effectcraft-cli PATH --out project_templates/trip_video [--variant 16x9|9x16|both]

Writes OUT/Trip Video 16x9.ecproj (and 9x16), Logo/Logo.png (a placeholder made here), Template Media/ (the templates' own sample
pictures and the example map pictures, copied in so every path in the project is inside OUT) and Music/README.txt; OUT/Photos/
holds Photo_1.jpg ... Photo_8.jpg already. The shots, their lengths and the overlays' timing come from
demo/australia_trip/demo.json, so the project follows the demo; only the text is generic. Each stage runs in its own
effectcraft-cli process on the saved project, so later stages use the ids earlier ones returned. Needs Pillow, the Natural Earth data
(`python3 tools/maps.py fetch`) and, for the short legs' roads, a connection to an Overpass server (tools/maps.py).
"""
import argparse
import json
import pathlib
import shutil
import subprocess
import sys
import tempfile

ROOT = pathlib.Path(__file__).resolve().parents[1]
EFFECTCRAFT = ROOT / "effectcraft"
DEMO = ROOT / "demo" / "australia_trip" / "demo.json"
STOPS = ROOT / "project_templates" / "trip_video" / "Make Maps" / "my.stops.json"
SIZES = {"16x9": (1920, 1080), "9x16": (1080, 1920)}
FADE = 0.5   # the crossfade between shots (demo.json crossfade)
TEMPLATES = {"fill": "utility/fill_frame", "title": "titles/animated_title", "logo": "logos/corner_logo",
             "lower": "lower_thirds/basic", "leg": "maps/route_leg", "locator": "maps/locator", "signoff": "titles/sign_off"}
# Generic text, by the demo's segment: the lower third's Subtitle, the title and the sign-off.
LOWER = {2: "Day 1", 3: "Day 2", 5: "Day 3", 6: "Day 4", 8: "Day 5", 9: "Day 6"}
TITLE, SIGN_OFF = "Your Trip Title", "Thanks for watching"
LEGS = {2: "leg01", 4: "leg02", 5: "leg03", 7: "leg04", 9: "leg05"}   # the demo's segments that show a route leg
MEDIA_CONTROLS = ("Map", "Media", "Logo")


class Builder:
    def __init__(self, cli, project):
        self.cli, self.project = cli, project

    def stage(self, *cmds, first=False):
        args = [self.cli, "run"]
        for name, params in cmds:
            args += [name, json.dumps(params)]
        args += (["--empty", "--save-as", str(self.project)] if first else [str(self.project), "--save"]) + ["--json"]
        r = subprocess.run(args, capture_output=True, text=True)
        if r.returncode:
            sys.exit(f"failed: {r.stdout[:3000]}\n{r.stderr[:3000]}")
        return [x["result"] for x in json.loads(r.stdout.splitlines()[0])["result"]]


def make_logo(path):
    """A plain placeholder: 'Your Logo' in Inter Bold, white with a soft shadow, on a transparent square."""
    from PIL import Image, ImageDraw, ImageFilter, ImageFont
    font = ImageFont.truetype(str(ROOT / "fonts" / "inter" / "Inter[opsz,wght].ttf"), 120)
    font.set_variation_by_name("Bold")
    size = 512
    layer = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    shadow = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    for img, colour, dx in ((shadow, (0, 0, 0, 200), 4), (layer, (255, 255, 255, 255), 0)):
        d = ImageDraw.Draw(img)
        for i, line in enumerate(("Your", "Logo")):
            d.text(((size - d.textlength(line, font=font)) / 2 + dx, 110 + i * 150 + dx), line, font=font, fill=colour)
    path.parent.mkdir(parents=True, exist_ok=True)
    Image.alpha_composite(shadow.filter(ImageFilter.GaussianBlur(6)), layer).save(path)


def make_maps(variant, work):
    """The example map pictures and their values files, drawn by tools/maps.py for the generic stops."""
    maps = str(ROOT / "tools" / "maps.py")
    for args in (["route-legs", "--out", str(work / "legs"), "--inset"], ["locator", "--stop", "0", "--out", str(work / "loc")]):
        subprocess.run([sys.executable, maps, args[0], "--stops", str(STOPS), "--variant", variant, *args[1:]],
                       check=True, capture_output=True)


def manifest(key):
    return json.loads((EFFECTCRAFT / TEMPLATES[key] / "effectcraft-0.13" / "template.json").read_text())


def template_file(key, variant):
    name = TEMPLATES[key].split("/")[-1]
    return str(EFFECTCRAFT / TEMPLATES[key] / "effectcraft-0.13" / "templates" / f"{name}_{variant}.ectemplate")


def plan(demo):
    """The shots and overlays from demo.json: each segment starts a crossfade before the previous one ends. The Corner Logo is one
    layer over the whole video, so it is left out of the overlays."""
    by_path = {f"effectcraft/{v}": k for k, v in TEMPLATES.items()}
    shots, start = [], 0.0
    for i, seg in enumerate(demo["segments"]):
        overlays = [(by_path[o["template"]], o) for o in seg.get("overlays", []) if by_path[o["template"]] != "logo"]
        key = by_path[seg["card"]] if seg.get("card") else "fill"
        shots.append({"index": i, "start": start, "seconds": seg["seconds"], "key": key, "overlays": overlays})
        start += seg["seconds"] - FADE
    return shots, start + FADE


def build(cli, out, variant):
    w, h = SIZES[variant]
    shots, total = plan(json.loads(DEMO.read_text()))
    project = out / f"Trip Video {variant}.ecproj"
    project.unlink(missing_ok=True)
    work = pathlib.Path(tempfile.mkdtemp())
    make_maps(variant, work)
    logo = out / "Logo" / "Logo.png"
    if not logo.is_file():
        make_logo(logo)
    media = out / "Template Media"
    media.mkdir(exist_ok=True)
    map_files = []
    for src in sorted((work / "legs").glob("map_*.png")) + sorted((work / "loc").glob("map_*.png")):
        shutil.copyfile(src, media / src.name)
        map_files.append(media / src.name)
    values = {f.name.split("_")[0]: json.loads(f.read_text())   # leg01 ... leg05, locator00
              for f in sorted((work / "legs").glob("*.values.json")) + sorted((work / "loc").glob("*.values.json"))}
    photo_files = [out / "Photos" / f"Photo_{i}.jpg" for i in range(1, 9)]
    b = Builder(cli, project)
    r = b.stage(("comp.new", {"name": "Trip Video", "width": w, "height": h, "frameRate": 24, "duration": round(total, 2)}),
                ("file.import", {"paths": [str(p) for p in photo_files], "sequence": False}),
                ("file.import", {"paths": [str(logo)], "sequence": False}),
                ("file.import", {"paths": [str(p) for p in map_files], "sequence": False}),
                *[("essential.importTemplate", {"path": template_file(k, variant), "addToComp": False}) for k in TEMPLATES],
                first=True)
    comp = r[0]["comp"]
    photo_items, logo_item = r[1]["items"], r[2]["items"][0]
    map_items = dict(zip((p.name for p in map_files), r[3]["items"]))
    tcomp = {k: x["comp"] for k, x in zip(TEMPLATES, r[4:])}
    # Copy each template's own sample pictures into the kit and point the project at the copies
    relinks = []
    for item in json.loads(project.read_text())["items"].values():
        path = (item.get("kind") or {}).get("path") if isinstance(item.get("kind"), dict) else None
        if path and not pathlib.Path(path).is_relative_to(out):
            copy = media / f"{pathlib.Path(path).parent.name}_{pathlib.Path(path).name}".replace(" ", "_")
            shutil.copyfile(path, copy)
            relinks.append(("footage.relink", {"item": item["id"], "path": str(copy)}))
    if relinks:
        b.stage(*relinks)
    # Layers, bottom to top: the shots in order (each above the one before, so its fade-in shows), then the overlays, then the logo
    overlay_list = [(s, k, o) for s in shots for k, o in s["overlays"]]
    r = b.stage(("comp.open", {"comp": comp}),
                *[("layer.addItem", {"item": tcomp[s["key"]], "time": s["start"]}) for s in shots],
                *[("layer.addItem", {"item": tcomp[k], "time": s["start"] + o.get("at", 0)}) for s, k, o in overlay_list],
                ("layer.addItem", {"item": tcomp["logo"], "time": 0}))
    layers = [x["layer"] for x in r[1:]]
    overlay_layers, logo_layer = layers[len(shots):-1], layers[-1]
    sets, timing, keys, names = [], [], [], []

    def put(layer, key, vals):
        """Set controls; a dropdown is set by its item's 0-based number, as tools/render.py does."""
        controls = {c["name"]: c for c in manifest(key)["controls"]}
        for control, value in vals.items():
            if controls[control]["type"] == "dropdown":
                value = controls[control]["options"].index(value)
            sets.append(("essential.set", {"layer": layer, "control": control,
                                           **({"item": value} if control in MEDIA_CONTROLS else {"value": value})}))

    def leg_values(name, **extra):
        return {**values[name], **extra, "Map": map_items[values[name]["Map"]]}

    def fade(layer, start, to, frm):
        return [("prop.addKey", {"layer": layer, "path": "transform/opacity", "time": t, "timeBase": "comp", "value": v})
                for t, v in ((start, frm), (start + FADE, to))]

    photo_n = 0
    for s, layer in zip(shots, layers):
        i, end = s["index"], s["start"] + s["seconds"]
        if s["key"] == "fill":
            put(layer, "fill", {"Media": photo_items[photo_n], "Duration": s["seconds"]})
            photo_n += 1
            names.append((layer, f"Shot {i + 1} · Photo_{photo_n}"))
        elif s["key"] == "locator":
            put(layer, "locator", leg_values("locator00"))
            names.append((layer, f"Shot {i + 1} · Locator map card"))
        else:
            put(layer, "leg", leg_values(LEGS[i], **{"Corner Inset": False}))
            names.append((layer, f"Shot {i + 1} · Route Leg map card"))
        timing.append(("layer.timing", {"layers": [layer], "start": s["start"], "in": s["start"], "out": end}))
        if i:
            keys += fade(layer, s["start"], 100, 0)
    for (s, k, o), layer in zip(overlay_list, overlay_layers):
        i, end, start = s["index"], s["start"] + s["seconds"], s["start"] + o.get("at", 0)
        v = o["values"]
        if k == "title":
            given = json.loads(pathlib.Path(v["file"].replace("{root}", str(ROOT))).read_text())
            put(layer, k, {**given, **v.get("set", {}), "Text": TITLE})
            names.append((layer, "Title (Animated Title)"))
        elif k == "lower":
            put(layer, k, {"Title": "Place Name", "Subtitle": LOWER[i]})
            names.append((layer, f"Place Name · {LOWER[i]} (Lower Third)"))
        elif k == "leg":
            put(layer, k, leg_values(LEGS[i]))   # the corner inset, as drawn
            names.append((layer, f"Shot {i + 1} · Route Leg (corner inset)"))
        else:
            put(layer, k, {**{x: y for x, y in v.items() if x != "Fade"}, "Text": SIGN_OFF})
            names.append((layer, "Sign-off"))
        timing.append(("layer.timing", {"layers": [layer], "start": start, "in": start, "out": end}))
        if i < len(shots) - 1:   # leaves with its shot, as in the demo's crossfade
            keys += fade(layer, end - FADE, 0, 100)
    put(logo_layer, "logo", {"Logo": logo_item, "Fade": "Fade In and Out", "Duration": round(total, 2)})
    timing.append(("layer.timing", {"layers": [logo_layer], "start": 0, "in": 0, "out": round(total, 2)}))
    names.append((logo_layer, "Corner Logo (whole video)"))
    b.stage(("comp.open", {"comp": comp}), *sets, *timing, *keys)
    # Names on the timeline and folders in the Project panel, so it is plain what to replace
    summary = b.stage(("project.summary", {}))[0]["items"]
    template_folders = [x["id"] for x in summary if x["type"] == "Folder" and x["parent"] is None]
    r = b.stage(("comp.open", {"comp": comp}),
                *[("layer.rename", {"layer": layer, "name": name}) for layer, name in names],
                *[("project.newFolder", {"name": n}) for n in
                  ("Photos – replace these", "Logo – replace this", "Maps (examples, see Make Maps)", "Templates (no need to edit)")])
    folders = [x["item"] if isinstance(x, dict) and "item" in x else x for x in r[-4:]]
    b.stage(("project.move", {"items": photo_items, "folder": folders[0]}),
            ("project.move", {"items": [logo_item], "folder": folders[1]}),
            ("project.move", {"items": list(map_items.values()), "folder": folders[2]}),
            ("project.move", {"items": template_folders, "folder": folders[3]}))
    shutil.rmtree(work, ignore_errors=True)
    print(f"built {project} ({len(shots)} shots, {len(overlay_list) + 1} overlays, {total:.1f} s)")


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--effectcraft-cli", required=True, help="path to effectcraft-cli (0.13 or later)")
    ap.add_argument("--out", required=True, type=pathlib.Path, help="the kit folder (project_templates/trip_video)")
    ap.add_argument("--variant", choices=[*SIZES, "both"], default="both")
    a = ap.parse_args()
    out = a.out.resolve()
    (out / "Music").mkdir(parents=True, exist_ok=True)
    (out / "Music" / "README.txt").write_text("Put your music file here, then drag it into the timeline.\n")
    for v in SIZES if a.variant == "both" else [a.variant]:
        build(a.effectcraft_cli, out, v)


if __name__ == "__main__":
    main()
