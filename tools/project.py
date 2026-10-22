"""RECIPE1 step 4: a two-shot project kit for Pixie to open in the EffectCraft app.

  python3 build2.py KIT_FOLDER

KIT_FOLDER/Trip Video Test.ecproj, Photos/Photo_1.jpg, Photo_2.jpg (placeholders), Template Media/ (the templates' own sample
pictures, copied in so the folder is complete). Shot 1 (0-4.5 s): Photo_1 through Fill the Frame, Title "Your Trip Title".
Shot 2 (4-8 s): Photo_2 fading in over 0.5 s, Box Wipe lower third "Place Name" / "Day 1". Each template is imported once; every
shot that uses it is a layer of that one comp with its own values. Each stage runs in its own effectcraft-cli process on the
saved project, so later stages use the ids earlier ones returned.
"""
import json
import pathlib
import shutil
import subprocess
import sys

CLI = str(pathlib.Path.home() / "projects/storytold/effectcraft/target/release/effectcraft-cli")
E = pathlib.Path.home() / "projects/pixies-craft-templates/effectcraft"
KIT = pathlib.Path(sys.argv[1]).resolve()
PROJ = KIT / "Trip Video Test.ecproj"


def stage(*cmds, first=False):
    args = [CLI, "run"]
    for c, p in cmds:
        args += [c, json.dumps(p)]
    args += (["--empty", "--save-as", str(PROJ)] if first else [str(PROJ), "--save"]) + ["--json"]
    r = subprocess.run(args, capture_output=True, text=True)
    if r.returncode:
        sys.exit(f"failed: {r.stdout[:3000]}\n{r.stderr[:3000]}")
    return [x["result"] for x in json.loads(r.stdout.splitlines()[0])["result"]]


def ectemplate(t):
    return str(E / t / "effectcraft-0.13" / "templates" / f"{t.split('/')[-1]}_16x9.ectemplate")


if __name__ == "__main__":
    shutil.rmtree(KIT, ignore_errors=True)
    (KIT / "Photos").mkdir(parents=True)
    for i in (1, 2):   # the labelled Pixabay photos (Pixie's picks 1b, 1e), made by pixabay/label.py
        shutil.copyfile(pathlib.Path(sys.argv[2]) / f"Photo_{i}.jpg", KIT / "Photos" / f"Photo_{i}.jpg")
    names = ["utility/fill_frame", "titles/title", "lower_thirds/box_wipe"]
    r = stage(("comp.new", {"name": "Trip Video", "width": 1920, "height": 1080, "frameRate": 24, "duration": 8}),
              ("file.import", {"paths": [str(KIT / "Photos/Photo_1.jpg"), str(KIT / "Photos/Photo_2.jpg")], "sequence": False}),
              *[("essential.importTemplate", {"path": ectemplate(n), "addToComp": False}) for n in names],
              ("project.summary", {}), first=True)
    comp, (photo1, photo2) = r[0]["comp"], r[1]["items"]
    fill, title_c, lower_c = (x["comp"] for x in r[2:5])
    # Copy each template's own sample pictures into the kit and point the project at the copies
    (KIT / "Template Media").mkdir()
    relinks = []
    for item in json.loads(PROJ.read_text())["items"].values():
        path = (item.get("kind") or {}).get("path") if isinstance(item.get("kind"), dict) else None
        if path and not pathlib.Path(path).is_relative_to(KIT):
            copy = KIT / "Template Media" / f"{len(relinks) + 1}_{pathlib.Path(path).name}"
            shutil.copyfile(path, copy)
            relinks.append(("footage.relink", {"item": item["id"], "path": str(copy)}))
    stage(*relinks)
    print("comp", comp, "photos", photo1, photo2, "template comps", fill, title_c, lower_c, "media copied", len(relinks))
    # Bottom to top: shot 1, shot 2 (above, so its fade-in shows over shot 1), title, lower third
    r = stage(("comp.open", {"comp": comp}),
              ("layer.addItem", {"item": fill, "time": 0}), ("layer.addItem", {"item": fill, "time": 4}),
              ("layer.addItem", {"item": title_c, "time": 0}), ("layer.addItem", {"item": lower_c, "time": 4.3}))
    shot1, shot2, title, lower = (x["layer"] for x in r[1:])
    stage(("comp.open", {"comp": comp}),
          ("essential.set", {"layer": shot1, "control": "Media", "item": photo1}),
          ("essential.set", {"layer": shot1, "control": "Duration", "value": 4.5}),
          ("essential.set", {"layer": shot2, "control": "Media", "item": photo2}),
          ("essential.set", {"layer": shot2, "control": "Duration", "value": 4}),
          ("essential.set", {"layer": title, "control": "Title", "value": "Your Trip Title"}),
          ("essential.set", {"layer": title, "control": "Label", "value": "Where you went"}),
          ("essential.set", {"layer": title, "control": "Duration", "value": 4}),
          ("essential.set", {"layer": lower, "control": "Title", "value": "Place Name"}),
          ("essential.set", {"layer": lower, "control": "Subtitle", "value": "Day 1"}),
          ("essential.set", {"layer": lower, "control": "Duration", "value": 3.5}),
          ("layer.timing", {"layers": [shot1], "start": 0, "in": 0, "out": 4.5}),
          ("layer.timing", {"layers": [title], "start": 0, "in": 0, "out": 4.0}),
          ("layer.timing", {"layers": [shot2], "start": 4.0, "in": 4.0, "out": 8.0}),
          ("layer.timing", {"layers": [lower], "start": 4.3, "in": 4.3, "out": 8.0}),
          ("prop.addKey", {"layer": shot2, "path": "transform/opacity", "time": 4.0, "timeBase": "comp", "value": 0}),
          ("prop.addKey", {"layer": shot2, "path": "transform/opacity", "time": 4.5, "timeBase": "comp", "value": 100}))
    # Names on the timeline and folders in the Project panel, so it is plain what to replace (PLAN.md, RECIPE1 fixes 1-2)
    summary = stage(("project.summary", {}))[0]["items"]
    template_folders = [i["id"] for i in summary if i["type"] == "Folder" and i["parent"] is None]
    r = stage(("comp.open", {"comp": comp}),
              ("layer.rename", {"layer": shot1, "name": "Shot 1 · Photo_1"}),
              ("layer.rename", {"layer": shot2, "name": "Shot 2 · Photo_2"}),
              ("layer.rename", {"layer": title, "name": "Title"}),
              ("layer.rename", {"layer": lower, "name": "Place Name (Box Wipe)"}),
              ("project.newFolder", {"name": "Photos – replace these"}),
              ("project.newFolder", {"name": "Templates (no need to edit)"}))
    photos_f, templates_f = (x["item"] if isinstance(x, dict) and "item" in x else x for x in r[5:7])
    stage(("project.move", {"items": [photo1, photo2], "folder": photos_f}),
          ("project.move", {"items": template_folders, "folder": templates_f}))
    print("layers", shot1, shot2, title, lower, "->", PROJ)
