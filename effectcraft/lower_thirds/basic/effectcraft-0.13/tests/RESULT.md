# Basic Lower Third: test result (2026-10-21)

**Pass: 14 of 14 checks** (version 2.0.0: Title Font and Subtitle Font).

Run: `python3 effectcraft/lower_thirds/basic/effectcraft-0.13/tests/run.py --effectcraft-cli <path>` (EffectCraft 0.13.0; no GPU). It renders the
default text and the long example (`examples/long.values.json`) in 16x9 and 9x16 as ProRes 4444 and writes `tests/out/` (clips,
frames, `sheet.png`; not committed).

| Case | Empty at frames 0 and 95 | In place by frame 12, steady to 84 | Bar holds the text, nothing outside it |
|---|---|---|---|
| default 16x9 | pass | pass | pass (bar 150–1140 px, text 211–1083) |
| long 16x9 | pass | pass | pass (bar 150–1524, text 212–1466) |
| default 9x16 | pass | pass | pass (bar 60–1040 of 1080) |
| long 9x16 | pass | pass | pass (title shrunk to fit; subtitle keeps its size) |

Names exactly as supplied, by eye on `sheet.png`.

Fixed on the way: a long title ran off the 9x16 frame (each line now shrinks only if it alone is too wide); the long 16x9 bar
showed at frame 0 (it now starts a full frame width to the left).

**Fonts** (`tools/fontcheck.py`): Title Font and Subtitle Font each take any font: Montserrat Bold changes the frame, and with that control's own text emptied it changes nothing, so it reaches no other text.

## Tested versions

Written by `tools/verify.py`; newest last.

| Date | EffectCraft | Result | Checks |
|---|---|---|---|
| 2026-10-21 | 0.13.0 | pass | 12/12 |
| 2026-10-21 | 0.13.0 | pass | 14/14 |
| 2026-10-22 | 0.13.0 | pass | 14/14 |
| 2026-10-22 | 0.14.0 | pass | 14/14 |
| 2026-10-22 | 0.13.0 | pass | 14/14 |
