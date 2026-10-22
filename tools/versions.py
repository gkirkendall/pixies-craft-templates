"""Which app versions a template was tested on, and which of its version folders to use (PLAN.md, VER1).

A template folder (effectcraft/utility/fill_frame) holds one self-contained folder per app-version line (effectcraft-0.13, and
later e.g. effectcraft-0.15 when a release broke the 0.13 build). Each folder's template.json records "built_with" (the version
that exported it; older versions cannot open it) and "tested", the list tools/verify.py writes: one record per version tested.
The tested range is the oldest to the newest passing version. Used by render.py, verify.py and catalog.py.
"""
import json
import pathlib
import re
import subprocess
import sys

APP_NAMES = {"effectcraft": "EffectCraft", "figcraft": "FigCraft", "vectorcraft": "VectorCraft", "filmcraft": "FilmCraft"}
FOLDER = re.compile(r"^(effectcraft|figcraft|vectorcraft|filmcraft)-[0-9]+\.[0-9]+(\.[0-9]+)?$")


def parse(v):
    return tuple(int(x) for x in v.split("."))


def folder_name(app, built_with):
    """effectcraft-0.13 for a folder first built with 0.13.0; effectcraft-0.13.5 for one first built with 0.13.5."""
    major, minor, patch = parse(built_with)
    return f"{app}-{major}.{minor}" + (f".{patch}" if patch else "")


def cli_version(cli):
    """The version an app's command-line tool reports ("effectcraft-cli 0.13.0" → "0.13.0")."""
    r = subprocess.run([cli, "--version"], capture_output=True, text=True)
    m = re.search(r"([0-9]+\.[0-9]+\.[0-9]+)", r.stdout + r.stderr)
    if r.returncode or not m:
        sys.exit(f"{cli} --version did not give a version:\n{r.stdout}{r.stderr}")
    return m.group(1)


class Folder:
    def __init__(self, path):
        self.path = pathlib.Path(path)
        self.manifest = json.loads((self.path / "template.json").read_text())

    @property
    def name(self):
        return self.path.name

    @property
    def built_with(self):
        return self.manifest["built_with"]

    @property
    def frozen(self):
        return self.manifest.get("frozen", False)

    def passed(self):
        return sorted((r["version"] for r in self.manifest["tested"] if r["result"] == "pass"), key=parse)

    def tested_range(self):
        """(oldest pass, newest pass), or None if it has never passed."""
        p = self.passed()
        return (p[0], p[-1]) if p else None

    def range_text(self):
        r = self.tested_range()
        return "not tested yet" if r is None else r[0] if r[0] == r[1] else f"{r[0]}–{r[1]}"

    def covers(self, version):
        """Tested on this version, or between two passing versions with no failure recorded on it."""
        r = self.tested_range()
        failed = any(t["version"] == version and t["result"] == "fail" for t in self.manifest["tested"])
        return r is not None and parse(r[0]) <= parse(version) <= parse(r[1]) and not failed

    def opens_in(self, version):
        return parse(self.built_with) <= parse(version)


def folders(template):
    """A template's version folders, oldest first. `template` is the template folder (or one of its version folders)."""
    template = pathlib.Path(template)
    if (template / "template.json").is_file() and FOLDER.match(template.name):
        template = template.parent
    found = [Folder(p) for p in sorted(template.iterdir()) if p.is_dir() and FOLDER.match(p.name) and (p / "template.json").is_file()]
    return sorted(found, key=lambda f: parse(f.built_with))


def choose(template, version, folder=None):
    """The version folder to use with this app version, and a warning (or None).

    A version folder given as the template, or --folder by name, is used as asked. Otherwise: the newest folder whose tested
    range includes the version; else the newest folder the version can open, with a warning; else exit with why."""
    template = pathlib.Path(template)
    all_folders = folders(template)
    if not all_folders:
        sys.exit(f"{template}: no version folders (expected e.g. {template}/effectcraft-0.13 with a template.json)")
    name = all_folders[-1].manifest["name"]
    if FOLDER.match(template.name) and (template / "template.json").is_file():
        folder = template.name
    if folder:
        chosen = next((f for f in all_folders if f.name == folder), None)
        if chosen is None:
            sys.exit(f"{name}: no folder {folder} ({', '.join(f.name for f in all_folders)})")
        if not chosen.opens_in(version):
            sys.exit(f"{name}: {chosen.name} was built with {chosen.manifest['app']} {chosen.built_with}, which {version} cannot open")
        return chosen, None if chosen.covers(version) else untested(name, chosen, version)
    covering = [f for f in all_folders if f.covers(version)]
    if covering:
        return covering[-1], None
    openable = [f for f in all_folders if f.opens_in(version)]
    if not openable:
        sys.exit(f"no folder of {name} opens in {APP_NAMES[all_folders[0].manifest['app']]} {version} (the oldest, {all_folders[0].name}, was built with "
                 f"{all_folders[0].built_with})")
    return openable[-1], untested(name, openable[-1], version)


def untested(name, folder, version):
    app_name = APP_NAMES[folder.manifest["app"]]
    if folder.tested_range() is None:
        return f"warning: {name} ({folder.name}) has not passed a test yet; run tools/verify.py to test it with {app_name} {version}."
    return (f"warning: {name} ({folder.name}) was tested with {app_name} {folder.range_text()}; you have {version}. "
            f"Run tools/verify.py to test it, or use {app_name} {folder.range_text()}.")
