# Typewriter

Text that types itself letter by letter from Start, at Speed letters a second, with a cursor after it: a bar, an underscore or
none. The cursor is solid while typing and blinks while it waits (before Start and once the line is typed). With Erase on, the
text deletes itself again, at twice the speed, finishing 0.3 s before Duration. The finished line is centred on Position and
types out from its left edge, so nothing shifts as it grows; a line too wide shrinks to Max Width. Over transparency.

24 fps, as long as the Duration control (5 s by default, up to 60 s). Two sizes: `16x9` (1920×1080) and `9x16` (1080×1920). Both
render as ProRes 4444 with transparency, to lay over footage.

## Controls

| Control | What it does |
|---|---|
| Text | The line to type. |
| Font | Inter SemiBold by default. |
| Speed | Letters typed a second (14 by default). |
| Cursor | Bar (default), Underscore or None. |
| Erase | Off by default. On: the text deletes itself again before Duration. |
| Position | Centre of the finished line, in frame pixels ([960, 540] in 16x9, [540, 960] in 9x16). |
| Max Width | Widest the line may be, in % of the frame width (default 86: 1651 px on 1920 wide, 929 on 1080). |
| Colour | The text's colour (white by default). |
| Shadow | Strength of the soft shadow under the text, 0 to 100 (40 by default). |
| Start | When the first letter is typed, in seconds (0.5 by default). |
| Duration | Length of the rendered clip in seconds (5 by default). |

Give it time to type: the line takes its length ÷ Speed seconds (29 letters at 14 a second is about 2 s).

## Using it

```
python3 tools/render.py effectcraft/titles/typewriter --variant 16x9 --values effectcraft/titles/typewriter/effectcraft-0.13/examples/travel.values.json --out typed.mov
```

In a values file Cursor is the item's name (`"Cursor": "Underscore"`); `tools/render.py` refuses any other.

**Fonts:** Inter ships with EffectCraft (and is in this repository's `fonts/inter/`, SIL Open Font License). No credits are needed.

## How it works

A hidden "Full" text layer holds the Text and Font controls. The visible "Typed" layer's text expression shows the first
n letters of it in its style (`style.setText`), n growing with time at Speed (and shrinking at twice Speed with Erase), plus the
cursor character while it is solid or in the "on" half of each second. Both layers are left-justified, and Typed's position and
scale come from Full's `sourceRectAtTime`, so the typed text starts where the finished line will and the finished line is
centred. A Fill effect colours it from Colour, and a Drop Shadow sits under it.

## Files

- `templates/`: the built templates. Rebuild them with `python3 effectcraft/titles/typewriter/effectcraft-0.13/build/build.py`.
- `examples/`: a values file to start from.
- `previews/`: the demo reel and the `demo.json` it is made from.
- `tests/`: the test script and its result.
