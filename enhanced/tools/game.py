"""Run the whole game - original or enhanced - in the emulator, frame by frame.

The program is loaded as the bootblock does; Start runs (the copyright wait is skipped),
then each frame is what the hardware would do: the vertical-blank interrupt (VblIRQ), then,
if it asked for one, the level-1 interrupt (Level1Logic, the game's main loop). When VblIRQ
diverts user mode to RedrawEntry (a background redraw), that runs to its end before the
next frame. Input: the joystick and fire button through the registers VblIRQ reads.

Not emulated: real timing (a frame's work always finishes within the frame), the disk
(LoadFile copies the files from disk/files), audio output, the keyboard interrupt."""
import os, re, struct
from unicorn import UC_HOOK_CODE, UC_HOOK_MEM_WRITE
from unicorn.m68k_const import UC_M68K_REG_PC, UC_M68K_REG_SR
from amiga import Amiga, CUSTOM, FILES, GLOBALS, equates

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, '..', '..')
BUILD = os.path.join(HERE, '..', 'build')
JOY = {'': 0, 'R': 0x0003, 'L': 0x0300, 'U': 0x0100, 'D': 0x0001,
       'UR': 0x0102, 'UL': 0x0200, 'DR': 0x0002, 'DL': 0x0301}

# per build: where the program goes, the globals, the files that describe it
BUILDS = {
    '512k': dict(base=0, load=0x80, globals=GLOBALS, ssp=0x80000, equates='gng_equates.i',
                 src='gng_main.s', orig='bin/main_512k.bin'),
    # the 1MB program as on a machine with 1MB of chip RAM: the bootblock loads it to $80000
    # ($4.w), the stack starts at $100000; its labels are offsets from the load address
    '1mb': dict(base=0x80000, load=0x80000, globals=0x80000+0x1893A, ssp=0x100000,
                equates='gng_equates.i', src='gng_main.s', orig='bin/main_1mb.bin'),
}
EQ = equates()
G = {k: GLOBALS+v for k, v in EQ.items() if k.startswith('g_')}      # (512K; GameRun.G per build)


def labels(build, listing=None):
    """label -> address in memory, from the listing build_enh.py made of the original source
    (or the given listing)"""
    cfg = BUILDS[build]
    text = open(listing or os.path.join(BUILD, build, 'orig_main.lst')).read()
    part = text[text.index('Symbols by name:'):text.index('Symbols by value:')]
    return {m.group(1): cfg['base'] + int(m.group(2), 16)
            for m in re.finditer(r'^(\S+)\s+A:([0-9A-F]+)$', part, re.M)}


def copyright_wait(build):
    """the label of Start's loop that waits 500 VBLs on the copyright screen"""
    lines = open(os.path.join(ROOT, BUILDS[build]['src'])).read().split('\n')
    for i, l in enumerate(lines):
        if re.match(r'\s+cmpi\.w\s+#\$1f4,g_VblCount', l):
            return re.match(r'(\w+):', lines[i-1]).group(1)


OVERRUN = os.environ.get('GNG_OVERRUN') == '1'

class GameRun(Amiga):
    """build: '512k' or '1mb'; binfile: the main program (default: the original); extra_files:
    {track: path} for files LoadFile reads that are not in disk/files (the modules)"""
    def __init__(self, binfile=None, extra_files=None, build='512k', machine=None, listing=None, by_id=False, disk=None):
        cfg = self.cfg = BUILDS[build]
        super().__init__(os.path.join(ROOT, BUILDS['512k']['orig']))
        big = machine and any(end > 0x80000 and attr & 2 for attr, start, end in machine[0])
        if build != '512k' or big:
            self.u.mem_map(0x80000, 0x80000)                  # 1MB of chip RAM
            self.u.mem_write(0, bytes(0x80000))
        self.u.mem_write(0, bytes(0x60))
        prog = open(binfile or os.path.join(ROOT, cfg['orig']), 'rb').read()
        self.u.mem_write(cfg['load'], prog)
        orig = os.path.getsize(os.path.join(ROOT, BUILDS['512k']['orig']))
        if len(prog) < orig:                   # a shorter program: no trace of the original after it
            self.u.mem_write(cfg['load'] + len(prog), bytes(orig - len(prog)))   # (the bootblock loads
                                               # whole tracks, and the rest of its last one is zeros)
        self.w32(4, cfg['load'] if build == '512k' else cfg['base'])   # $4.w as the bootblock leaves it
        if machine:                            # the enhanced bootblock's machine description:
            import test_bootinfo                # its own code, run on a fake exec memory list
            self.u.mem_write(test_bootinfo.MACHINE_INFO, test_bootinfo.run(*machine))
            for attr, start, end in machine[0]:          # expansion memory
                if not attr & 2:
                    self.u.mem_map(start & ~0xFFF, (end - (start & ~0xFFF) + 0xFFF) & ~0xFFF)
        chip = [e for a, st, e in machine[0] if a & 2] if machine else []
        self.chip_end = (0x80000 if max(chip) <= 0x80000 else 0x100000 << (max(chip) > 0x100000)) if chip \
            else (0x80000 if build == '512k' else 0x100000)      # (the physical end: exec may keep the top)
        self.L = L = labels(build, listing)
        # the one program moves itself out of chip RAM on some machines (EnhRelocate): where to
        self.reloc = relocation(machine, listing) if listing else 0
        if self.reloc:
            top = L['GlobalsBlock'] + 0x178C            # MAP_LOW: the memory map stays
            self.L0 = dict(L)
            self.L = L = {k: v + self.reloc if 0x80 <= v < top else v for k, v in L.items()}
            self.entry_orig = self.L0['ProgramEntry']
        self.entry, self.idle = L['ProgramEntry'], L['IdleLoop']
        self.copyright_wait = L[copyright_wait(build)]
        self.redraw_entry = L['RedrawEntry']           # ... and its idle loop (bra.b *): the first $60FE
        o = self.redraw_entry - self.reloc - cfg['load']
        self.redraw_idle = self.redraw_entry + next(i for i in range(0, 32, 2) if prog[o+i:o+i+2] == b'\x60\xfe')
        self.vbl, self.level1 = L.get('IrqLevel3', L['VblIRQ']), L.get('IrqLevel1', L['Level1Logic'])
        self.by_id = by_id                     # file records name a file (the one program's disk) and
                                               # load exactly its bytes; else a track (whole tracks)
        self.palette_addr = L['GamePalette']
        eq = equates(os.path.join(ROOT, cfg['equates']), build != '512k')
        # the globals: where the listing puts them (a program that has moved), else the build's
        self.globals = L['GlobalsBlock'] if listing and 'GlobalsBlock' in L else cfg['globals']
        if self.reloc: self.entry = self.entry_orig
        self.G = {k: self.globals + v for k, v in eq.items() if k.startswith('g_')}
        # every RTE in the program loaded (a hook on a data word that looks like one is harmless)
        rtes = [cfg['load'] + i for i in range(0, len(prog) - 1, 2) if prog[i:i+2] == b'\x4e\x73']
        if self.reloc: rtes = [a + self.reloc for a in rtes]     # (the first copy only runs Start's beginning)
        self.extra = extra_files or {}
        self.u.mem_map(0xFFFF0000, 0x10000)    # the game sometimes reads a little below 0 (MapTileAt
                                               # with a map byte >= $80); on the Amiga's 24-bit bus that
                                               # is ROM. Here it reads zeros.
        self.w16(CUSTOM+0x1E, 0x0790)          # INTREQR: copper and audio interrupts always pending
                                               # (ShowBackBuffer and the sound driver wait for them)
        if disk:                               # disk: an ADF the program's own LoadFile reads (the
            import floppy                       # byteloader, through tools/floppy.py)
            span = lambda Ls: (Ls['ByteLoader'], Ls['ByteLoader'] + 0x186)
            self.floppy = floppy.Floppy(self, open(disk, 'rb').read(),
                                        timing_ranges=[span(L)] + ([span(self.L0)] if self.reloc else []))
        else:
            self._stub_loadfile(L['LoadFile'])
        if self.reloc and not disk:            # EnhRelocate loads from the first copy, which the music
            first = self._stub_loadfile(self.L0['LoadFile'])    # package then overwrites
            def moved(uc, a, sz, ud):
                uc.hook_del(first); uc.hook_del(self._moved)
            self._moved = self.u.hook_add(UC_HOOK_CODE, moved, begin=L['Start'], end=L['Start'])
        for a in rtes:
            self.u.hook_add(UC_HOOK_CODE, self._rte, begin=a, end=a)
        self.u.hook_add(UC_HOOK_MEM_WRITE, self._intreq, begin=CUSTOM+0x9C, end=CUSTOM+0x9D)
        self.u.hook_add(UC_HOOK_CODE, self._shown, begin=L['ShowBackBuffer'], end=L['ShowBackBuffer'])
        self.softint = False
        self.shows = 0
        self.user_pc = None
        self.frame_no = 0

    def _stub_loadfile(self, addr):
        names = {int(f[1:4]): os.path.join(FILES, f) for f in os.listdir(FILES) if f[0] == 't' and f[1:4].isdigit()}
        names.update(self.extra)
        def hook(uc, a, sz, ud):
            a1 = self.reg('a1')
            dest, length, track = self.r32(a1), self.r32(a1+4), self.r16(a1+8)
            off = self.r32(self.L['LoadOffset']) if 'LoadOffset' in self.L else 0   # (a piece of a file)
            data = open(names[track], 'rb').read()[off:off + length]
            if OVERRUN and 'MfmBuf' in self.L:          # the MFM buffer the disk DMA fills ($1900 words)
                self.u.mem_write(self.r32(self.L['MfmBuf']), b'\xEE' * (0x2EC0 if self.by_id else 0x3200))
            self.u.mem_write(dest, data)
            pad = (-len(data)) % 0x18A8 if OVERRUN and not self.by_id else 0   # LoadFile writes whole tracks: what follows
            if pad:                                  # a file on its last track lands after it (GNG_OVERRUN=1
                                                     # fills that with $EE bytes, to check nothing needed
                                                     # is in the way; off by default, because the originals
                                                     # and the enhanced game leave different junk in
                                                     # memory that unused sprites then show)
                try: self.u.mem_write(dest + len(data), b'\xEE' * pad)
                except Exception: pass
            if self.reloc: uc.ctl_remove_cache(dest, dest + len(data) + pad)   # (code ran there before: the
            self.reg('a5', dest+len(data))                               # first copy of the program)
            sp = self.reg('a7'); ret = self.r32(sp); self.reg('a7', sp+4)
            uc.reg_write(UC_M68K_REG_PC, ret)
        return self.u.hook_add(UC_HOOK_CODE, hook, begin=addr, end=addr)

    def _rte(self, uc, a, sz, ud):
        sp = self.reg('a7')
        sr, pc = self.r16(sp), self.r32(sp+2)
        self.reg('a7', sp+6)
        uc.reg_write(UC_M68K_REG_SR, sr)          # (switches to the user stack when S is clear)
        uc.reg_write(UC_M68K_REG_PC, pc)
        uc.emu_stop()

    def _intreq(self, uc, access, addr, size, value, ud):
        v = value & 0xFFFF if size == 2 else value
        if v & 0x8000 and v & 0x0004: self.softint = True

    def _shown(self, uc, a, sz, ud):
        self.shows += 1

    # ---- running
    def boot(self):
        self.u.reg_write(UC_M68K_REG_SR, 0x2700)
        self.reg('a7', self.cfg['ssp'])
        self.u.emu_start(self.entry, self.copyright_wait, count=50_000_000)
        self.w16(self.G['g_VblCount'], 0x1F4)      # the copyright screen's 10 seconds
        self.u.emu_start(self.copyright_wait, self.idle, count=50_000_000)
        self.user_pc = self.idle

    def _interrupt(self, handler, ipl):
        self.u.reg_write(UC_M68K_REG_SR, 0x2000 | ipl << 8)   # supervisor: the system stack
        sp = self.reg('a7') - 6
        self.u.mem_write(sp, struct.pack('>HI', 0x0000, self.user_pc))
        self.reg('a7', sp)
        self.u.emu_start(handler, 0xFFFFFF, count=20_000_000)
        pc = self.u.reg_read(UC_M68K_REG_PC)
        if pc == self.redraw_entry:               # VblIRQ diverted user mode: the background redraw
            self.u.emu_start(self.redraw_entry, self.redraw_idle, count=50_000_000)
            pc = self.redraw_idle
        self.user_pc = pc

    def frame(self, joy='', fire=False, fire2=False):
        self.w16(CUSTOM+0x0C, JOY[joy])
        self.w8(0xBFE001, 0x7F if fire else 0xFF)
        self.w16(CUSTOM+0x16, 0xBF00 if fire2 else 0xFF00)    # POTINP: the second buttons (bit 14: port 2)
        self.softint = False
        self._interrupt(self.vbl, 3)
        if self.softint:
            self._interrupt(self.level1, 1)
        self.frame_no += 1

    def g(self, name, size=2):
        return {1: self.r8, 2: self.s16, 4: self.r32}[size](self.G[name])


MODULE_TRACK = {'512k': 132, '1mb': 133}


def relocation(machine, listing):
    """how far the one program moves itself (EnhRelocate) on this machine: 0 or the distance
    to the expansion it goes to (fast RAM, else slow RAM: the last region of each kind, as the
    bootblock's description; on 256 bytes; with RELOC_ROOM bytes of room)"""
    if not machine: return 0
    import build_game
    S = build_game.symbols(listing)
    if not S.get('RELOC_LEN'): return 0
    regions = machine[0]
    chip = [e for a, s, e in regions if a & 2]
    if not chip or max(chip) > 0x80000: return 0
    slot = {}
    for a, s, e in regions:
        if a & 2: continue
        slot['slow' if 0xC00000 <= s + 0x20 < 0xDC0000 else 'fast'] = (s + 0x20, e)
    for k in ('fast', 'slow'):
        if k in slot:
            lo, hi = slot[k]
            dest = (lo + 0xFF) & ~0xFF
            if hi > dest and hi - dest >= S['RELOC_ROOM']: return dest - 0x80
    return 0


def game(machine=None, disk=False):
    """the one program for every machine (build_game.py), on a machine as in
    test_bootinfo.MACHINES (regions, vblank, attnflags); None: no machine description.
    disk: its loads read the disk image through the byteloader (tools/floppy.py), not stubbed"""
    import build_game
    d = build_game.OUT
    files = build_game.disk_files(os.path.join(d, 'game.bin'), os.path.join(d, 'sfx.bin'),
                                  os.path.join(d, 'music.bin'), os.path.join(d, 'relocs.bin'), d)
    return GameRun(os.path.join(d, 'game.bin'), {fid: path for fid, (name, path) in enumerate(files)}, '512k',
                   machine, listing=os.path.join(d, 'game.lst'), by_id=True,
                   disk=os.path.join(d, '..', 'gng_game.adf') if disk else None)


def enhanced(build='512k', machine=None):
    """the enhanced game of a build (made by build_enh.py); machine: (regions, vblank,
    attnflags) as in test_bootinfo.MACHINES, to have the bootblock's description in memory"""
    d = os.path.join(BUILD, build)
    return GameRun(os.path.join(d, 'main.bin'), {MODULE_TRACK[build]: os.path.join(d, 'module.bin')}, build, machine)


def script_start():
    """attract mode, fire to start, then the opening scene"""
    return [('', False)]*60 + [('', True)]*4 + [('', False)]*20


if __name__ == '__main__':
    import sys, time
    build = sys.argv[1] if len(sys.argv) > 1 else '512k'
    which = sys.argv[2] if len(sys.argv) > 2 else 'orig'
    m = enhanced(build) if which == 'enh' else GameRun(build=build)
    t = time.time()
    m.boot()
    print(f'boot {time.time()-t:.1f}s, state {m.g("g_GameState",1)}')
    for i in range(int(sys.argv[3]) if len(sys.argv) > 3 else 300):
        m.frame(*(script_start()[i] if i < len(script_start()) else ('R', False)))
        if i % 50 == 0:
            print(i, 'state', m.g('g_GameState', 1), m.g('g_SubState', 1), 'cam', m.g('g_ScrollTileX'), m.g('g_ScrollFineX'),
                  m.g('g_ScrollTileY'), m.g('g_ScrollFineY'), 'arthur', m.g('g_ArthurX'), m.g('g_ArthurY'), 'shows', m.shows,
                  f'{time.time()-t:.1f}s')
    m.save_png(m.render(), os.path.join(BUILD, f'game_{build}_{which}.png'))
