"""The camera's redraw decisions (PlayFrame $6EF2-$7132) as a Python model, checked
against the real code in the emulator on random inputs, then used to describe what
the camera does while Arthur walks, climbs and falls.   python3 camera.py [main.bin]"""
import random, sys
from emu import Game, STACK

BIN = sys.argv[1] if len(sys.argv) > 1 else None
# globals
CAMDX, CAMDY, PENDX, PENDY = 0x7A, 0x7C, 0x7E, 0x80
TILEX, TILEY, FINEX, FINEY, NEWX, NEWY = 0x6E, 0x70, 0x72, 0x74, 0x82, 0x84
PENDING, DONE, SKIP = 0x1C, 0x1D, 0x1E
DIR, JUMP, FALL, LADDER, VELY = 0x103, 0x107, 0x108, 0x10B, 0xF4

def mag(v):            # the code's |v|: NOT for negative values (one less)
    return v if v >= 0 else ~v
def cls(v):
    return 0 if v < 8 else 1 if v < 16 else 2
def clamp(v):
    return max(-16, min(15, v))

def model(s):
    """s: dict of inputs. Returns (switch, finex, finey, skip, newx, newy, request)."""
    dX, dY, pX, pY = mag(s['camdx']), mag(s['camdy']), mag(s['pendx']), mag(s['pendy'])
    closerX, closerY = pX < dX, pY < dY
    cX, cY, cpX, cpY = cls(dX), cls(dY), cls(pX), cls(pY)
    ground = not s['ladder'] and (s['jump'] or not s['fall'])
    switch = False
    if s['done']:
        if ground:
            if cX == 2: switch = closerX
            elif cX == 1: switch = closerX and cpX != 2 and cpY != 2
            else: switch = closerY and cpX != 2
        else:
            if cY == 2: switch = closerY
            elif cY == 1: switch = (closerX or closerY) and cpY != 2 and cpX != 2
            else: switch = closerX and cpY == 0
    tx, ty = s['tilex'], s['tiley']
    camdx, camdy = s['camdx'], s['camdy']
    skip = s['skip']
    if switch:
        camdx, camdy = s['pendx'], s['pendy']
        finex, finey = clamp(camdx), clamp(camdy)
        tx, ty = s['newx'], s['newy']
    else:
        finex, finey = clamp(camdx), clamp(camdy)
        skip = finex != camdx or (s['vely'] >= 5 and finey != camdy)
    # redraw request
    newx, newy, req = s['newx'], s['newy'], False
    if s['done'] or switch and s['done']:
        nx, ny = tx, ty
        if ground:
            if s['dir'] == 0:
                nx += 1 if camdx > 7 else -1 if camdx < -8 else 0
            elif s['dir'] > 0:
                nx += 1 if camdx > -2 else -1 if camdx < -16 else 0
            else:
                nx += 1 if camdx > 15 else -1 if camdx < 1 else 0
            ny += 1 if camdy > 7 else -1 if camdy < -8 else 0
        else:
            if camdy > 7: ny += (camdy >> 4) + 1
            elif camdy < (0 if s['fall'] else -8): ny += camdy >> 4
            nx += 1 if camdx > 7 else -1 if camdx < -8 else 0
        if (nx, ny) != (tx, ty):
            newx, newy, req = nx, ny, True
    return switch, finex, finey, int(bool(skip)), newx, newy, req

def emulate(G, s):
    w16, w8 = G.w16, G.w8
    for off, k in [(CAMDX, 'camdx'), (CAMDY, 'camdy'), (PENDX, 'pendx'), (PENDY, 'pendy'), (TILEX, 'tilex'),
                   (TILEY, 'tiley'), (NEWX, 'newx'), (NEWY, 'newy'), (VELY, 'vely')]:
        w16(G.g(off), s[k])
    for off, k in [(DONE, 'done'), (JUMP, 'jump'), (FALL, 'fall'), (LADDER, 'ladder'), (DIR, 'dir'), (SKIP, 'skip')]:
        w8(G.g(off), s[k] & 0xFF)
    w8(G.g(PENDING), 0)
    hit = []
    from unicorn import UC_HOOK_CODE
    h = G.u.hook_add(UC_HOOK_CODE, lambda uc, a, z, u: hit.append(1), begin=0x702A, end=0x702A)
    G.reg('a7', STACK); G.run(0x6EF2, 0x7132, count=10000)
    G.u.hook_del(h)
    req = G.r8(G.g(PENDING)) != 0
    return (bool(hit), G.s16(G.g(FINEX)), G.s16(G.g(FINEY)), int(G.r8(G.g(SKIP)) != 0),
            G.s16(G.g(NEWX)), G.s16(G.g(NEWY)), req)

def rand_state(rng):
    tx, ty = rng.randint(0, 100), rng.randint(0, 60)
    s = dict(camdx=rng.randint(-40, 40), camdy=rng.randint(-40, 40), tilex=tx, tiley=ty,
             done=rng.choice([0, 0xFF]), jump=rng.choice([0, 0xFF]), fall=rng.choice([0, 0xFF]),
             ladder=rng.choice([0, 0, 0xFF]), dir=rng.choice([-1, 0, 1]), skip=0, vely=rng.choice([0, 3, 5]))
    if rng.random() < .5:      # a redraw at a nearby origin is waiting
        s['newx'], s['newy'] = tx+rng.randint(-1, 1), ty+rng.randint(-2, 2)
    else:
        s['newx'], s['newy'] = tx, ty
    s['pendx'] = s['camdx'] - 16*(s['newx']-tx); s['pendy'] = s['camdy'] - 16*(s['newy']-ty)
    return s

if __name__ == '__main__':
    G = Game(BIN); rng = random.Random(1)
    bad = 0; N = 20000
    for i in range(N):
        s = rand_state(rng)
        m, e = model(s), emulate(G, s)
        if m != e:
            bad += 1
            if bad <= 5: print('MISMATCH', s, '\n   model', m, '\n   code ', e)
    print(f'model vs real code: {N-bad} of {N} random states agree')
