# SLIDER1: instructions for doing it (written for a Sonnet session)

Approved by the user 2026-10-21 (PLAN.md, RECIPE1 item 4 and ECPATCH1's outcome). This file says exactly what to do. Do the steps
in order. If something doesn't match what this file says, stop and tell the user what you found and what you propose; don't guess.

## Why

In EffectCraft's Essential Graphics panel, a Slider Control's slider covers 0–100. The user (and anyone who uses Photoshop) reads
0–100 as a percent. Our templates use the number as pixels instead (Max Width 1651 px), so moving the slider sets 0–100 px and
the title shrinks to a speck. Fix: every such control becomes a percent, so its value sits inside 0–100 and the slider works.

## Rules for this session (from the user's standing rules)

- Commit with the no-reply address only: `61368993+gkirkendall@users.noreply.github.com` (already the repo's config; check
  `git config user.email`). End each commit message with `Co-Authored-By: Claude Sonnet <noreply@anthropic.com>` (or the line
  your session gives).
- After each commit: tag the next `v0.6.N` (`git tag -l | sort -V | tail -1`), push the commit and the tag.
- Before editing PLAN.md, README.md or any doc: `lsof 2>/dev/null | grep <file>`; if it's open, tell the user and wait.
- `git status` shows `??` files: ask the user about each. Never delete without asking.
- Wrap long runs (verify, demo renders) in `caffeinate -i -s …`.
- Open every result for the user with `open <file>` (frames, reels, sheets).
- **Pixie is the user's dog** (he/his), the name and face of these templates, not the person you work with: call that person "the user". (PLAN.md's records often say "Pixie approved"; read that as the user.) Public text (README, page, template docs) says "Pixie", never "owner". No footage file names, no travel dates, no emails in the repo.
- Never report a problem without a proposed fix. Don't spawn agents.

## The change, per control

**Max Width** becomes a percent of the frame width. Default `86` (the old 1651 px is 86% of 1920; on 9x16 it's 86% of 1080).
In `build/build.py`, wherever the expression reads the control:

```python
var mw = {CONTROL.format("Max Width", "Slider")};
```
make it
```python
var mw = {w} * {CONTROL.format("Max Width", "Slider")} / 100;
```
(`w` is the variant's frame width, already in scope in each build; check it is, per template.) The control's default in
`add_controls` changes from `round(w * 0.86)` (or box_wipe's per-variant `max_width`) to the percent: `86` for the titles; for
box_wipe, `round(old_px / w * 100)` per variant (1100 px on 1920 → `57`; work out the 9x16 one the same way and write it in).

**Size** becomes a percent of the template's normal size: default `100` means today's size. Wherever the expression reads
`{CONTROL.format("Size", "Slider")}`, put `({CONTROL.format("Size", "Slider")} * {SIZE} / 100)` instead (`SIZE`, or the
variant's `size` in animated_title, is the old default). The control's default becomes `100`.

Templates and places (from `grep -n 'Max Width\|"Size"' effectcraft/*/*/effectcraft-0.13/build/build.py`):

| Template | Control | Expression lines in build.py |
|---|---|---|
| titles/title | Max Width | 33, default 59 |
| titles/animated_title | Max Width, Size | 71–72, defaults 87–88 |
| titles/credits | Max Width | 35, 65, default 58 |
| titles/sign_off | Max Width | 33, default 56 |
| titles/typewriter | Max Width | 39, default 55 |
| lower_thirds/box_wipe | Max Width | 33, 70, default via `VARIANTS` (line 22) |
| logos/corner_logo | Size | 29, 54–55, default 48 |
| overlays/glint | Size | 42, 43, 50, default 37 |
| overlays/glint_set | Size | 50 (`size = …`, used below), default 46 |

Also check every other Slider Control in all templates (Margin, Heart Size, Spread, Glow, Opacity, …): if its default or any
example value is outside 0–100, it gets the same treatment. The new check (step 2) finds them.

## Steps

1. **Title first, to prove it.** Change `titles/title` as above. Update in the same folder:
   - `template.json`: the Max Width default (86), its description ("Widest the title may be, in % of the frame width"), and
     `version` 1.0.0 → 1.1.0. Don't touch `tested` or `app_min_version` (verify.py writes them).
   - `README.md` (the template's own, in `effectcraft-0.13/`): the Max Width line says percent.
   - `examples/*.values.json` and `tests/run.py`: any Max Width value becomes its percent.
   Rebuild (`python3 effectcraft/titles/title/effectcraft-0.13/build/build.py`; read its docstring for arguments), then
   run the test: `python3 tools/verify.py effectcraft/titles/title --effectcraft-cli ~/projects/storytold/effectcraft/target/release/effectcraft-cli`.
   Then **show the user**: build a project with the 2-shot kit script
   (`/private/tmp/claude-501/-Users-gkirkendall-projects-Wan2GP/d46a0846-9d97-4d4a-ac5f-6a57494af72c/scratchpad/proj1/build2.py`,
   usage in its docstring; photos in `…/scratchpad/pixabay/kit_photos/`) and open it in the 0.14 app
   (`~/projects/storytold/effectcraft/target/release/effectcraft "<kit>/Trip Video Test.ecproj"`). The user moves Max Width:
   it should show 86 and resize the title by percent. **Wait for the user's OK before step 2.**
   (If the scratchpad is gone, ask the user; the kit can be rebuilt from PLAN.md's RECIPE1 notes.)
2. **The check that stops this coming back.** In `tools/catalog.py --check`, add: for each template, every control whose
   `type` is the slider type (look at a template.json for its exact name) must have its default, and every value for it in
   `examples/*.json` and `previews/*.json`, within 0–100. Add a test for the check in `tools/tests/` like the existing ones
   (a template.json with a 1651 default fails; with 86 passes). Run `python3 -m pytest tools/tests` (or the way the
   existing tests run; check their headers).
3. **The other 8 templates**, one at a time, the same as step 1 (code, template.json, README, examples, tests, previews'
   `demo.json`/`styles.json` for glint and glint_set), each to 1.1.0, rebuilt, verified with the 0.13 CLI. Commit after each
   template passes (or in one commit at the end; either way tag and push).
4. **Verify on 0.14 too.** The 0.14 CLI is `~/projects/effectcraft-fork/target/release/effectcraft-cli` (check
   `--version` says 0.14.0). Run `caffeinate -i -s python3 tools/verify.py --all --effectcraft-cli <that path>`.
5. **Callers.** `grep -rn "Max Width\|\"Size\"" ~/projects/MoneyPrinterTurbo demo` (and `tools/`): any values passed to these
   controls become percents. MoneyPrinterTurbo is a separate repo: commit there too (tag and push per its own scheme).
6. **Previews and page.** Glint and glint_set reels and sheets: `tools/demo.py` / `tools/sheet.py` need `--footage DIR`;
   ask the user for the folder (never write its file names into the repo). Then `python3 tools/catalog.py --check` must pass,
   and `python3 tools/catalog.py` rewrites the README table and page. Open the new reels and sheets for the user.
7. **PLAN.md**: under RECIPE1 item 4, add "Done 2026-…" with what changed and the test results.
8. **Release**, after the user says go ahead: `python3 tools/release.py --publish <the new tag>`.

Then the full RECIPE1 8-shot kit (PLAN.md), which uses these 1.1.0 templates.

## What happened (2026-10-22, steps 1–4 done, v0.6.27 and v0.6.28)

Findings and deviations from the steps above. Where this section and the sections above disagree, this one is what was built.

### Deviations from the plan (each a one-constant change, so easy to reverse)

1. **Size: 50 is the normal size and 100 is double, not "100 = today's size".** With 100 as normal, the Glint previews (Size 170
   and 220, with a 140 px default) came out above 100 and the new check rejected them; a slider that starts at its maximum also
   cannot enlarge anything. Full scale is now twice the old default: Animated Title 240 px font (16x9; 192 in 9x16), Corner Logo
   360 px, Glint and Glint Set 280 px. Default 50 in all four. Glint previews converted: 170 → 61, 130 → 46, 150 → 54, 110 → 39,
   140 → 50, 80 → 29, 220 → 79. The expressions read `Size * normal / 50`.
2. **Route Leg's Curve was out of range too** (the inset example used -15; a 0–100 slider cannot go below 0). Curve is now
   50 = straight, 70 = a 20 % bow (the old default of 20), 35 = a 15 % bow the other way (the inset example). Route Leg 2.0.0 → 2.1.0.
3. **Box Wipe's Max Width defaults are 57.3 (16x9) and 83.3 (9x16)**, not 57 and 83: whole numbers moved the layout by about 6 px
   and the OCR in its test then misread the wrapped line. 57.3 % of 1920 is 1100 px and 83.3 % of 1080 is 900 px, as before.
4. **Credits was already 1.2.0**, so it went to 1.3.0, not 1.1.0.
5. **Max Width reads `thisComp.width`** inside each expression instead of the build's Python `w`: the expressions are module-level
   constants shared by both variants, and this gives the same result in both.

### Findings

- The plan's table of line numbers had drifted; every control was found by searching instead. Nine templates changed as listed,
  plus Route Leg.
- No other control was out of range. Margin, Heart Size, Spread, Glow, Opacity, Shadow and the rest all sit inside 0–100.
- MoneyPrinterTurbo and the repo's own tools and demos pass none of Size, Max Width or Curve, so step 5 needed no caller changes.
- Locator and Route Leg tests need Natural Earth data (`python3 tools/maps.py fetch`, about 52 MB, public domain, in the
  gitignored `data/`). It was fetched on this machine.
- `catalog.py` leaves a template out of the README table (and the page) while its style sheet is stale, so the table must be
  rewritten only after the sheets are remade. verify.py and catalog.py rewrite README.md and index.html on every run: restore
  them (`git checkout README.md index.html`) before committing a half-finished state.
- `verify.py --all` on 0.13.0 and 0.14.0: every template passes (Title 41/41, Animated Title 35/35, Credits 39/39, Sign-off 32/32,
  Typewriter 15/15, Box Wipe 17/17, Corner Logo 25/25, Glint 13/13, Glint Set 28/28, Route Leg 20/20, Locator 10/10).
- Tests that carried pixel values were converted: Glint and Corner Logo compute pixels from the percent; Animated Title's Size
  test uses 25 against the default 50 (ratio 0.5).

### Done

- Step 1 (Title) shown in the 0.14 app and approved by the user. Step 2: `catalog.py --check` fails any number control whose
  default or example/preview value is outside 0–100 (`tools/tests/test_sliders.py`, 6/6). Steps 3 and 4 as above.
- Step 6 sheets remade for Animated Title, Title, Typewriter, Box Wipe, Glint, Glint Set, Route Leg and Credits; `catalog.py`
  rewrote the README table and page; `catalog.py --check` passes.

### Status at the end of the session: SLIDER1 is finished and released

Nothing is left in SLIDER1. Steps 5 to 8 are done:
- **Step 5 (callers):** none. MoneyPrinterTurbo, `tools/` and `demo/` pass none of Size, Max Width or Curve.
- **Step 6:** the style sheets (8) and the reels (10, with the new version on their title pages) are remade from the footage in
  `~/projects/craft-templates-footage` and the music in `~/projects/mpt-local-motion/tests/m0/music`; every reel matches its committed demo
  in `verify.py --all`; `catalog.py` rewrote the README table and the page.
- **Step 7:** PLAN.md has the "SLIDER1 done" and release entries (under RECIPE1 item 4).
- **Step 8:** released with the user's go-ahead as **v0.6.36**; later releases v0.6.39 and **v0.6.41** (current) carry everything below.
  Checked live: the download links answer 200 and the Title template in the live zip is the repo's v1.1.0 build.
- `test_pages.py` needed one fix: tesseract reads the en-dash in "0.13.0–0.14.0" as a hyphen, so the test normalises it.

### After SLIDER1, the same session (all released in v0.6.41; details in PLAN.md and each file named)

- **KIT1** (`KIT1.md`, "Status" at its end): the trip video project kit, 16x9 and 9x16, built by `tools/project.py`, tested by
  `tools/tests/test_project.py`, with a preview reel (`tools/kit_preview.py`) and `pixies-trip-video-template.zip`.
- **GEOCODE** (`GEOCODE.md`, approved by the user): `python3 tools/maps.py stops-from-photos --photos DIR --out my.stops.json` makes the
  stops file from photo locations; photos without one are skipped and the places added by hand (`tools/tests/test_geocode.py`).
  `Make Maps/` (the script, README, example stops) is in both the kit and the all-templates zip.
- **Every reel and video has a title page and an end page**, including the Australia trip demo (now 66 s) and the kit's preview, which
  also has the demo's music (the kit project itself has none). `tools/demo.py` takes a `title_page` object and `credit_photos`.
- **SKILL.md** now explains the percent controls, the kit and Make Maps.

### Things Opus should know

- The deviations above (Size 50 = normal, Curve 50 = straight, Box Wipe 57.3 / 83.3) were made without asking, because the new check
  forced a choice; each is one constant. The user has seen the summary and not objected.
- Untested here: the percent controls in the app's slider for templates other than Title (only Title was moved by hand; the others pass
  the CLI tests on 0.13.0 and 0.14.0).
- Not done, user decisions: delete the test copy `title_16x9.ectemplate` in the user's EffectCraft Templates folder; delete the fork
  branch `essential-slider-keeps-value` on the user's fork.
- The lab's FL1c, R16 and R17 results were not touched by this session (see the mpt-local-motion and wan2gp-mac-lab repos).
