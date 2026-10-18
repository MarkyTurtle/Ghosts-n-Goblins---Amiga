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


def labels(build):
    """label -> address in memory, from the listing build_enh.py made of the original source"""
    cfg = BUILDS[build]
    text = open(os.path.join(BUILD, build, 'orig_main.lst')).read()
    part = text[text.index('Symbols by name:'):text.index('Symbols by value:')]
    return {m.group(1): cfg['base'] + int(m.group(2), 16)
            for m in re.finditer(r'^(\S+)\s+A:([0-9A-F]+)$', part, re.M)}


def copyright_wait(build):
    """the label of Start's loop that waits 500 VBLs on the copyright screen"""
    lines = open(os.path.join(ROOT, BUILDS[build]['src'])).read().split('\n')
    for i, l in enumerate(lines):
        if re.match(r'\s+cmpi\.w\s+#\$1f4,g_VblCount', l):
            return re.match(r'(\w+):', lines[i-1]).group(1)


class GameRun(Amiga):
    """build: '512k' or '1mb'; binfile: the main program (default: the original); extra_files:
    {track: path} for files LoadFile reads that are not in disk/files (the modules)"""
    def __init__(self, binfile=None, extra_files=None, build='512k', machine=None):
        cfg = self.cfg = BUILDS[build]
        super().__init__(os.path.join(ROOT, BUILDS['512k']['orig']))
        if build != '512k':
            self.u.mem_map(0x80000, 0x80000)                  # 1MB of chip RAM
            self.u.mem_write(0, bytes(0x80000))
        self.u.mem_write(0, bytes(0x60))
        prog = open(binfile or os.path.join(ROOT, cfg['orig']), 'rb').read()
        self.u.mem_write(cfg['load'], prog)
        self.w32(4, cfg['load'] if build == '512k' else cfg['base'])   # $4.w as the bootblock leaves it
        if machine:                            # the enhanced bootblock's machine description:
            import test_bootinfo                # its own code, run on a fake exec memory list
            self.u.mem_write(test_bootinfo.MACHINE_INFO, test_bootinfo.run(*machine))
        self.L = L = labels(build)
        self.entry, self.idle = L['ProgramEntry'], L['IdleLoop']
        self.copyright_wait = L[copyright_wait(build)]
        self.redraw_entry, self.redraw_idle = L['RedrawEntry'], L['RedrawEntry'] + 8
        self.vbl, self.level1 = L['VblIRQ'], L['Level1Logic']
        self.palette_addr = L['GamePalette']
        eq = equates(os.path.join(ROOT, cfg['equates']), build != '512k')
        self.globals = cfg['globals']
        self.G = {k: cfg['globals'] + v for k, v in eq.items() if k.startswith('g_')}
        orig = open(os.path.join(ROOT, cfg['orig']), 'rb').read()   # RTEs: same places in both programs
        rtes = [cfg['load'] + i for i in range(0, len(orig) - 1, 2) if orig[i:i+2] == b'\x4e\x73']
        self.extra = extra_files or {}
        self.u.mem_map(0xFFFF0000, 0x10000)    # the game sometimes reads a little below 0 (MapTileAt
                                               # with a map byte >= $80); on the Amiga's 24-bit bus that
                                               # is ROM. Here it reads zeros.
        self.w16(CUSTOM+0x1E, 0x0790)          # INTREQR: copper and audio interrupts always pending
                                               # (ShowBackBuffer and the sound driver wait for them)
        self._stub_loadfile(L['LoadFile'])
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
            data = open(names[track], 'rb').read()[:length]
            self.u.mem_write(dest, data)
            self.reg('a5', dest+len(data))
            sp = self.reg('a7'); ret = self.r32(sp); self.reg('a7', sp+4)
            uc.reg_write(UC_M68K_REG_PC, ret)
        self.u.hook_add(UC_HOOK_CODE, hook, begin=addr, end=addr)

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

    def frame(self, joy='', fire=False):
        self.w16(CUSTOM+0x0C, JOY[joy])
        self.w8(0xBFE001, 0x7F if fire else 0xFF)
        self.softint = False
        self._interrupt(self.vbl, 3)
        if self.softint:
            self._interrupt(self.level1, 1)
        self.frame_no += 1

    def g(self, name, size=2):
        return {1: self.r8, 2: self.s16, 4: self.r32}[size](self.G[name])


MODULE_TRACK = {'512k': 132, '1mb': 133}


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
