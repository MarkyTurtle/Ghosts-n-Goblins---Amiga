"""Which samples each tune and effect of a music package uses, including the overrun tails of
instruments whose length runs past their sample, and their sizes.
   python3 sound/tools/tune_samples.py sound/gng_music_1mb.s"""
import re, sys
src = open(sys.argv[1]).read().split('\n')
lab = {}; cur = None
for i, l in enumerate(src):
    m = re.match(r'^(\w+):', l)
    if m: lab[m.group(1)] = i
def body(name):
    i = lab[name]+1
    while i < len(src):
        l = src[i]
        if re.match(r'^\w+:', l): i += 1; continue
        yield l.split(';')[0].split(); i += 1
# sample chain: offsets from SampleBase
smp = {}; off = 64
for i, l in enumerate(src):
    m = re.search(r'sample (\d+) header: length (\d+) bytes', l)
    if m: n, ln = int(m.group(1)), int(m.group(2)); off += 6; smp[n] = (off, ln); off += ln
def ins_samples(k):
    i = lab[f'Ins{k:02d}']+1
    a = src[i].split(';')[0]; b = src[i+1].split(';')[0]; lens = src[i+4]
    la, lb = [int(x, 16)*2 for x in re.findall(r'\$([0-9A-F]+)', lens.split(';')[0])]
    out = set()
    for ref, ln in ((a, la), (b, lb)):
        m = re.search(r'Smp(\d+)', ref)
        if not m: continue
        s0, _ = smp[int(m.group(1))]
        for n, (o, l) in smp.items():          # every sample the played range touches
            if o < s0+ln and o+l > s0: out.add(n)
    return out
def walk(name, seen):
    ins = set()
    for t in body(name):
        if not t: continue
        op = t[0]
        if op == 'NOTE': ins.add(int(t[1].split(',')[1]))
        elif op in ('CALL', 'CALLN'):
            p = int(t[1].split(',')[0])
            if p not in seen: seen.add(p); ins |= walk(f'Pat{p:02d}', seen)
        elif op in ('RETURN', 'ENDTRACK', 'JUMP'): break
    return ins
def table(name, n):
    res = []
    i = lab[name]+1
    for k in range(n):
        chans = []
        for c in range(4):
            m = re.search(r'(\w+)-\*', src[i+4*k+c].split(';')[0]); chans.append(m.group(1) if m else None)
        insts = set()
        for ch in chans:
            if ch: insts |= walk(ch, set())
        samples = set()
        for x in insts: samples |= ins_samples(x)
        res.append((k, sorted(insts), sorted(samples), sum(smp[s][1]+6 for s in samples)))
    return res
tunes = table('MusicTable', 15); sfx = table('SfxTable', 30)
sfxs = set().union(*[set(s) for _, _, s, _ in sfx])
print('effects use samples', sorted(sfxs), sum(smp[s][1]+6 for s in sfxs), 'bytes')
print('all samples', sum(l+6 for o, l in smp.values()))
for k, ins, ss, sz in tunes:
    extra = set(ss)-sfxs
    print(f'tune {k:2d}: {sz:6,d} bytes in {len(ss)} samples; beyond the effects\' samples: {sum(smp[s][1]+6 for s in extra):6,d}  {sorted(extra)}')
mus = set().union(*[set(s) for _, _, s, _ in tunes])
print(f'all tunes together use samples {sorted(mus)}: {sum(smp[s][1]+6 for s in mus):,d} bytes '
      f'({sum(smp[s][1]+6 for s in mus - sfxs):,d} not shared with the effects)')
