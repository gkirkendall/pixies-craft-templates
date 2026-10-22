# Box Wipe Lower Third

A thin line sweeps in along the top, a see-through colour box wipes open from the left, and the title fades in in a script font
with an underline, a smaller subtitle under it. Before Duration the text fades, the box wipes shut and the line slides away. The
box fits the longer line; a title wider than Max Width wraps onto two lines (at the space nearest its middle), and a line still
too wide shrinks to fit. With no subtitle the box closes up. Over transparency.

24 fps, as long as the Duration control (5 s by default, up to 60 s): in by 0.85 s, out over the last 0.7 s. Two sizes: `16x9`
(1920×1080) and `9x16` (1080×1920). Both render as ProRes 4444 with transparency, to lay over footage.

## Controls

| Control | What it does |
|---|---|
| Title | The first line. Wraps onto two lines when wider than Max Width. |
| Subtitle | The smaller second line; leave it empty for none. |
| Title Font | Any installed font (Caveat Brush by default). |
| Subtitle Font | Any installed font (Caveat Brush by default). |
| Position | The box's bottom-left corner, in frame pixels ([110, 960] in 16x9, [70, 1640] in 9x16). |
| Max Width | Widest the box may be, in pixels (1100 or 900). |
| Box Colour | Deep blue (`#123047`) by default. |
| Box Opacity | How solid the box is, 0 to 100 (70 by default). |
| Line Colour | The line along the top and the underline (`#ffd166`). |
| Text Colour | White by default. |
| Duration | Length of the rendered clip in seconds (5 by default). |

## Using it

```
python3 tools/render.py effectcraft/lower_thirds/box_wipe --variant 16x9 --values effectcraft/lower_thirds/box_wipe/effectcraft-0.13/examples/stops.values.json --out stop.mov
```

One values file per stop: copy `examples/stops.values.json` and change the names. `examples/long.values.json` shows a title that
wraps.

**Fonts:** Caveat Brush is in this repository's `fonts/caveat_brush/` (SIL Open Font License); install it, or pick any font you
have. No credits are needed.

## How it works

A hidden "Title Text" layer holds the Title and Title Font controls on one line. The visible "Title" layer's text expression
copies it in its style (`style.setText`), breaking it at the space nearest the middle when it is wider than Max Width. One
layout, shared by every layer's expressions, measures Title and Subtitle with `sourceRectAtTime`, shrinks either if it is still
too wide, and places the box above and to the right of Position, its padding and gaps in proportion to the title's font size.
The box, line and underline are rectangles whose size and position come from that layout and the eased timing; the underline
sits under the title's glyph box, so no descender crosses it. Fill effects colour the text from Text Colour.

## Files

- `templates/`: the built templates. Rebuild them with `python3 effectcraft/lower_thirds/box_wipe/effectcraft-0.13/build/build.py`.
- `examples/`: values files for a stop and for a long title.
- `previews/`: the demo reel and the `demo.json` it is made from.
- `tests/`: the test script and its result.
