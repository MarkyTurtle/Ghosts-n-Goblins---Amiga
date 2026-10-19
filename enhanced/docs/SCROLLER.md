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

`PrintChar` on the playfield writes into the buffer being drawn, through the ring (8 lines
copied to a scratch area laid out like the original buffer, printed there by the original code,
copied back). Each character is also remembered for the frame; after the restore of that buffer
(`TextReplay`, from `EnhRestoreBackground`) it is printed again - the restore may have cut through
it, or the buffer been copied afresh - and gets a restore entry, so text the game stops printing
goes away two frames later, like a BOB. The in-play messages ('TAKE A KEY FOR COMING IN !') are
printed every frame, so they stay while shown. The original kept such text until its next full
redraw: the side-by-side runs show it a frame longer, or with a piece cut out where a BOB's
restore went through it, where the enhanced build shows it whole. Screens that are not redrawn
(title, high scores, game over, name entry) have no restore, so their text stays as before (201
game-over / name-entry frames compared identical in both builds).

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
| `PF_CACHE` | 1MB or more of chip RAM | graphics cached with masks in upper chip RAM (`CacheGraphics`, `BuildMaskedGfx`); one-blit BOBs (`DrawBobMasked`, `DrawSceneryMasked`); no graphics loads per level, the frame tables point into the cache; frame offsets doubled in place; progress map kept |
| `PF_MUSIC` | (with `PF_CACHE`) | the 1MB music package (assembled for `$80000`), its tunes and the extra effects |
| `PF_EVERY` | (with `PF_CACHE`) | draw every frame |

Without them (512K of chip RAM, with or without slow/fast RAM, or no machine description) it
is the 512K program. Upper chip RAM: music `$80000`, progress map `$9B400`, enemy sets
`$9D200`, small sets `$D7300`, shots `$D8D80`, items `$DB200`-`$E04D0` (checked at assembly).

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
so for the 1MB comparison the original starts with the same junk.

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
now fills the room up to `LEVEL_GFX_LIMIT` ($7F4DE, the original's end of level data) in the
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

## Next steps

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
