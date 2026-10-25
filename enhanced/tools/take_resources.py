"""Where the enhanced game's resources came from: they were copied from the original game
(original/) once, and since then they are the enhanced game's own, to change as it needs -
original/ stays the original game. This script records how each was made:

  python3 take_resources.py            (from anywhere) list the resources and whether each
                                       still matches the original it came from
  python3 take_resources.py --write    make them again from original/ (overwrites any change)

The resources (what build_game.py reads to make the disk):
  disk/files/           the graphics files the disk carries as they are: the loading picture, the
                        progress map and copyright screens, the sprites, BOBs, items, font and
                        each level's tiles (copies of original/disk/files/)
  sound/gng_sfx_512k.s  the 512K effects package and the 1MB music package (copies of
  sound/gng_music_1mb.s original/sound/), with their samples in sound/samples/
  data/level_map.bin    the map the level table files are made from (FORMATS.md): the original
  data/cell_tables.bin  512K program's LevelBounds, LevelMapTable and WorldMap with the bytes past
                        it that MapTileAt reads, and BlockTiles and CellTiles for every cell byte
                        as the original reads them (original/bin/main_512k.bin)

The tests still use original/ for the original game they compare the enhanced game with."""
import os, shutil, struct, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ENH = os.path.normpath(os.path.join(HERE, '..'))
ORIG = os.path.normpath(os.path.join(ENH, '..', 'original'))

DISK_FILES = ['t001-016_loading_screen.bin', 't033-036_arthur_sprites.bin', 't037_small_bob_sets.bin',
              't038-056_enemy_bobs.bin', 't057_item_gfx_part2.bin', 't058_enemy_shot_gfx.bin',
              't059-060_item_gfx.bin', 't061_font.bin', 't062-063_progress_map.rle',
              't082-083_copyright_screen.rle', 't084-088_level0_tiles.bin', 't089-096_level1_tiles.bin',
              't097-100_level2_tiles.bin', 't101-103_level3_tiles.bin', 't104-105_level4_tiles.bin',
              't106-107_level5_tiles.bin', 't108-109_level6_tiles.bin']
SOUND_FILES = ['gng_sfx_512k.s', 'gng_music_1mb.s']

# the original 512K program (loaded at $80): the level map and the cell tables
MAP_START, MAP_END = 0x4466, 0x44D6 + 0xB40   # LevelBounds .. WorldMap + MAP_LIMIT (FrameOffsets1)
BLOCK_TILES, CELL_TILES = 0x114, 0x1222C      # 64 bytes per cell, 256 bytes per cell


def copies():
    """[(resource, original)] for the files copied as they are"""
    out = [(os.path.join(ENH, 'disk', 'files', f), os.path.join(ORIG, 'disk', 'files', f)) for f in DISK_FILES]
    out += [(os.path.join(ENH, 'sound', f), os.path.join(ORIG, 'sound', f)) for f in SOUND_FILES]
    smp = os.path.join(ORIG, 'sound', 'samples')
    out += [(os.path.join(ENH, 'sound', 'samples', f), os.path.join(smp, f))
            for f in sorted(os.listdir(smp)) if f.endswith('.raw')]
    return out


def level_data():
    """{resource: bytes} for the data cut from the original program"""
    d = open(os.path.join(ORIG, 'bin', 'main_512k.bin'), 'rb').read()
    def mem(a, n):                       # the original's memory (zeros outside the program)
        return bytes(d[x - 0x80] if 0x80 <= x < 0x80 + len(d) else 0 for x in range(a, a + n))
    signed = lambda c: c - 256 if c >= 0x80 else c   # it indexes both tables with the byte sign extended
    cells = b''.join(mem(BLOCK_TILES + 64 * signed(c), 64) + mem(CELL_TILES + 256 * signed(c), 256) for c in range(256))
    return {os.path.join(ENH, 'data', 'level_map.bin'): mem(MAP_START, MAP_END - MAP_START),
            os.path.join(ENH, 'data', 'cell_tables.bin'): cells}


def main(args):
    write = '--write' in args
    made = {dst: open(src, 'rb').read() for dst, src in copies()}
    made.update(level_data())
    changed = 0
    for path, data in made.items():
        same = os.path.exists(path) and open(path, 'rb').read() == data
        if write and not same:
            os.makedirs(os.path.dirname(path), exist_ok=True)
            open(path, 'wb').write(data)
        changed += not same
        if not same or write:
            print(f'{"written" if write else "differs from the original"}: {os.path.relpath(path, ENH)}')
    print(f'{len(made)} resources, {changed} {"written" if write else "changed since they were taken"}')


if __name__ == '__main__':
    main(sys.argv[1:])
