"""A minimal Amiga for testing display code: the 68000 (Unicorn, via tools/verify/emu.py) plus
the parts of the custom chips the playfield needs - the blitter (area mode, run instantly when
BLTSIZE is written), the copper lists (interpreted per display line) and the bitplane display
(5 planes, lores, BPLCON1 fine scroll), rendered to an image.

Not emulated: timing, sprites, audio, interrupts, line / fill mode."""
import os, struct, sys
import numpy as np
import re
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, '..', '..')
sys.path.insert(0, os.path.join(ROOT, 'tools', 'verify'))
from emu import Game, GLOBALS                                  # noqa: E402
from unicorn import UC_HOOK_MEM_WRITE, UC_HOOK_CODE              # noqa: E402

CUSTOM = 0xDFF000
COPPER_INIT, LEVEL_FILE, WORLDMAP, GAMEPALETTE = 0x1A118, 0x65548, 0x44D6, 0x4FB0
FILES = os.path.join(ROOT, 'disk', 'files')


def minterm(mt, a, b, c):
    d = 0
    for i in range(8):
        if mt >> i & 1:
            d |= (a if i & 4 else ~a) & (b if i & 2 else ~b) & (c if i & 1 else ~c)
    return d & 0xFFFF


class Amiga(Game):
    def __init__(self, binfile=None, extra_mem=False):
        super().__init__(binfile)
        self.blits = 0; self.blit_words = 0
        self.u.hook_add(UC_HOOK_MEM_WRITE, self._custom_write, begin=CUSTOM+0x58, end=CUSTOM+0x59)
        self.w16(CUSTOM+0x1E, 0x0010)          # INTREQR: copper interrupt always pending
        self.w16(CUSTOM+0x02, 0)               # DMACONR: blitter never busy

    # ---- memory helpers
    def rd(self, a, n): return bytes(self.u.mem_read(a, n))
    def custom16(self, reg): return self.r16(CUSTOM+reg)
    def custom32(self, reg): return self.r32(CUSTOM+reg)

    # ---- blitter
    def _custom_write(self, uc, access, addr, size, value, ud):
        if addr == CUSTOM+0x58:
            self.blit(value & 0xFFFF)

    def blit(self, size):
        con0, con1 = self.custom16(0x40), self.custom16(0x42)
        if con1 & 1: raise RuntimeError('line mode not emulated')
        h = size >> 6 or 1024; w = size & 63 or 64
        use = con0 >> 8 & 15
        ash, bsh, mt = con0 >> 12, con1 >> 12, con0 & 0xFF
        desc = bool(con1 & 2)
        fwm, lwm = self.custom16(0x44), self.custom16(0x46)
        ptr = {k: self.custom32(r) & 0x1FFFFE for k, r in (('c', 0x48), ('b', 0x4C), ('a', 0x50), ('d', 0x54))}
        mod = {k: struct.unpack('>h', struct.pack('>H', self.custom16(r)))[0]
               for k, r in (('c', 0x60), ('b', 0x62), ('a', 0x64), ('d', 0x66))}
        adat, bdat, cdat = self.custom16(0x74), self.custom16(0x72), self.custom16(0x70)
        step = -2 if desc else 2
        olda = oldb = 0
        for y in range(h):
            for x in range(w):
                a = self.r16(ptr['a']) if use & 8 else adat
                if x == 0: a &= fwm
                if x == w-1: a &= lwm
                b = self.r16(ptr['b']) if use & 4 else bdat
                c = self.r16(ptr['c']) if use & 2 else cdat
                if desc:
                    sa = ((a << ash) | (olda >> (16-ash))) & 0xFFFF if ash else a
                    sb = ((b << bsh) | (oldb >> (16-bsh))) & 0xFFFF if bsh else b
                else:
                    sa = (((olda << 16) | a) >> ash) & 0xFFFF
                    sb = (((oldb << 16) | b) >> bsh) & 0xFFFF
                olda, oldb = a, b
                d = minterm(mt, sa, sb, c)
                if use & 1: self.w16(ptr['d'], d)
                for k, bit in (('a', 8), ('b', 4), ('c', 2), ('d', 1)):
                    if use & bit: ptr[k] += step
            for k, bit in (('a', 8), ('b', 4), ('c', 2), ('d', 1)):
                if use & bit: ptr[k] += -mod[k] if desc else mod[k]
        self.blits += 1; self.blit_words += w*h

    # ---- file loading: LoadFile copies the file straight from disk/files
    def stub_loadfile(self, addr=0xC476):
        from unicorn.m68k_const import UC_M68K_REG_PC
        names = {int(f[1:4]): f for f in os.listdir(FILES) if f[0] == 't' and f[1:4].isdigit()}
        def hook(uc, a, sz, ud):
            a1 = self.reg('a1')
            dest, length, track = self.r32(a1), self.r32(a1+4), self.r16(a1+8)
            data = open(os.path.join(FILES, names[track]), 'rb').read()[:length]
            self.u.mem_write(dest, data)
            self.reg('a5', dest+len(data))
            sp = self.reg('a7'); ret = self.r32(sp); self.reg('a7', sp+4)
            uc.reg_write(UC_M68K_REG_PC, ret)
        self.u.hook_add(UC_HOOK_CODE, hook, begin=addr, end=addr)

    # ---- display
    def copper_lines(self):
        """Run COP1 from COPPER_INIT (and COP2 after a COPJMP2) and return its register writes
        as (beam line, register, value), in order."""
        events = []
        pc = COPPER_INIT; line = 0; high = 0
        for _ in range(4000):
            w1, w2 = self.r16(pc), self.r16(pc+2); pc += 4
            if w1 & 1:                                   # WAIT (or SKIP)
                if (w1, w2) == (0xFFFF, 0xFFFE): break
                vp = w1 >> 8
                if vp == 0xFF: line, high = 0xFF, 0x100; continue    # the PAL wrap
                line = max(line, high | vp); continue
            reg = w1 & 0x1FE
            if reg == 0x8A: pc = self.custom32(0x84); continue        # COPJMP2
            if reg == 0x88: pc = self.custom32(0x80); continue        # COPJMP1
            events.append((line, reg, w2))
        return events

    def render(self, top=0x34, lines=240, width=256, ddf_words=17):
        """The displayed playfield as an array of colour indices (lines x width)."""
        ev = self.copper_lines()
        regs = {}
        ptr = [0]*5
        out = np.zeros((lines, width), dtype=np.uint8)
        ei = 0
        bpl1mod, bpl2mod = self.custom16(0x108), self.custom16(0x10A)
        for v in range(0, top+lines):
            while ei < len(ev) and ev[ei][0] <= v:
                _, reg, val = ev[ei]; ei += 1
                if 0xE0 <= reg < 0xF4:
                    p = (reg-0xE0) // 4
                    if reg & 2: ptr[p] = (ptr[p] & 0xFFFF0000) | val
                    else: ptr[p] = (ptr[p] & 0xFFFF) | (val << 16)
                elif reg == 0x108: bpl1mod = val
                elif reg == 0x10A: bpl2mod = val
                else: regs[reg] = val
            if v < top: continue
            con1 = regs.get(0x102, 0)
            y = v-top
            for p in range(5):
                data = self.rd(ptr[p], 2*ddf_words)
                bits = np.unpackbits(np.frombuffer(data, dtype=np.uint8))
                delay = (con1 & 15) if p % 2 == 0 else (con1 >> 4 & 15)
                seg = bits[16-delay:16-delay+width]
                out[y, :len(seg)] |= (seg.astype(np.uint8) << p)
                m = bpl1mod if p % 2 == 0 else bpl2mod
                m = m-0x10000 if m & 0x8000 else m
                ptr[p] += 2*ddf_words + m
        return out

    def palette(self):
        return [self.r16(GAMEPALETTE+2*i) for i in range(32)]

    def save_png(self, img, path):
        from PIL import Image
        pal = self.palette()
        rgb = np.array([((c >> 8 & 15)*17, (c >> 4 & 15)*17, (c & 15)*17) for c in pal], dtype=np.uint8)
        Image.fromarray(rgb[img]).save(path)


def equates(path=os.path.join(ROOT, 'gng_equates.i')):
    """name -> value for every equate in an equates file"""
    out = {}
    for l in open(path):
        m = re.match(r'^(\w+)\s+equ\s+\$?([0-9A-Fa-f]+)', l)
        if m: out[m.group(1)] = int(m.group(2), 16)
    return out
