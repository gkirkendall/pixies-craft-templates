#!/usr/bin/env python3
"""Build the files of a GitHub release (PLAN.md, RELEASE1): one download with every template, for people who don't want the source.

  python3 tools/release.py                     write dist/ (gitignored)
  python3 tools/release.py --publish v0.6.5    also create the GitHub release with those files (needs gh, signed in)

dist/ then holds:
  pixies-craft-templates.zip         templates/ (every current .ectemplate, flat), fonts/ (only the fonts the templates list, each
                                     folder with its licence text), README.txt, LICENSE-MIT, LICENSE-APACHE, CREDITS.md
  pixies-craft-templates-fonts.zip   the same fonts/ alone (the web page's "Fonts:" links)
  pixies-trip-video-template.zip     the trip-video project: project_templates/trip_video/ as "Trip Video/" (both .ecproj, Photos,
                                     Logo, Template Media, Music, Make Maps, README.txt), without the preview reel or poster
  <template>_<size>.ectemplate       each template file on its own (the web page's "Download:" links)
The asset names carry no version, so ASSETS + name (…/releases/latest/download/<name>) always fetches the newest release. The zips
are written with fixed dates, so the same files make the same zips. No reels, photos, footage, music or Pixie picture go in.
"""
import argparse
import pathlib
import shutil
import subprocess
import sys
import zipfile

import catalog
import page

ROOT = page.ROOT
DIST = ROOT / "dist"
ZIP, FONTS_ZIP, TRIP_ZIP, ASSETS = page.ZIP, page.FONTS_ZIP, page.TRIP_ZIP, page.ASSETS
TRIP = ROOT / "project_templates" / "trip_video"
TRIP_SKIP = {"preview.mp4", "preview_poster.jpg", ".DS_Store"}   # the preview reel is for the web page; "Make Maps/data" and "maps" are made by the user
STAMP = (2026, 1, 1, 0, 0, 0)


def templates():
    """(asset name, file) for every size of every current template."""
    out = []
    for template in page.templates():
        f = page.current(template)
        out += [(pathlib.Path(v["file"]).name, f.path / v["file"]) for v in f.manifest["variants"]]
    return sorted(out)


def fonts():
    """(path in the zip, file) for every file in the folder of each font a template lists."""
    families = sorted({n for t in page.templates() for n in page.current(t).manifest.get("fonts", [])})
    return [(p.relative_to(ROOT).as_posix(), p) for n in families for p in sorted(page.font_folder(n).iterdir())
            if p.is_file() and p.name != ".DS_Store"]


def readme():
    rows = [(f.manifest, pathlib.Path(v["file"]).name) for f in map(page.current, page.templates()) for v in f.manifest["variants"]]
    tested = sorted({catalog.tested_text(m["id"]) for m, _ in rows})
    lines = [f"{page.NAME}", "", "Free motion templates for EffectCraft. Sponsored By PixBack - Photo and Video Backup to Google Photos",
             "(https://getpixback.com/).", "", "See every template, with its demo reel: https://gkirkendall.github.io/pixies-craft-templates/",
             f"Source: {page.REPO}", "", "HOW TO INSTALL", "",
             "1. Get EffectCraft 0.13 or later: https://getartcraft.com/apps/effectcraft",
             "2. Install the fonts: open the fonts folder and double-click each .ttf file (on Linux, copy them to ~/.local/share/fonts).",
             "   EffectCraft swaps a missing font for its own.",
             "3. In EffectCraft: File > Import > Essential Graphics Template..., pick a file from the templates folder, then change its",
             "   text, colours, fonts and timing in the Essential Graphics panel.", "",
             f"Tested with EffectCraft {', '.join(tested)}.", "", "WHAT IS INSIDE", ""]
    lines += [f"  templates/{n}  {m['name']}" for m, n in rows]
    lines += ["", "LICENCE", "", "The templates are free: MIT or Apache 2.0, at your option (LICENSE-MIT, LICENSE-APACHE). The fonts are",
              "under the SIL Open Font License (the licence text is in each font's folder). Credits: CREDITS.md.", ""]
    return "\n".join(lines)


def write_zip(path, entries):
    """entries: (name in the zip, file path or bytes)."""
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as z:
        for name, src in entries:
            info = zipfile.ZipInfo(name, STAMP)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o644 << 16
            z.writestr(info, src if isinstance(src, bytes) else src.read_bytes())


def zip_entries():
    """What pixies-craft-templates.zip holds, in order."""
    return ([("README.txt", readme().encode())] + [(f"templates/{n}", p) for n, p in templates()] + fonts()
            + [(n, ROOT / n) for n in ("LICENSE-MIT", "LICENSE-APACHE", "CREDITS.md")])


def trip_entries():
    """What pixies-trip-video-template.zip holds: the kit folder as "Trip Video/", sorted, without the preview files or anything
    a person's own run of Make Maps leaves (its data and maps folders) or Python's caches."""
    entries = []
    for p in sorted(TRIP.rglob("*")):
        rel = p.relative_to(TRIP)
        if p.is_file() and p.name not in TRIP_SKIP and rel.parts[:2] not in (("Make Maps", "data"), ("Make Maps", "maps")) \
                and "__pycache__" not in rel.parts:
            entries.append((f"Trip Video/{rel.as_posix()}", p))
    return entries


def build():
    shutil.rmtree(DIST, ignore_errors=True)
    DIST.mkdir()
    write_zip(DIST / ZIP, zip_entries())
    write_zip(DIST / FONTS_ZIP, fonts())
    write_zip(DIST / TRIP_ZIP, trip_entries())
    for n, p in templates():
        shutil.copyfile(p, DIST / n)
    return sorted(DIST.iterdir())


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--publish", metavar="TAG", help="create the GitHub release TAG (already pushed) with the files in dist/")
    a = ap.parse_args()
    files = build()
    print(f"wrote {len(files)} files in {DIST.relative_to(ROOT)}/: {ZIP} ({(DIST / ZIP).stat().st_size / 1e6:.1f} MB), {FONTS_ZIP}, "
          f"{TRIP_ZIP}, {len(files) - 3} templates")
    if a.publish:
        notes = (f"Every template in one download: **{ZIP}** (the templates, their fonts and a README with the install steps). "
                 f"Or one template at a time: each `.ectemplate` below, with **{FONTS_ZIP}** for the fonts. "
                 f"**{TRIP_ZIP}** is the trip video project: open it in EffectCraft, swap in your own photos and text.\n\n"
                 "Install the fonts, then in EffectCraft: **File ▸ Import ▸ Essential Graphics Template…**. "
                 "See every template at work: https://gkirkendall.github.io/pixies-craft-templates/")
        r = subprocess.run(["gh", "release", "create", a.publish, "--repo", page.REPO.removeprefix("https://github.com/"),
                            "--title", f"{page.NAME} {a.publish}", "--notes", notes, *map(str, files)])
        sys.exit(r.returncode)


if __name__ == "__main__":
    main()
