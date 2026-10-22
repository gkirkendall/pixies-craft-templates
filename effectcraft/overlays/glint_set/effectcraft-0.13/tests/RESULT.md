# Glint Set: test result (2026-10-21)

**Pass: 28 of 28 checks.**

Run: `python3 effectcraft/overlays/glint_set/effectcraft-0.13/tests/run.py --effectcraft-cli <path>` (EffectCraft 0.13.0; no
GPU). It renders single transparent frames and writes `tests/out/` (frames, `sheet.png`; not committed).

In each size, at Spread 100 and 60, for each of the six glints (where and when `build/build.py` places them): nothing at its place
one frame before its start, something one frame after, and at its peak its centre within 1 % of the frame of where it belongs
(24 checks). At 1.4 s, nothing is drawn away from the six places (4 checks).

Fixed on the way: at Spread 60 in 9x16, glint 3 is still showing about 100 px from glint 5 when glint 5 starts, so the "nothing
before its start" check saw its neighbour. The check now leaves the other glints' places out.

## Tested versions

Written by `tools/verify.py`; newest last.

| Date | EffectCraft | Result | Checks |
|---|---|---|---|
| 2026-10-21 | 0.13.0 | pass | 28/28 |
| 2026-10-21 | 0.13.0 | pass | 28/28 |
| 2026-10-22 | 0.13.0 | pass | 28/28 |
| 2026-10-22 | 0.14.0 | pass | 28/28 |
