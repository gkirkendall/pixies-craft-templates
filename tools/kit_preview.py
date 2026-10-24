#!/usr/bin/env python3
"""Make the trip video kit's preview reel: the kit project rendered, with a title page, the end page and the demo's music.

  python3 tools/kit_preview.py --effectcraft-cli PATH --music DIR [--out project_templates/trip_video/preview.mp4] [--size 9x16 --out FILE]

Renders "Trip Video 16x9.ecproj" (or 9x16) with effectcraft-cli, then lets tools/demo.py add the title page and end page (as on every reel) and
mix the track named below from --music DIR (it is only ever mixed into this finished reel, never copied; the kit project itself has
no music). Writes the reel and its poster (preview_poster.jpg beside it).
"""
import argparse
import json
import pathlib
import subprocess
import sys
import tempfile

ROOT = pathlib.Path(__file__).resolve().parents[1]
KIT = ROOT / "project_templates" / "trip_video"
TRACK = "Relaxing Flute Tune-(SoundEffectsFactory.com)_.mp3"
TEMPLATES = ["utility/fill_frame", "titles/animated_title", "logos/corner_logo", "lower_thirds/basic", "maps/route_leg",
             "maps/locator", "titles/sign_off"]


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--effectcraft-cli", required=True)
    ap.add_argument("--music", required=True, type=pathlib.Path, help="the folder holding the track")
    ap.add_argument("--track", default=TRACK, help="the track's file name in --music DIR")
    ap.add_argument("--save-silent", type=pathlib.Path, help="also keep a video-only copy here (demo.py --save-silent)")
    ap.add_argument("--out", type=pathlib.Path, default=KIT / "preview.mp4")
    ap.add_argument("--full-size", action="store_true", help="1920x1080 instead of 1280x720 (a YouTube upload copy; needs --out)")
    ap.add_argument("--size", choices=["16x9", "9x16"], default="16x9", help="9x16 renders the vertical project (a YouTube Short; needs --out)")
    a = ap.parse_args()
    if a.full_size and a.out == KIT / "preview.mp4":
        ap.error("--full-size needs --out, so the project's 720p preview is not replaced")
    if a.size == "9x16" and a.out == KIT / "preview.mp4":
        ap.error("--size 9x16 needs --out, so the project's 16:9 preview is not replaced")
    with tempfile.TemporaryDirectory() as tmp:
        full = pathlib.Path(tmp) / "kit.mp4"
        subprocess.run([a.effectcraft_cli, "render", str(KIT / f"Trip Video {a.size}.ecproj"), "--comp", "Trip Video", "--out", str(full),
                        "--format", "h264", "--quality", "best"], check=True)
        spec = pathlib.Path(tmp) / "preview.json"
        reel = {"size": a.size, "music": a.track, "crossfade": 0.5, "poster_at": 2, "end_page": True,
                "credit_photos": "Photos: Pixabay (see CREDITS.md)",
                "segments": [{"clip": str(full), "start": 0, "seconds": 60}]}
        if a.size == "9x16":   # no title page, no thumbnail: the first frame says what it is (owner, 2026-10-24)
            reel["heading"] = "Travel Kit Sample"
        if a.size == "16x9":   # a Short opens straight on the picture, as the other Shorts do
            reel["title_page"] = {"name": "Trip Video", "line": "A ready-made project: swap in your photos and text",
                                  "templates": [f"effectcraft/{t}" for t in TEMPLATES]}
        spec.write_text(json.dumps(reel))
        subprocess.run([sys.executable, str(ROOT / "tools" / "demo.py"), str(spec), "--footage", tmp, "--music", str(a.music), "--out", str(a.out),
                        "--effectcraft-cli", a.effectcraft_cli, "--max-seconds", "75", "--max-mb", "8"] + (["--full-size"] if a.full_size else [])
                       + (["--save-silent", str(a.save_silent)] if a.save_silent else []),
                       check=True)


if __name__ == "__main__":
    main()
