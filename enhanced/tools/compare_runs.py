"""Run the original and the enhanced game side by side (512K or 1MB build) in the emulator, with the same input,
and compare what they show, frame by frame (the whole display, HUD included).

In the emulator a background redraw always finishes at once, so the original camera almost
always reaches its target just as the enhanced one does, and the two games stay in step:
same logic, same pictures. A difference in the picture while the game state is still the same
is a drawing difference. The reference has the DrawBob top-clip bug fixed (see test_bobs.py),
since the enhanced build draws those BOBs correctly.

  python3 compare_runs.py [frames] [seed] [--png DIR] [--level N] [--teleport N] [--build 512k|1mb]"""
import os, sys, time
import numpy as np
from game import GameRun, script_start, enhanced
from check_game import play_script

STATE = ('g_GameState', 1), ('g_SubState', 1), ('g_Level', 2), ('g_ArthurX', 2), ('g_ArthurY', 2), \
        ('g_ScrollTileX', 2), ('g_ScrollFineX', 2), ('g_ScrollTileY', 2), ('g_ScrollFineY', 2), \
        ('g_Lives', 1), ('g_Score', 4)


def camera(m):
    return (m.g('g_ScrollTileX')*16 + m.g('g_ScrollFineX'), m.g('g_ScrollTileY')*16 + m.g('g_ScrollFineY'))


def state(m):
    s = {k: m.g(k, n) for k, n in STATE}
    s['camera'] = camera(m)
    s['origin'] = (s.pop('g_ScrollTileX'), s.pop('g_ScrollTileY'))
    for k in ('g_ScrollFineX', 'g_ScrollFineY'): del s[k]
    return s


def main(frames=3000, seed=1, png=None, level=None, teleport=0, build='512k', pair=None, raw=True):
    """pair: (reference, tested) machines to compare as they are, instead of the original and
    the enhanced build; raw: also compare the camera tables byte for byte (not when the two
    programs are at different addresses: the tables hold pointers)"""
    if pair:
        orig, enh = pair
    else:
        orig, enh = GameRun(build=build), enhanced(build)
    if build == '512k' and not pair:
        orig.u.mem_write(0xBAF4, bytes.fromhex('c4c6'))  # DrawBob top-clip fix (the 1MB build is right)
        orig.u.mem_write(0xC2EA, bytes.fromhex('c4c6'))  # and in DrawSceneryOnRedraw
        orig.u.mem_write(0x6E76, bytes.fromhex('4e71'*5))  # draw every frame, as the enhanced 512K build
                                                           # (src/fps50_patches.s) and the 1MB program
    for m in (orig, enh): m.boot()
    inputs = list(script_start()); play = play_script(seed)
    same = differ = 0; diverged = None; t = time.time()
    states = set(); levels = set(); first_diffs = []; ys = set()
    started = playing = False
    import random; trnd = random.Random(seed)
    for f in range(frames):
        joy, fire = inputs[f] if f < len(inputs) else next(play)
        for m in (orig, enh): m.frame(joy, fire)
        if level is not None and not started and m.g('g_GameState', 1) == 0 and m.g('g_SubState', 1) == 2:
            started = True                                 # --level: once level 0 has started, load that level
            for m in (orig, enh):                          # instead; lives never run out (the game's cheat flag)
                m.w16(m.G['g_Level'], level); m.w8(m.G['g_CheatOn'], 0xFF)
                for k in ('g_SubState', 'g_SubState2', 'g_SubState3'): m.w8(m.G[k], 0)
        if teleport and f % teleport == 0 and orig.g('g_GameState', 1) == 0 and orig.g('g_SubState', 1) == 2:
            # --teleport N: every N frames put Arthur somewhere else in the level (both games), so
            # the camera jumps and scrolls vertically too
            w, h = orig.g('g_LevelWidth'), orig.g('g_LevelHeight')
            x, y = trnd.randrange(32, max(33, w + 200)), trnd.randrange(40, max(41, h + 200))
            for m in (orig, enh): m.w16(m.G['g_ArthurX'], x); m.w16(m.G['g_ArthurY'], y)
        so, se = state(orig), state(enh)
        co, ce = so, se
        if not raw and so['g_SubState'] == se['g_SubState'] == 2: playing = True
        if not raw and not playing:      # Arthur is set up with the level (SetupLevel)
            co, ce = ({k: v for k, v in x.items() if k not in ('g_ArthurX', 'g_ArthurY')} for x in (so, se))
        if not raw and so['g_GameState'] == se['g_GameState'] == 1:
            co = ce = None      # attract mode: programs with different file tails start with
            # different junk in the globals the game has not set yet (Arthur, lives); until a
            # game starts only the picture counts
        if co != ce or (raw and orig.rd(orig.G['g_CamMinY'], 0x60) != enh.rd(enh.G['g_CamMinY'], 0x60)):
            diverged = (f, so, se); break
        states.add((so['g_GameState'], so['g_SubState'])); levels.add(so['g_Level'])
        a, b = orig.render(), enh.render()
        if (a == b).all(): same += 1
        else:
            differ += 1
            if os.environ.get('DIFF_LOG') and so['g_GameState'] != 1:
                print(f'  play diff frame {f}: {int((a != b).sum())} px, state {so["g_GameState"]}/{so["g_SubState"]}', flush=True)
            if len(first_diffs) < 10 or (png and so['g_GameState'] == 0 and so['g_SubState'] == 2):
                first_diffs.append((f, int((a != b).sum()), so))
                if png:
                    os.makedirs(png, exist_ok=True)
                    orig.save_png(a, f'{png}/f{f:05d}_orig.png'); enh.save_png(b, f'{png}/f{f:05d}_enh.png')
        ys.add(so['camera'][1] >> 4)
        if f % 500 == 0:
            print(f'  frame {f}: state {so["g_GameState"]}/{so["g_SubState"]} level {so["g_Level"]} '
                  f'camera {so["camera"]} lives {so["g_Lives"]}, {time.time()-t:.0f}s', flush=True)
    n = same + differ
    print(f'{n} frames in step (game states {sorted(states)}, levels {sorted(levels)}): '
          f'{same} identical displays, {differ} different; camera tile rows visited: {len(ys)}')
    for f, d, s in first_diffs:
        print(f'  frame {f}: {d} pixels differ, state {s}')
    if diverged:
        f, so, se = diverged
        print(f'the games went out of step at frame {f}:')
        print('  original:', so); print('  enhanced:', se)
    return 1 if differ else 0


if __name__ == '__main__':
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    png = sys.argv[sys.argv.index('--png')+1] if '--png' in sys.argv else None
    if png in args: args.remove(png)
    lv = int(sys.argv[sys.argv.index('--level')+1]) if '--level' in sys.argv else None
    if lv is not None: args.remove(str(lv))
    tp = int(sys.argv[sys.argv.index('--teleport')+1]) if '--teleport' in sys.argv else 0
    if tp: args.remove(str(tp))
    build = sys.argv[sys.argv.index('--build')+1] if '--build' in sys.argv else '512k'
    if build in args: args.remove(build)
    sys.exit(main(int(args[0]) if args else 3000, int(args[1]) if len(args) > 1 else 1, png, lv, tp, build))
