---
name: craft-templates
description: Use and make motion-graphics templates for EffectCraft from the craft-templates repository — map cards (a route between two places, a locator that zooms to a place), lower thirds, titles (plain, animated letter by letter, typewriter), glints, a corner logo, end-card credits and sign-off, and a fill-the-frame background, filled from a values file or a list of stops and rendered from the command line. Use when someone wants a map, caption, logo, sparkle, title or end-card graphic for a video, wants to fill or render one of these templates, or wants to build a new template for this repository.
---

# craft-templates

Free templates for [EffectCraft](https://github.com/storytold/effectcraft) (an After Effects–style motion-graphics app). Each
template has named controls (text, colours, pictures, positions, a font) that you fill from a JSON values file, then render with
EffectCraft's command-line tool. Paths below are relative to the repository root.

## What you need

- Python 3 with Pillow (`pip install pillow`).
- EffectCraft's command-line tool, `effectcraft-cli` (on the PATH, or give its path with `--effectcraft-cli`). The templates need
  EffectCraft 0.13.0 or later.
- ffmpeg, only to lay a rendered overlay onto a clip.

## Using a template

1. **Pick one.** The README's "Templates" table lists every template, its sizes (`16x9` 1920×1080, `9x16` 1080×1920), the
   EffectCraft versions it was tested with, and what it does. Each version folder's `README.md` lists its controls and any credit
   it needs.
2. **Write a values file**: a JSON object of control names to values. Start from the template's `examples/`. Any control you
   leave out keeps its default.
   - Text: a string. Colour: `"#rrggbb"`. Number: a number. Checkbox: `true` or `false`. Dropdown: one of the item names its
     README lists (`"Corner": "Top Left"`).
   - Point: `[x, y]` in pixels of the picture it refers to (the map templates' points are in map-picture pixels).
   - Picture: a file path, relative to the values file.
3. **Check one still first**, then render the clip:

   ```
   python3 tools/render.py effectcraft/lower_thirds/basic --variant 16x9 --values my.values.json --out check.png --frame 2
   python3 tools/render.py effectcraft/lower_thirds/basic --variant 16x9 --values my.values.json --out lower_third.mov
   ```

   Overlay templates render ProRes 4444 with alpha, so give `--out` a `.mov` name; a template that fills the frame (Fill the
   Frame) renders H.264, so `.mp4`. Each version folder's `template.json` says which (`output`). Look at the still (and open the result
   for the person you are working for) before rendering many.
4. **Lay an overlay onto a clip** when needed, scaling it to the clip's size, for example:

   ```
   ffmpeg -i clip.mp4 -i lower_third.mov -filter_complex "[1:v]scale=iw*1024/1920:-1[o];[0:v][o]overlay=0:0:shortest=1" -c:a copy out.mp4
   ```

5. **Add the credits the template's README names**, in the video and in its description.
   **A logo across a whole video:** render Corner Logo once per photo or clip, with `"Fade": "Fade In"` on the first,
   `"Steady"` on those between and `"Fade Out"` on the last; it then holds still across every cut.
6. **Demo reels:** each version folder's `previews/demo*.json` describes its demo, which `tools/demo.py` makes from footage and
   music kept outside the repository (`--footage DIR --music DIR`); `tools/verify.py … --footage DIR --music DIR` remakes and
   compares them. A new template gets a demo the same way. The footage is named by key, never by its file name.
   Each card or footage segment has a `"caption"` naming the feature on screen (`"Style: Bounce · By: Words"`), drawn bottom
   left, or top left with `"caption_at": "top"` where the template sits bottom left.
   Every reel opens on a title page and ends on an end page (`"title_page": "template"` or `"collection"`, `"end_page": true`),
   drawn by `tools/demo.py` from `template.json` (name, version, EffectCraft versions tested, links) and the reel itself (music,
   maps and fonts credited; the templates, ArtCraft and EffectCraft links; the PixBack sponsor; the independent-project line).
   A new track needs its credit in `MUSIC_CREDITS`. `tools/tests/test_pages.py` reads the pages back.
7. **Style sheet and web page:** `previews/styles.json` lists a sheet's cells (label, values, moment, size; overlays over a dimmed
   photo); `tools/sheet.py previews/styles.json --footage DIR` writes `previews/styles.jpg`. `tools/catalog.py` (or
   `tools/page.py`) then rewrites the page `index.html` (repository root, served by GitHub Pages); `tools/catalog.py --check` fails on a missing or stale sheet or
   page, and `tools/tests/test_page.py` checks the page's rows and links. A new template needs both before it is committed.

### Map templates

The Route Leg and Locator templates need a map picture drawn for the places, by `tools/maps.py`.

1. Once: `python3 tools/maps.py fetch` (Natural Earth data, about 52 MB, into `data/`).
2. A stops file: a JSON list in travel order, each `{"name": …, "subtitle": …, "lat": …, "lon": …}` (example:
   `effectcraft/maps/route_leg/effectcraft-0.13/examples/australia.stops.json`).
3. Draw, and optionally render in the same step:

   ```
   python3 tools/maps.py route-legs --stops my.stops.json --out maps/ --variant 16x9 [--inset] [--render]
   python3 tools/maps.py locator --stops my.stops.json --stop 0 --out maps/ --variant 16x9 [--inset] [--render]
   ```

   Each card gets `map_*.png`, a ready values file `*.values.json` and, with `--render`, a `.mov`. `--inset` makes the corner
   card over transparency instead of the full-frame map.
- Legs under 25 km get no card (`--min-leg-km`). Legs under 200 km get roads, towns and parks from OpenStreetMap (`--osm-km`),
  fetched from the public Overpass server one query at a time and cached in `data/osm/`. Respect its usage policy: for heavy or
  commercial use, pass `--overpass-url` for your own or a paid server.
- **Credit:** a map with OpenStreetMap detail carries "© OpenStreetMap" in its corner (filled automatically) and the video's
  description or credits must say "Map data © OpenStreetMap contributors, https://www.openstreetmap.org/copyright". Natural Earth
  needs no credit.

## Making a new template

Follow the layout the existing templates use; `effectcraft/maps/route_leg/` is a complete example. A template folder holds one
self-contained folder per app-version line, named after the version it was first built with:

```
<app>/<category>/<template>/
  README.md            written by tools/catalog.py: what it is, and which folder to use with which app version
  effectcraft-0.13/    everything for EffectCraft 0.13.x; works on its own
    template.json      manifest (schema/template.schema.json): id = the template folder, sizes, controls with defaults, fonts,
                       credits, "built_with" and the "tested" records (written only by tools/verify.py)
    README.md          what it does, its controls, how to fill it, credits needed
    build/build.py     builds templates/<name>_<size>.ectemplate by script (tools/ecbuild.py); never only by hand
    templates/         the built .ectemplate files (zips that carry their own pictures)
    assets/            pictures it ships with, each listed in assets/SOURCES.md with its licence
    examples/          values files (and any input files) to start from
    tests/run.py       a free test with measured checks, ending "N of M checks pass"; tests/RESULT.md records the result and
                       the tested-versions history; tests/out/ is not committed
```

### App versions

Templates are tied to the app versions they were **tested** on, not to versions anyone claims.

1. **Check the version first.** `python3 tools/render.py <template> --which` names the folder it will use for the installed
   app and its tested range. On a version outside the range it warns and renders anyway.
2. **Untested version: verify before relying on it.** `python3 tools/verify.py <template> --effectcraft-cli PATH` (or `--all`)
   runs the folder's test with that version and records pass or fail. `--list` shows what would run.
3. **Never edit the `tested` records or `app_min_version` by hand**; `tools/verify.py` writes them.
4. **A new app release breaks a template: fix it in a new folder, never in a frozen one.**
   1. Copy the current folder to `effectcraft-<new version>` (e.g. `effectcraft-0.15`) and set `built_with` and
      `"tested": []`.
   2. Fix `build/build.py`, rebuild, bump the template's `version`, and run `tools/verify.py`.
   3. Mark the old folder `"frozen": true`. It stays usable by people who cannot upgrade: `render.py` chooses it for their
      version, and verify re-checks it on an older install.
5. **A new template** starts in `effectcraft-<installed version>` (e.g. `effectcraft-0.13` for 0.13.0) with `"tested": []`;
   `tools/catalog.py --check` fails until `tools/verify.py` has recorded a pass.

- **Only freely redistributable material**: public domain, CC0, CC BY, SIL OFL, MIT or Apache. Nothing personal-use, demo, or
  from paid stock or bought templates — copy a bought template's style and ideas, never its files or content. Fonts go in
  `fonts/<family>/` with their licence file; Inter ships with EffectCraft.
- One element per template (a glint, a logo, a lower third); people stack several on the timeline.
- **Every text takes any font** (Pixie, 2026-10-21): each text gets its own font control (`"as": "font"`), named for its
  role (Title Font, Subtitle Font, Credit Font); texts that must always match share one (Route Leg's Name Font); nothing is fixed
  to a font, map credits included. Each test calls `tools/fontcheck.py`'s `font_checks`: another font changes the frame, and with
  the control's own texts emptied it changes nothing.
- Comparing frames: Pillow's `getbbox()` on an RGBA image sees only alpha, so it finds no change on an opaque frame (a map);
  use `getbbox(alpha_only=False)`. A font value is a family and style ("Montserrat Bold") or `{font, style, size}`; a name
  that isn't installed falls back to the template's own font without an error, so `tools/render.py` checks every font first
  and stops, naming each missing one and its file in `fonts/` (FONT2); `tools/render.py TEMPLATE --check-fonts` runs only the
  check, and `tools/demo.py` runs it for every card and overlay before rendering anything.
- Tests check measured facts, not looks: positions and start times from the alpha channel, text read back with tesseract
  (inverted and doubled in size; `--psm 6` for a block, `--psm 7` for one line; straighten curly quotes before comparing).
  Where elements can overlap (Glint Set at a small Spread), mask out the others' places before checking one is empty.
- Keep fonts free (SIL OFL) and in `fonts/`; League Gothic and Montserrat are there for titles, Caveat Brush and Pacifico
  for script.
- Every size (`16x9`, `9x16`) is built from the same `build.py`.
- Scripts in a version folder find the repository root by looking for `tools/` (`ROOT = next(p for p in HERE.parents if (p / "tools" / "ecbuild.py").is_file())`), never by counting folders.
- Before committing: `python3 tools/catalog.py --check` (schema, files, fonts, asset licences) must pass; then
  `python3 tools/catalog.py` regenerates the README table.

### EffectCraft command-line lessons

Found while building the templates here; `tools/ecbuild.py` already handles the first four.

- Set an expression with `prop.setExpression`. `effectcraft-cli set … --expression` needs a value of the property's own type, and
  a path property has none to give, so the expression is silently not set.
- Several controls of one kind (two Point Controls) are told apart by renaming each effect with `prop.renameGroup`; expressions
  then read `effect("From Position")("Point")`.
- Key times: `prop.addKey` with `timeBase: "comp"`; then `keys.selectAll` and `keys.easyEase`.
- An exported template is a zip; rendering a `.ectemplate` unpacks its pictures into a "<name> Media" folder beside it, so render
  from a copy (`tools/render.py` does).
- `createPath` takes plain `[x, y]` arrays; property values passed straight in come out as `[0, 0]`.
- Text layers centre on their position unless created with `"justify": "left"` (or `"right"`).
- Only for texts that must match (see the font rule above), one font control can drive several text layers: put it on one layer (`essential.addProperty` with `"as": "font"`) and give the
  others the expression `text.sourceText.style.setFont(thisComp.layer("Title").text.sourceText.style.font)`; their own text
  controls still apply.
- Fit text to a box with `sourceRectAtTime(time, false)` and a scale expression; shrink each line on its own.
- Clip a layer to a card with a shape layer as its track matte (`layer.setTrackMatte`, kind `alpha`).
- A ProRes render has alpha only with `--format prores --prores 4444 --channels rgba`.
- When checking renders with Pillow, compare in RGB: `getbbox()` on an RGBA difference looks only at the alpha channel.
- `prop.setExpression` and `prop.set` accept a path that does not exist without an error (`transform/anchorPoint` instead of
  `transform/anchor`). List the real paths with `effectcraft-cli props <comp> <layer> --flat --project P` and check a still.
- A media control swaps only the layer it is attached to, and a nested comp's media cannot be exposed as a control. To show one
  picture twice (sharp and blurred), use one media layer and an adjustment layer above it (see `effectcraft/utility/fill_frame/`).
- Give a footage layer whose picture can be swapped the anchor expression `[width / 2, height / 2, 0]`: a fixed anchor belongs
  to the default picture's size.
- EffectCraft 0.13 imports a numbered file whose folder holds other numbered files (`IMG_5322.jpg` beside `IMG_5156.jpg`) as
  one image sequence, and shows colour bars where the sequence has no frame. It also shows a file with an upper-case extension
  (`.JPG`) as missing, and cannot read HEIC. `tools/render.py` hands every media file over under its control's name in a temp
  folder ("Media.jpg"), and converts HEIC to PNG with ffmpeg.
- A template whose length should be chosen: make the comp long and give it a number control named "Duration"; `tools/render.py`
  renders up to that many seconds.
- `source.duration` of an MP4 is usually one frame long in EffectCraft 0.13 (it reads the track header, not the edit list). To
  loop a clip exactly, give the template a number control named "Clip Length", which `tools/render.py` fills from ffprobe, and
  remap with `time % length`.
- A Dropdown Menu Control (`ecbuild.add_controls` with `("Corner", "Dropdown Menu Control", (items, default))`, exposed with
  `essential.addProperty … "as": "dropdown"`) is stored 0-based, and a template's values file sets it only by that number,
  while expressions read it 1-based. Give it `"type": "dropdown"` and its `"options"` in `template.json`: `tools/render.py`
  then takes the item's name in a values file and passes the number.
- In expressions, `substr` is not available ("not a callable function"; `effectcraft-cli script` has it): use `slice`. A text
  expression that fails falls back silently to the plain text, so check a still for every branch. `"\r"` in a text
  expression's result breaks the line.
- Colour text with an `ec.generate.fill` effect whose colour has the Colour control's expression, not a fill expression on
  the text (that clashes with a Source Text expression). Add `ec.perspective.dropshadow` (distance 3, softness 14) to keep
  white text readable over bright footage; tests render with the shadow off.
- Draw a custom shape (the Sign-off hearts) with `shape.newPath`: Bézier points with in and out tangents, `closed: true`,
  `space: "layer"`; see `effectcraft/titles/sign_off/effectcraft-0.13/build/build.py`.
- `tools/demo.py` writes a temporary `_demoNN.values.json` per clip and deletes it; such files are gitignored.
- **Text animators** (per letter, word or line): `layer.addTextAnimator` with `{"properties": ["position", "opacity", ...]}`
  (also scale, rotation, blur, tracking, fillColor), then `layer.addTextSelector` with `"kind": "expression"`. Paths are
  `text/animators/animator/...`, then `animator#2`, `animator#3`. An Expression Selector's `amount` reads `textIndex` (1-based)
  and `textTotal`; a negative amount overshoots (Scale Pop, Wave). See `effectcraft/titles/animated_title/`.
- A selector's `basedOn` and a layer's `text/moreOptions/anchorGrouping` take a value only; an expression on either is
  ignored. To choose them by a control, build one text layer per choice and show one by opacity.
- A hidden text layer can hold the Text and Font controls for several visible ones: they read it with
  `thisComp.layer("Raw").text.sourceText` and keep its font with `.style.setText(newText)`.
- Fonts that ship with EffectCraft include Inter (styles "Regular", "Medium", "SemiBold", "Bold"); `effectcraft-cli exec text.fonts`
  lists every family and its exact style names.
- tesseract misses small, spaced-out text read together with large text: read each band of text on its own (`--psm 7`, enlarged).
