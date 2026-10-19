"""Test the enhanced bootblock's memory survey (src/boot_patches.s) in the emulator.

The bootblock (build/boot/boot.bin) is run from its entry ($0C) up to the instruction after
the call (its first original instruction, at $12) with a6 pointing at a fake ExecBase whose
memory list describes a machine: chip RAM, slow RAM at $C00000, fast RAM. The machine block
it leaves at MACHINE_INFO ($7FB00) is checked against what the machine has.

  python3 test_bootinfo.py"""
import os, struct, sys
from unicorn import Uc, UC_ARCH_M68K, UC_MODE_BIG_ENDIAN
from unicorn.m68k_const import UC_CPU_M68K_M68000, UC_M68K_REG_A0, UC_M68K_REG_A6, UC_M68K_REG_A7, UC_M68K_REG_SR

HERE = os.path.dirname(os.path.abspath(__file__))
BOOT = os.path.join(HERE, '..', 'build', 'boot', 'boot.bin')
MACHINE_INFO = 0x7FB00
EXEC, BOOTBUF = 0x676, 0x20000          # where Kickstart 1.3 has ExecBase; a boot buffer
MEMF_PUBLIC, MEMF_CHIP, MEMF_FAST = 1, 2, 4

# (name, [(attributes, start, end)] in the order exec lists them (fast first, as AddMemList
# adds them with a higher priority), VBlankFrequency, AttnFlags)
MACHINES = [
    ('A500 512K chip', [(MEMF_PUBLIC | MEMF_CHIP, 0x400, 0x80000)], 50, 0),
    ('A500 512K chip + 512K slow', [(MEMF_PUBLIC | MEMF_FAST, 0xC00000, 0xC80000),
                                   (MEMF_PUBLIC | MEMF_CHIP, 0x400, 0x80000)], 50, 0),
    ('A500+ 1MB chip', [(MEMF_PUBLIC | MEMF_CHIP, 0x400, 0x100000)], 50, 0),
    # Kickstart 1.3 on a 1MB-chip A500 (ECS Agnus) keeps the top of chip RAM: it lists $FE800
    ('A500 1MB chip, Kickstart 1.3', [(MEMF_PUBLIC | MEMF_CHIP, 0x400, 0xFE800)], 50, 0),
    ('1MB chip + 512K slow (NTSC)', [(MEMF_PUBLIC | MEMF_FAST, 0xC00000, 0xC80000),
                                     (MEMF_PUBLIC | MEMF_CHIP, 0x400, 0x100000)], 60, 0),
    ('A1200 2MB chip + 4MB fast', [(MEMF_PUBLIC | MEMF_FAST, 0x200000, 0x600000),
                                   (MEMF_PUBLIC | MEMF_CHIP, 0x400, 0x200000)], 50, 0x0003),
    ('A500 + 1.5MB slow + 2MB fast', [(MEMF_PUBLIC | MEMF_FAST, 0x200000, 0x400000),
                                      (MEMF_PUBLIC | MEMF_FAST, 0xC00000, 0xD80000),
                                      (MEMF_PUBLIC | MEMF_CHIP, 0x400, 0x80000)], 50, 0),
]


def run(regions, vblank, attn):
    u = Uc(UC_ARCH_M68K, UC_MODE_BIG_ENDIAN)
    u.ctl_set_cpu_model(UC_CPU_M68K_M68000)
    u.mem_map(0, 0x1000000)                       # 16MB: chip, slow, fast all addressable
    u.mem_write(MACHINE_INFO, b'\xA5' * 64)       # garbage, to check the block is cleared
    u.mem_write(BOOTBUF, open(BOOT, 'rb').read())
    w = lambda a, f, *v: u.mem_write(a, struct.pack(f, *v))
    w(EXEC + 0x128, '>H', attn)
    w(EXEC + 0x212, '>B', vblank)
    lst = EXEC + 0x142                            # struct List: lh_Head, lh_Tail (0), lh_TailPred
    headers = [start for _, start, _ in regions]  # a MemHeader sits at the start of its region
    for i, (attr, start, end) in enumerate(regions):
        succ = headers[i + 1] if i + 1 < len(regions) else lst + 4
        pred = headers[i - 1] if i else lst
        w(start, '>LLBBLHLLLL', succ, pred, 10, 0, 0, attr, start + 0x20, start + 0x20, end, end - start - 0x20)
    w(lst, '>LLL', headers[0], 0, headers[-1])
    u.reg_write(UC_M68K_REG_A6, EXEC)
    u.reg_write(UC_M68K_REG_SR, 0x2700)                # (supervisor first: it selects the stack)
    u.reg_write(UC_M68K_REG_A7, 0x7F000)
    u.emu_start(BOOTBUF + 0x0C, BOOTBUF + 0x12, count=10000)
    assert u.reg_read(UC_M68K_REG_A0) == 0xDFF000, 'a0 must be $DFF000 after the call, as before'
    return bytes(u.mem_read(MACHINE_INFO, 32))


def expected(regions, vblank, attn):
    chip = slow = fast = (0, 0)
    for attr, start, end in regions:
        r = (start + 0x20, end)
        if attr & MEMF_CHIP: chip = r
        elif 0xC00000 <= start + 0x20 < 0xDC0000: slow = r
        else: fast = r
    return b'GNGM' + struct.pack('>BBH6L', 1, vblank, attn, *chip, *slow, *fast)


def describe(info):
    magic, ver, vb, attn, cl, cu, sl, su, fl, fu = struct.unpack('>4sBBH6L', info)
    kb = lambda lo, hi: (hi - (lo & ~0xFFFF)) // 1024 if hi else 0
    return (f'{magic.decode()} v{ver} {vb} Hz, AttnFlags ${attn:04X}: chip {kb(cl, cu)}K'
            f', slow {kb(sl, su)}K' + (f' at ${sl & ~0xFFFF:X}' if su else '')
            + f', fast {kb(fl, fu)}K' + (f' at ${fl & ~0xFFFF:X}' if fu else ''))


def main():
    bad = 0
    for name, regions, vb, attn in MACHINES:
        got, want = run(regions, vb, attn), expected(regions, vb, attn)
        ok = got == want
        bad += not ok
        print(f'{"ok " if ok else "BAD"} {name:32} {describe(got)}')
        if not ok: print(f'    expected {describe(want)}')
    print(f'{len(MACHINES) - bad} of {len(MACHINES)} machines described correctly')
    return 1 if bad else 0


if __name__ == '__main__':
    sys.exit(main())
