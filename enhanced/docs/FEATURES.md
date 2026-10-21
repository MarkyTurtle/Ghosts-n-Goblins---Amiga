# The enhanced game: features

Ghosts'n Goblins (Elite, 1990) rebuilt from the annotated disassembly as **one program for every
Amiga**, with an incremental scroller, 50 fps drawing, music on every machine, a standard
AmigaDOS disk, two-button joysticks and a title menu. The game itself - its logic, levels,
enemies, timings and scoring - is the original's: in the emulator the enhanced game and the
original program are run side by side with the same input and stay in the same game state
every frame (*Testing*, below).

This branch is `enhanced/scroll`. Where things are:

| Document | |
|---|---|
| `FEATURES.md` | this: every feature, what it does and where the code is |
| `MEMORY.md` | the memory layout on each kind of machine (generated from the build) |
| `DISK.md` | the disk layout, the file table, every file, booting (generated from the build) |
| `FORMATS.md` | the format of every file and of the data the game builds from them |
| `SCROLLER.md` | the development log: how each feature was made, measured and tested, in order |
| `../../docs/TODO.md` | what is done and what is left |
| `../../README.md` | the original game: the disassembly, its formats, findings and bugs |

## Playing it

`enhanced/build/gng_game.adf` (made by `enhanced/tools/build_game.py`) is an ordinary 880K disk
image: put it in DF0 of any Amiga with Kickstart 1.3 or later and 512K of chip RAM or more (in
WinUAE: A500, A500+, A600, A1200 and others tried). It boots by itself.

* **Title menu**: up / down choose, fire selects - `PLAYER 1 START`, `PLAYER 2 START`,
  `INPUT` (jump on up or on the joystick's second button: fire, left or right switch it),
  `TEST MENU` (the machine's memory, a sound test, an input test, a sprite test, the cheat, `EXIT`).
* **Keys** (as the original): space pauses, Esc gives up the game; on the title F1 / F2 start a
  1 / 2 player game at once, J switches the jump input, C the cheat.
* **Joystick** in port 2. With jump on button 2, up only climbs ladders, as on the arcade
  machine; with jump on up (the default) it plays as the original.

## Display and drawing

**Incremental scrolling** (`src/scroll.s`, `src/scroller.s`). The original redrew the whole
screen - 288 tile blits and a 46 KB CPU copy - every time the view crossed a 16-pixel tile
boundary, in the background, and the game's logic froze when a redraw fell behind (falling,
fast scrolling). The enhanced game keeps three buffers - a *pristine* background and two
*display* buffers - laid out as a **corkscrew** horizontally (scrolling right moves the bitplane
pointers on a word, so a new column's memory is the column that just left: nothing is ever
moved) and a **256-line ring** vertically (the copper list waits for the wrap line and reloads
the pointers). Only the new tile column or row is drawn, into the pristine buffer, and copied
into the display buffers. The screen stays line-interleaved, so a tile is one blit. No freezes;
the camera and the tile origin (which also selects the enemy spawn zones) move exactly as in
the original.

* **Look-ahead** (`ScrPrepare`, `ScrPrepareRow`): the column and the row that will come into view
  next are built a few tiles a frame out of sight, so crossing a tile boundary costs almost
  nothing in the frame it happens.
* **Pristine restore**: a BOB is removed by copying its rectangle back from the pristine buffer
  (one blit) - no background save before drawing, no `$3000`-byte budget.
* **Scenery** (gravestones and other shootable items) is drawn into the pristine buffer with the
  tiles, as the original drew it during its redraws.

**50 frames a second on every machine** (`PF_EVERY`). The original 512K program moved
everything every frame but drew only every other frame (25 fps). Without the background redraws
there is time to draw every frame; when a frame's work does not fit, the vertical blank skips a
logic run as the original does, and the game drops to 25 fps for those frames rather than
tearing. On a plain A500 it holds 50 fps except briefly in the busiest scenes (the dragon).

**Faster BOBs on 512K** (`BuildLevelMasks`, `BobMaskFind`, `ScrDrawBob`). The original built
each BOB's mask with two blits before its five cookie-cut blits. Now, when a level loads:
* the images the memory allows are converted to **pre-masked** images (the 1MB program's
  format: a mask row after every plane row) - **one blit** a BOB - in the order of
  `GfxPriority`: enemy shots, small BOBs, the dragon, items and weapons, then the other enemy
  sets, smallest first;
* the rest get **one-plane masks** made once - five blits a BOB instead of seven.
With 1MB of chip RAM every image is pre-masked at start-up, as in the original 1MB program.
`MEMORY.md` shows what each stage gets.

**Playfield text** (`TextReplay`, `TextFlush`, `PrFast`, `DrawStrip`). Characters are queued and
drawn once a frame, straight into the ring buffers from a glyph cache; a line of a message
('TAKE A KEY FOR COMING IN !', 'BONUS') is put together once as a single pre-masked BOB and drawn
in one blit a frame. Text the game stops printing disappears like a BOB.

**End-of-level timings.** The original's slow drawing kept the end-of-level messages on screen
far longer than their frame counts; at 50 fps they would flash by, so the key message now shows
for 5 seconds and the bonus for 3.

**The progress map's tune** starts when the map appears, not while it loads from the disk.

## Machines and memory

**One program for every machine** (`gng_game.s`, made by `make_game.py` from the merged source
of both original programs). The original disk has two programs, for 512K and for 1MB; the
enhanced disk has one, loaded to `$80` everywhere, which decides at start-up what to use from a
description of the machine the bootblock leaves (`ReadProfile`, `Profile`):

| Machine | What it gets |
|---|---|
| 512K of chip RAM (A500) | music (the 512K package), one-plane masks and pre-masked images as far as memory goes |
| 512K of chip RAM + slow / fast RAM (A500 with a trapdoor or side expansion) | the program moves to the expansion (`EnhRelocate`), the full-quality music and the 1MB effects go into the chip RAM it left |
| 1MB of chip RAM or more (A500+, A600, A1200; others untested) | the 1MB program's features: every graphic cached with masks in upper chip RAM (one-blit BOBs, no graphics loading per level), the progress map kept, the full-quality music |

Where the two original programs differ (sound calls, text, caching), both versions are in the
source and chosen at run time, keeping the condition codes each original saw. `MEMORY.md` has
the layout on each machine.

**Machine description** (bootblock: `MemDetect`). Before taking the machine over, the bootblock
reads exec's memory list and writes chip, slow and fast RAM, PAL / NTSC and the CPU to
`MACHINE_INFO` (`FORMATS.md`). The test page shows it (`CHIP 512K SLOW 512K FAST 0K`).

**The program moves to expansion memory** (`EnhRelocate`, `ApplyRelocs`). With 512K of chip RAM
and an expansion with room, the program copies itself (code, tables, globals: about 80 KB) to
fast RAM, else slow RAM, loads a relocation file listing its addresses (`build_game.py` makes it
by assembling the program at two addresses), moves them and runs from there. Only the CPU reads
the program, so the screens and graphics stay in chip RAM, and the chip RAM it left holds the
1MB sound package.

**Memory freed on 512K** - what made room for the music and the pre-masked images:
* the scroller: three buffers of 47,120 bytes instead of four screens of 46,080 (43 KB);
* per-level map tables (`LoadLevelTables`): each level's collision and graphics tables for its
  map cells in a file of its own instead of every level's in the program (about 17 KB);
* the old background save areas and load buffers: the small BOBs and the progress map load into
  the screens, the disk's MFM buffer goes to the top of the level area (24 KB); two unused gaps
  joined to the level data (3 KB);
* the original routines the scroller replaced and debug code removed (`drop_dead_code`, 3 KB).

## Sound

**Music on every machine.** The original 512K program played only sound effects; the 1MB one had
the music. Now:
* with 1MB of chip RAM, or with the program moved to an expansion: the original 1MB sound
  package - 15 tunes and the 1MB set of effects, full quality;
* on a plain 512K A500: a package made for it (`sound/gng_music_512k.s`,
  `sound/tools/make_music_512k.py`) - the 512K effects with the 1MB tunes, the tunes' sampled
  instruments resampled to 3/4 of their rate (the pitch kept exact by the instruments' period
  multipliers), 67 KB. The quality was chosen by ear; `build_game.py --music-rate N/D` builds
  others. Every tune is checked against the 1MB package and every effect against the 512K one
  (`check_music_512k.py`).

## Disk and loading

**An AmigaDOS-format disk** (`DISK.md`). The original disk is in a custom track format; the
enhanced one is a standard 880K disk (11 sectors of 512 bytes a track) with a file table, read
with the [4489_byteloader](https://github.com/MarkyTurtle/4489_byteloader). The bootblock
(`src/boot_4489.s`) surveys the memory, shows the loading picture and loads the program; the
game's `LoadFile` reads any file by its id.

**Boot from any drive.** The bootblock finds the drive it was booted from (it opens
`trackdisk.device`'s units until one is the boot IORequest's) and passes it on in the machine
description; every load, the bootblock's and the game's, reads that drive. Kickstart 1.3 boots
only from DF0; with 2.0 and later the disk can be booted from DF1-DF3 (the early startup menu:
both mouse buttons held at power-on). Files load with interrupts running, so the game's
interrupt handlers set up their own `a6` (`IrqLevel1`, `IrqLevel3`).

## Loading

**A level's enemy sets only** (`LoadEnemySets`). Each level start read the whole enemy graphics
file (118 KB) to copy out the sets the level uses; now only those sets are read (22-65 KB), each
to its place, sets less than a track apart as one piece (the disk is read in whole tracks
anyway): 8-16 fewer track reads at a level start. `LoadFile` takes a starting point in a file
from `LoadOffset`.

**The file cache** (`CacheInit`, `LoadFile` in front of `LoadDisk`). On a machine with memory to
spare, the files read again and again are kept after their first load and copied from memory
afterwards; files are kept first come, first served while there is room (`MEMORY.md`):

| Machine | Where | Files kept |
|---|---|---|
| 512K chip + slow / fast RAM (the program moved) | the rest of the expansion region (431 KB with 512K of slow RAM) | all of them: the enemy graphics, small BOBs, progress map, every level's tiles and tables (341 KB) |
| 1MB of chip RAM or more | chip RAM above the graphics caches, or a slow / fast RAM region if larger | the levels' tile and table files (the graphics are cached already) |

A level loaded again (a restart, a second game) then reads nothing from the disk; on an expanded
A500 neither does the progress map after a life is lost.

## Controls and menu

**Two-button joysticks** (`two_buttons` in `make_game.py`; `ArthurReadUpDown`). The second
button of a Sega-style pad, a two-button stick or a CD32 pad's blue button (port 2, pin 9, read
through `POTGO` / `POTINP`) can be jump. With it, up only climbs ladders; jumping from a ladder
is not possible, as in the original. The setting is on the title menu (`INPUT`).

**Title menu** (`EnhMenu`, `EnhTitleText`). Replaces the original's instruction lines; one line
remains for the in-game keys. A change redraws the title (double-buffered) and restarts its
time-out to the high-score table. On the high-score table the joystick returns to the menu.

**Test page** (`TEST MENU`; no time-out): the machine's memory (from the bootblock's
description), then:

| Item | |
|---|---|
| `MUSIC OFF` / `nn` | the sound test's tunes: left / right choose (`OFF`, 00-14), fire plays the tune or, on `OFF`, stops the music (`StopMusic`) |
| `EFFECT nn` | the sound effects: left / right choose (00-29), fire plays it |
| `INPUT TEST` | an arcade-style switch test: `UP`, `DOWN`, `LEFT`, `RIGHT`, `FIRE`, `FIRE 2` (port 2) lit while held, and `KEY $nn`: the raw code of the last key pressed |
| `SPRITE TEST` | Arthur on screen in each of his 42 sprite frames (left / right) and, for frames 0-39, their mirrored copies (fire), with the frame's number |
| `BOB TEST` | (1MB of chip RAM or more only) the BOB viewer: every cached BOB strip (39 enemy, 10 small-BOB, 3 enemy-shot, 7 item / weapon strips) drawn pre-masked with one blit, as in the game; left / right choose the strip, up / down scroll it 16 lines at a time; shows the group, number, size and first line |
| `CHEAT OFF` / `ON` | the original's own cheat (lives never decrease, no harm once the armour is gone - what typing `)!(` as a high-score name turns on) |
| `EXIT` | back to the title (the music stopped) |

The input and sprite tests go back to the test page with Esc or with fire held for 3 seconds
(the BOB test with Esc). The tests' pages are drawn again when what they show changes, so the
input test follows the joystick within a few frames.

**BOB viewer** (`src/bobviewer.s`, file `FID_VIEWER`). Only machines with 1MB of chip RAM or
more (`PF_CACHE`) keep every BOB graphic in chip RAM, pre-masked; there the viewer (530 bytes)
is loaded at start-up after the caches (`VIEWER_ORG`) and `BOB TEST` appears on the test page
(`ViewerOn`). On 512K of chip RAM - with or without slow / fast expansion - the enemies' BOBs
exist only for the level being played, so the item is not shown and nothing is loaded. The
program carries only the hooks (296 bytes); the viewer is assembled against the program's
symbols (`viewer_syms.i`, written by `build_game.py`).

## Fixes

* **`MapTileAt`**: for an object far below a level the original reads its own program code as
  map cells, so what it finds depends on the program's layout; a read past the map's tables now
  finds the empty cell.
* **BOBs clipped at the top of the screen** show the right lines (the original 512K `DrawBob`
  skips twice the lines it should; the scroller's drawing does it right).
* Disk errors are retried until the read succeeds; after 8 failures the background turns red
  while it keeps trying.

## Builds

`enhanced/tools/build_game.py` (needs vasm, `vasmm68k_mot`) makes `enhanced/build/gng_game.adf`:

| Option | Builds |
|---|---|
| (none) | the game: `gng_game.adf` |
| `--raster` | the timing build: the background colour shows each stage of a frame - grey logic, red scroller edges and restores, orange text, blue BOBs, yellow copper list, green waiting for the display, black idle (`gng_game_raster.adf`) |
| `--nasty-wait` | blitter priority only while the CPU waits for the blitter (to be measured; `gng_game_nastywait.adf`) |
| `--music-rate N/D` | the 512K music package at another quality (`--music-rate 1`: full quality) |

`make_game.py` writes `src/gng_game.s` from the root `gng_main.s` (both original programs); run
it after changing `gng_main.s`, `make_game.py` or `make_game_support.s`. `make_docs.py` writes
`DISK.md` and `MEMORY.md` from the build.

The earlier enhanced builds - the original programs with the scroller patched in and loaded as a
module (`tools/build_enh.py`, `src/module.s`, `src/patches.s`) - are still here for reference;
`SCROLLER.md` describes them.

## Testing

All in a 68000 emulator (Unicorn) with a model of the blitter, copper, display and disk drive
(`tools/amiga.py`, `tools/game.py`, `tools/floppy.py`):

| Tool | Checks |
|---|---|
| `compare_game.py` | the enhanced game against the original program, same input (random play, `--teleport` to jump the camera), game state and picture every frame; `--machine 512k / 1mb / ks13 / slow / fast`; `--disk`: reading the disk image with the byteloader |
| `check_game.py` | each frame shown against the original's display code drawing the same state |
| `test_boot4489.py` | the bootblock from Kickstart's call to the program's entry (`--random-start`): booted from DF0, DF1, DF3 and from another device's unit |
| `test_drive.py` | the game's loads from the drive booted from (DF0, DF1), on 512K, 512K + slow and 1MB |
| `test_bootinfo.py` | the machine description on seven memory configurations |
| `test_jump.py` | the two jump inputs: open ground, at a ladder, on it |
| `test_menu.py` | the title menu, the test page and its sound, input, sprite and (1MB) BOB tests |
| `test_cache.py` | the file cache and the level's enemy sets, from the disk image on each machine |
| `check_harness.py` | the harness's display emulation against the level pictures (`render/out/`) |
| `sound/tools/check_music_512k.py` | the 512K music package against the original packages |

`compare_game.py` stays in step on every stage and machine; the pictures differ only in the
title's text, the frames while graphics load and one frame of the progress map, where the
originals show leftover memory.
