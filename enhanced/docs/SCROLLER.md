# Incremental scroller (enhanced build, branch `enhanced/scroll`)

Replaces the original full-screen redraws (`RedrawScreen`, a 288-blit redraw plus a 46 KB CPU copy
every time the view crosses a 16-px tile boundary) with buffers that are updated one tile column or
row at a time.

## Status

| Step | State |
|---|---|
| Test harness: blitter, copper and display emulation on top of the 68000 emulator (`tools/amiga.py`) | done; reproduces the original display exactly (`tools/check_harness.py`: 16 of 16 views equal the level pictures) |
| Background scroller: layout, tile drawing, edge columns / rows, copper list with ring wrap (`src/scroll.s`) | done as a standalone module; equal to the original at every camera position tested (`tools/test_scroll.py`: 560 of 560 frames over all 7 levels, random walks with steps of 1-40 px, two buffers updated alternately) |
| Pristine buffer: tiles drawn once, display buffers copy new edges from it | done |
| BOBs: `ScrDrawBob` / `ScrRestore` with the corkscrew addressing, restore from the pristine buffer, ring-wrap split | done; equal to the original's `DrawBobs` (`tools/test_bobs.py`: 280 of 280 frames with 3-10 BOBs each, moving camera, BOBs off every edge and across the ring wrap) |
| Scenery drawn into the pristine buffer (`ScrDrawScenery`) | done; 401 of 401 frames of sweeps over the gravestones of levels 0 and 2 |
| Text printed on the playfield (`PrintChar` into the screen buffer) | to do, at integration |
| Integration into the game: camera / redraw logic, `SetBitplanePtrs`, `SwapScreens`, `ShowBackBuffer`, memory map | to do |
| Full-emulator test (WinUAE / FS-UAE) for timing | to do |

## The corkscrew works with the interleaved layout

The screen stays line-interleaved, as in the original: each 180-byte line holds the 5 planes'
36-byte rows. (The first version of the prototype used separate bitplanes, on the mistaken view
that a corkscrew can't work interleaved; it can, and the interleaved version passes the same test.)

Scrolling right moves the bitplane pointers on one word, so each plane's 34-byte fetch runs 2 bytes
further into memory. Past the end of its own row it reads the start of the next plane's row (plane 4:
the next line's plane 0). Those bytes belonged to that plane's leftmost column, which has itself
just scrolled off the left, so they are free: that is exactly where the new right-hand column is
drawn. In memory terms every plane row is one link in a single chain, and the address of a pixel is
linear in its column, so nothing ever has to move.

Advantages over separate planes:

* **A tile is one blit** (16 lines x 5 planes, D modulo 34), as in the original `RedrawScreen`.
* **A BOB restore is one blit,** and BOBs can use either mask scheme: one-plane masks with 5
  cookie-cut blits (as the 512K build, minus its 2 mask-building blits; +20% memory), or fully
  pre-masked graphics with one blit (as the 1MB build; +100%).
* **Less memory:** the corkscrew slack is needed once per buffer, not once per plane.

## BOBs and the pristine buffer

Per frame, for the display buffer about to be drawn:

1. `ScrScrollTo` on the **pristine** buffer: new edges from the tiles, then the shootable scenery
   again (drawing a gravestone over itself changes nothing, so every one in view is simply drawn
   again; only on level 0 left of tile column `$70` and level 2 left of `$40`, as the original).
2. `ScrScrollTo` on the **display** buffer: its new edges are copied from the pristine buffer (one
   blit per tile).
3. `ScrRestore`: every rectangle its BOBs covered last time is copied back from the pristine buffer
   (one blit each). Because every buffer uses the same addresses, this always writes the current
   background, even where the view has moved since.
4. `ScrDrawBobs`: the game's own draw list, each BOB drawn as `DrawBob` does (mask = OR of the
   planes in 2 blits, then 5 cookie-cut blits), clipped to the 17 fetched columns and the visible
   lines, in two parts when it crosses the ring wrap; each part adds a restore entry. No
   background save and no `$3000` budget.

Every buffer keeps exactly the window the camera needs (17 columns, the visible rows), so the
pristine and display buffers always agree on which column a shared address holds.

**A bug in the original found by these tests:** `DrawBob` skips twice the graphics lines it should
when a BOB is clipped at the top of the buffer (`$BAF4`: the count is multiplied by 2 x the
words per line, then by 10). The part still on screen shows the wrong lines. The same code is right
in the 1MB build, whose masked graphics have twice the bytes a line; the 512K build kept it.
`DrawSceneryOnRedraw` has it too (`$C2EA`). The enhanced code skips the right number, and the test
compares against the original with that one instruction corrected. Now in the main README's bug
list and `tools/verify/checks.py`.

## Layout

```
buffer:               180 * 256 + 1040 = 47,120 bytes
world tile column C:  byte 2*(C+1) of a plane row          (corkscrew: never moves)
world line y (Y up):  ring line (-1-y) & 255, line address = 180 * ring line
plane p:              + 36*p
pixel (C, y, p):      base + 2*(C+1) + 180*((-1-y) & 255) + 36*p
```

* The mapping is the same for every buffer, so a rectangle can be blitted from the pristine buffer to
  the same offset in a display buffer.
* **Corkscrew drift:** scrolling right by 16 px moves the start by 2 bytes, so the buffer needs 2
  bytes per world column of slack: 1,040 bytes covers levels up to 512 columns (32 map cells, the
  whole world map width).
* **Aliasing:** (C, plane p) shares memory with (C+18, plane p-1) of the same line, so a buffer
  holds at most 18 columns (17 are fetched); the 256-line ring holds 16 tile rows (14-15 visible).
* **Copper:** the playfield list (jumped to at line `$44`, after the 16-line HUD strip) sets the 5
  pointers (36 bytes apart), modulo 146 (180 - 34 fetched) and the fine scroll in BPLCON1. Where the ring wraps inside the
  display it waits for that line (with the `$FFDF` wait past line 255) and reloads the pointers
  with the start of ring line 0.
* **Camera:** the same values as the original (x = `g_ScrollTileX`*16 + `g_ScrollFineX`, y =
  `g_ScrollTileY`*16 + `g_ScrollFineY`), so the rest of the game's coordinates are unchanged.

## Memory

| | Original | Enhanced |
|---|---:|---:|
| Display buffers | 4 x 46,080 (two shown, two being redrawn) | 2 x 47,120 |
| Pristine background | - | 47,120 |
| Total | 184,320 | 141,360 |
| BOB background save areas | 2 x 12,288 (in the graphics load buffers) | none (restore from the pristine buffer) |

So about 43 KB saved on the screens, and the save areas go as well.

## Cost per frame (from the test)

* **Original:** every 16-px boundary crossing triggers a full redraw: 288 blits of 80 words
  (23,040 words) plus a 46,080-byte CPU copy. It runs in the background and forces logic freezes
  when falling.
* **Enhanced:** a new column is about 15 tile blits of 80 words (1,200 words); a row 18 blits. In the
  test walks, the frames that needed drawing blitted a median of 1,440 words. A full draw (level
  start, big jumps) is 255 blits / 20,400 words, about the same as one original redraw.
* With a pristine buffer, each edge is drawn once into the pristine buffer and copied into the two
  display buffers (a column is one 1-word-wide blit, modulo 34). Today the
  prototype draws each buffer's edges from the tiles directly; switching to the pristine copy is
  part of the BOB step.

## Files

* `src/scroll.s`: the scroller module (`ScrFullDraw`, `ScrScrollTo`, `ScrBuildCopper`), assembled at
  `$7A000` for the harness.
* `tools/amiga.py`: harness: 68000 + blitter + copper + display renderer.
* `tools/original.py`: drives the original game's display code in the harness (the reference).
* `tools/check_harness.py`: checks the harness against the level pictures in `render/out/`.
* `tools/test_scroll.py`: the scroller against the original, frame by frame.
* `tools/test_bobs.py`: BOBs, restores and scenery against the original's `DrawBobs` and
  `DrawSceneryOnRedraw`.

```
cd enhanced/tools
python3 check_harness.py
VASM=/path/to/vasmm68k_mot python3 test_scroll.py 80     # steps per level
VASM=/path/to/vasmm68k_mot python3 test_bobs.py 40       # frames per level, then the scenery sweeps
```

## Next steps

1. **Integration:** a separate source tree derived from `gng_main.s` (for example
   `enhanced/src/gng_enh.s`):
   * replace the redraw request / switch logic of the camera code (`$6EF2`; `tools/verify/camera.py`
     documents it) with `ScrScrollTo` every drawn frame, and drop `RedrawEntry`, `g_SkipLogic`
     freezes, `CameraJump`'s buffer rotation and the 4-buffer pointers;
   * `RestoreBackground` / `DrawBobs` / `DrawBob` become `ScrRestore` / `ScrDrawBobs`;
     `SetBitplanePtrs` becomes `ScrBuildCopper`; `ShowBackBuffer` swaps the two display buffers;
   * `PrintChar` on the playfield: write through the buffer's line address with the ring wrap,
     into both display buffers and the pristine one (or as a BOB);
   * the memory map: three buffers of 47,120 bytes where the four were, a staging area for the
     level-start load, the HUD strip and copper lists;
   * level start, checkpoint and restart: `ScrFullDraw` on all three buffers.
2. **One-plane masks** stored per frame (or the on-demand cache) instead of the 2 mask-building
   blits; fully pre-masked graphics for the 1MB build.
3. **Real machine timing** in WinUAE / FS-UAE: the integrated build on a disk image from
   `tools/disk/mkdisk.py`.
