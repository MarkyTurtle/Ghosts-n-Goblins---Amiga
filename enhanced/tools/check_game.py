"""(512K build.) Play the enhanced game in the emulator with scripted input and check every frame it shows
against the original game's own display code.

For each frame the enhanced build shows while playing, the whole memory is copied into a
second emulator holding the ORIGINAL program, which then draws the same picture its own way:
RedrawScreen at the same camera, CameraJump, DrawBobs with the same draw list, SetBitplanePtrs,
ShowBackBuffer. The two displays (below the HUD) must be identical. (The reference has the
DrawBob top-clip bug fixed (docs/FEATURES.md, Fixes); text printed on the playfield is not redrawn
by the reference, so frames after playfield text are reported separately.)

  python3 check_game.py [frames] [seed] [--png DIR]"""
import os, random, struct, sys, time
import numpy as np
from game import GameRun, G, GLOBALS, script_start, enhanced
from amiga import Amiga

HERE = os.path.dirname(os.path.abspath(__file__))
BUILD = os.path.join(HERE, '..', 'build')
REDRAW, CAMERAJUMP, DRAWBOBS, SETBPL, SHOWBACK = 0xBFDE, 0x8046, 0xBA3E, 0x789A, 0x80DC
SS_INPLAY = 2


def module_syms():
    out = {}
    for l in open(os.path.join(BUILD, '512k', 'module_syms.i')):
        p = l.split()
        if len(p) == 3 and p[1] == 'equ': out[p[0]] = int(p[2][1:], 16)
    return out


class Reference(Amiga):
    """the original program, drawing a given game state"""
    def __init__(self):
        super().__init__()
        self.w16(0xDFF108, 0x92); self.w16(0xDFF10A, 0x92)     # BPL1MOD / BPL2MOD as InitHardware
        self.prog = open(os.path.join(HERE, '..', '..', 'original', 'bin', 'main_512k.bin'), 'rb').read()

    def draw(self, ram):
        self.u.mem_write(0, ram)
        self.u.mem_write(0x80, self.prog[:GLOBALS-0x80])         # original code (the globals stay)
        self.u.mem_write(0xBAF4, bytes.fromhex('c4c6'))           # DrawBob top-clip fix (docs/FEATURES.md, Fixes)
        self.u.mem_write(0xC2EA, bytes.fromhex('c4c6'))
        self.u.mem_write(0x60, struct.pack('>I', 0x7FFE0))        # no sound driver
        g = lambda n: G[n]
        self.w16(g('g_NewTileX'), self.s16(g('g_ScrollTileX'))); self.w16(g('g_NewTileY'), self.s16(g('g_ScrollTileY')))
        self.w16(g('g_PendFineX'), self.s16(g('g_ScrollFineX'))); self.w16(g('g_PendFineY'), self.s16(g('g_ScrollFineY')))
        lst = self.r32(g('g_BlitListPtr'))
        self.call(REDRAW)
        self.call(CAMERAJUMP)
        self.w32(g('g_BlitListPtr'), lst)
        self.call(DRAWBOBS)
        self.call(SETBPL)
        self.call(SHOWBACK)
        return self.render()


def play_script(seed):
    """endless joystick input: mostly walking right, with jumps, throws and some back-tracking"""
    rnd = random.Random(seed)
    while True:
        move = rnd.choice(['R']*8 + ['L', '', 'UR', 'U', 'D'])
        fire = rnd.random() < 0.3
        for i in range(rnd.randrange(8, 60)):
            yield move, fire and i % 10 == 0


def main(frames=1500, seed=1, png=None):
    ms = module_syms()
    m = enhanced('512k')
    prints = [0]
    from unicorn import UC_HOOK_CODE
    m.u.hook_add(UC_HOOK_CODE, lambda *a: prints.__setitem__(0, prints[0]+1),
                 begin=ms['EnhPrintField'], end=ms['EnhPrintField'])
    ref = Reference()
    m.boot()
    inputs = iter(script_start() + [('', False)]*0)
    play = play_script(seed)
    checked = bad = text_frames = 0
    levels, deaths = set(), 0
    t = time.time()
    last_level = None; text_since_redraw = False
    for f in range(frames):
        try: joy, fire = next(inputs)
        except StopIteration: joy, fire = next(play)
        shows, p0, died = m.shows, prints[0], m.g('g_PlayerDied', 1)
        redraw_done = m.r8(G['g_RedrawDone'])
        m.frame(joy, fire)
        if prints[0] != p0: text_since_redraw = True
        if m.g('g_GameState', 1) != 0 or m.g('g_SubState', 1) != SS_INPLAY:
            text_since_redraw = prints[0] != p0
            continue
        lv = m.g('g_Level'); levels.add(lv)
        if m.shows == shows: continue                     # nothing new shown this frame
        a = m.render()[16:]
        b = ref.draw(bytes(m.u.mem_read(0, 0x80000)))[16:]
        checked += 1
        diff = int((a != b).sum())
        if diff:
            if text_since_redraw: text_frames += 1
            else:
                bad += 1
                cam = (m.g('g_ScrollTileX')*16+m.g('g_ScrollFineX'), m.g('g_ScrollTileY')*16+m.g('g_ScrollFineY'))
                print(f'frame {f}: level {lv} camera {cam}: {diff} pixels differ')
                if png:
                    os.makedirs(png, exist_ok=True)
                    m.save_png(a, f'{png}/f{f}_enh.png'); m.save_png(b, f'{png}/f{f}_ref.png')
                if bad >= 10: break
        if f % 200 == 0:
            print(f'  frame {f}: level {lv}, camera x {m.g("g_ScrollTileX")*16+m.g("g_ScrollFineX")}, '
                  f'{checked} checked, {time.time()-t:.0f}s', flush=True)
    print(f'{checked} frames shown while playing were checked (levels {sorted(levels)}): '
          f'{checked-bad-text_frames} identical to the original display code, {bad} different'
          + (f', {text_frames} with playfield text (not compared)' if text_frames else ''))
    return 1 if bad else 0


if __name__ == '__main__':
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    png = sys.argv[sys.argv.index('--png')+1] if '--png' in sys.argv else None
    if png in args: args.remove(png)
    sys.exit(main(int(args[0]) if args else 1500, int(args[1]) if len(args) > 1 else 1, png))
