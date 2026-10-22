# Route Leg: MAP1 test result (2026-10-21)

**Pass: 20 of 20 checks** (version 2.0.0: Name Font and Credit Font).

Run: `python3 effectcraft/maps/route_leg/effectcraft-0.13/tests/run.py --effectcraft-cli <path> --clip <16:9 clip>` (EffectCraft 0.13.0; about
90 s once the OpenStreetMap answers are cached; no GPU). It draws the example legs with `tools/maps.py` (16x9 and 9x16), renders
them with test pin and line colours, and writes `tests/out/` (frames, ProRes 4444 clips, `sheet.png`, `inset_over_clip.mp4`; not
committed). The clip used was MPT's `tests/t-sf1/sf1.mp4` (an S1 trip clip, 1024×576).

| Case | Pins to GPS (limit 1 % of the frame) | Line meets both pins | OSM credit |
|---|---|---|---|
| Point Ritchie → Mushroom Rock, 16x9 (1,797 km) | 0.04 %, 0.05 % | yes | none, correctly (Natural Earth only) |
| Point Ritchie → Mushroom Rock, 9x16 | 0.05 %, 0.03 % | yes | none, correctly |
| Sydney Cove → Hilda's Lookout, 16x9 (86 km) | 0.05 %, 0.04 % | yes | "© OpenStreetMap", drawn |
| Port Campbell → Point Ritchie, 16x9 (43 km) | 0.03 %, 0.03 % | yes | "© OpenStreetMap", drawn |
| Point Ritchie → Mushroom Rock, 16x9 corner card | 0.06 %, 0.11 % of the frame | yes | none, correctly |

- The pin check finds each pin by colour in the last frame, maps it back through the leg's Web Mercator view to latitude and
  longitude, and measures the distance to the stop's GPS position.
- Short-leg rule: the 43 km leg is drawn at the default `--min-leg-km 25` and skipped at 50.
- Corner card: transparent outside its frame, solid inside; laid over the clip with ffmpeg → `inset_over_clip.mp4`.
- Names exactly as supplied, by eye on `sheet.png`.

Fixed on the way: names sat on the line where it leaves a pin (now on the side away from the line); long names ran past the card
(now shrink to fit); the public Overpass server cut long answers short (now five tries, 60 s apart); the test's first credit
comparison read only the alpha channel, so it now compares RGB.

Still for the owner: open `templates/route_leg_16x9.ectemplate` in the EffectCraft app and check its named controls.

**Fonts** (`tools/fontcheck.py`): Name Font (both names) and Credit Font each take any font: Montserrat Bold changes the frame, and with that control's own text emptied it changes nothing, so it reaches no other text.

## Tested versions

Written by `tools/verify.py`; newest last.

| Date | EffectCraft | Result | Checks |
|---|---|---|---|
| 2026-10-21 | 0.13.0 | pass | 17/17 |
| 2026-10-21 | 0.13.0 | pass | 18/18 |
| 2026-10-21 | 0.13.0 | pass | 20/20 |
