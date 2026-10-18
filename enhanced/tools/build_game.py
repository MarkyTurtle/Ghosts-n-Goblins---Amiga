"""Build the one program for every machine (src/gng_game.s) and the sound packages it loads.

  cd enhanced/tools
  VASM=/path/to/vasmm68k_mot python3 build_game.py

Writes enhanced/build/game/:
  game.bin, game.lst   the main program (loaded to $80 on every machine)
  sfx.bin              the 512K effects package (sound/gng_sfx_512k.s), assembled for the
                       program's MUSIC_FILE - the memory map moves with the program's size
  music.bin            the 1MB music package (sound/gng_music_1mb.s), assembled for
                       MUSIC1M_FILE in upper chip RAM (loaded only with 1MB of chip RAM)"""
import os, re, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ENH = os.path.join(HERE, '..')
ROOT = os.path.join(ENH, '..')
OUT = os.path.join(ENH, 'build', 'game')
VASM = os.environ.get('VASM', 'vasmm68k_mot')
TRACK_SFX, TRACK_MUSIC = 126, 64


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
    print(f'game.bin {os.path.getsize(prog):,} bytes ($80-${end:X}); globals ${syms["GlobalsBlock"]:X}, '
          f'memory map from ${syms["MAP_LOW"]:X} (screens ${syms["SCREEN_0"]:X}, level file ${syms["LEVEL_FILE"]:X}); '
          f'effects package for ${syms["MUSIC_FILE"]:X}, music package for ${syms["MUSIC1M_FILE"]:X}')
    return prog, lst, {TRACK_SFX: sfx, TRACK_MUSIC: music}, syms


if __name__ == '__main__':
    build()
