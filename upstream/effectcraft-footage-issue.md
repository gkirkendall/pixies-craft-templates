Found while building a trip-video project in EffectCraft 0.14.0 (macOS, Apple Silicon): photos filled to the frame, which people swap for their own.

**1. File ▸ Replace Footage on a numbered photo imports the whole numbered run as one image sequence, without asking**

Steps:
1. Have a folder of camera photos named in a run (`IMG_2330.JPG`, `IMG_2331.JPG`, … as most cameras name them).
2. Select a still in the Project panel, File ▸ Replace Footage, pick `IMG_2331.JPG`.

Expected: the item becomes that one photo.
Seen: the item becomes an image sequence of every photo in the run (100 photos became one 3-second sequence). The dialog has no Sequence option to turn this off.

File ▸ Import ▸ File… handles the same file correctly: its "JPG Sequence" tick starts off, and dragging from Finder imports single photos.

Suggested fix: give Replace Footage the same Sequence option as Import (off by default), or replace a still with a still unless asked.

**2. Reload Footage keeps the old picture size after the file has changed**

Steps:
1. Import a 1920×1080 photo `Photo_2.jpg` and use it in a comp.
2. Overwrite `Photo_2.jpg` on disk with a photo of another shape (for example 1080×1350).
3. Reload Footage.

Expected: the item takes the new picture's size.
Seen: the item keeps 1920×1080, so anything sized from the item's width and height (a fill-the-frame expression, here) uses the old size, and the new picture comes out cropped. File ▸ Replace Footage with the same file reads the new size correctly.

Suggested fix: re-read the picture's size when footage is reloaded, as Replace Footage does.
