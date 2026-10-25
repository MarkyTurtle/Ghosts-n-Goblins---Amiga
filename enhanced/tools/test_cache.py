"""The file cache and the level's enemy sets (support.s: CacheInit, LoadFile,
LoadEnemySets), from the disk image (tools/floppy.py) on each machine of compare_game.py: a game
started on a level, then the level loaded again (LoadLevel). Checks:
  * the cache's memory: none on a plain 512K machine; after the moved program on a machine with
    slow / fast RAM; above the upper chip RAM caches with 1MB of chip RAM;
  * loading the level again reads no track where the cache keeps its files (slow / fast RAM:
    all of them; 1MB of chip RAM: the tile and table files, the graphics are cached already),
    and as many as the first time on 512K;
  * the level's data (the level area: tables, tile file, the level's sets and masks) is the same
    after the second load;
  * with 1MB of chip RAM: the cache starts above the BOB viewer, which is loaded and unchanged.

  python3 test_cache.py [level]        (after build_game.py)"""
import hashlib, sys
import build_game, compare_game
from game import game, script_start


def run(mach, lv):
    (name, regions, vb, attn), build = compare_game.MACHINES[mach]
    m = game((regions, vb, attn), disk=True)
    m.boot()
    S = build_game.symbols(build_game.OUT + '/game.lst')
    for f, (j, fi) in enumerate(script_start()):
        m.frame(j, fi)
        if f == 60: m.w16(m.G['g_Level'], lv); r0 = m.floppy.reads
    for _ in range(10): m.frame()
    first = m.floppy.reads - r0
    area = lambda: hashlib.md5(bytes(m.u.mem_read(S['LEVEL_TABLES'], S['MFM_BUFFER'] - S['LEVEL_TABLES']))).digest()
    a = area()
    m.w8(m.G['g_SubState'], 0)                   # LoadLevel again
    r1 = m.floppy.reads
    for _ in range(10): m.frame()
    second = m.floppy.reads - r1
    ptr, end = m.r32(m.L['CachePtr']), m.r32(m.L['CacheEnd'])
    kept = [i for i in range(S['FID_COUNT']) if m.r32(m.L['CacheTable'] + 4 * i)]
    viewer = True
    if m.r8(m.L['ViewerOn']):                     # the BOB viewer (1MB of chip RAM): untouched
        code = open(build_game.OUT + '/viewer.bin', 'rb').read()
        viewer = (bytes(m.u.mem_read(S['VIEWER_ORG'], len(code))) == code
                  and ptr >= S['VIEWER_ORG'] + len(code))
    elif mach in ('1mb', 'ks13'):
        viewer = False
    return name, ptr, end, kept, first, second, a == area() and viewer


def main(lv):
    ok = True
    for mach, cache in (('512k', False), ('slow', True), ('fast', True), ('1mb', True), ('ks13', True)):
        name, ptr, end, kept, first, second, same = run(mach, lv)
        good = same and (second == 0 if cache else second == first and end == 0 and not kept)
        ok &= good
        where = f'{ptr:06X}-{end:06X}, {(end - ptr) // 1024} KB left, files {kept}' if end else 'none'
        print(f'  {"ok  " if good else "FAIL"} {name}: cache {where}; level {lv + 1}: {first} track reads, '
              f'again {second}; the level data (and the BOB viewer, 1MB) {"the same" if same else "DIFFERENT"}', flush=True)
    print('all as expected' if ok else 'FAILED')
    return ok


if __name__ == '__main__':
    sys.exit(0 if main(int(sys.argv[1]) if len(sys.argv) > 1 else 1) else 1)
