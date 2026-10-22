"""A floppy drive (DF0, or DF1-DF3: unit) with an AmigaDOS-format disk (ADF) for the Unicorn
harness, enough for the 4489_byteloader (src/byteloader.i): the drive lines on the CIAs, disk
DMA, the DSKBLK interrupt request, and VHPOSR moving while the loader times itself.

  CIA-B PRB ($BFD100), written: /MTR (bit 7, latched when the drive's /SELn goes low), /SEL0-3
      (bits 3-6: the drive answers to its own; the other drives are empty),
      /SIDE (bit 2: 0 = upper head), DIR (bit 1: 1 = out, towards cylinder 0), /STEP (bit 0:
      a step when it goes low)
  CIA-A PRA ($BFE001), read: /RDY (bit 5: the motor is on), /TRK0 (bit 4), /WPRO (bit 3),
      /CHNG (bit 2); bits 7-6 (the fire buttons) and 1-0 are left as they are
  DSKLEN ($DFF024): two writes with bit 15 start the DMA: the track's MFM words, from the word
      after a $4489 (WORDSYNC), to DSKPT ($DFF020); then DSKBLK (bit 1) in INTREQR ($DFF01E)
  INTREQ ($DFF09C): clearing bit 1 clears it in INTREQR
  VHPOSR ($DFF006): moves on at every read while the PC is in one of the given ranges (the
      loader's waits count changes of its high byte)

The track is written as a disk is: sectors 0-10 after the gap (each: $AAAA $AAAA $4489 $4489,
info and label, header and data checksums, 512 data bytes; odd bits then even bits, with the
MFM clock bits). The DMA starts at sector 0, or (random_start) at a random sector, as a real
drive would: the byteloader reads again until it starts at sector 0."""
import random, struct
from unicorn import UC_HOOK_MEM_WRITE, UC_HOOK_MEM_READ
from unicorn.m68k_const import UC_M68K_REG_PC

SECTOR_WORDS, GAP_WORDS = 544, 400


def _longs_oddeven(longs):
    """data longs -> words: all odd halves, then all even halves (data bits only)"""
    odd = [(v >> 1) & 0x55555555 for v in longs]
    even = [v & 0x55555555 for v in longs]
    w = []
    for v in odd + even: w += [v >> 16, v & 0xFFFF]
    return w


def sector_words(track, sector, data):
    info = 0xFF000000 | track << 16 | sector << 8 | (11 - sector)
    info_w = _longs_oddeven([info])
    label_w = _longs_oddeven([0, 0, 0, 0])
    data_l = list(struct.unpack('>128L', data))
    data_w = _longs_oddeven(data_l)
    def xor(ws):
        x = 0
        for i in range(0, len(ws), 2): x ^= ws[i] << 16 | ws[i + 1]
        return x & 0x55555555
    hsum, dsum = xor(info_w + label_w), xor(data_w)
    body = info_w + label_w + _longs_oddeven([hsum]) + _longs_oddeven([dsum]) + data_w
    # $AAAA $AAAA $4489 $4489 are raw (the sync breaks the clock rule); the rest is encoded,
    # following on from the last sync word (which ends in a 1)
    enc = _clock_from(body, 1)
    return [0xAAAA, 0xAAAA, 0x4489, 0x4489] + enc


def _clock_from(words, prev):
    """MFM: a clock bit (odd positions) between two zero data bits; words: 16-bit words with the
    data in the even bit positions, one bit stream; prev: the bit before the first"""
    out = []
    for w in words:
        d = w & 0x5555
        v = d
        for b in range(15, -1, -2):
            left = prev if b == 15 else (d >> (b + 1)) & 1
            right = (d >> (b - 1)) & 1
            if not left and not right: v |= 1 << b
        out.append(v); prev = v & 1
    return out


class Floppy:
    def __init__(self, owner, adf, timing_ranges=(), random_start=False, seed=1, unit=0):
        self.m, self.u = owner, owner.u
        self.unit = unit                       # the drive: DF0-DF3 (/SELn = bit 3 + n)
        self.adf = adf
        self.cyl, self.side, self.sel, self.motor, self.prb = 0, 0, False, False, 0xFF
        self.ranges = list(timing_ranges)
        self.random_start, self.rnd = random_start, random.Random(seed)
        self.armed = False
        self.vpos = 0
        self.reads = 0                         # DMA reads done (tracks)
        self.cache = {}
        u = self.u
        u.hook_add(UC_HOOK_MEM_WRITE, self._prb, begin=0xBFD100, end=0xBFD100)
        u.hook_add(UC_HOOK_MEM_READ, self._pra, begin=0xBFE001, end=0xBFE001)
        u.hook_add(UC_HOOK_MEM_WRITE, self._dsklen, begin=0xDFF024, end=0xDFF025)
        u.hook_add(UC_HOOK_MEM_WRITE, self._intreq, begin=0xDFF09C, end=0xDFF09F)
        u.hook_add(UC_HOOK_MEM_READ, self._vhpos, begin=0xDFF006, end=0xDFF007)

    # ---- the track as MFM words
    def track(self, t):
        if t not in self.cache:
            w = []
            for s in range(11):
                off = (t * 11 + s) * 512
                w += sector_words(t, s, self.adf[off:off + 512])
            self.cache[t] = w + [0xAAAA] * GAP_WORDS
        return self.cache[t]

    # ---- hooks
    def _prb(self, uc, acc, addr, size, value, ud):
        v = value & 0xFF
        sel = not v & (0x08 << self.unit)
        if sel and not self.sel: self.motor = not v & 0x80      # latched as the drive is selected
        if sel and self.prb & 0x01 and not v & 0x01:           # /STEP goes low
            self.cyl = max(0, self.cyl - 1) if v & 0x02 else min(79, self.cyl + 1)
        self.sel, self.side, self.prb = sel, 0 if v & 0x04 else 1, v

    def _pra(self, uc, acc, addr, size, value, ud):
        cur = self.m.r8(0xBFE001)
        st = 0x3C
        if self.sel and self.motor: st &= ~0x20
        if self.sel and self.cyl == 0: st &= ~0x10
        self.m.w8(0xBFE001, (cur & 0xC3) | st)

    def _dsklen(self, uc, acc, addr, size, value, ud):
        v = value & 0xFFFF
        if not v & 0x8000: self.armed = False; return
        if not self.armed: self.armed = True; return
        self.armed = False
        if not (self.sel and self.motor):                    # another drive (empty), or ours
            return                                           # not spinning: no data, no DSKBLK
        n, ptr = v & 0x3FFF, self.m.r32(0xDFF020) & 0x1FFFFE
        w = self.track(self.cyl * 2 + self.side)
        s = self.rnd.randrange(11) if self.random_start else 0
        start = s * SECTOR_WORDS + 3                         # after the first $4489
        out = [w[(start + i) % len(w)] for i in range(n)]
        self.u.mem_write(ptr, struct.pack(f'>{n}H', *out))
        self.m.w16(0xDFF01E, self.m.r16(0xDFF01E) | 0x0002)  # DSKBLK
        self.reads += 1

    def _intreq(self, uc, acc, addr, size, value, ud):
        if addr == 0xDFF09C:
            v = (value >> 16 if size == 4 else value) & 0xFFFF
            if not v & 0x8000 and v & 0x0002:
                self.m.w16(0xDFF01E, self.m.r16(0xDFF01E) & ~0x0002)

    def _vhpos(self, uc, acc, addr, size, value, ud):
        pc = uc.reg_read(UC_M68K_REG_PC)
        if any(a <= pc < b for a, b in self.ranges):
            self.vpos = (self.vpos + 0x100) & 0xFFFF         # (a line a read: the high byte moves)
            self.m.w16(0xDFF006, self.vpos)
