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
