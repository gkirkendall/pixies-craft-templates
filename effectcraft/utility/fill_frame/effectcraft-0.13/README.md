# Fill the Frame

Shows a picture or clip of any shape whole, fitted inside the frame, over a blurred, darkened copy of itself that fills the rest of
the frame instead of black bars. Nothing of the picture is cut off: a 4:3 photo in a 16:9 video, a portrait photo in a landscape
video, or a landscape clip in a 9:16 video.

24 fps, as long as the Duration control (5 s by default, up to 60 s). Two sizes: `16x9` (1920×1080) and `9x16` (1080×1920). Both
render as H.264 MP4, since the result fills the frame.

## Controls

| Control | What it does |
|---|---|
| Media | The picture or clip. Any shape; shown whole and centred. |
| Blur | How blurred the copy behind is (60 by default). |
| Darken | How much darker the copy behind is, from 0 (as bright as the picture) to 100 (near black); 30 by default. |
| Duration | Length of the rendered clip in seconds (5 by default, up to 60). A clip shorter than this plays again from the start until then. |
| Clip Length | The clip's exact length, so it loops without a held frame. `tools/render.py` fills it in; leave it out. Filling the template by hand in EffectCraft, type the clip's length here (0 uses EffectCraft's own reading, which is usually one frame long, so each loop holds the last frame once). |

## Using it

```
python3 tools/render.py effectcraft/utility/fill_frame --variant 16x9 --values effectcraft/utility/fill_frame/effectcraft-0.13/examples/portrait.values.json --out filled.mp4
```

Phone photos work as they come: `tools/render.py` gives EffectCraft a lower-case-named copy of an `.JPG` (EffectCraft 0.13 shows
upper-case extensions as missing) and converts `.HEIC` with ffmpeg (7 or later), which EffectCraft cannot read.

No credits are needed.

## How it works

One Media layer is scaled to fit inside the frame. An adjustment layer above it scales what is below about the frame's centre
until it covers the frame (Transform), blurs it (Gaussian Blur, edges repeated) and darkens it (Exposure), and CC Composite puts
the sharp picture back in front. There is only one Media layer because a template's media control swaps only the layer it is
attached to; both sizes are measured from the swapped-in picture's own width and height. The Media layer is time-remapped to
`time % Clip Length`, which loops a short clip.

## Files

- `templates/`: the built templates. Rebuild them with `python3 effectcraft/utility/fill_frame/effectcraft-0.13/build/build.py`.
- `assets/`: the default picture (see `assets/SOURCES.md`).
- `examples/`: a values file that puts a portrait picture into the frame.
- `tests/`: the test script and its result.
