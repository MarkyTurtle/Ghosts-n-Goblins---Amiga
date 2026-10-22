"""The title menu (scroller.s: EnhMenu, EnhTitleText), on a 512K machine, each case from the same
saved state of the title screen:
  fire on PLAYER 1 START / PLAYER 2 START starts a 1 / 2 player game; F1 / F2 too;
  INPUT: fire, left and right switch the jump input (JumpButton);
  TEST MENU: the test page (no time-out): MUSIC plays and stops tunes, EFFECT plays effects;
    the input test shows what is held and the last key, Esc goes back; the sprite test shows
    Arthur's frames and their mirrored copies, fire held 3 s goes back; CHEAT switches the
    cheat, EXIT goes back;
  the title goes on to the high scores after 400 frames, where fire goes back to the title
  (it does not start a game).
On a 1MB machine (the BOB viewer, bobviewer.s, loaded with the graphics caches): the test page
has BOB TEST; right / left choose the strip (wrapping round), down / up scroll it, the strip is
drawn into the window, Esc goes back. On 512K the viewer is not loaded (no BOB TEST).

  python3 test_menu.py        (after build_game.py)"""
import copy, struct, sys
import compare_game
from game import game

PAGES = [(0, 0x80000), (0xBFD000, 0x2000), (0xDFF000, 0x1000)]


def main():
    (name, regions, vb, attn), build = compare_game.MACHINES['512k']
    m = game((regions, vb, attn))
    m.boot()
    for _ in range(40): m.frame()
    st = ([(a, bytes(m.u.mem_read(a, n))) for a, n in PAGES], m.u.context_save(),
          {k: copy.copy(v) for k, v in m.__dict__.items() if k != 'u'})
    def load():
        mem, ctx, d = st
        for a, b in mem: m.u.mem_write(a, b)
        m.u.context_restore(ctx)
        m.__dict__.update({k: copy.copy(v) for k, v in d.items()})
    def press(joy='', fire=False, wait=20):
        m.frame(joy, fire); m.frame(joy, fire)
        for _ in range(wait): m.frame()
    def key(code, wait=20):
        m.w8(m.G['g_RawKey'], code)
        for _ in range(wait): m.frame()
    g = lambda k: m.g(k, 1)
    var = lambda k: m.r8(m.L[k])
    playing = lambda: g('g_GameState') == 0
    ok = True
    def check(what, good):
        nonlocal ok
        ok &= bool(good)
        print(f'  {"ok  " if good else "FAIL"} {what}')
    check('512K: no BOB viewer (ViewerOn 0)', var('ViewerOn') == 0)
    load(); press('', True)
    check('fire on PLAYER 1 START: a 1 player game', playing() and not g('g_TwoPlayer'))
    load(); press('D'); press('', True)
    check('down, fire on PLAYER 2 START: a 2 player game', playing() and g('g_TwoPlayer'))
    load(); press('U'); press('U'); press('U'); press('', True)
    check('up three times (wrapping round) and fire: PLAYER 2 START', playing() and g('g_TwoPlayer'))
    load(); key(0x51)
    check('F2: a 2 player game', playing() and g('g_TwoPlayer'))
    load(); key(0x50)
    check('F1: a 1 player game', playing() and not g('g_TwoPlayer'))
    load(); press('D'); press('D')
    j0 = var('JumpButton'); press('', True); j1 = var('JumpButton'); press('R'); j2 = var('JumpButton')
    press('L'); j3 = var('JumpButton')
    check(f'INPUT: fire, right, left switch the jump input ({j0} {j1} {j2} {j3})',
          j0 == 0 and j1 and not j2 and j3 and not playing())
    load(); press('U'); press('', True)
    check('TEST MENU: the test page', var('MenuPage') == 1 and var('MenuItem') == 0 and g('g_GameState') == 1)
    # the sound test: the driver's voices (its workspace found as StopMusic finds it)
    drv = m.r32(0x60)
    dv = drv + 0x20 + struct.unpack('>h', bytes(m.u.mem_read(drv + 0x20, 2)))[0]
    voice = lambda k: m.r32(dv + 4 + 0x68 * k)
    press('R'); press('R'); press('R')
    t = m.r8(m.L['TestMusic'])
    press('', True)
    for _ in range(50): m.frame()
    on = [voice(k) for k in range(4)]
    check(f'MUSIC: right three times is tune {t}, fire plays it ({sum(1 for v in on if v)} voices)', t == 2 and any(on))
    press('L'); press('L'); press('L'); press('', True)
    for _ in range(10): m.frame()
    check(f'MUSIC: back to OFF ({m.r8(m.L["TestMusic"])}), fire stops it', m.r8(m.L['TestMusic']) == 0xFF
          and not any(voice(k) for k in range(4)))
    press('L'); press('L')
    check(f'MUSIC: left from OFF goes round to the last tune ({m.r8(m.L["TestMusic"])})', m.r8(m.L['TestMusic']) == 13)
    press('D'); press('L'); press('', True, wait=2)
    e = m.r8(m.L['TestEffect'])
    check(f'EFFECT: left from 0 is 29 ({e}), fire plays it', e == 29 and any(voice(k) for k in range(4, 8)))
    # the input test
    press('D'); press('', True)
    check('INPUT TEST: its page', var('MenuPage') == 2)
    for _ in range(30): m.frame('UL', False, True)
    shown = m.r16(m.L['InputShown'])
    check(f'the page shows up, left and fire 2 held (${shown:04X})', shown == 0x4300)
    for _ in range(5): m.frame()
    m.w8(m.G['g_RawKey'], 0x21); [m.frame() for _ in range(30)]
    check(f'a key: shown by its raw code (${m.r8(m.L["InputKeyShown"]):02X})', m.r8(m.L['InputKeyShown']) == 0x21)
    key(0x45)
    check('Esc: back to the test page', var('MenuPage') == 1 and var('MenuItem') == 2)
    # the sprite test
    press('D'); press('', True)
    check('SPRITE TEST: its page, Arthur shown', var('MenuPage') == 3 and g('g_ArthurVisible'))
    press('R'); press('R'); press('L', wait=25); press('L'); press('L')
    f1 = m.r8(m.L['SprFrame'])
    check(f'left / right step the frames round ({f1})', f1 == 41 and g('g_ArthurFrame') == 41)
    press('R'); press('R'); press('', True)
    check(f'fire: frame 1 mirrored (g_ArthurFrame ${g("g_ArthurFrame"):02X})', g('g_ArthurFrame') == 0xFE)
    for _ in range(160): m.frame('', True)
    for _ in range(25): m.frame()
    check('fire held 3 s: back to the test page, Arthur hidden', var('MenuPage') == 1 and not g('g_ArthurVisible'))
    press('D'); c0 = g('g_CheatOn'); press('', True); c1 = g('g_CheatOn'); press('R'); c2 = g('g_CheatOn')
    check(f'CHEAT: fire, right switch the cheat ({c0} {c1} {c2})', not c0 and c1 and not c2)
    for _ in range(500): m.frame()
    check('the test page stays (500 frames)', g('g_GameState') == 1 and var('MenuPage') == 1)
    press('D'); press('', True)
    check('EXIT: the title, on TEST MENU', not var('MenuPage') and var('MenuItem') == 3 and g('g_GameState') == 1)
    load()
    for _ in range(420): m.frame()
    check('the title goes on to the high scores', g('g_GameState') == 2)
    press('', True)
    check('fire on the high scores: the title, no game', g('g_GameState') == 1 and not var('MenuPage'))
    ok &= viewer()
    print('all as expected' if ok else 'FAILED')
    return ok


def viewer():
    """The BOB viewer on a 1MB machine."""
    (name, regions, vb, attn), build = compare_game.MACHINES['1mb']
    m = game((regions, vb, attn))
    m.boot()
    for _ in range(40): m.frame()
    def press(joy='', fire=False, wait=20):
        m.frame(joy, fire); m.frame(joy, fire)
        for _ in range(wait): m.frame()
    var = lambda k: m.r8(m.L[k])
    word = lambda k: m.r16(m.L[k])
    ok = True
    def check(what, good):
        nonlocal ok
        ok &= bool(good)
        print(f'  {"ok  " if good else "FAIL"} 1MB: {what}')
    check(f'the BOB viewer loaded (ViewerOn ${var("ViewerOn"):02X})', var('ViewerOn') == 0xFF)
    press('U'); press('', True)
    for _ in range(4): press('D')
    press('', True)
    check('BOB TEST: its page (item 4)', var('MenuPage') == 4)
    win = lambda im: im[60:170, 80:240].tobytes()          # the window, about
    a = win(m.render())
    press('R'); press('R')
    b = win(m.render())
    check(f'right twice: strip {word("ViewSel")}, drawn differently', word('ViewSel') == 2 and a != b)
    press('L'); press('L'); press('L')
    check(f'left past 0 goes round to the last strip ({word("ViewSel")})', word('ViewSel') == 58)
    press('R'); press('D'); press('D')
    t = word('ViewTop'); c = win(m.render())
    check(f'down twice scrolls the strip (line {t}), drawn differently', t == 32 and c != a)
    press('U')
    check(f'up scrolls back ({word("ViewTop")})', word('ViewTop') == 16)
    m.w8(m.G['g_RawKey'], 0x45)
    for _ in range(30): m.frame()
    check('Esc: back to the test page on BOB TEST', var('MenuPage') == 1 and var('MenuItem') == 4)
    return ok


if __name__ == '__main__':
    sys.exit(0 if main() else 1)
