"""Changes of display (gng_game.s: LoadLevel, ProgressMap, SetupLevel; scroller.s: EnhDisplayOff,
EnhDisplayOn): on a 512K and a 1MB machine, a game is started, the time is let run out (a life
lost: the progress map, then the level again). The beam moves on at every read of VPOSR / VHPOSR,
so the waits for the vertical blank are exercised. Checks:
  * every write that turns the bitplanes off or on comes in the vertical blank (the beam above
    the display, lines $00-$2B, or below it, from $125);
  * the bitplanes are off while the progress map is unpacked (into the scroller's display
    buffers) and while SetupLevel draws the level into them (the map shown from there);
  * they are on again on the map and in play (the map's / the level's copper list in place);
  * the loading picture ($60000-$78300) is not written while it is on show: up to InitHardware,
    which puts the copyright screen up (level 0 loads after it, on every machine).

  python3 test_display.py        (after build_game.py)"""
import random, sys
import compare_game
from game import game, script_start
from unicorn import UC_HOOK_CODE, UC_HOOK_MEM_READ, UC_HOOK_MEM_WRITE
from unicorn.m68k_const import UC_M68K_REG_PC

PIC0, PIC1 = 0x60000, 0x78300


def run(mach):
    (name, regions, vb, attn), build = compare_game.MACHINES[mach]
    m = game((regions, vb, attn))
    m.beam_reset = False                              # the beam moved here, not reset
    st = {'line': 0x40, 'raster': True, 'bad': [], 'writes': 0, 'map_off': None, 'draw_off': [],
          'boot': True, 'pic': False}
    def beam(uc, acc, addr, size, value, ud):        # the beam: 3 lines on at every read
        st['line'] = (st['line'] + 3) % 312
        v = st['line']
        m.w16(0xDFF004, v >> 8); m.w16(0xDFF006, (v & 0xFF) << 8)
    m.u.hook_add(UC_HOOK_MEM_READ, beam, begin=0xDFF004, end=0xDFF007)
    def dmacon(uc, acc, addr, size, value, ud):
        v = value & 0xFFFF
        if not v & 0x0100: return
        on = bool(v & 0x8000)
        if not st['boot'] and on != st['raster']:
            st['writes'] += 1
            if 0x2C <= st['line'] < 0x125:
                st['bad'].append((on, st['line'], uc.reg_read(UC_M68K_REG_PC)))
        st['raster'] = on
        m.w16(0xDFF002, (m.r16(0xDFF002) & ~0x0100) | (0x0100 if on else 0))    # DMACONR
    m.u.hook_add(UC_HOOK_MEM_WRITE, dmacon, begin=0xDFF096, end=0xDFF097)
    def unpack(uc, addr, size, ud):                   # the map unpacked
        st['map_off'] = (st['map_off'] or False) or not st['raster']
    m.u.hook_add(UC_HOOK_CODE, unpack, begin=m.L['pm_have'], end=m.L['pm_have'])
    def redraw(uc, addr, size, ud):                   # SetupLevel's drawing
        if m.g('g_SubState', 1) == 1 and m.g('g_SubState2', 1) == 1:
            st['draw_off'].append(not st['raster'])
    m.u.hook_add(UC_HOOK_CODE, redraw, begin=m.L['RedrawScreen'], end=m.L['RedrawScreen'])
    m.u.mem_write(PIC0, bytes(random.Random(1).randrange(256) for _ in range(PIC1 - PIC0)))
    pic = bytes(m.u.mem_read(PIC0, PIC1 - PIC0))
    def copyright(uc, addr, size, ud):                # the display leaves the loading picture
        if not st['pic']: st['pic'] = bytes(m.u.mem_read(PIC0, PIC1 - PIC0)) == pic or 'changed'
    m.u.hook_add(UC_HOOK_CODE, copyright, begin=m.L['InitHardware'], end=m.L['InitHardware'])
    m.boot()
    st['boot'] = False
    st['raster'] = True; m.w16(0xDFF002, m.r16(0xDFF002) | 0x0100)
    for j, fi in script_start(): m.frame(j, fi)
    for _ in range(1200):                             # the opening scene, into play
        m.frame()
        if m.g('g_SubState', 1) == 1 and m.g('g_SubState2', 1) == 2: break
    playing1 = st['raster']
    m.w16(m.G['g_TimeLeft'], 0x0001)                  # 1 second left
    seen_map = map_on = False
    for _ in range(3000):
        m.frame()
        if st['map_off'] is not None and m.g('g_SubState3', 1) == 1:
            seen_map = True; map_on |= st['raster']
        if seen_map and m.g('g_SubState', 1) == 1 and m.g('g_SubState2', 1) == 2: break
    for _ in range(5): m.frame()
    playing2 = st['raster'] and m.g('g_SubState2', 1) == 2
    return name, st, playing1, seen_map, map_on, playing2


def main():
    ok = True
    def check(what, good):
        nonlocal ok
        ok &= bool(good)
        print(f'  {"ok  " if good else "FAIL"} {what}')
    for mach in ('512k', '1mb'):
        name, st, p1, seen, map_on, p2 = run(mach)
        print(name)
        check('the loading picture untouched while it is shown (to InitHardware)', st['pic'] is True)
        check(f'bitplanes on in play after the opening scene', p1)
        check(f'the progress map after the life lost; unpacked with the bitplanes off', seen and st['map_off'])
        check('the bitplanes on while the map scrolls', map_on)
        check(f'SetupLevel draws the level with the bitplanes off ({st["draw_off"]})', st['draw_off'] and all(st['draw_off']))
        check('the bitplanes on again in play', p2)
        check(f'{st["writes"]} bitplane switches, all in the vertical blank'
              + (f': not {[(o, hex(l), hex(pc)) for o, l, pc in st["bad"]]}' if st['bad'] else ''), st['writes'] and not st['bad'])
    print('all as expected' if ok else 'FAILED')
    return ok


if __name__ == '__main__':
    sys.exit(0 if main() else 1)
