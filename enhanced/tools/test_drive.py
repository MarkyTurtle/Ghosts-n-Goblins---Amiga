"""The game loading from the drive it was booted from (support.s: LoadDisk; the
bootblock leaves the drive in the machine description, version 2: boot_4489.s MI_DRIVE).
The disk image in DF0 and in DF1 (tools/floppy.py: the other drives are empty), on each machine
of compare_game.py: the game started and a level loaded from the disk. Checks: the loads read
the disk in the drive booted from (DF1: no load hangs on the empty DF0), the game reaches the
level, and the level's data (the level area: tables, tile file, the level's sets and masks) is
the same as when booted from DF0. A version-1 description (an older bootblock) means DF0.

  python3 test_drive.py [level]        (after build_game.py)"""
import hashlib, sys
import build_game, compare_game
from game import game, script_start


def run(mach, lv, drive):
    (name, regions, vb, attn), build = compare_game.MACHINES[mach]
    m = game((regions, vb, attn), disk=True, drive=drive)
    m.boot()
    S = build_game.symbols(build_game.OUT + '/game.lst')
    for f, (j, fi) in enumerate(script_start()):
        m.frame(j, fi)
        if f == 60: m.w16(m.G['g_Level'], lv)
    for _ in range(10): m.frame()
    area = hashlib.md5(bytes(m.u.mem_read(S['LEVEL_TABLES'], S['MFM_BUFFER'] - S['LEVEL_TABLES']))).digest()
    return name, m.floppy.reads, m.g('g_GameState', 1), m.g('g_Level', 2), area


def main(lv):
    ok = True
    for mach in ('512k', 'slow', '1mb'):
        base = run(mach, lv, None)                  # a version-1 description: DF0
        for drive in (0, 1):
            name, reads, state, level, area = run(mach, lv, drive)
            good = reads > 0 and state == 0 and level == lv and area == base[4]
            ok &= good
            print(f'  {"ok  " if good else "FAIL"} {name}: booted from DF{drive}: {reads} track reads, '
                  f'level {level + 1} {"playing" if state == 0 else f"state {state}"}, the level data '
                  f'{"as from DF0 (version 1)" if area == base[4] else "DIFFERENT"}', flush=True)
    print('all as expected' if ok else 'FAILED')
    return ok


if __name__ == '__main__':
    sys.exit(0 if main(int(sys.argv[1]) if len(sys.argv) > 1 else 1) else 1)
