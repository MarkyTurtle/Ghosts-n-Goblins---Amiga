# Incremental scroller (enhanced build, branch `enhanced/scroll`)

Replaces the original full-screen redraws (`RedrawScreen`, a 288-blit redraw plus a 46 KB CPU copy
every time the view crosses a 16-px tile boundary) with buffers that are updated one tile column or
row at a time.

## Status

| Step | State |
|---|---|
| Test harness: blitter, copper and display emulation on top of the 68000 emulator (`tools/amiga.py`) | done; reproduces the original display exactly (`tools/check_harness.py`: 16 of 16 views equal the level pictures) |
| Background scroller: layout, tile drawing, edge columns / rows, copper list with ring wrap (`src/scroll.s`) | done as a standalone module; equal to the original at every camera position tested (`tools/test_scroll.py`: 560 of 560 frames over all 7 levels, random walks with steps of 1-40 px, two buffers updated alternately) |
| BOBs: `DrawBob` / `RestoreBackground` on separate planes, restore from the pristine buffer, ring-wrap split | to do |
| Scenery drawn into the pristine buffer (`DrawSceneryOnRedraw`), text printed on the playfield | to do |
| Integration into the game: camera / redraw logic, `SetBitplanePtrs`, `SwapScreens`, `ShowBackBuffer`, memory map | to do |
| Full-emulator test (WinUAE / FS-UAE) for timing | to do |

## A finding that changed the design: no corkscrew with interleaved planes

The original screen is line-interleaved: each 180-byte line holds the 5 planes' 36-byte rows one
after another. A corkscrew scroll moves the bitplane pointers one word right every 16 px, so each
plane's fetch runs 2 bytes past the end of its row. That only works if the next bytes are the same
plane's next row. With interleaved planes they are the next plane's row, so the picture would break
after the first 16 px. So the enhanced screen uses **separate bitplanes**: each plane is a continuous
run of 36-byte rows.

Consequences:

* **Tiles:** the tile graphics stay as they are on disk (interleaved). A tile is drawn with 5 blits,
  one per plane (A modulo 8 picks one plane's words).
* **BOBs:** a one-plane mask serves all 5 planes (the same mask pointer for each plane's blit). So the
  masked-graphics plan in `docs/TODO.md` item 3 simplifies: no 2x pre-masked copies are needed, only
  a one-plane mask per frame (+20%, or an on-demand mask cache). Each BOB is drawn with 5 cookie-cut
  blits, as in the 512K build today, minus its 2 mask-building blits.
* **Restore:** 5 blits per BOB (one per plane) from the pristine buffer.

## Layout

```
plane p of a buffer:  base + p*PLANE_SIZE,   PLANE_SIZE = 36*256 + 1040 = 10,256 bytes
world tile column C:  byte 2*(C+1) of a row                (corkscrew: never moves)
world line y (Y up):  ring line (-1-y) & 255, row address = 36 * ring line
pixel (C, y):         base + p*PLANE_SIZE + 2*(C+1) + 36*((-1-y) & 255)
```

* The mapping is the same for every buffer, so a rectangle can be blitted from the pristine buffer to
  the same offset in a display buffer.
* **Corkscrew drift:** scrolling right by 16 px moves the start by 2 bytes, so each plane needs 2
  bytes per world column of slack: 1,040 bytes covers levels up to 512 columns (32 map cells, the
  whole world map width).
* **Aliasing:** (C, line L) shares memory with (C+18, L-1), so a buffer holds at most 18 columns
  (17 are fetched); the 256-line ring holds 16 tile rows (14-15 are visible).
* **Copper:** the playfield list (jumped to at line `$44`, after the 16-line HUD strip) sets the 5
  pointers, modulo 2 (36 - 34 fetched) and the fine scroll in BPLCON1. Where the ring wraps inside the
  display it waits for that line (with the `$FFDF` wait past line 255) and reloads the pointers
  with the start of ring line 0.
* **Camera:** the same values as the original (x = `g_ScrollTileX`*16 + `g_ScrollFineX`, y =
  `g_ScrollTileY`*16 + `g_ScrollFineY`), so the rest of the game's coordinates are unchanged.

## Memory

| | Original | Enhanced |
|---|---:|---:|
| Display buffers | 4 x 46,080 (two shown, two being redrawn) | 2 x 51,280 |
| Pristine background | - | 51,280 |
| Total | 184,320 | 153,840 |
| BOB background save areas | 2 x 12,288 (in the graphics load buffers) | none (restore from the pristine buffer) |

So about 30 KB saved on the screens. That is less than the 36-41 KB first estimated in `docs/TODO.md`,
because of the corkscrew slack and the separate-plane layout. The save areas go as well.

## Cost per frame (from the test)

* **Original:** every 16-px boundary crossing triggers a full redraw: 288 blits of 80 words
  (23,040 words) plus a 46,080-byte CPU copy. It runs in the background and forces logic freezes
  when falling.
* **Enhanced:** a new column is about 15 tiles x 5 planes = 75 blits of 16 words (1,200 words); a
  row 18 x 5 = 90 blits. In the test walks, the frames that needed drawing blitted a median of 1,440
  words. A full draw (level start, big jumps) is 1,275 blits / 20,400 words, about the same as one
  original redraw.
* With a pristine buffer, each edge is drawn once into the pristine buffer and copied into the two
  display buffers with one blit per plane (a column is a 1-word-wide blit with modulo 34). Today the
  prototype draws each buffer's edges from the tiles directly; switching to the pristine copy is
  part of the BOB step.

## Files

* `src/scroll.s`: the scroller module (`ScrFullDraw`, `ScrScrollTo`, `ScrBuildCopper`), assembled at
  `$7A000` for the harness.
* `tools/amiga.py`: harness: 68000 + blitter + copper + display renderer.
* `tools/original.py`: drives the original game's display code in the harness (the reference).
* `tools/check_harness.py`: checks the harness against the level pictures in `render/out/`.
* `tools/test_scroll.py`: the scroller against the original, frame by frame.

```
cd enhanced/tools
python3 check_harness.py
VASM=/path/to/vasmm68k_mot python3 test_scroll.py 80     # steps per level
```

## Next steps

1. **Pristine buffer + BOBs:** port `DrawBob` / `RestoreBackground` to the separate-plane layout
   (clip to the 17 fetched columns; split a BOB that crosses the ring wrap into two blits; one-plane
   mask), draw edges into the pristine buffer and copy them to the display buffers. Test by drawing
   the game's own BOB lists in the harness against the original.
2. **Scenery and text:** `DrawSceneryOnRedraw` draws into the pristine buffer when its column comes
   into view; check every routine that writes to the screen buffers (text such as "TAKE A KEY").
3. **Integration:** a separate source tree derived from `gng_main.s`. Replace the redraw request and
   switch logic in the camera code (`$6EF2`; `tools/verify/camera.py` documents it) with
   `ScrScrollTo` every frame, drop `g_SkipLogic` freezes, `RedrawEntry`, `CameraJump`'s buffer
   rotation and the 4-buffer pointers, and move the buffers in the memory map.
4. **512K and 1MB builds;** then full-emulator tests.
