"""Run pieces of the real Ghosts'n Goblins main program (512K build) in a 68000 emulator
(Unicorn) to check what the annotations claim. The program is loaded at $80 as the
bootblock does; a6 points at the globals block (GLOBALS, $1898C). Routines are called
with a sentinel return address, or a code range is run from one address to another.
Sound calls go through vector $60, which points at an RTS here."""
import struct, os, sys
from unicorn import Uc, UC_ARCH_M68K, UC_MODE_BIG_ENDIAN
from unicorn.m68k_const import *

HERE = os.path.dirname(os.path.abspath(__file__))
GLOBALS = 0x1898C
RET = 0x7FFF0; STACK = 0x7FF00; RTS_STUB = 0x7FFE0
REG = {**{f'd{i}': globals()[f'UC_M68K_REG_D{i}'] for i in range(8)},
       **{f'a{i}': globals()[f'UC_M68K_REG_A{i}'] for i in range(8)}}

class Game:
    def __init__(self, binfile=None):
        binfile = binfile or os.environ.get('GNG_BIN', os.path.join(HERE, '..', '..', 'bin', 'main_512k.bin'))
        u = self.u = Uc(UC_ARCH_M68K, UC_MODE_BIG_ENDIAN)
        try: u.ctl_set_cpu_model(UC_CPU_M68K_M68000)
        except Exception: pass
        u.mem_map(0, 0x80000); u.mem_map(0xdff000, 0x1000); u.mem_map(0xbfd000, 0x2000)
        u.mem_write(0x80, open(binfile, 'rb').read())
        u.mem_write(RTS_STUB, b'\x4e\x75')
        u.mem_write(0x60, struct.pack('>I', RTS_STUB))           # sound driver vector
        u.mem_write(0xbfe001, b'\xff')                           # fire not pressed
        u.mem_write(GLOBALS, bytes(0x1000))
        self.reg('a6', GLOBALS)
    # registers / memory
    def reg(self, r, v=None):
        if v is None:
            return self.u.reg_read(REG[r])
        self.u.reg_write(REG[r], v & 0xFFFFFFFF)
    def w8(self, a, v): self.u.mem_write(a, struct.pack('>B', v & 0xFF))
    def w16(self, a, v): self.u.mem_write(a, struct.pack('>H', v & 0xFFFF))
    def w32(self, a, v): self.u.mem_write(a, struct.pack('>I', v & 0xFFFFFFFF))
    def r8(self, a): return self.u.mem_read(a, 1)[0]
    def s8(self, a): v = self.r8(a); return v-256 if v > 127 else v
    def r16(self, a): return struct.unpack('>H', bytes(self.u.mem_read(a, 2)))[0]
    def s16(self, a): return struct.unpack('>h', bytes(self.u.mem_read(a, 2)))[0]
    def r32(self, a): return struct.unpack('>I', bytes(self.u.mem_read(a, 4)))[0]
    def g(self, off): return GLOBALS+off
    # execution
    def call(self, addr, count=2000000, **regs):
        for r, v in regs.items(): self.reg(r, v)
        self.reg('a6', GLOBALS)
        self.w32(STACK-4, RET); self.reg('a7', STACK-4)
        self.u.emu_start(addr, RET, count=count)
    def run(self, start, stop, count=200000, **regs):
        for r, v in regs.items(): self.reg(r, v)
        self.reg('a6', GLOBALS)
        if self.reg('a7') == 0: self.reg('a7', STACK)
        self.u.emu_start(start, stop, count=count)
