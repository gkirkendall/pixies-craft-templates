"""Helpers for a template's build/build.py: drive EffectCraft's command-line tool to make a project and export it as a template.

  from ecbuild import Project
  p = Project(cli, workdir / "route_leg.ecproj", "Route Leg", 1920, 1080, fps=24, duration=5)
  p.run(("layer.newNull", {"name": "Controls"}))
  p.expression("Pin", "transform/position", "...")
  p.export(out_template, "Route Leg")

Every call loads the project, runs its commands in the comp and saves, so a failed step stops the build with the CLI's message.
Lessons from building the map templates are in PLAN.md (SKILL1) and the comments below.
"""
import json
import pathlib
import shutil
import subprocess
import sys


def find_cli(name):
    cli = shutil.which(name) or (name if pathlib.Path(name).is_file() else None)
    if cli is None:
        sys.exit(f"effectcraft-cli not found ({name}); install EffectCraft's command-line tool or pass --effectcraft-cli")
    return cli


class Project:
    def __init__(self, cli, path, comp, width, height, fps, duration):
        self.cli, self.path, self.comp = cli, pathlib.Path(path), comp
        self.path.unlink(missing_ok=True)
        params = {"name": comp, "width": width, "height": height, "frameRate": fps, "duration": duration}
        self._call(["exec", "comp.new", "--params", json.dumps(params), "--empty", "--save-as", str(self.path)])

    def _call(self, args):
        r = subprocess.run([self.cli, *args], capture_output=True, text=True, cwd=self.path.parent)
        if r.returncode != 0:
            sys.exit(f"effectcraft-cli {' '.join(args[:3])}… failed:\n{r.stderr or r.stdout}")
        return r.stdout

    def run(self, *commands):
        """Run (command, params) pairs in order inside the comp, then save."""
        args = ["run", str(self.path), "comp.open", json.dumps({"comp": self.comp})]
        for cmd, params in commands:
            args += [cmd, json.dumps(params)]
        return self._call(args + ["--save"])

    def import_files(self, *paths):
        self._call(["exec", "file.import", json.dumps({"paths": [str(pathlib.Path(p).resolve()) for p in paths]}), str(self.path), "--save"])

    def tree(self, layer):
        return json.loads(self._call(["props", self.comp, layer, "--project", str(self.path), "--json"]))

    def set(self, layer, path, value, time=None):
        """A value, or a keyframe when time is given (seconds)."""
        params = {"layer": layer, "path": path, "value": value}
        if time is not None:
            params.update(time=time, timeBase="comp")
            return self.run(("prop.addKey", params))
        return self.run(("prop.set", params))

    def expression(self, layer, path, code):
        # prop.setExpression, not `set … --expression`: `set` needs a value of the property's type and a path property has none to give.
        return self.run(("prop.setExpression", {"layer": layer, "path": path, "expression": code}))

    def add_controls(self, layer, controls):
        """Expression-control effects on a layer, each renamed so expressions read it as effect("Name")("Point") and the like.
        controls: [(name, effect, value)], effect one of Point/Color/Slider/Checkbox/Dropdown Menu Control; a dropdown's value is
        (items, default item). Returns {name: param path}."""
        params = {"Point Control": "point", "Color Control": "color", "Slider Control": "slider", "Checkbox Control": "checkbox",
                  "Dropdown Menu Control": "menu"}
        before = len(self._effects(layer))
        self.run(*[("effect.apply", {"effect": effect, "layers": [layer]}) for _, effect, _ in controls])
        added = self._effects(layer)[before:]
        paths = {}
        for (name, effect, value), group in zip(controls, added):
            path = f"{group['path']}/{params[effect]}"
            if effect == "Dropdown Menu Control":
                # Stored 0-based (what a values file sets); expressions read it 1-based, as in After Effects.
                items, default = value
                self.run(("effect.editDropdown", {"layer": layer, "path": path, "items": items}))
                value = items.index(default)
            self.run(("prop.renameGroup", {"layer": layer, "prop": group["uid"], "name": name}),
                     ("prop.set", {"layer": layer, "path": path, "value": value}))
            paths[name] = path
        return paths

    def _effects(self, layer):
        groups = self.tree(layer)["properties"]["children"]
        return next((g["children"] for g in groups if g.get("match") == "effects"), [])

    def export(self, out, name):
        out = pathlib.Path(out).resolve()
        out.parent.mkdir(parents=True, exist_ok=True)
        self.run(("essential.exportTemplate", {"comp": self.comp, "path": str(out), "name": name}))
        return out


def find_path(tree, suffix):
    """The path of the first leaf property in a layer's tree (Project.tree) whose path ends with suffix, e.g. "fill/color"."""
    stack = [tree["properties"]]
    while stack:
        node = stack.pop(0)
        if node.get("path", "").endswith(suffix) and "children" not in node:
            return node["path"]
        stack += node.get("children", [])
    sys.exit(f"no property ending {suffix} on layer {tree.get('name')}")


def hex_colour(h):
    """#rrggbb as the [r, g, b, a] (0–1) a Color Control takes."""
    h = h.lstrip("#")
    return [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)] + [1.0]
