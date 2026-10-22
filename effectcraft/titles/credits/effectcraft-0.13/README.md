# Credits

A title in quotes, in tall condensed capitals (League Gothic), with up to five credit lines under it (Montserrat Medium), centred,
over transparency. Empty credit lines close up and the block stays centred on Position. A title too long for one line breaks
onto two at the space nearest its middle; any line still too wide shrinks to fit Max Width. It fades and rises in at Start and
fades out over the last 0.5 s before Duration, with a soft shadow so it reads over a bright clip. One of the three end-card
templates (with Corner Logo and Sign-off, stacked over the last clip).

24 fps, as long as the Duration control (6 s by default, up to 60 s). Two sizes: `16x9` (1920×1080) and `9x16` (1080×1920). Both
render as ProRes 4444 with transparency, to lay over footage.

## Controls

| Control | What it does |
|---|---|
| Title | The title, shown in capitals between curly quotes whatever case it is typed in. Leave it empty for none: no quotes, and the lines move up (for a title made with the Title or Animated Title template instead). |
| Line 1 to Line 5 | The credit lines; leave any empty and the others close up. |
| Title Font | League Gothic Regular by default. |
| Line Font | Montserrat Medium by default; all five lines follow it. |
| Position | Centre of the whole block, in frame pixels: [960, 470] in 16x9, [540, 800] in 9x16 (above the middle, leaving room for a Sign-off below). |
| Max Width | Widest any line may be, in % of the frame width (default 86: 1651 px on 1920 wide, 929 on 1080). |
| Colour | The text's colour (white by default). |
| Shadow | Strength of the soft shadow under the text, 0 to 100 (50 by default). |
| Start | When it starts to fade and rise in, in seconds (0.3 by default; fully in 0.6 s later). |
| Duration | Length of the rendered clip in seconds (6 by default); it fades out over its last 0.5 s. |

## Using it

```
python3 tools/render.py effectcraft/titles/credits --variant 16x9 --values effectcraft/titles/credits/effectcraft-0.13/examples/australia.values.json --out credits.mov
```

**Fonts:** League Gothic and Montserrat (SIL Open Font License) are in this repository's `fonts/league_gothic/` and
`fonts/montserrat/`. Install them on the computer that renders (on a Mac, open the `.ttf` and click Install) before using the
template.

No credits are needed for the template itself; credit your own music and map data on its lines.

## How it works

Six text layers (Title, Line 1 to Line 5). The title's text expression makes it capitals between quotes and breaks a long one by
its length (League Gothic capitals average about 0.37 of the font size). Every layer's position and scale come from the same
layout expression: each layer's `sourceRectAtTime` gives its size and whether it is empty; each non-empty line goes 1.5 × its font
size below the last (the first sits under the title's real bottom edge); the whole block is centred on Position; each layer
shrinks on its own to Max Width. A Fill effect colours the text from Colour, and a Drop Shadow sits under it. Line 2 to Line 5 take
their font from Line 1. An empty title's expression returns nothing (no quotes), and the layout starts at the first line.

## Files

- `templates/`: the built templates. Rebuild them with `python3 effectcraft/titles/credits/effectcraft-0.13/build/build.py`.
- `examples/`: the values for the Australia trip's end card.
- `previews/`: the demo reel and the `demo.json` it is made from.
- `tests/`: the test script and its result.
