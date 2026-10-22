# Sign-off

One line, "Thank you for watching" by default (Montserrat Medium), between two hearts in a Heart Colour, centred on Position,
over transparency. The hearts follow the text's width, so any line works; a row too wide shrinks, hearts and all, to fit Max
Width. The text fades and rises in at Start, the hearts pop in 0.25 s later with a small overshoot, and everything fades out over
the last 0.5 s before Duration. With Blink on, the hearts then beat, blinking fully on and off together. A soft shadow keeps it readable over a bright clip. One of the three end-card templates (with
Corner Logo and Credits, stacked over the last clip): by default it sits below the Credits block.

24 fps, as long as the Duration control (5 s by default, up to 60 s). Two sizes: `16x9` (1920×1080) and `9x16` (1080×1920). Both
render as ProRes 4444 with transparency, to lay over footage.

## Controls

| Control | What it does |
|---|---|
| Text | The line (one line). |
| Font | Montserrat Medium by default. |
| Position | Centre of the row, in frame pixels: [960, 790] in 16x9, [540, 1160] in 9x16. |
| Max Width | Widest the row, hearts included, may be, in pixels (86 % of the frame width: 1651 or 929). |
| Text Colour | White by default. |
| Heart Colour | Red `#e5484d` by default. |
| Heart Size | Width of each heart in % of the font size (70 by default). |
| Shadow | Strength of the soft shadow, 0 to 100 (50 by default). |
| Blink | Off by default. On: once popped in, the hearts beat, fully on and off together, on for 60 % of each beat; the text stays steady. |
| Beats per Minute | How fast the hearts beat with Blink on (70 by default). |
| Start | When the text starts to fade and rise in, in seconds (0.6 by default). |
| Duration | Length of the rendered clip in seconds (5 by default); it fades out over its last 0.5 s. |

## Using it

```
python3 tools/render.py effectcraft/titles/sign_off --variant 16x9 --values sign_off.values.json --out sign_off.mov
```

with, for example, `sign_off.values.json`: `{"Text": "See you on the road", "Heart Colour": "#f2b134"}`.

**Font:** Montserrat (SIL Open Font License) is in this repository's `fonts/montserrat/`. Install it on the computer that renders
(on a Mac, open the `.ttf` and click Install) before using the template.

No credits are needed.

## How it works

A text layer and two shape layers drawn as Bézier hearts (`shape.newPath`). One row expression measures the text with
`sourceRectAtTime`, puts each heart 0.45 × the font size beyond its ends, and scales the row down if it would pass Max Width; the
text's middle sits on Position. The hearts' scale pops with an eased-out-back curve; with Blink on, their opacity switches on and off
by the beat from 0.7 s after Start. Fill effects colour text and hearts from their
colour controls, and a Drop Shadow sits under each.

## Files

- `templates/`: the built templates. Rebuild them with `python3 effectcraft/titles/sign_off/effectcraft-0.13/build/build.py`.
- `previews/`: the demo reel and the `demo.json` it is made from.
- `tests/`: the test script and its result.
