"""At what rates does the game actually play each sample? Runs the real driver (sndemu.Driver)
through every tune and effect of a package and records the Paula period whenever a channel plays
a sample. A sample that is never played above rate R can be resampled down to about R without
losing anything the game uses; halving a sample's rate halves its size, and its instruments then
need their period multiplier doubled (or the notes moved an octave down).
   python3 sound/tools/sample_rates.py sound/gng_music_1mb.s sound/bin/music_1mb.hunk 15 30"""
import re, sys, os, statistics
sys.path.insert(0, os.path.dirname(__file__))
from sndemu import Driver, PAL_CLOCK
src, binf, ntunes, nsfx = sys.argv[1], sys.argv[2], int(sys.argv[3]), int(sys.argv[4])
S = open(src).read().split('\n')
def addr_of(label):
    i = next(k for k, l in enumerate(S) if l.startswith(label+':'))
    for l in S[i+1:i+6]:
        m = re.search(r';\s*([0-9A-F]{5})', l)
        if m: return int(m.group(1), 16)
smp = {}
for l in S:
    m = re.search(r'sample (\d+) header: length (\d+) bytes, (\d+) Hz', l)
    if m: smp[int(m.group(1))] = (int(m.group(2)), int(m.group(3)))
offs = {n: addr_of(f'Smp{n:02d}') for n in smp}
varoff = addr_of('DriverVars')
BASE = 0x10000
def which(a):
    for n, o in offs.items():
        if BASE+o <= a < BASE+o+max(smp[n][0], 2): return n
    return None
used = {n: [] for n in smp}
def run(cmd, num, frames):
    d = Driver(binf, BASE)
    lc = [0]*4; per = [0]*4
    d.call(cmd, num)
    for t in range(frames):
        for reg, size, val in d.writes:
            regs = [(reg, val)] if size == 2 else [(reg, (val >> 16) & 0xffff), (reg+2, val & 0xffff)]
            for r, v in regs:
                if 0xA0 <= r < 0xE0:
                    c, o = (r-0xA0) >> 4, (r-0xA0) & 15
                    if o == 0: lc[c] = (lc[c] & 0xffff) | (v << 16)
                    elif o == 6: per[c] = v
                    if o in (2, 6):                   # a new sample (e.g. the loop part) or period
                        if o == 2: lc[c] = (lc[c] & 0xffff0000) | v
                        n = which(lc[c])
                        if n is not None and per[c] >= 64: used[n].append((per[c], cmd, num))
        d.writes.clear()
        d.call(0)
for k in range(ntunes): run(1, k, 50*120)
for k in range(nsfx): run(2, k, 50*10)
tot = 0; cand = 0
print('sample  bytes  header Hz  played at (Hz): max  median  | users')
for n in sorted(smp):
    ln, hz = smp[n]
    if not used[n]:
        print(f'{n:6d} {ln:6d} {hz:9d}   never played'); continue
    rates = [PAL_CLOCK/p for p, _, _ in used[n]]
    who = sorted({('tune ' if c == 1 else 'sfx ')+str(k) for _, c, k in used[n]})
    print(f'{n:6d} {ln:6d} {hz:9d}   {max(rates):8.0f} {statistics.median(rates):7.0f}  | {", ".join(who[:6])}{" ..." if len(who) > 6 else ""}')
