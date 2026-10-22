#!/usr/bin/env python3
"""Test templates with one app version and record the result (PLAN.md, VER1).

  python3 tools/verify.py --all --effectcraft-cli PATH
  python3 tools/verify.py effectcraft/utility/fill_frame [...] --effectcraft-cli PATH
  python3 tools/verify.py --all --effectcraft-cli PATH --list    show which folders would run, and why; run nothing
  python3 tools/verify.py --all --effectcraft-cli PATH --footage DIR --music DIR   also remake and compare the demo reels

For each template, runs each version folder that this version can open: the current (not frozen) folders, and a frozen folder only
when the version is within its tested range (re-checking an older install). Each run is the folder's tests/run.py; its result is
written to the folder's template.json "tested" list (one record per version; a re-run replaces it) and to the history table in
its tests/RESULT.md, and app_min_version becomes the oldest passing version. Then the README catalogue is regenerated. Exits 1 if
any folder fails. Never edit the "tested" records by hand.

The demo half (with --footage, as the footage stays outside the repository): each previews/demo*.json is remade into tests/out/
with tools/demo.py and checked (plays to the end, within size and length, no metadata). It is then compared with the committed
previews/demo*.mp4 at one frame per second: a visible difference writes tests/out/<demo>_compare.png (committed | new | difference)
and reports "review" for a person to look at; it does not fail the folder.
"""
import argparse
import datetime
import json
import pathlib
import re
import shutil
import subprocess
import sys

import versions
from PIL import Image, ImageChops, ImageStat

ROOT = pathlib.Path(__file__).resolve().parents[1]
HISTORY = "## Tested versions"


def templates(args, everything):
    if everything:
        found = {p.parent.parent for p in ROOT.glob("*/*/*/*/template.json") if versions.FOLDER.match(p.parent.name)}
        return sorted(found)
    return [(ROOT / t) if not pathlib.Path(t).is_absolute() else pathlib.Path(t) for t in args]


def plan(template, version):
    """[(folder, run?, reason)] for one template."""
    out = []
    for f in versions.folders(template):
        if not f.opens_in(version):
            out.append((f, False, f"built with {f.built_with}; {version} cannot open it"))
        elif f.frozen and not f.covers(version):
            out.append((f, False, f"frozen (tested with {f.range_text()}); replaced by a newer folder"))
        else:
            out.append((f, True, "frozen, re-checking an older install" if f.frozen else "current"))
    return out


def record(folder, version, ok, checks):
    today = datetime.date.today().isoformat()
    m = folder.manifest
    m["tested"] = sorted([r for r in m["tested"] if r["version"] != version] +
                         [{"version": version, "date": today, "result": "pass" if ok else "fail", "checks": checks}],
                         key=lambda r: versions.parse(r["version"]))
    passed = folder.passed()
    if passed:
        m["app_min_version"] = passed[0]
    (folder.path / "template.json").write_text(json.dumps(m, indent=2, ensure_ascii=False) + "\n")
    result = folder.path / "tests" / "RESULT.md"
    text = result.read_text() if result.is_file() else f"# {m['name']}: test result\n"
    row = f"| {today} | {version} | {'pass' if ok else 'FAIL'} | {checks} |"
    if HISTORY not in text:
        text = text.rstrip("\n") + f"\n\n{HISTORY}\n\nWritten by `tools/verify.py`; newest last.\n\n| Date | EffectCraft | Result | Checks |\n|---|---|---|---|\n"
    result.write_text(text.rstrip("\n") + "\n" + row + "\n")


def demos(folder, a, cli):
    """Remake, check and compare each demo; returns notes ("demo ok", "demo review: …", "demo FAILED: …")."""
    notes, failed = [], False
    out_dir = folder.path / "tests" / "out"
    out_dir.mkdir(parents=True, exist_ok=True)
    for spec in sorted((folder.path / "previews").glob("demo*.json")):
        new = out_dir / spec.with_suffix(".mp4").name
        cmd = [sys.executable, ROOT / "tools" / "demo.py", spec, "--footage", a.footage, "--out", new, "--effectcraft-cli", cli]
        if a.music:
            cmd += ["--music", a.music]
        r = subprocess.run([str(c) for c in cmd], capture_output=True, text=True)
        check = subprocess.run([sys.executable, ROOT / "tools" / "demo.py", "--check", str(new)], capture_output=True, text=True)
        if r.returncode or check.returncode:
            failed = True
            notes.append(f"{spec.stem} FAILED: {(r.stderr or check.stdout).strip()[-300:]}")
            continue
        old = spec.with_suffix(".mp4")
        if not old.is_file():
            notes.append(f"{spec.stem} made (nothing committed to compare)")
            continue
        worst, rows = 0.0, []
        seconds = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(new)],
                                       capture_output=True, text=True).stdout.strip() or 0)
        for s in range(int(seconds)):
            frames = []
            for src, tag in ((old, "old"), (new, "new")):
                png = out_dir / f"{spec.stem}_{tag}_{s:02d}.png"
                subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", str(s + 0.5), "-i", str(src), "-frames:v", "1", str(png)])
                frames.append(Image.open(png).convert("RGB") if png.is_file() else None)
            if None in frames or frames[0].size != frames[1].size:
                worst = 255
                continue
            diff = ImageChops.difference(*frames)
            d = max(ImageStat.Stat(diff).mean)
            worst = max(worst, d)
            rows.append((frames[0], frames[1], diff.point(lambda v: min(255, v * 4))))
        if worst > 3 and not rows:
            notes.append(f"{spec.stem} review: its frames differ in size or number from the committed demo")
        elif worst > 3:
            w, h = rows[0][0].size
            k = 320 / w
            sheet = Image.new("RGB", (int(3 * w * k) + 20, int(len(rows) * h * k) + 10 * len(rows)), "white")
            for i, row in enumerate(rows):
                for j, im in enumerate(row):
                    sheet.paste(im.resize((int(w * k), int(h * k))), (j * (int(w * k) + 10), i * (int(h * k) + 10)))
            sheet.save(out_dir / f"{spec.stem}_compare.png")
            notes.append(f"{spec.stem} review: differs from the committed demo (worst second {worst:.1f} of 255), "
                         f"see tests/out/{spec.stem}_compare.png")
        else:
            notes.append(f"{spec.stem} ok (matches the committed demo, worst second {worst:.1f} of 255)")
    return notes, failed


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("templates", nargs="*", help="template folders, e.g. effectcraft/utility/fill_frame")
    ap.add_argument("--all", action="store_true", help="every template in the repository")
    ap.add_argument("--list", action="store_true", help="show what would run, and why; run nothing")
    ap.add_argument("--effectcraft-cli", required=True, help="path to the effectcraft-cli of the version to test")
    ap.add_argument("--footage", type=pathlib.Path, help="footage folder for the demo reels (tools/demo.py); omit to skip the demos")
    ap.add_argument("--music", type=pathlib.Path, help="music folder for the demo reels")
    a = ap.parse_args()
    if not a.templates and not a.all:
        ap.error("name templates, or give --all")
    cli = shutil.which(a.effectcraft_cli) or a.effectcraft_cli
    version = versions.cli_version(cli)
    print(f"EffectCraft {version} ({cli})\n")
    rows, failed = [], False
    for template in templates(a.templates, a.all):
        rel = template.relative_to(ROOT).as_posix() if template.is_relative_to(ROOT) else str(template)
        for folder, run, reason in plan(template, version):
            if not run or a.list:
                rows.append((rel, folder.name, "run" if run else "skip", reason))
                continue
            print(f"--- {rel}/{folder.name}", flush=True)
            r = subprocess.run([sys.executable, folder.path / "tests" / "run.py", "--effectcraft-cli", cli], capture_output=True, text=True)
            m = re.findall(r"([0-9]+) of ([0-9]+) checks pass", r.stdout)
            checks = f"{m[-1][0]}/{m[-1][1]}" if m else "0/0"
            ok = r.returncode == 0 and bool(m)
            if not ok:
                failed = True
                print(r.stdout[-3000:] + r.stderr[-3000:])
            detail = f"{checks} checks"
            if a.footage:
                notes, demo_failed = demos(folder, a, cli)
                ok, failed = ok and not demo_failed, failed or demo_failed
                detail += "; " + "; ".join(notes) if notes else "; no demo"
            else:
                detail += "; demos not checked (no --footage)"
            record(folder, version, ok, checks)
            rows.append((rel, folder.name, "pass" if ok else "FAIL", detail))
    width = max((len(r[0]) for r in rows), default=8)
    print()
    for rel, name, result, detail in rows:
        print(f"{rel:<{width}}  {name:<18} {result:<5} {detail}")
    if not a.list:
        subprocess.run([sys.executable, ROOT / "tools" / "catalog.py"])
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
