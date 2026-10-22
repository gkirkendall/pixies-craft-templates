#!/usr/bin/env python3
"""Make the trip video kit's preview reel: the kit project rendered, with a title page, the end page and the demo's music.

  python3 tools/kit_preview.py --effectcraft-cli PATH --music DIR [--out project_templates/trip_video/preview.mp4]

Renders "Trip Video 16x9.ecproj" with effectcraft-cli, then lets tools/demo.py add the title page and end page (as on every reel) and
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
    ap.add_argument("--out", type=pathlib.Path, default=KIT / "preview.mp4")
    a = ap.parse_args()
    with tempfile.TemporaryDirectory() as tmp:
        full = pathlib.Path(tmp) / "kit.mp4"
        subprocess.run([a.effectcraft_cli, "render", str(KIT / "Trip Video 16x9.ecproj"), "--comp", "Trip Video", "--out", str(full),
                        "--format", "h264", "--quality", "best"], check=True)
        spec = pathlib.Path(tmp) / "preview.json"
        spec.write_text(json.dumps({
            "size": "16x9", "music": TRACK, "crossfade": 0.5, "poster_at": 2, "end_page": True,
            "title_page": {"name": "Trip Video", "line": "A ready-made project: swap in your photos and text",
                           "templates": [f"effectcraft/{t}" for t in TEMPLATES]},
            "credit_photos": "Photos: Pixabay (see CREDITS.md)",
            "segments": [{"clip": str(full), "start": 0, "seconds": 60}]}))
        subprocess.run([sys.executable, str(ROOT / "tools" / "demo.py"), str(spec), "--footage", tmp, "--music", str(a.music), "--out", str(a.out),
                        "--effectcraft-cli", a.effectcraft_cli, "--max-seconds", "75", "--max-mb", "8"], check=True)


if __name__ == "__main__":
    main()
