# Future enhancements

Ideas and planned work for an enhanced build, roughly in the order they build on each other. The
enhanced build lives in a separate source tree; the byte-identical sources here stay as they are.

## Summary of every optimisation discussed

Each line points to the item below with the details and measurements. **Closed:** an item
decided against, kept for the record with the reason.

**Loading and disk layout**
- [x] Own loader and a shared file directory file, read by both the bootblock and the game (1):
      the 4489_byteloader disk's file table at `$400` (see **Disk**)
- [x] Optional second-stage loader to escape the bootblock's 1,024-byte limit (1): not needed;
      the byteloader bootblock fits in 1 KB and copies its loader to `$7FB20`
- [x] Disk builder lays the files out itself and patches the tables (2): `build_game.py` places
      every file, writes the file table and checks each file record's length
- [x] **Closed:** zx0 compression of every file, decompressed in place (4); about 296 KB less on
      disk (5). On 512K there is no buffer space left to unpack files into (the level area
      is full with the music in), and every file already fits on the disk (about 100 KB free)
- [x] One main program for every memory size: the bootblock finds the memory and leaves a machine
      description at a known place; the program picks its features from it (`gng_game.s`) (7)
- [x] Slow / fast RAM used on machines that have it: under 1MB of chip RAM the program moves to
      the expansion at start-up (`EnhRelocate`, a relocation file made by `build_game.py`), and
      the 1MB music package goes into the chip RAM it left (7)
- [x] **Closed:** font stored without its unused bytes: 3 KB less on disk only (5); not worth
      it with the disk not full

**Display and drawing**
- [x] Double-buffered corkscrew scroller with vertical copper wrap: 3 screen buffers instead of 4,
      redraw only the new edge instead of the whole screen; no freezes when falling (3).
      Integrated into both programs (512K and 1MB) on branch `enhanced/scroll`, with a disk image;
      tested in the emulator side by side with the originals. Still to do: real-machine timing (WinUAE)
- [x] Pristine background buffer: restore BOBs from it, no save blit, no `$3000` budget (3)
- [x] Clean changes of display between a level and the progress map (bitplanes off while the
      screens are rebuilt, switched in the vertical blank), and the loading picture no longer
      overwritten on 1MB before the copyright screen (branch `enhanced/display`, merged; tried in WinUAE)
- [x] Raster-time debug build (COLOR00 per stage), then drawing every frame (50 fps instead of
      the game's 25) on the 512K program too: 50 fps on an A500 except in busy scenes (25 fps
      there); see `enhanced/docs/SCROLLER.md`, *Frame rate*
- [x] One-plane BOB masks made at level load on 512K (7 blits per BOB -> 5, about a quarter less
      blitter work); see `enhanced/docs/SCROLLER.md`, One program for every machine
- [x] Pre-masked (one-blit) images on 512K as far as each level's memory goes: shots, small
      BOBs, the dragon, items, then the other sets (stages 4 and 7: every image); see
      `enhanced/docs/SCROLLER.md`
- [x] Look-ahead column: the next column built a few tiles a frame in the spare column's
      memory, so a crossing no longer draws a whole column in one frame (`ScrPrepare`)
- [x] Playfield text: queued and drawn once a frame from a glyph cache straight into the ring;
      name entry keeps the background (key message ~11x less CPU, title 3x, name entry ~3x)
- [x] Look-ahead rows (the ring's spare tile row): `ScrPrepareRow`
- [x] **Closed:** keep busy scenes at 50 fps on an A500 with a copper-driven blit queue (an
      interrupt per blit costs about as much as it saves on a 68000). In WinUAE with the 512K
      music the A500 slows only briefly, at the dragon's stages, and hardly noticeably
- [x] Fold the scroller into the game source (`enhanced/src/gng_game.s`, `scroller.s`)
- [x] BOB masks: one-plane masks on 512K; fully pre-masked graphics for one-blit BOBs on 1MB (3)
- [x] **Closed:** blitter priority only while waiting (`--nasty-wait`): not pursued, little to
      gain (the build option stays, for a timing build)
- [x] **Retired:** `tools/test_scroll.py` and `tools/test_bobs.py` and their test build
      (`scroll_test.s`, which no longer assembled since the scroller was folded into the game):
      `compare_game.py` and the features' own tests cover the scroller and the BOBs now
- [x] Draw at 50 fps once the redraw cost is gone (3): see above

**Disk**
- [x] An AmigaDOS-format disk (880K ADF) with a file table, loaded with the 4489_byteloader
      by the bootblock and the game (made on branch `enhanced/byteloader`, merged)
- [x] Boot from any drive (the boot IORequest's unit) and load from it (5): the bootblock finds
      the unit and passes it on in the machine description (version 2); the bootblock's and the
      game's loads read it (branch `enhanced/bootdrive`, merged; tried in WinUAE: A500+ 2.04,
      A600, A1200 from DF1; Kickstart 1.3 boots only from DF0)

**Memory**
- [x] Per-level map tables: each level's `BlockTiles` / `CellTiles` entries in a file of its
      own (`LoadLevelTables`): 17 KB less resident, the program 77 KB instead of 110 KB
- [x] 512K: the old background save areas: the small BOBs and the progress map load into the
      screens, the MFM buffer is at the top of the level area (the first screen while the
      progress map loads); a trace of every `LoadFile`. The screens come 24 KB lower
- [x] Remove the original routines the scroller replaced and the debug routines (`drop_dead_code`,
      make_game.py): 3 KB
- [x] **Closed:** per-level `TileAttr` banks (5). Measured with the cells round each level's
      edges (what `MapTileAt` can read): levels 0, 1, 3 and 4 use all four banks, and level 1
      (stage 2, the fullest) 680 different records, too many for a byte index, so the stages
      that need memory would gain nothing
- [x] **Closed:** the zone, spawn and placement tables per level (4): 3,170 bytes for all
      levels, so stage 2 would gain at most about 2 KB, for moving tables full of pointers
- [x] The level's enemy graphics only (4): `LoadEnemySets` reads just the level's BOB sets
      from the enemy graphics file (22-65 KB of its 118 KB), each to its place, sets less than a
      track apart as one piece; per-level files would not fit on the disk (about 330 KB). A
      level start reads 8-16 fewer tracks (25-59%). See `enhanced/docs/SCROLLER.md`, *Loading
      less, and the file cache*
- [x] File cache in spare memory (4): with the program moved to slow / fast RAM, the enemy
      graphics, small BOBs, progress map and the levels' tile and table files are kept after
      their first load (a level loaded again reads no track); with 1MB of chip RAM or more, the
      levels' tile and table files, in the chip RAM above the graphics caches or in slow / fast
      RAM (`CacheInit`, `LoadFile`)
- [x] **Closed:** drop mirrored enemy frames (39% of the enemy graphics) and flip them when the
      frame cache builds them: about 24 KB less on level 5 (5). Flipping at run time would cost
      too much frame time
- [x] **Closed:** mirror Arthur's current frame on demand instead of keeping 40 mirrored frames:
      about 20 KB (5); not needed
- [x] **Closed** (not worth it, measured: metatile recoding of the map tables, flip flags for level tiles,
      trimming sample tails) (5)

**Sound**
- [x] Music on 512K machines with an expansion (slow or fast RAM): the whole 1MB package, in the
      chip RAM the program moved out of
- [x] Music on a plain 512K A500 (made on branch `enhanced/music512`, merged; tried in WinUAE on A500, A500 + 512K, A500+, A600 and A1200): a combined package
      (`sound/gng_music_512k.s`: the 512K effects with the 1MB tunes, 75.5 KB) in the room freed
      by the per-level map tables, joined gaps, old save areas and dead code; stages 1, 2, 3, 5
      and 6 pre-mask fewer BOB sets, and about 7 KB is left on the fullest stage
- [x] Music quality tiers chosen by the machine's memory (4): the 512K package (plain 512K
      A500) has the tunes' samples at 3/4 of their rate, chosen from listening to 3/4, 2/3
      and 1/2; machines with 1MB of chip RAM or an expansion keep full quality. A menu choice
      cannot free memory (the layout is fixed at build time). The 8.2 KB saved goes to
      pre-masking (made on branch `enhanced/musicquality`, merged; tried in WinUAE)
- [x] Resample the music samples by scaling the instruments' period multipliers (5): done at
      3/4 for 512K (`make_music_512k.py --rate`). The resampled samples' lowest periods rise from
      114 to about 152, within Paula's minimum of 124; the waveform samples 0-1 (not resampled)
      still go down to about 120
- [x] **Closed:** effects: at most a modest cut (they already play at their recorded 8-10 kHz) (5)

**Controls and extras**
- [x] Two-button joysticks: one button fires, the other jumps; up-to-jump kept as an option (8):
      the title menu's INPUT item (or J) switches it (`JumpButton`); see
      `enhanced/docs/SCROLLER.md`, *Two-button joysticks* (made on branch `enhanced/joystick`,
      merged; tried in WinUAE)
- [x] A title menu instead of the instructions: PLAYER 1 START, PLAYER 2 START, INPUT (the jump
      setting), TEST MENU (the memory line and the cheat, moved from the title) (8); see
      `enhanced/docs/SCROLLER.md`, *The title menu* (made on branch `enhanced/titlemenu`,
      merged; tried in WinUAE)
- [x] A sound test on the test page: play each tune and effect (8); MUSIC (OFF, 00-14) and
      EFFECT (00-29), fire plays, MUSIC OFF stops the tune (made on branch `enhanced/testmenu`, merged)
- [x] A sprite test on the test page (8): Arthur's 42 sprite frames and their mirrored copies;
      the enemies' BOB sets are not shown (on 512K only the level's sets exist, and BOBs are drawn
      by the play loop)
- [x] A BOB viewer on the test page (`BOB TEST`), on machines with 1MB of chip RAM or more only:
      every cached, pre-masked BOB strip drawn with `ScrDrawBob`; its own file (`FID_VIEWER`)
      loaded after the caches (branch `enhanced/testmenu`, merged). Not on 512K chip machines (with or
      without an expansion): their BOB graphics are only the level's
- [x] An input test on the test page, as on an arcade machine (8): the joystick's directions and
      both buttons lit while held, and the last key's raw code

**Testing**
- [x] Boot and timing tests of the disk image and the enhanced builds in a full emulator (6):
      the emulator harness boots the disk (`test_boot4489.py`); WinUAE runs on A500, A500 +
      512K, A500+, A600 and A1200
- [x] Before building: a full chip-RAM budget for the enhanced 512K build (4): `build_game.py`
      checks the layout and prints each stage's level data and pre-masking at every build

## 1. Shared file directory loaded from disk (own loader)

**Goal:** replace the file tables built into the bootblock and both main programs with one
directory file on the disk. The bootblock and the game both load it and use it, so files can be
moved, resized or added by rebuilding the directory alone, without reassembling the programs.

**Where things stand now**

* The bootblock hard-codes three loads (`move.w #track,$28.w` / `move.l #length,d5`): the loading
  screen (track 1, `$18300` bytes) and the main program (`$18A80` bytes from track 110 for 512K, or
  track 17 for 1MB). See `gng_boot.s` at `$0BA`, `$0CE`, `$14E`, `$172`, `$17C`.
* Each main program has its own `FileTable` (`FENTRY dest,length,track`, 17 entries).
  `LoadFile` takes a pointer to an entry in `a1`; `LevelFileIndex` picks the level tile files.
  The two builds' tables differ only in load addresses (the 1MB build loads most files to the
  `$80` staging area).
* `tools/disk/mkdisk.py` already reads all of this to lay out the disk.
* Loader state lives at `$28-$2E` (`LDR_TRACK`, `LDR_CYL`, `LDR_RETRY`, `LDR_DIRFLAG`).

**Proposed design**

* **Directory file** on a fixed, known track. It must be a track the bootblock can find without a
  table, e.g. track 132 (unused today), or track 1 with the loading screen moved up. Format sketch:
  * header: magic (`'GNGD'`), version word, entry count;
  * entries of `id.w, track.w, length.l, dest512.l, dest1mb.l, flags.w`. Keep a `track.w, length.l`
    pair that `LoadFile` can use directly, or adapt `LoadFile` to the new entry layout;
  * a checksum over the whole directory.
* **Bootblock:** load the directory first (one track) to a fixed address that both builds leave
  alone (to be checked against the memory maps in `docs/GLOBALS.md`). Then take the loading
  screen and main program entries from it instead of immediates. Space is tight: the bootblock is
  1,024 bytes with code and data up to about `$3A8`. The loading-screen palette's unused trailing
  zero words could be reclaimed.
* **Game:** replace `lea FileTable(pc)` / `LevelFileIndex` lookups with a lookup by file id in the
  loaded directory (keep a pointer in a spare global, e.g. a new `g_FileDir`). Pick `dest512` or
  `dest1mb` by build. Leave `LoadFile` itself unchanged if the entry layout allows it.
* **Own loader (optional):** a second-stage loader file, loaded by a minimal bootblock, would free
  the bootblock's space limit. It could also hold the directory code and better error handling
  (retries, a "insert disk" message).
* **Tools:**
  * `mkdisk.py` gains a layout spec (JSON or YAML: file id, source path, load addresses, optional
    fixed track). It packs the files onto tracks, writes the directory and builds the image.
  * The current table reader stays as a check that the original disk is reproduced.
* **Verification:** both builds must boot and load every level in an emulator (see 6), and the
  original layout must still be reproducible as a regression check.

**Open questions**

* Fixed address for the directory in both builds (chip RAM, not overwritten by screens / caches).
* Whether to keep byte-identical original sources alongside a modified "mod" build (e.g. an
  assembler flag `ORIGINAL=1` in the sources).

## 2. Automatic layout with patching (step 3 of the disk builder)

A simpler alternative to 1 that needs no new loader: let `mkdisk.py` lay the files out itself and
patch the new lengths / tracks into both `FileTable`s and the bootblock immediates (then
recompute the bootblock checksum). This changes the binaries whenever a file changes size, so it
would be opt-in.

## 3. Incremental scrolling: double-buffered corkscrew with a pristine buffer

**Goal:** replace the full-redraw scrolling with incremental scrolling, to cut memory use and,
more importantly, the scrolling cost.

**Integrated (branch `enhanced/scroll`, `enhanced/docs/SCROLLER.md`).** The scroller, the
pristine buffer and the BOBs now run in the 512K game (a module loaded from its own track plus
in-place patches), with a disk image to try. The first prototype's findings:

The background part works:
a module that draws one tile column / row at a time, with a vertical ring and copper wrap,
matches the original display at every camera position tested (560 frames, all levels), in an
emulator harness that adds blitter, copper and display emulation. What it showed:

* **The corkscrew works with the line-interleaved layout.** A plane's fetch runs into the start of
  the next plane's row, whose own column has just scrolled off the left - which is where the new
  column is drawn. So a tile stays one blit, as in the original.
* **Measured memory:** 3 buffers of 47,120 bytes (with 1,040 bytes of corkscrew slack) = 141,360
  against 184,320: about 43 KB saved.
* **Cost:** a new column is about 15 tile blits (1,200 words) against the original's 288-blit,
  23,040-word redraw plus a 46 KB CPU copy.
* **Masks:** both schemes below still work with this layout. On 512K, one-plane masks (+20%) with 5
  cookie-cut blits per BOB; on 1MB, fully pre-masked graphics with one blit.

**Where things stand now** (512K build; see README *Scrolling* and `tools/verify/camera.py`)

* Four full screen buffers, `SCREEN_0`-`SCREEN_3`, each `$B400` bytes (288 x 256, 5 planes,
  line-interleaved, 180 bytes a line): 184,320 bytes, over a third of chip RAM. Two are the
  displayed front / back pair; the other two receive a complete redraw around the next 16-px tile
  origin.
* `RedrawScreen` redraws the whole playfield (about 14,600 instructions and 288 blits) and runs
  almost all the time. Hardware fine scroll covers up to 16 px until the switch. When falling, the
  camera outruns the redraw and `g_SkipLogic` freezes the game logic (short freezes).
* BOBs save the background under them each frame (`g_SaveBufA` / `B`, `$3000` bytes each, in the
  graphics load buffers) and restore it next frame. A BOB that would overflow the `$3000` budget is
  not drawn that frame.
* `SCREEN_0` doubles as the load / unpack area for the 118 KB enemy graphics file (tracks 38-56)
  at every level start in the 512K build. Any memory freed must still leave a staging area for
  that (or the file must be loaded in parts).

**Proposed design**

* **Horizontal: corkscrew.** One buffer per displayed screen, 288 px wide (272 shown + one 16-px
  column), with a few spare lines. Scrolling 16 px moves the bitplane pointers on 2 bytes, so the
  picture "corkscrews" one line down every full buffer width. Only the new 16-px column is drawn:
  16 tiles. The spare lines needed grow with the level width: up to 32 cells x 256 px / 288 px,
  about 29 lines (5 KB). Alternatively, wrap with a copper split.
* **Vertical: ring buffer with a copper split.** Vertical scrolling (levels 4-6 especially, and
  falls) moves the start line. At the buffer's end the copper reloads the bitplane pointers with
  the buffer start, so only the new 16-px row is drawn (17 tiles). BOBs that straddle the wrap line
  must be split into two blits (`DrawBob` clipping).
* **Double buffering:** two display buffers, as now, each updated with the new column / row when
  its own scroll position reaches it.
* **Pristine buffer:** a third buffer with the same scroll scheme holding only the background
  (tiles and the shootable scenery that `DrawSceneryOnRedraw` draws today). New edges are drawn
  into it once and copied to the two display buffers. Restoring under a BOB becomes one copy from
  the pristine buffer. This removes the save blit per BOB, the save areas and the `$3000` budget,
  so BOBs are no longer dropped.
* **Full redraws** remain only for camera jumps (level start, checkpoint, restart).

**Expected gains (to be measured)**

* Memory: three buffers of about 46-50 KB instead of four of 45 KB, roughly one buffer (about
  45 KB) saved, plus the save areas no longer needed. That depends on how much vertical margin and
  corkscrew slack is needed, and on keeping a staging area for the level-start load.
* CPU / blitter: per 16 px of scroll, about 16-17 tile blits (times 1 draw + 2 copies) instead of
  a 288-blit full redraw. No more `g_SkipLogic` freezes; probably enough headroom to consider
  drawing at 50 fps instead of 25.

**Risks / work involved**

* This touches most of the display code: `RedrawScreen`, `CameraJump` / `SwapScreens`, the copper
  lists (a split per buffer), `DrawBob` / `RestoreBackground` clipping and addressing,
  `DrawSceneryOnRedraw`, the HUD strip and the progress map.
* Scenery that changes (gravestones shot away, platforms) must be updated in the pristine buffer
  as well as on screen.
* Combining the horizontal corkscrew drift with the vertical wrap point needs care: the wrap line
  moves with the corkscrew.
* Like item 1, this is a modified build: it will live in a separate source tree, leaving the
  byte-identical original sources alone.

**Graphics format and BOB blits**

* The screen, the tiles (160 bytes per 16 x 16 tile) and the BOB graphics are already
  line-interleaved (5 planes per line), so a tile is one blit (height 16 x 5).
* BOBs differ by build:
  * The 512K build stores no masks. Each BOB costs 8 blits: save background, 2 blits to build a
    one-plane mask (OR of the planes), then 5 cookie-cut blits, one per plane. A single-plane mask
    can't be reused for every plane line in one blit, because the blitter modulo can't repeat a
    line 5 times and then move on.
  * The 1MB build converts the graphics at load time (`BuildMaskedGfx`) into a copy with a mask
    line after every plane line. That doubles their size (every frame offset doubles), but each
    BOB is then 2 blits: save background and one cookie-cut blit.
* For the new tree: adopt the 1MB approach (converted at load time, so the disk files stay as
  they are). With the pristine buffer the save blit goes too: restore from pristine, then 1
  cookie-cut blit.
* The cost is memory: about twice the BOB graphics in use (the 118 KB enemy file becomes about
  236 KB if all of it is cached, as the 1MB build does). That suits 1MB machines.
* On 512K, full pre-masking of every set a level uses costs up to 65 KB more and does not fit
  alongside the music (see the budget in item 4). Instead, build the masked copies on demand and
  cache only what is in use (below). The simple fallback is a one-plane mask per frame (+20%, at
  most 13 KB) with the 5 per-plane blits, which still saves the 2 mask-building blits per BOB.

**On-demand masked graphics cache (for 512K)**

Different parts of a level have different enemies, so not every set needs a masked copy at the
same time. `tools/budget/enemy_windows.py` estimates, for every camera cell of each level, which
graphics sets can be on screen within one cell (256 px) either way. It uses the zone spawners and
placed enemies there, plus the rules in the code: a Blue Killer turns into a Red Arremer,
gravestones release the Magician, the Crow's set depends on its param, and bosses / Red Arremer /
Big Man keep running once started. These are estimates from the tables, not play traces.

| Level | All sets, masked (x2) | Peak within +-1 cell, masked | Peak within +-2 cells, masked |
|---:|---:|---:|---:|
| 0 | 129,220 | 59,800 | 62,040 |
| 1 | 111,900 | 67,520 | 84,080 |
| 2 | 88,040 | 63,320 | 69,400 |
| 3 | 55,880 | 46,920 | 55,880 |
| 4 | 98,640 | 74,460 | 98,640 |
| 5 | 126,020 | 117,380 | 126,020 |
| 6 | 44,840 | 40,960 | 40,960 |

* **Caching whole sets by area** halves the need on the spread-out levels (0-2). On the compact
  levels (4, 5) almost every enemy type is close by, so level 5 still peaks at about 117 KB:
  50+ KB more than the unmasked sets need today. Area-based caching of whole sets is not enough
  for 512K.
* **Caching individual frames** should be. An enemy only uses a few frames at a time (a walk
  cycle, an attack), so keep a fixed-size pool (say 24-32 KB) of fully masked frames, keyed by
  (set, frame), with least-recently-used eviction. On a miss, build the frame with the blitter:
  * one blit copies the 5 plane lines into the cache entry, leaving the mask lines empty (the
    destination modulo skips them);
  * two blits build the mask (OR of the planes, as the 512K `DrawBob` does today);
  * the mask is copied into each plane's mask line, about 5 more blits, or with the CPU.

  That is roughly the cost of one draw in the 512K build today, paid once while the frame stays in
  use. After that every draw is one cookie-cut blit (plus the restore from the pristine buffer).
* A typical 32 x 32 frame is 640 bytes, 1,280 masked, so a 32 KB pool holds about 25 frames. The
  pool size, the hit rate and the number of misses per frame (spread misses over frames, or
  pre-build when a spawner starts) need measuring in a full emulator with real play (item 6).
* The same cache works for the enemy-shot and effect graphics, which are drawn the same way.
* Prototype first in the emulator harness (`tools/verify/emu.py`) for addressing, then confirm
  timing in a full emulator (item 6).

## 4. Compression, per-level files, caching and music on 512K

**Goal:** zx0-compressed files, level data in per-level files, a file cache on 1MB machines,
and enough chip RAM freed to play the music on 512K machines.

### Measurements

Made with `tools/budget/level_sizes.py` and `sound/tools/tune_samples.py`.

**Chip RAM in the 512K build today** (from `gng_equates.i`; the A500's 512 KB is all chip RAM):

| Range | Bytes | Use |
|---|---:|---|
| `$00000-$00080` | 128 | exception vectors |
| `$00080-$18B00` | 100,992 | main program, including all levels' map / tile tables and the globals at `$1898C` |
| `$18B00-$1A118` | 5,656 | work areas (to be itemised) |
| `$1A118-$1A298` | 384 | copper lists |
| `$1A298-$1DE34` | 15,260 | enemy-shot, weapon and effect BOBs |
| `$1DE34-$28234` | 42,000 | Arthur's sprite frames, normal and mirrored |
| `$28234-$28E54` | 3,104 | font |
| `$28E54-$30BB8` | 32,100 | sound driver + 30 effects |
| `$30BB8-$311E8` | 1,584 | sprite DMA data (HUD) |
| `$311E8-$37468` | 25,216 | small BOBs, the two `$3000` background save areas, MFM track buffer, mask buffer |
| `$37468-$64468` | 184,320 | four screen buffers |
| `$64468-$65548` | 4,320 | top strip / clear area |
| `$65548-$80000` | 109,240 | the level's tile file, then its enemy BOB sets |

The last region is nearly full: level 1 needs 49,440 + 55,950 = 105,390 bytes, leaving 778.

**Per level** (`tools/budget/level_sizes.py`):

| Level | Map / tile tables used | Tile file | Enemy BOB sets | Pre-masked (x2) | One-plane masks (+20%) |
|---:|---:|---:|---:|---:|---:|
| 0 | 5,496 | 29,760 | 64,610 | 129,220 | 12,922 |
| 1 | 10,264 | 49,440 | 55,950 | 111,900 | 11,190 |
| 2 | 10,584 | 21,600 | 44,020 | 88,040 | 8,804 |
| 3 | 4,288 | 18,560 | 27,940 | 55,880 | 5,588 |
| 4 | 5,480 | 10,080 | 49,320 | 98,640 | 9,864 |
| 5 | 3,840 | 10,720 | 63,010 | 126,020 | 12,602 |
| 6 | 568 | 6,560 | 22,420 | 44,840 | 4,484 |

All levels' tables are resident today: `CellTiles` 26,368 + `BlockTiles` 6,656 + `TileAttr` 8,192 =
41,216 bytes. Per-level files would keep at most 10,584 (level 2), saving about **30 KB**. Spawn,
zone and placement tables (a few KB) would move too.

**Done (per-level map tables):** `BlockTiles` and `CellTiles` now come from a file per level
(`enhanced/docs/SCROLLER.md`, *Per-level map tables*). The estimate above counted only the
level's own cells; a level also reads the cells round it and some bytes past the map, so the
largest level needs 49 cells and the saving is about 17 KB, not 30. `TileAttr` (8 KB) is still
resident.

**Music** (`sound/tools/tune_samples.py`, which follows each tune's patterns to its instruments,
and counts the samples their lengths run into when they overrun):

* The 1MB package is 111,508 bytes, of which 97,690 are samples: 63,254 used by the effects and
  34,314 by the tunes. No sample is shared between the two groups (sample 4, 116 bytes, is used
  by neither).
* The level tunes (2, 12, 13) each use samples 5-9 (32,756 bytes), and most other tunes use 5, 7
  and 8 (26,314). Splitting the music per tune therefore saves almost nothing: load all the tune
  samples together.
* The 512K package already has the driver and its own, shorter effect samples (27,206 bytes). So
  music on 512K needs only **the tunes' samples plus their voice data: about 34.3 + 9 = 43 KB**,
  not the 79 KB of the whole 1MB package. The 17 effects that sound different in the 512K build
  would stay as they are. Using the 1MB effects as well would cost another 36 KB.

### Budget for an enhanced 512K build (estimates; check once the code exists)

| Change | KB |
|---|---:|
| Corkscrew + pristine buffer (item 3): 3 buffers instead of 4, less the corkscrew slack (measured layout) | +43 |
| Per-level map / tile tables instead of all levels | +30 |
| Background save areas no longer needed (pristine restore); the MFM buffer and small BOBs stay | +8 |
| Music: the tunes' samples and voice data, added to the 512K package | -43 |
| One-plane BOB masks (worst level) | -13 |
| **Margin** | **about +25** |

Full pre-masked BOBs as in the 1MB build (up to +65 KB on level 0) do **not** fit alongside the
music on 512K. Use one-plane masks there (the 13 KB in this budget, or less with an on-demand mask
cache); keep full pre-masking for 1MB machines.

### Design

* **zx0** for every file (**closed**: no buffer space left on 512K to unpack into, and every file fits on the disk). The decompressor is small, and zx0 can decompress in place (packed data
  at the end of the destination with a small safety margin), so no staging buffer is needed.
  Decompression should be well ahead of floppy speed (about 6 KB per track), so loads get shorter
  and faster (to be measured on a 68000). Samples are unpacked once into chip RAM; packing them
  only saves disk space and load time.
* **Per-level files:** one file per level with its tiles, the cells / block tiles / attributes it
  uses, its map rows, zones, spawn scripts, placement lists and its enemy BOB sets. The main
  program keeps only common code and data. This also ends the 118 KB load of all enemy graphics
  into a screen buffer at every level start, and makes levels easy to edit or add (ties in with
  the file directory in item 1).
* **1MB cache:** keep the compressed files in expansion memory after the first load and decompress
  into chip RAM at each level start, so the disk is read only once. Slow (trapdoor) RAM is fine for
  the cache, since only the CPU reads it; anything the blitter or Paula use is unpacked into chip
  RAM. On 1MB machines, also pre-mask the BOB graphics fully and use the 1MB effect samples.
* **512K music package:** build a combined package from the symbolic sources: the 512K driver and
  effects, plus the 1MB tunes, their instruments and samples 0-3 and 5-9. Renumber the instruments
  and keep each sample's neighbours where an instrument overruns into them (the overrun tails are
  part of the sound; see `sound/SOUND.md`), or fix the lengths deliberately.

### Music quality tiers

Build several versions of the music file from the same symbolic sources and load the one the
machine has room for (chosen at start-up from the detected memory, through the file directory of
item 1). The driver is the same in every tier; only the samples and the instruments' lengths and
period multipliers differ, so a script can generate the tiers by resampling and rescaling.

| Tier | Machine | Effects | Music samples | Approx. samples in chip RAM |
|---|---|---|---|---:|
| 0 | 512K, tight | 512K effects (shorter, 27 KB) | none (effects only, as the original 512K build) | 27 KB |
| 1 | 512K | 512K effects | resampled to 2/3 (about 23 KB) | 50 KB |
| 2 | 512K with room to spare | 512K effects | full rate (34 KB) | 61 KB |
| 3 | 1MB | 1MB effects (63 KB) | full rate (34 KB) | 97 KB |

Plus about 9 KB of note data and instruments for every tier that has music. Notes:

* The samples must be in chip RAM to play, so on 1MB machines (where the extra memory is usually
  slow or fast RAM) tier 3 still uses chip RAM. It fits there because the screens and graphics
  sizes are the same and the 1MB build already does this today.
* A player option could pick a lower tier to free memory for the frame cache.
* The resampled tiers can also fix the instruments played at periods below 124.
* Each tier can be rendered to WAV with the real driver (`sound/tools/sndemu.py`) and compared by
  ear before it is used.

### Still to measure

* The `$18B00-$1A118` work areas, the corkscrew slack and the vertical margin, so the screen saving
  is exact.
* zx0 ratios for each file, and decompression speed on a 7 MHz 68000.

## 5. Further space savings (measured)

### Where the bytes are

Disk files, with their size compressed by zx0 (`zx0` from github.com/einar-saukas/ZX0, optimal
mode) as a guide to the disk space a packed version would take:

| Group | File | Bytes | zx0 | Resident in 512K RAM |
|---|---|---:|---:|---|
| Code | bootblock | 1,024 | 700 | at boot only |
| | main program, 512K | 100,992 | 45,894 | always |
| | main program, 1MB | 100,992 | 45,903 | (1MB only) |
| Graphics | loading screen (HAM) | 99,072 | 87,386 | at boot only |
| | Arthur's sprites | 21,504 | 9,185 | always, plus 20,480 of mirrored copies built at start-up |
| | enemy BOB sets (21) | 118,850 | 68,704 | the level's sets (22-65 KB) |
| | weapon / effect BOBs (2 files) | 10,600 | 6,277 | always |
| | enemy shot BOBs | 4,660 | 2,258 | always |
| | small item / scenery BOBs | 3,360 | 1,862 | always |
| | font | 6,208 | 2,202 | 3,104 (every other byte) |
| | progress map (RLE) | 7,516 | 4,467 | between levels |
| | copyright screen (RLE) | 9,726 | 5,308 | at boot only |
| Level tiles | levels 0-6 (7 files) | 146,720 | 88,010 | the level's file (6.5-49 KB) |
| Sound | driver + effects, 512K | 32,100 | 26,657 | always (27,206 of samples) |
| | driver + music + effects, 1MB | 111,508 | 83,654 | (1MB only; 97,522 of samples) |
| **All** | | **774,832** | **478,467** | |

zx0 saves about 38% overall: a lot on code and tables (55%) and BOB graphics (40-55%), little on
the HAM picture (12%) and the samples (17-25%).

The 512K main program (`tools/budget/program_breakdown.py`):

| Part | Bytes |
|---|---:|
| Code (every traced instruction, including routines nothing calls) | 42,452 |
| Map & tile tables (`CellTiles`, `TileAttr`, `BlockTiles`, profiles, `WorldMap`) | 42,702 |
| Animation & movement scripts | 4,608 |
| Spawn & placement tables | 3,170 |
| BOB frame and size tables | 1,946 |
| HUD / icon graphics, palette | 1,624 |
| Copper template, file table, hunk header | 1,044 |
| Box / hit tables | 886 |
| Text | 705 |
| Level / score tables | 450 |
| Other data | 1,405 |

### Options

**1. Drop mirrored enemy frames (biggest saving).** 46,120 of the 118,850 bytes of enemy graphics
(39%) are exact mirror images of another frame in the same set: the left- and right-facing poses
(`tools/budget/gfx_redundancy.py`; Astaroth 10,240, Unicorn 5,760, Satan 5,460, Red Arremer
4,560 ...). Keep one of each pair and build the other when the frame cache (item 3) misses. The
blitter can't mirror, so the CPU flips it with a byte bit-reverse table (`BitReverseTable` already
exists). That is about 640 table lookups for a 32 x 32 frame, paid once per cache miss. This saves
about 39% of each level's resident enemy graphics, for example about 24 KB on level 5, and the
same on disk.

**2. Mirror Arthur on demand.** Start-up builds mirrored copies of Arthur's frames 0-39: 20,480
bytes of chip RAM. Arthur is one frame (4 sprites, 512 bytes) at a time. Mirroring the current
frame into a small double-buffered sprite area when the frame or facing changes saves about 20 KB.
The cost is roughly 512 table lookups per change, a noticeable but bounded part of a frame; to be
measured.

**3. Map tables.** Per-level files (item 4) already cut the resident 41 KB to at most about
10.6 KB. Recoding `CellTiles` as metatiles shrinks all levels' cells only from 26,368 to about
17,000 bytes (933 distinct 2 x 2 blocks), and `TileAttr` has 862 records in use (831 distinct).
After per-level files the gain is a few KB, so this is not worth the extra decoding.

**4. Level tiles.** Only level 0 has many mirrored tiles (36 of 186). A flip flag would need the
CPU at draw time for little gain; zx0 already takes the tile files from 146,720 to 88,010 bytes
on disk.

**5. Samples.** `sound/tools/sample_rates.py` runs the real driver through every tune and effect
and records the rate each sample is actually played at:

* **Effects** are played at their recording rate, 8-10 kHz. Resampling them is directly audible:
  halving gives 4-5 kHz and sounds muffled. At most a modest cut (3/4 saves about 6.8 KB of the
  512K effects), checked by ear.
* **Music samples** (recorded at 14 kHz) are played at a median of 12-14 kHz and up to 31 kHz on
  high notes. Resampling them to 2/3 (about 9.4 kHz) saves about 11.4 KB of the 34.3 KB; halving
  saves about 17 KB but dulls them more.
* **How the driver allows it:** each instrument has a period multiplier (period = `PitchTable` x
  multiplier >> 16). Resampling a sample by a factor f means dividing the multiplier by f. The
  multipliers in use are at most `$8080`, so x1.5 always fits in a word; x2 fits except for the
  `$8000` / `$8080` instruments, whose notes would instead move down an octave (48 pitch steps).
  Attack / loop lengths shrink by the same factor.
* **A bonus:** the tunes play samples 0, 1, 5, 7 and 8 at periods down to 114, below the 124 that
  the Hardware Reference Manual gives as the minimum for audio DMA. Resampling those instruments
  also brings their periods back into range.
* **Checking:** the sound tools can render each tune and effect to WAV with the real driver, so a
  resampled package can be compared by ear with the original before it goes into the game.
* Sample tails are not padded (under 110 bytes of near-silence in all), so trimming gains nothing.

**6. Disk-only savings** (no RAM effect, but fewer tracks and faster loads):
* zx0 everything (about 296 KB less over all the files).
* The disk carries two full main programs (512K and 1MB, 100,992 bytes each). One program built
  for both, choosing its memory layout at start-up, saves 100 KB of disk.
* The font file stores every other byte unused (3 KB).

### Rough total for an enhanced 512K build

On top of the budget in item 4: dropping mirrored enemy frames (about 24 KB on level 5),
mirroring Arthur on demand (about 20 KB) and resampling the music to 2/3 (about 11 KB) together
free roughly 50-55 KB more. That turns the tight margin of item 4 into a comfortable one, with
room for full-quality effects or a larger frame cache.

## 6. Boot and timing tests in a full emulator

* Boot `gng.adf` from `mkdisk.py` in WinUAE / FS-UAE (512K and 1MB configurations) to confirm the
  extended ADF loads, including track 0 stored as an AmigaDOS track. Not yet tested: no Kickstart
  ROM is available in the build environment.
* Measure the documented timing behaviour: 25 fps drawing, redraw cost, and the short freezes
  while falling (`g_SkipLogic`).

## 7. One program for every memory size

Today there are two main programs on the disk (512K at track 110, 1MB at track 17), and the
bootblock picks one with a rough test (`$4.w` - ExecBase - above 512K, or the stack above
`$80000`). The two differ in about 190 places (the `ifd BUILD_1MB` blocks of `gng_main.s`, which
on `main` now assembles both programs: 21,580 lines of code shared, about 640 512K-only and 680
1MB-only), all of which come down to memory:

| | 512K program | 1MB program |
|---|---|---|
| Code | at `$80`, absolute addresses | anywhere: position independent through `g_BaseAddr` |
| Enemy graphics | reloaded from disk for each level | loaded once, cached with masks (`BuildMaskedGfx`) |
| BOB drawing | 2 mask blits + 5 plane blits | one blit (pre-masked) |
| Progress map | reloaded each time | cached |
| Sound | effects only (32 KB package) | music and effects (111 KB package), `PlayMusic` |
| Drawing | every other frame (25 fps) | every frame (50 fps) |
| Screens, HUD, copper, sprites | `$37468`-`$65548` | `$80`-`$2E914` |

**Plan**

* **Bootblock: describe the machine.** *Done on `enhanced/scroll`: `enhanced/src/boot_patches.s`
  leaves a 32-byte description at `$7FB00` (layout in `enhanced/docs/SCROLLER.md`), the title
  screen shows it; tested on six fake memory lists, not yet on real Kickstarts.* Kickstart is still running when the bootblock starts, so
  instead of guessing it can walk exec's memory list (`ExecBase->MemList`: each MemHeader gives
  the type - chip, fast; slow RAM at `$C00000` shows up as fast without DMA - its start and end).
  It writes a small block - say `'GNGM'`, version, chip size, then up to 4 (start, size, type)
  regions, PAL/NTSC, CPU type from `AttnFlags` - at a well-known address before taking the
  machine over. Candidates: `$100`-`$1FF` (the user interrupt vectors, unused on the Amiga), or
  a reserved block at the start of the loaded program file (then it moves with the program and
  nothing else can overwrite it). Space in the bootblock is tight (code and data up to about
  `$3A8` of 1,024 bytes); the own-loader idea in item 1 would lift that limit, and the machine
  block fits naturally next to the shared file directory there.
* **One program, position independent** (start from the 1MB source: it already is). At start-up
  it reads the machine block and chooses a profile, with the addresses of every buffer computed
  into globals instead of equates:
  * *512K chip only*: today's 512K layout and behaviour (graphics reloaded per level, effects
    only, 2-pass masks or the one-plane masks / on-demand cache of item 3).
  * *512K chip + 512K slow RAM* (the most common expanded A500): code, level data, collision
    tables, the progress map cache and the music sequences in slow RAM; everything the blitter,
    copper, sprites or audio DMA read (screens, graphics, masks, samples) in chip RAM. The
    original 1MB program cannot use this machine properly (its masked graphics would land in
    slow RAM, which the blitter cannot read); a merged program can.
  * *1MB chip (or more)*: today's 1MB behaviour.
  * Fast RAM (A1200 / accelerators) treated like slow RAM.
* **Feature switches from the profile**, not from the build: masked-graphics cache, music
  quality tier (item 4), 50 / 25 fps drawing, file caching (item 4). The scroller module
  (`enhanced/`) already builds both ways from one source (`BUILD_1MB`); the assemble-time switch
  becomes a runtime one (two ScrDrawBob variants behind a pointer).
* **Disk:** one main program instead of two (about 100 KB less), loaded where the bootblock
  chose; the 1MB music package and the 512K effects package both stay, picked by profile.
* **Order:** *One source for both builds: done (on `main`, `tools/merge_src.py`; both programs
  byte-identical). One program for every machine: done on `enhanced/scroll` without the
  scroller (`enhanced/src/gng_game.s`, profiles from the machine description; tested against
  both originals; see `enhanced/docs/SCROLLER.md`, One program for every machine). Not yet:
  slow/fast RAM used (a 512K chip + slow machine runs the 512K profile).* Next the source folding in `enhanced/docs/SCROLLER.md` (*Next steps* 0), into
  both builds of the one source; then this item turns the `ifd BUILD_1MB` blocks into run-time
  choices. The blocks give the complete list of places to merge.
* **Testing:** `enhanced/tools/compare_runs.py` already runs both originals side by side with the
  enhanced builds; the merged program can be run in each profile against the matching original
  (512K, 1MB chip), plus a 512K chip + 512K slow configuration in the emulator and in WinUAE.

## 8. Controls, options menu, sound and sprite tests

**Two-button joysticks** (done; `enhanced/docs/SCROLLER.md`, *Two-button joysticks*). The
second button is read from `POTINP` bit 14 (port 2's pin 9, set as an output driven high by
`POTGO`). Fire stays on the first button; jump on the second, or on up (the default, as the
original), switched with J on the title for now and in the options menu later. With jump on the
button, up only climbs ladders. (A CD32 pad's extra buttons need its serial read-out: not done.)

**Options menu** (done as the title menu: `enhanced/docs/SCROLLER.md`, *The title menu*). The
title page has the start items and INPUT; the test page the memory line, CHEAT and EXIT, with
room for the tests below. Every byte of it is resident: on 512K it comes out of the level
data area, where the fullest stages pre-mask what fits.

**Sound test.** Play each of the 15 tunes and 30 effects through the driver already loaded
(`MUSIC_PLAYER` commands 1 and 2); on 512K the 512K package has every tune and effect, on 1MB
the 1MB package's extra effects too.

**Sprite test.** Show Arthur's frames and the BOB sets one by one. The enemy sets are only
in memory for the current level (512K), so it would load the enemy graphics file into a screen
buffer as a level start does; only if the room allows.

**Input test.** As an arcade machine's switch test: the four joystick directions and both
buttons (fire on the CIA, the second button on `POTINP`) for each port, shown on screen and
lit while held, with the keyboard keys the game uses. Small (text drawn with the existing
font), so it should fit with the options menu.
