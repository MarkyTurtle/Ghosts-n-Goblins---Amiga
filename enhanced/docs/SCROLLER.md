# Incremental scroller (enhanced build, branch `enhanced/scroll`)

> **The development log.** This file records how the enhanced game was made, step by step, with
> the measurements and tests of each step; the earlier sections describe builds that came before
> the one program (the patched original programs with a scroller module) and figures from then.
> For the game as it is now see `FEATURES.md`, `MEMORY.md`, `DISK.md` and `FORMATS.md`.

Replaces the original full-screen redraws (`RedrawScreen`, a 288-blit redraw plus a 46 KB CPU copy
every time the view crosses a 16-px tile boundary) with buffers that are updated one tile column or
row at a time.

## Status

| Step | State |
|---|---|
| Test harness: blitter, copper and display emulation on top of the 68000 emulator (`tools/amiga.py`) | done; reproduces the original display exactly (`tools/check_harness.py`: 16 of 16 views equal the level pictures) |
| Background scroller: layout, tile drawing, edge columns / rows, copper list with ring wrap (`src/scroll.s`) | done; equal to the original at every camera position tested (`tools/test_scroll.py`) |
| Pristine buffer, BOBs, restores, scenery | done; equal to the original's `DrawBobs` / `DrawSceneryOnRedraw` (`tools/test_bobs.py`) |
| Integration into the game (`src/module.s`, `src/patches.s`), a disk image (`tools/build_enh.py`) | done for both programs, 512K and 1MB: `build/gng_enhanced.adf` |
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

`tools/build_enh.py` builds both programs - the 512K and the 1MB one - from the same module and
patch sources, into `build/512k/` and `build/1mb/`:

* `module.bin` - `src/module.s` (which includes `src/scroll.s`): the scroller and the game glue,
  about 2.5 KB, at `$5C000` (512K) or `$24400` (1MB, `BUILD_1MB`). Its storage (records, copper
  lists, restore lists) follows it in memory but is not in the file (EnhInit clears it).
* `main.bin` - the original program with the blocks of `src/patches.s` written over it in place
  (and, for the 512K program, `src/fps50_patches.s`: it draws every frame, see *Frame rate*).
  Each block is assembled on its own at its address and checked to fit, so nothing else in the
  program moves (the tables `scroll.s` uses, `CellTiles` and so on, stay where they are). The
  labels come from the original's assembler listing (`orig_syms.i`, generated).

and two disk images, made by `tools/disk/mkdisk.py` with the modules added on tracks 132 (512K)
and 133 (1MB) (`--add`: files no table lists); the build decodes each image again and checks
that the bootblock and every file it changed read back exactly:

* `gng_enhanced.adf` - both enhanced programs and the bootblock, which chooses as on the
  original disk: the 1MB program when it finds more than 512K (1MB of chip RAM, or memory above
  512K), otherwise the 512K one. The bootblock is the original plus a memory survey (see *The
  machine description*).
* `gng_enhanced_512k.adf` - the 512K program only, with the bootblock's two memory tests
  changed so the load base is always 0 (to try the 512K program on a bigger machine).

`--fps25` makes `gng_enhanced_512k_25hz.adf` instead: the 512K program at the original's fixed
25 fps (into `build/512k_25hz/`), to compare.

### Frame rate

The original 512K program moves everything every frame but sets the camera and draws only on
odd frames (`btst #0,g_GameFrame+1` / `beq` in `PlayFrame`, `$6E76`): a fixed 25 fps. The 1MB
program has no such test. Without the original's background redraws the 512K program can draw
every frame too, so the enhanced build removes the test (`src/fps50_patches.s`, five `nop`s).
When a frame's work does not fit in 20 ms, `VblIRQ` sees the logic still running and skips the
next run, so the game drops to 25 fps for those frames rather than tearing.

On a 512K A500 in WinUAE (played to the big men of level 2) it runs at 50 fps most of the time
and is much smoother than the locked 25 fps; it dropped to 25 fps when the screen was busy (on
level 1: a flower, projectiles and zombies at once).

### The 1MB build

The 1MB program is the 512K one with more kept in memory (graphics, the progress map, music).
Two differences matter here:

* **It is position independent:** it runs wherever the bootblock loads it (`$80000` with 1MB of
  chip RAM) and adds `g_BaseAddr` to every program address. The patches only use pc-relative
  branches into the program; the module sits at a fixed chip-RAM address (`$24400`, in the old
  screen area: its three buffers are at `$80`-`$22AB0`, the progress map's picture can reach
  `$242C0`, the HUD strip starts at `$2D080`) and adds `g_BaseAddr` where it reads the program's
  tables (`CellTiles`, `ItemBoxSizes`, `SmallBobSizes`) or jumps back into `PrintChar`.
* **Its BOB graphics carry their masks** (`BuildMaskedGfx`: every plane line followed by its mask
  line), so a BOB is one blit - 5 x height blitter lines, A = mask, B = graphics, C/D = screen -
  instead of 2 mask blits and 5 plane blits. `ScrDrawBob` does the same in the 1MB build, through
  the ring and corkscrew addressing, split at the ring wrap.
* It also **draws every frame** (50 fps): the 1MB `PlayFrame` has no odd-frame test (the 512K
  build's `btst #0,g_GameFrame+1` at `$6E76`), so its camera moves, and its redraws are asked
  for, twice as often.

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
possible. Input is random walking, jumping, climbing and throwing; `--teleport` also puts
Arthur somewhere else in the level every 100-150 frames, so the camera jumps and scrolls
vertically. DrawBob's top-clip bug is fixed in the 512K reference.

Results with the current code (both builds):

| Build | Runs | Frames in step | Identical displays | Different |
|---|---|---:|---:|---:|
| 1MB | every level (0-6) with teleporting, level 2 twice; 11-63 camera tile rows on levels 1, 2, 4, 5 | 17,000 | 16,996 | 4 |
| 512K | walking on level 0; levels 1, 2, 4, 5 with teleporting | 12,500 | 12,485 | 15 |

The two games never went out of step (game state compared every frame), and none of the frames
that differ is a playfield difference:

* (512K only) 2-3 frames per run while a level's graphics load: both builds show the loading
  data passing through screen memory, laid out differently. The 1MB program keeps its graphics
  in memory and has none of these;
* the first frame of the progress map, 1-10 pixels at its top-left: the map's copper list starts
  2 bytes before its picture, and those bytes belong to a different buffer in each build.

**A bug these runs found** (fixed, both builds): the gravestones drawn into the pristine buffer
were clipped to the lines visible at the time; when the view then moved down within the same
tile rows (on level 2, teleporting), the lines cut off came into view as background. They are now
clipped to the tile rows the pristine buffer holds. The first 512K image you tried has it too: on level 2 it could show as part of a gravestone missing while the screen scrolls down.

Earlier, before that fix, the 512K build had run 53,500 frames in step in the same way (all
levels, walking and teleporting), with only the loading and map frames above differing.

Separately, `tools/test_scroll.py` and `tools/test_bobs.py` still pass (280 of 280 and 140 + 401
of 401 frames) with the core as integrated. The deepest stack use in play went from about 120 to
about 320 bytes below `$80000`; the highest level data (level 1's enemy graphics) ends at
`$7F4DE`, so 2.4 KB remain.

What this does not show: anything about timing (the emulator runs each frame's work at once),
the real disk loader (LoadFile is replaced by a copy), sound, and how it looks on a real
display. Those need WinUAE or a real Amiga.

### Playfield text

`PrintChar` on the playfield does not draw: the character goes into the frame's text queue
(`TextQ`) and is drawn once - by `TextReplay` after the restore of the buffer being drawn (in
play; the restore may cut through text, so it has always been drawn again there, and drawing it
when printed as well was wasted: the game prints its in-play messages every frame, before the
restore), or by `TextFlush` just before the buffer is shown (text printed after that, and the
screens with no restore: title, high scores, name entry). A character is drawn at once only
when the queue (64) is full. Each character drawn in play gets a restore entry, so text the game
stops printing goes away two frames later, like a BOB.

Drawing (`PrFast`) goes straight into the ring (no copy of the 8 lines in and out of a scratch
area, no update check of both buffers per character), from a glyph cache in the scroller's
storage: 29 slots (character code mod 29) of a tag (character, colours) and 8 lines of a mask
byte and the 5 plane bytes, worked out as the original `PrintBody` does. NameEntry's background
redraw at every cursor move (`EnhRedrawSame`) keeps the pristine buffer when it already shows the
camera (it was 255 tile blits a move).

**Lines of text as one BOB (`DrawStrip`).** In play, a run of 4-28 queued characters on one line,
one after the other in one set of colours (the game's messages), is drawn as a single pre-masked
BOB: its glyphs are put together once into a strip in the 1MB BOB format (`TEXT_STRIP`, the
2,392 bytes of chip RAM between the end of the progress map's picture, `SCREEN_2 + $DA40`, and
the scroller's storage), and each frame it is one `ScrDrawBob` call - one blit, one restore
entry - instead of 26 characters drawn by the CPU. The strip is made again only when the line
changes (length, colours, characters) or a level loads.

**End-of-level timings.** The original's drawing slowed right down while it printed 'TAKE A KEY
FOR COMING IN !' and 'BONUS', which kept them on screen far longer than their frame counts; at
50 fps they flashed by. The one program shows the key message for 250 frames (5 s; the original
counts 36) and the bonus for 150 (3 s; the original counts 64). Everything else about the end of
a level is unchanged.

CPU work (instruction bytes executed, emulator): the key message ('TAKE A KEY FOR COMING IN !')
adds about 18 K a frame instead of 203 K (play alone is 13 K) drawn character by character,
and next to nothing as a strip; drawing the title screen 0.57 M
instead of 1.74 M; a name-entry cursor move about 130 K instead of 365 K plus the full redraw.
The pictures are the same as the original's (title, high scores, the key message for 60 frames,
201 name-entry frames with moves and letters, and the usual runs on every stage).

### The machine description (bootblock)

The enhanced bootblock (`src/boot_patches.s`, applied to `gng_boot.s` by the build like the
program patches) surveys the memory before taking the machine over: Kickstart calls a bootblock
with `a6` = ExecBase, so `MemDetect` walks exec's memory list and leaves a 32-byte description at
`$7FB00`:

| Offset | |
|---|---|
| +0 | `'GNGM'` |
| +4 | version (1) |
| +5 | `VBlankFrequency` (50 PAL / 60 NTSC) |
| +6 | `AttnFlags` (CPU / FPU bits) |
| +8 | chip RAM: `mh_Lower`, `mh_Upper` (512K: upper `$80000`; 1MB: `$100000`) |
| +16 | slow RAM (`$C00000`-`$DBFFFF`): lower, upper (0 if none) |
| +24 | fast RAM (any other; the last region listed): lower, upper |

It takes the 92 free bytes after the loading-screen palette (only its 16 colours are used) and
one call in place of the bootblock's first instruction (`MemDetect` does that instruction
itself). How the bootblock chooses the 512K or 1MB program is unchanged. `$7FB00` is above the
loader's track buffer and below the loader copy and its stack, and above the highest game data
(level 1's graphics end at `$7F4DE`); the module copies the block at start-up (`EnhInit`, into
`EnhMachine`) since nothing guarantees the address later.

The title screen shows it, in the free line under the credits, centred - for example
`CHIP 512K SLOW 512K FAST 0K` (chip = its upper end; slow and fast = upper end minus the 64K
boundary below the region's start). Without a description (the original bootblock) nothing
is printed. `tools/test_bootinfo.py` runs the bootblock's own code on fake exec memory lists for
six machines (A500 512K, + 512K slow, A500+ 1MB, 1MB + slow NTSC, A1200 2MB + 4MB fast, 512K +
1.5MB slow + 2MB fast) and checks the description; `GameRun(..., machine=...)` puts it in memory
for the whole-game runs.

### Timing build

`build_enh.py --raster` makes `gng_enhanced_raster.adf` (and `_512k_raster`): the same game with
the background colour (COLOR00) set at each stage of a frame, so in WinUAE each stage shows as a
band down the screen (on the black parts) and its height is the time it takes:

| Colour | Stage |
|---|---|
| grey | game logic (`Level1Logic`; `src/raster_patches.s` marks its start and its two exits) |
| red | scroller: new edges, restore of the buffer's BOBs |
| orange | playfield text printed again (`TextReplay`) |
| blue | BOBs |
| yellow | copper list |
| green | waiting for the copper interrupt at line `$44` (`ShowBackBuffer`) |
| black | idle: the frame's work is done |

A frame whose logic does not finish before the next vertical blank shows grey (or another stage)
running on past the bottom; a pause shows as the colours standing still.

### Trying it

Build (or use the images in the release), then in WinUAE with Kickstart 1.3 insert
`gng_enhanced.adf` in DF0 (WinUAE reads extended ADFs): with 512K of chip RAM it runs the 512K
program, with 1MB of chip RAM the 1MB one. `gng_enhanced_512k.adf` always runs the 512K
program. (Use 1MB of chip RAM for the 1MB program, as for the original: it keeps the masked enemy
graphics the blitter draws from next to itself (`ENEMY_GFX_CACHE`, an offset from its load
address), and the blitter can only read chip RAM - so loaded into slow RAM, as the bootblock
would do on a 512K chip + 512K slow machine, those BOBs could not be drawn. That is how the
source reads; it has not been tried.) Keys as the original: F1 one player,
F2 two, space to pause, Esc to abort.

If something looks wrong, the most useful report is what was on screen and what Arthur was
doing (walking, falling, climbing), and the level.

## One program for every machine

The original disk has two main programs; `enhanced/src/gng_game.s` is one program for every
machine, made from the merged source by `tools/make_game.py` and built with `tools/build_game.py`
(`build/game/`, disk `build/gng_game.adf`; `--raster`: the timing build, `gng_game_raster.adf`).
The scroller is part of it: `src/scroller.s` (the module's glue, storage at `SCROLL_STORE`) and
`src/scroll.s` (`BUILD_ONE`: the one-blit masked BOB drawing or the 512K mask-and-5-blits drawing
chosen at run time); `make_game.py` puts the calls into the game's routines where the earlier
builds patched them (`RedrawScreen`, `SwapScreens`, `ShowBackBuffer`, `SetBitplanePtrs`,
`RestoreBackground`, `DrawBobs`, `CameraJump`, PrintChar's playfield path, `RedrawEntry`, the
machine line after `DrawCreditsScreen`). Every machine draws every frame (`PF_EVERY`).

**How it chooses.** It is the 512K program - its memory map, loaded to `$80` on every machine -
plus the 1MB program's features. `ReadProfile` (first thing in `Start`) reads the bootblock's
machine description (`MACHINE_INFO`) and sets `Profile`:

| Bit | When | What it turns on |
|---|---|---|
| `PF_CACHE` | 1MB or more of chip RAM (any chip RAM above `$80000`: Kickstart 1.3 on a 1MB A500 keeps the top for itself and lists chip RAM as ending at `$FE800`) | graphics cached with masks in upper chip RAM (`CacheGraphics`, `BuildMaskedGfx`); one-blit BOBs (`DrawBobMasked`, `DrawSceneryMasked`); no graphics loads per level, the frame tables point into the cache; frame offsets doubled in place; progress map kept |
| `PF_MUSIC` | every machine with a machine description: with `PF_CACHE`, or the program moved to slow / fast RAM (below), the 1MB package; otherwise (a plain 512K A500) the 512K music package (*Music on 512K*) | the tunes: the 1MB music package (assembled for `$80000`; at `$80` when the program moved) with its extra effects, or on 512K the 512K effects with the 1MB tunes |
| `PF_EVERY` | (with `PF_CACHE`) | draw every frame |

Without them (512K of chip RAM and no expansion with room, or no machine description) it is
the 512K program. Upper chip RAM: music `$80000`, progress map `$9B400`, enemy sets
`$9D200`, small sets `$D7300`, shots `$D8D80`, items `$DB200`-`$E04D0` (checked at assembly).

**Slow / fast RAM: the program moves out of chip RAM (`EnhRelocate`).** With less than 1MB of
chip RAM and an expansion with room (fast RAM first, else slow RAM: the last region of each
kind in the bootblock's description), the first thing `Start` does is copy everything from
`$80` to the memory map (`MAP_LOW`: code, tables, globals - about 114 KB) to the expansion, load
the relocation file after it (track 17, one of the original 1MB program's tracks, free on this
disk), add the distance to every 32-bit address of the program in the copy, and run `Start`
again there (`RelocDone`). The memory map - screens, BOB graphics, copper lists, sprites, the
sound package - stays in chip RAM where it was: only the CPU reads the program. The chip RAM
from `$80` is then free, and `ReadProfile` turns on `PF_MUSIC`: `LoadSound` loads the 1MB music
package to `$80` (`MUSICB_FILE`; 18 whole tracks end below `MAP_LOW`, checked) and moves its
addresses too, so an A500 with a 512K trapdoor expansion plays the music and the 1MB effects.
The graphics are the 512K program's (one-plane masks and pre-masked images in the level data
area, as on 512K), and the title says MUSIC.

The relocation file is made by `build_game.py`: the program is assembled a second time 2MB on
(`RELOC_ORG`) with the memory map where it is (`MAP_FIX`), and every long that differs by 2MB
is an address to move; anything else that differs stops the build (a 16-bit address, or a
number worked out from one). The music package likewise (it turns out to be position
independent: no addresses). The file is a count and word gaps (238 addresses in the program,
484 bytes). `make_game.py` widens `(pc)` references the larger program puts out of reach.

In the emulator (`compare_game.py --machine slow|fast`: 512K chip + 512K slow, and 512K chip +
1.5MB slow + 2MB fast, against the original 1MB program, whose sound code it runs) the games
stay in step on every stage, the pictures as on the 512K machine. `tools/amiga.py` now checks
that every DMA pointer (blitter channels, copper lists and the bitplane / sprite pointers they
set, audio samples) is in chip RAM, and none of these runs read anywhere else. `game.py` maps
the expansion memory, works out where the program goes (`relocation()`, as `EnhRelocate` does)
and moves its labels and hooks; it also drops Unicorn's translated code where a file is loaded
over code that ran before (the 68000 has no cache).

**Per-level map tables (`LoadLevelTables`).** The originals keep every level's collision and
graphics tables for the map cells resident: `BlockTiles` (64 bytes a cell) and `CellTiles` (256
bytes a cell), 33 KB for the 104 cell types. Now `build_game.py` writes one file per level with
only the cells that level can read (`tables0.bin`-`tables6.bin`, tracks 18-32, the original 1MB
program's place), and `LoadLevelTables` loads the level's file to `LEVEL_TABLES`, below the
level file, whenever a level is set up (including from the cache on 1MB machines and at a
restart). A file is a slot byte for each of the 256 cell values, then `TBL_SLOTS` x 64 bytes of
block tiles and 256 bytes of cell tiles per slot; `MapTileAt` (collision) and `DrawTile` (the
scroller) look up the cell's slot first. Cell `$67` (empty: tile 0 everywhere) is slot 0, and so
is any cell a level never reads. Which cells a level reads follows from how the map is
addressed (`g_MapPtr + (X >> 8) + (Y >> 8) * 32`, with no bounds): the level's rectangle of
`WorldMap` from its origin (`LevelMapTable`, so level 6, the throne room, is `WorldMap+352` and
the bytes after the map) and size (`LevelBounds`), one cell more on every side, and columns 254
and 255 of those rows (an object just off the left edge has X >> 8 = 255). Bytes past the map
that `MapTileAt` still reads count as cells too, with the table entries the original reads for
them (it indexes both tables with the byte sign extended). The largest level needs 49 slots, so
the area is 256 + 49 x 320 = 15,936 bytes: about 17 KB less than the resident tables (the 512K
level data now ends at most at `$7A5E0`, before at `$7E806`). The program is 77,270 bytes
(110,140 before). The tables are the original 512K program's data, read from
`bin/main_512k.bin`; `build_game.py` checks that the map's readable span (`FrameOffsets1 -
WorldMap`) is still the one it assumed.

**Two unused gaps joined to the level data (3 KB).** A scan of chip RAM (fill everything from
`MAP_LOW` with a pattern, play every stage, see what is never written; then fill only those gaps
and check nothing reads or shows them) found two gaps next to the level data: the last third of
the HUD area (the HUD is 16 lines of 5 planes, `$B40` bytes, as `ClearHudArea` clears and the
copper shows; the original kept `$10E0`), and `$7F4DE-$7FB00` between the original's end of
level data and the bootblock's machine description (`EnhInit` copies that, and the loader above
it is finished with; the supervisor stack comes down from `$80000`, 318 bytes deep at most in
the emulator). The level tables now start at `CLEAR_AREA+$B40` and `LEVEL_GFX_LIMIT` is
`$7FB00`: the fullest stage (2) leaves 23,232 bytes free without pre-masking (20,222 before).

**The old save areas (24 KB).** Before the screens the original had the small BOBs' load
buffer (`BOB_GFX_A`) and two `$3000`-byte background save areas, with `LoadFile`'s MFM buffer
inside them. The scroller restores the background from its pristine buffer and saves nothing,
so the rest was only needed while loading. A trace of every `LoadFile` on 512K (start-up, every
level start and restart, the progress map) showed where else those buffers can go:

* the small BOBs' file loads into the screens right after the enemy sets' file
  (`SMALLBOB_LOAD`, `SCREEN_0+$1D478`); `LoadLevel` and `BuildLevelMasks` build the level's
  sets from both files there, before anything is drawn. `LoadLevel` now turns the bitplane
  DMA off before this load instead of after it;
* the MFM buffer goes to the top of the level area, below `LEVEL_TOP` (`$7FB00`): nothing there
  is in use while a level loads (its tile and table files load far below it, `build_game.py`
  checks; its sets and pre-masked images are copied in after the loads);
* the progress map, though, is loaded after the level (before each level and after a life is
  lost), when the level area is full. Its packed file and, for that load, the MFM buffer go into
  the first screen (`PM_LOAD`, `PM_MFM`; `LoadFile` takes the MFM buffer from `MfmBuf`): the
  bitplane DMA is still off then, and the map is unpacked into a higher screen (the lower of
  `g_ScreenSpare1/2`, `SCREEN_1` at the lowest).

`GNG_OVERRUN=1` also fills the MFM buffer with `$EE` at every load in `game.py`.

The screens, the scroller's storage, the HUD and the level area all move down `$6000`: the
fullest stage (2) leaves 47,782 bytes free without pre-masking (23,232 before).

**Dead code (3 KB).** A reachability pass over the listing (from `Start`, every label a table or
an equate refers to, and the targets of jump tables; a routine ends at an unconditional jump)
found what nothing reaches. `make_game.py` (`drop_dead_code`) now removes it: the original
routines the scroller took over at their label (`SetBitplanePtrs`, `CameraJump`, `SwapScreens`,
`ShowBackBuffer`, `RestoreBackground`, `DrawBobs`, `RedrawScreen`: everything after the `jmp`),
the original drawing the scroller replaced (`DrawBob`, `DrawBobMasked`, `DrawSceneryOnRedraw`,
`DrawSceneryMasked`, `WaitBlitIRQ`) and the debug `PrintHex*` routines; `scroll.s` loses
`DrawColumnAll` and `DrawRowAll`. The program is 74,250 bytes (77,296), the fullest stage leaves
50,828 bytes free. About 300 bytes of small unreachable pieces of the original are left as they
are (an unused path routine of the Petite Devil, a few instructions after jumps).

**The disk: an AmigaDOS-format disk and the 4489_byteloader** (made on branch `enhanced/byteloader`, merged).
The one program's disk (`build_game.py`: `gng_game.adf`, 901,120 bytes) is now an ordinary
880K disk, 11 sectors of 512 bytes a track with the `$4489` sync, with no filesystem (Workbench
shows it as NDOS). Every file is read with the [4489_byteloader](https://github.com/MarkyTurtle/4489_byteloader)
(`src/byteloader.i`, included as published: 390 bytes, any number of bytes from any offset; it
reads a whole track by DMA into an MFM buffer of `$1760` words, decodes it there, checks the
sectors and copies out the bytes asked for; it times itself on VHPOSR and leaves the
interrupts, CIA timers, blitter and copper alone).

| Disk offset | |
|---|---|
| `$000` | the bootblock (`src/boot_4489.s`) |
| `$400` | the file table (`FT_OFFSET`): `'GNGF'`, version, count, 8 bytes, then the offset and length (longs) of each file, by file id |
| `$600` | the files, one after another (720 KB; 175 KB free) |

The file ids are the `FID_` equates of `gng_game.i`, in the order of `disk_files()` in
`build_game.py` (the program 0, the loading picture 1, then the graphics, levels, sound and
table files). A file record (`FENTRY`) is now load address, length, file id; `build_game.py`
checks each record's length against its file.

*Bootblock* (`boot_4489.s`): the memory survey as before (`MemDetect`), the take-over, the
fade and the loading picture of the original bootblock; its loader runs at `$7FB20` (after the
machine description), with the MFM buffer at `$7C000` and the file table at `$7F000`. It reads
the file table, the picture (file 1, to `$60000`) and the program (file 0, to `$80`), sets
`$4.w` to `$80` and enters the program at `$A0`, as the original did on 512K. A failed load is
read again; after 8 failures COLOR00 turns red while it keeps trying.

*The game's loader*: the original's track loader (`LoadFile` to `SeekTrack0`) is gone; the
new `LoadFile` (`make_game_support.s`) keeps its interface (a1 = file record; out a5 = end of
the data, a0 = `CUSTOM`; the other registers are kept), reads the file table once into
`FileDir` and loads each file from its offset into its MFM buffer (`MfmBuf`: `MFM_BUFFER` at
the top of the level area, `PM_MFM` while the progress map loads). Two things follow from the
byteloader:
* it loads exactly the file's bytes: nothing is written past a file any more (the whole-track
  rounding of the relocation room and the progress map's buffer are gone);
* it uses a6, and files load with the interrupts running. The level 1 and level 3 handlers
  assume a6 = `GLOBALS`, so their vectors now point at `IrqLevel1` / `IrqLevel3`, which save
  the interrupted a6, set `GLOBALS` and enter `Level1Logic` / `VblIRQ`; their `rte`s became
  jumps to `IrqExit1` / `IrqExit3`, which put the interrupted a6 back.

*Testing*: `tools/floppy.py` emulates DF0 with the disk image in the harness (the drive lines
on the CIAs, disk DMA writing the track's MFM words from a sync, DSKBLK, and VHPOSR moving
while the byteloader waits). `test_boot4489.py` boots the disk from Kickstart's call to the
program's entry and checks the program, the picture, `$4.w`, the machine description and the
display (also with `--random-start`: the DMA starting at any sector, which the byteloader
handles by reading the track again). `compare_game.py --disk` runs the one program with its
own loader reading the disk image, against the original. With it the games stay in step on 512K (levels 1, 2
and 7, with teleporting), on a 1MB A500+, with Kickstart 1.3 on 1MB, and with 512K slow RAM
(where `EnhRelocate` loads the relocation file with the first copy's loader); the pictures as
with the loads stubbed. The bootblock test passes with the DMA starting at sector 0 and at any
sector (347 track reads instead of 34: the byteloader reads a track again until it starts at
sector 0).

With the smaller program the memory map moved down, and the slow / fast RAM music needed a new
order: the effects package's area now comes first after the program (`SFX_AREA`), and
`LoadSound` runs right after `ReadProfile`, so that the 1MB music package, loaded over the
program's old place, can run on into buffers that are only filled later.

### Music on 512K (made on branch `enhanced/music512`, merged)

A plain 512K A500 now plays the music. The memory came from the work above: the per-level map
tables (17 KB), two joined gaps (3 KB), the old background save areas (24 KB) and the dead code
(3 KB).

*The package* (`sound/gng_music_512k.s`, 75,514 bytes, made by `sound/tools/make_music_512k.py`
from the two symbolic sources; do not edit it). The 512K and 1MB packages are the same driver
with the same instrument numbers (0-9 the music's, 10-37 the effects'), so the new one is the
1MB driver, tune table and tune instruments, the 512K effects' instruments, sequences and
samples, and the 1MB tunes' voice data, patterns and samples (0-9). Instrument 9 is an effect's
(the 512K file's Ins00); the unused instrument 7 loops on sample 9 instead of the 1MB effect
sample 10, which is not included. Every tune plays as in the 1MB package and every effect as in
the 512K one: `sound/tools/check_music_512k.py` runs the driver in `sndemu` and compares the
Paula writes over 600 frames for all 15 tunes (against the 1MB package) and all 30 effects
(against the 512K package). The effects on 512K stay the 512K set (the 1MB package's extra
effects need its samples).

*In the game*: the package is file `FID_MUSIC512` on the disk, loaded by `LoadSound`
(`FileMusic512`) at `MUSIC_FILE` when the profile has `PF_MUSIC` without `PF_CACHE` and the
program did not move. `ReadProfile` now sets `PF_MUSIC` (and `PF_EVERY`) on every machine with a
machine description, so the tune calls and the title's MUSIC text work as on 1MB. `SFX_AREA`
grows from `$7D64` to `$12700` (43,420 bytes more), and everything after it in the map moves up
(the sprite data and `MASK_LINE_BUF` are now relative to `SFX_AREA` as the rest already were).
The level area loses the same amount, so `BuildLevelMasks` pre-masks less:

| Stage | Data ends (music) | Still 5 blits with music | Without music (before this change) |
|---|---|---|---|
| 1 | $7F9D4 | items / weapons, 7 enemy sets | 2 enemy sets |
| 2 | $7F9BC | enemy shots, items / weapons, 5 enemy sets | 3 enemy sets |
| 3 (dragon) | $7F888 | 2 enemy sets | nothing |
| 4 (dragon) | $7B320 | nothing | nothing |
| 5 | $7DF14 | 2 enemy sets | nothing |
| 6 (dragon) | $7F268 | 5 enemy sets | nothing |
| 7 | $754AC | nothing | nothing |

With no image pre-masked the fullest stage's data ends at `$7DFBA`, about 7 KB below the MFM
buffer: that is the room left for anything else on 512K. The sets left with 5 blits are drawn
with their one-plane masks, as all of them were before pre-masking.

*Testing*: `compare_game.py --machine 512k` now compares the 512K machine with the **1MB**
original (the tunes are the 1MB program's). The games stay in step on every stage (512K: level
0 3,000 frames, levels 1-6 2,500 frames with teleporting; the same on 512K + slow RAM, a 1MB
A500+ and an A1200 with fast RAM), and with `--disk` (the byteloader reading the disk image) on
512K levels 1 and 7, slow RAM level 3 and 1MB. The pictures differ only where they did before:
the title's machine line, the loading frames and, on stage 6, the one progress-map frame the
slow-RAM comparison already showed against the 1MB original. On 512K the channels play the tunes'
samples (1MB samples 5-9 in the opening tune) alongside the effects' samples.

*In WinUAE* (tried on an unexpanded A500, an A500 + 512K, an unexpanded A500+, an A600 and an
A1200): it works on all of them. On the plain A500 the slow-down is small and brief, mostly at
the end of a level with the dragon and on the dragon's level itself, and hardly noticeable.

**Music quality on 512K** (made on branch `enhanced/musicquality`, merged; tried in WinUAE). The tunes' sampled
instruments (samples 5-9: 32,726 of the package's bytes) are now at **3/4 of their rate** in the
512K package: `make_music_512k.py` resamples them (scipy's polyphase filter; the loop samples 7-9
as loops) and divides their instruments' period multipliers by 3/4, so every note keeps its
pitch (within 7 cents, about one period step; the multipliers stay below `$FFFF`). The
single-cycle waveforms (samples 0-4) stay, as their length is their pitch. The resampled samples
are kept in `sound/samples/r3_4/`. The package is 67,332 bytes (8,182 less), and `SFX_AREA`
now follows its length (`MUSIC512_LEN` rounded up to 16 bytes, at least the effects package's
`$7D64`), so the level area gets the difference: with no image pre-masked the fullest stage's
data ends at `$7C160` (14.4 KB free instead of 6.4 KB), and pre-masking takes it:

| Stage | Data ends | Still 5 blits (3/4 music) | At full quality |
|---|---|---|---|
| 1 | $7EE1A | items / weapons, 5 enemy sets | items / weapons, 8 enemy sets |
| 2 | $7F6AA | items / weapons, 6 enemy sets | enemy shots, items / weapons, 6 enemy sets |
| 3 (dragon) | $7EB1E | 1 enemy set | 2 enemy sets |
| 4 (dragon) | $794C6 | nothing | nothing |
| 5 | $7E682 | 1 enemy set | 2 enemy sets |
| 6 (dragon) | $7E18E | 4 enemy sets | 5 enemy sets |
| 7 | $73652 | nothing | nothing |

The quality was chosen from listening to 3/4, 2/3 and 1/2 (8.2, 10.9 and 16.4 KB saved; renders
and test disks): 3/4 was the best compromise. `build_game.py --music-rate N/D` still builds the others
(`--music-rate 1`: full quality). The 1MB package (1MB of chip RAM, or slow / fast RAM) keeps
full quality. A menu choice could not give memory back: the package is at the bottom of the map
and the level area at the top, fixed when the program is built.

*Testing*: `check_music_512k.py` now makes the package at full quality too and checks that it
writes the same Paula registers as the 1MB package for every tune, and that the 3/4 package
writes the same registers as full quality except the periods on resampled samples (full
quality's / 3/4, to within one period step) and their lengths; the effects as the 512K
package. (Checked to fail when told the wrong rate.) The comparisons with the originals stay in
step (game logic is unchanged).

**Where the originals differ** both versions are in the source, chosen at run time. In the
sound code the choice keeps the condition codes (`move sr,-(a7)` ... `move (a7)+,ccr`; game
logic runs in supervisor mode), so each profile sees exactly the flags and `d0` its original
did. Jump-table entries stay single `bra.w`s. Two text differences (`SOUND`/`MUSIC` in the
credits, the blank-name initials) are patched at start-up.

**A bug fixed on the way (`MapTileAt`).** For an object far below a level (Y negative) the
original reads its own code as map cells (the cell index runs $1FE0 bytes past the map), so
what it finds depends on the program's layout: the 512K and 1MB programs already differ there,
and any changed program differs again. Now a cell read at or past the BOB frame tables (where
the programs' contents start to differ; the map and the tables after it read as before) is the
empty cell `$67`. `compare_game.py` gives the originals the same fix (a hook) when comparing.

**Testing** (`tools/compare_game.py --machine 512k|1mb`, against the matching original, game
state and picture every frame; the 512K original drawing every frame and with its DrawBob
top-clip bug fixed, as the enhanced builds were always compared). Before the scroller was folded
in: on a 512K A500 identical to the 512K program in every frame (level 0 4,000 frames; levels 2,
4, 5 2,500 frames with teleporting); on a 1MB A500+ in step with the 1MB program throughout,
pictures identical except two single frames of leftover screen junk in the original. With the
scroller: the same runs stay in step on both machines; the pictures differ only on the title
screen (the machine line), the loading frames, one progress-map frame, and where the original
leaves playfield text on screen that the game no longer prints (the key message; see *Playfield
text*). The originals' globals overlay the end of the program
file and some are used before they are set (the fraction of `g_ArthurX` in the opening scene),
so for the 1MB comparison the original starts with the same junk. The enemy slots are such
globals too (Astaroth's first X fraction is whatever the slot held), and the one program is now
shorter than the 512K original: `game.py` clears the memory after it (the bootblock loads whole
tracks, and the rest of the program's last track is zeros), where it used to leave the
original's bytes. `LoadFile` also writes whole tracks; `GNG_OVERRUN=1` makes `game.py` fill the
rest of each file's last track with `$EE` bytes, to check that nothing needed lies in the way
(off by default: the originals and the one program then leave different junk where unused
sprites show it).

**One-plane masks (512K profile).** The 512K drawing built each BOB's mask with two blits (the
OR of its 5 planes into `MASKBUF`) before its 5 cookie-cut blits. Now `BuildLevelMasks` (called
by `LoadLevel` after the sets are copied) makes the masks once per level, strip by strip from the
graphics files' strip tables (`CacheSizes*`): for the level's BOB sets (region 2, after the
copies) and for the item / weapon / shot graphics (region 1). A mask line is the OR of an image
line's 5 plane lines, so a region's masks are a fifth of its size and an image's mask is at
`mask base + (graphics - region base) / 5`; `BobMaskFind` looks it up when a BOB is drawn, and
each drawn part finds its place from how far clipping has moved the graphics pointer (whole
lines: a fifth; bytes at the left: the same). A BOB with no mask (none found in the runs) is
drawn the old way. 7 blits per BOB become 5, and the blitter work per BOB falls by about a
quarter. Measured in the emulator over 600 frames of level 0 (restore and new edges included):
20.9 blits and 3,803 channel-words per frame before, 15.8 and 3,016 after. Every BOB in the
runs found its mask; the pictures are the same as before on all seven levels. Memory: at most
13 KB per level plus 3 KB (the worst level's data now ends at $7DD56).

**Pre-masked images on 512K, as far as memory goes.** A pre-masked image (the 1MB format:
every plane line followed by its mask line, `BuildMaskedGfx`) is drawn in one blit instead of 5.
The blitter moves the same words either way; what goes is the 4 set-ups between blits (the CPU
waiting for the blitter, then loading it, with the blitter idle) and the mask lookup with its
divisions: about 1.5 raster lines per BOB, a large part of a small BOB's cost. `BuildLevelMasks`
now fills the room up to `LEVEL_GFX_LIMIT` ($7FB00; at first $7F4DE, the original's end of level data) in the
order of `GfxPriority`: the enemy shots, the small BOB sets, the dragon's set, the items /
weapons / effects, then the other enemy sets, smallest first; whatever does not fit gets
one-plane masks as above. A set costs 0.8 x its size more than with a one-plane mask; the shots
and the items cost twice their size (their files stay where they are loaded, for the next
level). The game's own image addresses are not changed: a converted image's pointer
(`g_BobSets`, `g_SmallBobSets`, `EShotGfxPtr`, `ItemGfxPtr`) becomes a key in
`[KeyBase, KeyBase + KeyLen)` and its masked copy is at `KeyBase + 2 x (key - KeyBase)` - the
doubling the 1MB program applies to its offsets - so `BobMaskFind` needs one compare to send a
BOB down the one-blit path (`BobMasked`, which `GFXMUL` and the drawing test instead of the
profile). The sets are taken again from the graphics files still in memory at that point (enemy
sets at `SCREEN_0`, small sets at `BOB_GFX_A`). `build_game.py` prints what each stage gets:

| Stage | Data ends | Still 5 blits |
|---|---|---|
| 1 | $7F382 | items / weapons, 8 enemy sets |
| 2 | $7F12A | enemy shots, items / weapons, 6 enemy sets |
| 3 (dragon) | $7EB96 | 3 enemy sets |
| 4 (dragon) | $7B3AE | nothing |
| 5 | $7DFA2 | 2 enemy sets |
| 6 (dragon) | $7F2F6 | 5 enemy sets |
| 7 | $7553A | nothing |

Measured in the emulator (2,500 frames with the same input, teleporting): blits per play frame
on stage 1 21.6 -> 18.1, stage 3 36.5 -> 19.4, stage 6 (the dragon present) 35.2 -> 18.9; the
blitter words are unchanged, and so are the pictures on all seven stages (512K and 1MB runs in
step with the originals). The time saved has to be measured in WinUAE (timing build).

**Look-ahead rows (`ScrPrepareRow`).** The same for vertical scrolling. The 256-line ring holds
16 tile rows and the window needs 14-16; while it has 15 or fewer, the row next to it on the
side the camera last moved to (vertically) is built in the spare row's memory - 6 tiles a frame
in the pristine buffer, then its scenery (the clip grown by a row that way), then 12 per update
in each display buffer - and `DrawRowNew` draws only the columns still missing when the row
comes into view. A column entering on the right leaves the columns done valid; one on the left
starts the row again (as rows do for the look-ahead column). Measured with teleporting play: the
camera climbs at up to 4 px a frame and falls at 4-10, a new row every 4-8 frames; on stage 5,
144 of 155 row crossings found the row already complete in the pristine buffer.

**Cheat key (testing).** On the title and high-score screens, **C** turns the game's own cheat
(`g_CheatOn`, the one entering `)!(` on the high-score table sets: lives never decrease, no harm
once the armour is gone) on or off, and shows the title again with `CHEAT ON` under the key
lines while it is on (`EnhCheatKey`, `EnhShowCheat`). It stays set until switched off or the
machine is reset; a high-score entry other than `)!(` clears it, as in the original.

**Look-ahead column (`ScrPrepare`).** A frame that crossed a tile column drew the whole new
column at once: about 15 tile blits into the pristine buffer and 15 tile copies into the display
buffer, and the other display buffer's 15 the next frame - a spike on top of a busy frame. A
buffer holds 18 columns' memory and 17 are fetched; the 18th is the column next to the window on
the side the camera last moved to (it shares its memory with the one on the other side, so it is
one or the other). `ScrPrepare` (once a frame, after the restore) builds the column that will
come into view next there, out of sight: the pristine buffer 4 tiles a frame, then, once it is
finished, its scenery (`ScrDrawScenery` with the window moved over it); each display buffer
copies 8 tiles per update once the pristine one has finished the same column (so the copies
carry the scenery). When the camera crosses into it, `DrawColumnNew` draws only the rows not
done yet; a crossing the other way (a change of direction, rare: 5-9 in 2,000 frames of play)
draws the whole column as before. Rows: a new top row leaves the rows done valid (the new row
is after them); a new bottom row starts the column again. Measured: the camera moves at most
2 px a frame, a column every 10-16 frames when walking, and the look-ahead is finished well
before the crossing. Blitter words in the crossing frame and the next two, stage 1: 8,870 ->
6,724 on average; stage 6: 13,601 -> 11,515; the 99th-percentile frame: 4,635 -> 3,840 and
5,620 -> 4,880 words. Pictures unchanged on all seven stages (512K and 1MB).

**Blitter priority while waiting (`--nasty-wait`, to be measured).** The original sets BLTPRI
("blitter nasty") once at start-up and never clears it. With all code and data in chip RAM, the
CPU then cannot fetch an instruction while a blit runs, so the work between blits (the next BOB's
clipping and addresses, the copper list and the logic after the last blit) never runs alongside
one. `build_game.py --nasty-wait` (`NASTY_WAIT`) sets BLTPRI only inside `WAITBLIT`, while the CPU
does nothing but poll, and clears it after (the first wait clears the original's setting). With
the bus shared, a blit loses up to a quarter of its bus cycles while the CPU uses the bus, but the CPU work it
overlaps is saved; whether that is a net gain needs WinUAE (cycle-exact): the emulator here does
not model bus contention. Disks: `gng_game_nastywait.adf`, `gng_game_raster_nastywait.adf`.

**Memory (512K profile).** The program has grown (to $1A19C) and the whole map after it moves
with it, so the HUD area (`CLEAR_AREA`) and the level file (`LEVEL_FILE`) are moved down into the
old fourth screen, free above the scroller's storage: the worst level's data (stage 2: tile file
$C120 + BOB sets $DE76) now ends at $7A27A, 21 KB below the original's $7F4DE. `build_game.py`
checks it from the game's own tables. (The first disks of the one program did not do this; on a
512K machine stage 2's data ran past $80000.)

**Disk** (`build/gng_game.adf`): the bootblock (memory survey, always loads to `$80`) loads
the program from tracks 134-150 (it is 17 tracks now); effects package at 126 (assembled for
the program's `MUSIC_FILE`), music package at 64; the original programs' tracks are empty.
`tools/disk/mkdisk.py --one` builds it.

### Two-button joysticks (made on branch `enhanced/joystick`, merged; tried in WinUAE)

The joystick's second button (port 2, pin 9: a Sega-style pad or a two-button stick) can make
Arthur jump, as on the arcade machine. The title menu's **INPUT** item (or the J key) switches
between jump on up (the original, and the default) and jump on button 2 (*The title menu*,
below). The setting is `JumpButton` (`scroller.s`), kept until the machine is reset.

*Reading it* (`make_game.py`, `two_buttons`): the vertical blank, which reads the joystick into
`g_Joy` (right, down, left, up as decoded from `JOY1DAT`; fire bit 15), now also sets bit 14 when
`POTINP` bit 14 (DATRY) is low, and writes `POTGO` = `$C000` (pin 9 an output driven high, so a
pressed button pulls it low; the mouse port's pins are left as inputs). Nothing else reads bit 14,
so with jump on up the game is the same as before.

*Jump on button 2* (`ArthurReadUpDown`): the button counts when held for two samples, as up
does, and jumps unless Arthur is on a ladder (taking the original's jump path, so the frog jumps
too and nothing jumps while climbing). Up then only climbs: at a ladder as before (and stepping
off at the top), elsewhere it does nothing (the original's jump entry returns as if nothing were
held), also for the frog. Down is unchanged.

*Testing*: `tools/test_jump.py` saves one state of a game on level 1 and runs each setting with
up, button 2 and both, on open ground, at the foot of a ladder and on it (15 cases): up jumps or
climbs and the button does nothing with jump on up; the button jumps (not from the ladder) and up
only climbs with jump on button 2. The emulator harness's `frame()` takes the second button
(`fire2`; `POTINP` reads as not pressed otherwise). The comparisons with the originals (jump on
up) stay in step as before.

### The title menu (made on branch `enhanced/titlemenu`, merged; tried in WinUAE)

The title screen's instructions ('Press fire for 1 player game', the F1 / F2 lines, 'Press
SPACE to pause game', 'Press Esc to abort game') are replaced by a menu (`scroller.s`: `EnhMenu`
from `CheckGameStart`, `EnhTitleText` from `DrawCreditsScreen` after the logo; `make_game.py`:
`title_menu`). The logo, the credits and the copyright lines stay.

| Page | Items |
|---|---|
| title | `PLAYER 1 START`, `PLAYER 2 START`, `INPUT - JUMP ON UP` / `JUMP ON BUTTON 2`, `TEST MENU`; then one line `SPACE pause   Esc abort` |
| test | `TEST MENU`, the memory the bootblock found (`CHIP 512K SLOW 0K FAST 0K`: the line that was on the title), then `CHEAT OFF` / `ON`, `EXIT` |

Up and down move (round from the last item to the first), fire chooses; on `INPUT` and `CHEAT`
left, right and fire switch the setting. The item chosen shows as `> ... <` in the credits'
colours. A move or a change draws the title again (as the C key did: `GS_TITLE` from step 0,
double-buffered), which also starts its 400-frame time-out to the high scores again; the test
page has no time-out. On the high-score page the joystick goes back to the title (it no longer
starts a game there). The keys still work: F1 / F2 start a 1 / 2 player game at once, J switches
the jump input, C the cheat. Moves and fire count when newly pressed (`g_Joy` against
`g_JoyPrev`; the original read the fire button's level), so a held button does not repeat: fire
on `PLAYER 1 START` starts a game in the same frame as the original's fire did, and the
comparisons stay in step.

The sound, sprite and input tests (`docs/TODO.md`, 8) are to go on the test page. Memory: the
program is 206 bytes longer (the menu, less the original's instruction code and texts); stages
1 and 2 now pre-mask one small enemy set fewer.

*Testing*: `tools/test_menu.py` (12 cases from one saved state of the title: starting 1 and 2
player games from the menu and with F1 / F2, moving round, the input and cheat switches, the
test page staying, EXIT, the time-out to the high scores and back).

### The test page's tests (made on branch `enhanced/testmenu`)

The test page (`TEST MENU`) has a sound test, an input test and a sprite test (`scroller.s`:
`EnhMenu`, `EnhTitleText`, `StopMusic`, `EnhTitleSprite`; `MenuPage` is now `PAGE_TITLE`,
`PAGE_TEST`, `PAGE_INPUT` or `PAGE_SPRITE`). Its items start a row higher (`ItemRow` = `$70`)
to fit six.

*Sound*: `MUSIC` and `EFFECT` call `PlayMusic` / `PlaySfx` as the game does (with no machine
description there is no music, and `MUSIC` does nothing). The driver has no command to stop a
tune - the game only ever starts another - so `StopMusic` points each of its four music voices
at an end-of-track byte (`$67`), as `CmdPlayTune` points them at a tune: at the next tick each
voice stops and its channel gets the silent sample. The driver's workspace is found from its
code (`lea DriverVars(pc),a3` in `CmdPlayTune`, at the entry + `$1E`; the same driver in all
three packages: checked there before writing). Leaving the test page or starting a game stops
the music.

*Input*: the page shows the bits of `g_Joy` (the vertical blank's joystick reading: directions,
fire, the second button) and the last raw key code; when either changes and the title is not
being drawn, it is drawn again (`InputShown`, `InputKeyShown`). Esc, or fire held for 150
frames (`HoldTime`), goes back.

*Sprite*: the title's step 0 now calls `EnhTitleSprite` where it cleared `g_ArthurVisible`: on
the sprite test Arthur is made visible, placed a fixed distance from the camera
(`SPR_X`, `SPR_Y`) so that `ArthurSpritePos` (called next) puts him between the text lines,
and given the frame chosen (`~n` for a mirrored copy, frames 0-39); `g_ArthurShownFrame` is set
to an impossible frame so the vertical blank copies the frame into the sprite data. Everything
else on the title is as before (`g_ArthurVisible` cleared on every other page).

Memory: the program is 1,376 bytes longer; stage 2 draws one more small set (set 20) with 5
blits. *Testing*: `test_menu.py` now has 24 cases (the sound test's tunes and effects, playing and
stopping, checked in the driver's voices; the input test's display of held directions, the
second button and a key; Esc; the sprite test's frames, mirrored copies and visibility; fire
held to go back), `StopMusic` also checked with the driver in upper chip RAM (1MB) and at `$80`
(the program moved). The emulator draws no sprites, so Arthur's place was checked from his
sprite control words (an overlay in a test script).

## Files

* `src/scroll.s`: the scroller core (`ScrFullDraw`, `ScrScrollTo`, `ScrBuildCopper`, `ScrRestore`,
  `ScrDrawBobs`, `CopyAll`); `src/scroll_test.s` assembles it at `$7A000` for the unit tests.
* `src/module.s`: the game module (scroller + glue); `src/patches.s`: the changes to the main
  program.
* `tools/build_enh.py`: builds the module, the patched program, the bootblock and the disk image.
* `tools/game.py`: runs the whole game in the emulator - 512K or 1MB program, original or
  enhanced (`python3 game.py 1mb enh 300`).
* `tools/compare_runs.py`: the original and the enhanced game side by side.
* `tools/check_game.py`: each frame the enhanced game shows, against the original's display code
  drawing the same state (a second check, independent of the two games staying in step).
* `tools/amiga.py`: harness: 68000 + blitter + copper + display renderer.
* `tools/original.py`: drives the original game's display code in the harness (the reference).
* `tools/check_harness.py`: checks the harness against the level pictures in `render/out/`.
* `tools/test_scroll.py`: the scroller against the original, frame by frame.
* `src/boot_patches.s`: the bootblock's memory survey; `tools/test_bootinfo.py` tests it.
* `tools/test_jump.py`: the two-button joystick settings (jump on up or on button 2).
* `tools/test_menu.py`: the title menu.
* `tools/test_bobs.py`: BOBs, restores and scenery against the original's `DrawBobs` and
  `DrawSceneryOnRedraw`.

```
cd enhanced/tools
VASM=/path/to/vasmm68k_mot python3 build_enh.py         # -> ../build/gng_enhanced.adf
python3 compare_runs.py 6000 1                           # frames, input seed [--level N] [--teleport N]
python3 compare_runs.py 5000 1 --build 1mb               # the 1MB program   [--png DIR]
python3 check_harness.py
VASM=/path/to/vasmm68k_mot python3 test_scroll.py 80     # steps per level
VASM=/path/to/vasmm68k_mot python3 test_bobs.py 40       # frames per level, then the scenery sweeps
```

## Next steps (as planned at the time; all done - the current list is `docs/TODO.md`)

0. **Fold the scroller into the game source.** Today the enhanced program is the original binary
   with patches written over it, plus the module loaded from track 132. The aim is one source on
   this branch (`gng_main.s`, edited here) that assembles the enhanced program directly - both
   builds, since `gng_main.s` on `main` now holds the 512K and the 1MB program in one source
   (`ifd BUILD_1MB` blocks; `tools/merge_src.py`, both byte-identical):
   * **First make the source relocatable** (on `main`, still byte-identical; this is the 512K side
     only, the 1MB code is already position independent): about 36
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
   * Note: `gng_main.s` is generated on `main` (`tools/gen.py`, `gen1m.py`, then
     `merge_src.py`); on this branch it would be edited by hand from then on, so later annotation
     changes on `main` merge as text. Doing the relocation step on `main` first keeps those merges
     small.

1. **Real machine timing.** First WinUAE run (played to the end with the cheat): vertical
   scrolling while falling is clearly better (no freezes); the general frame rate is not
   noticeably different. That is expected: the game moves everything every frame (50 Hz) but
   PlayFrame only sets the camera and draws on odd frames (`btst #0,g_GameFrame+1` at `$6E76`),
   so the display runs at 25 fps in both builds; the original's redraws ran in the background
   between those frames and only showed when they made the logic freeze.
   * **Raster-time build:** done (`--raster`, see *Timing build*). First WinUAE results: the
     pauses seen with the 1MB program were WinUAE in full-screen mode (none in a window). On an
     A1200 configuration a frame's work takes about half a frame; on an A500 it does not always
     fit in one frame at the 1MB program's 50 fps. In the A500 screenshot the BOBs (blue) are the
     biggest drawing stage, then the restore and new edges (red); the CPU waits for the blitter
     through both.
   * **Let the CPU work while the blitter does:** today every blit is set up after waiting for
     the one before, so the CPU idles through the red and blue bands. A queue of blits fed by
     the blitter-finished interrupt (or the logic of the next objects running between blits)
     would overlap the two.
   * **Draw every frame (50 fps) on the 512K program:** *done, now the default (see *Frame
     rate*).* In the emulator it shows a frame every logic frame (830 of 831 in play), and 1,000
     of those frames checked against the original's display code (`check_game.py`) were
     identical. On a 512K A500 in WinUAE it holds 50 fps except in busy scenes, where it drops to
     25 fps; the CPU/blitter overlap above is what would keep those at 50.
2. **Use the freed memory** (43 KB of screens, the 24 KB of save areas): the first step towards
   music on 512K machines and the other items in `docs/TODO.md`.
3. **One-plane masks** stored per frame (or the on-demand cache) instead of the 512K build's 2
   mask-building blits (the 1MB build already has pre-masked graphics, and its scroller uses
   them).
