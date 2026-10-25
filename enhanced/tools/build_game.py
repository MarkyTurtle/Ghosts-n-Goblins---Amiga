"""Build the one program for every machine (src/gng_game.s) and the sound packages it loads.

  cd enhanced/tools
  VASM=/path/to/vasmm68k_mot python3 build_game.py [--raster]

--raster: the timing build (RASTER_BUILD): the background colour shows which part of each frame
is running (grey logic, red new edges / restore, orange text, blue BOBs, yellow copper list,
green waiting for line $44, black idle); build/game_raster/, build/gng_game_raster.adf
--nasty-wait: blitter priority only while waiting for the blitter (NASTY_WAIT, scroll.s);
build/game_nastywait/ (with --raster: game_raster_nastywait/), build/gng_game_nastywait.adf
--music-rate N/D: the 512K music package with the tunes' sampled instruments at N/D of their
rate (enhanced/sound/tools/make_music_512k.py --rate; smaller, so the level area gets the difference);
build/game_musicN_D/, build/gng_game_musicN_D.adf

Writes enhanced/build/game/:
  game.bin, game.lst   the main program (loaded to $80 on every machine)
  sfx.bin              the 512K effects package (sound/gng_sfx_512k.s), assembled for the
                       program's MUSIC_FILE - the memory map moves with the program's size
  music.bin            the 1MB music package (sound/gng_music_1mb.s), assembled for
                       MUSIC1M_FILE in upper chip RAM (loaded only with 1MB of chip RAM)
  boot.bin             the bootblock (src/boot_4489.s): the memory survey, the loading picture
                       and the program, loaded with the 4489_byteloader through the file table
and enhanced/build/gng_game.adf: an ordinary 880K AmigaDOS-format disk (no filesystem): the
bootblock, the file table at $400 (FT_OFFSET: 'GNGF', version, count, then offset and length of
each file, in the order of disk_files() and the FID_ equates of gng_game.i), then the files."""
import os, re, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ENH = os.path.join(HERE, '..')
ROOT = os.path.join(ENH, '..', 'original')  # the original game's folder (original/: its sources, tools, files)
ENH_SND = os.path.join(ENH, 'sound')                 # the enhanced game's sound: the 512K music package
RASTER = '--raster' in sys.argv
NASTY = '--nasty-wait' in sys.argv
MUSIC_RATE = sys.argv[sys.argv.index('--music-rate') + 1] if '--music-rate' in sys.argv else None
VARIANT = (('_raster' if RASTER else '') + ('_nastywait' if NASTY else '')
           + (f'_music{MUSIC_RATE.replace("/", "_")}' if MUSIC_RATE else ''))
OUT = os.path.join(ENH, 'build', 'game' + VARIANT)
M512_SRC = (os.path.join(OUT, 'gng_music_512k.s') if MUSIC_RATE        # (the committed one: full quality)
            else os.path.join(ENH_SND, 'gng_music_512k.s'))
VASM = os.environ.get('VASM', 'vasmm68k_mot')
ADF_SIZE = 901120                        # 80 cylinders x 2 heads x 11 sectors x 512 bytes
FT_OFFSET, FT_VERSION = 0x400, 1         # the file table (gng_game.i FT_OFFSET, boot_4489.s)
FILES_START = 0x600


def vasm(src, out, listing=None, defs=(), incl=None):
    """assemble src to out (vasm, -Fbin -no-opt) with the include paths the game needs and -D
    for each (name, value) in defs; the listing too if asked; stops the build on an error"""
    cmd = [VASM, '-Fbin', '-m68000', '-no-opt', '-quiet', '-I', os.path.join(ENH, 'src'), '-I', ROOT,
           '-I', os.path.join(ROOT, 'sound'), '-I', ENH_SND, '-o', out] + (['-I', incl] if incl else [])
    if listing: cmd += ['-L', listing]
    cmd += [f'-D{k}={v}' for k, v in defs] + [src]
    try:
        r = subprocess.run(cmd, capture_output=True, text=True)
    except FileNotFoundError:
        sys.exit(f'{VASM} not found: put vasmm68k_mot on the PATH, or set VASM to its full path')
    if r.returncode: sys.exit(f'vasm {os.path.basename(src)}:\n{r.stdout}{r.stderr}')


def symbols(listing):
    text = open(listing).read()
    part = text[text.index('Symbols by name:'):text.index('Symbols by value:')]
    return {m.group(1): int(m.group(3), 16) for m in re.finditer(r'^(\S+)\s+([AE]):([0-9A-F]+)$', part, re.M)}


RELOC_DELTA = 0x200000                   # the relocation pass assembles 2MB further on


def relocations(a, b, what, lst=None):
    """the offsets of the longs that differ by RELOC_DELTA between two assemblies of the same
    source at two origins (everything else must be the same)"""
    import struct
    assert len(a) == len(b), what
    offs, i = [], 0
    while i < len(a) - 1:
        if a[i:i+2] == b[i:i+2]: i += 2; continue
        va, vb = struct.unpack_from('>L', a, i)[0], struct.unpack_from('>L', b, i)[0]
        if (vb - va) & 0xFFFFFFFF != RELOC_DELTA:
            sys.exit(f'{what}: offset ${i:X} (address ${0x80 + i:X}) is not a 32-bit address of the program '
                     f'(${va:08X} / ${vb:08X})')
        offs.append(i); i += 4
    return offs


def reloc_table(offs):
    """a relocation table (FORMATS.md): count.l, then the word gap from the previous offset to
    each (the first from 0)"""
    import struct
    out, prev = bytearray(struct.pack('>L', len(offs))), 0
    for o in offs:
        assert 0 < o - prev < 0x10000 or (prev == 0 and o < 0x10000), (o, prev)
        out += struct.pack('>H', o - prev); prev = o
    return bytes(out)




MAP_LIMIT = 0xB40                         # FrameOffsets1 - WorldMap: the map bytes MapTileAt reads


def level_tables():
    """the per-level map table files (LoadLevelTables), from the original 512K program's
    BlockTiles and CellTiles -> (slots, [file bytes]). A level reads the map at
    g_MapPtr + (X >> 8) + (Y >> 8) * 32 (MapTileAt, the scroll), so a level's cells are the
    bytes at its origin (LevelMapTable) plus its size (LevelBounds) in cells, one cell more
    on every side (Arthur and the look-ahead at the edges), and columns 254 and 255 of each
    of those rows (a small negative X, an object going off the left edge, gives X >> 8 = 255).
    Bytes past the map that MapTileAt reads (up to FrameOffsets1) count as cells too, with
    the tables the original reads for them: it indexes both tables with the byte sign
    extended, so cell $FA reads 6 entries before the start (zeros below the program).
    Cell $67 (empty) takes slot 0, and so does a cell the level never reads."""
    import struct
    D = open(os.path.join(ROOT, 'bin', 'main_512k.bin'), 'rb').read(); B = 0x80
    WM, LMT, LB, BT, CT = 0x44D6, 0x44BA, 0x4466, 0x114, 0x1222C
    LIMIT = MAP_LIMIT                     # FrameOffsets1 - WorldMap (checked against the build)
    rw = lambda a: struct.unpack('>H', D[a-B:a-B+2])[0]
    def mem(a, n):                        # the original's memory (zeros outside the program)
        return bytes(D[x-B] if B <= x < B + len(D) else 0 for x in range(a, a + n))
    sets = []
    for l in range(7):
        org = LMT + rw(LMT + 2*l)
        x0, x1, y1, y0 = D[LB-B+4*l:LB-B+4*l+4]
        cols = list(range(-1, x1 - x0 + 2)) + [254, 255]
        cells = {D[a-B] if a < WM + LIMIT else 0x67
                 for cy in range(-1, y1 - y0 + 2) for cx in cols for a in [org + cx + 32*cy]}
        cells.discard(0x67)
        sets.append([0x67] + sorted(cells))
    slots = max(len(c) for c in sets)
    files = []
    for cells in sets:
        slot = bytearray(256)
        for i, c in enumerate(cells): slot[c] = i
        blocks = bytearray(64 * slots); tiles = bytearray()
        for i, c in enumerate(cells):
            sc = c - 256 if c >= 0x80 else c
            blocks[64*i:64*i+64] = mem(BT + 64*sc, 64)
            tiles += mem(CT + 256*sc, 256) if c != 0x67 else bytes(256)
        files.append(bytes(slot + blocks + tiles))
    return slots, files


def build(extra_defs=()):
    """the whole build into OUT: the level table files, the sound packages, the program (and its
    relocation file: the program assembled again at RELOC_ORG), the layout checks, the stage
    plan, the bootblock and the disk image"""
    os.makedirs(OUT, exist_ok=True)
    prog, lst = os.path.join(OUT, 'game.bin'), os.path.join(OUT, 'game.lst')
    src = os.path.join(ENH, 'src', 'gng_game.s')
    slots, tables = level_tables()
    tdefs = [('TBL_SLOTS', slots)]
    for l, data in enumerate(tables):
        path = os.path.join(OUT, f'tables{l}.bin')
        open(path, 'wb').write(data)
        tdefs += [(f'TBLLEN{l}', len(data))]
    # the 512K music package (enhanced/sound/tools/make_music_512k.py): its length for the program's file
    # record (the same wherever it is assembled; it is assembled again for MUSIC_FILE below)
    subprocess.run([sys.executable, os.path.join(ENH_SND, 'tools', 'make_music_512k.py')]
                   + (['--rate', MUSIC_RATE, '--out', M512_SRC] if MUSIC_RATE else []), check=True, capture_output=True)
    music512 = os.path.join(OUT, 'music512.bin')
    vasm(M512_SRC, music512)
    tdefs += [('MUSIC512_LEN', os.path.getsize(music512))]
    extra_defs = tuple(extra_defs) + tuple(tdefs)
    print(f'level tables: {slots} cells at most, {", ".join(f"{len(t):,}" for t in tables)} bytes')
    vasm(src, prog, lst, extra_defs)
    syms = symbols(lst)
    # the BOB viewer (src/bobviewer.s, 1MB of chip RAM only): assembled for VIEWER_ORG with the
    # program's symbols; the program then again with its length (nothing in it moves)
    viewer = os.path.join(OUT, 'viewer.bin')
    with open(os.path.join(OUT, 'viewer_syms.i'), 'w') as f:
        f.write('; the program\'s symbols for bobviewer.s (build_game.py writes this)\n')
        for k, v in sorted(syms.items()):
            if re.fullmatch(r'[A-Za-z_]\w*', k): f.write(f'{k}\tequ\t${v:X}\n')
    vasm(os.path.join(ENH, 'src', 'bobviewer.s'), viewer, os.path.join(OUT, 'viewer.lst'),
         defs=(('VIEWER_BUILD', 1),), incl=OUT)
    extra_defs = tuple(extra_defs) + (('VIEWER_LEN', os.path.getsize(viewer)),)
    vasm(src, prog, lst, extra_defs)
    s2 = symbols(lst)
    if any(s2.get(k) != v for k, v in syms.items() if k not in ('VIEWER_LEN',)):
        sys.exit('the program moved when the viewer\'s length went in')
    syms = s2
    if syms['FrameOffsets1'] - syms['WorldMap'] != MAP_LIMIT:
        sys.exit('MAP_LIMIT is not FrameOffsets1 - WorldMap: the level tables would miss cells')
    sfx, music = os.path.join(OUT, 'sfx.bin'), os.path.join(OUT, 'music.bin')
    vasm(os.path.join(ROOT, 'sound', 'gng_sfx_512k.s'), sfx, defs=(('SND_ORG', syms['MUSIC_FILE']),))
    vasm(os.path.join(ROOT, 'sound', 'gng_music_1mb.s'), music, defs=(('SND_ORG', syms['MUSIC1M_FILE']),))
    vasm(M512_SRC, music512, defs=(('SND_ORG', syms['MUSIC_FILE']),))
    # the relocation file (EnhRelocate): the program assembled 2MB on with the memory map where
    # it is, and the music package likewise; then the program again with the file's length
    moved, music2 = os.path.join(OUT, 'moved.bin'), os.path.join(OUT, 'music_moved.bin')
    vasm(src, moved, defs=tuple(extra_defs) + (('RELOC_ORG', 0x80 + RELOC_DELTA), ('MAP_FIX', syms['MAP_LOW'])))
    vasm(os.path.join(ROOT, 'sound', 'gng_music_1mb.s'), music2, defs=(('SND_ORG', syms['MUSIC1M_FILE'] + RELOC_DELTA),))
    rp = relocations(open(prog, 'rb').read(), open(moved, 'rb').read(), 'the program')
    rm = relocations(open(music, 'rb').read(), open(music2, 'rb').read(), 'the music package')
    relocs = os.path.join(OUT, 'relocs.bin')
    open(relocs, 'wb').write(reloc_table(rp) + reloc_table(rm))
    vasm(src, prog, lst, tuple(extra_defs) + (('RELOC_LEN', os.path.getsize(relocs)),))
    syms = symbols(lst)
    print(f'relocations: {len(rp):,} in the program, {len(rm):,} in the music package ({os.path.getsize(relocs):,} bytes)')
    end = 0x80 + os.path.getsize(prog)
    # layout checks the assembler cannot make where the symbols are defined (the map moves with
    # the program, so it is only known at the end)
    checks = [('the program file runs past the globals block?', end <= syms['GlobalsBlock'] + 0x1780),
              ('the scroller code is inside the program file', syms['ScrDrawBob'] < syms['GlobalsBlock']),
              ("the scroller's buffers end before its storage", syms['SCREEN_0'] + 3 * 47120 <= syms['SCROLL_STORE']),
              ("the scroller's storage ends before the HUD area", syms['ScrollStoreEnd'] <= syms['CLEAR_AREA']),
              ("the music package fits where the program was and the effects package's area (MUSICB_FILE)",
               syms['MUSICB_FILE'] + os.path.getsize(music) <= syms['MAP_LOW'] + syms['SFX_AREA']),
              ("the 512K effects package fits its area", os.path.getsize(sfx) <= syms['SFX_AREA']),
              ("the 512K music package fits its area", os.path.getsize(music512) <= syms['SFX_AREA']),
              ("the BOB viewer fits below $FE800 (Kickstart 1.3's top of a 1MB machine's chip RAM)",
               syms['VIEWER_ORG'] + os.path.getsize(viewer) <= 0xFE800),
              ("the text strip is after the buffers and holds 28 characters",
               syms['TEXT_STRIP'] >= syms['SCREEN_0'] + 3 * 47120 and syms['STRIP_MAX'] >= 28)]
    import struct as _st
    _d = open(prog, 'rb').read()
    _files = [_st.unpack_from('>L', _d, syms[f'FileLevel{n}'] + 4 - 0x80)[0] for n in range(7)]
    _load_top = syms['LEVEL_FILE'] + max(_files)
    checks.append((f'the level files load (up to ${_load_top:X}) below LoadFile\'s MFM buffer '
                   f'(${syms["MFM_BUFFER"]:X}-${syms["LEVEL_GFX_LIMIT"]:X})',
                   _load_top <= syms['MFM_BUFFER'] and syms['MFM_BUFFER'] + syms['MFM_BYTES'] <= syms['LEVEL_GFX_LIMIT']))
    checks.append(('the progress map and its MFM buffer stay in the first screen (the map is unpacked above it)',
                   syms['PM_MFM'] + syms['MFM_BYTES'] <= syms['SCREEN_1']))
    top = level_data_top(prog, syms)
    checks.append((f'the level data (file, BOB sets, masks; worst ${top:X}) ends below LEVEL_GFX_LIMIT',
                   top <= syms['LEVEL_GFX_LIMIT']))
    for what, ok in checks:
        if not ok: sys.exit('layout: ' + what + ' - no')
    print(f'level data up to ${top:X} with no image pre-masked')
    for lv, (top_lv, left) in enumerate(level_plan(prog, syms)):
        print(f'  stage {lv + 1}: data to ${top_lv:X}; 5 blits for: {", ".join(left) or "nothing"}')
    print(f'game.bin {os.path.getsize(prog):,} bytes ($80-${end:X}); globals ${syms["GlobalsBlock"]:X}, '
          f'memory map from ${syms["MAP_LOW"]:X} (screens ${syms["SCREEN_0"]:X}, level file ${syms["LEVEL_FILE"]:X}); '
          f'effects package for ${syms["MUSIC_FILE"]:X}, music package for ${syms["MUSIC1M_FILE"]:X}')
    files = disk_files(prog, sfx, music, relocs)
    print(f'512K music package {os.path.getsize(music512):,} bytes (effects alone {os.path.getsize(sfx):,})')
    check_records(src, syms, files)
    return prog, lst, files, syms


def disk_files(prog, sfx, music, relocs, out=None):
    """the disk's files, in file id order (gng_game.i FID_...): [(name, path)]"""
    out = out or OUT
    D = lambda f: os.path.join(ROOT, 'disk', 'files', f)
    return ([('program', prog), ('loading picture', D('t001-016_loading_screen.bin')),
             ("Arthur's sprites", D('t033-036_arthur_sprites.bin')), ('small BOBs', D('t037_small_bob_sets.bin')),
             ('enemy BOBs', D('t038-056_enemy_bobs.bin')), ('items 2', D('t057_item_gfx_part2.bin')),
             ('enemy shots', D('t058_enemy_shot_gfx.bin')), ('items', D('t059-060_item_gfx.bin')),
             ('font', D('t061_font.bin')), ('progress map', D('t062-063_progress_map.rle')),
             ('music (1MB package)', music), ('copyright screen', D('t082-083_copyright_screen.rle'))]
            + [(f'level {l} tiles', D(f)) for l, f in enumerate(
                ['t084-088_level0_tiles.bin', 't089-096_level1_tiles.bin', 't097-100_level2_tiles.bin',
                 't101-103_level3_tiles.bin', 't104-105_level4_tiles.bin', 't106-107_level5_tiles.bin',
                 't108-109_level6_tiles.bin'])]
            + [('effects (512K package)', sfx), ('relocations', relocs)]
            + [(f'level {l} map tables', os.path.join(out, f'tables{l}.bin')) for l in range(7)]
            + [('music (512K package)', os.path.join(out, 'music512.bin'))]
            + [('BOB viewer (1MB)', os.path.join(out, 'viewer.bin'))])


def check_records(src, syms, files):
    """every file record (FENTRY) with a number for its length asks for its file's length (the
    records in gng_game.s and the files it includes)"""
    if len(files) != syms['FID_COUNT']: sys.exit('disk_files() and the FID_ equates disagree')
    text = '\n'.join(open(os.path.join(os.path.dirname(src), f)).read() for f in ('gng_game.s', 'support.s', 'scroller.s'))
    for m in re.finditer(r'^\tFENTRY\t[^,\n]+,\$([0-9A-F]+),(FID_\w+)(?:\+(\d))?', text, re.M):
        fid = syms[m.group(2)] + int(m.group(3) or 0)
        name, path = files[fid]
        if int(m.group(1), 16) != os.path.getsize(path):
            sys.exit(f'the file record for {name} asks for ${m.group(1)} bytes; the file has {os.path.getsize(path):,}')


def level_data_top(prog, syms):
    """the highest address the 512K profile fills when a level loads: the level file at
    LEVEL_FILE, the level's BOB sets copied after it (BuildFrameTable), then their masks"""
    import struct
    d = open(prog, 'rb').read()
    r = lambda a, f: struct.unpack_from(f, d, a - 0x80)
    sizes, masks = r(syms['BobSetSizes'], '>21H'), r(syms['LevelBobSetMask'], '>7L')
    ss, sm = r(syms['SmallBobSetSizes'], '>10H'), r(syms['LevelSmallBobMask'], '>7H')
    files = [r(syms[f'FileLevel{n}'] + 4, '>L')[0] for n in range(7)]
    def top(lv):
        sets = sum(sizes[i] for i in range(21) if masks[lv] >> i & 1) + sum(ss[i] for i in range(10) if sm[lv] >> i & 1)
        # then the one-plane masks (BuildLevelMasks): a fifth of the sets and of the item graphics
        return syms['LEVEL_FILE'] + files[lv] + sets + sets // 5 + 2 + (0x1234 + 0x1AC2 + 0xEA6) // 5
    return max(top(lv) for lv in range(7))


def level_plan(prog, syms):
    """what BuildLevelMasks pre-masks on each level (as the program decides it: GfxPriority while
    the room up to LEVEL_GFX_LIMIT lasts) -> per level (end of the data, the images left with
    one-plane masks)"""
    import struct
    d = open(prog, 'rb').read()
    r = lambda a, f: struct.unpack_from(f, d, a - 0x80)
    sizes, masks = r(syms['BobSetSizes'], '>21H'), r(syms['LevelBobSetMask'], '>7L')
    ss, sm = r(syms['SmallBobSetSizes'], '>10H'), r(syms['LevelSmallBobMask'], '>7H')
    files = [r(syms[f'FileLevel{n}'] + 4, '>L')[0] for n in range(7)]
    pri = d[syms['GfxPriority'] - 0x80:]
    pri = pri[:pri.index(0xFF)]
    r1 = syms['ESHOT_LEN'] + syms['ITEM_LEN']
    plan = []
    for lv in range(7):
        def size(c):
            if c == 0x40: return syms['ESHOT_LEN'], 2 * syms['ESHOT_LEN'], 'enemy shots'
            if c == 0x41: return syms['ITEM_LEN'], 2 * syms['ITEM_LEN'], 'items/weapons'
            if c >= 0x20:
                n = ss[c - 0x20] if sm[lv] >> (c - 0x20) & 1 else 0
                return n, n - n // 5, f'small set {c - 0x20}'
            n = sizes[c] if masks[lv] >> c & 1 else 0
            return n, n - n // 5, f'set {c}'
        s2 = sum(sizes[i] for i in range(21) if masks[lv] >> i & 1) + sum(ss[i] for i in range(10) if sm[lv] >> i & 1)
        end = syms['LEVEL_FILE'] + files[lv] + s2 + s2 // 5 + r1 // 5 + 4
        left = []
        for c in pri:
            n, cost, name = size(c)
            if not n: continue
            if end + cost <= syms['LEVEL_GFX_LIMIT']: end += cost
            else: left.append(name)
        plan.append((end, left))
    return plan


def bootblock():
    """the bootblock (src/boot_4489.s), with its checksum"""
    import struct
    path = os.path.join(OUT, 'boot.bin')
    vasm(os.path.join(ENH, 'src', 'boot_4489.s'), path)
    boot = bytearray(open(path, 'rb').read())
    assert len(boot) == 1024 and boot[:4] == b'DOS\0'
    boot[4:8] = bytes(4)
    s = 0
    for i in range(0, 1024, 4):
        s += struct.unpack_from('>L', boot, i)[0]
        if s > 0xFFFFFFFF: s = (s & 0xFFFFFFFF) + 1
    struct.pack_into('>L', boot, 4, ~s & 0xFFFFFFFF)
    open(path, 'wb').write(boot)
    return path, bytes(boot)


def make_disk(prog, files):
    """the disk: bootblock, file table, files (ADF, 901,120 bytes)"""
    import struct
    boot, bootbytes = bootblock()
    adf = bytearray(ADF_SIZE)
    adf[:1024] = bootbytes
    table, pos = bytearray(struct.pack('>4sHH8x', b'GNGF', FT_VERSION, len(files))), FILES_START
    for name, path in files:
        data = open(path, 'rb').read()
        if pos + len(data) > ADF_SIZE: sys.exit(f'the disk is full at {name}')
        adf[pos:pos + len(data)] = data
        table += struct.pack('>LL', pos, len(data))
        pos = (pos + len(data) + 1) & ~1
    assert len(table) <= FILES_START - FT_OFFSET
    adf[FT_OFFSET:FT_OFFSET + len(table)] = table
    path = os.path.abspath(os.path.join(OUT, '..', f'gng_game{VARIANT}.adf'))
    open(path, 'wb').write(adf)
    # read it back as the loaders do: the table, then each file by its offset and length
    back = open(path, 'rb').read()
    magic, ver, n = struct.unpack_from('>4sHH', back, FT_OFFSET)
    assert magic == b'GNGF' and n == len(files)
    for i, (name, f) in enumerate(files):
        off, ln = struct.unpack_from('>LL', back, FT_OFFSET + 16 + 8 * i)
        assert back[off:off + ln] == open(f, 'rb').read(), name
    print(f'{os.path.basename(path)}: {len(files)} files, {pos - FILES_START:,} bytes of {ADF_SIZE - FILES_START:,} '
          f'({ADF_SIZE - pos:,} free); the files read back exactly')
    return path


if __name__ == '__main__':
    prog, lst, files, syms = build((('RASTER_BUILD', 1),) * RASTER + (('NASTY_WAIT', 1),) * NASTY)
    make_disk(prog, files)
