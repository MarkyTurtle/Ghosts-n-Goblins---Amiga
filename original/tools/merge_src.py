"""Merge the two generated sources - the 512K build (tools/gng_main.s, from gen.py) and the 1MB
build (tools/build1mb/gng_main_1mb.s, from gen1m.py) - into the one source in the repository
root, gng_main.s, which assembles to either program:

  vasmm68k_mot -Fbin -m68000 -no-opt -o main.bin     gng_main.s                 (512K)
  vasmm68k_mot -Fbin -m68000 -no-opt -o main_1mb.bin -DBUILD_1MB=1 gng_main.s   (1MB)

The equates are merged the same way into gng_equates.i.

How: both sources are cut into lines and aligned (difflib) on what assembles - code with the
comments left out, and with the 1MB build's address labels (l_XXXXX, named after 1MB file
offsets) renamed to their 512K counterparts through the instruction map of mkmap.py
(build1mb/map.json). Lines the two share are written once; where they differ, the 1MB lines go
in an 'ifd BUILD_1MB' block and the 512K lines in its 'else'. The address column of a shared
line gives both addresses (512K/1MB); a line only in one build gives its own.

  python3 merge_src.py [--check]     (--check: assemble both and compare with the originals)"""
import difflib, hashlib, json, os, re, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, '..')
SRC512 = os.path.join(HERE, 'gng_main.s')
SRC1M = os.path.join(HERE, 'build1mb', 'gng_main_1mb.s')
EQ512 = os.path.join(HERE, 'gng_equates.i')
EQ1M = os.path.join(HERE, 'build1mb', 'gng_equates_1mb.i')
SHA = {'512k': '2628a93c164a5a8791272c146053b0afb3ddcf14', '1mb': 'e44347679297d5d864ae7b0da689714970e261ad'}
LABEL = re.compile(r'\bl_([0-9A-F]{5})\b')
ADDR = re.compile(r';\s([0-9A-F]{5})\b(?:\s|$)')
NOTE = re.compile(r'\s*<<[^>]*>>')


def split_comment(line):
    """(code, comment) - the comment starts at the first ';' outside quotes"""
    q = None
    for i, c in enumerate(line):
        if q:
            if c == q: q = None
        elif c in '\'"': q = c
        elif c == ';': return line[:i], line[i:]
    return line, ''


def label_map():
    """1MB l_XXXXX name -> 512K name (or a name of its own for code only the 1MB build has)"""
    m = json.load(open(os.path.join(HERE, 'build1mb', 'map.json')))['amap']
    inv = {v: int(k, 16) for k, v in m.items()}
    have512 = set(LABEL.findall(open(SRC512).read()))
    out = {}
    for h in set(LABEL.findall(open(SRC1M).read())):
        a = inv.get(int(h, 16))
        n512 = f'{a:05X}' if a is not None else None
        out['l_' + h] = f'l_{n512}' if n512 in have512 else f'l1m_{h}'
    return out


class Line:
    def __init__(self, text, ren=None):
        if ren: text = LABEL.sub(lambda m: ren['l_' + m.group(1)], text)
        self.text = text
        code, cmt = split_comment(text)
        self.code, self.cmt = code.rstrip(), cmt
        m = ADDR.match(cmt)
        self.addr = m.group(1) if m else None
        # the alignment key: what assembles (comment lines and blank lines: the text itself)
        self.key = ' '.join(code.split()) if code.strip() else text.strip()
        self.asm = bool(code.strip())


def with_addr(line, col):
    """the line with its address column replaced by col, and the 1MB notes dropped"""
    if line.addr is None:
        return NOTE.sub('', line.text).replace('[1MB] ', '').rstrip()
    rest = NOTE.sub('', line.cmt[2 + 5:]).replace('[1MB] ', '').replace('[1MB]', '').rstrip()
    return f'{line.code.ljust(48)}; {col}{rest}'


def merge(a_lines, b_lines, header=None):
    """a: 512K Lines, b: 1MB Lines -> merged text lines"""
    sm = difflib.SequenceMatcher(None, [l.key for l in a_lines], [l.key for l in b_lines], autojunk=False)
    out, stats = [], dict(shared=0, only512=0, only1mb=0, blocks=0)
    ops = sm.get_opcodes()
    for tag, i1, i2, j1, j2 in ops:
        A, B = a_lines[i1:i2], b_lines[j1:j2]
        if tag == 'equal':
            for x, y in zip(A, B):
                out.append(with_addr(x, f'{x.addr}/{y.addr}') if x.addr and y.addr else x.text)
            stats['shared'] += sum(x.asm for x in A)
            continue
        if not any(l.asm for l in A + B):          # comments only: the 512K ones, then what the
            out += [l.text for l in A]              # 1MB source says differently, marked [1MB]
            seen = {x.text for x in A}
            out += ['; [1MB] ' + l.text[1:].strip().replace('[1MB] ', '') for l in B
                    if l.text.startswith(';') and l.text[1:].strip(' -=') and l.text not in seen]
            continue
        stats['blocks'] += 1
        stats['only512'] += sum(l.asm for l in A); stats['only1mb'] += sum(l.asm for l in B)
        out.append('\tifd\tBUILD_1MB' if B else '\tifnd\tBUILD_1MB')
        out += [with_addr(l, f'     /{l.addr}') for l in B]
        if A and B: out.append('\telse')
        out += [with_addr(l, f'{l.addr}/     ') for l in A]
        out.append('\tendc')
    return out, stats


def merge_main():
    ren = label_map()
    a = [Line(t) for t in open(SRC512).read().split('\n')]
    b = [Line(t, ren) for t in open(SRC1M).read().split('\n')]
    # the file header (up to the include) is written new; the rest is merged
    ia = next(i for i, l in enumerate(a) if 'include' in l.code)
    ib = next(i for i, l in enumerate(b) if 'include' in l.code)
    body, stats = merge(a[ia + 1:], b[ib + 1:])
    head = [l.text for l in a[:ia]]
    head[0] = "; Ghosts'n Goblins (Elite, 1990, v3) - main program, both builds: 512K and expanded memory (1MB)"
    k = next(i for i, t in enumerate(head) if t.startswith('; ===') or t.startswith(';---'))
    head[k:k] = MERGED_NOTE.split('\n')
    return head + ['\tinclude\t"gng_equates.i"'] + body, stats


MERGED_NOTE = """;
; ONE SOURCE, TWO PROGRAMS. The disk holds two builds of the main program: the 512K one
; (tracks 110-125, loaded to $80, absolute addresses) and the expanded-memory one (tracks
; 17-32: 1MB of chip RAM, or memory above 512K; position independent through g_BaseAddr,
; assembled at org 0 so its labels are file offsets). This file assembles to either:
;   vasmm68k_mot -Fbin -m68000 -no-opt -o main.bin gng_main.s                     (512K)
;   vasmm68k_mot -Fbin -m68000 -no-opt -DBUILD_1MB=1 -o main_1mb.bin gng_main.s   (1MB)
; Where the builds differ the 1MB code is in an 'ifd BUILD_1MB' block and the 512K code in its
; 'else'. The address column gives both addresses (512K/1MB); a line in one build only gives
; its own. Labels l_XXXXX are named after the 512K address; l1m_XXXXX after the 1MB file
; offset of code only that build has. gng_equates.i holds the equates of both (the memory map
; differs).
; Generated: tools/gen.py and tools/build1mb/gen1m.py write the two builds' sources,
; tools/merge_src.py merges them into this file (see README, Extending the annotations)."""


def merge_equates():
    """the two equates files: names with the same definition once, the others per build.
    The globals (offsets from a6) are the same in both builds except that the 1MB one has
    g_BaseAddr at $2 and everything after it 4 bytes further on: they are written once as
    G_SHIFT+offset, with G_SHIFT 0 or 4."""
    def shift(text, by, after):
        out = []
        for t in text.split('\n'):
            m = re.match(r'^(g_\w+)(\s+equ\s+)\$([0-9A-F]+)(.*)$', t)
            if m and int(m.group(3), 16) >= 2 + by and m.group(1) != 'g_BaseAddr':
                t = f'{m.group(1)}{m.group(2)}G_SHIFT+${int(m.group(3), 16) - by:03X}{m.group(4)}'
            out.append(t)
            if t.startswith(after):
                out.append(f'G_SHIFT             \tequ\t{by}\t; added to the offsets of the globals '
                           + ('after g_BaseAddr' if by else '(4 in the 1MB build: g_BaseAddr comes first)'))
        return out
    a = [Line(t) for t in shift(open(EQ512).read(), 0, 'g_SavedSR')]
    b = [Line(t) for t in shift(open(EQ1M).read(), 4, 'g_BaseAddr')]
    body, stats = merge(a[1:], b[1:])
    return [a[0].text.rstrip() + ' (both builds; BUILD_1MB selects the 1MB memory map)'] + body, stats


def assemble(src, defs=()):
    vasm = os.environ.get('VASM', 'vasmm68k_mot')
    out = os.path.join(HERE, '_merge_check.bin')
    r = subprocess.run([vasm, '-Fbin', '-m68000', '-no-opt', '-quiet', *[f'-D{d}=1' for d in defs], '-o', out, src],
                       cwd=ROOT, capture_output=True, text=True)
    if r.returncode: sys.exit(r.stdout + r.stderr)
    h = hashlib.sha1(open(out, 'rb').read()).hexdigest(); os.remove(out)
    return h


def main():
    main_lines, s = merge_main()
    open(os.path.join(ROOT, 'gng_main.s'), 'w').write('\n'.join(main_lines).rstrip('\n') + '\n')
    print(f"gng_main.s: {s['shared']} lines of code shared, {s['only512']} 512K only, "
          f"{s['only1mb']} 1MB only, in {s['blocks']} conditional blocks")
    eq_lines, s = merge_equates()
    open(os.path.join(ROOT, 'gng_equates.i'), 'w').write('\n'.join(eq_lines).rstrip('\n') + '\n')
    print(f"gng_equates.i: {s['shared']} shared, {s['only512']} 512K only, {s['only1mb']} 1MB only")
    if '--check' in sys.argv:
        bad = 0
        for name, defs in (('512k', ()), ('1mb', ('BUILD_1MB',))):
            h = assemble('gng_main.s', defs)
            ok = h == SHA[name]; bad += not ok
            print(f'  {name}: {"OK" if ok else "MISMATCH " + h}')
        sys.exit(1 if bad else 0)


if __name__ == '__main__':
    main()
