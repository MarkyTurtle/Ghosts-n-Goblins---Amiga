"""Check enhanced/sound/gng_music_512k.s (make_music_512k.py) with the real driver code (sndemu.py):
 * the package at full quality (--rate 1, made into a temporary file): every tune writes the
   same Paula registers, frame by frame, as with the 1MB package;
 * the game's package (the tunes' samples 5-9 at 3/4 of their rate): every tune writes the same
   registers as at full quality, except that on a resampled sample the period is the full
   quality's / 3/4 (to within one period step) and its length is the new sample's;
 * every effect the same registers as with the 512K package
(sample addresses compared as sample + offset).
   python3 enhanced/sound/tools/check_music_512k.py [frames]"""
import os, re, subprocess, sys, tempfile
VASM = os.environ.get('VASM', 'vasmm68k_mot')          # the assembler (VASM: its full path, if not on the PATH)
HERE = os.path.dirname(os.path.abspath(__file__))
SND = os.path.join(HERE, '..')          # enhanced/sound: the 512K package and the packages it is made from
# (sndemu, the driver emulated, is the original game's tool)
sys.path.insert(0, os.path.join(HERE, '..', '..', '..', 'original', 'sound', 'tools'))
import sndemu

FRAMES = int(sys.argv[1]) if len(sys.argv) > 1 else 1500
TMP = tempfile.mkdtemp()


def build(src):
    out, lst = os.path.join(TMP, src + '.bin'), os.path.join(TMP, src + '.lst')
    subprocess.run([VASM, '-Fbin', '-m68000', '-no-opt', '-quiet', '-I', SND,
                    '-o', out, '-L', lst, src], cwd=SND, check=True)
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


FULL = '_full_quality.s'                  # (in sound/, for its incbin paths; removed at the end)
subprocess.run([sys.executable, os.path.join(HERE, 'make_music_512k.py'), '--rate', '1', '--out',
                os.path.join(SND, FULL)], check=True, capture_output=True)
RATE = 0.75
RESAMPLED = re.compile(r'Smp0[5-9]\+\d+')


def resampled_like(a, b):
    """the game's package's frame b against the full quality's frame a: the first frame that
    differs other than as resampling allows, or None"""
    if len(a) != len(b): return False
    loc = {}
    for (ra, sa, va), (rb, sb, vb) in zip(a, b):
        if (ra, sa) != (rb, sb): return False
        if sa == 4 and ra in (0xA0, 0xB0, 0xC0, 0xD0):
            if va != vb: return False
            loc[ra >> 4] = va
        elif (ra & 0xF) == 6 and va >= 64 and RESAMPLED.fullmatch(str(loc.get(ra >> 4, ''))):
            if abs(vb - va / RATE) > 1 + 1 / RATE: return False            # the period, rounded twice
        elif (ra & 0xF) == 4 and RESAMPLED.fullmatch(str(loc.get(ra >> 4, ''))):
            pass                                                            # the new sample's length
        elif va != vb: return False
    return True


bad = 0
for t in range(15):
    full = run(FULL, 1, t, lambda k: k)
    f = same(run('gng_music_1mb.s', 1, t, lambda k: k), full)
    g = next((k for k, (x, y) in enumerate(zip(full, run('gng_music_512k.s', 1, t, lambda k: k)))
              if not resampled_like(x, y)), None)
    print(f'tune {t:2d}: ' + ('full quality as the 1MB package' if f is None else f'full quality differs at frame {f}')
          + ', 3/4 ' + ('as full quality, resampled' if g is None else f'differs at frame {g}'))
    bad += f is not None or g is not None
os.remove(os.path.join(SND, FULL))
for e in range(30):
    f = same(run('gng_sfx_512k.s', 2, e, lambda k: 'Eff' + k if k.startswith('Smp') else k),
             run('gng_music_512k.s', 2, e, lambda k: k))
    print(f'effect {e:2d}: ' + ('the same' if f is None else f'differs at frame {f}')); bad += f is not None
print(f'{FRAMES} frames each:', 'all the same' if not bad else f'{bad} differ')
sys.exit(1 if bad else 0)
