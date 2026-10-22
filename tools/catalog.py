#!/usr/bin/env python3
"""Check every template against the repo's rules and regenerate the catalogue in README.md.

  python3 tools/catalog.py           check, then rewrite the catalogue between the README markers
  python3 tools/catalog.py --check   check only; exit 1 on any problem (for CI and before a commit)

Rules (PLAN.md, "Layout", "Decisions" and VER1): a template folder holds only version folders (effectcraft-0.13, …) and its
README.md, which this script writes. Each version folder's template.json passes schema/template.schema.json, its id is the template
folder, its folder name matches "built_with", it has a README.md and tests/run.py, it has passed tools/verify.py at least once
(app_min_version = the oldest pass), every variant file exists, every font it names has a folder under fonts/ with a licence file,
and every asset listed in its assets/SOURCES.md carries a licence that allows redistribution. WEB1: each has a style sheet
(previews/styles.jpg) made by tools/sheet.py from the current previews/styles.json and template version, and the web page
index.html is what tools/page.py would write now (this script rewrites it, as it does the README catalogue).
"""
import argparse
import json
import pathlib
import re
import sys

import versions

ROOT = pathlib.Path(__file__).resolve().parents[1]
APPS = ("effectcraft", "figcraft", "vectorcraft", "filmcraft")
ALLOWED_LICENCES = ("public domain", "cc0", "cc by", "ofl", "mit", "apache")  # PLAN.md: only freely redistributable assets
START, END = "<!-- catalog:start -->", "<!-- catalog:end -->"


def validate(value, schema, path="$"):
    """The subset of JSON Schema the manifest schema uses; returns a list of problems."""
    errors = []
    types = {"object": dict, "array": list, "string": str, "integer": int, "number": (int, float), "boolean": bool}
    t = schema.get("type")
    if t and not (isinstance(value, types[t]) and not (t in ("integer", "number") and isinstance(value, bool))):
        return [f"{path}: expected {t}"]
    if "enum" in schema and value not in schema["enum"]:
        errors.append(f"{path}: {value!r} is not one of {schema['enum']}")
    if isinstance(value, str):
        if len(value) < schema.get("minLength", 0):
            errors.append(f"{path}: empty")
        if "pattern" in schema and not re.search(schema["pattern"], value):
            errors.append(f"{path}: {value!r} does not match {schema['pattern']}")
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        if "minimum" in schema and value < schema["minimum"]:
            errors.append(f"{path}: below {schema['minimum']}")
        if "exclusiveMinimum" in schema and value <= schema["exclusiveMinimum"]:
            errors.append(f"{path}: must be above {schema['exclusiveMinimum']}")
    if isinstance(value, list):
        if len(value) < schema.get("minItems", 0) or len(value) > schema.get("maxItems", len(value)):
            errors.append(f"{path}: wrong number of items")
        for i, item in enumerate(value):
            errors += validate(item, schema.get("items", {}), f"{path}[{i}]")
    if isinstance(value, dict):
        for key in schema.get("required", ()):
            if key not in value:
                errors.append(f"{path}: missing {key}")
        props = schema.get("properties", {})
        for key, item in value.items():
            if key in props:
                errors += validate(item, props[key], f"{path}.{key}")
            elif schema.get("additionalProperties") is False:
                errors.append(f"{path}: unknown key {key}")
    return errors


def font_folder(family):
    return ROOT / "fonts" / re.sub(r"[^a-z0-9]+", "_", family.lower()).strip("_")


def check_template(manifest_path, schema):
    folder = manifest_path.parent
    rel = folder.relative_to(ROOT).as_posix()
    try:
        m = json.loads(manifest_path.read_text())
    except json.JSONDecodeError as e:
        return None, [f"{rel}/template.json: invalid JSON ({e})"]
    errors = [f"{rel}/template.json {e}" for e in validate(m, schema)]
    if errors:
        return None, errors
    for c in m["controls"]:
        if (c["type"] == "dropdown") != ("options" in c):
            errors.append(f"{rel}: control {c['name']}: options go with a dropdown and only a dropdown")
        elif c["type"] == "dropdown" and "default" in c and c["default"] not in c["options"]:
            errors.append(f"{rel}: control {c['name']}: default {c['default']!r} is not one of its options")
    if m.get("id") != folder.parent.relative_to(ROOT).as_posix():
        errors.append(f"{rel}: id {m.get('id')!r} does not match the template folder")
    if folder.name != versions.folder_name(m["app"], m["built_with"]):
        errors.append(f"{rel}: built with {m['built_with']}, so the folder should be {versions.folder_name(m['app'], m['built_with'])}")
    passed = versions.Folder(folder).passed()
    if not passed:
        errors.append(f"{rel}: no passing test recorded; run tools/verify.py")
    elif m["app_min_version"] != passed[0]:
        errors.append(f"{rel}: app_min_version {m['app_min_version']} is not the oldest passing version {passed[0]} (tools/verify.py sets it)")
    for needed in ("README.md", "tests/run.py"):
        if not (folder / needed).is_file():
            errors.append(f"{rel}: no {needed}")
    for demo in sorted((folder / "previews").glob("demo*.mp4")):   # DEMO1: each demo has its poster, its demo.json and the README
        poster = demo.with_name("poster" + demo.stem[4:] + ".jpg")
        for needed in (poster, demo.with_suffix(".json"), demo.with_name("README.md")):
            if not needed.is_file():
                errors.append(f"{rel}: {demo.name} has no {needed.name}")
    styles = folder / "previews" / "styles.json"   # WEB1: a current style sheet
    if not styles.is_file():
        errors.append(f"{rel}: no previews/styles.json (the style sheet's cells)")
    elif not styles.with_name("styles.jpg").is_file():
        errors.append(f"{rel}: no previews/styles.jpg; run tools/sheet.py {rel}/previews/styles.json")
    else:
        import sheet
        from PIL import Image
        made = Image.open(styles.with_name("styles.jpg")).info.get("comment", b"").decode(errors="replace")
        if made != sheet.stamp(styles):
            errors.append(f"{rel}: previews/styles.jpg is older than the template or its styles.json; run tools/sheet.py")
    for v in m.get("variants", []):
        if not (folder / v.get("file", "")).is_file():
            errors.append(f"{rel}: variant {v.get('key')} file {v.get('file')} is missing")
    for family in m.get("fonts", []):
        f = font_folder(family)
        if family != "Inter" and not f.is_dir():  # Inter also ships with EffectCraft; fonts/inter keeps a copy
            errors.append(f"{rel}: font {family!r} has no folder {f.relative_to(ROOT)}")
    sources = folder / "assets" / "SOURCES.md"
    if (folder / "assets").is_dir() and not sources.is_file():
        errors.append(f"{rel}: assets/ has no SOURCES.md")
    if sources.is_file():
        for line in sources.read_text().splitlines():  # a table: | File | Source | Licence |
            cells = [c.strip() for c in line.strip().strip("|").split("|")]
            if not line.startswith("|") or set(line) <= set("|-: ") or cells[0].lower() in ("file", "asset"):
                continue
            if not any(a in cells[-1].lower() for a in ALLOWED_LICENCES):
                errors.append(f"{rel}: asset {cells[0]!r} has licence {cells[-1]!r}, which does not allow redistribution")
    return m, errors


def check_fonts():
    errors = []
    for f in sorted((ROOT / "fonts").iterdir()) if (ROOT / "fonts").is_dir() else ():
        if f.is_dir() and not any(re.search(r"(ofl|licen[cs]e)", p.name, re.I) for p in f.rglob("*") if p.is_file()):
            errors.append(f"fonts/{f.name}: no licence file")
    return errors


def tested_text(template):
    """The current folder's range, then older folders: "0.13.0–0.14.1; 0.12.0 in effectcraft-0.12"."""
    fs = versions.folders(ROOT / template)
    current = [f for f in fs if not f.frozen] or fs
    parts = [current[-1].range_text()] + [f"{f.range_text()} in {f.name}" for f in fs if f is not current[-1]]
    return "; ".join(parts)


def catalogue(manifests):
    rows = ["| Template | App | Kind | Sizes | Tested with | Description |", "|---|---|---|---|---|---|"]
    latest = {}
    for m in manifests:
        if m["id"] not in latest or versions.parse(m["built_with"]) > versions.parse(latest[m["id"]]["built_with"]):
            latest[m["id"]] = m
    for m in sorted(latest.values(), key=lambda m: m["id"]):
        sizes = ", ".join(v["key"] for v in m["variants"])
        rows.append(f"| [{m['name']}]({m['id']}/) | {m['app']} | {m['kind']} | {sizes} | {tested_text(m['id'])} | {m['description']} |")
    return "\n".join(rows) if len(rows) > 2 else "_No templates yet._"


def template_readme(template):
    """The template folder's README.md: what it is, and which version folder to use with which app version."""
    fs = versions.folders(ROOT / template)
    m = fs[-1].manifest
    app = {"effectcraft": "EffectCraft", "figcraft": "FigCraft", "vectorcraft": "VectorCraft", "filmcraft": "FilmCraft"}[m["app"]]
    lines = [f"# {m['name']}", "", m["description"], "",
             f"Each folder below is complete and works on its own. Use the one tested with your {app} version; `tools/render.py`",
             "chooses it for you (`--which` shows the choice). The details, controls and examples are in each folder's README.", "",
             f"| Folder | Tested with {app} | Template version | Status |", "|---|---|---|---|"]
    for f in reversed(fs):
        status = "frozen (kept for older versions)" if f.frozen else "current"
        lines.append(f"| [{f.name}]({f.name}/README.md) | {f.range_text()} | {f.manifest['version']} | {status} |")
    lines += ["", "Written by `tools/catalog.py` from the test records `tools/verify.py` keeps; do not edit by hand.", ""]
    return "\n".join(lines)


def check_layout(template):
    """A template folder holds only version folders and its README.md."""
    rel = template.relative_to(ROOT).as_posix()
    return [f"{rel}: {p.name} does not belong here (only version folders such as effectcraft-0.13, and README.md)"
            for p in sorted(template.iterdir())
            if p.name not in ("README.md", ".DS_Store") and not (p.is_dir() and versions.FOLDER.match(p.name))]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true", help="check only; do not rewrite README.md")
    a = ap.parse_args()
    schema = json.loads((ROOT / "schema" / "template.schema.json").read_text())
    manifests, errors = [], check_fonts()
    template_dirs = set()
    for app in APPS:
        for path in sorted((ROOT / app).rglob("template.json")) if (ROOT / app).is_dir() else ():
            if "/tests/out/" in path.as_posix():
                continue
            if not versions.FOLDER.match(path.parent.name):
                errors.append(f"{path.parent.relative_to(ROOT)}: template.json must sit in a version folder (e.g. effectcraft-0.13)")
                continue
            template_dirs.add(path.parent.parent)
            m, e = check_template(path, schema)
            errors += e
            if m and not e:
                manifests.append(m)
    for template in sorted(template_dirs):
        errors += check_layout(template)
    import page as web   # tools/page.py
    page = web.build()
    if a.check and (not web.PAGE.is_file() or web.PAGE.read_text() != page):
        errors.append("index.html is out of date; run python3 tools/page.py (or tools/catalog.py)")
    for e in errors:
        print("FAIL", e)
    if not a.check:
        if not web.PAGE.is_file() or web.PAGE.read_text() != page:
            web.PAGE.parent.mkdir(exist_ok=True)
            web.PAGE.write_text(page)
            print("index.html written")
        readme = ROOT / "README.md"
        text = readme.read_text()
        if START not in text or END not in text:
            sys.exit("README.md has no catalogue markers")
        new = text[:text.index(START) + len(START)] + "\n" + catalogue(manifests) + "\n" + text[text.index(END):]
        if new != text:
            readme.write_text(new)
            print("README.md catalogue updated")
        for template in sorted({m["id"] for m in manifests}):
            path = ROOT / template / "README.md"
            body = template_readme(template)
            if not path.is_file() or path.read_text() != body:
                path.write_text(body)
                print(f"{template}/README.md written")
    print(f"{len(manifests)} template(s) pass, {len(errors)} problem(s)")
    sys.exit(1 if errors else 0)


if __name__ == "__main__":
    main()
