# GEOCODE: make map stops from a folder of photos (plan; approved 2026-10-22, built: see PLAN.md)

Pixie, 2026-10-22: "If it had location data, we could try the dynamic map generation." The kit's Pixabay photos carry no GPS
(checked with exiftool and Pillow: no GPS, XMP or IPTC fields), so the kit's maps stay fixed example places. Pixie's own photos
(phone and camera files) usually do. This adds a way to turn them into a stops file, which `maps.py`'s `route-legs` and
`locator` already turn into map pictures. Approved by Pixie on 2026-10-22.

## What changes

1. **A new command in `tools/maps.py`:**
   `python3 tools/maps.py stops-from-photos --photos DIR --out my.stops.json [--names]`
   - Reads each photo's GPS position and the camera's own clock time (EXIF DateTimeOriginal, never converted through the
     computer's time zone) in DIR (not subfolders; `.jpg`, `.jpeg`, `.png`, `.tif`, and `.heic`/`.heif` when ExifRead is installed).
   - Sorts the photos by capture time and writes the stops file `maps.py` already reads: a list of
     `{"name": "Stop 1", "subtitle": "", "lat": …, "lon": …}` in travel order, coordinates at 3 decimals (about 100 m).
   - Photos taken at nearly the same spot (within 1 km) and within a day of each other become one stop, so a day of snaps is not
     forty stops. `--merge-km N` changes the 1 km.
   - A photo with no GPS is listed ("IMG_0001.jpg: no location, skipped") and never silently dropped; a folder with fewer than
     two located photos stops with a message saying what to do (the route needs two stops; the locator needs one).
   - Prints the stops, then the two commands to run next.
2. **No place names are looked up.** The names stay "Stop 1", "Stop 2", …, and the person types the real ones in Essential Graphics
   (the kit's map templates take typed names). So no coordinate leaves the computer, and the kit needs no extra network service
   beyond the map-data download it already has. (MoneyPrinterTurbo's own `tests/s1/geo.py` does the lookups through OpenStreetMap
   Nominatim for MPT's captions; that stays in MPT and is not copied here.)
3. **Code reused, not rewritten:** `dms()`, `exif()` and `exif_heic()` from the author's MoneyPrinterTurbo photo-input code (about 40 lines),
   trimmed to what is needed: latitude, longitude and taken time, with no time-zone offset logic.
4. **Optional HEIC:** needs `pip install exifread` (BSD-3-Clause, pure Python, no dependencies). Without it, a HEIC photo is listed
   as skipped with the install command in the message. JPEG and PNG need only Pillow, which `maps.py` already requires.
5. **The kit's `Make Maps/`** gets the same function in its copy of `maps.py` (KIT1.md), and `README.txt` gets one step:
   "Your own photos' locations": the command above, then the two map commands, then pick the pictures in Essential Graphics.
   It warns that messaging apps and social sites often strip the location, so use the original files, and that the locations stay
   on the computer.

## Privacy rules (from the standing rules)

- No photo with a location ever goes in the repository or the kit: the test makes its own JPEGs with a made-up position (the
  middle of the ocean at 0.000, 0.000 is avoided because it reads as "no data"; the test uses 12.345, 67.890).
- The command prints coordinates only for the person running it, in their own terminal.

## Tests (`tools/tests/test_geocode.py`, free, no app, no network)

Generated JPEGs with EXIF GPS (Pillow writes GPS IFD), checking: located photos come out in capture-time order; two photos within
1 km and a day become one stop and `--merge-km` splits them; a photo without GPS is reported and skipped; south and west references
give negative signs; fewer than two located photos stops with a message; the written file is accepted by `maps.py route-legs`
(reads it, writes a values file); a HEIC without ExifRead installed is listed as skipped with the install command.

## Steps once approved

1. Add the command and its test to `tools/maps.py`; run `tools/tests/test_geocode.py` and the existing map tests.
2. Copy `maps.py` into the kit's `Make Maps/` (KIT1.md) with the README step; the kit test (`tools/tests/test_project.py`) runs the
   kit's copy on a generated photo folder.
3. SKILL.md "Map templates": a line for the new command. PLAN.md entry. Commit, tag, push.

## Decision for Pixie

Approve as written, or change: (a) the 1 km / one-day merge rule, (b) the file types, (c) whether names should ever be looked up
(this plan says no).
