"""Build the one program for every machine (src/gng_game.s) and the sound packages it loads.

  cd enhanced/tools
  VASM=/path/to/vasmm68k_mot python3 build_game.py [--raster]

--raster: the timing build (RASTER_BUILD): the background colour shows which part of each frame
is running (grey logic, red new edges / restore, orange text, blue BOBs, yellow copper list,
green waiting for line $44, black idle); build/game_raster/, build/gng_game_raster.adf

Writes enhanced/build/game/:
  game.bin, game.lst   the main program (loaded to $80 on every machine)
  sfx.bin              the 512K effects package (sound/gng_sfx_512k.s), assembled for the
                       program's MUSIC_FILE - the memory map moves with the program's size
  music.bin            the 1MB music package (sound/gng_music_1mb.s), assembled for
                       MUSIC1M_FILE in upper chip RAM (loaded only with 1MB of chip RAM)
  boot.bin             the bootblock: the original with the memory survey (src/boot_patches.s),
                       always loading the one program to $80, from MAIN_TRACK
and enhanced/build/gng_game.adf: the disk (tools/disk/mkdisk.py --one): the program at tracks
MAIN_TRACK-, the effects package at 126, the music package at 64 (the original disk's places);
the two original main programs' tracks (17-32, 110-125) are left empty."""
import os, re, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ENH = os.path.join(HERE, '..')
ROOT = os.path.join(ENH, '..')
RASTER = '--raster' in sys.argv
OUT = os.path.join(ENH, 'build', 'game_raster' if RASTER else 'game')
VASM = os.environ.get('VASM', 'vasmm68k_mot')
TRACK_SFX, TRACK_MUSIC = 126, 64
MAIN_TRACK = 134                         # tracks no file of the original disk uses


def vasm(src, out, listing=None, defs=()):
    cmd = [VASM, '-Fbin', '-m68000', '-no-opt', '-quiet', '-I', os.path.join(ENH, 'src'), '-I', ROOT, '-o', out]
    if listing: cmd += ['-L', listing]
    cmd += [f'-D{k}={v}' for k, v in defs] + [src]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode: sys.exit(f'vasm {os.path.basename(src)}:\n{r.stdout}{r.stderr}')


def symbols(listing):
    text = open(listing).read()
    part = text[text.index('Symbols by name:'):text.index('Symbols by value:')]
    return {m.group(1): int(m.group(3), 16) for m in re.finditer(r'^(\S+)\s+([AE]):([0-9A-F]+)$', part, re.M)}


def build(extra_defs=()):
    os.makedirs(OUT, exist_ok=True)
    prog, lst = os.path.join(OUT, 'game.bin'), os.path.join(OUT, 'game.lst')
    vasm(os.path.join(ENH, 'src', 'gng_game.s'), prog, lst, extra_defs)
    syms = symbols(lst)
    sfx, music = os.path.join(OUT, 'sfx.bin'), os.path.join(OUT, 'music.bin')
    vasm(os.path.join(ROOT, 'sound', 'gng_sfx_512k.s'), sfx, defs=(('SND_ORG', syms['MUSIC_FILE']),))
    vasm(os.path.join(ROOT, 'sound', 'gng_music_1mb.s'), music, defs=(('SND_ORG', syms['MUSIC1M_FILE']),))
    end = 0x80 + os.path.getsize(prog)
    # layout checks the assembler cannot make where the symbols are defined (the map moves with
    # the program, so it is only known at the end)
    checks = [('the program file runs past the globals block?', end <= syms['GlobalsBlock'] + 0x1780),
              ('the scroller code is inside the program file', syms['ScrDrawBob'] < syms['GlobalsBlock']),
              ("the scroller's buffers end before its storage", syms['SCREEN_0'] + 3 * 47120 <= syms['SCROLL_STORE']),
              ("the scroller's storage ends before the HUD area", syms['ScrollStoreEnd'] <= syms['CLEAR_AREA'])]
    for what, ok in checks:
        if not ok: sys.exit('layout: ' + what + ' - no')
    print(f'game.bin {os.path.getsize(prog):,} bytes ($80-${end:X}); globals ${syms["GlobalsBlock"]:X}, '
          f'memory map from ${syms["MAP_LOW"]:X} (screens ${syms["SCREEN_0"]:X}, level file ${syms["LEVEL_FILE"]:X}); '
          f'effects package for ${syms["MUSIC_FILE"]:X}, music package for ${syms["MUSIC1M_FILE"]:X}')
    return prog, lst, {TRACK_SFX: sfx, TRACK_MUSIC: music}, syms


def bootblock(length):
    """the enhanced bootblock (the memory survey), loading the one program: always to $80 (the
    two memory tests replaced, as for the 512K-only disk), length bytes from MAIN_TRACK"""
    import build_enh
    boot = build_enh.build_boot(os.path.join(OUT, 'boot'))
    for off, old, new in ((0x2C, '20380004', '70004e71'),                 # move.l $4.w,d0 -> moveq #0,d0
                          (0x40, '203c00080000', '70004e714e71'),          # move.l #$80000,d0 -> moveq #0,d0
                          (0x14E, '2a3c00018a80', '2a3c%08x' % length),    # main program length
                          (0x172, '31fc006e0028', '31fc%04x0028' % MAIN_TRACK),   # its track (512K path)
                          (0x17C, '31fc00110028', '31fc%04x0028' % MAIN_TRACK)):  # (and the 1MB path)
        assert boot[off:off+len(old)//2].hex() == old, f'bootblock ${off:X}'
        boot[off:off+len(new)//2] = bytes.fromhex(new)
    path = os.path.join(OUT, 'boot.bin')
    open(path, 'wb').write(boot)
    return path, bytes(boot)


def make_disk(prog, sound):
    import build_enh
    boot, bootbytes = bootblock(os.path.getsize(prog))
    adf = os.path.abspath(os.path.join(OUT, '..', 'gng_game_raster.adf' if RASTER else 'gng_game.adf'))
    args = [sys.executable, os.path.join('tools', 'disk', 'mkdisk.py'), '-o', adf, '--boot', os.path.abspath(boot),
            '--one', os.path.abspath(prog), '--file', f'{TRACK_SFX}={os.path.abspath(sound[TRACK_SFX])}',
            '--add', f'{TRACK_MUSIC}={os.path.abspath(sound[TRACK_MUSIC])}']
    r = subprocess.run(args, cwd=ROOT, capture_output=True, text=True)
    print(r.stdout + r.stderr, end='')
    if r.returncode: sys.exit('mkdisk failed')
    build_enh.verify_image(adf, bootbytes, {MAIN_TRACK: prog, TRACK_SFX: sound[TRACK_SFX], TRACK_MUSIC: sound[TRACK_MUSIC]})
    return adf


if __name__ == '__main__':
    prog, lst, sound, syms = build((('RASTER_BUILD', 1),) if RASTER else ())
    make_disk(prog, sound)
