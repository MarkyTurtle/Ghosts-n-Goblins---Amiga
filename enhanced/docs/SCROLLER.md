# Incremental scroller (enhanced build, branch `enhanced/scroll`)

Replaces the original full-screen redraws (`RedrawScreen`, a 288-blit redraw plus a 46 KB CPU copy
every time the view crosses a 16-px tile boundary) with buffers that are updated one tile column or
row at a time.

## Status

| Step | State |
|---|---|
| Test harness: blitter, copper and display emulation on top of the 68000 emulator (`tools/amiga.py`) | done; reproduces the original display exactly (`tools/check_harness.py`: 16 of 16 views equal the level pictures) |
| Background scroller: layout, tile drawing, edge columns / rows, copper list with ring wrap (`src/scroll.s`) | done; equal to the original at every camera position tested (`tools/test_scroll.py`) |
| Pristine buffer, BOBs, restores, scenery | done; equal to the original's `DrawBobs` / `DrawSceneryOnRedraw` (`tools/test_bobs.py`) |
| Integration into the game (`src/module.s`, `src/patches.s`), a disk image (`tools/build_enh.py`) | done: a playable image, `build/gng_enhanced.adf` |
| Whole game in the emulator against the original (`tools/compare_runs.py`) | done: see *Testing* below |
| Real hardware / WinUAE timing | **not tested yet** - the emulator here has no timing |

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
  display buffers (a column is one 1-word-wide blit, modulo 34).
* A whole display buffer can also be refreshed from the pristine one in a single blit (`CopyAll`,
  589 lines of 40 words): used when the game starts a new screen (`SwapScreens`).

## The enhanced game

### What is built

`tools/build_enh.py` makes everything in `build/`:

* `module.bin` - `src/module.s` (which includes `src/scroll.s`), assembled at `$5C000`: the
  scroller and the game glue, about 2.5 KB. Its storage (records, copper lists, restore lists)
  follows it in memory but is not in the file (EnhInit clears it).
* `main_enh.bin` - the original 512K program with the blocks of `src/patches.s` written over it
  in place. Each block is assembled on its own at its address and checked to fit, so nothing
  else in the program moves (the tables `scroll.s` uses, `CellTiles` and so on, stay where they
  are). The labels come from the original's assembler listing (`orig_syms.i`, generated).
* `boot_enh.bin` - the bootblock with two instructions changed so the load base is always 0:
  the 512K program from track 110 on any machine (the 1MB program is not patched).
* `gng_enhanced.adf` - an extended ADF made by `tools/disk/mkdisk.py`, with the module added
  on track 132 (`--add`, a new option: a file no table lists). The build decodes the image again
  and checks that the bootblock, main program and module read back exactly.

### The patches

| Original | Now |
|---|---|
| `Start` (`$5D32`, loading the copyright screen) | first loads the module (`EnhLoad`, a FileTable-style entry for track 132) and calls `EnhInit` |
| `RedrawScreen` | full draw of the pristine buffer at `g_NewTileX/Y` (+ scenery); sets `g_RedrawDone` |
| `RedrawEntry` (the background redraw the camera asks for at almost every step) | nothing to draw: sets `g_RedrawDone`; still lets the logic run again and idles |
| `CameraJump` | the same fine-scroll rules and origin switch, without rotating buffers |
| `SwapScreens` | adopts `g_NewTileX/Y`; marks both display buffers 'unknown' (they are copied from the pristine buffer when next used - not straight away, because the progress map calls `SwapScreens` with its picture in the same memory) |
| `RestoreBackground` | brings the pristine buffer and the buffer being drawn to the camera (new edges only), then undoes that buffer's BOBs from the pristine one |
| `DrawBobs` | the game's draw list, through `ScrDrawBobs` |
| `SetBitplanePtrs` | `ScrBuildCopper` for the buffer being drawn |
| `ShowBackBuffer` | waits for the copper interrupt, shows that list, swaps the two display buffers |
| `PrintChar`, playfield text (`$B0D6`) | the 8 lines are copied from the ring to a scratch area laid out like the original buffer, the original code prints there, and they are copied back |

The camera logic itself is the original's, so the tile origin (`g_ScrollTileX/Y`, which also
selects the enemy spawn zones) moves exactly as before. (A first version set the camera
straight to its target; it played, but the origin then changed a few pixels earlier or later
than in the original and the enemy zones with it - found by the side-by-side test below.)
What is gone is the work: no 288-blit redraw and 46 KB CPU copy at every origin change, no
redraw racing the camera, and so no logic freezes waiting for one.

### Memory

| Address | |
|---|---|
| `$371E8` | BOB mask (the original's mask area) |
| `$37468` | pristine buffer, 47,120 bytes |
| `$42B78` | display buffer A |
| `$4E288` | display buffer B (ends `$59998`) |
| `$5C000` | the module, then its storage (to about `$5E200`) |
| `$64468` | the HUD strip, as before |

The original's four screen pointers keep their values: only the progress map still uses them, as
raw memory (it unpacks its picture at `$4DC68`..`$5B6A8`, below the module), and the level loader
still stages the enemy graphics at `$37468`..`$544AA`. Both happen while no playfield is shown,
and the game draws the level again (`RedrawScreen`) afterwards. The original's background save
areas (`$311E8`, `$341E8`) and the screen memory from `$59998` to `$5C000` and after the module
are no longer used; nothing has been moved into them yet.

### Testing

`tools/game.py` runs the whole game in the emulator - the boot sequence's Start (without the
copyright wait), then each frame the vertical-blank interrupt and, when it asks for it, the
game's level-1 interrupt, with joystick input - for either build. `tools/compare_runs.py` runs
the original and the enhanced game side by side with the same input and compares the whole
display every frame, and the game state (`$88`-`$E7` of the globals: Arthur, the camera, score,
lives...).

In the emulator a background redraw finishes at once, so the original never waits for one
and the two games stay in step - same logic, same pictures - which makes a direct comparison
possible. Results (random walking, jumping, climbing and throwing; DrawBob's top-clip bug fixed
in the reference):

| Run | Level | Frames in step | Identical displays | Different |
|---|---|---:|---:|---:|
| walking, 3 input seeds (with deaths, the progress map, restarts) | 0 | 3 x 6,000 | 17,989 | 11 |
| walking, started on each level | 1-6 | 6 x 3,000 | 17,980 | 20 |
| teleporting Arthur every 150 frames (camera jumps, vertical scrolling: 29-51 tile rows on levels 1, 2, 4, 5) | 0-6 | 7 x 2,500 | 17,476 | 24 |
| **total** | | **53,500** | **53,445** | **55** |

The two games never went out of step (game state compared every frame), and none of the 55
frames is a playfield difference:

* 2-3 frames per run while a level's graphics load: both builds show the loading data passing
  through screen memory, laid out differently;
* the first frame of the progress map, 2-5 pixels at its top-left: the map's copper list starts
  2 bytes before its picture, and those bytes belong to a different buffer in each build.

Separately, `tools/test_scroll.py` and `tools/test_bobs.py` still pass (280 of 280 and 140 + 401
of 401 frames) with the core as integrated. The deepest stack use in play went from about 120 to
about 320 bytes below `$80000`; the highest level data (level 1's enemy graphics) ends at
`$7F4DE`, so 2.4 KB remain.

What this does not show: anything about timing (the emulator runs each frame's work at once),
the real disk loader (LoadFile is replaced by a copy), sound, and how it looks on a real
display. Those need WinUAE or a real Amiga.

### Trying it

Build (or use the image in the release), then in WinUAE: an A500 with 512K chip RAM (or more:
the enhanced bootblock always loads the 512K program), Kickstart 1.3, and insert
`gng_enhanced.adf` in DF0 (WinUAE reads extended ADFs). Keys as the original: F1 one player,
F2 two, space to pause, Esc to abort.

If something looks wrong, the most useful report is what was on screen and what Arthur was
doing (walking, falling, climbing), and the level.

## Files

* `src/scroll.s`: the scroller core (`ScrFullDraw`, `ScrScrollTo`, `ScrBuildCopper`, `ScrRestore`,
  `ScrDrawBobs`, `CopyAll`); `src/scroll_test.s` assembles it at `$7A000` for the unit tests.
* `src/module.s`: the game module (scroller + glue); `src/patches.s`: the changes to the main
  program.
* `tools/build_enh.py`: builds the module, the patched program, the bootblock and the disk image.
* `tools/game.py`: runs the whole game (either build) in the emulator.
* `tools/compare_runs.py`: the original and the enhanced game side by side.
* `tools/check_game.py`: each frame the enhanced game shows, against the original's display code
  drawing the same state (a second check, independent of the two games staying in step).
* `tools/amiga.py`: harness: 68000 + blitter + copper + display renderer.
* `tools/original.py`: drives the original game's display code in the harness (the reference).
* `tools/check_harness.py`: checks the harness against the level pictures in `render/out/`.
* `tools/test_scroll.py`: the scroller against the original, frame by frame.
* `tools/test_bobs.py`: BOBs, restores and scenery against the original's `DrawBobs` and
  `DrawSceneryOnRedraw`.

```
cd enhanced/tools
VASM=/path/to/vasmm68k_mot python3 build_enh.py         # -> ../build/gng_enhanced.adf
python3 compare_runs.py 6000 1                           # frames, input seed [--level N] [--png DIR]
python3 check_harness.py
VASM=/path/to/vasmm68k_mot python3 test_scroll.py 80     # steps per level
VASM=/path/to/vasmm68k_mot python3 test_bobs.py 40       # frames per level, then the scenery sweeps
```

## Next steps

0. **Fold the scroller into the game source.** Today the enhanced program is the original binary
   with patches written over it, plus the module loaded from track 132. The aim is one source on
   this branch (`gng_main.s`, edited here) that assembles the enhanced program directly:
   * **First make the source relocatable** (on `main`, still byte-identical): about 36
     instructions still give addresses as numbers (`lea $371e8.l`, `move.l #$1a250,COP2LCH`,
     `move.l #$37468,...`, the HUD sprite blocks...) and a few pieces of code are kept as bytes
     (`RedrawEntry`'s `bsr.w`, the bytes before `PrintChar`). Turn them into symbols and real
     instructions. Test: assemble with padding inserted early in the program and run the whole
     game in the emulator (`tools/compare_runs.py` against the original): it must stay in step.
   * **Memory map as symbols**: `GLOBALS` (`$1898C`) is inside the program file's last bytes, and
     the copper lists and sprite data follow at fixed addresses; once the code size changes they
     must be placed after the program (equates computed from an end label), and the bootblock's
     length (`$18A80`) and the disk layout follow (`mkdisk.py` already reads both).
   * **Replace the routines in the source**: `RedrawScreen`, `RedrawEntry`, `CameraJump`,
     `SwapScreens`, `SetBitplanePtrs`, `ShowBackBuffer`, `RestoreBackground`, `DrawBobs` and the
     `PrintChar` playfield path become the module's versions; `include "scroll.s"`; drop the module
     track, its loader stub and the dead code (old `RedrawScreen`, `DrawBob`,
     `DrawSceneryOnRedraw`, the save areas).
   * **Check**: the same side-by-side runs as now (all levels, teleporting), with the harness taking
     its addresses (VblIRQ, Level1Logic, LoadFile...) from the listing instead of constants.
   * Note: `gng_main.s` is generated on `main` (`anno/gen.py`); on this branch it would be edited
     by hand from then on, so later annotation changes on `main` merge as text. Doing the
     relocation step on `main` first keeps those merges small.

1. **Real machine timing.** First WinUAE run (played to the end with the cheat): vertical
   scrolling while falling is clearly better (no freezes); the general frame rate is not
   noticeably different. That is expected: the game moves everything every frame (50 Hz) but
   PlayFrame only sets the camera and draws on odd frames (`btst #0,g_GameFrame+1` at `$6E76`),
   so the display runs at 25 fps in both builds; the original's redraws ran in the background
   between those frames and only showed when they made the logic freeze.
   * **Raster-time build:** set COLOR00 at the start / end of the logic, the camera, the restore,
     the BOB drawing and the scroller (both builds), to see in WinUAE how much of each frame is
     used and what headroom the scroller left.
   * **Draw every frame (50 fps):** drop the odd-frame test so the camera and drawing run every
     frame. Needs the whole frame (logic + restore + BOBs + new edges) to fit in one 20 ms frame;
     if it does not, VblIRQ already skips the next logic run (it sees IPL 1 still running), which
     would slow the game down rather than tear. The raster-time build shows whether it fits; an
     option would keep 25 fps for busy scenes or slower machines.
2. **Use the freed memory** (43 KB of screens, the 24 KB of save areas): the first step towards
   music on 512K machines and the other items in `docs/TODO.md`.
3. **One-plane masks** stored per frame (or the on-demand cache) instead of the 2 mask-building
   blits; fully pre-masked graphics for the 1MB build.
4. **The 1MB build**: the same module on top of `gng_main_1mb.s` (its addresses differ).
5. **Playfield text** goes into the buffer being drawn only, as the original; a BOB passing over
   it restores the background from the pristine buffer, so text that is not printed again every
   frame can lose pieces where a BOB crossed it. None was seen in the tests (the in-game messages
   are printed every frame, or while nothing moves), but it is worth watching for.
