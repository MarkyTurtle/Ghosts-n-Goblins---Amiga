"""Generate a byte-identical, annotated vasm source for a GnG sound-driver file.

usage: python3 gen_snd.py <file.hunk> <load_base_hex> <trace.json> <name> <outdir>
Writes <outdir>/<name>.s and <outdir>/samples/<name>_smpNN.raw
"""
import sys, os, re, json, struct
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sndparse import SndFile, NOTE
import snd_anno as A

fn, BASE, tj, NAME, OUT = sys.argv[1], int(sys.argv[2], 16), sys.argv[3], sys.argv[4], sys.argv[5]
f = SndFile(fn); D = f.d
t = json.load(open(tj))
INS = {int(k, 16) - BASE: v for k, v in t['insn'].items()}
CODELAB = {int(k, 16) - BASE for k in t['labels']}
os.makedirs(os.path.join(OUT, 'samples'), exist_ok=True)

# ------------------------------------------------------------------ labels
lab = {}            # file offset -> label
def L(o, name):
    lab.setdefault(o, name); return lab[o]
for o, nm in A.CODE_NAMES.items(): lab[o] = nm
for o in sorted(CODELAB):
    if o not in lab: lab[o] = f'.l{o:04X}' if 0x20 <= o < 0x612 else f'l{o:04X}'
L(f.songtab, 'MusicTable')
sfx_label = 'SfxTable'
ALIAS = {}          # extra labels at same address
if f.sfxtab == f.songtab: ALIAS.setdefault(f.songtab, []).append('SfxTable')
else: L(f.sfxtab, 'SfxTable')
L(f.instab, 'InstrumentTable')
L(f.calltab, 'PatternTable')
if f.pitch == f.calltab: ALIAS.setdefault(f.calltab, []).append('PitchTable')
else: L(f.pitch, 'PitchTable')
L(f.vars, 'DriverVars'); L(f.smpbase, 'SampleBase')
ALIAS.setdefault(f.smpbase, []).append('NullSample')
# local labels in the code use the .lXXXX form; make them global-safe
for o in list(lab):
    if lab[o].startswith('.l'): lab[o] = 'c' + lab[o][2:]

# streams
starts = {}
for kind, tab in (('Mus', f.music()), ('Sfx', f.sfx())):
    for i, ch in enumerate(tab):
        for c, p in enumerate(ch):
            if p: starts.setdefault(p, f'{kind}{i:02d}_Ch{c}')
cmds = {}; todo = list(starts); seen = set(); pats = {}; jumps = set()
while todo:
    a = todo.pop()
    if a in seen: continue
    seen.add(a)
    for x, n, txt in f.decode_stream(a, ''):
        cmds[x] = (n, txt)
        if txt.startswith('CALL'):
            p = int(txt.split()[2]); pp = f.pattern_ptr(p); pats[p] = pp; todo.append(pp)
        if txt.startswith('JUMP'):
            j = int(txt.split()[1], 16); jumps.add(j); todo.append(j)
for p, o in starts.items(): L(p, o)
for p, o in sorted(pats.items()): L(o, f'Pat{p:02d}')
for j in sorted(jumps): L(j, f'Loop_{j:04X}')
npat = (max(pats) + 1) if pats else 0
# pattern table may hold entries beyond the highest used one (unused patterns)
pt_entries = []
for i in range(npat):
    a = f.calltab + 2 * i; pt_entries.append(a + struct.unpack('>h', D[a:a + 2])[0])

# instruments, envelopes, samples
ninstr = f.ninstr(); instr = [f.instrument(k) for k in range(ninstr)]
for k, I in enumerate(instr): L(I['rec'], f'Ins{k:02d}')
envs = {}
for k, I in enumerate(instr):
    for key, term in (('venv', 0), ('penv', 0x80)):
        a = I[key]
        if a and a not in envs:
            b = a
            while D[b] != term: b += 1
            envs[a] = (b + 1 - a, key)
            L(a, ('VolEnv' if key == 'venv' else 'PitchEnv') + f'_{a:04X}')
# sample chain
samples = []; a = f.smpbase + 64; n = 0
while a + 6 <= len(D):
    ln, rate = struct.unpack('>IH', D[a:a + 6]); samples.append((n, a, ln, rate)); a += 6 + ln; n += 1
for n, h, ln, rate in samples:
    L(h, f'SmpHdr{n:02d}'); L(h + 6, f'Smp{n:02d}')
    open(os.path.join(OUT, 'samples', f'{NAME}_smp{n:02d}.raw'), 'wb').write(D[h + 6:h + 6 + ln])
def smp_label(off):
    a = f.smpbase + off
    for n, h, ln, rate in samples:
        if h + 6 <= a < h + 6 + ln:
            if a == h + 6: return f'Smp{n:02d}'
            return L(a, f'Smp{n:02d}_{a - h - 6:X}')
    return L(a, f'SmpX_{a:X}')
ins_smp = []
for k, I in enumerate(instr):
    ins_smp.append((smp_label(I['attack']) if I['attack'] else None, smp_label(I['loop']) if I['loop'] else None))

# ------------------------------------------------------------------ code conversion
from hw import CUSTOM
HEX = re.compile(r'\$([0-9a-f]+)')
def lname(o):
    if o in lab: return lab[o]
    return None
def addrsym(a):
    o = a - BASE
    if o in lab: return lab[o]
    return f'${a:X}'
VFIELD = A.VOICE_FIELDS; VARF = A.VAR_FIELDS; AUDF = A.AUD_FIELDS
def conv(o, m, op):
    base = m.split('.')[0]
    isbr = base in ('bra', 'bsr') or base.startswith('db') or (base.startswith('b') and base not in ('btst', 'bchg', 'bclr', 'bset'))
    if isbr:
        tg = int(HEX.findall(op)[-1], 16); op = re.sub(r'\$[0-9a-f]+$', addrsym(tg), op)
    op = re.sub(r'\$([0-9a-f]+)\(pc', lambda mm: addrsym(int(mm.group(1), 16)) + '(pc', op)
    def absr(mm):
        v = int(mm.group(1), 16)
        if v == 0xdff000: return 'CUSTOM'
        if 0xdff000 < v < 0xdff200 and v - 0xdff000 in CUSTOM: return 'CUSTOM+' + CUSTOM[v - 0xdff000]
        if v == 0xbfe001: return 'CIAA_PRA'
        return mm.group(0)
    op = re.sub(r'(?<![#\w-])\$([0-9a-f]+)\.l', absr, op)
    rng = A.reg_context(o)
    def regoff(mm):
        neg, off, r = mm.group(1), int(mm.group(2), 16), mm.group(3)
        if neg: return mm.group(0)
        role = rng.get(r)
        if role == 'voice' and off in VFIELD: return f'{VFIELD[off]}({r})'
        if role == 'vars' and off in VARF: return f'{VARF[off]}({r})'
        if role == 'aud' and off in AUDF: return f'{AUDF[off]}({r})'
        if role == 'custom' and off in CUSTOM: return f'{CUSTOM[off]}({r})'
        return mm.group(0)
    op = re.sub(r'(?<![\w$])(-?)\$([0-9a-f]+)\((a[0-7])\)', regoff, op)
    if base == 'moveq':
        mm = re.match(r'#\$([0-9a-f]+), (d\d)', op); v = int(mm.group(1), 16)
        if v > 127: op = f'#{v - 256}, {mm.group(2)}'
    if base in ('btst', 'bchg', 'bclr', 'bset'): m = base
    return m, op.replace(', ', ',')

# ------------------------------------------------------------------ emit
out = []
def hdr(o):
    if o in A.HEADERS:
        out.append(''); out.append(';' + '-' * 76)
        for l in A.HEADERS[o].strip('\n').split('\n'): out.append('; ' + l if l else ';')
        out.append(';' + '-' * 76)
def label(o):
    hdr(o)
    for al in ALIAS.get(o, []): out.append(f'{al}:')
    if o in lab: out.append(f'{lab[o]}:')
def line(text, o, cmt=''):
    s = text.expandtabs(8).ljust(44) + f'; {o:05X}'
    if cmt: s += '  ' + cmt
    out.append(s)

out.append(A.PRELUDE.format(name=NAME, base=BASE, fn=os.path.basename(fn)))
o = 0
# hunk header
label(0) if 0 in lab else None
out.append('HunkHeader:')
for i in range(0, 0x20, 4): line(f'\tdc.l\t${struct.unpack(">I", D[i:i + 4])[0]:08X}', i, A.HUNK_CMT.get(i, ''))
o = 0x20
# code
while o < 0x612:
    label(o)
    if o in INS:
        sz, m, op, hx = INS[o]
        m2, op2 = conv(o, m, op)
        line(f'\t{m2}\t{op2}', o, A.COMMENTS.get(o, ''))
        o += sz
    else:
        line(f'\tdc.w\t${D[o:o+2].hex().upper()}', o); o += 2

# data from $612 onwards: walk in address order
items = {}   # offset -> (size, list of (text, comment))
def put(o, size, lines): items[o] = (size, lines)
def songtab(base, n, kind):
    for i in range(n):
        for c in range(4):
            a = base + i * 16 + c * 4; v = struct.unpack('>i', D[a:a + 4])[0]
            txt = f'\tdc.l\t{lab[a + v]}-*' if v else '\tdc.l\t0'
            cm = (f'{kind} {i:2d}  ' + A.song_name(kind, i)) if c == 0 else ''
            put(a, 4, [(txt, cm)])
songtab(f.songtab, f.nmusic, 'tune'); songtab(f.sfxtab, f.nsfx, 'sfx')
for k in range(ninstr):
    a = f.instab + 2 * k; put(a, 2, [(f'\tdc.w\t{lab[instr[k]["rec"]]}-*', f'instrument {k}')])
for k, I in enumerate(instr):
    r = I['rec']; s0, s1 = ins_smp[k]
    lines = [
        (f'\tdc.l\t{s0}-SampleBase' if s0 else '\tdc.l\t0', 'attack sample (offset from SampleBase)'),
        (f'\tdc.l\t{s1}-SampleBase' if s1 else '\tdc.l\t0', 'loop sample (offset from SampleBase)'),
        (f'\tdc.l\t{lab[I["venv"]]}-*' if I['venv'] else '\tdc.l\t0', 'volume envelope (self-relative)'),
        (f'\tdc.l\t{lab[I["penv"]]}-*' if I['penv'] else '\tdc.l\t0', 'pitch envelope (self-relative)'),
        (f'\tdc.w\t${I["attack_len"]:04X},${I["loop_len"]:04X}', f'attack / loop length (words) = {2*I["attack_len"]} / {2*I["loop_len"]} bytes'),
        (f'\tdc.w\t${I["attack_mul"]:04X},${I["loop_mul"]:04X}', 'period multipliers (PitchTable * mul >> 16)'),
        (f'\tdc.b\t{I["venv_speed"]},{I["penv_speed"]}', 'volume / pitch envelope speed (ticks per step)'),
        (f'\tdc.w\t{I["volume"]}', 'instrument volume (x channel volume >> 8; /4 -> AUDxVOL)'),
    ]
    sizes = [4, 4, 4, 4, 4, 4, 2, 2]
    put(r, 28, [(t, c, z) for (t, c), z in zip(lines, sizes)])
for a, (n, key) in envs.items():
    bs = D[a:a + n]
    if key == 'venv': put(a, n, [('\tdc.b\t' + ','.join(str(b) for b in bs), f'volume steps (vol = (n+1)*chanvol*insvol>>16), 0 = end')])
    else: put(a, n, [('\tdc.b\t' + ','.join(str(b - 256 if b > 127 else b) for b in bs), 'pitch offsets in 1/4 semitones, -128 = end')])
for i, pp in enumerate(pt_entries):
    a = f.calltab + 2 * i; put(a, 2, [(f'\tdc.w\t{lab[pp]}-*' if pp in lab else f'\tdc.w\t${struct.unpack(">H",D[a:a+2])[0]:04X}', f'pattern {i}' + ('' if i in pats else ' (unused)'))])
def note_name(n): return f'{A.NOTE_SYM[n % 12]}{n // 12}'
for x, (n, txt) in cmds.items():
    b = D[x]; c = b & 0x7f
    if c < 0x60:
        put(x, 4, [(f'\tNOTE\t{note_name(b)},{D[x+1]},{D[x+2]}' if D[x+3] == 0 and b < 0x80 else f'\tdc.b\t${b:02X},{D[x+1]},{D[x+2]},{D[x+3]}', f'n=${b:02X} ins {D[x+1]} dur {D[x+2]}')])
    elif c == 0x60: put(x, 4, [(f'\tREST\t{(D[x+1]<<8)|D[x+2]}', '') if D[x+3] == 0 else (f'\tdc.b\t$60,{D[x+1]},{D[x+2]},{D[x+3]}', 'rest')])
    elif c == 0x63: put(x, 2, [(f'\tVOLUME\t{D[x+1]}', '')])
    elif c == 0x64: put(x, 3, [(f'\tCALL\t{D[x+1]},{struct.unpack("b",D[x+2:x+3])[0]}', 'pattern, transpose')])
    elif c == 0x65: put(x, 4, [(f'\tCALLN\t{D[x+1]},{struct.unpack("b",D[x+2:x+3])[0]},{D[x+3]}', f'pattern, transpose, plays {D[x+3]+1}x')])
    elif c == 0x66: put(x, 1, [('\tRETURN', '')])
    elif c == 0x67: put(x, 1, [('\tENDTRACK', '')])
    elif c == 0x68:
        j = x + struct.unpack('>h', D[x + 1:x + 3])[0]; put(x, 3, [(f'\tJUMP\t{lab[j]}', '')])
    elif c == 0x69: put(x, 2, [(f'\tPORTA_ON\t{D[x+1]}', 'glide time (ticks)')])
    elif c == 0x6b: put(x, 1, [('\tPORTA_OFF', '')])
# pitch table
pt = []
for i in range(0, 384, 8):
    a = f.pitch + 2 * i
    put(a, 16, [('\tdc.w\t' + ','.join(f'${struct.unpack(">H",D[a+2*k:a+2*k+2])[0]:04X}' for k in range(8)), f'semitone {i//4}' + (f' (octave {i//48})' if i % 48 == 0 else ''))])
put(f.vars, f.smpbase - f.vars, [(f'\tdcb.b\t${f.smpbase - f.vars:X},0', 'driver variables (see DRV_* / VC_* equates)')])
put(f.smpbase, 64, [('\tdcb.b\t64,0', 'silent 32-word sample used for stopped channels')])
for n, h, ln, rate in samples:
    put(h, 6, [('\tdc.b\t' + ','.join(f'${b:02X}' for b in D[h:h+6]), f'sample {n} header: length {ln} bytes, {rate} Hz (not used by the driver)')])
    # split the sample at any interior labels
    cuts = sorted(set([h + 6] + [o2 for o2 in lab if h + 6 < o2 < h + 6 + ln] + [h + 6 + ln]))
    for s0, s1 in zip(cuts, cuts[1:]):
        put(s0, s1 - s0, [(f'\tincbin\t"samples/{NAME}_smp{n:02d}.raw",{s0 - h - 6},{s1 - s0}', f'{s1 - s0} bytes')])

o = 0x612
keys = sorted(items)
while o < len(D):
    label(o)
    if o in items:
        size, lines = items[o]
        lo = o
        for i, ln in enumerate(lines):
            txt, cm = ln[0], ln[1]
            line(txt, lo, cm if cm else '')
            if len(ln) > 2: lo += ln[2]
        o += size
        continue
    # gap: emit raw bytes up to next item/label
    e = o + 1
    while e < len(D) and e not in items and e not in lab: e += 1
    if e == o + 1 and D[o] == 0x67 and o > 0x612 and o < f.calltab:
        line('\tENDTRACK', o, 'unreachable: follows a JUMP'); o = e; continue
    for p in range(o, e, 16):
        q = min(e, p + 16)
        line('\tdc.b\t' + ','.join(f'${b:02X}' for b in D[p:q]), p, A.gap_comment(NAME, p) if p == o else '')
    o = e
open(os.path.join(OUT, f'{NAME}.s'), 'w').write('\n'.join(out) + '\n')
print('written', len(out), 'lines; samples', len(samples), 'patterns', npat, 'instr', ninstr)
