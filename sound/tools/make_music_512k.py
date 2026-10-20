"""Make sound/gng_music_512k.s: the music for 512K machines - the 512K effects package with the
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

  python3 sound/tools/make_music_512k.py        (writes sound/gng_music_512k.s)"""
import os, re

HERE = os.path.dirname(os.path.abspath(__file__))
SND = os.path.join(HERE, '..')
M = open(os.path.join(SND, 'gng_music_1mb.s')).read().split('\n')
K = open(os.path.join(SND, 'gng_sfx_512k.s')).read().split('\n')


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
       '; gng_music_512k.s - made by sound/tools/make_music_512k.py from gng_music_1mb.s and',
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
open(os.path.join(SND, 'gng_music_512k.s'), 'w').write('\n'.join(out).rstrip('\n') + '\n')
print('sound/gng_music_512k.s written')
