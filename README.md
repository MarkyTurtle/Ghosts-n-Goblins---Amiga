# Ghosts'n Goblins (Elite, 1990, v3) – annotated disassembly

| File | What it is |
|---|---|
| `gng_main.s` | Main program, 512K build (tracks 110-125, runs at `$80`). ~25,500 lines |
| `gng_equates.i` | Custom-chip / CIA registers, memory map, all named `a6` globals, object slot fields |
| `gng_main_1mb.s` / `gng_equates_1mb.i` | Main program, **expanded-memory (1MB) build** (tracks 17-32), assembled at org 0. Carries all the 512K annotations; every difference is marked |
| `gng_boot.s` | Bootblock + trackloader (track 0) |
| `build.sh` | Assembles all three sources with vasm and checks SHA-1 against the originals |
| `bin/` | The original binaries the sources reproduce |
| `tools/` | The tracer / generator used to produce `gng_main.s` (see below), `compare_builds.py`; `tools/budget/` (memory and size measurements for `docs/TODO.md`: `level_sizes.py`, `enemy_windows.py`, `gfx_redundancy.py`, `program_breakdown.py`; `sound/tools/sample_rates.py` and `tune_samples.py` for the samples); `tools/build1mb/` produces the 1MB source; `tools/verify/checks.py` runs the real code in a 68000 emulator to check the bug notes; `tools/refdocs.py` writes `docs/GLOBALS.md` and `docs/XREF.md` |
| `sound/` | Sound driver and music/sfx data: annotated sources, samples, renders (`sound/SOUND.md`) |
| `render/` | Scripts that render levels, enemy BOBs and Arthur's sprites from the disk data; output in `render/out/`, including `worldmap_cells.png` (the whole world map with every cell number) |
| `disk/` | **Every file loaded from the disk** (`disk/files/`), the file table (`disk/FILES.md`) and a track-by-track disk map (`disk/DISKMAP.md`). `tools/disk/mkdisk.py` builds a playable disk image from them (see *Making a disk image*) |
| `docs/` | `HOW_IT_WORKS.md` (a guided tour with diagrams: interrupts, the state machine, a frame, objects, spawning, drawing, level data), `GLOBALS.md` (every global, the memory map, object slot and per-type fields), `XREF.md` (which routines use each global, routine and table), `SPAWNS.md` (every level's spawn zones and scripts, decoded), `TODO.md` (planned enhancements: a shared file directory and own loader, automatic disk layout, corkscrew scrolling with a pristine buffer, zx0 / per-level files / caching / music on 512K, further space savings, emulator tests), sprite/BOB flipping spreadsheet |
| `bin/tracks/` | All 131 decoded tracks (6,312 bytes each) used by the render scripts |
| `bin/main_1mb.bin` | The expanded-memory build (tracks 17-32) |
| `enhanced/` | (branch `enhanced/scroll`) The enhanced build: the incremental corkscrew scroller integrated into the 512K game, its tests (whole game in the emulator, side by side with the original) and a disk image builder - see `enhanced/docs/SCROLLER.md` |

All three sources reassemble **byte-identical** to the originals:

```
vasmm68k_mot -Fbin -m68000 -no-opt -o main.bin gng_main.s         ; sha1 2628a93c164a5a8791272c146053b0afb3ddcf14
vasmm68k_mot -Fbin -m68000 -no-opt -o main_1mb.bin gng_main_1mb.s ; sha1 e44347679297d5d864ae7b0da689714970e261ad
vasmm68k_mot -Fbin -m68000 -no-opt -o boot.bin gng_boot.s         ; sha1 0bf93a4078bf317fa2774b4b973e1c79c0060227
```

`-no-opt` matters: the source keeps the original instruction sizes explicitly.

## Disk contents (see `disk/FILES.md` and `disk/DISKMAP.md`)

| Tracks | Contents |
|---|---|
| 0 | AmigaDOS bootblock (whole trackloader) |
| 1-16 | HAM loading screen |
| 17-32 | main program, 1MB build |
| 33-36 | Arthur's sprite frames |
| 37 | 10 single-image item/scenery BOBs: coin, money bag, stone block, grass raft, rock, 3 gravestones, boulder and ice platforms |
| 38-56 | enemy BOB graphics (21 sets) |
| 57, 59-60 | weapon / pickup / effect BOBs |
| 58 | enemy projectile BOBs |
| 61 | font |
| 62-63 | between-level progress map (RLE) |
| 64-81 | sound driver + music + effects (1MB build) |
| 82-83 | FAST copyright / anti-piracy warning screen (RLE), shown for 10 s at boot |
| 84-109 | level tile sets 0-6 |
| 110-125 | main program, 512K build |
| 126-131 | sound driver + effects (512K build) |
| 132-167 | unformatted |

`python3 tools/disk/extract_files.py` regenerates `disk/` from `bin/tracks/`; `tools/disk/` also holds the
original IPF decoding tools (`dump.cpp` uses the capsimg library, `gng.py` decodes the custom tracks).

## How the program runs

1. **Bootblock** loads the HAM loading screen (tracks 1-16), then the main program raw to `$80`
   (512K) or to the address it left in `$4.w` (expanded memory build, tracks 17-32), and jumps to `$A0`.
2. **`Start`** points every CPU exception at `CrashReset` (writes `RESET; JMP 0` to address 0 → reboot),
   sets `a6 = GLOBALS ($1898C)` for the whole run, loads the common files, builds sprite/HUD data,
   installs interrupts, shows the title, then drops to user mode and spins in `IdleLoop`.
3. Everything else is interrupt driven:
   * **`VblIRQ`** (level 3): Arthur's hardware sprites, HUD sprites, joystick, music tick, then raises
     **SOFTINT** unless last frame's logic is still running.
   * **`Level1Logic`** (level 1, SOFTINT): the real main loop. `g_GameState` → attract screens or
     `InGame`, which dispatches on `g_SubState` (load level, progress map / set-up, play (`InPlay`),
     game over, level complete, intro cut-scene, ending, "weapon useless").
   * **`KeyboardIRQ`** (level 2): raw key → `g_RawKey`, ASCII → `g_AsciiKey`.
   * When a full redraw is needed, `VblIRQ` rewrites the user-mode return address to `RedrawEntry`,
     so `RedrawScreen` runs outside the interrupts.

## Object systems (all slots live in the globals block)

| Table | Slots × size | Update routine | Dispatch |
|---|---|---|---|
| `g_Enemies` | 40 × `$3C` | `UpdateEnemies` | `EnemyTypeTable` (19 types, by `+$1A`) then state `+3` |
| `g_Shots` | 4 × `$26` | `UpdateShots` | `ShotTable`: torch, lance, axe, cross, dagger, and the armour pieces that fly off when Arthur is hit |
| `g_EnemyShots` | 6 × `$1C` | `UpdateEnemyShots` | `EnemyShotTypeTable` |
| `g_Items` | 30 × `$1C` | `UpdateItems` | `ItemTypeTable`: invisible triggers and point pickups, shootable scenery, platforms |
| `g_SpecialObjs` | 2 × `$20` | `UpdateSpecialObjs` | bonus prizes: carried by every 6th spawned enemy, or dropped by a trigger |
| `g_Spawners` | 16 × `$C` | `UpdateSpawners` | enemy spawners, one per enemy type (see below) |

The slot header shared by all object tables is named in `gng_equates.i` (`O_Active`, `O_State`, `O_Step`,
`O_X`, `O_Y`, `O_Type`, `O_HP` …) and used symbolically inside the object handlers (`O_State(a5)`).
Labels inside each enemy handler are prefixed with the enemy's name. State routines are named from
the dispatch tables: `RedArremer_Main`, `_State1`, `_Killed`, `_Remove`, with `_Step<n>` / `_Sub<n>`
for the second and third dispatch levels (`O_Step`, `O_Step2`). Likewise `Shot_`, `EShot_`, `Item_`,
`Arthur_`, `Game_`.

Enemy state (`O_State`): 0 = the enemy's main behaviour, 1 = a type-specific second phase,
2 = killed (set by `EnemyHitByShot` after scoring), 3 = remove.

### Enemy types (confirmed from each type's graphics set)

| # | Enemy | # | Enemy | # | Enemy |
|---|---|---|---|---|---|
| 0 | Woody Pig | 7 | Magician (frog spell) | 14 | Fire |
| 1 | Crow (bat / red crow variants) | 8 | Unicorn (2-part BOB) | 15 | Princess |
| 2 | Petite Devil | 9 | Skeleton | 16 | (unused) |
| 3 | Flying Knight | 10 | Big Man | 17 | Man-eater plant |
| 4 | Blue Killer | 11 | Zombie | 18 | Fire pillar |
| 5 | Red Arremer | 12 | Dragon | | |
| 6 | Satan | 13 | Astaroth | | |

Each handler has a header with its behaviour, points and hits (from `EnemyPoints`, `EnemyHitboxes`,
`EnemyVulnerability`), and lines that change state, play sound, score, fire shots or free the slot
are commented automatically (`tools/autoanno.py`).

| Enemy | Points | Hits | Enemy | Points | Hits |
|---|---|---|---|---|---|
| Woody Pig, Crow, Petite Devil, Flying Knight, Blue Killer, Skeleton, Plant, Princess | 100 | 1 | Zombie | 200 | 1 |
| Red Arremer | 1,000 | 3 | Dragon | 200 per segment (+1,000) | head: 6 |
| Satan | 3,000 | 4 | Big Man | 500 | 10 |
| Magician | 2,000 | 1 | Unicorn | 2,000 | 10 |
| Fire pillar | 100 | 4 | Astaroth | 10,000 | 10, cross only, ±9 px band |
| Fire | – | invulnerable | | | |

The cross is not used up when it kills.

### Enemy behaviour (all handlers annotated in detail)

Every enemy handler has every routine, table and per-enemy field named (equates such as `Uni_`,
`Sat_`, `Drg_`, `RA_`, `BK_`, `PD_` for slot offsets `$1C-$3B`, listed in `gng_equates.i`) and a
"Behaviour, as coded" summary in its header: how it moves, when it shoots, dodges, swoops or
charges, and the timings and speeds from its tables.

* **Unicorn** (boss of level 0, two on level 1, also on level 5): walks to scripts inside an arena, keeps its distance from Arthur,
  jumps over his shots, fires every so often, and when angry charges or jumps at him.
* **Satan** (level 4 boss, two on level 5): hovers and fires, folds its wings to let shots pass
  through, then dives in a sine-shaped arc, swoops or flies straight at Arthur.
* **Dragon** (boss of levels 2 and 3): a head plus 7 body segments and a tail in 9 enemy slots,
  linked as a list. The head steers along path scripts and every direction change is passed down
  the chain with a 6-frame delay, which makes the body follow. Hitting a body segment kills the tail.
* **Astaroth** (final boss): walks in a 128-pixel arena and fires from two points.
* **Red Arremer**: perches, walks, flies, dodges Arthur's shots, glides, swoops, and rages once.
* **Blue Killer**: walks in or swoops down from above, hops over shots - and after 72 seconds
  turns into a Red Arremer.
* **Magician** (type 7, first labelled "Ghost"): rises from a gravestone Arthur has shot and casts
  one spell (enemy shot type 0) that turns him into a frog.
* **Woody Pig**: flies in 16 directions, loops the loop near Arthur, and drops a carried shot.
* **Petite Devil**: hunts Arthur in up to four legs and fires a single shot.
* **Flying Knight**: flies left in a wave, shielded until it has passed Arthur.
* **Crow / bat**: five behaviours by parameter (hanging bat, perched crow that dives, flying in).
* **Skeleton**: rises from a pile of bones, hops twice, then leaps onto Arthur's spot.
* **Zombie**: rises out of the ground (its collision box grows with it), shambles, sinks back.
* **Big Man**: walks and pauses, fights Arthur on his level, throws down at him from above.
* **Fire / fire pillar / plant**: fixed hazards on timers.

## Data formats (all verified by rendering, see `render/out/`)

* **World map** (`WorldMap`, `$44D6`): one 32 × 11 map shared by every level, plus one extra byte
  (cell `$63`, the level-6 throne room). One byte per 256 × 256-pixel cell, bottom row first.
  Each level's bottom-left origin comes from `LevelMapTable` (word offsets **from the table start**
  `$44BA`), and its size in cells from `LevelBounds`. Levels 5 and 6 have their origin one cell to the
  right of their `LevelBounds` x0.
* **Cells** (`CellTiles`, `$1222C`): 256 bytes per cell type, a 16 × 16 grid of tile numbers.
  **Tile 0 is a real tile** (the first one in the level file), and map cell `$67` means "tile 0
  everywhere". On the early levels tile 0 happens to be blank; on the castle levels it is the brick wall.
* **Tiles**: in the per-level file (tracks 84-109), 160 bytes per 16 × 16 tile, 5 line-interleaved
  bitplanes. Level 1 uses a second bank (tile + 256) for cells `$1D`/`$1F`.
* **Screen**: 288 × 256, 5 planes, line-interleaved (180 bytes per line), double buffered.
* **BOBs** (enemies): big file tracks 38-56 holds 21 graphics sets (`BobSetOffsets` / `BobSetSizes`).
  `LoadLevel` copies only the sets the level needs (`LevelBobSetMask`). Frames are line-interleaved,
  5 planes, colour 0 transparent (mask built by the blitter at draw time). Frame descriptors
  (`BobFrameDescs`): offset.w, y-adjust.b, height.b; width from the object's size class.
* **Arthur**: 4 hardware sprites (two attached pairs, 16 colours from COLOR16), 42 frames of 32 × 32
  from tracks 33-36, plus mirrored copies of frames 0-39 built at start-up. Frames 0-14 armoured,
  15 frog, 16-31 the same poses without armour, 32-36 skeleton, 37-39 frog, 40 sitting (opening scene),
  41 arms raised (end of level and ending).
* **Collision** (`MapTileAt`): cell → `BlockTiles` (8 × 8 grid of 32-pixel tiles per cell, column-major,
  rows from the bottom) → `TileAttr` record of 8 bytes: four profile bytes (one per 16 × 16 quadrant)
  and four flag bytes. The profile byte is **sign-extended** before indexing `FloorProfile` (floor height
  1-16 in the quadrant, 0 = none) and `WallProfileR` / `WallProfileL`. Profiles `$40-$7D` are ladders.
  Flag bits 6-7 = background (not solid). Rendered as overlays in `render/out/level*_collision.png`.
* **In the source**, the map and tile tables are written out structurally (`tools/map_data.py`):
  `WorldMap` as 11 rows of 32 cells (each row noting which levels it holds), `CellTiles` as 16 rows
  of 16 per cell, `BlockTiles` column by column, every `TileAttr` record with its quadrant floor
  heights / ladders / background flags in the comment, and the three profile tables around their
  middle labels. Each cell type is annotated with the levels that use it.
* **Animations, movement and boxes in the source** (`tools/anim_data.py`, `tools/tables_data.py`):
  every enemy and weapon animation script is written with `AF frame,ticks` / `AL frame,ticks,next`
  macros and labelled direction tables; movement tables as `dx,dy` (8.8 px/frame) with the speeds in
  the comments; contact boxes, hit boxes and shot boxes one line per enemy or shot type; the item
  and enemy placement lists with a `PLACE type,param,x,y` macro and `E_…` / `I_…` type equates; the
  level tables (bounds, times, start and checkpoint positions, spawn quotas), `ScoreValues`,
  `EnemyPoints` and `EnemyVulnerability` (as weapon bitmasks). No `dat_…` labels remain.
* **More tables in the source** (`tools/tables2_data.py`): the BOB frame descriptors
  (`BobFrameDescs`, `EnemyShotFrames`, `EffectFrames`) with a `FRAME offset,yadjust,height` macro and
  a labelled table per enemy type; the copper list template as `dc.w REGISTER,value` with the
  bitplane / sprite addresses and waits in the comments; the moving platforms' step tables and
  scripts (`ItemPaths`, `ItemPathScripts`, `ISTEP` / `ILOOP`); the Dragon's entrance, patrol, turn,
  climb and dive paths (`DSTEP` / `DLOOP`, with compass directions); the unused Petite Devil
  appearance points; and the file table (`FileTable`, `FENTRY address,length,track`, which the disk
  builder reads). The 1MB build has the same tables with every graphics offset doubled (its
  cached graphics carry a mask line after each plane line); they are decoded there too.
* **Graphics-set sizes** (`CacheSizes…`, `$4002` and `$432A`): (width, height) of each graphics set,
  read only by the 1MB build's `BuildMaskedGfx`. The 512K build carries the same tables unused.
* **Items / scenery** (track 37): 10 single-image BOBs (`SmallBobSetOffsets`, sizes in `SmallBobSizes`),
  drawn by `DrawItem` through `ItemImageTable`. Item type 1 is shootable scenery (gravestones),
  checked by `ShotsVsScenery`. Rendered in `render/out/small_bobs_t037.png`.
* **HUD weapon icons** (`WeaponIcons`): 16 × 16, 16 colours, written into two attached sprite pairs
  (`render/out/weapon_icons.png`).
* **Enemy spawners**: most enemies are not placed but created by 16 spawners (`g_Spawners`, one
  per enemy type). Each map cell has a zone number (`MapZoneTable`). Entering a new zone starts that
  zone's spawners (`ZoneSpawners`), each running a script of (x, y, param, delay) entries
  (`SpawnScripts`). `g_SpawnQuota` (per type, from `LevelSpawnQuota`) limits how many exist, and
  each handler gives its quota back when its enemy leaves. Every 6th spawned enemy carries a bonus
  (`BonusKinds`). The zone is that of the cell under the camera. Types with `ZoneFlags` = 0 (the
  bosses, Red Arremer and Big Man) only start in a zone further on than any reached before.
  The spawn tables are written out in the source with `SPAWNER` / `SPAWN` macros, and decoded per
  level in `docs/SPAWNS.md` and `render/out/level<n>_spawns.png` (world-coordinate spawn points
  circled). The Magician has no zone spawner: each gravestone takes 15 shots, then the Magician's
  spawner is started there (`ShotsVsScenery`). (These were first labelled
  as "animated tiles" and a "level palette"; the names are now corrected.)
* **Arthur's animations** (`ArthurAnims` …): written out with `AFRAME` / `ALOOP` macros; `~n` is
  the mirrored copy of frame n. Frames 0-15 armoured, +16 without armour, 31 knocked back,
  32-36 skeleton, 15 and 37-39 frog.
* **Placement lists** (`LevelEnemyLists`, `LevelItemLists`): count.w then type.b, param.b, x.w, y.w
  in world pixels with Y increasing upwards.

## 512K vs 1MB builds

Compared instruction by instruction (`tools/compare_builds.py`): **the same program**. There is no
extra title or ancillary code in the 1MB build. `gng_main_1mb.s` is the full 1MB source: about 260
instructions have no 512K counterpart (marked `[1MB]`), and each of the 121 places where the builds
differ has a `<< … >>` note naming the 512K code it replaces. The differences are:

* **Addressing**: the 1MB build runs at `$80000` or `$C00000`, so it adds a base register adjustment
  (`adda.l base(a6)`) wherever the 512K build uses an absolute address.
* **File caching**: it loads all the common graphics files once at start-up (via a staging area,
  then converted by `BuildMaskedGfx` into permanent buffers). The 512K build reloads the enemy graphics
  (tracks 37-56) every time a level starts. The per-level file is reloaded in both builds.
* **Stored masks**: `BuildMaskedGfx` writes a mask line after every plane line, so the 1MB `DrawBob`
  does one save blit and one cookie-cut blit with the stored mask. The 512K build builds the mask with
  the blitter at draw time (it has no memory to keep masks).
* **Memory layout**: the program sits in fast/slow RAM at the load address; screens (`$80`, `$B480`,
  `$16880`, `$21C80`), copper lists, sprites and the music package (`$3604C`) are in chip RAM at
  absolute addresses. `g_BaseAddr` is inserted at `$2(a6)`, so every global from `+2` on is 4 bytes
  further into the block than in the 512K build (`gng_equates_1mb.i` has the 1MB offsets).
* **Music**: the 1MB build loads a 111KB music package (tracks 64-81) instead of the 512K build's 32KB
  one (tracks 126-131), and has 13 extra calls to a **PlayMusic** entry (player command 1) for level
  tunes, game over, time-up, beating Astaroth (tune 9) and so on, plus extra sound effects (e.g. effect 9 when enemies are hit). In the 512K build those calls were removed but their set-up
  was left behind: e.g. `LevelMusic` is still looked up at `$6C0E` and never played. These spots are
  marked `[1MB build: …]` in the source.

## Findings

* **Copy protection is only the disk format.** Every disk access goes through `LoadFile` (a copy of the
  bootblock loader). The program has no code checksums, no protection-track reads, no timing checks.
  Besides the long tracks, the only protection is the exception vectors that reset the machine.
* **Cheat:** entering **`)!(`** as your initials on the high-score table sets `g_CheatOn`: lives
  never decrease, and once Arthur has lost his armour enemies and their shots no longer hit him
  (he can lose the armour once, then enemies cannot touch him).
* **Extra lives** at 20,000 and 70,000 points, then every 70,000.
* **Keys:** F1/F2 start a 1/2-player game, Space pauses (fire resumes), Esc aborts.
* **Level 6 boss** without the cross (weapon 3) → "THIS WEAPON IS USELESS ! GET A CRUCIFIX AND TRY
  AGAIN." and you're sent back to level 5 (index 4).
* **The ending** (beating Astaroth with the cross): Arthur and the princess walk to each other,
  "CONGRATULATIONS ! THIS STORY HAS A HAPPY ENDING." stays up for 550 frames, 50,000 points are
  added and the game ends (lives cleared, straight to game over and the high-score table). Unlike
  the arcade there is no second loop.
* **Opening scene:** the demon is Satan's graphics and animations; Arthur's armour is a special
  object he walks over and picks up. The scene is played once per game and skips the first progress
  map. The progress map is a 5-plane RLE picture scrolled 144 px, with a start and a checkpoint
  marker position for each level.
* **Frame rate:** the game logic runs on every vertical blank it can (up to 50 a second), but the
  camera and drawing only happen on every second logic frame, so the screen updates at 25 frames a
  second.
* **Scrolling** is done by full redraws. The playfield buffer is redrawn around a new 16-px tile
  origin (outside the interrupts, about 14,600 instructions and 288 blits each) and the display then
  switches to it; in between, hardware fine scroll covers up to 16 px either way. Walking right, the
  screen switches every 16 px with the fine scroll between -8 and +7, and the next origin is chosen
  one tile ahead in the direction Arthur faces. The request compares against the current origin,
  not the one already drawn, so the same screen is redrawn again every camera step until the switch
  - the redraw runs almost all the time. If the camera would need more than 16 px before a redraw is
  ready, `g_SkipLogic` stops the game logic until it is: walking never hits this (it would need a
  redraw slower than 14 frames), but falling at full speed does, so falls cause short freezes. The
  exact switch and request rules are in the source at `$6EF2` and as a Python model in
  `tools/verify/camera.py`, which matches the real code on 20,000 random states.
* **BOB budget:** each frame may save at most `$3000` bytes of background under its BOBs; any BOB
  that would go over is simply not drawn that frame.
* **Scrolling back** is limited: levels 0, 1 and 3 keep the camera within 256 px of the furthest point
  reached, levels 4-6 within 512 px vertically; level 2 has no limit.
* **End of level:** after the boss, "TAKE A KEY FOR COMING IN !" appears and everything except
  Arthur freezes. The key drops at the end of the level (1000 points); then Arthur walks off, gets
  the level bonus (5000 / 10000 / 15000 for levels 0-1 / 2-3 / 4-5) and his armour back.
* **Level times:** 2:00, 1:30, 2:30, 2:30, 3:40, 3:40 and 2:00 for levels 0-6. Level 1 restarts
  from its checkpoint with 2:30 - a minute more than from the start.
* **Platforms:** shootable scenery (item type 1, the gravestones) is solid - Arthur can stand on it -
  but only item types 2-5 carry him when they move. Each moving platform runs a script of
  (step, frames) moves (`ItemPathScripts`). Types 2 and 3 only have a script for param 0, so the
  one type-3 platform with param 1 (level 1) runs type 4's first script with its own, faster
  vertical steps (checked in the emulator).
* **Unused bits:** the 16th and 17th `ScoreValues` entries are not valid BCD and nothing uses them;
  a few enemy fields are cleared but never read (Woody Pig, Blue Killer); one bat/crow
  animation table has no reference; the second half of `LevelMapTable` is never read.
* **High scores** start at 10,000 for everyone, with the initials Ric, DP, MC, PJC, GB, JCM and GnG.
  Leaving your initials blank stores "504".
* Loader state is kept at `$28-$2E`, the Line-A / Line-F exception vector slots. `Start` leaves those
  two vectors unset for that reason.
* `PrintHexByte` (`$B026`) and a few other routines are never called, probably debug leftovers.
* **Bugs** (each one checked by running the real code in a 68000 emulator - `tools/verify/checks.py`):
  * Satan's dying state tests its timer the wrong way round (`beq` for `bne`), so the 63-frame
    pause after the explosion is skipped.
  * Astaroth's stand-and-fire phase ends on the frame it starts (inverted branch at `$11858`),
    so its faster firing table is never used.
  * `DirectionToArthur` returns 5 instead of 6 for 'left and below' at 45 degrees (table data). Its
    slope bands use the whole quotient |dy| / |dx|, so the 1.5 threshold never applies.
  * Red Arremer start mode 2 counts `$F0` down by `$61` per frame waiting for exactly 0, twice:
    52,706 frames (17½ minutes) blinking and unhittable. Mode 2 is what a Blue Killer turns into
    after 3,600 frames; the placed Red Arremers use mode 1.
  * The Red Arremer's dodge test only checks the first shot slot's active flag (a free slot's old
    position still counts), and its 'which side' test compares bit 7 of the low bytes, so it is
    only right while the distances are under 128 px.
  * The Petite Devil's turning code works out the new direction and then stores `#1`: once it
    starts turning it flies right and a little down, whatever it was turning towards.
  * Going down a ladder from the top skips the first getting-on pose (frame 13): the code
    compares `d0` (always `$FF` there) instead of the step counter.
  * Arthur's shots against enemy shots: the box pointer is not reset per shot, so after one shot
    misses, the next is tested against the following words of the table.
  * The vertical camera overshoots when moving down (to the target minus the distance less 2 px),
    so while Arthur falls the view alternates between on target and up to 8 px past it.
  * Skeletons, plants and fire pillars do not give their spawn quota back when removed.
  * The fire pillar writes three fields from a frame table during its shots that nothing reads.
  * `DrawBob`: a BOB that crosses the top of the screen buffer has twice too many graphics lines
    skipped, so the part still on screen shows the wrong lines of its image. The same code is right
    in the 1MB build, whose masked graphics have twice the bytes a line; the 512K build kept it.
    `DrawSceneryOnRedraw` has it too. (Found by the enhanced scroller's tests.)
  * In the unused `PetiteDevil_PathUnused`, `PetiteDevil_PathNext` adds each list offset after
    stepping past it, so it lands 2 bytes into the list: the first X is read as the point count.
* **Corrected by the emulator checks:** the Big Man crouches when Arthur is within 16 px of it
  vertically (an earlier note said "exactly 16"), and two Astaroth bytes thought unused are the
  low bytes of its walk and stand timers.
* **Arthur's physics:** walks at 1.125 px/frame and climbs at 1.375. A jump launches at 4.25 px/frame
  up with gravity 0.24 px/frame^2 (falling at up to 5): 17 frames up, about 39 px high, 35 frames in
  all and about 44 px forward. The direction can't change in the air. Being hit uses the same
  launch, away from the enemy; losing the armour gives 120 frames of invulnerable flashing. The frog
  lasts 8 x 64 frames and can walk and jump but not climb or fire.
* **Weapons:** torch, lance, axe and cross fly at 4.19 px/frame, the dagger at 5.63. The lance
  goes 192 px and the dagger 197; the cross only 48 px (but survives kills); the torch and axe fall in
  an arc after 48 px and the torch burns on the ground for 64 frames.
* **Hidden bonuses:** invisible trigger items drop a prize from above when Arthur walks past - one
  only when he has lost his armour (it gives the armour back), another drops 10,000 points.
* **Sounds removed from the 512K build**: several enemies still load a sound number into `d0`
  before an unrelated call. These are the 1MB build's footstep and other effects (commented
  `[1MB build: …]`).
* Credits in the strings: program R Frankish, graphics D Percival, sound M Cooksey.

## Making a disk image

`tools/disk/mkdisk.py` writes an extended ADF (`UAE-1ADF`, for WinUAE / FS-UAE) in the game's own
track format, so the long protected tracks are kept. With no options the image holds exactly the
original disk; its 131 custom tracks were compared bit for bit with the MFM decoded from the IPF.

The builder holds no file list of its own: it reads the layout from the programs going onto the
disk - the `FileTable` of both main programs (written in the source as `FENTRY load address,
length, first track`) and the three loads in the bootblock (loading screen and the two main
programs). `--layout` prints what it found and which table each file comes from. So to move or
resize a file, change its `FENTRY` in the source (in both builds if both load it), rebuild, and
pass the new binaries; a file's length must match its entry and it must end before the next file
starts (the builder stops with a message otherwise). A file at a new track is given with
`--file TRACK=PATH`. A file no table lists (for example a module that a patched program loads
with its own entry) is added with `--add TRACK=PATH`; it is checked against the others like any
file.

```
python3 tools/disk/mkdisk.py -o gng.adf                      # the original disk
sh build.sh                                                  # assemble main.bin, main_1mb.bin, boot.bin
python3 tools/disk/mkdisk.py -o mine.adf --main512 main.bin --main1mb main_1mb.bin --boot boot.bin
python3 tools/disk/mkdisk.py --check mine.adf               # decode it again and compare
python3 tools/disk/mkdisk.py --layout                        # the layout read from the tables
```

Any file can be replaced with `--file NAME=PATH` (a `disk/files` name or its first track); the
bootblock checksum is recomputed. Built from unchanged sources the image's
SHA-1 is `98b341330c2ea19bcf6a8fad06d88c0c5cd8099a`. The image follows the format's published
description (track type 0 = AmigaDOS, 1 = raw MFM with a bit length) but has not yet been booted in
an emulator here (no Kickstart ROM is available in this environment); please report if it doesn't.

## Reference pages

* `docs/GLOBALS.md` - every `a6` global with its size and meaning, the memory map, the shared object
  slot layout and every per-type field.
* `docs/XREF.md` - for each global, routine and table, the routines that use it.
* `render/out/worldmap_cells.png` - the whole 32 x 11 world map, each cell cut from the level
  renders, with its cell number and a border in its level's colour.

## Sound (see `sound/SOUND.md`)

The sound driver is Richard Frankish's music player, with music and effects by Mark Cooksey, in two
data files: `sound/gng_sfx_512k.s` (30 effects, 512K build) and `sound/gng_music_1mb.s` (15 tunes +
30 effects, 1MB build). Both reassemble byte-identical, with the music data written as readable macros.
`sound/audio/` has MP3 renders of every tune and effect, made by running the original driver code in a
68000 emulator, plus every sample as a WAV.

## Annotation depth

* **Reading aids in the source:** a 'how to read this file' guide and a contents list at the top;
  named constants instead of bare numbers where the meaning is certain - sound effects (`SFX_`),
  tunes (`TUNE_`), score indices (`PTS_`), game and in-game states (`GS_`, `SS_`), Arthur's state
  (`AS_`), enemy states and types (`ST_`, `E_`), and DMACON / INTENA / INTREQ bits (`DMAF_`, `INTF_`);
  jump tables named after their routine (`InGame_Jumps` ...); labels nothing refers to removed.
  The constants are generated by `tools/readable.py` and assemble to the same bytes.

* **Fully annotated:** start-up, interrupts, game state machines, level load/setup, play frame,
  Arthur (states, physics, ladders, weapons), collisions, scoring/extra lives, HUD/text, display &
  copper double buffering, loader, file table, bootblock.
* **All 19 enemy handlers:** every routine, table and per-enemy field named, with behaviour
  summaries and comments on the decisions, plus automatic comments on state changes, sounds,
  scoring and shots.
* **Enemy spawners** and the bonus-carrier system, with the spawn tables decoded in the source.
* **Arthur:** every state, the jump / fall physics, ladders, firing and walls commented.
* **Arthur's shots, enemy projectiles, items and bonus prizes:** every handler named and described
  (weapon speeds and ranges, what each projectile type belongs to, what each trigger and prize does).
* **Cut-scenes:** the opening scene, the ending, "weapon useless" and the between-level progress
  map, step by step (each step labelled, timings and the map's RLE format in the headers).
* **Game flow:** every in-game sub state, the play frame (timer, checkpoint, camera and redraw
  decisions), level set-up, the boss key and level bonus, game over, high-score insertion and name
  entry, and the attract screens.
* **Rendering:** the BOB draw list, background save / restore, the masked blit (clipping, mask
  building, cookie-cut), full redraws, buffer rotation and the 4-colour text renderer.
* **Line comments** on the mechanical routines too (explosions, map zones, spawners, the collision
  routines, VBL, hardware set-up, bitplane pointers, ladders, Unicorn and Petite Devil details).
* **1MB-only code:** the start-up caching, the one-blit masked `DrawBob`, and every extra sound
  call (which effect and why) are commented in `gng_main_1mb.s`.
* **Checked by emulation:** every bug note and several behaviour claims are confirmed by running
  the original code in a 68000 emulator (`tools/verify/checks.py`, 16 checks, including the camera model).
* **Data:** every table the code reads is named; the map, tile, spawn, animation, movement, box,
  placement, level and score tables are written out structurally. Every object field and global the
  code uses has a name (the remaining raw offsets on a5 are slot sizes, e.g. `lea $3c(a5),a5`).
  Only graphics, sound, the font and similar bulk data stay as `dc.b`.

## Extending the annotations

`gng_main.s` is generated, so edit `tools/anno_db.py` (and `tools/anno_bosses.py`,
`tools/anno_enemies.py`, `tools/anno_arthur.py`, `tools/anno_scenes.py`, `tools/anno_flow.py`,
`tools/anno_render.py`, which it runs) rather than the `.s` file.
`tools/spawn_data.py`, `tools/arthur_anims.py`, `tools/map_data.py`, `tools/anim_data.py`,
`tools/tables_data.py` and `tools/tables2_data.py` (with `tools/anno_tables.py`) write the spawn, animation, map / tile and
other data tables as structured source (`DATA_BLOCKS`); the build check proves they still
assemble to the same bytes. The 1MB generator finds each of these blocks by its bytes in the 1MB
binary; where the bytes differ (the frame tables, the copper template) it decodes the 1MB bytes
with the same builders.

```
N(addr, 'Name', "block header")   C(addr, 'line comment')   V(a6_offset, 'g_Name', 'comment')
M(abs_addr, 'EQUATE', 'comment')
```

then regenerate and verify:

```
cd tools
python3 mkeq.py && python3 gen.py      # writes gng_main.s / gng_equates.i
vasmm68k_mot -Fbin -m68000 -no-opt -o out.bin gng_main.s && cmp out.bin main.bin
```

`autoanno.py` regenerates `anno_auto.py` (automatic enemy comments and state-routine names).
For the 1MB source, run `trace1m.py`, `mkmap.py`, `make_gen1m.py`, `mkeq1m.py` and `gen1m.py` in
`tools/build1mb/` (`make_gen1m.py` derives `gen1m.py` from `gen.py`):
`mkmap.py` aligns the two builds instruction by instruction (checking that branch targets and
immediates agree), and `anno_db1m.py` carries every name, header and comment across; 1MB-only
annotations are at the end of `anno_db1m.py`.

`trace.py` re-runs the control-flow trace (`seeds.json` holds the extra entry points: interrupt
handlers, `JSR (a0)` targets and unreferenced routines).
