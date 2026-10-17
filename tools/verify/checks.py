"""Check the annotations' claims about bugs and behaviour by running the real code
(512K main.bin) in a 68000 emulator. Each check prints what the code did and whether it
matches what the source and README say.   python3 checks.py [path/to/main.bin]"""
import math, sys
from emu import Game, STACK

BIN = sys.argv[1] if len(sys.argv) > 1 else None
results = []
def check(name, ok, detail):
    results.append(ok)
    print(f"[{'PASS' if ok else 'FAIL'}] {name}\n       {detail}")

ENEMY0 = 0xE28; SHOTS = 0x8E0; ESHOTS = 0x978

# 1. DirectionToArthur: 16 directions, data bug at 45 degrees left-below
G = Game(BIN); S = G.g(ENEMY0)
def direction(dx, dy):
    G.w16(G.g(0xE6), 1000+dx); G.w16(G.g(0xEA), 1000+dy); G.w16(S+6, 1000); G.w16(S+0xA, 1000)
    G.call(0xADA4, a5=S, d0=0); return G.reg('d0') & 0xFF
got = {deg: direction(round(100*math.cos(math.radians(deg))), round(100*math.sin(math.radians(deg))))
       for deg in (0, 45, 135, 225, 315)}
check('DirectionToArthur: 45 degrees left-below gives 5, not 6',
      got == {0: 0, 45: 14, 135: 10, 225: 5, 315: 2}, f'0/45/135/225/315 degrees -> {list(got.values())}')
bands = [direction(100, dy) for dy in (-10, -30, -100, -150, -199, -200, -599, -600)]
check('DirectionToArthur: slope bands use the integer quotient |dy| / |dx|',
      bands == [0, 1, 2, 2, 2, 3, 3, 4], f'dx 100, dy -10 -30 -100 -150 -199 -200 -599 -600 -> {bands}')

# 2. Petite Devil turning stores direction 1
G = Game(BIN); S = G.g(ENEMY0)
G.w8(S, 1); G.w16(S+6, 500); G.w16(S+0xA, 300); G.w8(S+0x12, 4); G.w32(S+0xE, 0xD978)
G.w8(S+0x22, 1); G.w8(S+0x23, 5); G.w8(S+0x39, 8); G.w8(S+0x36, 200); G.w8(S+0x30, 100)
G.w16(G.g(0xE6), 300); G.w16(G.g(0xEA), 300)
dirs = set()
for f in range(40):
    G.call(0xD560, a5=S, d0=0); dirs.add(G.r8(S+0x12))
check('Petite Devil: a turn always stores direction 1', dirs == {1},
      f'wanting direction 8 (left), O_Dir over 40 frames = {sorted(dirs)}; it moved to X {G.r16(S+6)}, Y {G.r16(S+0xA)} '
      f'(from 500, 300: right and down)')

# 3. Big Man crouch wait: a +-16 px range
G = Game(BIN); S = G.g(ENEMY0); ok = []
for dy in range(-40, 41):
    G.u.mem_write(S, bytes(0x3C)); G.w16(S+0xA, 400+dy); G.w16(G.g(0xEA), 400)
    G.call(0x1062E, a5=S, d0=0)
    if G.r8(S+5): ok.append(dy)
check('Big Man: crouches when Arthur is within 16 px vertically', ok == list(range(-16, 17)),
      f'advances for O_Y - Arthur Y in {min(ok)} .. {max(ok)}')

# 4. Red Arremer start mode 2: 2 x 26,352 frames
G = Game(BIN); S = G.g(ENEMY0); G.w8(S, 1); G.w8(S+4, 2)
f = 0
while G.r8(S+4) == 2 and f < 100000:
    G.w16(G.g(6), f); G.call(0xE2D0, a5=S, d0=0); f += 1
check('Red Arremer mode 2: blinks in for 2 x 26,352 frames', f == 52706, f'left the blink-in after {f} frames')

# 5. Red Arremer dodge test
def dodge(active1, rax=1100, shx=1050):
    G = Game(BIN); S = G.g(ENEMY0); SH = G.g(SHOTS)
    G.w16(S+6, rax); G.w16(S+0xA, 400); G.w16(G.g(0xE6), 1000); G.w16(G.g(0xEA), 400)
    G.w8(SH, 0); G.w8(SH+0x26, active1); G.w16(SH+0x26+6, shx); G.w16(SH+0x26+0xA, 400)
    G.call(0xEAF4, a0=0xE874, a5=S, d0=0); return bool(G.reg('d0') & 0xFFFF)
check("Red Arremer: a free shot slot's stale position still makes it dodge", dodge(0),
      f'slot 1 free but its old position threatening -> dodge = {dodge(0)}')
far = dodge(1, 1200, 1100)
check('Red Arremer: the side test compares bit 7 of the low bytes', dodge(1) and not far,
      f'shot 50 px right of Arthur, Red Arremer at 100 px -> {dodge(1)}; shot at 100, Red Arremer at 200 -> {far}')

# 6. Satan's dying pause and Astaroth's stand phase
G = Game(BIN); S = G.g(ENEMY0)
G.w8(S, 2); G.w8(S+3, 2); G.w8(S+4, 2); G.w8(S+0x30, 0x3F); G.call(0xF3AA, a5=S, d0=0)
check("Satan: the 63-frame pause after the explosion is skipped", G.r8(S+3) == 3,
      f'O_State after one frame of the wait = {G.r8(S+3)}')
G = Game(BIN); S = G.g(ENEMY0)
G.w8(S, 1); G.w8(S+0x1A, 13); G.w16(S+0x22, 1); G.w16(S+6, 200); G.w16(G.g(0xE6), 150)
G.call(0x11820, a5=S, d0=0)
check("Astaroth: the stand-and-fire phase ends on the frame it starts", G.r8(S+0x32) == 0,
      f'Ast_Standing after the frame that starts it = {G.r8(S+0x32)}, Ast_StandIn now {G.r16(S+0x22)}')

# 7. Ladder: stepping down from the top never shows frame 13
def ladder(down):
    G = Game(BIN)
    G.u.mem_write(0x8B74, b'\x50\xC0\x4E\x75' if down else b'\x42\x00\x4E\x75')   # LadderCheck stub
    if not down: G.w8(G.g(0x10B), 0xFF)
    seen = []
    for f in range(30):
        bit = 1 if down else 0x100
        G.w16(G.g(0x5A), bit); G.w16(G.g(0x5C), bit); G.call(0x87E6, d0=0)
        fr = G.r8(G.g(0x101))
        if not seen or seen[-1] != fr: seen.append(fr)
    return seen
dn, up = ladder(True), ladder(False)
check('Ladder: going down from the top skips the frame-13 pose', 13 not in dn and 13 in up,
      f'frames going down: {dn}; going up and off: {up[:3]}')

# 8. ShotsVsEnemyShots: wrong box after a miss
def block(dx, other):
    G = Game(BIN); ES = G.g(ESHOTS); SH = G.g(SHOTS)
    G.w16(G.g(0x9C), 3)
    G.w8(ES, 1); G.w8(ES+1, 1); G.w8(ES+0x1A, 7); G.w16(ES+6, 500); G.w16(ES+0xA, 300)
    if other: G.w8(SH, 1); G.w8(SH+1, 1); G.w16(SH+6, 100); G.w16(SH+0xA, 300)
    S1 = SH+0x26; G.w8(S1, 1); G.w8(S1+1, 1); G.w16(S1+6, 500-dx); G.w16(S1+0xA, 300)
    G.call(0x9704, d0=0); return G.r8(ES) == 2
check("Cross vs enemy shots: after a miss the next shot uses the wrong box",
      not block(13, False) and block(13, True),
      f'cross 13 px away: alone -> {block(13, False)}, with another shot missing first -> {block(13, True)}')

# 9. Vertical camera response (characterised, not a pass/fail claim)
G = Game(BIN)
def cam(diff, falling=0):
    G.w16(G.g(0x70), 20); G.w16(G.g(0x74), 0); G.w16(G.g(0x88), 0); G.w16(G.g(0x90), 2000)
    G.w16(G.g(0xEA), 320-diff+0x8E); G.w16(G.g(6), 1); G.w8(G.g(0x108), falling); G.w8(G.g(0x107), 0)
    G.reg('a7', STACK); G.run(0x6E64, 0x6EE6); return G.s16(G.g(0x7C))
resp = {d: cam(d) for d in (-20, -3, -1, 0, 1, 2, 3, 4, 10, 20)}
exp = {-20: 2, -3: 2, -1: 1, 0: 0, 1: -1, 2: -2, 3: -4, 4: -6, 10: -18, 20: -38}
check('Camera Y: up at most 2 px a step; down by 2 x distance - 2 (overshoot)', resp == exp,
      'camera minus target -> change: ' + ', '.join(f'{d:+d}:{v:+d}' for d, v in resp.items()))

# 10. The camera's switch / scroll / redraw rules (tools/verify/camera.py) against the code
import random, camera
G = Game(BIN); rng = random.Random(7); agree = 0
for i in range(2000):
    st = camera.rand_state(rng); agree += camera.model(st) == camera.emulate(G, st)
check('Camera: the documented switch / scroll / redraw rules match the code', agree == 2000,
      f'{agree} of 2000 random camera states give the same result as the model')

# 11. Platform scripts: the type-3 platform with param 1 runs type 4's first script
G = Game(BIN); S = G.g(ENEMY0); got = {}
for t, p in ((3, 0), (3, 1), (4, 0)):
    G.u.mem_write(S, bytes(0x3C)); G.w8(S+0x1A, t); G.w8(S+2, p); G.call(0xA666, a5=S, d0=0)
    got[(t, p)] = (G.r16(S+0xE) << 16 | G.r16(S+0x10), G.r16(S+0x14) << 16 | G.r16(S+0x16))
check("Platforms: type 3 param 1 takes type 4's param-0 script with its own steps",
      got[(3, 1)][0] == got[(4, 0)][0] and got[(3, 1)][1] not in (got[(3, 0)][1], got[(4, 0)][1]),
      ', '.join(f'type {t} param {p}: script ${a:X}, steps ${b:X}' for (t, p), (a, b) in got.items()))

# 12. PetiteDevilPath (unused code): the offsets land 2 bytes past each list
G = Game(BIN); S = G.g(ENEMY0); G.w8(S+0x36, 1); G.call(0xD244, a0=0xD2D0, a5=S, d0=0)
seg = G.r16(S+0x28) << 16 | G.r16(S+0x2A)
check('PetiteDevil_PathNext: reads the first X as the count (offset applied after the word)',
      G.r8(S+0x22) == 0xD8 and seg == 0xD352,
      f'list 0 holds 3 points from $D350; PD_TurnWait = {G.r8(S+0x22)} (low byte of X $10D8), segment ${seg:X}')

print(f'\n{sum(results)} of {len(results)} checks pass')
sys.exit(0 if all(results) else 1)
