"""Build a playable extended ADF (UAE-1ADF) of the game from the files in this archive, using the
game's own track format, and check images.          Run from the archive root:

  python3 tools/disk/mkdisk.py [-o gng.adf] [--main512 main.bin] [--main1mb main_1mb.bin]
                               [--boot boot.bin] [--file NAME=PATH ...] [--add TRACK=PATH ...]
                               [--raw DIR]
  python3 tools/disk/mkdisk.py --check gng.adf       decode an image and compare it with bin/tracks
  python3 tools/disk/mkdisk.py --compare-raw DIR     compare the MFM with raw track dumps tNNN.bin
  python3 tools/disk/mkdisk.py --layout              print the layout read from the binaries

The disk layout is not stored here: it is read from the programs that will be on the disk -
the FileTable of both main programs (FENTRY: load address, length, first track) and the three
loads in the bootblock (loading screen, 512K and 1MB main programs). Each file's contents come
from disk/files (named tNNN_...) or from the replacement given on the command line, and are
written over the original track contents (bin/tracks), so bytes after the end of a file stay
as on the original disk; with no options the image holds exactly the original data.
  python3 tools/disk/mkdisk.py --layout [--main512 ...]    print the layout it works out
A file must have the length its table entry gives, and must end before the next file starts.
To move or resize a file, change its FENTRY (and the bootblock for the three it loads).

Track format (tracks 1-131, see disk/DISKMAP.md): $AAAAAAAA, DSKSYNC $A245, $4489, the track
number as an odd/even MFM word, $62A longs of data as odd/even MFM (all odd halves first, then
all even halves, the checksum long last in each half), checksum = NOT(sum of the longs), then
a gap of MFM zeros with one set bit in its middle (as on the original). The tracks are 105,552
or 105,560 bits long (TRACK_BITS) - longer than a normal track; this is the copy protection,
which is why the image must keep them as raw MFM tracks. Track 0 is a normal AmigaDOS track
(bootblock + filler, bin/track0.bin); tracks no file uses are left blank (MFM zeros, no sync)."""
import argparse, glob, hashlib, os, re, struct, sys

TB = 6312                      # data bytes per custom track ($62A longs)
NLONG = 0x62A
NTRACKS = 160                  # tracks in the image (the game uses 0-131)
# bits per track 1-131: S = 105,552, L = 105,560 (as on the original disk)
_LEN = ('SLLLLSLSLSLSSLLLSSSSSSLSSLSSSSSSLSSSSSSLLLLSLSSSSSSSSLSLSLSSSSLSSSSLLSSSSSSSSSLSSSLSSSS'
        'LLSSSLSLSLLLSLLSSLLLSSLSSSSSSLSSSSLLSSSSSSSS')
TRACK_BITS = {t+1: 105560 if c == 'L' else 105552 for t, c in enumerate(_LEN)}
NEW_TRACK_BITS = 105552         # for tracks beyond the original 131
BLANK_BITS = 100000

# command-line shortcuts: the file starting at this track
ALIASES = {'main512': 110, 'main1mb': 17, 'sfx512': 126, 'music1mb': 64}
# SHA-1 of the image built from the unchanged archive
ORIGINAL_SHA1 = '98b341330c2ea19bcf6a8fad06d88c0c5cd8099a'


# ---------------------------------------------------------------- MFM
class Bits:
    """MFM bit writer: data bits get a clock bit of 1 only between two 0 data bits."""
    def __init__(self):
        self.b = []; self.last = 0
    def raw(self, value, n):
        self.b += [(value >> (n-1-i)) & 1 for i in range(n)]; self.last = self.b[-1]
    def data(self, value, n):            # n data bits, most significant first
        for i in range(n):
            d = (value >> (n-1-i)) & 1
            self.b += [1 if (d == 0 and self.last == 0) else 0, d]; self.last = d
    def odd_even(self, values, width):   # Amiga odd/even split: all odd halves, then all even halves
        mask = int('01'*(width//2), 2)
        for v in values: self.data(self.squeeze((v >> 1) & mask, width), width//2)
        for v in values: self.data(self.squeeze(v & mask, width), width//2)
    @staticmethod
    def squeeze(v, width):               # take the bits at the even positions
        r = 0
        for i in range(width//2): r |= ((v >> (2*i)) & 1) << i
        return r
    def tobytes(self):
        b = self.b + [0]*(-len(self.b) % 8)
        return bytes(int(''.join(map(str, b[i:i+8])), 2) for i in range(0, len(b), 8))


def checksum(payload):
    return ~sum(struct.unpack(f'>{NLONG}L', payload)) & 0xFFFFFFFF


def encode_track(t, payload):
    """raw MFM for custom track t (bytes, bit length)"""
    assert len(payload) == TB
    longs = list(struct.unpack(f'>{NLONG}L', payload)) + [checksum(payload)]
    w = Bits()
    w.raw(0xAAAAAAAA, 32); w.raw(0xA245, 16); w.raw(0x4489, 16)
    w.odd_even([t], 16)
    w.odd_even(longs, 32)
    bits = TRACK_BITS.get(t, NEW_TRACK_BITS)
    gap = bits - len(w.b)      # data bits of zeros, one set in the middle
    n = gap // 2
    w.data(0, n//2); w.data(1, 1); w.data(0, n - n//2 - 1)
    assert len(w.b) == bits
    return w.tobytes(), len(w.b)


def decode_track(raw, nbits):
    """(track number, payload, checksum ok) from raw MFM, or None"""
    s = bin(int.from_bytes(raw, 'big'))[2:].zfill(len(raw)*8)[:nbits]
    s = s + s
    i = s.find(format(0xA245, '016b'))
    if i < 0 or i >= nbits: return None
    p = i + 32
    word = lambda k: int(s[p+16*k:p+16*k+16], 2)
    hdr = ((word(0) & 0x5555) << 1) | (word(1) & 0x5555)
    q = p + 32
    L = lambda k: int(s[q+32*k:q+32*k+32], 2)
    M = 0x55555555
    longs = [((L(k) & M) << 1) | (L(k+NLONG+1) & M) for k in range(NLONG+1)]
    payload = struct.pack(f'>{NLONG}L', *longs[:NLONG])
    return hdr, payload, checksum(payload) == longs[NLONG]


def bootblock_checksum(b):
    s = 0
    for i in range(256):
        s += 0 if i == 1 else struct.unpack('>L', b[4*i:4*i+4])[0]
        if s > 0xFFFFFFFF: s = (s + 1) & 0xFFFFFFFF
    return ~s & 0xFFFFFFFF


# ---------------------------------------------------------------- layout
def file_table(prog, what):
    """[(load address, length, first track)] from a main program's FileTable. It is found by
    LevelFileIndex, which comes just before it: 7 word offsets, each from its entry, to entries
    10 bytes apart (the level tile files, the last entries of the table)."""
    w = lambda o: struct.unpack('>h', prog[o:o+2])[0]
    found = []
    for o in range(0, len(prog)-14, 2):
        t = [o+2*i+w(o+2*i) for i in range(7)]
        T = o+14
        if t[0] <= T or any((x-T) % 10 or y-x != 10 for x, y in zip(t, t[1:])) or (t[0]-T) % 10:
            continue
        ent = [struct.unpack('>LLH', prog[a:a+10]) for a in range(T, t[-1]+10, 10)]
        if all(0 < ln < 0x80000 and 0 < tr < NTRACKS and not d & 1 for d, ln, tr in ent):
            found.append(ent)
    if len(found) != 1: sys.exit(f'{what}: cannot find FileTable ({len(found)} candidates)')
    return found[0]


def boot_loads(boot):
    """the bootblock's loads: (first track, length) of the loading screen and the two main programs.
    The tracks are 'move.w #track,$28.w', the lengths 'move.l #length,d5', in program order:
    screen (track, length), then the main program's length and its 512K / 1MB first tracks."""
    trk = [int.from_bytes(m.group(1), 'big') for m in re.finditer(rb'\x31\xfc(..)\x00\x28', boot, re.S)]
    ln = [int.from_bytes(m.group(1), 'big') for m in re.finditer(rb'\x2a\x3c(....)', boot, re.S)]
    if len(trk) != 3 or len(ln) != 2: sys.exit('bootblock: cannot find its three loads')
    return [(trk[0], ln[0], 'bootblock: loading screen'), (trk[1], ln[1], 'bootblock: 512K main program'),
            (trk[2], ln[1], 'bootblock: 1MB main program')]


def layout(boot, main512, main1mb, extra=()):
    """{first track: (length, [who loads it])}, checked for clashes and overlaps. extra:
    (first track, length) of files no table lists (--add)"""
    files = {}
    def add(t, ln, who):
        if t in files and files[t][0] != ln:
            sys.exit(f'track {t}: {who} reads {ln} bytes, {files[t][1][0]} reads {files[t][0]}')
        files.setdefault(t, (ln, []))[1].append(who)
    for t, ln, who in boot_loads(boot): add(t, ln, who)
    for prog, build in ((main512, '512K'), (main1mb, '1MB')):
        for dest, ln, t in file_table(prog, f'{build} main program'):
            add(t, ln, f'{build} FileTable (to ${dest:X})')
    for t, ln in extra: add(t, ln, 'added (--add)')
    order = sorted(files)
    for t, nxt in zip(order, order[1:] + [NTRACKS]):
        if t + ntracks(files[t][0]) > nxt:
            sys.exit(f'the file at track {t} ({files[t][0]} bytes) runs into track {nxt}')
    return files


def ntracks(n): return (n + TB - 1) // TB


def source_file(t):
    """the file in disk/files that starts at track t"""
    m = glob.glob(f'disk/files/t{t:03d}[-_]*')
    return m[0] if len(m) == 1 else None


# ---------------------------------------------------------------- image
def payloads(files, lay):
    """track payloads: the original tracks with each file written over its first tracks"""
    used = {t+k for t, (ln, _) in lay.items() for k in range(ntracks(ln))}
    trk = {}
    for t in sorted(used):
        f = f'bin/tracks/t{t:03d}.bin'
        trk[t] = bytearray(open(f, 'rb').read() if os.path.exists(f) else bytes(TB))
    for t0, (ln, who) in lay.items():
        path = files.get(t0) or source_file(t0)
        if not path: sys.exit(f'track {t0}: no file in disk/files and none given ({who[0]})')
        data = open(path, 'rb').read()
        if len(data) != ln:
            sys.exit(f'{path} is {len(data):,} bytes but {who[0]} reads {ln:,}: change the table entry')
        for k in range(0, len(data), TB):
            chunk = data[k:k+TB]
            trk[t0 + k//TB][:len(chunk)] = chunk
    return trk


def build(files, boot, lay, raw_dir=None):
    track0 = bytearray(open('bin/track0.bin', 'rb').read())
    track0[:1024] = boot
    struct.pack_into('>L', track0, 4, bootblock_checksum(bytes(track0[:1024])))
    trk = payloads(files, lay)
    heads, datas = [], []
    heads.append(struct.pack('>HHLL', 0, 0, len(track0), len(track0)*8)); datas.append(bytes(track0))
    for t in range(1, NTRACKS):
        if t in trk:
            raw, nb = encode_track(t, bytes(trk[t]))
            if raw_dir: open(f'{raw_dir}/t{t:03d}.bin', 'wb').write(raw)
        else:
            nb = BLANK_BITS; raw = b'\xAA' * (nb // 8)
        raw += b'\0' * (len(raw) & 1)
        heads.append(struct.pack('>HHLL', 0, 1, len(raw), nb)); datas.append(raw)
    return b'UAE-1ADF' + struct.pack('>HH', 0, NTRACKS) + b''.join(heads) + b''.join(datas)


def read_image(img):
    assert img[:8] == b'UAE-1ADF', 'not an extended ADF'
    n = struct.unpack('>H', img[10:12])[0]
    pos = 12 + 12*n; out = []
    for t in range(n):
        _, typ, ln, nb = struct.unpack('>HHLL', img[12+12*t:24+12*t])
        out.append((typ, img[pos:pos+ln], nb)); pos += ln
    return out


def check(path):
    tracks = read_image(open(path, 'rb').read())
    ok = True
    typ, d, nb = tracks[0]
    if typ != 0 or d[:1024] != open('bin/bootblock.bin', 'rb').read():
        print('track 0: bootblock differs from bin/bootblock.bin'); ok = False
    for t in range(1, 132):
        typ, raw, nb = tracks[t]
        r = decode_track(raw, nb)
        if not r or r[0] != t or not r[2]:
            print(f'track {t}: no valid block'); ok = False; continue
        if r[1] != open(f'bin/tracks/t{t:03d}.bin', 'rb').read():
            print(f'track {t}: data differs from bin/tracks'); ok = False
        if nb != TRACK_BITS[t]:
            print(f'track {t}: {nb} bits, the original has {TRACK_BITS[t]}'); ok = False
    print(f'{path}: {"all 131 custom tracks decode, checksums good, data as bin/tracks" if ok else "DIFFERENCES"}')
    return ok


def compare_raw(rawdir):
    """compare each generated track bit for bit with raw MFM dumps of the original (tNNN.bin)"""
    trk = payloads({}, default_layout())
    same = 0
    for t in range(1, 132):
        mine, nb = encode_track(t, bytes(trk[t]))
        orig = open(f'{rawdir}/t{t:03d}.bin', 'rb').read()
        if mine == orig: same += 1
        else: print(f'track {t}: differs from {rawdir}/t{t:03d}.bin')
    print(f'{same} of 131 custom tracks are bit-identical to the raw dumps')
    return same == 131


def default_layout():
    return layout(*(open(f, 'rb').read() for f in DEFAULT_PROGS))


DEFAULT_PROGS = ('bin/bootblock.bin', 'bin/main_512k.bin', 'bin/main_1mb.bin')


if __name__ == '__main__':
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.add_argument('-o', '--out', default='gng.adf')
    ap.add_argument('--boot', help='bootblock (1,024 bytes); its checksum is recomputed')
    for k, t in ALIASES.items(): ap.add_argument('--'+k, help=f'the file at track {t}')
    ap.add_argument('--file', action='append', default=[], metavar='TRACK=PATH',
                    help='replace the file starting at TRACK (or a disk/files name)')
    ap.add_argument('--add', action='append', default=[], metavar='TRACK=PATH',
                    help='add a file no table lists (for example a module a patched program loads)')
    ap.add_argument('--raw', metavar='DIR', help="also write each track's raw MFM to DIR")
    ap.add_argument('--layout', action='store_true', help='print the layout read from the binaries')
    ap.add_argument('--check', metavar='ADF', help='decode an image and compare it with bin/tracks')
    ap.add_argument('--compare-raw', metavar='DIR', help='compare the MFM with raw track dumps')
    a = ap.parse_args()
    if a.check: sys.exit(0 if check(a.check) else 1)
    if a.compare_raw: sys.exit(0 if compare_raw(a.compare_raw) else 1)
    files = {}
    for k, t in ALIASES.items():
        if getattr(a, k): files[t] = getattr(a, k)
    for f in a.file:
        key, path = f.split('=', 1)
        m = re.match(r't?(\d+)', os.path.basename(key))
        if not m: sys.exit(f'--file {f}: give the first track or a disk/files name')
        files[int(m.group(1))] = path
    extra = []
    for f in a.add:
        key, path = f.split('=', 1)
        t = int(key)
        if not 0 < t < NTRACKS: sys.exit(f'--add {f}: track out of range')
        files[t] = path; extra.append((t, os.path.getsize(path)))
    boot = open(a.boot or DEFAULT_PROGS[0], 'rb').read()
    assert len(boot) == 1024, 'the bootblock is 1,024 bytes'
    lay = layout(boot, open(files.get(110, DEFAULT_PROGS[1]), 'rb').read(),
                 open(files.get(17, DEFAULT_PROGS[2]), 'rb').read(), extra)
    if a.layout:
        print('track   tracks  bytes     file / loaded by')
        for t, (ln, who) in sorted(lay.items()):
            n = ntracks(ln)
            print(f'{t:5d}  {t:3d}-{t+n-1:<3d} {ln:8,d}  {os.path.basename(files.get(t) or source_file(t) or "?")}')
            for w in who: print(f'{"":26}{w}')
        sys.exit(0)
    for t in files:
        if t not in lay: sys.exit(f'no file starts at track {t}; see --layout')
    if a.raw: os.makedirs(a.raw, exist_ok=True)
    img = build(files, boot, lay, a.raw)
    open(a.out, 'wb').write(img)
    h = hashlib.sha1(img).hexdigest()
    print(f'{a.out}: {len(img):,} bytes, {NTRACKS} tracks, SHA-1 {h}'
          + (' (the original disk)' if h == ORIGINAL_SHA1 else ''))
