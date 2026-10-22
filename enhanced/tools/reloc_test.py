"""Relocation test of gng_main.s (512K build): assemble it with RELOC_PAD bytes inserted right
after the entry point, so that every address after that point - the code, the tables, the
globals and the whole memory map after them (MAP_LOW) - moves, and check that nothing still
points at the old places:

 1. static: every 32-bit value in the normal program that is an address past the insertion
    point must have moved by RELOC_PAD in the padded one (values that did not move are listed;
    some are numbers that only look like addresses);
 2. running: the padded program (with the effects package assembled for its new MUSIC_FILE)
    runs side by side with the original in the emulator, with the same input; the game state
    and the picture must stay identical.

  python3 reloc_test.py [frames] [--pad N] [--level N] [--teleport N]"""
import os, re, struct, subprocess, sys
import numpy as np
import srcedit
from game import GameRun, script_start
from check_game import play_script
from compare_runs import state

HERE = os.path.dirname(os.path.abspath(__file__))
TMP = os.path.join(HERE, '..', 'build', 'reloc')
ROOT = srcedit.ROOT
LOAD = 0x80


def symbols(lst):
    text = open(lst).read()
    part = text[text.index('Symbols by name:'):text.index('Symbols by value:')]
    return {m.group(1): int(m.group(3), 16) for m in re.finditer(r'^(\S+)\s+([AE]):([0-9A-F]+)$', part, re.M)}


def build(pad):
    os.makedirs(TMP, exist_ok=True)
    src = os.path.join(TMP, f'main_pad{pad}_{os.getpid()}.s')
    open(src, 'w').write(f'RELOC_PAD\tequ\t{pad}\n\tinclude\t"gng_main.s"\n' if pad else '\tinclude\t"gng_main.s"\n')
    out, lst = src[:-2] + '.bin', src[:-2] + '.lst'
    data = srcedit.assemble(src, out=out, listing=lst)
    return data, symbols(lst), out, lst


def sound(org):
    out = os.path.join(TMP, f'sfx_{org:X}_{os.getpid()}.bin')
    r = subprocess.run([srcedit.VASM, '-Fbin', '-m68000', '-no-opt', '-quiet', f'-DSND_ORG={org}', '-o', out,
                        os.path.join(ROOT, 'sound', 'gng_sfx_512k.s')], capture_output=True, text=True)
    if r.returncode: sys.exit(r.stdout + r.stderr)
    return out


DATA = re.compile(r'^\s*(\w+:)?\s*(dc\.[bw]|dcb|ds\.|FRAME|AFRAME|ALOOP|SPAWN\w*|PLACE|AF|AL)\b', re.I)


def code_ranges(lst):
    """(start, end) of every listing line that is an instruction or a long-word / file-table /
    copper-pointer entry (byte and word tables are left out: their numbers are not addresses)"""
    out = []
    for m in re.finditer(r'^00:([0-9A-F]{8}) ([0-9A-F]+)\s*\t\s*\d+:(.*)$', open(lst).read(), re.M):
        if not DATA.match(m.group(3)) or re.search(r'\b(FENTRY|COPPTR)\b', m.group(3)):
            a = int(m.group(1), 16); out.append((a, a + len(m.group(2)) // 2))
    return out


def static_scan(a, b, insert, pad, syms, ranges):
    """the long operands (absolute '.l' addresses, '#' long immediates, long data entries) of
    the normal program that are addresses at or past 'insert' and did not move by 'pad' in the
    padded one"""
    import capstone
    md = capstone.Cs(capstone.CS_ARCH_M68K, capstone.CS_MODE_M68K_000)
    near = sorted((v, k) for k, v in syms.items() if v >= 0x80)
    def where(addr):
        best = max(((v, k) for v, k in near if v <= addr), default=(0, '?'))
        return f'{best[1]}+${addr - best[0]:X}'
    def longs(data, addr, n):
        i = next(md.disasm(data[addr - LOAD:addr - LOAD + n], addr), None)
        if not i or i.size != n:                  # a long-word data entry
            return [struct.unpack_from('>I', data, addr - LOAD + k)[0] for k in range(0, n - 3, 4)]
        vals = [int(x, 16) for x in re.findall(r'\$([0-9a-f]+)\.l', i.op_str)]
        if i.mnemonic.endswith('.l') or i.mnemonic in ('lea', 'pea'):
            vals += [int(x, 16) for x in re.findall(r'#\$([0-9a-f]+)', i.op_str)]
        return vals
    bad = []
    for lo, hi in ranges:
        if lo < insert: continue
        for v, w in zip(longs(a, lo, hi - lo), longs(b, lo + pad, hi - lo)):
            if insert <= v < 0x80000 and w != v + pad: bad.append((lo, v, w, where(lo)))
    return bad


def run(frames, pad, moved_bin, moved_lst, sfx, level=None, teleport=0):
    import compare_runs
    orig = GameRun(build='512k')
    moved = GameRun(moved_bin, {126: sfx}, build='512k', listing=moved_lst)
    return compare_runs.main(frames, 1, None, level, teleport, '512k', pair=(orig, moved), raw=False) == 0


def main(frames=2000, pad=0x246, level=None, teleport=0):
    a, sa, _, alst = build(0)
    b, sb, bpath, blst = build(pad)
    insert = sa['ProgramEntry'] + 4
    print(f'padded by ${pad:X} after ${insert:X}: GLOBALS ${sa["GlobalsBlock"]:X} -> ${sb["GlobalsBlock"]:X}, '
          f'MUSIC_FILE ${sa["MUSIC_FILE"]:X} -> ${sb["MUSIC_FILE"]:X}, LEVEL_FILE ${sa["LEVEL_FILE"]:X} -> ${sb["LEVEL_FILE"]:X}')
    bad = static_scan(a, b, insert, pad, sa, code_ranges(alst))
    print(f'static: {len(bad)} values that look like addresses past ${insert:X} did not move')
    for addr, v, w, where in bad[:80]:
        print(f'  ${addr:05X} ({where}): ${v:05X} -> ${w:05X}')
    ok = frames == 0 or run(frames, pad, bpath, blst, sound(sb['MUSIC_FILE']), level, teleport)
    return 0 if ok else 1


if __name__ == '__main__':
    args = [x for x in sys.argv[1:] if not x.startswith('--')]
    pad = int(sys.argv[sys.argv.index('--pad') + 1], 0) if '--pad' in sys.argv else 0x246
    if '--pad' in sys.argv: args.remove(sys.argv[sys.argv.index('--pad') + 1])
    lv = int(sys.argv[sys.argv.index('--level') + 1]) if '--level' in sys.argv else None
    tp = int(sys.argv[sys.argv.index('--teleport') + 1]) if '--teleport' in sys.argv else 0
    for o in ('--level', '--teleport'):
        if o in sys.argv: args.remove(sys.argv[sys.argv.index(o) + 1])
    sys.exit(main(int(args[0]) if args else 2000, pad, lv, tp))
