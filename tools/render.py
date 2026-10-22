#!/usr/bin/env python3
"""Fill and render one template from its manifest and a values file.

  python3 tools/render.py effectcraft/maps/route_leg --variant 16x9 --values my.values.json --out leg.mp4
  python3 tools/render.py effectcraft/maps/route_leg --variant 16x9 --values my.values.json --out leg.png --frame 3.0

The values file maps control names to values ({"From Name": "Point Ritchie", "Map": "maps/leg1.png"}); picture (media) values are
paths, relative to the values file. The output format follows the variant's "output" in template.json (h264 MP4, or ProRes 4444 with
alpha for overlays); --frame renders one still PNG instead. The template's version folder is chosen by the installed
EffectCraft's version (tools/versions.py): the one tested on it, else the newest it can open, with a warning; --folder picks one,
--which shows the choice. A template with a number control named "Duration" (one whose comp is
made long, like Fill the Frame) is rendered only up to that many seconds; one with a number control named "Clip Length" gets the
exact length of its media clip from ffprobe, unless the values file gives it. EffectCraft's command-line tool is found on the PATH, or given with
--effectcraft-cli.

Before rendering it checks that every font the template will use is installed (each font control's value, or its default when the
values file leaves it alone), because EffectCraft draws a missing font in the template's own font without a word. If one is
missing it renders nothing and says which, with the font file to install from this repository's fonts/ when there is one.
--check-fonts runs only that check.
"""
import argparse
import difflib
import json
import pathlib
import shutil
import subprocess
import sys
import tempfile

import versions

ROOT = pathlib.Path(__file__).resolve().parents[1]
OUTPUT_ARGS = {"h264": ["--format", "h264"], "prores4444": ["--format", "prores", "--prores", "4444", "--channels", "rgba"]}


def resolved_values(manifest, values_path, tmp):
    """Values with media paths made absolute and every name checked against the manifest's controls.

    Each media file is handed to EffectCraft from tmp under the control's own name ("Media.jpg"), as a link (a copy where links
    are not allowed). EffectCraft 0.13 imports a numbered file whose folder holds other numbered files (IMG_5322.jpg beside
    IMG_5156.jpg) as one image sequence, and shows the missing frames as colour bars; it also shows a file with an upper-case
    extension (.JPG) as missing. A HEIC/HEIF photo, which EffectCraft cannot read, is converted to PNG in tmp with ffmpeg."""
    values = json.loads(values_path.read_text()) if values_path else {}
    controls = {c["name"].lower(): c for c in manifest["controls"]}
    for name, value in values.items():
        control = controls.get(name.lower())
        if control is None:
            sys.exit(f"{values_path}: {name!r} is not a control of {manifest['id']} ({', '.join(c['name'] for c in manifest['controls'])})")
        if control["type"] == "dropdown":
            # By item name; EffectCraft 0.13 takes only the item's 0-based number (expressions then read it 1-based).
            names = [o.lower() for o in control["options"]]
            if not isinstance(value, str) or value.lower() not in names:
                sys.exit(f"{values_path}: {name} must be one of {', '.join(map(repr, control['options']))}, not {value!r}")
            values[name] = names.index(value.lower())
        if control["type"] == "media" and isinstance(value, str) and value:
            path = (values_path.parent / value).resolve()
            if not path.is_file():
                sys.exit(f"{values_path}: {name} file {path} not found")
            if path.suffix.lower() in (".heic", ".heif"):
                copy = pathlib.Path(tmp) / f"{name}.png"
                r = subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(path), "-frames:v", "1", str(copy)], capture_output=True, text=True)
                if r.returncode:
                    sys.exit(f"{values_path}: {name}: ffmpeg could not convert {path} (HEIC needs ffmpeg 7 or later):\n{r.stderr}")
                path = copy
            else:
                alone = pathlib.Path(tmp) / f"{name}{path.suffix.lower()}"
                try:
                    alone.symlink_to(path)
                except OSError:
                    shutil.copyfile(path, alone)
                path = alone
            values[name] = str(path)
    # Clip Length: the exact length of the first media value that is a video, from ffprobe (it honours the MP4 edit list, which
    # EffectCraft 0.13 ignores, so its own reading is a frame long and a looped clip would hold its last frame).
    clip_length = controls.get("clip length")
    if clip_length and clip_length["type"] == "number" and "Clip Length" not in values:
        for c in manifest["controls"]:
            if c["type"] == "media" and values.get(c["name"]):
                seconds = video_length(values[c["name"]])
                if seconds:
                    values["Clip Length"] = seconds
                break
    return values


def video_length(path):
    """A video's length in seconds as ffprobe reports it, or None for a still picture (or when ffprobe is missing)."""
    try:
        r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=format_name,duration", "-of", "default=nw=1", path],
                           capture_output=True, text=True)
    except FileNotFoundError:
        return None
    info = dict(line.split("=", 1) for line in r.stdout.splitlines() if "=" in line)
    if r.returncode or "image" in info.get("format_name", "") or "pipe" in info.get("format_name", ""):
        return None
    try:
        return float(info.get("duration", "")) or None
    except ValueError:
        return None


def installed_fonts(cli):
    """{family: [styles]} of the fonts EffectCraft can use, or None if its command-line tool can't list them."""
    r = subprocess.run([cli, "exec", "text.fonts"], capture_output=True, text=True)
    try:
        return {f["family"]: f.get("styles", []) for f in json.loads(r.stdout)["families"]}
    except (ValueError, KeyError, TypeError):
        return None


def font_installed(value, fonts):
    """Whether a font value ("Family Style", "Family" or {font, style}) names an installed font."""
    if isinstance(value, dict):
        family, style = value.get("font"), value.get("style")
        return family in fonts and (style is None or style in fonts[family])
    if not isinstance(value, str):
        return False
    return any(value == f or value.startswith(f + " ") and value[len(f) + 1:] in styles for f, styles in fonts.items())


def squash(name):
    return "".join(c for c in name.lower() if c.isalnum())


def font_fix(value, fonts):
    """How to get a missing font: this repository's file for it, else the nearest installed name."""
    name = value if isinstance(value, str) else f"{value.get('font', '')} {value.get('style', '')}".strip()
    files = sorted((ROOT / "fonts").rglob("*.[ot]tf"))
    match = [f for f in files if squash(f.stem) == squash(name)] or [f for f in files if squash(f.stem) == squash(name) + "regular"]
    if match:
        return f"install {match[0].relative_to(ROOT)} from this repository"
    names = [f"{f} {s}" for f, styles in fonts.items() for s in styles] + list(fonts)
    near = difflib.get_close_matches(name, names, n=1, cutoff=0.8)
    return f'not installed; did you mean "{near[0]}"?' if near else "not installed; install it, or pick an installed font"


def missing_fonts(manifest, values, cli):
    """Lines naming each font the render needs that isn't installed (empty when all are), or a warning when they can't be listed."""
    fonts = installed_fonts(cli)
    if fonts is None:
        print("warning: effectcraft-cli could not list its fonts, so they were not checked", file=sys.stderr)
        return []
    wanted = {c["name"]: values.get(c["name"], c.get("default")) for c in manifest["controls"] if c["type"] == "font"}
    return [f"  {name} {json.dumps(v, ensure_ascii=False)}: {font_fix(v, fonts)}" for name, v in wanted.items()
            if v is not None and not font_installed(v, fonts)]


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("template", help="template folder, e.g. effectcraft/maps/route_leg (or one of its version folders)")
    ap.add_argument("--variant", help="variant key from template.json, e.g. 16x9")
    ap.add_argument("--values", type=pathlib.Path, help="values file (JSON); omit to render the defaults")
    ap.add_argument("--out", type=pathlib.Path)
    ap.add_argument("--frame", type=float, help="render the still at this time (seconds) as PNG instead of the whole clip")
    ap.add_argument("--folder", help="use this version folder (e.g. effectcraft-0.13) instead of choosing by the installed version")
    ap.add_argument("--which", action="store_true", help="print the version folder that would be used, and why, then stop")
    ap.add_argument("--check-fonts", action="store_true", help="check only that the fonts it needs are installed; render nothing")
    ap.add_argument("--effectcraft-cli", default="effectcraft-cli", help="path to effectcraft-cli (default: on the PATH)")
    a = ap.parse_args()

    cli = shutil.which(a.effectcraft_cli) or (a.effectcraft_cli if pathlib.Path(a.effectcraft_cli).is_file() else None)
    if cli is None:
        sys.exit(f"effectcraft-cli not found ({a.effectcraft_cli}); install EffectCraft's command-line tool or pass --effectcraft-cli")
    template_dir = (ROOT / a.template) if not pathlib.Path(a.template).is_absolute() else pathlib.Path(a.template)
    version = versions.cli_version(cli)
    chosen, warning = versions.choose(template_dir, version, a.folder)
    if warning:
        print(warning, file=sys.stderr)
    if a.which:
        print(f"{chosen.path}  (EffectCraft {version}; tested with {chosen.range_text()})")
        return
    values = json.loads(a.values.read_text()) if a.values else {}
    missing = missing_fonts(chosen.manifest, values, cli)
    if missing:
        sys.exit(("Fonts missing" if a.check_fonts else "Fonts missing, so nothing was rendered") + ":\n" + "\n".join(missing))
    if a.check_fonts:
        needs = any(c["type"] == "font" for c in chosen.manifest["controls"])
        print(f"{chosen.manifest['name']}: " + ("every font it needs is installed" if needs else "uses no fonts"))
        return
    if not a.variant or not a.out:
        ap.error("--variant and --out are needed to render")
    folder, manifest = chosen.path, chosen.manifest
    if manifest["app"] != "effectcraft":
        sys.exit(f"{manifest['id']}: rendering {manifest['app']} templates is not supported yet")
    variant = next((v for v in manifest["variants"] if v["key"] == a.variant), None)
    if variant is None:
        sys.exit(f"{manifest['id']}: no variant {a.variant!r} ({', '.join(v['key'] for v in manifest['variants'])})")

    with tempfile.TemporaryDirectory() as tmp:
        values_file = pathlib.Path(tmp) / "values.json"
        values_file.write_text(json.dumps(resolved_values(manifest, a.values.resolve() if a.values else None, tmp)))
        # Render from a copy: EffectCraft unpacks a template's pictures into a "<name> Media" folder beside it.
        template = pathlib.Path(tmp) / pathlib.Path(variant["file"]).name
        shutil.copyfile(folder / variant["file"], template)
        cmd = [cli, "render-frame" if a.frame is not None else "render", "--template", str(template),
               "--values", str(values_file), "--out", str(a.out.resolve())]
        cmd += ["--time", str(a.frame)] if a.frame is not None else OUTPUT_ARGS.get(variant["output"], [])
        duration = next((c for c in manifest["controls"] if c["name"] == "Duration" and c["type"] == "number"), None)
        if duration and a.frame is None:
            values = json.loads(values_file.read_text())
            cmd += ["--end", str(values.get("Duration", duration["default"]))]
        if a.frame is not None and variant["output"] == "prores4444":
            cmd.append("--transparent")
        sys.exit(subprocess.run(cmd).returncode)


if __name__ == "__main__":
    main()
