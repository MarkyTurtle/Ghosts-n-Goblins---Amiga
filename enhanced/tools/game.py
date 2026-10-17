"""Run the whole game - original or enhanced - in the emulator, frame by frame.

The program is loaded as the bootblock does; Start runs (the copyright wait is skipped),
then each frame is what the hardware would do: the vertical-blank interrupt (VblIRQ), then,
if it asked for one, the level-1 interrupt (Level1Logic, the game's main loop). When VblIRQ
diverts user mode to RedrawEntry (a background redraw), that runs to its end before the
next frame. Input: the joystick and fire button through the registers VblIRQ reads.

Not emulated: real timing (a frame's work always finishes within the frame), the disk
(LoadFile copies the files from disk/files), audio output, the keyboard interrupt."""
import os, struct
from unicorn import UC_HOOK_CODE, UC_HOOK_MEM_WRITE
from unicorn.m68k_const import UC_M68K_REG_PC, UC_M68K_REG_SR
from amiga import Amiga, CUSTOM, FILES, GLOBALS, equates

EQ = equates()
G = {k: GLOBALS+v for k, v in EQ.items() if k.startswith('g_')}
START, COPYRIGHT_WAIT, IDLE = 0x5AEE, 0x5E36, 0x5EAA
REDRAW_ENTRY, REDRAW_IDLE = 0x5EAC, 0x5EB4
VBL_IRQ, LEVEL1 = 0xBDC2, 0x5EB6
RTES = (0x6BF6, 0x71EA, 0xBFA6, 0xBFDC)
SHOWBACK = 0x80DC
SSP = 0x80000                  # as the bootblock leaves it (the level data reaches $7Fxxx)
JOY = {'': 0, 'R': 0x0003, 'L': 0x0300, 'U': 0x0100, 'D': 0x0001,
       'UR': 0x0102, 'UL': 0x0200, 'DR': 0x0002, 'DL': 0x0301}


class GameRun(Amiga):
    def __init__(self, binfile=None, extra_files=None):
        super().__init__(binfile)
        self.extra = extra_files or {}
        self.u.mem_map(0xFFFF0000, 0x10000)    # the game sometimes reads a little below 0 (MapTileAt
                                               # with a map byte >= $80); on the Amiga's 24-bit bus that
                                               # is ROM. Here it reads zeros.
        self.w16(CUSTOM+0x1E, 0x0790)          # INTREQR: copper and audio interrupts always pending
                                               # (ShowBackBuffer and the sound driver wait for them)
        self._stub_loadfile()
        for a in RTES:
            self.u.hook_add(UC_HOOK_CODE, self._rte, begin=a, end=a)
        self.u.hook_add(UC_HOOK_MEM_WRITE, self._intreq, begin=CUSTOM+0x9C, end=CUSTOM+0x9D)
        self.u.hook_add(UC_HOOK_CODE, self._shown, begin=SHOWBACK, end=SHOWBACK)
        self.softint = False
        self.shows = 0
        self.user_pc = None
        self.frame_no = 0

    def _stub_loadfile(self, addr=0xC476):
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
        self.reg('a7', SSP)
        self.u.emu_start(START, COPYRIGHT_WAIT, count=50_000_000)
        self.w16(G['g_VblCount'], 0x1F4)           # the copyright screen's 10 seconds
        self.u.emu_start(COPYRIGHT_WAIT, IDLE, count=50_000_000)
        self.user_pc = IDLE

    def _interrupt(self, handler, ipl):
        self.u.reg_write(UC_M68K_REG_SR, 0x2000 | ipl << 8)   # supervisor: the system stack
        sp = self.reg('a7') - 6
        self.u.mem_write(sp, struct.pack('>HI', 0x0000, self.user_pc))
        self.reg('a7', sp)
        self.u.emu_start(handler, 0xFFFFFF, count=20_000_000)
        pc = self.u.reg_read(UC_M68K_REG_PC)
        if pc == REDRAW_ENTRY:                    # VblIRQ diverted user mode: the background redraw
            self.u.emu_start(REDRAW_ENTRY, REDRAW_IDLE, count=50_000_000)
            pc = REDRAW_IDLE
        self.user_pc = pc

    def frame(self, joy='', fire=False):
        self.w16(CUSTOM+0x0C, JOY[joy])
        self.w8(0xBFE001, 0x7F if fire else 0xFF)
        self.softint = False
        self._interrupt(VBL_IRQ, 3)
        if self.softint:
            self._interrupt(LEVEL1, 1)
        self.frame_no += 1

    def g(self, name, size=2):
        return {1: self.r8, 2: self.s16, 4: self.r32}[size](G[name])


def script_start():
    """attract mode, fire to start, then the opening scene"""
    return [('', False)]*60 + [('', True)]*4 + [('', False)]*20


if __name__ == '__main__':
    import sys, time
    which = sys.argv[1] if len(sys.argv) > 1 else 'orig'
    here = os.path.dirname(os.path.abspath(__file__))
    if which == 'enh':
        b = os.path.join(here, '..', 'build')
        m = GameRun(os.path.join(b, 'main_enh.bin'), {132: os.path.join(b, 'module.bin')})
    else:
        m = GameRun()
    t = time.time()
    m.boot()
    print(f'boot {time.time()-t:.1f}s, state {m.g("g_GameState",1)}')
    for i in range(int(sys.argv[2]) if len(sys.argv) > 2 else 300):
        m.frame(*(script_start()[i] if i < len(script_start()) else ('R', False)))
        if i % 50 == 0:
            print(i, 'state', m.g('g_GameState', 1), m.g('g_SubState', 1), 'cam', m.g('g_ScrollTileX'), m.g('g_ScrollFineX'),
                  m.g('g_ScrollTileY'), m.g('g_ScrollFineY'), 'arthur', m.g('g_ArthurX'), m.g('g_ArthurY'), 'shows', m.shows,
                  f'{time.time()-t:.1f}s')
    m.save_png(m.render(), f'/tmp/claude-0/-home-claude/f208003a-532a-549d-984d-a12c42fdbbaa/scratchpad/game_{which}.png')
