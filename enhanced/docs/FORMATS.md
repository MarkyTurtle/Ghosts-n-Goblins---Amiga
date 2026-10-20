# Data formats

The formats of every file on the enhanced game's disk (`DISK.md` lists them with their offsets
and sizes) and of the data the game builds from them in memory. All numbers are big-endian
(68000). *Line-interleaved* means a picture is stored line by line, each line holding the rows
of all its bitplanes one after another (plane 0 first); a row is `width / 8` bytes.

The files that come from the original disk are unchanged (`disk/files/`, `disk/FILES.md`);
the main README's *Data formats* section has more on the world map, cells, collision and the
game's tables, and `docs/SPAWNS.md` on the spawn tables. The files new to the enhanced disk
are the map table files, the relocation file, the 512K music package and the file table.

## The disk

* **Bootblock** (disk offset 0, 1,024 bytes): `'DOS',0`, the checksum (the long that makes the
  sum of the bootblock's 256 longs, with carries added back, `$FFFFFFFF`), the root block
  number (880), then code from offset `$0C` (`src/boot_4489.s`; `build_game.py` sets the
  checksum). It also holds the loading picture's two copper lists and its palette.
* **File table** (offset `$400`): `'GNGF'`, version.w (1), count.w, 8 zero bytes, then for each
  file id an offset.l and a length.l (bytes, from the start of the disk). See `DISK.md`.
* **Files** from offset `$600`, in file id order, each the exact bytes of the file.

## Graphics

### Loading picture (`FID_LOADPIC`, 99,072 bytes)

HAM6, 256 x 516 interlaced (two fields of 258 lines), 6 planes, 32 bytes a row, line-interleaved
(192 bytes a line), the two fields' lines alternating in pairs: frame line *r* is at
`(r / 2) x 384 + (r & 1) x 192`. The bootblock shows it with two copper lists swapped each
frame (`BPLCON0` = `$6804`) and the 16-colour palette at its end (`Palette` in
`boot_4489.s`; the original bootblock kept it at `$382`). Rendered: `render/out/loadscreen.png`.

### Copyright screen and progress map (`FID_COPYRIGHT`, `FID_PROGMAP`): RLE pictures

ByteRun1 (as IFF ILBM's): for each line, for each of the 5 planes, a plane row of *n* bytes
packed as runs - a control byte *c* < 128: the next *c* + 1 bytes as they are; *c* > 128: the
next byte 257 - *c* times; 128: nothing. The rows are unpacked into the line-interleaved screen
layout with 4 zero bytes in front of each plane row (the 16 pixels the screen's fetch starts
early) and, for the progress map, 2 bytes after each line.

| File | Lines | Bytes a plane row | Unpacked line | Shown |
|---|---|---|---|---|
| copyright screen (9,726) | 224 | 32 | 5 x 36 = 180 | colours 0-3 only (black, white, `$BBB`, `$888`) |
| progress map (7,516) | 80 | 44 | 5 x 48 + 2 = 242 | the game palette, with its own copper list (`COPPER_MAP`) |

Rendered: `render/out/copyright_screen.png`, `render/out/progress_map.png` (`render/pictures.py`
has the decoder).

### Level tiles (`FID_LEVEL0` + level)

16 x 16-pixel tiles of 160 bytes, one after another: 16 lines x 5 planes x 2 bytes,
line-interleaved. A tile number is the index in the file (the file is loaded to `LEVEL_FILE`, and
a tile is at `LEVEL_FILE + 160 x n`); stage 2 has more than 256 and uses a second bank for two
cell types. Tile 0 is a real tile (map cell `$67` is "tile 0 everywhere"). Colours: the game
palette (32 colours, `GamePalette`). Rendered: `render/out/level*.png`.

### BOB graphics: enemies, small BOBs, items, shots

The enemy sets' file (`FID_ENEMYBOBS`, 118,850 bytes) holds 21 graphics *sets*; the small BOBs'
file (`FID_SMALLBOBS`) 10 single images; the item, weapon and effect files (`FID_ITEMS`,
`FID_ITEMS2`) and the enemy shots' file (`FID_ESHOTS`) one block each. Every image is
line-interleaved, 5 planes, a whole number of 16-pixel words wide; colour 0 is transparent.

* Where a set starts and how long it is: `BobSetOffsets` (21 longs, offsets in the file, *not*
  in set order) and `BobSetSizes` (21 words); the small BOBs: `SmallBobSetOffsets`,
  `SmallBobSetSizes` and `SmallBobSizes` (y adjust, height). `LevelBobSetMask` (a long a level)
  and `LevelSmallBobMask` (a word a level) say which a level uses.
* A frame of an enemy, shot or effect: a 4-byte descriptor (`BobFrameDescs`, `EnemyShotFrames`,
  `EffectFrames`; the `FRAME` macro): offset.w (from the set's start), y adjust.b, height.b. Its
  width comes from the object's size class. The program's `CacheSizes*` tables give each set's
  blocks as (width in pixels, height) for the masked copies.
* Rendered: `render/out/bobs.png`, `small_bobs_t037.png`, `item_gfx.png`,
  `enemy_shot_gfx.png`.

**Masks.** The files have no masks: the original 512K program built each BOB's mask at draw time
(two blits, the OR of the 5 planes). The enhanced game makes them in advance:

* **One-plane mask** (512K, `BuildLevelMasks`): one row a line, the OR of the line's 5 plane
  rows - a fifth of the image's size. A region of images (the level's sets after `LEVEL_FILE`;
  the items, weapons and shots from `ESHOT_GFX_BUF`) has its masks in one block, the mask of
  the image at `g` at `mask base + (g - region base) / 5`. A BOB is then 5 cookie-cut blits.
* **Pre-masked** (the 1MB program's format, `BuildMaskedGfx`): after every plane row a copy of the
  line's mask row - 10 rows a line, twice the bytes. A BOB is one blit (A = the mask rows, B =
  the plane rows, C / D = the screen, 5 x height lines). With 1MB of chip RAM every image is
  converted at start-up into the upper chip RAM caches and the frame offsets are doubled; on 512K
  `BuildLevelMasks` converts as many as fit (`GfxPriority`) and the game's pointer to such an
  image becomes a *key* in `[KeyBase, KeyBase + KeyLen)`, the copy being at
  `KeyBase + 2 x (key - KeyBase)`.

### Arthur (`FID_ARTHUR`, 21,504 bytes)

42 frames of 32 x 32 pixels, 4 planes (16 colours, from `COLOR16`), 512 bytes a frame: 32 lines
of 8 words, `[left p0, right p0, left p1, right p1, left p2, right p2, left p3, right p3]`.
Start-up splits them into four hardware-sprite banks `$2900` apart at `ARTHUR_SPR_GFX`
(sprites 0 + 1, an attached pair, the left 16 pixels; 2 + 3 the right): in each, the 42 frames
of `$80` bytes (32 lines of the sprite's two data words), then mirrored copies of frames 0-39
(bits reversed, halves swapped). Frames: 0-14 armoured, 15 frog, 16-31 without armour, 32-36
skeleton, 37-39 frog, 40 sitting (opening scene), 41 arms raised. Rendered:
`render/out/arthur.png`.

### Font (`FID_FONT`, 6,208 bytes)

Only every other byte is used (the even ones): start-up copies them to `MASK_BUF`, 3,104
bytes, 16 bytes a character for character codes 0-193: 8 lines of 2 bytes (two bitplanes).
`PrintChar` draws plane bits *a*, *b* as: *a* only = `g_TextShadow`, *b* only = `g_TextInk`,
both = `g_TextPaper`, neither = transparent (the background shows; colour 0 in the HUD).

## Level data

### Map tables (`FID_TABLES0` + level; new on the enhanced disk)

Made by `build_game.py` (`level_tables()`) from the original 512K program's `BlockTiles` and
`CellTiles`, for the map cells the level can read (its rectangle of `WorldMap`, one cell more on
every side, and columns 254-255 of those rows; see `FEATURES.md`). Loaded to `LEVEL_TABLES`:

| Offset | Bytes | |
|---|---|---|
| 0 | 256 | the slot of each cell value (`LEVEL_SLOTS`): cell `$67` (empty) and any cell the level never reads are slot 0 |
| 256 | 64 x `TBL_SLOTS` | each slot's `BlockTiles` (`LEVEL_BLOCKS`): 8 x 8 collision tiles of 32 pixels, column by column, each column from the bottom up; a tile number indexes `TileAttr` (bank from `MapBlockIndex`) |
| 256 + 64 x `TBL_SLOTS` | 256 a slot | each slot's `CellTiles` (`LEVEL_CELLS`): 16 x 16 tile numbers, the graphics tiles of the cell, for the slots the level uses |

`TBL_SLOTS` is the most any level uses (49), so the block tiles are at the same place in every
file; the files are 5,184-15,936 bytes. `MapTileAt` (collision) and the scroller's `DrawTile`
look a cell's slot up first.

### World map, collision and spawn tables

Resident in the program, unchanged from the original: `WorldMap` (32 x 11 cells, one byte a
256 x 256-pixel cell, bottom row first), `LevelMapTable` / `LevelBounds`, `MapBlockIndex`,
`TileAttr` (8-byte collision records: four quadrant profile bytes, then four flag bytes),
`FloorProfile` / `WallProfileR` / `WallProfileL`, `MapZoneTable`, `ZoneSpawners`,
`SpawnScripts`, `LevelItemLists` / `LevelEnemyLists` (`PLACE type, param, x, y`). See the main
README's *Data formats* and `docs/SPAWNS.md`.

## Sound

### Sound packages (`FID_MUSIC512`, `FID_MUSIC1M`, `FID_SFX`)

An AmigaDOS hunk file of one code hunk: `HUNK_HEADER` (`$3F3`), no libraries, one hunk, its size
in longs, `HUNK_CODE` (`$3E9`), the size again; the driver's entry is at offset `$20`
(`MUSIC_PLAYER`), called with `d0.l` = argument << 16 | command (0: tick, from the vertical
blank; 1: start a tune; 2: start an effect; 3: a value nothing reads). Then the tables, the
instrument records (28 bytes), the voices' bytecode, the pattern table, `PitchTable`, the
driver's workspace and the samples (each: length.l, rate.w, then signed 8-bit data). Nothing
reads the hunk header: the game loads the whole file to the address it was assembled for
(`SND_ORG`, `build_game.py`) and calls offset `$20`; loaded anywhere else (the 1MB package at
`$80` when the program has moved) its addresses are moved with the relocation file. The full description is `sound/SOUND.md`.

| Package | Bytes | Tunes | Effects | Used on |
|---|---:|---|---|---|
| `FID_MUSIC1M` (`sound/gng_music_1mb.s`, the original 1MB file) | 111,508 | 15, full quality | 30, the 1MB set | 1MB of chip RAM; 512K with the program moved |
| `FID_MUSIC512` (`sound/gng_music_512k.s`, made by `make_music_512k.py`) | 67,332 | 15, the sampled instruments (samples 5-9) at 3/4 of their rate | 30, the 512K set | a plain 512K machine |
| `FID_SFX` (`sound/gng_sfx_512k.s`, the original 512K file) | 32,100 | none | 30, the 512K set | no machine description |

In the 512K music package the resampled instruments' period multipliers are divided by 3/4, so
every note keeps its pitch; `sound/tools/check_music_512k.py` checks every tune and effect
against the original packages.

## Program support files

### Relocation file (`FID_RELOCS`; new on the enhanced disk)

Made by `build_game.py`: the program is assembled a second time 2MB further on (`RELOC_ORG`,
with the memory map where it is: `MAP_FIX`), and every long that differs by 2MB is an address
to move. Two tables, one after the other - the program's, then the 1MB sound package's:

| | |
|---|---|
| count.l | the number of addresses (0: none) |
| count x gap.w | from the image's base, the distance to the next long to move (the first from the base itself) |

`ApplyRelocs` walks a table adding the distance the image moved to each long (`EnhRelocate`
for the program copied to the expansion; `LoadSound` for the 1MB package loaded to `$80`).

### Machine description (`MACHINE_INFO`, `$7FB00`, 32 bytes, written by the bootblock)

| Offset | Size | |
|---|---|---|
| 0 | 4 | `'GNGM'` |
| 4 | 1 | version (1) |
| 5 | 1 | `VBlankFrequency` (50 PAL / 60 NTSC) |
| 6 | 2 | `AttnFlags` (the CPU / FPU bits) |
| 8 | 4 + 4 | chip RAM: lower, upper end (512K: `$80000`; 1MB: `$100000`; Kickstart 1.3 with 1MB lists `$FE800`) |
| 16 | 4 + 4 | slow RAM (`$C00000`-`$DBFFFF`): lower, upper (0: none) |
| 24 | 4 + 4 | fast RAM (any other region; the last one exec lists): lower, upper (0: none) |

The bootblock's `MemDetect` reads exec's memory list (Kickstart calls a bootblock with `a6` =
ExecBase); the program copies it at start-up (`EnhInit`, to `EnhMachine`) and `ReadProfile`
decides the profile from it. `tools/test_bootinfo.py` checks it on seven machines.

### File record (`FENTRY`, in the program)

dest.l (load address), length.l, file id.w - 10 bytes. `LoadFile` takes `a1` = a record and
returns `a5` = the end of the loaded data and `a0` = `CUSTOM`, keeping the other registers.
