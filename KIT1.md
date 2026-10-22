# KIT1: instructions for building the trip-video kit (written for a Sonnet session)

Approved by Pixie 2026-10-21 (PLAN.md, "RECIPE1"; read that section first: it is the spec). **Do SLIDER1.md first**: the kit
uses the 1.1.0 templates, whose sliders are percents. If something doesn't match this file, stop and tell Pixie what you found
and what you propose; don't guess.

## What it is

An EffectCraft project anyone can download, open in the app, swap in their own photos and text, and render: the trip demo
(`demo/australia_trip/demo.json`, `demo.mp4`) rebuilt with Pixabay photos and generic text. No scripts or command line for the
person using it.

## Rules for this session

The same as SLIDER1.md's "Rules" section (no-reply email, tag and push after each commit, `lsof` before editing docs, ask about
`??` files, `caffeinate -i -s` for long runs, `open` every result, "Pixie" in public text, no footage file names / travel dates /
emails in the repo, every problem with a proposed fix, no agents). Plus:
- **The Pixabay key never enters the repo or any file.** You shouldn't need it: the 8 photos are already downloaded and labelled.
- **Pixie's own photos and the demo's music never go in the kit** (`demo.json`'s footage and music folders are Pixie's private
  files; read nothing from them into the kit).

## What's already done (in the repo)

- `project_templates/trip_video/Photos/Photo_1.jpg` … `Photo_8.jpg`: the Pixabay photos, 1920 wide, labelled "Photo N" in the
  top-left corner (so they aren't distributed in their original form, as Pixabay's licence asks). Photographers and pages: the
  table under "RECIPE1 photos picked" in PLAN.md.
- `tools/kit_label_photos.py`: the script that labelled them (only needed if a photo is ever swapped).
- `tools/project.py`: **the two-shot prototype** Pixie tested in the app (Fill the Frame + Title, then a second photo with a
  0.5 s crossfade + Box Wipe). It works; extend it. Its patterns are the ones to keep: each stage is a separate
  `effectcraft-cli run … --save` call so later stages use ids from earlier ones; `essential.importTemplate` once per template,
  then one layer per use; `essential.set` for values; `layer.timing`; opacity keys for the crossfade; `layer.rename`;
  `project.newFolder` + `project.move`. Fix two things while extending it: the CLI path becomes a required flag
  (`--effectcraft-cli PATH`), and the output folder a flag (`--out DIR`); use argparse (Pixie wants flags, not env vars or
  positional magic).

## The shots (from demo.json; the later shot always sits above the earlier one so the crossfade shows)

Photo segments get the next photo in order, so Photo_1 … Photo_8 are segments 0, 2, 3, 5, 6, 8, 9, 10:

| Seg | Seconds | Picture | Overlays (all also get Corner Logo) | Generic text |
|---|---|---|---|---|
| 0 | 4 | Photo_1 | Animated Title | "Your Trip Title" |
| 1 | 5 | Locator card (live) | – | the locator's own place text: "First Stop" |
| 2 | 9 | Photo_2 | Basic lower third, Route Leg inset | "Place Name" / "Day 1" |
| 3 | 4.5 | Photo_3 | Basic lower third | "Place Name" / "Day 2" |
| 4 | 5 | Route Leg card (live) | – | stop names "Start" / "Next Stop" |
| 5 | 9 | Photo_4 | Basic lower third, Route Leg inset | "Place Name" / "Day 3" |
| 6 | 4.5 | Photo_5 | Basic lower third | "Place Name" / "Day 4" |
| 7 | 5 | Route Leg card (live) | – | "Start" / "Next Stop" |
| 8 | 4.5 | Photo_6 | Basic lower third | "Place Name" / "Day 5" |
| 9 | 9.5 | Photo_7 | Route Leg inset, Basic lower third | "Place Name" / "Day 6" |
| 10 | 5 | Photo_8 | Sign-off | "Thanks for watching" |

Crossfade 0.5 s between shots (`demo.json` `crossfade`). Take each overlay's timing and position from `demo.json` and from
`tools/demo.py`, which renders the demo: the kit must look like the demo shot for shot. Where the demo's values files say a real
place, use the generic text above.

**Maps: live map templates (Pixie chose (b), 2026-10-21).** The map cards (segments 1, 4, 7) and the Route Leg insets use the
map templates in the project, with generic stops ("First Stop", "Start" / "Next Stop"), so people type their own places in
Essential Graphics instead of making map pictures. No `Maps/` folder of pictures. First check, in the app, what can change there:
place names should be typeable in Essential Graphics; the map picture itself is made by `tools/maps.py` from a stops file.
**If a new map needs the script, the kit supplies it (Pixie, 2026-10-21: "so supply the script, if it is needed"):**
- `Make Maps/` in the kit: `maps.py` and whatever of `tools/` it imports (copy only what it needs; it must run from the kit
  folder alone, without this repo), an example `my.stops.json` with generic places, and `README.txt`.
- That README: install Python 3 (python.org; Windows, Mac and Linux), `pip install` the exact packages it needs, run
  `python3 maps.py fetch` once (Natural Earth data, about 52 MB), write your stops in `my.stops.json`, then the two commands
  (route legs, locator) that write the map pictures, and how to pick them in the map layers' Essential Graphics **Media** (or
  whichever control takes the map). Spell out every command in full.
- The kit's main README.txt points to it in one line ("New places on the maps: see Make Maps/README.txt").
- A test: copy the kit to a temporary folder, run `Make Maps/` there on the example stops, and check it writes the map
  pictures and the project shows them.
- Natural Earth is public domain; check `maps.py`'s other dependencies' licences before shipping them (only free licences:
  PLAN.md and SKILL.md list which).

**Logo:** `Logo/Logo.png`, a plain placeholder (text "Your Logo" in Inter on a transparent square, made by script).

**Music:** none. `Music/README.txt`: "Put your music file here and drag it into the timeline."

## Layout of the kit

```
project_templates/trip_video/
  Trip Video 16x9.ecproj      (and Trip Video 9x16.ecproj, same shots; the photos are 16:9, Fill the Frame fills the tall frame)
  Photos/  Logo/  Music/  Make Maps/  Template Media/   (Template Media: the templates' own pictures, copied in, as the prototype does)
  README.txt
```
Folders in the Project panel: "Photos – replace these", "Templates (no need to edit)". Timeline layer
names say what each is ("Shot 3 · Photo_3", "Place Name (Lower Third)").

## README.txt (plain words, for people new to EffectCraft)

1. Open `Trip Video 16x9.ecproj` in EffectCraft.
2. **Your photos:** drag them into the Project panel. Click a shot layer ("Shot 1 · Photo_1"), open Window ▸ Essential Graphics,
   and pick your photo in **Media**. Don't use File ▸ Replace Footage: with camera-numbered photos (IMG_2331.JPG) it can bring
   in the whole numbered run as one image sequence.
3. **Your text:** click a title or lower-third layer and type in Window ▸ Essential Graphics. The title fades in from 0.3 s:
   move the playhead past that to see it.
4. **Music:** see `Music/README.txt`.
5. File ▸ Export to make your video.
Credits line: photos from Pixabay (see CREDITS.md); templates by Pixie, https://gkirkendall.github.io/pixies-craft-templates/

## Steps

1. Extend `tools/project.py` to all 11 shots for 16x9 (then 9x16). Build into `project_templates/trip_video/`. Open the
   project in the 0.14 app for Pixie (`~/projects/storytold/effectcraft/target/release/effectcraft "<path>.ecproj"`) and **wait
   for his OK**.
2. `tools/tests/test_project.py` (PLAN.md RECIPE1 3): opens in the CLI with no missing footage (run `footage.check`: the CLI
   doesn't run it on open), every Photo_N is used, every title holds the generic text, a still at each shot shows that
   shot's template in the demo's place, and the total length equals the demo's. Use the existing `tools/tests/` style.
3. `CREDITS.md`: a "Trip video kit photos (Pixabay)" section: each Photo_N, its Pixabay page and photographer (PLAN.md table).
   Pixabay's licence needs no credit; this records the source.
4. **Preview reel** (RECIPE1 3a): render the kit project itself to `project_templates/trip_video/preview.mp4` (+ a poster
   frame); open it for Pixie. On the web page, beside the trip demo: "Make your own: download the project template"
   (`tools/page.py`), and a line in the README.
5. **Release:** `tools/release.py` gains `pixies-trip-video-template.zip` (the `project_templates/trip_video/` folder, minus
   preview files; fixed dates like the other zips), with a test in `tools/tests/test_release.py`. `python3 tools/catalog.py
   --check` must pass. Publish only after Pixie says go ahead: `python3 tools/release.py --publish <tag>`.
6. PLAN.md: "RECIPE1 done 2026-…" with what shipped. Commit, tag, push.
