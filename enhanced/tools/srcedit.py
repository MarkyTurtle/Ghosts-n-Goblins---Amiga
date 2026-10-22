"""Helpers for hand-editing the merged source (gng_main.s): its ifd BUILD_1MB / else / endc
blocks, and the check that both builds still assemble to the original programs.

  python3 srcedit.py check          assemble both builds, compare with the originals
  python3 srcedit.py symbols        name the absolute addresses still written as numbers
  python3 srcedit.py collapse       write blocks whose two sides now read the same once"""
import hashlib, os, re, subprocess, sys
from amiga import equates

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, '..', '..', 'original')  # the original game's folder (original/: its sources, tools, files)
SRC = os.path.join(ROOT, 'gng_main.s')
EQ = os.path.join(ROOT, 'gng_equates.i')
VASM = os.environ.get('VASM', 'vasmm68k_mot')
SHA = {False: '2628a93c164a5a8791272c146053b0afb3ddcf14', True: 'e44347679297d5d864ae7b0da689714970e261ad'}
ADDR = re.compile(r';\s([0-9A-F]{5}|     )/([0-9A-F]{5}|     )')


def assemble(src=SRC, build_1mb=False, out=None, listing=None):
    out = out or os.path.join(HERE, '_srcedit.bin')
    cmd = [VASM, '-Fbin', '-m68000', '-no-opt', '-quiet', '-I', ROOT, '-o', out]
    if build_1mb: cmd.append('-DBUILD_1MB=1')
    if listing: cmd += ['-L', listing]
    r = subprocess.run(cmd + [src], capture_output=True, text=True, cwd=ROOT)
    if r.returncode: sys.exit(r.stdout + r.stderr)
    return open(out, 'rb').read()


def check():
    ok = True
    for b in (False, True):
        h = hashlib.sha1(assemble(build_1mb=b)).hexdigest()
        print(f'  {"1MB " if b else "512K"}: {"OK" if h == SHA[b] else "MISMATCH " + h}')
        ok &= h == SHA[b]
    return ok


def blocks(lines):
    """[(start, else_or_None, end, kind)] of the top-level ifd/ifnd BUILD_1MB blocks (line indices)"""
    out, i = [], 0
    while i < len(lines):
        m = re.match(r'^\t(ifd|ifnd)\tBUILD_1MB', lines[i])
        if m:
            e, j = None, i + 1
            while not lines[j].startswith('\tendc'):
                if lines[j].startswith('\telse'): e = j
                j += 1
            out.append((i, e, j, m.group(1))); i = j
        i += 1
    return out


def code(l):
    c = l.split(';')[0]
    return ' '.join(c.split())


def sides(lines, b):
    i, e, j, kind = b
    first, second = lines[i + 1:e if e else j], lines[e + 1:j] if e else []
    return (first, second) if kind == 'ifd' else (second, first)       # (1MB, 512K)


def collapse(lines):
    """blocks whose 1MB and 512K sides assemble from the same text -> shared lines"""
    n = 0
    for b in reversed(blocks(lines)):
        one, five = sides(lines, b)
        c1, c5 = [code(l) for l in one if code(l)], [code(l) for l in five if code(l)]
        if c1 != c5 or not c5: continue
        it1 = iter([l for l in one if code(l)])
        merged = []
        for l in five:
            if not code(l): merged.append(l); continue
            o = next(it1)
            m5, m1 = ADDR.search(l), ADDR.search(o)
            if m5 and m1:
                l = l[:m5.start()] + f'; {m5.group(1)}/{m1.group(2)}' + l[m5.end():]
            merged.append(l)
        lines[b[0]:b[2] + 1] = merged; n += 1
    return n


def name_for(v, eq, exact_only=False, prefer=()):
    """an expression naming address v from the equates of one build (names starting with one
    of 'prefer' first)"""
    hits = [k for k, x in eq.items() if x == v and k.isupper() and not k.startswith(('G_', 'O_'))]
    pref = [k for k in hits if not k.startswith(('VEC_', 'DMAF', 'INTF'))]
    if pref: return sorted(pref, key=lambda k: (not k.startswith(prefer) if prefer else 0, len(k)))[0]
    if exact_only: return None
    near = [(v - x, k) for k, x in eq.items() if k.isupper() and 0 < v - x < 0x100 and x >= 0x400
            and re.match(r'^(SPRITE\w+_DATA|MFM_BUFFER)$', k)]
    if near:
        d, k = min(near); return f'{k}+${d:X}'
    m = [k for k, x in eq.items() if x == v + 4 and k == 'COPPER_INIT']
    if m: return 'COPPER_INIT-4'
    return None


def symbolize(lines):
    """name the absolute addresses written as numbers: '$xxxxx.l' operands, '#$xxxxx' moved into
    pointers (screens, save areas, level file, copper, DMA pointer), FENTRY load addresses"""
    eqs = {False: equates(EQ), True: equates(EQ, True)}
    n, misses = 0, []
    for b in blocks(lines):
        i, e, j, kind = b
        for k in range(i + 1, j):
            if k == e: continue
            in_first = e is None or k < e
            is1m = in_first == (kind == 'ifd')
            eq = eqs[is1m]
            c, cmt = lines[k].split(';', 1) if ';' in lines[k] else (lines[k], None)
            fentry = bool(re.match(r'^\s+FENTRY\s', c))
            def rep(m):
                v = int(m.group(2), 16)
                if v < 0x80 or (v < 0x400 and not re.search(r'g_Screen', c)): return m.group(0)
                nm = name_for(v, eq, prefer=('BOB_GFX', 'SCREEN') if fentry else ('SAVE_BUF', 'SCREEN'))
                if not nm: misses.append((k + 1, c.strip())); return m.group(0)
                return f'{m.group(1)}({nm}){m.group(3)}' if m.group(3) else f'{m.group(1)}{nm}'
            new = c
            if re.match(r'^\s+(lea\.l|clr\.l|move\.l|movea\.l)\s', c):
                new = re.sub(r'()\$([0-9a-fA-F]{4,6})(\.l)', rep, new)
                if re.search(r'#\$[0-9a-fA-F]+,(g_Screen\w+|g_SaveBuf\w|g_LevelFileAddr)\(a6\)|,COP[12]LCH\(|,\$20\(a0\)', c):
                    new = re.sub(r'(#)\$([0-9a-fA-F]{2,6})()', rep, new)
            elif re.match(r'^\s+FENTRY\s', c):
                new = re.sub(r'(FENTRY\s+)\$([0-9A-F]{5})()', rep, new)
            if new != c:                            # keep the comment column (48) where it fits
                new = new.rstrip()
                lines[k] = (new.ljust(47 if fentry else 48) if cmt is not None else new) + \
                           (' ' if len(new) >= 48 and cmt is not None else '') + (';' + cmt if cmt is not None else '')
                n += 1
    return n, misses


if __name__ == '__main__':
    what = sys.argv[1] if len(sys.argv) > 1 else 'check'
    lines = open(SRC).read().split('\n')
    if what == 'symbols':
        n, misses = symbolize(lines)
        print(f'{n} lines given names'); [print('  not named:', m) for m in misses]
    if what in ('symbols', 'collapse'):
        print(f'{collapse(lines)} blocks collapsed')
        open(SRC, 'w').write('\n'.join(lines))
    sys.exit(0 if check() else 1)
