"""Make enhanced/sound/gng_music_512k.s: the music for 512K machines - the 512K effects package with the
1MB package's tunes added.

Both packages are the same driver (Richard Frankish's player) with the same instrument numbers:
instruments 0-9 are the music's (the 512K file keeps them as dummies), 10-37 the effects'. The
new source is put together from the two symbolic sources, in the 1MB file's order:

  1MB:   driver, MusicTable (the 15 tunes), SfxTable, InstrumentTable, instruments 0-8 (the
         tunes use 1-6 and 8; 0 and 7 are unused)
  512K:  instrument 9 (an effect's: the 512K file's Ins00) and instruments 10-37 (the effects')
  1MB:   the tunes' voice data and patterns
  512K:  the 30 effect sequences
  1MB:   PatternTable, the volume envelopes, PitchTable, DriverVars, SampleBase
  1MB:   samples 0-9 (the tunes' samples: 34,314 bytes, and the 116-byte sample 4)
  512K:  its 9 samples (the effects'), renamed EffSmp.., in their own order

So every tune plays as in the 1MB package (its instruments and samples, and no tune instrument
runs past its sample chain into an effect's), and every effect as in the 512K package (its
instruments, and its samples in the same order: the instruments that run past their sample
into the next one find the same neighbours; the last one runs past the end of the package, as
the 512K one did).

Quality (--rate N/D; the game's package: 3/4, the default): the tunes' sampled instruments (samples 5-9: 32,726 bytes)
resampled to N/D of their rate (scipy's polyphase filter; the loop samples 7-9 as loops), their
instruments' lengths set to the new sizes and their period multipliers divided by N/D (capped
at $FFFF: $8000 x 2 is 1 in 65,536 short), so every note keeps its pitch. Samples 0-4 (the
single-cycle waveforms, 1,650 bytes) stay: their length is their pitch. The new samples go to
enhanced/sound/samples/r<N>_<D>/ (made again each time; r3_4/ is kept in the repository, so
the committed gng_music_512k.s assembles as it is). --rate 1: full quality, as the 1MB package.
The original packages and their samples are read from original/sound/; the package assembles
with both original/sound and enhanced/sound as include paths (its incbins: samples/...).

  python3 enhanced/sound/tools/make_music_512k.py [--rate N/D] [--out FILE]
                                                  (default enhanced/sound/gng_music_512k.s)"""
import os, re, sys
from fractions import Fraction

HERE = os.path.dirname(os.path.abspath(__file__))
SND = os.path.join(HERE, '..')                                    # enhanced/sound: what this makes
ORIG_SND = os.path.join(HERE, '..', '..', '..', 'original', 'sound')  # the original packages
M = open(os.path.join(ORIG_SND, 'gng_music_1mb.s')).read().split('\n')
K = open(os.path.join(ORIG_SND, 'gng_sfx_512k.s')).read().split('\n')


def at(lines, label):
    return next(i for i, l in enumerate(lines) if re.match(re.escape(label) + r':', l))


def part(lines, start, end):
    """lines from the line with label start (or index) up to the label end (excluded)"""
    a = start if isinstance(start, int) else at(lines, start)
    b = end if isinstance(end, int) else at(lines, end)
    return lines[a:b]


def effects(lines):
    """512K lines with its samples renamed (Smp.., SmpHdr.. -> EffSmp.., EffSmpHdr..)"""
    return [re.sub(r'\bSmp(Hdr)?(\d\d)', r'EffSmp\g<1>\2', l) for l in lines]


head = part(M, 0, 'SfxTable')
head = '\n'.join(head)
head = head.replace('\torg\t$3604C', '\torg\t$28E54')
n = head.count('dc.l    $00006CDD')
assert n == 2, n
head = head.replace('dc.l    $00006CDD', 'dc.l    (SndEnd-SndEntry+3)/4')
out = [';==============================================================================',
       '; gng_music_512k.s - made by enhanced/sound/tools/make_music_512k.py from gng_music_1mb.s and',
       '; gng_sfx_512k.s: the 512K effects package with the 1MB tunes (see that script). Do not edit.',
       ';==============================================================================',
       head]
out += part(M, 'SfxTable', 'Ins07')
ins07 = part(M, 'Ins07', 'Ins08')                      # (unused by any tune or effect; its loop
out += [l.replace('Smp10-SampleBase', 'Smp09-SampleBase') for l in ins07]   # was the 1MB effect sample 10)
out += part(M, 'Ins08', 'Ins09')
out += ['Ins09:\t; instrument 9 is an effect\'s (the 512K file\'s Ins00, which its dummies 0-9 share)']
out += effects(part(K, 'Ins00', 'Ins10')[1:])
out += effects(part(K, 'Ins10', 'Sfx00_Ch3'))
out += part(M, 'Mus00_Ch0', 'Sfx00_Ch3')
out += effects(part(K, 'Sfx00_Ch3', 'PitchTable'))
out += ['\teven']
out += part(M, 'PatternTable', 'SmpHdr00')
out += ['; ---- the tunes\' samples (the 1MB package\'s 0-9)']
out += part(M, 'SmpHdr00', 'SmpHdr10')
out += ['; ---- the effects\' samples (the 512K package\'s, in its order)']
k0 = at(K, 'SmpHdr00')
out += effects(K[k0:])
out += ['\teven', 'SndEnd:']

RESAMPLED = (5, 6, 7, 8, 9)                 # the sampled instruments' samples
LOOPS = (7, 8, 9)                           # played as loops (Ins05: 8 whole; Ins06: 7; Ins08: 9)
TUNE_INS = {5: (8, 8), 6: (5, 7), 7: (6, 9), 8: (6, 9)}     # instrument: (attack, loop) sample


def resample(data, f, loop):
    """8-bit signed samples at f (a Fraction) of their rate, an even number of bytes"""
    import numpy as np
    from scipy.signal import resample_poly
    x = np.frombuffer(data, dtype=np.int8).astype(float)
    p, q = f.numerator, f.denominator
    pad = 32 * q
    if loop: x = np.concatenate([x[-pad:], x, x[:pad]])            # as it repeats
    y = resample_poly(x, p, q)
    if loop: y = y[pad * p // q:len(y) - pad * p // q]
    n = int(round(len(data) * f / 2)) * 2
    y = np.resize(y, n) if len(y) < n else y[:n]
    return np.clip(np.round(y), -128, 127).astype(np.int8).tobytes()


def quality(lines, f):
    """the tunes' sampled instruments at f of their rate (see the module's text)"""
    tag = f'r{f.numerator}_{f.denominator}'
    d = os.path.join(SND, 'samples', tag)
    os.makedirs(d, exist_ok=True)
    size = {}
    for n in RESAMPLED:
        raw = open(os.path.join(ORIG_SND, 'samples', f'gng_music_1mb_smp{n:02d}.raw'), 'rb').read()
        new = resample(raw, f, n in LOOPS)
        open(os.path.join(d, f'gng_music_1mb_smp{n:02d}.raw'), 'wb').write(new)
        size[n] = len(new)
    text = '\n'.join(lines)
    for n in RESAMPLED:
        old = re.search(rf'(SmpHdr{n:02d}:\n\s+dc\.b\s+)\$00,\$00,\$([0-9A-F]{{2}}),\$([0-9A-F]{{2}}),\$([0-9A-F]{{2}}),\$([0-9A-F]{{2}})[^\n]*', text)
        hz = round(int(old.group(4) + old.group(5), 16) * f)
        b = size[n].to_bytes(2, 'big') + hz.to_bytes(2, 'big')
        text = text.replace(old.group(0), old.group(1) + '$00,$00,' + ','.join(f'${x:02X}' for x in b)
                            + f'     ; sample {n} header: length {size[n]} bytes, {hz} Hz (resampled to {f} of the rate)')
        text, k = re.subn(rf'incbin  "samples/gng_music_1mb_smp{n:02d}\.raw",0,\d+;[^\n]*',
                          f'incbin  "samples/{tag}/gng_music_1mb_smp{n:02d}.raw",0,{size[n]}; {size[n]} bytes', text)
        assert k == 1
    for ins, (a, l) in TUNE_INS.items():
        m = re.search(rf'(Ins{ins:02d}:\n(?:[^\n]*\n){{4}})\s+dc\.w\s+\$([0-9A-F]{{4}}),\$([0-9A-F]{{4}})[^\n]*\n\s+dc\.w\s+\$([0-9A-F]{{4}}),\$([0-9A-F]{{4}})[^\n]*', text)
        mul = [min(0xFFFF, round(int(m.group(k), 16) / f)) for k in (4, 5)]
        new = (m.group(1) + f'        dc.w    ${size[a] // 2:04X},${size[l] // 2:04X}                 ; attack / loop length (words) = {size[a]} / {size[l]} bytes\n'
               + f'        dc.w    ${mul[0]:04X},${mul[1]:04X}                 ; period multipliers (PitchTable * mul >> 16): / {f}')
        text = text.replace(m.group(0), new)
    return text.split('\n')


args = sys.argv[1:]
rate = Fraction(args[args.index('--rate') + 1]) if '--rate' in args else Fraction(3, 4)
dest = args[args.index('--out') + 1] if '--out' in args else os.path.join(SND, 'gng_music_512k.s')
if rate != 1:
    assert 0 < rate < 1, rate
    out = quality(out, rate)
    out[2] = out[2] + f' Tunes\' samples 5-9 at {rate} of their rate (--rate).'
open(dest, 'w', newline='\n').write('\n'.join(out).rstrip('\n') + '\n')      # (LF on every system: it is committed)
print(os.path.relpath(dest, os.path.join(SND, '..', '..')), 'written' + (f' (tunes\' samples 5-9 at {rate} of their rate)' if rate != 1 else ''))
