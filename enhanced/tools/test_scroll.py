"""Test the incremental scroller (src/scroll.s) against the original game.

For a random camera walk through each level, two buffers are updated alternately with
ScrScrollTo (as double buffering would) and shown with ScrBuildCopper; every displayed
frame must equal the original game's display at the same camera position, drawn by its
own RedrawScreen. Both run in the emulator harness (amiga.py).
   python3 enhanced/tools/test_scroll.py [steps per level]"""
import os, random, struct, sys, subprocess
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
from original import Original, G_
from amiga import GLOBALS

ORG = 0x7A000
FULL, SCROLL, COPPER = ORG, ORG+4, ORG+8
BUF_SIZE = 180*256+1040
BUFS = [0x37468, 0x37468+BUF_SIZE]
RECS = [0x79000, 0x79040]                  # buffer records (buf_SIZEOF is under $40)
LIST = 0x79100
BIN = os.path.join(HERE, '..', 'build', 'scroll.bin')

def assemble():
    src = os.path.join(HERE, '..', 'src', 'scroll.s')
    vasm = os.environ.get('VASM', 'vasmm68k_mot')
    os.makedirs(os.path.dirname(BIN), exist_ok=True)
    subprocess.run([vasm, '-Fbin', '-m68000', '-quiet', '-o', BIN, src], check=True)

class Enhanced(Original):
    def __init__(self, level):
        super().__init__(level)
        self.u.mem_write(ORG, open(BIN, 'rb').read())
        for r, b in zip(RECS, BUFS):
            self.u.mem_write(r, bytes(0x40)); self.w32(r, b)
        self.u.mem_write(BUFS[0], bytes(2*BUF_SIZE))
    def show_cam(self, k, cx, cy):
        self.blits = self.blit_words = 0
        self.call(SCROLL, a0=RECS[k], d0=cx & 0xFFFF, d1=cy & 0xFFFF)
        drawn = (self.blits, self.blit_words)
        self.call(COPPER, a0=RECS[k], a1=LIST, d0=cx & 0xFFFF, d1=cy & 0xFFFF)
        self.w32(0xDFF084, LIST)                      # COP2LC
        return self.render(), drawn

def bounds(o, level):
    import struct
    D = bytes(o.u.mem_read(0x4466+4*level, 4))
    x0, x1, y1, y0 = D
    return (x1-x0+1)*256, (y1-y0+1)*256

def main(steps=60):
    assemble()
    total = bad = 0; blits = []
    for level in range(7):
        ref = Original(level); enh = Enhanced(level)
        W, H = bounds(ref, level)
        rnd = random.Random(level)
        cx, cy = rnd.randrange(0, max(1, W-288)), rnd.randrange(0, max(1, H-256)) // 16 * 16
        for step in range(steps):
            if step:                                      # walk, mostly small steps, sometimes a jump
                cx += rnd.choice([0, 1, 2, 3, 8, 16, -1, -2, -3, -8, -16, 5, 40])
                cy += rnd.choice([0, 0, 0, 1, 2, -1, -2, 7, -7, 16, -16])
                cx = max(0, min(cx, W-288)); cy = max(0, min(cy, max(0, H-256)))
            a = ref.show(cx >> 4, cy >> 4, cx & 15, cy & 15)[16:]
            b, n = enh.show_cam(step & 1, cx, cy)
            b = b[16:]
            total += 1; blits.append(n)
            if (a != b).any():
                bad += 1
                print(f'level {level} step {step} camera ({cx},{cy}): {(a != b).sum()} pixels differ')
                if bad > 5: return 1
    moved = [b for b in blits if b[0]]
    print(f'{total-bad} of {total} frames identical to the original display')
    print(f'frames that drew something: {len(moved)}; blitted words per such frame: median '
          f'{int(np.median([w for _, w in moved]))}, max {max(w for _, w in moved)} (a full draw)')
    print('the original redraws the whole buffer instead: 288 blits, 23,040 words, plus a 46,080-byte CPU copy')
    return 1 if bad else 0

if __name__ == '__main__':
    sys.exit(main(int(sys.argv[1]) if len(sys.argv) > 1 else 60))
