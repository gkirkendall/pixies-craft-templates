# craft-templates: plan

Free, reusable motion-graphics templates for the Craft apps, starting with EffectCraft. Owner, 2026-10-21: "templates probably
deserve their own project … i will probably publish this as a free resource, so craft-templates should be used".

Nothing here is built until the owner approves this plan ("approved", "go ahead").

## Decisions (owner, 2026-10-21)

- **Name and place:** `craft-templates`, at `~/projects/craft-templates`; a private GitHub repo `gkirkendall/craft-templates` until
  the owner says to publish it. Not "artcraft-…": ArtCraft is Storytold's brand, and a published repo under that name would look
  official. The README calls these "templates for EffectCraft" and uses no ArtCraft logos or brand art.
- **Licence:** MIT OR Apache-2.0, the Craft apps' own dual licence. Anyone may use, change and sell work made with the templates;
  MPT (`~/projects/mpt-local-motion`) stays sellable.
- **Layout by app:** `effectcraft/` now; `figcraft/` (still cards), `vectorcraft/` (charts, logos) and `filmcraft/` later.
- **Templates and their fill scripts** live here, so anyone can make a map card from a list of GPS stops with one command.
- **Only freely redistributable assets** (owner: "I want to keep non-free to distribute assets out of the templates"). Everything in
  the repo (fonts, pictures, video, data inside `.ectemplate` files, previews and posters) must be public domain or under a licence that
  allows redistribution: OFL, CC0, CC BY (credited in CREDITS.md), MIT or Apache. Stock assets bought under a licence (Vecteezy bundles:
  "Re-selling or distributing this file in its original form is strictly prohibited"), personal-use or demo fonts never go in, not even as
  a default or in a preview. Users fill picture slots with their own files at render time. `tools/catalog.py` fails when a font folder
  has no licence file or a template's `assets/SOURCES.md` lists an asset without one of the allowed licences.
- **MPT finds this repo by a `--templates <folder>` flag** (default `~/projects/craft-templates`) and records this repo's git tag in
  each video's provenance. No environment variables, no submodule.

## Layout (APPROVED 2026-10-21 with MAP1)

Owner, 2026-10-21: "a structure that will be reusable and will work on a variety of template types … not all templates will use all
folders". One shape for every template, whichever Craft app opens it and whatever it is (motion title, map, still card, chart, logo,
transition). Only `template.json` and `README.md` are required; every folder is optional.

### Repo root

```
craft-templates/
  README.md                  the catalogue: every template with its poster, app, type and sizes (generated from the manifests)
  CREDITS.md                 every third-party font, data set and asset, with source and licence
  LICENSE-MIT, LICENSE-APACHE
  schema/template.schema.json   the JSON Schema every template.json must pass
  tools/                     shared scripts (Python 3, cross-platform)
    catalog.py               checks every template.json against the schema and regenerates the root README
    render.py                fills and renders any template from its manifest and a values file
    maps.py                  map pictures for the map templates (used by their fill step)
  fonts/<family>/            open fonts the templates use, each with its licence file
  data/                      downloaded caches (Natural Earth, OSM); gitignored, fetched by the tool that needs them
  <app>/<category>/<template>/   one folder per template (below)
```

`<app>` is the Craft app that opens the template (`effectcraft`, `figcraft`, `vectorcraft`, `filmcraft`); `<category>` groups templates
by purpose (`maps`, `titles`, `lower_thirds`, `cards`, `charts`, `logos`, `transitions`, …). Folder and file names are lowercase with
underscores; control names are Title Case ("From Name"), as people see them in the app.

### One template

```
<app>/<category>/<template>/
  template.json      REQUIRED  the manifest (below)
  README.md          REQUIRED  what it does, the preview, a controls table, the render command, credits it needs
  templates/         the files the app opens: <template>_<variant>.<ext>  (route_leg_16x9.ectemplate, route_leg_inset_9x16.ectemplate)
  build/             scripts that make templates/ from scratch (build.py), so every file in templates/ can be rebuilt and reviewed
  fill/              a fill step only this template needs (anything shared lives in tools/)
  assets/            media built into the template (textures, shapes, sample pictures), listed in assets/SOURCES.md with licences
  examples/          filled examples: <name>.values.json, plus any inputs they need (a stops list, a CSV for a chart, a picture)
  previews/          poster_<variant>.png and preview_<variant>.mp4 (motion) rendered from an example; small, shown in the READMEs
  tests/             the test script and RESULT.md; its renders are gitignored
```

What a few kinds would use:

| Kind | Uses |
|---|---|
| Map card (EffectCraft) | all but `assets/` (the map picture comes from the fill step) |
| Lower third (EffectCraft) | `templates/`, `build/`, `examples/`, `previews/`, `tests/` |
| Still card (FigCraft) | `templates/`, `build/`, `examples/`, `previews/` (poster only) |
| Chart (VectorCraft) | `templates/`, `build/`, `examples/` (CSV data), `previews/`, maybe `fill/` |
| Logo sting (EffectCraft) | `templates/`, `build/`, `assets/` (sample logo), `previews/` |

### template.json

Checked against `schema/template.schema.json` by `tools/catalog.py`. Example for the route leg:

```json
{
  "id": "effectcraft/maps/route_leg",
  "name": "Route leg",
  "version": "1.0.0",
  "app": "effectcraft",
  "app_min_version": "0.13.0",
  "kind": "motion",
  "category": "maps",
  "description": "A route line draws itself from one stop to the next on a map, with pins and names.",
  "duration_seconds": 3.5,
  "fps": 24,
  "variants": [
    {"key": "16x9", "size": [1920, 1080], "file": "templates/route_leg_16x9.ectemplate", "output": "h264"},
    {"key": "inset_16x9", "size": [1920, 1080], "file": "templates/route_leg_inset_16x9.ectemplate", "output": "prores4444"}
  ],
  "controls": [
    {"name": "Map", "type": "media", "description": "The map picture"},
    {"name": "From Position", "type": "point", "default": [480, 540]},
    {"name": "From Name", "type": "text", "default": "Point Ritchie"},
    {"name": "Line Colour", "type": "color", "default": "#d9482b"},
    {"name": "Map Credit", "type": "text", "default": ""}
  ],
  "fonts": ["Inter"],
  "fill": "tools/maps.py route-leg",
  "credits": ["\"© OpenStreetMap\" on the map and in the video's credits when the map uses OSM data"],
  "tags": ["travel", "map", "route"]
}
```

- `kind`: `motion`, `still`, `chart`, `logo`, `transition`, … (a still has no `duration_seconds` or `fps`).
- Control `type`: `text`, `number`, `color`, `point`, `checkbox`, `media`, `data` (a table for charts).
- `variants` cover size and mode in one list, so a template can add 1:1 or 4:5 later without a new folder.
- **Versioning:** each template has its own `version`. Renaming or removing a control is a major version (it breaks fill scripts);
  a new control or a look change is minor; a fix is a patch. The repo tag marks a release of the whole set. MPT records both the repo
  tag and the template version in each video's provenance.

## MAP1: map templates (route leg and locator). APPROVED 2026-10-21 (owner: "yes", with the layout above)

Moved here from MPT's PLAN.md (owner, 2026-10-21). The owner's earlier answers: route leg + locator; a clean drawn map; full-screen card
or corner inset, chosen per video; tidy controls, since the owner will open and tweak the templates in the EffectCraft app; OSM detail on
short legs with its credit.

*The two templates* (each made by script, in 16:9 1920×1080 and 9:16 1080×1920, 24 fps, so four `.ectemplate` files):
- **Route leg** (3.5 s): the map fades in with a slow push-in; a pin and name at the start; the route line draws itself to the next stop
  (trim paths, Easy Ease, a gentle arc set by a Curve control, 0 = straight); the second pin drops with a small overshoot and its name
  slides up; hold. Controls, grouped in the Essential Graphics panel: **Map** (Media Replacement: the map picture), **From Position** and
  **To Position** (points on the map, in pixels), **From Name**, **To Name**, **Line Colour**, **Pin Colour**, **Curve**, **Corner Inset**,
  **Map Credit**.
- **Locator** (3.5 s): the whole country, then a zoom to the place, a pin drop, and the name with a subtitle (e.g. "Victoria, Australia").
  Controls: **Map**, **Place Position**, **Zoom**, **Place Name**, **Subtitle**, **Pin Colour**, **Corner Inset**, **Map Credit**.
- **Card or inset:** Corner Inset off = a full-screen card (H.264); on = a framed map at about a third of the width in the lower corner,
  everything outside it transparent (ProRes 4444 with alpha), to lay over the start of a clip.
- **Picture slots** (owner, 2026-10-21: "yes, keep it generic"): **Texture** on both templates (a picture laid over the drawn land and
  sea, empty by default) and **Badge** on the locator (a picture beside the place name: a flag, park emblem, stamp or logo; empty and
  hidden by default). Users fill them with their own files at render time; nothing non-free ships (see Decisions).
- **Font** (owner, 2026-10-21: "yes"): every text layer's font is a template control (EffectCraft's `font` control type), Inter by
  default (shipped with EffectCraft). A user can pick any installed font per video in the app or from a values file; a published default
  or preview only ever names Inter or a font in `fonts/`.
- **Map Credit:** small text in the map's bottom-right corner, readable on the card and on the inset, empty by default. `tools/maps.py`
  fills it with "© OpenStreetMap" only when that map uses OSM data.
- The route line is drawn from the two position controls by an expression (`createPath`, supported by EffectCraft's expression engine),
  so one template serves every leg.

*The map pictures* (`tools/maps.py`; Python 3 with Pillow, no other library):
- **Input:** a plain stops file, `[{"name", "subtitle", "lat", "lon"}, …]` in travel order. MPT converts its S1 `stops.json` into it.
- **Command:** `python3 tools/maps.py --stops stops.json --out DIR --aspect 16x9|9x16 --mode card|inset --effectcraft-cli PATH`. It
  draws each map, writes each template's `values.json` (pixel positions, names, credit), and renders with `effectcraft-cli render
  --template … --values … --out …`.
- **Natural Earth 1:10m GeoJSON**, public domain, commercial use allowed, no credit required
  ([terms](https://www.naturalearthdata.com/about/terms-of-use/)): land (10.2 MB), state and province borders (21.1 MB), country borders
  (2.3 MB), lakes (5.0 MB), from `github.com/nvkelso/natural-earth-vector/geojson` at a pinned commit with SHA-256s recorded. Fetched once
  by `--fetch` into `data/naturalearth/`; cross-platform, offline afterwards.
- **Not OpenStreetMap's tile servers:** their policy forbids offline use and prefetching, and warns commercial users access "may be
  withdrawn at any point" ([tile policy](https://operations.osmfoundation.org/policies/tiles/)).
- **OSM detail on short legs** (under about 200 km): main roads, towns and national-park outlines from OpenStreetMap data, drawn by
  `maps.py` itself. One Overpass query per leg, with a stable app User-Agent and no email, cached in `data/osm/`. The locator and long
  legs stay Natural Earth only, with no credit. OSM's terms: a credit worded "© OpenStreetMap", in a corner of the map where OSM is a
  major part of it, plus the end credits or the video's description with the link `openstreetmap.org/copyright`, on screen long enough to
  read ([attribution guidelines](https://osmfoundation.org/wiki/Licence/Attribution_Guidelines)). A rendered map is a Produced Work
  ([guideline](https://osmfoundation.org/wiki/Licence/Community_Guidelines/Produced_Work_-_Guideline)); under ODbL §4.6
  ([licence](https://opendatacommons.org/licenses/odbl/1-0/)) a Produced Work from a changed (Derivative) Database must come with an offer
  of that data or the changes, so the Overpass query used is written beside each map. The README tells users both duties. ODbL §4.6 is
  read in full again before the repo is published.
- Each leg's map frames both stops (padded, at least about 150 km across, because the 1:10m coastline turns blocky closer in); the
  locator shows the stop's whole country, drawn at 3× the frame so the zoom stays sharp. Land, sea, lakes, coast, dashed state borders
  (plus OSM roads, towns and parks on short legs); no text drawn into the picture (names come from the templates' text layers).
- Legs shorter than about 25 km (two stops in the same park) get no route card; that threshold to be judged by eye.
- Starting colours (land warm off-white, sea soft blue, borders grey, route and pins a warm red), judged by eye, then exposed as
  `maps.py` options.

*Font:* Inter, the copy EffectCraft itself ships on every platform (Regular, Medium, SemiBold, Bold, Italic; OFL-1.1, listed in
EffectCraft's `ATTRIBUTION.md`). Found in step 1, so nothing is bundled here and no `EFFECTCRAFT_FONT_DIRS` variable is set; anyone who
opens the templates in EffectCraft already has the font. `fonts/<family>/` stays in the layout for a future template whose font
EffectCraft lacks.

*Steps:*
1. Check three things in EffectCraft first, each with a fallback: a point property can be an Essential Graphics control (else X and Y
   number controls); a checkbox can be one (else separate `…_inset` templates); the Inter variable font shapes correctly (else Inter's
   static files from `github.com/rsms/inter` releases, same licence). Also read the public Overpass instance's usage policy and cite it
   here before the first query.
   **Step 1 result (2026-10-21): all pass.** A throwaway template (comp, picture, a null with Point Control and Checkbox Control, a pin
   whose position and opacity follow them by expression) exported with three controls (Map as Media Replacement, From Position as a
   point, Corner Inset as a checkbox); `render-frame --template … --values …` swapped the picture, moved the pin and hid it, 22 ms a
   frame. Control types EffectCraft accepts: font, scale, text, color, slider, checkbox, point, angle, dropdown
   (`crates/engine/src/commands/essential.rs`). Inter Bold rendered correctly, curly apostrophe and middle dot included.
   **Overpass usage policy** ([OSM wiki, Overpass API](https://wiki.openstreetmap.org/wiki/Overpass_API)), main instance
   `overpass-api.de`: under 10,000 queries and 1 GB a day, divided by 100 for anything that runs regularly; an app counts all its
   users together and must send a User-Agent that identifies it; no parallel scripts; cache and rate-limit; pause 30 s after a 429 or
   406; "Commercial use should use self-hosted or paid Overpass servers"; currently overloaded, "do not expect high reliability".
   So `maps.py` sends one query at a time, caches every answer in `data/osm/`, waits 30 s after a 429 or 406, identifies itself as
   `craft-templates-maps/<version> (+https://github.com/gkirkendall/craft-templates)`, and takes `--overpass-url` so a paid or
   self-hosted server can be used. The test (four short legs at most) and personal use are well inside the limits. **For MPT when sold:**
   commercial use needs a paid or self-hosted Overpass server, or a region extract (Geofabrik, ODbL) read locally; decided at MPT's
   integration step, not here.
2. Set up the repo to the layout above: root README, CREDITS.md, both licence files, `schema/template.schema.json`,
   `tools/catalog.py`, `tools/render.py`, `.gitignore` (`.DS_Store`, `data/`, `**/tests/**` renders); tag `v0.1.0`.
3. Fetch the data; build the map templates with each one's `build/build.py` (as MPT's `tests/e1/build.sh`, in Python), with
   `template.json`, README, examples and previews; `tools/catalog.py` must pass.
4. Write `tools/maps.py` and render the test.
5. Move T-E1's lower third here as `effectcraft/lower_thirds/basic/` in the same layout (its build script in Python, switched to Inter); MPT's `tests/e1/RESULT.md` gets a
   line pointing to it.

*Test* (each template's `tests/`, free, no GPU, opened for the owner), from the S1 trip in MPT (`tests/s1/1/stops.json`):
- Locator: Port Campbell National Park (16:9 card).
- Route legs: Point Ritchie → Mushroom Rock (1,797 km, VIC → NT; 16:9 card and 9:16 card), Sydney Cove → Hilda's Lookout (86 km; 16:9
  card, with OSM detail and the credit), and Port Campbell → Point Ritchie (43 km) to try the short-leg rule.
- One inset: the Mushroom Rock leg in a corner over the start of an existing lab clip (ffmpeg overlay for the test).
- **Pass:** pins sit on the right places (checked against the GPS by re-projecting the pixel positions, within 1 % of the frame); the line
  starts and ends on the pins; names exactly as supplied; "© OpenStreetMap" appears on exactly the maps that use OSM data and nowhere
  else; the inset is transparent outside its frame; and each template opens in the EffectCraft app with its named controls (owner checks
  by eye).

*Later, separate approval:* MPT's side (the `--templates` flag, placing cards and insets in its assembly and OTIO timeline by preset, and
the OSM line in end credits or description); publishing the repo. **Before publishing:** squash the history to one commit
(early commits carry an example subtitle with a travel date, removed in `v0.4.1`), then grep the whole tree once more for dates,
emails and licence numbers.

## SKILL1: a SKILL.md for agents. APPROVED 2026-10-21 (owner: "yes, at root level")

The owner asked whether a SKILL.md would be useful. Recommendation: yes, one `SKILL.md` at the repo root (Claude Code's skill format:
`name`/`description` front matter, then instructions), so it ships with the public repo. Users install it by linking it into
`~/.claude/skills/craft-templates/`; MPT's agent can read the same file. Written after MAP1 step 4 passes, so it describes working
templates.

- **Using a template:** find one in the README catalogue; read its README for the controls; copy `examples/*.values.json`; run
  `tools/render.py <template> --variant K --values V --out F` (or `--frame S` for a still to check first); open the result; add the
  credit the README names (for example "© OpenStreetMap" plus the copyright link) to the video and its description. For the map
  templates: draw the map pictures with `tools/maps.py` first (Overpass usage policy: one query at a time, cached; `--overpass-url`
  for heavy or commercial use).
- **Authoring a template:** the folder layout and `template.json` rules above; build by script (`build/build.py`), never by hand
  only; only freely redistributable assets with a `assets/SOURCES.md` row; `python3 tools/catalog.py --check` must pass before a
  commit.
- **EffectCraft command-line lessons** (each found while building MAP1): `createPath` takes plain `[x, y]` arrays, not property
  values (they come out as [0, 0]); set an expression on a path property with `prop.setExpression`, since `set` with a dummy
  value is ignored; several controls of one kind are told apart with `prop.renameGroup`, then read as
  `effect("From Position")("Point")`; one Font control drives other text layers by
  `text.sourceText.style.setFont(...)` expressions; text layers centre on their position unless `"justify":"left"`; a ProRes
  render has alpha only with `--prores 4444 --channels rgba`; an exported `.ectemplate` is a zip that carries its media.
- **Test:** a fresh Claude Code session given only the skill renders the route-leg example and a locator for a new stop without
  further help; the result is opened for the owner.

## TPL2: templates from a published travel video. APPROVED 2026-10-21 (owner: "approved new templates")

**Status 2026-10-21:** built, tested and verified on EffectCraft 0.13.0, each with its demo: Fill the Frame (11/11), Glint
(13/13), Glint Set (28/28), Corner Logo (19/19), Credits (29/29), Sign-off (30/30), and the Box Wipe Lower Third (17/17;
Caveat Brush by default, Title Font and Subtitle Font take any font, as the owner asked; its demo is in the showreel, now 71 s).
The optional `tools/captions.py` was left out: one values file per stop, copied from `examples/stops.values.json`, does the job.

The owner shared one of their published travel videos (made in Premiere Pro with bought Motion Graphics templates) for more
template ideas. **Owner's rule: copy the style and ideas, not the content.** Each template below is an original build by
`build/build.py` (our own shapes, timing and free fonts); nothing is taken from the bought templates' files, and the owner's video,
logo and footage never enter this repo. All are EffectCraft motion templates in 16x9 and 9x16, rendering as ProRes 4444 with alpha,
in the layout above, with `tests/` that are free (no GPU) and opened for the owner.

1. **Box Wipe Lower Third** (`effectcraft/lower_thirds/box_wipe/`). Its own template: a general lower third (a place, a fact,
   a name), not tied to maps. The video's signature element, on almost every shot.
   - In: a thin line sweeps in along the top edge; a see-through colour box wipes open from the left; the text appears in a script
     font with an underline. Out, at the end: the box wipes shut, then the line slides away. About 0.7 s in, 0.7 s out.
   - Controls: Title; Subtitle (optional smaller second line; the box shrinks to one line when empty); Box Colour and Box Opacity;
     Line Colour; Text Colour; Font; Position (a point: the lower third's left edge and baseline); Duration (seconds: the exit plays
     just before it; `render.py` renders up to it).
   - The box sizes itself to the longer line (`sourceRectAtTime`, as the T-E1 lower third). A long title wraps to two lines at a
     Max Width control.
   - Optional fill from a stops file (name, subtitle), the same list the maps use: `tools/captions.py` writes one values file per
     stop. Any other text is filled by hand or by its own values file.
   - **Font:** one test frame in Caveat Brush, Pacifico and one more free script font from `fonts/`; the owner picks the default.
   - Test: the example stops (one line, two lines, a long wrapped title), Position near each corner, 16x9 and 9x16; pass: text
     exactly as supplied, box always contains the text, transparent outside it, the exit finishes by Duration.
2. **End card: three separate templates** (owner, 2026-10-21: "each element should be a separate template"; three, stacked
   on the timeline over the last clip). Each fades and rises in; transparent elsewhere.
   - **Corner Logo** (`effectcraft/logos/corner_logo/`): a Logo picture slot fitted inside a square box (like the Locator's
     Badge) in a chosen corner (Corner: a dropdown of the four, or a Position point), with Size, Opacity and a fade in and out.
     Also the logo the owner puts in a corner of commercial videos.
   - **Credits** (`effectcraft/titles/credits/`): a title in quotes in tall condensed capitals (League Gothic) and two to four
     credit lines under it (empty lines close up), centred; Font controls for the title and the lines.
   - **Sign-off** (`effectcraft/titles/sign_off/`): one line ("Thank you for watching", Montserrat) between two heart shapes in
     a Heart Colour; the hearts follow the text's width.
   - Test (each): with and without the optional parts (no logo, three and four credit lines, a long title, a long sign-off);
     pass: no overlaps, text exactly as supplied, transparent outside the graphic.
3. **Fill the frame** (`effectcraft/utility/fill_frame/`). **Done 2026-10-21: 9 of 9 checks pass (`tests/RESULT.md`).**
   - **FF2, loop clips (owner, 2026-10-21: "loop for longer videos"). APPROVED and DONE (see the finding below).** When Media is a clip
     shorter than Duration, it plays again from the start until Duration ends, instead of stopping. How: `build.py` turns on
     Time Remapping for the Media layer (`layer.enableTimeRemap`) with the expression
     `var d = source.duration; d > 0 ? time % d : 0`, and keeps the layer's out point at the comp's end, so a swapped-in clip of
     any length repeats; a still picture is unaffected. The blurred copy follows by itself (the adjustment layer works on what is
     below it). Sound: the clip's audio loops with it if EffectCraft remaps audio too; the test reports which.
     README: replace "A clip shorter than this ends early" (written without a test) with the loop behaviour.
     Test (added to `tests/run.py`): a 2 s clip with Duration 5 renders 5.0 s, and its frame at 2.5 s matches the clip's frame
     at 0.5 s (mean difference under 8 of 255), and at 4.5 s matches 0.5 s again; the 9 existing checks still pass.
     Commit, tag and push; open the looped clip for the owner.
   - **FF2 finding (2026-10-21); Clip Length fix APPROVED (owner: "clip loop fix 1 approved") and DONE: 10 of 10 checks.** FF2 is approved and built as above, and the clip does repeat,
     but `source.duration` is one frame too long for ordinary H.264 clips: EffectCraft 0.13 reads the MP4's track header
     (`mdhd`: 2.042 s for a 48-frame, 2.000 s test clip) and ignores the edit list that trims the encoder's B-frame delay (ffprobe
     honours it: 2.000 s). So each loop holds the last frame for one extra frame (test: clip frame 11 at 2.5 s instead of 12;
     a hard-coded 2 s loop gives 12). Proposed fix: a number control **Clip Length** (seconds; 0 = use the file's own
     length). `tools/render.py` fills it from `ffprobe` for any template with a Clip Length control when the Media value is a
     video and the values file leaves it out, so command-line renders loop exactly; someone filling the template by hand in
     EffectCraft gets the one-frame hold unless they type the length. The Media layer's remap becomes
     `var d = Clip Length > 0 ? Clip Length : source.duration; d > 0 ? time % d : 0`. Test unchanged (clip frames 12, 36, 12, 12
     at 0.5, 1.5, 2.5, 4.5 s, ±1). Alternative: accept the one-frame hold and say so in the README. Also worth reporting to
     EffectCraft: footage duration should honour the MP4 edit list.
   - A Media slot (picture or clip, any shape). The whole picture is shown fitted inside the frame; behind it, a copy scaled to
     cover the frame, with Gaussian Blur and a Darken control, instead of black bars. Nothing of the picture is cut off.
   - Controls: Media, Blur, Darken, Duration. Output H.264 (it fills the frame).
   - Test: a 4:3 picture and a portrait picture into 16x9, and a 16:9 picture into 9x16; pass: the whole picture is visible
     (its edges match the source), no black bars.
4. **Glints: two separate templates** (owner, 2026-10-21: a single-element glint, and a "pre-filled" one like the video).
   Both are transparent overlays, separate from any title card, over a title picture or any shot.
   - **Glint** (`effectcraft/overlays/glint/`): one four-point star (a star shape) that pops in, turns a little and fades.
     Controls: Position, Start, Size, Colour, Glow (a soft blur copy). Meant to be used many times in one video: each
     instance is placed separately with its own Position, Start and Size (owner, 2026-10-21), as separate layers or clips.
   - **Glint Set** (`effectcraft/overlays/glint_set/`): several glints already placed and timed in a pleasing order, as in the
     video's title, ready to drop over a title picture; controls: Size, Colour, Glow, and a Spread (scales the placement about the
     centre) so the set fits the title.
   - Test: Glint at a set point and time, and Glint Set at default; pass: each glint appears at its point within 1 % of the frame
     and at its start time within one frame; transparent elsewhere.

Order: after MAP1 step 5 (the plain lower third moves as approved; the Box Wipe Lower Third joins it in `effectcraft/lower_thirds/`),
and after SKILL1, whose "authoring" section these builds then follow.

## DEMO1: demo reels, as the commercial vendors do. APPROVED 2026-10-21 (music: owner picks the tracks)

Owner, 2026-10-21: use the Australia map video as an example of how to use the templates, kept in this project as a "demo
reel"; "We should have a demo reel for each feature, that is how the commercial vendors do it."

**Decisions (owner, 2026-10-21):**
- **Footage:** the owner's own, from their original trip photos and videos (not the H3 clips). It is the owner's, shown only to
  demonstrate the templates: `CREDITS.md` and each `previews/README.md` say the demo videos are © Gregory Kirkendall, all rights
  reserved, and not under the templates' MIT/Apache licence. The footage itself stays outside the repo; only the finished demo
  videos are committed.
- **Storage:** a small MP4 per template, `previews/demo.mp4` (1280×720 H.264, under 15 s, about 2–5 MB) plus
  `previews/poster.jpg`; 9:16 templates also get `previews/demo_9x16.mp4` (720×1280).
- **Showreel:** yes, one at the root, `demo/showreel.mp4` (30–60 s, 720p, under about 15 MB), rebuilt by script from the
  per-template demos, linked at the top of the README with its poster.

**Privacy (standing rule):** no travel dates anywhere. Every demo is encoded with metadata stripped (`-map_metadata -1`, no
creation time, no GPS); no shot shows a date on screen; footage file names are not kept in the repo.

**How they are made:** `tools/demo.py`, from a `previews/demo.json` in each template folder: a list of segments (a footage file
named relative to `--footage DIR`, its in and out points, and the template values laid over it, or a full-frame card on its
own). It renders the templates through `tools/render.py`, lays them over the footage with ffmpeg, adds short crossfades and
encodes the result. Photos are shown whole, never cropped: a photo that is not the frame's shape goes through the Fill the frame
template (blurred copy behind it), and photos are held still or eased in with the whole picture visible. **Music** (owner, 2026-10-21: from Sound Effects Factory, soundeffectsfactory.com, already used under its Free License for
the PixBack films; record and saved licence page in `pixback_launch/video/launch_film/music/` and
`video/dinosaur_ad/sound/LICENSES.md`). The Free License allows "Use in commercial projects (YouTube videos, podcasts, games,
films)" and editing, with no attribution required; it forbids redistributing "the original files" and distributing through "a
separate sound effects directory, library, YouTube channel, or mobile application" (terms §2.2). So the music is only ever mixed
into the finished demo videos: the audio files never enter this repo, `tools/demo.py` reads them from `--music DIR`, fades them
in and out under the cut, and `demo/LICENSES.md` names each track, its source page, the licence and the date the licence page
was checked (credit given though not required). Free content carries no warranty (Premium adds legal protection); the owner picks
the tracks.
**Track picked (owner, 2026-10-21):** "Relaxing Flute Tune" by SoundEffectsFactory/kerri,
https://soundeffectsfactory.com/sounds/sound_1758316318737_78tamezjs (Music SFX; MP3, 24.6 s). Licence page
https://soundeffectsfactory.com/license checked 2026-10-21: the Free License terms quoted above are unchanged. The owner's copy is
in `mpt-local-motion/tests/m0/music/`, which `tools/demo.py` reads with `--music`. Demos longer than 24.6 s (the trip demo,
the showreel) loop it with a 2 s crossfade at each join (editing is allowed), fading in at the start and out over the last 2 s.

**The Australia trip demo** (`demo/australia_trip/`, about 45–60 s), the example of templates working together, from the six
example stops in travel order:
1. Locator, full frame: the whole country, zooming to Port Campbell National Park.
2. Footage of Port Campbell with the Basic Lower Third (name and state).
3. Route Leg corner card over that footage: Port Campbell → Point Ritchie (43 km, OpenStreetMap detail and credit).
4. Footage of Point Ritchie with its lower third.
5. Route Leg full frame: Point Ritchie → Mushroom Rock (1,797 km).
6. Footage of Mushroom Rock, then Tjoritja / West MacDonnell, each with its lower third; the Route Leg between them as a corner card.
7. Route Leg full frame: Tjoritja → Sydney Cove (2,087 km); Sydney footage with its lower third.
8. Route Leg corner card: Sydney Cove → Hilda's Lookout (86 km, OpenStreetMap); Blue Mountains footage.
9. End: the Credits template (TPL2) with "Map data © OpenStreetMap contributors" and "Natural Earth"; until it exists, a plain
   title card made by script.

Per-template demos are cut from the same material: Route Leg (one full card, one corner card), Locator (full, then corner card),
Basic Lower Third (two places, 16:9 and 9:16). Each TPL2 template gets its demo when it is built (Box Wipe Lower Third over the
same places, Fill the frame with a portrait photo, Glint and Glint Set over a title picture, Corner Logo, Credits and Sign-off at
the end of the trip demo).

**Footage (owner, 2026-10-21):** the original trip photos the owner downloaded for MPT's clip work, `mpt-local-motion/tests/m0/photos/`:
one photo per stop (Port Campbell, Point Ritchie, Mushroom Rock, Tjoritja / West MacDonnell, Sydney Cove, Hilda's Lookout), all
4:3 landscape, so each goes through the Fill the frame template: **Fill the frame is built before the Australia demo.** The
portrait frame grab in that folder belongs to no stop and is left out. Still photos: the motion comes from the templates and the
crossfades; each photo is shown whole.
**Sydney Cove photo (settled 2026-10-21):** the first Sydney photo was taken during Vivid Sydney, with projected artwork on the
sails, so it stays out of the public demo. The owner supplied a daytime replacement, `IMG_0600.JPG` (Opera House from the water,
4:3, 3264×2448, GPS at the Opera House), with nothing projected. Like every demo input, its metadata is stripped and no date is
shown.

**Test:** each demo plays to the end; size and length within the limits above; `ffprobe` shows no creation time or location;
`tools/catalog.py` checks that every template with `previews/demo.mp4` also has its poster; each demo opened for the owner.

**Order:** the Australia trip demo and the map and lower-third demos first (those templates exist); TPL2 demos as each TPL2
template is built; the showreel last.

**DEMO1 built (2026-10-21) for the four existing templates.**
- **The tool:** `tools/demo.py`, with segment types card, footage, title and clip; music is looped with 2 s crossfades.
- **Footage:** named by place. The owner's footage folder `~/projects/craft-templates-footage/australia/` links each name to its
  trip photo, so no photo file names enter the repo.
- **Demos:**
  - Route Leg 10.5 s;
  - Locator 11 s;
  - Basic Lower Third 8.5 s in 16:9 and 9:16;
  - Fill the Frame 7.5 s in 16:9 and 9:16 (4:3 photos into both shapes: the trip has no portrait photo);
  - Glint 4.5 s, Glint Set 4.5 s, Corner Logo 8.5 s in 16:9 and 4.5 s in 9:16, Credits 6 s, Sign-off 5 s (TPL2, 2026-10-21);
  - the Australia trip demo `demo/australia_trip/demo.mp4`, 58.5 s, 5.2 MB, all nine steps; step 9 is now the real end card
    (Credits, Sign-off and Corner Logo stacked over the Hilda's Lookout photo) in place of the script-drawn title;
  - the showreel `demo/showreel.mp4`, 52 s, 6.3 MB, linked at the top of the README, now with Glint, Glint Set and Corner Logo,
    and ending on the trip demo's end card (Credits and Sign-off).
- **Checks:** every demo passes `tools/demo.py --check` (decodes to the end, within limits, no metadata).
- **verify.py** remakes and compares them when given `--footage` (VER1's demo half).
- **Found on the way:** EffectCraft 0.13 reads numbered phone photos in one folder as an image sequence (colour bars). `render.py`
  now hands each media file over under its control's name, and Fill the Frame's test covers it (11/11).
- **Done 2026-10-21:** the Box Wipe Lower Third's demo (Point Ritchie in Caveat Brush; Tjoritja in Montserrat with other
  colours), added to the showreel.

**END-CREDITS1: sponsor, music artist and project link on the trip demo's end card; blinking hearts. PROPOSED 2026-10-21
(revised the same day). APPROVED (owner: "approved") and DONE 2026-10-21.**
Owner, 2026-10-21: add "sponsored by PixBack", "https://getpixback.com/" and the music's artist, "Kerri", to the end credits;
go to five lines "so they can find the github project"; and the Sign-off hearts "actually beat (blink on and off)", as an option.

1. **Credits: five lines** (`effectcraft/titles/credits/`). `LINES = 5` in `build/build.py` (a Line 5 text control, which
   takes its font from Line 1 like the others; empty lines still close up). The block stays centred on Position; at 16x9 five
   lines plus the title is about 520 px tall, inside the frame. README and `template.json`: "up to five". Test: add a five-line
   case (text read back exactly, no overlaps, transparent outside); the 29 existing checks still pass. Rebuild, bump the
   version, `tools/verify.py`, `tools/catalog.py`.
2. **Sign-off: a Blink option** (`effectcraft/titles/sign_off/`). A checkbox **Blink** (default off, so the template behaves as
   now) and a number **Beats per Minute** (default 70). With Blink on, once the hearts have popped in they switch fully on and
   off together, on for 60 % of each beat; the text is unaffected. Done by the hearts' opacity expression only. Test: with Blink
   on, a heart is drawn at a time in the "on" part of a beat and nothing is drawn there in the "off" part, the text is the same
   in both; Blink off matches today (the 30 existing checks). The Sign-off demo turns Blink on so the option is seen.
3. **The trip demo's end card** (`demo/australia_trip/demo.json`):
   - Line 1: `Photos by Gregory Kirkendall`
   - Line 2: `Music: "Relaxing Flute Tune" by Kerri, Sound Effects Factory`
   - Line 3: `Map data © OpenStreetMap contributors · Natural Earth` (required credit)
   - Line 4: `Sponsored by PixBack · https://getpixback.com/`
   - Line 5: `Made with craft-templates · github.com/gkirkendall/craft-templates`
   - Sign-off: Blink on.
   - Corner Logo throughout (owner, 2026-10-21: "show logo throughout video, fade in, stay steady fade out at the end of end
     card"): on every segment, bottom right; Fade In on the first segment, Steady on every segment between, and Fade Out on
     the end card (which today has Fade In and Out), so it fades out with the end card.
   The repo is private until it is published, so the link works only from then; if the name changes (see "For discussion
   later"), the line changes with it and the demo is remade at publishing anyway.
4. **Corner Logo: fade chosen per photo** (`effectcraft/logos/corner_logo/`). Owner, 2026-10-21: "Fade in and fade out for
   first/last photo, steady for the rest, should be configurable for each photo", and then: "fade out" means start at full
   strength and fade out; "fade in" means fade in and then stay at full strength; a third option fades in and out in the same
   picture. One dropdown, **Fade**, with four items:
   - **Fade In and Out** (default: today's behaviour, for a logo on one picture or the end card);
   - **Fade In**: fades and rises in at Start, then stays at full Opacity to the last frame (the first photo);
   - **Steady**: full Opacity and in place from the first frame to the last (the photos between);
   - **Fade Out**: full Opacity and in place from the first frame, fading out over the last 0.5 s (the last photo).
   Each photo's overlay is rendered with its own values, so the logo holds still across every cut. The 60 s limit stays, since it
   applies per photo. README: a short "a logo across a whole video" section with the values for first, middle and last photos.
   Test: for each item, the logo's strength at frame 0, mid-clip and the last frame is as above; the last frame of a Fade In clip,
   both ends of a Steady clip and the first frame of a Fade Out clip are identical (no jump at a cut); the 19 existing checks
   still pass with the default. Its demo: three photos (Fade In, Steady, Fade Out) with the logo steady across the cuts.
5. **Remake and check:** the Credits, Sign-off and Corner Logo demos, the trip demo and the showreel (which ends on this card; music mixed in
   as before, outside the repo). Check a still of the card: every line readable, long lines shrunk to Max Width, the five-line
   block clear of the Sign-off (if not, move the Credits' Position up in the demo's values). `tools/demo.py --check` on each;
   open all of them. Commit, tag and push.

**Done (2026-10-21):** Credits 1.1.0, five lines (33/33); Sign-off 1.1.0, Blink and Beats per Minute (31/31); Corner Logo
1.1.0, the Fade dropdown (25/25); all three verified on EffectCraft 0.13.0. `tools/demo.py` now lays overlays on map cards too, so
the logo runs across the whole trip demo (fade in on the first card, steady, fade out on the end card). The end card's Credits
moved up to Position [960, 420] to leave a clear gap above the Sign-off. Remade: the Credits, Sign-off and Corner Logo demos (the
last now three photos: Fade In, Steady, Fade Out), the trip demo (58.5 s) and the showreel (54 s; its Corner Logo excerpt now
spans a cut). The preview READMEs credit the music "by Kerri". OCR reads "·" as "-", so the Credits test treats them alike.

**END-CREDITS2: an ArtCraft lower third on the end card. APPROVED (owner: "approved from end credits") and DONE 2026-10-21.**
Owner, 2026-10-21: "the end card should also have a lower thirds 'Made with Artcraft Tools - https://getartcraft.com/'", and
"the end credits will vary by project" (each project fills its own Credits, Sign-off, logo and lower third; the trip demo is one
example, and nothing about its text is built into a template).
- Add the Basic Lower Third to the end card (`demo/australia_trip/demo.json`, last segment), bottom left, from about 1 s:
  Title `Made with ArtCraft Tools`, Subtitle `https://getartcraft.com/` (spelled "ArtCraft", as Storytold writes it).
- Line 5 of the Credits then says the same thing twice; change it to `Templates: github.com/gkirkendall/craft-templates`.
- Check a still: the lower third clear of the Sign-off above it and the logo to its right (if not, raise the Credits and
  Sign-off a little in the demo's values). Remake the trip demo and the showreel; `tools/demo.py --check`; open both. Commit, tag
  and push.

**Done (END-CREDITS2):** the lower third shows from 2 s into the end card; Line 5 reads `Templates: github.com/gkirkendall/
craft-templates`; to keep everything apart, the Sign-off moved up to [960, 740] and the Credits to [960, 395] in the demo's
values. Trip demo and showreel remade (58.5 s, 54 s).

## TITLE1: title templates. APPROVED 2026-10-21 (owner: "approved"; trip demo opening title: "Yes")

**DONE 2026-10-21:** Title (39/39), Animated Title (35/35) and Typewriter (14/14) built, tested and verified on EffectCraft
0.13.0, each with a demo; Credits 1.2.0 takes an empty title (37/37). The trip demo opens with the Animated Title over the Port
Campbell photo (62 s; the logo fades in there), and the showreel shows the three (67 s). Found on the way: a text selector's Based
On and a layer's Anchor Point Grouping ignore expressions (one title layer per By item); a long text's Stagger is now shortened to
fit a third of Duration. Lessons in SKILL.md.

Owner, 2026-10-21: "Normally titles are their own category/template"; examples: four title demo reels in
`~/projects/mpt-local-motion/template-examples/` (bought/commercial demos: studied only, never copied; they stay out of this
repo). **Owner's rule: copy the style and ideas, not the content.** What they show:
- `basic-titles.mov`: plain titles. A small label ("TITLE") over a name, in a corner or bottom centre; a centred title; a scroll.
- `58843029.mp4`: a text animator. Letters, words or lines come in and go out one after another (slide, turn, scale, blur, or
  "decode", random characters settling into the text), with an easing slider: "all in one simple control".
- `60706699.mp4`: a text kit. Typewriter with a cursor; letters closing in from wide spacing ("C I N E M A T I C"); bounce; a
  wave; a glitch slice; word by word; a blur reveal.
- `62540596.mp4`: big kinetic words, one at a time, some in a highlight colour; blur-in; typewriter cursor.

EffectCraft 0.13 has After Effects–style text animators (range, wiggly and expression selectors, based on characters, words
or lines), and the command-line tool adds them (`layer.addTextAnimator`, `layer.addTextSelector`), so all of this can be built.

**First batch (recommended): three templates in `effectcraft/titles/`**, each 16x9 and 9x16, ProRes 4444 with alpha, built by
`build.py`, with free fonts (Inter or Manrope Bold for titles), a free test and a demo, the same way as TPL2:
1. **Title** (`effectcraft/titles/title/`): one title line and an optional small label over it (empty: it closes up). Place: a
   dropdown (Centre, Bottom Centre, Bottom Left, Bottom Right, Top Left, Top Right) plus Margin; fades and rises in, holds, fades
   out, with the same Fade dropdown as Corner Logo (Fade In and Out, Fade In, Steady, Fade Out). Size, Colour, Shadow, Max Width,
   Start, Duration.
2. **Animated Title** (`effectcraft/titles/animated_title/`): the "all in one" title. Controls: Text; **Style** (a dropdown:
   Fade Up, Slide, Scale Pop, Turn, Blur, Spread In (letters close in from wide spacing), Wave, Bounce); **By** (Letters, Words,
   Lines); **Stagger** (how quickly each one follows the last); **Ease**; In and Out (play the animation in, out, or both, by
   the same Fade dropdown); Size, Colour, Highlight Colour (words wrapped in `*stars*` take it), Position, Max Width, Start,
   Duration.
3. **Typewriter** (`effectcraft/titles/typewriter/`): the text types itself letter by letter at a Speed (letters a second) with
   a blinking cursor after it (Cursor: Bar, Underscore or None); optional erase at the end; Size, Colour, Position, Start,
   Duration.

**Also:** Credits gets an optional title (an empty Title shows no quotes and the lines move up to close the gap), so a project
can put its title in the new Title template instead.

**Tests (each):** nothing before Start; at rest the text reads back exactly (OCR) and sits in its place; transparent elsewhere;
plus per template: Title, each Place within 1 % of where it belongs and the label closes up when empty; Animated Title, for each
Style and By, mid-animation the first letters/words are further on than the last ones (measured on the drawn alpha), and Out
plays it back; Typewriter, at a given time OCR reads exactly the letters typed so far, and the cursor is on and off in turn.

**Demos:** one per template over the owner's trip photos, then the showreel. The trip demo opens with an Animated Title
"Australia, coast to centre" over the first photo (owner: "Yes").

**Contact sheets** of the example reels (one frame a second) are committed in mpt-local-motion
`template-examples/contact-sheets/` (v0.0.108); the reels are gitignored (owner, 2026-10-21).

**Later, if wanted:** Decode (random characters settling into the text), Glitch, Kinetic Words (several big words one at a time),
and a Scroll (rolling credits).

## WEB1: a web page of the templates and their demo reels. APPROVED 2026-10-21 (owner: "WEB1 approved")

Owner, 2026-10-21: "I actually want to have a github-based webpage to show the different types of effects with the demo reels";
then, from a screenshot of a vendor's catalogue: each template's contact sheet and demo reel in a grid, separated by template,
the name under each picture or video; no search; one image showing all the styles of a template, and a separate demo reel that
says which feature is on screen. Answers (2026-10-21): a row per template; captions burned into the reels; the owner's example
reels stay off the page; category headings.

1. **Style sheets** (`previews/styles.jpg` per template, made by a new `tools/sheet.py` from a `previews/styles.json` that lists
   each cell: its label, values, size and the moment to show). One image per template, cells in a grid, each labelled underneath
   by script (Inter). Overlay templates are shown over one of the owner's photos, dimmed, so every cell reads alike; full-frame
   templates show their own frame. What each sheet shows:
   - Animated Title: the 8 Styles, each caught mid-move, plus By Words and By Lines; Title: the 6 Places and "no label";
     Typewriter: Bar, Underscore, None, and part-way through Erase.
   - Credits: 3 lines, 5 lines, no title; Sign-off: default, short, long, Blink (on and off); Corner Logo: the 4 corners and a
     tall logo; Basic Lower Third: one line, two lines, 9x16.
   - Glint: 3 sizes; Glint Set: Spread 100 and 60; Locator and Route Leg: full frame and corner card; Fill the Frame: a 4:3
     and a portrait picture in 16x9, a 16:9 picture in 9x16.
   - Each sheet is checked by the catalog (`tools/catalog.py --check` fails if a template has no sheet or it is older than the
     template).
2. **Captions in the reels.** A demo segment gets a `"caption"` (e.g. `Style: Bounce · By: Words`, `Fade: Steady`, `Corner
   Inset`), drawn by `tools/demo.py` as a small label at the bottom left (Inter on a dark translucent pill, clear of the
   templates' own places; moved to the top left where a template sits bottom left). Every template's demo gets captions and is
   remade; the trip demo names the templates in each shot (e.g. `Route Leg · Basic Lower Third`); the showreel's excerpts carry
   them. A demo without captions still works.
3. **The page** (`docs/index.html`, built by `tools/site.py` from each `template.json`, sheet and reel; plain HTML and CSS, no
   outside scripts or fonts, works on a phone):
   - At the top: the showreel and the Australia trip demo ("the templates together"), labelled underneath.
   - Then a heading per category (Maps, Lower Thirds, Titles, Logos, Overlays, Utility). Under it, one row per template: the
     style sheet on the left and the demo reel on the right (stacked on a phone), each with its label underneath
     ("Animated Title: all styles", "Animated Title: demo reel"), then a line with its description, sizes, tested EffectCraft
     versions, and a link to its folder.
   - Videos show their poster and play with controls on click; nothing loads until played.
   - `tools/catalog.py --check` fails if the page is older than any manifest, sheet or reel.
4. **Hosting:** GitHub Pages serving the repository root, so the page at `docs/index.html` uses the committed reels and sheets
   in place (no copies). Until the repo is published the page is opened locally; switching Pages on is part of publishing.
5. **Not on the page:** the owner's example reels and their contact sheets. Credits for the photos, music (Kerri, Sound Effects
   Factory) and maps in a footer.
6. **Test:** every template has a row, a sheet and a reel; every link resolves; no outside requests. Open the page and the
   sheets for the owner. Commit, tag and push.

**Done 2026-10-21 (v0.5.34).** `tools/sheet.py` makes `previews/styles.jpg` for all 13 templates from their `styles.json` (each
JPEG records the template version and a hash of its styles.json; `tools/catalog.py --check` fails on a missing or stale sheet).
Every demo has captions (shown between the crossfades, so two never overlap), and all demos, the trip demo and the showreel were
remade. The page is built by **`tools/page.py`** (not `site.py`: Python already loads its own module of that name at startup);
`tools/catalog.py` rewrites it with the README and `--check` fails when it is stale. `tools/tests/test_page.py`: 7 of 7 (a row,
sheet and reel per template; 49 linked files exist; no outside requests; videos load on play). Two sheets differ from the list
above: Corner Logo shows the 4 corners and 9x16 (no tall logo: the template's own logo is the one shown), and Fill the Frame shows
4:3 and portrait pictures in both sizes (the footage has no 16:9 photo).

## VER1: templates tied to the app versions they were tested on. APPROVED 2026-10-21 (owner: "version plan approved")

**Why (owner, 2026-10-21):** bought templates rarely say which After Effects/Premiere version they work with, or claim one
wrongly; about a third fail because they were made for an older version and never updated. Here every template is tied to the
range of app versions it was *tested* on, each has a test that also makes its demo reel, and older builds stay usable in their
own folder "because sometimes people cannot upgrade". It has to suit people and AI agents alike.

**Decisions (owner, 2026-10-21):** a separate, self-contained folder for an older version, inside each template; on an untested
version `render.py` warns and renders; demo reels are judged by the measured checks, with a side-by-side review sheet for a
person; the tested record lives in each folder's `template.json` (written by the tool) and its `tests/RESULT.md` (history).

**Layout.** Each template folder holds one folder per app-version line, each complete and runnable on its own:

```
effectcraft/utility/fill_frame/
  README.md                what it does; a table: your EffectCraft version → which folder → tested range
  effectcraft-0.13/        built with 0.13.0; frozen once a later release breaks it
    template.json          as now, plus "built_with" and the tool-written "tested" block
    build/ templates/ assets/ examples/ previews/ tests/
  effectcraft-0.15/        made only if 0.15 broke the 0.13 build (copied, fixed, rebuilt, retested)
```

- A new folder is made **only when a release breaks the template**. If the template still passes, its current folder's
  tested range just grows. So most templates keep one folder for a long time.
- A folder is named after the first version it was built with, shortened to `effectcraft-<major>.<minor>` when that version
  was a `.0` release (`effectcraft-0.13`, otherwise e.g. `effectcraft-0.13.5`).
- When a folder is replaced it is **frozen**: `"frozen": true`, no new features, and its range stays closed. It is still
  re-verified on its own last version so it keeps working (see below). The template's own `version` is bumped in the new folder
  (1.x → 2.0.0 when the controls change, otherwise a minor bump).
- Shared tools (`render.py`, `ecbuild.py`, `maps.py`, `catalog.py`, `demo.py`) must keep working for every folder that isn't
  retired; verify (below) proves it by running the frozen folders as well.

**The tested record** (in each folder's `template.json`, schema-checked, written only by `tools/verify.py`):

```json
"built_with": "0.13.0",
"tested": [
  {"version": "0.13.0", "date": "2026-10-21", "result": "pass", "checks": "9/9"}
]
```

The **tested range** shown everywhere is the oldest to the newest passing version. `app_min_version` becomes generated
(= the oldest pass), so nothing claims a version that was not tested. EffectCraft refuses project files from a newer version,
so a folder can never be tested below its `built_with`.

**The test is the demo reel.** Each folder's `tests/run.py` keeps its measured checks and also renders `previews/demo.mp4`
(DEMO1's `tools/demo.py`, silent in tests; music only in the published demo).
- Pass/fail comes from the measured checks.
- The new demo is compared frame by frame (one frame per second) with the committed `previews/demo.mp4`, the last
  passing one. A visible difference makes `tests/out/demo_compare.png` (old | new | difference) and a "review" note in the
  report, not a failure.

**`tools/verify.py`** (new):

```
python3 tools/verify.py [TEMPLATE ...] --effectcraft-cli PATH
```

- **Which folders:** reads the CLI's version (`effectcraft-cli --version`) and runs every folder it can open
  (`built_with` ≤ that version). For a frozen folder, it runs only when the version is within or next to its closed range.
- **What it records:** appends the result to the folder's `tested` list and `tests/RESULT.md` history, then regenerates the
  README catalogue.
- **The report:** prints a table (template, folder, pass/fail/review) and exits non-zero on any failure.
- **On a new EffectCraft release:** run it with `--all`. A failure is fixed by copying the folder to the new version's
  folder, adjusting `build.py`, rebuilding, and verifying.
- **Older EffectCraft versions:** they can be kept installed anywhere, one `--effectcraft-cli` path per version. On the owner's
  Mac that's `~/projects/effectcraft-versions/<version>/`.

**`tools/render.py`** chooses the folder for the installed version, so the command stays
`render.py effectcraft/utility/fill_frame …`:
1. The folder whose tested range includes the installed version.
2. Otherwise the newest folder it can open, with the warning: "Fill the Frame was tested with EffectCraft 0.13.0–0.13.2;
   you have 0.14.0. Run tools/verify.py to test it, or use an EffectCraft version in that range."
3. `--folder effectcraft-0.13` picks a folder by hand.

**For people:**
- The README catalogue gets a "Tested with EffectCraft" column (e.g. "0.13.0–0.14.1; 0.12 in effectcraft-0.12").
- Each template's README has the version → folder table.
- `tests/RESULT.md` keeps the history and links the review sheet when there is one.

**For agents:** SKILL.md gets the rules:
1. Check the installed version against the tested range first (`render.py` prints it).
2. On an untested version, run `tools/verify.py` for that template before relying on it.
3. Never edit the `tested` block by hand.
4. Fix a break in a new folder, never in a frozen one.

**Other Craft apps:** same layout and record, keyed by the manifest's `app` (`figcraft-<version>/` and so on).

**Moving what exists:** Route Leg, Locator, Basic Lower Third and Fill the Frame move into `effectcraft-0.13/` folders
(`git mv`, so history follows). Their scripts' root paths gain one level, and `catalog.py` and the schema learn the new
layout. Then `verify.py --all` on 0.13.0 writes their first `tested` records. The template ids stay the same.

**Test:**
- `verify.py --all` on 0.13.0 passes every template and writes the records.
- `catalog.py --check` passes (it now checks that every folder has `built_with`, a non-empty `tested` list, and a test
  script).
- `render.py`'s folder choice is tested with a small stand-in CLI that reports other versions:
  - 0.13.0 → `effectcraft-0.13`, no warning;
  - 0.14.0 → `effectcraft-0.13` with the warning;
  - 0.12.0 → refused: "no folder of Fill the Frame opens in 0.12.0".
- A frozen-folder rehearsal uses a scratch copy, not committed: a copy marked frozen with a second folder beside it, checking
  that verify and render pick the right one.

**Order:**
1. FF2: the loop fix, once the owner picks option 1 or 2.
2. VER1, before the demo reels, so the previews land in their version folders.
3. DEMO1.
4. The rest of TPL2.

**VER1 built (2026-10-21).**
- **Layout:** the four templates moved into `effectcraft-0.13/` folders (`git mv`).
- **Tools:**
  - `tools/versions.py` holds the shared logic.
  - `tools/verify.py` runs the tests and writes the records.
  - `tools/render.py` chooses the folder (`--folder`, `--which`).
  - `tools/catalog.py` checks the new rules and writes each template's root README.
- **Schema:** `built_with`, `tested`, `frozen`.
- **First verify on 0.13.0:** all pass (Basic Lower Third 12/12, Locator 7/7, Route Leg 18/18, Fill the Frame 10/10).
- **Route Leg's test is now self-contained:** without `--clip` it lays the card over an ffmpeg test pattern.
- **Locator** has its own copy of the stops file.
- **`tools/tests/test_versions.py`:** 9 of 9. It uses a stand-in CLI for 0.12.0, 0.13.0 and 0.14.0, plus the rehearsal with a
  frozen 0.13 folder beside a 0.14 one, for render and for `verify --list`.
- **Still to come, in DEMO1:** the demo half of each test (render `previews/demo.mp4`, then the review sheet against the last
  passing demo). It is wired in as each demo is made.

## FONT1: every piece of text can take any font. APPROVED 2026-10-21 (owner: "approved")

Owner, 2026-10-21: "All templates using letters should support any font."

**Where things stand.** Every template with text already has a font control that takes any installed font. Three templates
share one control across several texts, and two leave a text out entirely:

| Template | Texts | Font controls now | Gap |
|---|---|---|---|
| Basic Lower Third | Title, Subtitle | Font (the subtitle follows it) | the subtitle can't differ |
| Locator map | Place Name, Subtitle, Map Credit | Font (the subtitle follows it) | **Map Credit is fixed to Inter** |
| Route Leg map | From Name, To Name, Map Credit | Font (To Name follows it) | **Map Credit is fixed to Inter** |
| Box Wipe, Credits, Title | | one per text | none |
| Animated Title, Sign-off, Typewriter | one text each | Font | none |

Only Animated Title's test checks that its Font control works.

**Proposed fix**
1. **One font control per text role**, named like Credits, Title and Box Wipe:
   - Basic Lower Third: "Font" becomes Title Font and Subtitle Font.
   - Locator: Name Font (Place Name), Subtitle Font, Credit Font.
   - Route Leg: Name Font (both names, so they always match), Credit Font.
   - Each new control defaults to the font that text uses now, so the default look doesn't change.
   - Renaming "Font" breaks no values file (none sets it). Major version bump for these three (2.0.0), noted in each RESULT.md.
2. **A font check in every lettered template's test**: render with another font (Montserrat Bold) for each font control and check
   that only that text's width changes. 8 templates.
3. **A rule for new templates**: in SKILL.md (lessons) and the README's "Making a template": every text gets a font control;
   texts that must match share one; nothing is fixed to a font.
4. Rebuild, run all tests and `tools/verify.py`, then commit, tag and push. No demo changes are needed (they don't set fonts).

Box Wipe (built, v0.5.31) already follows this: Title Font and Subtitle Font, Caveat Brush by default.

**Done 2026-10-21 (v0.5.32).** Basic Lower Third, Locator and Route Leg are 2.0.0 with a font control per text role (Map Credit
included); `tools/fontcheck.py` runs in the tests of all 9 templates with text (Animated Title and Box Wipe keep their own font
checks); the rule is in SKILL.md and the README. `tools/verify.py --all`: 13 of 13 pass, every demo matches. Found on the way: the
first run said the maps' fonts never changed, but the check was wrong (Pillow's `getbbox()` on RGBA sees only alpha, and a map is
opaque); it now compares every channel. A font name that isn't installed falls back to the template's own font without an error.

## FONT2: say so when a font is missing, before rendering. APPROVED 2026-10-21 (owner: "FONT2 approved")

Owner, 2026-10-21: "if a needed font is missing, it should notify before running the template."

**The problem.** EffectCraft draws a font it doesn't have in the template's own font and reports nothing (found in FONT1). So a
misspelt font in a values file, or a template whose default font isn't installed (Box Wipe's Caveat Brush on a fresh machine),
renders without warning in the wrong font.

**Proposed fix**
1. **`tools/render.py` checks every font first**, before anything renders: each font control's value in the values file, and the
   default of every font control the values file leaves alone. It reads the installed fonts from EffectCraft
   (`effectcraft-cli exec text.fonts`: families and their styles) and accepts "Family Style", "Family" or `{font, style}`.
2. **When one is missing it stops** (exit 1, nothing rendered) and lists every missing font in one message, each with its fix:
   ```
   Fonts missing, so nothing was rendered:
     Title Font "Caveat Brush Regular": install fonts/caveat_brush/CaveatBrush-Regular.ttf from this repository
     Subtitle Font "Montserat Bold": not installed; did you mean "Montserrat Bold"?
   ```
   The fix names the repository's own font file when there is one (`fonts/`), and otherwise the nearest installed name.
3. **`tools/render.py --check-fonts`** runs only this check (for agents, MPT and before a batch). `tools/demo.py` and
   `tools/verify.py` render through `render.py`, so they stop the same way, before the first segment.
4. **In the EffectCraft app** (opening a `.ectemplate` by hand) the scripts can't step in; each template README's Fonts line
   already names the font files to install, and the top README gets one line saying so.
5. **Test** (`tools/tests/test_fonts.py`, with the stand-in CLI `test_versions.py` uses, so no EffectCraft run): a missing value
   font, a missing default font, a near-miss name, a `{font, style}` value and an all-installed case; the missing cases must stop
   before the stand-in's render is called. Then SKILL.md (the rule and `--check-fonts`), commit, tag and push.

**Done 2026-10-21 (v0.5.33).** `tools/render.py` checks every font before rendering and stops with the list (a misspelling gets
"did you mean"; a repository font gets its file); `--check-fonts` checks only. `tools/demo.py` checks every card and overlay up
front (a bad demo stops in 0.2 s). `tools/tests/test_fonts.py`: 6 of 6; `test_versions.py` 9 of 9; every template's defaults are
installed here; Box Wipe and Locator re-verified with their demos unchanged.

## DEMO2: a title page and an end page on every demo reel. APPROVED 2026-10-21 (owner: "proceed with DEMO2")

Owner, 2026-10-21: "For the demo reel, they need a title page and an end page." "The demo reel identifies the template name, the
product and product versions it works with and their web links and version of the template. End page is for credits and web
links. Include a link to Artcraft in the end credits."

**Proposed (recommendations; the open questions are below)**
1. **Title page**, about 3 s, first in every template's demo reel (16x9 and 9x16), filled in from `template.json` so it is never
   out of date:
   ```
   Box Wipe Lower Third
   Template version 1.0.0
   For EffectCraft 0.13.0 (tested)
   getartcraft.com/apps/effectcraft · github.com/storytold/effectcraft
   ```
   "Tested" lists every EffectCraft version in the `tested` records (`tools/verify.py` writes them), as a range when there are
   several (0.13.0–0.14.1).
2. **End page**, about 4 s, last in every reel: the credits and links.
   ```
   Credits
   Photos © Gregory Kirkendall · Music: "Relaxing Flute Tune" by Kerri, Sound Effects Factory
   Maps: Natural Earth; © OpenStreetMap contributors          (only on reels that show a map)
   Fonts: Caveat Brush, Inter (SIL Open Font License)          (the template's own fonts)

   Templates  github.com/gkirkendall/craft-templates
   ArtCraft   getartcraft.com
   EffectCraft  getartcraft.com/apps/effectcraft

   Sponsored By PixBack - Photo and Video Backup to Google Photos
   getpixback.com
   ```
   The sponsor lines are the owner's wording (2026-10-21), on every end page, the showreel's included.
   **All end cards the same** (owner, 2026-10-21: "change all end cards to be the same"): the Australia trip demo also ends on this
   end page. Its old end card (Credits, the ArtCraft lower third and the sponsor line in the Credits template) is dropped; its last
   shot keeps Sign-off ("Thank you for watching", blinking) and the logo fading out, then the standard end page follows.
3. **How they are made:** `tools/demo.py` adds both to any demo whose `demo.json` says `"title_page": true, "end_page": true`,
   drawing them by script in Inter (as the closing title card is now) from the template's manifest and the reel's own credits.
   Captions stay on the template's own segments only.
4. **Limits:** the reel check's 15 s limit becomes 25 s (title and end pages add about 7 s).
5. Remake all template reels and the showreel, rebuild the page; `verify.py` checks the page text against `template.json`
   (version, tested range) by OCR on one reel. Commit, tag and push.

**Owner's answers (2026-10-21):**
- **Which reels:** every template reel (16x9 and 9x16) gets both pages; the showreel gets one title page for the whole collection
  ("Craft Templates", the EffectCraft versions they are tested with, the links) and one end page. The Australia trip demo keeps its
  own opening title and end card.
- **Drawn by script** in Inter, from `template.json`, as in point 3.
- **The end page ends with the independent-project line**, small: "An independent project, not made or endorsed by the EffectCraft
  or ArtCraft teams."
- **Links in short form** (github.com/gkirkendall/craft-templates, getartcraft.com), no https://.

**Done 2026-10-21 (v0.5.35).** `tools/demo.py` draws both pages from `template.json` and the reel (`"title_page"`, `"end_page"`;
fonts the values pick are credited too; long lines break after " - " on 9x16). All 17 reels have both pages, the trip demo ends
on the same end page (64 s) and the showreel opens on a collection title page (77 s; its excerpts skip the reels' title pages by
themselves). The reel check's limit is 25 s. `tools/tests/test_pages.py`: 6 of 6 (OCR of Box Wipe's, the showreel's and the trip
demo's pages). The owner reviewed the Box Wipe reel: "looks good".

## WEB2: GitHub hosts the page, its pictures and its videos; PixBack under the title. APPROVED 2026-10-21 ("Approved"); items 1, 2, 4 built, publishing (3) next

Owner, 2026-10-21: "I like the web page as a starting point, will need to point to artifacts committed on github. I want github
to host the page and the images/videos. At the Top - Craft Templates, New Line, Then the "Sponsered By PixBack" information from
the end card with a clickable link to the website."

**Where things stand.** The page is `docs/index.html`, linking up (`../effectcraft/…`) to the committed sheets and reels. The
repository is private and GitHub Pages is off, so nothing is hosted yet.

**Proposed**
1. **Top of the page:** "Craft Templates", then on its own line "Sponsored By PixBack - Photo and Video Backup to Google Photos"
   (the end card's wording), linking to https://getpixback.com/. The current intro sentence follows.
2. **The page at the repository root** (`index.html`, written by `tools/page.py`; `docs/` removed), with a `.nojekyll` file so
   GitHub serves every file as it is. GitHub Pages then serves the `main` branch root: the page at
   https://gkirkendall.github.io/craft-templates/ and every sheet, poster and reel straight from the committed files (Pages
   serves MP4 with seeking; the whole repository, about 140 MB, is well within its 1 GB limit). No copies, no outside hosting.
3. **Switching Pages on** (`gh api` or Settings ▸ Pages: source `main`, folder `/`) makes the page public. GitHub serves Pages
   from a private repository only on a paid plan, and the site is public either way, so this is the publishing step: first the
   pre-publication checks already agreed (history squashed; no travel dates, footage file names or photo metadata; no non-free
   assets), then Pages on, then the page and a reel opened from github.io to check.
4. `tools/tests/test_page.py` gains: the sponsor line and its link; `.nojekyll` present; every link resolves from the root.
5. **YouTube: later, not part of WEB2** (owner, 2026-10-21: "I already have a YouTube page for PixBack, I will add it as a
   collection there. Something to look at after Github is working."). The reels go up as a collection on PixBack's channel once
   the GitHub page works; then the page may gain "Watch on YouTube" links, as a plan of its own. Check before that upload: the
   Sound Effects Factory licence allows YouTube, and what to do about a Content ID claim.

**Decided (owner, 2026-10-21):** publishing is "squash, then public": run the pre-publication checks, squash the history to one
commit, make the repository public and switch Pages on (free). Each of those GitHub steps is confirmed with the owner as it comes.

**Pre-publication check, run 2026-10-21 (v0.5.36): clean, with one finding.** No travel dates (the only date in the tree is
today's work date; the footage dates appear nowhere), no footage file names except generic examples (`IMG_5322.jpg` in a
note, test files `IMG_000n`), no EXIF dates or GPS in any tracked picture or video, coordinates at 3 decimals, no Vecteezy
licence number, no third-party reels or music files, 108 MB of files. **Finding:** every commit's author email is the owner's
personal address, which the squashed public commit would show. **Fix:** the public commit and all later ones use GitHub's
no-reply address (`61368993+gkirkendall@users.noreply.github.com`, set as this repository's `user.email`).
**Second finding:** the 61 tags (v0.1.x … v0.5.36) point at the old commits, so the old history stays reachable through them
after a squash, and GitHub can keep serving old commits by their ID. **Proposed publishing steps (each confirmed):**
1. Keep the full history privately: rename the GitHub repository to `craft-templates-history` (stays private), and save a
   local copy as `~/projects/craft-templates-history.bundle`.
2. Make one new commit holding today's tree, with the no-reply address; tag it `v0.6.0` (first public version).
3. Create a new public `gkirkendall/craft-templates` and push only that commit and tag (no old tags, no old commit IDs).
4. Switch Pages on (`main`, `/`), then open https://gkirkendall.github.io/craft-templates/ and play a reel to check.

## BRAND1: Pixie's Craft Templates. APPROVED 2026-10-21 ("approved")

Owner, 2026-10-21: "i had mentioned at tie-in with Pixie. Perhaps this is the time to decide on that since the new repo could be
called "pixies-craft-templates and there could be a graphic based on Pixie". Settles the "For discussion later" item below, and
comes before WEB2's publishing, because the name is in the repository address that every reel's end page shows.

**Proposed**
1. **Name:** "Pixie's Craft Templates" on the page, README, title pages and showreel; repository `gkirkendall/pixies-craft-templates`,
   page at https://gkirkendall.github.io/pixies-craft-templates/. The sponsor line stays as it is.
2. **The graphic:** Pixie in the **peach** dinosaur costume, the ad's approved still (`pixback_launch/assets/pixie_chihuahua_model/
   models/pixie_dino_neutral.png`), cut out from its grey background by script (`rembg`, local, free; needs installing) and placed
   by script; all words set by script. Not turquoise: Higgsfield's IP filter blocked the turquoise costume in the ad. A new pose
   (Pixie "crafting") would be a paid render needing its own approved render list; not proposed.
3. **Where:** the page header (Pixie beside the title and sponsor line), the README top, and every reel's title page and end page.
   The 17 reels are rendered again anyway for the new address on the end page (local, free).
4. **Licence:** the Pixie picture is PixBack's mascot, © Gregory Kirkendall, all rights reserved, not under the templates' licence:
   listed in CREDITS.md and the page footer like the photos; never inside a template file.
5. **Then WEB2's publishing** under the new name: the current repository renamed `craft-templates-history` (private), a new
   public `pixies-craft-templates` with one commit `v0.6.0` by the no-reply address, Pages on.
**Decided (owner, 2026-10-21):** the name is written "Pixie's Craft Templates"; the graphic is the existing peach still, cut out
by script; Pixie appears on the page, the README and every reel's title and end page.
**Built 2026-10-21 (v0.5.41):** `tools/brand/make_pixie.py` → `brand/pixie.png` (reels, README) and `brand/pixie_web.png` (page);
page header, README top, every reel's title and end page (`demo.py` `page_card`: Pixie left of the text on 16x9, above it on 9x16);
new address on the end page, the Credits sheet, `maps.py` and the schema id; CREDITS.md and the footer credit Pixie. All 17 reels,
the Credits sheet and the page remade; every test passes (fonts 6/6, page 13/13, pages 6/6, versions 9/9, catalog 13/13).
**Graphic changed (owner, 2026-10-21: "pixie_C approved, converted to peach and purple"):** the friendliest Pixie is the ad's
turquoise candidate `pixback_launch/video/dinosaur_ad/review/pixie_candidates/pixie_C.png` (tongue out, slight smile); its
turquoise fur is recoloured by script to the final costume's peach, purple spots and spikes kept. One test image first, opened
for the owner; if the fur looks wrong, the fallback is a paid Higgsfield edit (render list first) or the peach neutral still.
**Recolour accepted (owner, 2026-10-21: "fixed pixie will work"):** the second pass (blue fringes at the spot edges moved to
purple, purple deepened to the costume's) by `recolour_pixie.py`; it goes in `tools/brand/` with the cut-out so the picture can be
remade. `rembg` 2.0.85 installed by the owner (Anaconda Python; it also moved Pillow to 12.3.0, all checks still pass).

## INSTALL1: "How to install" on the page and in the README. APPROVED 2026-10-21 ("approve INSTALL1")

Owner, 2026-10-21: "we might want ot have a "how to install" section on the web page and the README", after asking "will these
templates show up in the GUI?".

**How the templates reach EffectCraft's window (read from EffectCraft 0.13's source, 2026-10-21).** Each template is an
Essential Graphics template (`.ectemplate`). In the app: **File ▸ Import ▸ Essential Graphics Template…** adds it to the open
project as a composition, with its named controls in the Essential Graphics panel (EffectCraft's own command,
`essential.importTemplate`). The Home screen's **New Project from Template** gallery lists the `.ectemplate` files in the
`Templates` folder of EffectCraft's settings folder; its reader does not check the template kind, so ours should list there
too (named by file, under "My Templates"), but that is untested.

**Proposed: one short "How to install" section, the same on the page (under the showreel) and in the README:**
1. **Get EffectCraft** 0.13 or later (getartcraft.com/apps/effectcraft).
2. **Download a template:** each row on the page gains "Download" links to its `.ectemplate` files, one per size (16x9, 9x16),
   served by GitHub Pages straight from the repository; or the whole collection with GitHub's "Download ZIP".
3. **Install its fonts:** each row names the fonts it uses, each linked to its folder in `fonts/` (double-click a font file to
   install it on macOS or Windows; Linux: copy it to `~/.local/share/fonts`). Every font is free (SIL Open Font License).
4. **Use it:** File ▸ Import ▸ Essential Graphics Template…, then change the text, colours, fonts and timing in the Essential
   Graphics panel. (To find it under New Project from Template instead: copy the file into EffectCraft's `Templates` folder; only
   if the test below passes.)
5. **From a script** (for tools like MPT): `tools/render.py`, one line and a link to the README's existing section.
**Decided (owner, 2026-10-21):** per-template download links (plus GitHub's ZIP for everything); the gallery step goes in only
after the owner's test shows a template listed there. Gallery folder: `~/Library/Application Support/EffectCraft/Templates`
(macOS), `%APPDATA%\EffectCraft\Templates` (Windows), `~/.config/effectcraft/Templates` (Linux), as EffectCraft's `app_dirs.rs` sets it.
**Built 2026-10-21 (v0.5.41):** the five steps on the page (under the showreel) and in the README; a download link per template
size (26) and font links per row; `test_page.py` 13/13. Waiting: the owner's gallery test.
**Test:** the owner imports one template through the menu and, if wanted, the gallery copy, by eye (EffectCraft's window cannot be
driven from here); `test_page.py` checks every download and font link resolves; the README and the page say the same steps.

## END2: "See Pixie on YouTube" under Pixie on the end page. DONE 2026-10-21, owner: "i like the new end card, approved" (v0.5.42; all 17 reels remade, every test passes; the YouTube lines are read from Pixie's column, since OCR of both columns at once misreads "YouTube")

Owner, 2026-10-21: "to the end credit card. Under (?) Pixie - "See Pixie on YouTube - youtube.com/@PixBack" format as needed".
The handle matches `pixback_launch/LINKS.md`.
1. **End page only** (title pages unchanged). Directly under Pixie, centred on him, two lines: "See Pixie on YouTube" (Inter
   SemiBold, white) and "youtube.com/@PixBack" (Inter Medium, the link blue), split at the " - " like the sponsor line.
   16x9: Pixie's column on the left, Pixie made a little smaller (0.66 → 0.56 of the frame height) so the lines fit beneath him.
   9x16: between Pixie and "Credits".
2. `test_pages.py` also reads "See Pixie on YouTube" and "youtube.com/@PixBack" on the end pages.
3. All 17 reels remade (local, free, about 8 min, after FL1b frees the GPU); every test run; a reel opened for the owner; commit,
   tag, push.


## For discussion later (owner, 2026-10-21; not actioned)

- **Name and brand: "Pixies Craft Templates"**, using Pixie from the PixBack ad. The owner means to tie media creation (these
  templates) in with media backup (PixBack). The templates stay free. Nothing is renamed or rebranded until this is discussed.
  Points to settle then: the repo and README name, whether Pixie appears in demos or the showreel, and how PixBack is linked.
