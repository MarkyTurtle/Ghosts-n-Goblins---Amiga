"""More raw tables as readable source for gen.py's DATA_BLOCKS (512K addresses, main.bin
loaded at $80): BOB frame descriptors, the copper list template, the platform paths, the
Petite Devil's (unused) appearance points and the Dragon's flight paths.
build(D, B, names) returns a list of (start, end, lines, labels); labels already named in the
annotation database (names) are kept. Macros FRAME / ISTEP / ILOOP / DSTEP / DLOOP are in
the prelude."""
import struct
from hw import CUSTOM

TYPES = ['WoodyPig', 'Crow', 'PetiteDevil', 'FlyingKnight', 'BlueKiller', 'RedArremer', 'Satan',
         'Magician', 'Unicorn', 'Skeleton', 'BigMan', 'Zombie', 'Dragon', 'Astaroth', 'Fire',
         'Princess', 'Type16', 'Plant', 'FirePillar']
COMPASS = ['E', 'ESE', 'SE', 'SSE', 'S', 'SSW', 'SW', 'WSW', 'W', 'WNW', 'NW', 'NNW', 'N', 'NNE', 'NE', 'ENE']


def build(D, B=0x80, names=None):
    names = names or {}
    rb = lambda a: D[a-B]
    rsb = lambda a: struct.unpack('>b', D[a-B:a-B+1])[0]
    rw = lambda a: struct.unpack('>h', D[a-B:a-B+2])[0]
    ruw = lambda a: struct.unpack('>H', D[a-B:a-B+2])[0]
    px = lambda v: f'{v/256:+.2f}'
    blocks = []

    def known(s, e):
        return {a: n for a, n in names.items() if s <= a < e}

    def finish(s, e, L, lab):
        for a, n in known(s, e).items():           # every database name must be emitted
            assert lab.get(n) == a, (hex(a), n)
        blocks.append((s, e, L, lab))

    def label(L, lab, a, n):
        L.append(f'{n}:'); lab[n] = a

    blocks.append(bob_frame_descs(D, B, 0x4FF0, 0x53AA, 0x538E, names))

    # ------------------------------------------------------------ CopperTemplate $7E0E-$7F8E
    S, E = 0x7E0E, 0x7F8E
    nm = known(S, E); lab = {}; L = []
    parts = {0: 'COPPER_INIT (COP1): before line $44 the 16-line strip at $64468, all eight sprites,\n'
                '; then the copper interrupt and a jump to COP2 (the front list)',
             0x78: 'COPPER_A1: playfield planes in SCREEN_0 (one of the four lists COP2 points at)',
             0xA8: 'COPPER_A2: SCREEN_1', 0xD8: 'COPPER_B1: SCREEN_2', 0x108: 'COPPER_B2: SCREEN_3',
             0x138: 'COPPER_MAP: the between-level progress map (50-byte lines, modulo $D8 then $92)'}
    a = S
    while a < E:
        o = a-S
        if o in parts:
            L += ['; '+x for x in parts[o].split('\n; ')]
        if a in nm: label(L, lab, a, nm[a])
        w1, w2 = ruw(a), ruw(a+2)
        if w1 & 1:
            if (w1, w2) == (0xFFFF, 0xFFFE): c = 'end of list'
            elif w2 & 1: c = f'SKIP line ${w1>>8:02X}'
            elif w1 >> 8 == 0xFF: c = f'WAIT line $FF, x ${w1 & 0xFE:02X} (the PAL wrap: later waits are lines $100+)'
            else: c = f'WAIT line ${w1>>8:02X}' + (' ($124 after the wrap)' if o > 0x138 else '')
            L.append(f'\tdc.w\t${w1:04X},${w2:04X}\t; {c}')
            a += 4; continue
        reg = CUSTOM.get(w1, f'${w1:03X}')
        if reg.endswith('PTH') and ruw(a+4) == w1+2:
            v = (w2 << 16) | ruw(a+6)
            L.append(f'\tdc.w\t{reg},${w2:04X},{CUSTOM[w1+2]},${ruw(a+6):04X}\t; {reg[:-1]} = ${v:05X}')
            a += 8; continue
        c = {'INTREQ': 'set COPER: the copper interrupt (level 3)',
             'COPJMP2': 'jump to COP2LC (the front list)',
             'BPLCON1': 'no fine scroll'}.get(reg, '')
        L.append(f'\tdc.w\t{reg},${w2:04X}' + (f'\t; {c}' if c else ''))
        a += 4
    finish(S, E, L, lab)

    # ------------------------------------------------------------ EnemyShotFrames, EffectFrames
    S, E = 0x9002, 0x916A
    nm = known(S, E); lab = {}; L = []
    for a in range(S, E, 4):
        if a in nm:
            if a != S: L.append('')
            label(L, lab, a, nm[a]); base = a
        L.append(f'\tFRAME\t${ruw(a):04X},{rsb(a+2)},{rb(a+3)}\t; {(a-base)//4}')
    finish(S, E, L, lab)

    # ------------------------------------------------------------ ItemPaths, ItemPathScripts
    S, E = 0xA72E, 0xA91C
    nm = known(S, E); lab = {}; L = []
    P1, P2 = 0xA72E, 0xA7FC
    def two_level(top, end, kind):
        """level-2 tables of types 2-5; returns ({table: (type, n)}, {data target: (type, param)})"""
        l2 = {}
        for t in range(2, 6):
            l2.setdefault(top+2*t+rw(top+2*t), t)
        data = {}
        for x, t in l2.items():
            for p in range(16):
                q = x+2*p
                if q in l2 and p: break
                if data and q >= min(data): break
                data.setdefault(q+rw(q), (t, p))
        starts = sorted(l2)
        out = {}
        for k, x in enumerate(starts):
            nxt = starts[k+1] if k+1 < len(starts) else min(data)
            out[x] = (l2[x], (nxt-x)//2)
        return out, data
    pl2, pdata = two_level(P1, P2, 'paths')
    sl2, sdata = two_level(P2, E, 'scripts')
    nm_ = dict(nm)
    for x, (t, n) in pl2.items(): nm_.setdefault(x, f'ItemPathsType{t}')
    for x, (t, p) in pdata.items(): nm_.setdefault(x, f'ItemSteps{t}_{p}')
    for x, (t, n) in sl2.items(): nm_.setdefault(x, f'ItemScriptsType{t}')
    for x, (t, p) in sdata.items(): nm_.setdefault(x, f'ItemScript{t}_{p}')
    # loop targets inside scripts
    sstarts = sorted(sdata)
    loops = {}
    for k, x in enumerate(sstarts):
        end = sstarts[k+1] if k+1 < len(sstarts) else E
        a = x
        while a < end:
            if rb(a+1) & 0x80:
                t = a+2+rw(a+2); loops[t] = x; a += 4
            else: a += 2
        assert a == end, hex(a)
    for t, x in loops.items():
        if t not in nm_: nm_[t] = f'{nm_[x]}_{t-x}'
    def top_table(top, l2, comment):
        label(L, lab, top, nm_[top])
        for t in range(6):
            q = top+2*t
            if rw(q) == 0:
                L.append(f'\tdc.w\t0\t\t; type {t}: no path'); continue
            x = q+rw(q)
            note = '' if t >= 2 else ' (types 0-1 never start a path)'
            L.append(f'\tdc.w\t{nm_[x]}-*\t; type {t}{note}')
        for x in sorted(l2):
            t, n = l2[x]
            label(L, lab, x, nm_[x])
            for p in range(n):
                q = x+2*p
                L.append(f'\tdc.w\t{nm_[q+rw(q)]}-*\t; param {p}')
    top_table(P1, pl2, 'paths')
    pst = sorted(pdata)
    L.append('; step tables: (dx, dy) per step number, pixels x 256 a frame (Y up)')
    for k, x in enumerate(pst):
        end = pst[k+1] if k+1 < len(pst) else P2
        users = ', '.join(f'type {t} param {p}' for q, (t, p) in pdata.items() if q == x)
        label(L, lab, x, nm_[x])
        for s_ in range((end-x)//4):
            dx, dy = rw(x+4*s_), rw(x+4*s_+2)
            L.append(f'\tdc.w\t{dx},{dy}\t; step {s_}: dx {px(dx)}, dy {px(dy)}')
    L.append('')
    top_table(P2, sl2, 'scripts')
    L.append('; scripts: (step, frames); the last entry has bit 7 set on frames and loops back')
    for k, x in enumerate(sstarts):
        end = sstarts[k+1] if k+1 < len(sstarts) else E
        a = x
        while a < end:
            if a in nm_: label(L, lab, a, nm_[a])
            st, fr = rb(a), rb(a+1)
            if fr & 0x80:
                L.append(f'\tILOOP\t{st},{fr & 0x7F},{nm_[a+2+rw(a+2)]}'); a += 4
            else:
                L.append(f'\tISTEP\t{st},{fr}'); a += 2
    finish(S, E, L, lab)

    # ------------------------------------------------------------ PetiteDevilPath $D2D0-$D35C
    S, E = 0xD2D0, 0xD35C
    nm = known(S, E); lab = {}; L = []
    sets = {}
    for i in range(9):
        a = S+2*i; sets[a+rw(a)] = i
    label(L, lab, S, nm[S])
    for i in range(9):
        a = S+2*i
        L.append(f'\tdc.w\tPetiteDevilPath_{i}-*\t; {i}')
    a = S+18
    for t in sorted(sets):
        assert t == a, (hex(t), hex(a))
        n = ruw(t)
        label(L, lab, t, f'PetiteDevilPath_{sets[t]}')
        L.append(f'\tdc.w\t{n}\t\t; points')
        for k in range(n):
            b = t+2+4*k
            L.append(f'\tdc.w\t${ruw(b):04X},${ruw(b+2):04X}\t; world x, y')
        a = t+2+4*n
    assert a == E
    finish(S, E, L, lab)

    # ------------------------------------------------------------ Dragon paths
    def dpath(a, end, nm_, L, lab, term=False):
        while a < end:
            if a in nm_: label(L, lab, a, nm_[a])
            fr, d = rb(a), rb(a+1)
            if term and fr == 0 and d == 0:
                L.append('\tdc.w\t0\t\t; end'); a += 2; continue
            if fr & 0x80:
                L.append(f'\tDLOOP\t{fr & 0x7F},{d},{nm_[a+2+rw(a+2)]}\t; {COMPASS[d]}, then loop'); a += 4
            else:
                L.append(f'\tDSTEP\t{fr},{d}\t; {COMPASS[d]}'); a += 2
        assert a == end, hex(a)

    S, E = 0x10F46, 0x10F54
    nm = known(S, E); lab = {}; L = []
    dpath(S, E, nm, L, lab, term=True)
    finish(S, E, L, lab)

    S, E = 0x11302, 0x1130A
    nm = known(S, E); lab = {}; L = []
    for a in (0x11302, 0x11306):
        label(L, lab, a, nm[a])
        for f in range(2):
            fr, d = rb(a+2*f), rb(a+2*f+1)
            L.append(f'\tDSTEP\t{fr},{d}\t; facing {"right" if f == 0 else "left"}: {COMPASS[d]}')
    finish(S, E, L, lab)

    S, E = 0x11408, 0x114EE
    nm = dict(known(S, E)); lab = {}; L = []
    p1 = S+rw(S)
    nm[p1] = 'DragonPatrolLeftward'; nm[0x1145E] = 'DragonPatrolRightward'
    label(L, lab, S, nm[S])
    L.append(f'\tdc.w\t{nm[p1]}-*')
    dpath(p1, 0x1145E, nm, L, lab)
    dpath(0x1145E, 0x114B2, nm, L, lab)
    for top, side in ((0x114B2, 'right'), (0x114D0, 'left')):
        sub = {top+2*k+rw(top+2*k): k for k in range(2)}
        for x, k in sub.items(): nm[x] = f'{nm[top]}{"Upper" if k == 0 else "Lower"}'
        end = 0x114D0 if top == 0x114B2 else E
        label(L, lab, top, nm[top])
        for k in range(2):
            x = top+2*k+rw(top+2*k)
            L.append(f'\tdc.w\t{nm[x]}-*\t; in the {"upper" if k == 0 else "lower"} half of the screen')
        dpath(top+4, end, nm, L, lab)
    finish(S, E, L, lab)

    # ------------------------------------------------------------ LevelFileIndex, FileTable
    blocks.append(file_table(D, B, 0x7F8E, names))
    return blocks


def bob_frame_descs(D, B, S, E, bat, names):
    """BobFrameDescs block: 19 offsets, then the frame tables up to E (bat table at bat)"""
    rb = lambda a: D[a-B]
    rsb = lambda a: struct.unpack('>b', D[a-B:a-B+1])[0]
    rw = lambda a: struct.unpack('>h', D[a-B:a-B+2])[0]
    ruw = lambda a: struct.unpack('>H', D[a-B:a-B+2])[0]
    def label(L, lab, a, n):
        L.append(f'{n}:'); lab[n] = a
    # ------------------------------------------------------------ BobFrameDescs $4FF0-$53AA
    nm = {a: n for a, n in names.items() if S <= a < E}; lab = {}; L = []
    tgt = {}
    for i in range(19):
        a = S+2*i
        if rw(a): tgt.setdefault(a+rw(a), i)
    starts = sorted(set(tgt) | {bat})
    tname = {}
    for t in starts:
        tname[t] = nm.get(t) or f'BobFrames{TYPES[tgt[t]]}'
    for i in range(19):
        a = S+2*i
        if a in nm and a != S: label(L, lab, a, nm[a])
        elif a == S: label(L, lab, a, nm[a])
        if rw(a):
            L.append(f'\tdc.w\t{tname[a+rw(a)]}-*\t; {i:2d} {TYPES[i]}')
        else:
            L.append(f'\tdc.w\t0\t\t; {i:2d} {TYPES[i]}: no graphics')
    a = S+38
    for k, t in enumerate(starts):
        assert t == a, (hex(t), hex(a))
        end = starts[k+1] if k+1 < len(starts) else E
        assert (end-t) % 4 == 0
        who = 'bat graphics (Crow with param < 3)' if t == bat else \
              ', '.join(TYPES[i] for i in range(19) if rw(S+2*i) and S+2*i+rw(S+2*i) == t)
        if tname[t] == 'BobFrameDescsRedCrow': who += ' (also the red crow, param 3)'
        L.append(f'; {who}: {(end-t)//4} frames')
        label(L, lab, t, tname[t])
        for f in range((end-t)//4):
            b = t+4*f
            L.append(f'\tFRAME\t${ruw(b):04X},{rsb(b+2)},{rb(b+3)}\t; {f}')
        a = end
    for a_, n_ in nm.items(): assert lab.get(n_) == a_, (hex(a_), n_)
    return (S, E, L, lab)



# what each file holds, by first track (disk/FILES.md)
FILE_INFO = {33: "Arthur's sprite frames", 37: 'small item / scenery BOBs', 38: 'enemy BOB sets',
             57: 'weapon / effect BOBs, tail', 58: 'enemy shot BOBs', 59: 'weapon / pickup / effect BOBs',
             61: 'font', 62: 'progress map (RLE)', 64: 'sound driver, music and effects (1MB)',
             82: 'copyright warning screen (RLE)', 84: 'level 0 tiles', 89: 'level 1 tiles',
             97: 'level 2 tiles', 101: 'level 3 tiles', 104: 'level 4 tiles', 106: 'level 5 tiles',
             108: 'level 6 tiles', 126: 'sound driver and effects (512K)'}


def file_table(D, B, S, names):
    """LevelFileIndex (7 offsets to the level file entries) followed by FileTable: FENTRY
    dest, length, first track, up to the end of the last level entry. Works out its own size."""
    rw = lambda a: struct.unpack('>h', D[a-B:a-B+2])[0]
    rl = lambda a: struct.unpack('>L', D[a-B:a-B+4])[0]
    ruw = lambda a: struct.unpack('>H', D[a-B:a-B+2])[0]
    lv = [S+2*i+rw(S+2*i) for i in range(7)]
    T = S+14
    assert all((x-T) % 10 == 0 for x in lv) and lv == sorted(lv)
    E = lv[-1]+10
    nm = {a: n for a, n in names.items() if S <= a < E}
    for i, x in enumerate(lv): nm.setdefault(x, f'FileLevel{i}')
    L, lab = [], {}
    L.append(f'{nm[S]}:'); lab[nm[S]] = S
    for i, x in enumerate(lv):
        L.append(f'\tdc.w\t{nm[x]}-*\t; level {i}')
    for a in range(T, E, 10):
        if a in nm: L.append(f'{nm[a]}:'); lab[nm[a]] = a
        dest, ln, trk = rl(a), rl(a+4), ruw(a+8)
        n = (ln+6311)//6312
        tr = f'track {trk}' if n == 1 else f'tracks {trk}-{trk+n-1}'
        L.append(f'\tFENTRY\t${dest:05X},${ln:05X},{trk}\t; {tr}: {FILE_INFO.get(trk, "?")}')
    for a_, n_ in nm.items(): assert lab.get(n_) == a_, (hex(a_), n_)
    return (S, E, L, lab)
