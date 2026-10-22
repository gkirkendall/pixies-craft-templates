# Fill the Frame: test result (2026-10-21)

**Pass: 11 of 11 checks.**

Run: `python3 effectcraft/utility/fill_frame/effectcraft-0.13/tests/run.py --effectcraft-cli <path>` (EffectCraft 0.13.0; no GPU). It draws three
test pictures (a bright gradient with a grid and a red border) and writes `tests/out/` (pictures, frames, clips, `sheet.png`; not
committed).

| Case | Whole picture shown (fitted rectangle vs the picture scaled) | No black bars |
|---|---|---|
| 4:3 into 16x9 | pass (240–1680 px, mean difference 0.6 of 255, red border at all four edges) | pass (0 dark rows or columns) |
| 3:4 into 16x9 | pass (555–1365 px, difference 0.6) | pass |
| 16:9 into 9x16 | pass (656–1264 px high, difference 1.4) | pass |

Also: Darken 0 vs 80 takes the margin from brightness 161 to 55 (pass); Duration 2 renders a 2.00 s clip (pass); a 16:9 clip as
Media into 9x16 shows its frame at 1 s whole (difference 1.1, pass); a 2 s moving clip with Duration 5 renders 5.00 s and shows
clip frames 12, 36, 12, 12 at 0.5, 1.5, 2.5 and 4.5 s: it loops, frame-exact (pass); a numbered picture (IMG_0002.png beside
IMG_0001 and IMG_0003) renders whole (pass).

Checked by eye outside the test: Pixie's 4:3 `.JPG` and `.HEIC` trip photos (Opera House into 9x16, Hilda's Lookout into
16x9) render whole after the `tools/render.py` fixes for upper-case extensions and HEIC.

Fixed on the way: two Media layers (sharp and blurred) cannot work, because a media control swaps only its own layer; a nested
comp's media cannot be exposed as a control. Hence one Media layer and an adjustment layer. The Media layer's anchor is an
expression (half its own size), so a swapped-in picture of another size stays centred.

Loop fix: with EffectCraft's own clip length the loop held the last frame once per pass (frames 12, 36, 11, 10): EffectCraft 0.13
reads the MP4 track header (2.042 s for this 2.000 s clip) without its edit list. The Clip Length control, filled by
`tools/render.py` from ffprobe, makes it exact.

Image-sequence fix (found making the demos): EffectCraft 0.13 imports a numbered photo whose folder holds other numbered photos as
one image sequence (`IMG_[0600-5937].JPG`) and shows colour bars where the sequence has no frame. `tools/render.py` now hands
every media file over under its control's own name in a temp folder.

## Tested versions

Written by `tools/verify.py`; newest last.

| Date | EffectCraft | Result | Checks |
|---|---|---|---|
| 2026-10-21 | 0.13.0 | pass | 10/10 |
| 2026-10-21 | 0.13.0 | pass | 11/11 |
| 2026-10-21 | 0.13.0 | pass | 11/11 |
| 2026-10-21 | 0.13.0 | pass | 11/11 |
| 2026-10-22 | 0.13.0 | pass | 11/11 |
| 2026-10-22 | 0.14.0 | pass | 11/11 |
