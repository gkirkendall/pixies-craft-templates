#!/usr/bin/env python3
"""Test the catalogue web page index.html (PLAN.md, WEB1, WEB2). Free: no app needed.

  python3 tools/tests/test_page.py

Checks: the page is what tools/page.py writes now; every template has a row with its style sheet and at least one demo reel; every
file the page links to exists; it makes no outside requests (no outside src, poster, script or stylesheet; outside links are
fine); every video loads nothing until played (preload="none") and has a poster; the showreel and the trip demo are at the top;
the PixBack sponsor line sits under the title, linking to getpixback.com, with Pixie beside them;
the how-to-install steps; a download link per template size, to the file the latest release attaches, and the
download-all and fonts zips (PLAN.md, RELEASE1); every font a template lists has its folder in fonts/; the README's
video and page links go to the live site (github.com doesn't play a repository video); .nojekyll is present and the page sits at
the root.
"""
import json
import pathlib
import re
import sys
from html.parser import HTMLParser

ROOT = pathlib.Path(__file__).resolve().parents[2]
SITE = "https://gkirkendall.github.io/pixies-craft-templates/"
sys.path.insert(0, str(ROOT / "tools"))
import page  # noqa: E402
import release  # noqa: E402


class Links(HTMLParser):
    def __init__(self):
        super().__init__()
        self.tags, self.sections, self.current = [], {}, None

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        self.tags.append((tag, a))
        if tag == "section":
            self.current = a.get("id")
            self.sections[self.current] = []
        elif self.current:
            self.sections[self.current].append((tag, a))

    def handle_endtag(self, tag):
        if tag == "section":
            self.current = None


def main():
    results = []

    def check(name, ok, detail):
        results.append(ok)
        print(("PASS " if ok else "FAIL ") + name + ": " + detail)

    html = page.build()
    check("page up to date", page.PAGE.is_file() and page.PAGE.read_text() == html, str(page.PAGE.relative_to(ROOT)))
    p = Links()
    p.feed(html)
    ids = sorted({json.loads(m.read_text())["id"] for m in ROOT.glob("effectcraft/*/*/*/template.json")})
    rows = [i for i in ids if i.split("/")[-1] in p.sections]
    check("a row for every template", rows == ids, f"{len(rows)} of {len(ids)}")
    bare = [i for i in ids if i.split("/")[-1] in p.sections and not (
        any(t == "img" and a["src"].endswith("styles.jpg") for t, a in p.sections[i.split("/")[-1]])
        and any(t == "video" for t, a in p.sections[i.split("/")[-1]]))]
    check("each row has its sheet and a reel", not bare, f"missing in {bare}" if bare else "all")
    local, outside = [], []
    for tag, a in p.tags:
        for attr in ("src", "poster", "href"):
            url = a.get(attr)
            if not url:
                continue
            if url.startswith(("http://", "https://", "//")):
                if attr != "href" or tag == "link":
                    outside.append(f"{tag} {attr}={url}")
            elif not url.startswith("#"):
                local.append(url)
    missing = [u for u in local if not (page.PAGE.parent / u).resolve().is_file()]
    check("every linked file exists", not missing, f"{len(local)} files; missing {missing}" if missing else f"{len(local)} files")
    scripts = [t for t, _ in p.tags if t == "script"]
    check("no outside requests", not outside and not scripts, f"outside: {outside}; scripts: {len(scripts)}")
    videos = [a for t, a in p.tags if t == "video"]
    lazy = all(a.get("preload") == "none" and a.get("poster") for a in videos)
    check("videos load only when played, with a poster", lazy and len(videos) > 2, f"{len(videos)} videos")
    first = [a["src"] for t, a in p.tags if t == "video"][:2]
    check("showreel and trip demo first", first == ["demo/showreel.mp4", "demo/australia_trip/demo.mp4"], str(first))
    top = html[html.index("<h1>"):html.index("<h2>")]
    check("sponsor line under the title", '<h1>Pixie\'s Craft Templates</h1>\n<p class="sponsor"><a href="https://getpixback.com/">'
          'Sponsored By PixBack - Photo and Video Backup to Google Photos</a></p>' in top, top.split("\n")[1])
    check("Pixie beside the title", top.startswith("<h1>") and '<header class="brand">\n<img src="brand/pixie_web.png"' in html
          and html.index('<img src="brand/pixie_web.png"') < html.index("<h1>"), "brand/pixie_web.png in the header")
    steps = html[html.index('<h2 id="install">'):html.index("</ol>")] if '<h2 id="install">' in html else ""
    check("how to install", steps.count("<li>") == 5 and "File ▸ Import ▸ Essential Graphics Template…" in steps,
          f"{steps.count('<li>')} steps")
    want = sorted(f.manifest["id"] + "|" + v["key"] for f in map(page.current, sorted({i for i in ids})) for v in f.manifest["variants"])
    got = sorted(a["href"] for t, a in p.tags if t == "a" and a.get("href", "").endswith(".ectemplate"))
    attached = sorted(page.ASSETS + n for n, _ in release.templates())
    check("a release download link per template size", len(got) == len(want) and got == attached,
          f"{len(got)} links for {len(want)} template sizes" + ("" if got == attached else f"; not release files: {sorted(set(got) - set(attached))}"))
    zips = [a["href"] for t, a in p.tags if t == "a" and a.get("href", "").endswith(".zip")]
    check("download-all and fonts zips from the release", page.ASSETS + page.ZIP in zips and page.ASSETS + page.FONTS_ZIP in zips
          and '<p class="download"><a href="' + page.ASSETS + page.ZIP + '">Download all templates (zip)</a></p>' in top, f"{len(zips)} zip links")
    fonts = sorted({n for i in ids for n in page.current(i).manifest.get("fonts", [])})
    gone = [n for n in fonts if not page.font_folder(n).is_dir()]
    check("every listed font has its folder", not gone, f"{len(fonts)} fonts" + (f"; no folder: {gone}" if gone else ""))
    # github.com shows a repository video or page as a file instead of playing or rendering it, so the README links to the live site
    readme = re.findall(r"\]\(([^)]+)\)", (ROOT / "README.md").read_text())
    stuck = [u for u in readme if u.endswith((".mp4", ".html")) and not u.startswith(SITE)]
    check("README videos and page link to the live site", not stuck and any(u.endswith(".mp4") for u in readme),
          f"links that won't play on github.com: {stuck}" if stuck else f"{sum(u.startswith(SITE) for u in readme)} links")
    up = [u for u in local if u.startswith("../")]
    check("served from the root", page.PAGE == ROOT / "index.html" and (ROOT / ".nojekyll").is_file() and not up,
          f".nojekyll {'present' if (ROOT / '.nojekyll').is_file() else 'missing'}; links leaving the root: {up}")
    print(f"\n{sum(results)} of {len(results)} checks pass")
    sys.exit(0 if all(results) else 1)


if __name__ == "__main__":
    main()
