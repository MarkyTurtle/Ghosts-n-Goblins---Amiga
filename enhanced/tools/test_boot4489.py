"""Boot the one program's disk (build_game.py: enhanced/build/gng_game.adf) in the emulator:
its bootblock (src/boot_4489.s) from Kickstart's call to the program's entry ($A0), with the
4489_byteloader reading the disk through tools/floppy.py. Checks: the program at $80 and the
loading picture at $60000 as on the disk, $4.w = $80, the machine description (version 2: with
the drive booted from), the loading picture's display (copper lists, the level 3 vector, DMA),
and that the drive was left off.

The bootblock finds the drive it was booted from by opening trackdisk.device's units and
comparing each with the boot IORequest's unit; here exec's OpenDevice is a stub (a Python hook)
that knows the drives connected. Cases: booted from DF0, DF1 and DF3 (the disk in that drive,
the others empty), and from a unit that is none of them (DF0 then).

  python3 test_boot4489.py [--random-start]      (the DMA starting at any sector)"""
import os, struct, sys
from unicorn import Uc, UC_ARCH_M68K, UC_MODE_BIG_ENDIAN, UC_HOOK_MEM_READ, UC_HOOK_CODE
from unicorn.m68k_const import (UC_CPU_M68K_M68000, UC_M68K_REG_A0, UC_M68K_REG_A1, UC_M68K_REG_A6, UC_M68K_REG_A7,
                                UC_M68K_REG_D0, UC_M68K_REG_SR, UC_M68K_REG_PC)
import build_game, floppy, test_bootinfo

EXEC, BOOTBUF = 0x676, 0x20000
OPENDEVICE = 0x1000                     # exec's OpenDevice (EXEC - $1BC jumps here): a hook, then rts
DEVICE, NAME, BOOTREQ = 0x1100, 0x1200, 0x1300
UNITS = [0x1400 + 0x40 * n for n in range(4)]     # trackdisk's unit structures, DF0-DF3
FOREIGN = 0x1600                        # a unit of some other device


class Machine:
    def __init__(self):
        u = self.u = Uc(UC_ARCH_M68K, UC_MODE_BIG_ENDIAN)
        u.ctl_set_cpu_model(UC_CPU_M68K_M68000)
        u.mem_map(0, 0x80000); u.mem_map(0xBFD000, 0x2000); u.mem_map(0xDFF000, 0x1000)
    def r8(self, a): return self.u.mem_read(a, 1)[0]
    def r16(self, a): return struct.unpack('>H', bytes(self.u.mem_read(a, 2)))[0]
    def r32(self, a): return struct.unpack('>L', bytes(self.u.mem_read(a, 4)))[0]
    def w8(self, a, v): self.u.mem_write(a, bytes([v & 0xFF]))
    def w16(self, a, v): self.u.mem_write(a, struct.pack('>H', v & 0xFFFF))
    def w32(self, a, v): self.u.mem_write(a, struct.pack('>L', v & 0xFFFFFFFF))


def boot(unit=0, drives=(0, 1), random_start=False, foreign=False):
    """unit: the drive with the disk, booted from; drives: those connected; foreign: the boot
    IORequest's unit is none of trackdisk's (the bootblock should then use DF0)"""
    adf = open(os.path.join(build_game.OUT, '..', 'gng_game.adf'), 'rb').read()
    m = Machine(); u = m.u
    name, regions, vblank, attn = test_bootinfo.MACHINES[0]          # an A500 with 512K
    w = lambda a, f, *v: u.mem_write(a, struct.pack(f, *v))
    w(EXEC + 0x128, '>H', attn); w(EXEC + 0x212, '>B', vblank)
    lst = EXEC + 0x142
    headers = [start for _, start, _ in regions]
    for i, (attr, start, end) in enumerate(regions):
        succ = headers[i + 1] if i + 1 < len(regions) else lst + 4
        pred = headers[i - 1] if i else lst
        w(start, '>LLBBLHLLLL', succ, pred, 10, 0, 0, attr, start + 0x20, start + 0x20, end, end - start - 0x20)
    w(lst, '>LLL', headers[0], 0, headers[-1])
    u.mem_write(BOOTBUF, adf[:1024])
    # exec's OpenDevice, trackdisk.device and the boot IORequest
    w(EXEC - 0x1BC, '>HL', 0x4EF9, OPENDEVICE)                 # jmp OPENDEVICE
    w(OPENDEVICE, '>H', 0x4E75)                                  # rts
    opened = []
    def opendevice(uc, addr, size, ud):
        n, req = u.reg_read(UC_M68K_REG_D0), u.reg_read(UC_M68K_REG_A1)
        name = bytes(u.mem_read(u.reg_read(UC_M68K_REG_A0), 17))
        good = name == b'trackdisk.device\0' and n in drives
        opened.append(n)
        if good: w(req + 0x14, '>LL', DEVICE, UNITS[n])
        w(req + 0x1F, '>B', 0 if good else 32)                  # io_Error (TDERR_BadUnitNum)
        u.reg_write(UC_M68K_REG_D0, 0 if good else 32)
    u.hook_add(UC_HOOK_CODE, opendevice, begin=OPENDEVICE, end=OPENDEVICE)
    w(DEVICE + 10, '>L', NAME); u.mem_write(NAME, b'trackdisk.device\0')
    w(BOOTREQ + 0x14, '>LL', DEVICE, FOREIGN if foreign else UNITS[unit])
    u.reg_write(UC_M68K_REG_A1, BOOTREQ)
    m.w8(0xBFE001, 0xFF)
    def vertb(uc, acc, addr, size, value, ud):        # a vertical blank is always pending
        m.w16(0xDFF01E, m.r16(0xDFF01E) | 0x0020)
    u.hook_add(UC_HOOK_MEM_READ, vertb, begin=0xDFF01E, end=0xDFF01F)
    fd = floppy.Floppy(m, adf, timing_ranges=[(0x7FB20, 0x80000)], random_start=random_start, unit=unit)
    u.reg_write(UC_M68K_REG_A6, EXEC)
    u.reg_write(UC_M68K_REG_SR, 0x2700)
    u.reg_write(UC_M68K_REG_A7, 0x7F000)
    u.emu_start(BOOTBUF + 0x0C, 0xA0, count=400_000_000)
    pc = u.reg_read(UC_M68K_REG_PC)
    # the checks
    ft = struct.unpack_from('>4sHH', adf, 0x400)
    entry = lambda i: struct.unpack_from('>LL', adf, 0x410 + 8 * i)
    po, pl = entry(0); lo, ll = entry(1)
    checks = [('at the program entry ($A0)', pc == 0xA0),
              ('the file table', ft[0] == b'GNGF'),
              ('the program at $80', bytes(u.mem_read(0x80, pl)) == adf[po:po + pl]),
              ('the loading picture at $60000', bytes(u.mem_read(0x60000, ll)) == adf[lo:lo + ll]),
              ('$4.w = $80', m.r32(4) == 0x80),
              (f'the machine description, the drive DF{unit}', bytes(u.mem_read(0x7FB00, 36)) == expected(regions, vblank, attn, unit)),
              (f'units opened: {opened}', opened[0] == 3 and opened[-1] == (0 if foreign else unit)),
              ('the copper lists in the loader', 0x7FB20 <= m.r32(0xDFF080) < 0x80000 and 0x7FB20 <= m.r32(0xDFF084) < 0x80000),
              ('the level 3 vector', 0x7FB20 <= m.r32(0x6C) < 0x80000),
              ('BPLCON0 HAM interlaced', m.r16(0xDFF100) == 0x6804),
              (f'the motor off and DF{unit} deselected', not fd.motor or not fd.sel)]
    print(f'DF{unit} ({"booted from a unit of another device" if foreign else "booted from"}; drives {list(drives)}): '
          f'{fd.reads} track reads (random start: {random_start}), head at cylinder {fd.cyl}')
    ok = True
    for what, good in checks:
        print(f'  {"ok  " if good else "FAIL"} {what}'); ok &= good
    return ok


def expected(regions, vblank, attn, unit):
    """the bootblock's machine description, version 2: test_bootinfo's (version 1) and the drive"""
    v1 = test_bootinfo.expected(regions, vblank, attn)
    return v1[:4] + bytes([2]) + v1[5:] + struct.pack('>L', unit)


def main():
    rs = '--random-start' in sys.argv
    ok = True
    for unit, drives, foreign in ((0, (0, 1), False), (1, (0, 1), False), (3, (0, 1, 2, 3), False), (0, (0, 1), True)):
        ok &= boot(unit, drives, rs, foreign)
    print('all as expected' if ok else 'FAILED')
    return ok


if __name__ == '__main__':
    sys.exit(0 if main() else 1)
