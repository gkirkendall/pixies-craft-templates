# Locator

Shows where a place is. It opens on the whole country, zooms in while the place glides to the centre, then a pin pops in and the
place name and a subtitle fade in under it. Use it full frame, or switch on **Corner Inset** to play it in a small card in the
top-right corner over transparency, to lay over a clip.

5 seconds at 24 fps: the whole country until 0.6 s, the zoom from 0.6 to 2.4 s, the pin at 2.3 s, the text at 2.5 s, then a hold.
Two sizes: `16x9` (1920×1080) and `9x16` (1080×1920). Both render as ProRes 4444 with alpha.

## Controls

| Control | What it does |
|---|---|
| Map | The map picture, at three times the frame size so the zoom stays sharp. Draw it with `tools/maps.py locator`. |
| Place Position | The place, in the map picture's pixels. `maps.py` works this out from the coordinates. |
| Zoom | How far to zoom in: 1 is no zoom, and 3 (the default) shows the map picture at its full detail. Above 3 it softens. A place near the map's edge stops short of the centre, so the map always fills the frame. |
| Place Name, Subtitle | The text under the pin, or above it when there is no room below. A name too long for the card shrinks to fit. |
| Pin Colour | The pin's colour. |
| Corner Inset | Off: full frame. On: a bordered card in the top-right corner, with transparency around it. |
| Map Credit | Small text in the map's bottom-right corner. Natural Earth maps need none. |
| Texture | Optional paper or grain picture laid over the map in Multiply mode. White changes nothing. |
| Badge | Optional logo or flag in the card's top-left corner. Any shape fits inside a 180-pixel square. Leave it empty for none. |
| Name Font | Any installed font, for the place name (Inter Bold by default). |
| Subtitle Font | Any installed font (Inter Medium by default). |
| Credit Font | Any installed font, for the map credit (Inter Regular by default). |

## Making the map

```
python3 tools/maps.py fetch
python3 tools/maps.py locator --stops my.stops.json --stop 0 --out maps/ --variant 16x9
python3 tools/render.py effectcraft/maps/locator --variant 16x9 --values maps/locator00_16x9.values.json --out place.mov
```

`--stop` picks the place from the stops file (the first is 0; the format is in `examples/australia.stops.json`). The
map shows the country the place is in: its main land, leaving out islands far offshore. A place on the coast that falls just
offshore of the map's coastline still counts, up to 25 km out.

## Credits you need

None. The maps use Natural Earth data, which is public domain. If you add your own map with OpenStreetMap detail, put
"© OpenStreetMap" in Map Credit and "Map data © OpenStreetMap contributors, https://www.openstreetmap.org/copyright" in the
video's description or credits.

## Files

- `templates/`: the built templates. Rebuild them with `python3 effectcraft/maps/locator/effectcraft-0.13/build/build.py`.
- `assets/`: the default maps and the blank Texture and Badge pictures (`assets/SOURCES.md`).
- `examples/`: a values file for the corner card (`inset_badge.values.json`; add `"Badge": "your_logo.png"`).
