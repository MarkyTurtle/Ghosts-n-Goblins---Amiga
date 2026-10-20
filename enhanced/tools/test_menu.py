"""The title menu (scroller.s: EnhMenu, EnhTitleText), on a 512K machine, each case from the same
saved state of the title screen:
  fire on PLAYER 1 START / PLAYER 2 START starts a 1 / 2 player game; F1 / F2 too;
  INPUT: fire, left and right switch the jump input (JumpButton);
  TEST MENU: the test page (no time-out), CHEAT switches the cheat, EXIT goes back;
  the title goes on to the high scores after 400 frames, where fire goes back to the title
  (it does not start a game).

  python3 test_menu.py        (after build_game.py)"""
import copy, sys
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
    check('TEST MENU: the test page', var('MenuPage') and var('MenuItem') == 0 and g('g_GameState') == 1)
    c0 = g('g_CheatOn'); press('', True); c1 = g('g_CheatOn'); press('R'); c2 = g('g_CheatOn')
    check(f'CHEAT: fire, right switch the cheat ({c0} {c1} {c2})', not c0 and c1 and not c2)
    for _ in range(500): m.frame()
    check('the test page stays (500 frames)', g('g_GameState') == 1 and var('MenuPage'))
    press('D'); press('', True)
    check('EXIT: the title, on TEST MENU', not var('MenuPage') and var('MenuItem') == 3 and g('g_GameState') == 1)
    load()
    for _ in range(420): m.frame()
    check('the title goes on to the high scores', g('g_GameState') == 2)
    press('', True)
    check('fire on the high scores: the title, no game', g('g_GameState') == 1 and not var('MenuPage'))
    print('all as expected' if ok else 'FAILED')
    return ok


if __name__ == '__main__':
    sys.exit(0 if main() else 1)
