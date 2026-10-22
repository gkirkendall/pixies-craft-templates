Found while building a trip-video project in EffectCraft 0.14.0 (macOS, Apple Silicon): photos filled to the frame, which people swap for their own.

Steps:
1. Have a folder of camera photos named in a run (`IMG_2330.JPG`, `IMG_2331.JPG`, … as most cameras name them).
2. Select a still in the Project panel, File ▸ Replace Footage, pick `IMG_2331.JPG`.

Expected: the item becomes that one photo.
Seen: the item becomes an image sequence of every photo in the run (100 photos became one 3-second sequence). The dialog has no Sequence option to turn this off.

File ▸ Import ▸ File… handles the same file correctly: its "JPG Sequence" tick starts off, and dragging from Finder imports single photos.

Suggested fix: give Replace Footage the same Sequence option as Import (off by default), or replace a still with a still unless asked.
