"""Run the one program for every machine (build_game.py) side by side with the original it
stands in for, in the emulator, with the same input (the 512K original drawing every frame and
with its DrawBob top-clip bug fixed, both originals with the one program's MapTileAt fix):

  --machine 512k   an A500 with 512K of chip RAM   against the original 512K program
  --machine 1mb    an A500+ with 1MB of chip RAM   against the original 1MB program
  --machine ks13   an A500 with 1MB chip, Kickstart 1.3 ($FE800)  against the original 1MB program
  --machine slow   an A500 with 512K chip + 512K slow RAM  against the original 1MB program
  --machine fast   512K chip + 1.5MB slow + 2MB fast RAM   against the original 1MB program

The game state must stay the same every frame and so must the picture (compare_runs.py does
the comparing; the camera tables are not compared byte for byte, as they hold pointers).

  python3 compare_game.py [frames] [seed] --machine 512k|1mb [--level N] [--teleport N] [--png DIR] [--disk]
(--disk: the one program loads its files from the disk image with its own loader, tools/floppy.py)"""
import sys
import compare_runs, test_bootinfo
from game import GameRun, game

M = {m[0]: m for m in test_bootinfo.MACHINES}
MACHINES = {# 512K chip: the music too (the 512K music package), so the 1MB program's sound and
            # profile logic: compared with that, as the expanded 512K machines (the pictures are the
            # 512K program's either way)
            '512k': (M['A500 512K chip'], '1mb'), '1mb': (M['A500+ 1MB chip'], '1mb'),
            # Kickstart 1.3 lists a 1MB machine's chip RAM as ending at $FE800
            'ks13': (M['A500 1MB chip, Kickstart 1.3'], '1mb'),
            # 512K chip + 512K slow: the program moves to slow RAM and loads the music where it was
            # (EnhRelocate): the sound code is the 1MB program's, so it is compared with that
            'slow': (M['A500 512K chip + 512K slow'], '1mb'),
            'fast': (M['A500 + 1.5MB slow + 2MB fast'], '1mb')}


def main(frames, seed, machine, level=None, teleport=0, png=None, disk=False):
    (name, regions, vb, attn), build = MACHINES[machine]
    print(f'the one program on "{name}" against the original {build} program')
    ref, test = GameRun(build=build), game((regions, vb, attn), disk=disk)
    if build == '1mb':
        # The globals overlay the end of the program file, and the game uses some before it sets
        # them (the fraction of g_ArthurX in the opening scene, for one): with the 1MB file's
        # tail Arthur reaches his armour a frame later. Give the original the same starting junk
        # as the one program (its globals from +2 on are 4 bytes further on: g_BaseAddr).
        n = 0x1780
        junk = bytes(test.u.mem_read(test.globals - test.reloc, n))     # (a program that moves itself
                                                                        # takes them along: EnhRelocate)
        ref.u.mem_write(ref.globals, junk[:2]); ref.u.mem_write(ref.globals + 6, junk[2:])
    if build == '512k':     # as the enhanced builds were always compared (compare_runs.py): the
        ref.u.mem_write(0xBAF4, bytes.fromhex('c4c6'))    # DrawBob top-clip fix, the one program
        ref.u.mem_write(0xC2EA, bytes.fromhex('c4c6'))    # draws BOBs correctly (scroller)
        ref.u.mem_write(0x6E76, bytes.fromhex('4e71' * 5))  # every frame drawn, as the one program
    fix_map_reads(ref, test)
    return compare_runs.main(frames, seed, png, level, teleport, build, pair=(ref, test), raw=False)


def fix_map_reads(ref, test):
    """the one program's MapTileAt fix, in the original: a cell read at or past the BOB frame
    tables (where the programs' contents start to differ) reads the empty cell $67 instead"""
    from unicorn import UC_HOOK_CODE
    limit = test.L['FrameOffsets1'] - test.L['WorldMap']
    empty = ref.L['WorldMap'] + bytes(ref.u.mem_read(ref.L['WorldMap'], 0x161)).index(b'\x67')
    at, wm = ref.L['MapTileAt'] + 0x12, ref.L['WorldMap']           # move.b (a1),d0
    assert bytes(ref.u.mem_read(at, 2)) == b'\x10\x11'
    def hook(uc, a, sz, ud):
        if ref.reg('a1') >= wm + limit: ref.reg('a1', empty)
    ref.u.hook_add(UC_HOOK_CODE, hook, begin=at, end=at)


if __name__ == '__main__':
    a = [x for x in sys.argv[1:] if x != '--disk']
    opt = lambda k, d=None, f=str: f(a[a.index(k) + 1]) if k in a else d
    args = [x for i, x in enumerate(a) if not x.startswith('--') and (i == 0 or not a[i - 1].startswith('--'))]
    sys.exit(main(int(args[0]) if args else 2000, int(args[1]) if len(args) > 1 else 1, opt('--machine', '512k'),
                  opt('--level', None, int), opt('--teleport', 0, int), opt('--png'), '--disk' in sys.argv))
