#!/usr/bin/env python3
"""Test the release files tools/release.py builds (PLAN.md, RELEASE1). Free: no app needed.

  python3 tools/tests/test_release.py

Checks: the zip holds every current template file and nothing else in templates/; every font a template lists, each with its
licence text; the README, licences and credits; and nothing outside that list (no reels, photos, music or Pixie picture). The
fonts zip holds the same fonts; each template file is also on its own; building twice gives the same zips.
"""
import hashlib
import pathlib
import sys
import zipfile

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
import page  # noqa: E402
import release  # noqa: E402


def main():
    results = []

    def check(name, ok, detail):
        results.append(ok)
        print(("PASS " if ok else "FAIL ") + name + ": " + detail)

    files = release.build()
    names = zipfile.ZipFile(release.DIST / page.ZIP).namelist()
    want = sorted(f"{pathlib.Path(v['file']).name}" for f in map(page.current, page.templates()) for v in f.manifest["variants"])
    got = sorted(n.removeprefix("templates/") for n in names if n.startswith("templates/"))
    check("every template file in the zip", got == want, f"{len(got)} of {len(want)}")
    families = sorted({n for t in page.templates() for n in page.current(t).manifest.get("fonts", [])})
    folders = [page.font_folder(n).relative_to(ROOT).as_posix() + "/" for n in families]
    unlicensed = [d for d in folders if not any(n.startswith(d) and n.endswith(".ttf") for n in names) or d + "OFL.txt" not in names]
    check("every listed font with its licence", not unlicensed, f"{len(families)} fonts" + (f"; missing: {unlicensed}" if unlicensed else ""))
    top = {"README.txt", "LICENSE-MIT", "LICENSE-APACHE", "CREDITS.md"}
    extra = [n for n in names if n not in top and not n.startswith("templates/") and not any(n.startswith(d) for d in folders)]
    check("nothing else in the zip", top <= set(names) and not extra, f"{len(names)} files" + (f"; extra: {extra}" if extra else ""))
    fz = sorted(zipfile.ZipFile(release.DIST / page.FONTS_ZIP).namelist())
    check("fonts zip holds the same fonts", fz == sorted(n for n in names if n.startswith("fonts/")), f"{len(fz)} files")
    alone = sorted(p.name for p in files if p.suffix == ".ectemplate")
    check("each template file on its own", alone == want, f"{len(alone)} files")
    first = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in files if p.suffix == ".zip"}
    release.build()
    again = {p.name: hashlib.sha256((release.DIST / p.name).read_bytes()).hexdigest() for p in files if p.suffix == ".zip"}
    check("same files make the same zips", first == again, ", ".join(first))
    print(f"\n{sum(results)} of {len(results)} checks pass")
    sys.exit(0 if all(results) else 1)


if __name__ == "__main__":
    main()
