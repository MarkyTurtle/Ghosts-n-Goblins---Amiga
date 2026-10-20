"""Check sound/gng_music_512k.s (make_music_512k.py) with the real driver code (sndemu.py): every
tune writes the same Paula registers, frame by frame, as with the 1MB package, and every effect
as with the 512K package (sample addresses compared as sample + offset).
   python3 sound/tools/check_music_512k.py [frames]"""
import os, re, subprocess, sys, tempfile
HERE = os.path.dirname(os.path.abspath(__file__))
SND = os.path.join(HERE, '..')
sys.path.insert(0, HERE)
import sndemu

FRAMES = int(sys.argv[1]) if len(sys.argv) > 1 else 1500
TMP = tempfile.mkdtemp()


def build(src):
    out, lst = os.path.join(TMP, src + '.bin'), os.path.join(TMP, src + '.lst')
    subprocess.run(['vasmm68k_mot', '-Fbin', '-m68000', '-no-opt', '-quiet', '-o', out, '-L', lst, src],
                   cwd=SND, check=True)
    text = open(lst).read()
    part = text[text.index('Symbols by name:'):text.index('Symbols by value:')]
    syms = {m.group(1): int(m.group(2), 16) for m in re.finditer(r'^(\S+)\s+A:([0-9A-F]+)$', part, re.M)}
    return out, syms


def run(src, cmd, num, rename):
    path, syms = build(src)
    base = syms['HunkHeader']
    smp = sorted((v, rename(k)) for k, v in syms.items() if re.fullmatch(r'(Eff)?Smp\d\d(_\d+)?|NullSample', k))
    def name(a):
        best = max((v, k) for v, k in smp if v <= a) if any(v <= a for v, k in smp) else (0, '?')
        return f'{best[1]}+{a - best[0]}'
    d = sndemu.Driver(path, base)
    d.call(cmd, num)
    frames = []
    for f in range(FRAMES):
        d.writes = []
        d.call(0)
        w = []
        for reg, size, val in d.writes:
            if size == 4 and reg in (0xA0, 0xB0, 0xC0, 0xD0): val = name(val)
            w.append((reg, size, val))
        frames.append(w)
    return frames


def same(a, b):
    for f, (x, y) in enumerate(zip(a, b)):
        if x != y: return f
    return None


bad = 0
for t in range(15):
    f = same(run('gng_music_1mb.s', 1, t, lambda k: k), run('gng_music_512k.s', 1, t, lambda k: k))
    print(f'tune {t:2d}: ' + ('the same' if f is None else f'differs at frame {f}')); bad += f is not None
for e in range(30):
    f = same(run('gng_sfx_512k.s', 2, e, lambda k: 'Eff' + k if k.startswith('Smp') else k),
             run('gng_music_512k.s', 2, e, lambda k: k))
    print(f'effect {e:2d}: ' + ('the same' if f is None else f'differs at frame {f}')); bad += f is not None
print(f'{FRAMES} frames each:', 'all the same' if not bad else f'{bad} differ')
sys.exit(1 if bad else 0)
