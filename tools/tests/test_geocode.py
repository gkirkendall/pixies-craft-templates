#!/usr/bin/env python3
"""Test `tools/maps.py stops-from-photos` (GEOCODE.md). Free: no app, no network.

  python3 tools/tests/test_geocode.py

Photos are generated here (Pillow) with made-up locations (12.345 N, 67.890 E and nearby); none of the repository's pictures has one.
Checks: located photos come out in the order they were taken (not by file name); two photos within 1 km and a day are one stop and
--merge-km splits them; a photo without a location is reported and skipped; south and west give negative signs; a folder with no
located photo stops with a message and writes nothing; one located photo writes a one-stop file; a HEIC without ExifRead is skipped
with the install command; the file it writes is accepted by `maps.py route-legs`.
"""
import json
import pathlib
import subprocess
import sys
import tempfile

from PIL import Image

ROOT = pathlib.Path(__file__).resolve().parents[2]
MAPS = ROOT / "tools" / "maps.py"


def photo(path, lat=None, lon=None, taken=None):
    """A 64x64 JPEG, with GPS (decimal degrees; the hemisphere goes in the reference letters) and the camera's time if given."""
    exif = Image.Exif()
    if lat is not None:
        def dms(v):
            v = abs(v)
            return (float(int(v)), float(int(v % 1 * 60)), round(v % 1 * 60 % 1 * 60, 3))
        exif[0x8825] = {1: "N" if lat >= 0 else "S", 2: dms(lat), 3: "E" if lon >= 0 else "W", 4: dms(lon)}
    if taken:
        exif[0x8769] = {36867: taken}
    Image.new("RGB", (64, 64), "grey").save(path, exif=exif)


def run(*args):
    r = subprocess.run([sys.executable, str(MAPS), "stops-from-photos", *map(str, args)], capture_output=True, text=True)
    return r.returncode, r.stdout + r.stderr


def main():
    results = []

    def check(name, ok, detail):
        results.append(ok)
        print(("PASS " if ok else "FAIL ") + name + ": " + detail.strip().replace("\n", " | "))

    with tempfile.TemporaryDirectory() as tmp:
        tmp = pathlib.Path(tmp)
        # Taken in the order c, a, b (file names a, b, c sort the other way); a and b are 0.3 km apart
        d = tmp / "trip"
        d.mkdir()
        photo(d / "c.jpg", 12.345, 67.890, "2026:01:02 09:00:00")
        photo(d / "a.jpg", 20.000, 70.000, "2026:01:02 12:00:00")
        photo(d / "b.jpg", 20.002, 70.002, "2026:01:02 12:30:00")
        photo(d / "plain.jpg")
        out = tmp / "my.stops.json"
        code, said = run("--photos", d, "--out", out)
        stops = json.loads(out.read_text()) if out.is_file() else []
        check("in the order taken; two close photos are one stop", code == 0 and [(s["lat"], s["lon"]) for s in stops] == [(12.345, 67.89), (20.0, 70.0)]
              and [s["name"] for s in stops] == ["Stop 1", "Stop 2"], f"{stops}")
        check("a photo without a location is reported and skipped", "plain.jpg: no location, skipped" in said and "3 of 4 photos" in said, said)
        check("it tells you to add the skipped photos' places by hand", "1 photo without a location got no stop" in said, said)
        code, said = run("--photos", d, "--out", out, "--merge-km", "0.01")
        check("--merge-km splits close photos", code == 0 and len(json.loads(out.read_text())) == 3, f"{len(json.loads(out.read_text()))} stops")
        far = tmp / "days"
        far.mkdir()
        photo(far / "x.jpg", 20.0, 70.0, "2026:01:02 12:00:00")
        photo(far / "y.jpg", 20.0, 70.0, "2026:01:05 12:00:00")
        run("--photos", far, "--out", out)
        check("the same place on another day is another stop", len(json.loads(out.read_text())) == 2, f"{len(json.loads(out.read_text()))} stops")
        south = tmp / "south"
        south.mkdir()
        photo(south / "s.jpg", -33.857, -70.5, "2026:01:02 12:00:00")
        run("--photos", south, "--out", out)
        s = json.loads(out.read_text())[0]
        check("south and west are negative", abs(s["lat"] + 33.857) < 0.002 and abs(s["lon"] + 70.5) < 0.002, f"{s}")
        none = tmp / "none"
        none.mkdir()
        photo(none / "n.jpg")
        gone = tmp / "gone.json"
        code, said = run("--photos", none, "--out", gone)
        check("no located photo: stops with a message, writes nothing", code != 0 and not gone.exists() and "none of the 1 photos has a location" in said and "write the places yourself" in said, said)
        code, said = run("--photos", south, "--out", out)
        check("one located photo writes a one-stop file", code == 0 and len(json.loads(out.read_text())) == 1 and "a route needs two stops" in said, said)
        try:
            import exifread  # noqa: F401
            check("HEIC without ExifRead names the install command", True, "ExifRead is installed here, so the message cannot appear (not checked)")
        except ImportError:
            heic = tmp / "heic"
            heic.mkdir()
            (heic / "h.heic").write_bytes(b"not a real heic")
            photo(heic / "j.jpg", 12.0, 67.0, "2026:01:02 12:00:00")
            code, said = run("--photos", heic, "--out", out)
            check("HEIC without ExifRead names the install command", code == 0 and "python3 -m pip install exifread" in said, said)
        if (ROOT / "data" / "naturalearth").is_dir():
            run("--photos", d, "--out", out)
            r = subprocess.run([sys.executable, str(MAPS), "route-legs", "--stops", str(out), "--out", str(tmp / "legs"), "--osm-km", "0"],
                               capture_output=True, text=True)
            check("maps.py route-legs accepts the file", r.returncode == 0 and (tmp / "legs" / "leg01_16x9.values.json").is_file(),
                  r.stdout + r.stderr)
        else:
            check("maps.py route-legs accepts the file", False, "run `python3 tools/maps.py fetch` once first")
    print(f"\n{sum(results)} of {len(results)} checks pass")
    sys.exit(0 if all(results) else 1)


if __name__ == "__main__":
    main()
