"""Two-button joysticks (JumpButton, the title's J key): from one saved state of a game on
level 1 (512K), each setting with up, the second button and both, on open ground, at the foot
of a ladder and on the ladder. Expected:

  jump on up (the original):  up jumps, or climbs at a ladder; the second button does nothing
  jump on button 2:           the second button jumps (also at the foot of a ladder, not on
                              it); up only climbs ladders

  python3 test_jump.py        (after build_game.py)"""
import copy, sys
import compare_game
from game import game, script_start

PAGES = [(0, 0x80000), (0xBFD000, 0x2000), (0xDFF000, 0x1000)]


class Test:
    def __init__(self):
        (name, regions, vb, attn), build = compare_game.MACHINES['512k']
        m = self.m = game((regions, vb, attn))
        m.boot()
        for j, f in script_start(): m.frame(j, f)
        while not (m.g('g_GameState', 1) == 0 and m.g('g_SubState', 1) == 2): m.frame()
        for _ in range(100): m.frame()
        m.w8(m.G['g_CheatOn'], 0xFF)                 # (nothing kills him while the ladder is found)

    def save(self):
        m = self.m
        return ([(a, bytes(m.u.mem_read(a, n))) for a, n in PAGES], m.u.context_save(),
                {k: copy.copy(v) for k, v in m.__dict__.items() if k != 'u'})

    def load(self, st):
        m = self.m
        mem, ctx, d = st
        for a, b in mem: m.u.mem_write(a, b)
        m.u.context_restore(ctx)
        m.__dict__.update({k: copy.copy(v) for k, v in d.items()})

    def run(self, joy, fire2, frames=12):
        """what Arthur did: 'jump', 'climb' or nothing"""
        m, seen = self.m, set()
        for _ in range(frames):
            m.frame(joy, False, fire2)
            if m.g('g_Jumping', 1): seen.add('jump')
            if m.g('g_OnLadder', 1): seen.add('climb')
        return 'jump' if 'jump' in seen else 'climb' if 'climb' in seen else '-'

    def setting(self, button):
        self.m.w8(self.m.L['JumpButton'], 0xFF if button else 0)

    def ladder(self):
        """a state with Arthur standing at the foot of a ladder (level 1, along the ground)"""
        m = self.m
        x0 = m.g('g_ArthurX')
        for x in range(x0, x0 + 2600, 16):
            m.w16(m.G['g_ArthurX'], x); m.w16(m.G['g_ArthurY'], 102)
            for _ in range(60): m.frame()
            if m.g('g_Falling', 1) or m.g('g_Jumping', 1): continue
            st = self.save()
            self.setting(False)
            found = self.run('U', False, 4) == 'climb'
            self.load(st)
            if found: return st
        sys.exit('no ladder found')


def main():
    t = Test()
    ok = True
    def check(where, st, button, joy, fire2, want, before=None):
        nonlocal ok
        t.load(st); t.setting(button)
        if before: t.run(*before)
        got = t.run(joy, fire2)
        what = {('U', False): 'up', ('', True): 'button 2', ('U', True): 'up + button 2', ('D', False): 'down'}[joy, fire2]
        good = got == want
        ok &= good
        print(f'  {"ok  " if good else "FAIL"} {where:14} jump on {"button 2" if button else "up":8}  {what:14} -> {got}'
              + ('' if good else f' (expected {want})'))
    ground = t.save()
    for button, results in ((False, ('jump', '-', 'jump')), (True, ('-', 'jump', 'jump'))):
        for (joy, fire2), want in zip((('U', False), ('', True), ('U', True)), results):
            check('open ground', ground, button, joy, fire2, want)
    foot = t.ladder()
    for button, results in ((False, ('climb', '-', 'climb')), (True, ('climb', 'jump', 'jump'))):
        for (joy, fire2), want in zip((('U', False), ('', True), ('U', True)), results):
            check('ladder foot', foot, button, joy, fire2, want)
    for joy, fire2 in (('', True), ('U', False), ('D', False)):
        check('on the ladder', foot, True, joy, fire2, 'climb', before=('U', False, 20))
    print('all as expected' if ok else 'FAILED')
    return ok


if __name__ == '__main__':
    sys.exit(0 if main() else 1)
