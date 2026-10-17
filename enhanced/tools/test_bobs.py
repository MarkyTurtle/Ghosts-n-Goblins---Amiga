"""Test BOB drawing and restoring on the incremental scroller against the original game.

Each frame: the camera moves (random walk), a fresh set of BOBs (test graphics with
transparent holes, 16-64 px wide) is placed in and around the view, partly off every edge
and across the ring's wrap line. The original game redraws, queues the same draw list and
runs its own DrawBobs; the enhanced code brings the pristine buffer and one of two display
buffers up to date, restores that buffer's previous BOBs from the pristine buffer
(ScrRestore) and draws the list (ScrDrawBobs). The displayed playfields must be equal.

The shootable scenery (gravestones on levels 0 and 2) is set up from the level's item list
as the game does, so the original draws it on every redraw (DrawSceneryOnRedraw) and the
enhanced code into the pristine buffer (ScrDrawScenery).

The original DrawBob has a bug the enhanced code does not copy: when a BOB is clipped at the
top of the screen buffer it skips 2 x the graphics lines it should (mulu d7,d2 at $BAF4, with
d7 = twice the words per line), so the visible part shows the wrong lines. The reference here
runs the original with that one instruction corrected (mulu d6,d2); DrawSceneryOnRedraw has the same bug at $C2EA.
   python3 enhanced/tools/test_bobs.py [frames per level]"""
import os, random, sys
import numpy as np
from original import Original, G_
from amiga import GLOBALS
from test_scroll import ORG, BIN, assemble, bounds

FULL, SCROLL, COPPER, RESTORE, DRAWBOBS = ORG, ORG+4, ORG+8, ORG+12, ORG+16
BUF_SIZE = 180*256+1040
BUFS = [0x37468+i*BUF_SIZE for i in range(3)]           # pristine, display A, display B
RECS = [0x79000, 0x79040, 0x79080]
RLISTS = [0, 0x79200, 0x79500]
LIST, GFX, COPLIST = 0x79600, 0x78000, 0x79100
DRAWBOBS_ORIG, SETBPL, SHOWBACK, REDRAW, CAMERAJUMP = 0xBA3E, 0x789A, 0x80DC, 0xBFDE, 0x8046
SIZES = [(16, 16), (32, 24), (48, 32), (64, 20), (32, 48), (16, 64)]

def make_gfx(rnd):
    """test frames: line-interleaved, 5 planes, a coloured pattern with transparent holes"""
    frames, data = [], bytearray()
    for w, h in SIZES:
        ww = w // 16
        img = np.zeros((h, w), dtype=np.uint8)
        for y in range(h):
            for x in range(w):
                inside = (x-w/2)**2/(w/2)**2 + (y-h/2)**2/(h/2)**2 < 1.0
                img[y, x] = 0 if not inside or (x+y) % 7 == 0 else 1 + (x//4 + y//3 + rnd.randrange(3)) % 31
        frames.append((GFX+len(data), w, h))
        for y in range(h):
            for p in range(5):
                bits = (img[y] >> p) & 1
                data += np.packbits(bits).tobytes()
    return frames, bytes(data)

class Both:
    def __init__(self, level, rnd):
        self.o = Original(level); self.e = Original(level)
        for m in (self.o, self.e):                      # the level's items and small BOBs, as the game sets them up
            m.call(0xC476, a1=0x7FA6)                   # LoadFile: the small BOB file
            m.run(0x687E, 0x68A0)                       # LoadLevel: its frame table (g_SmallBobSets)
            m.run(0x694E, 0x6982)                       # SetupLevel: level bounds and origin
            m.run(0x6ACA, 0x6B34)                       # SetupLevel: g_Items from LevelItemLists
        self.o.u.mem_write(0xBAF4, bytes.fromhex('c4c6'))   # fix the top-clip bug in the reference (DrawBob)
        self.o.u.mem_write(0xC2EA, bytes.fromhex('c4c6'))   # and the same bug in DrawSceneryOnRedraw
        self.frames, data = make_gfx(rnd)
        for m in (self.o, self.e): m.u.mem_write(GFX, data)
        e = self.e
        e.u.mem_write(ORG, open(BIN, 'rb').read())
        e.u.mem_write(BUFS[0], bytes(3*BUF_SIZE))
        for i, (r, b) in enumerate(zip(RECS, BUFS)):
            e.u.mem_write(r, bytes(0x40)); e.w32(r, b)
            if i:
                e.w32(r+14, RECS[0])                    # buf_Source = the pristine buffer
                e.w32(r+18, RLISTS[i]); e.w32(r+22, RLISTS[i])

    def entries(self, bobs):
        out = b''
        for (x, y, k) in bobs:
            addr, w, h = self.frames[k]
            out += bytes(np.array([x, y, w, h], dtype='>i2').tobytes()) + addr.to_bytes(4, 'big')
        return out

    def original(self, cx, cy, bobs):
        o = self.o; g = lambda n: GLOBALS+G_[n]
        o.w16(g('g_NewTileX'), cx >> 4); o.w16(g('g_NewTileY'), cy >> 4)
        o.call(REDRAW)
        o.w16(g('g_PendFineX'), cx & 15); o.w16(g('g_PendFineY'), cy & 15)
        o.call(CAMERAJUMP)
        lst = self.entries(bobs)
        start = g('g_SaveBufA') - len(lst)
        o.u.mem_write(start, lst); o.w32(g('g_BlitListPtr'), start)
        o.call(DRAWBOBS_ORIG)
        o.call(SETBPL); o.call(SHOWBACK)
        return o.render()[16:]

    def enhanced(self, k, cx, cy, bobs):
        e = self.e; rec = RECS[1+k]
        e.blits = e.blit_words = 0
        e.call(SCROLL, a0=RECS[0], d0=cx, d1=cy)       # pristine: new edges from the tiles
        e.call(SCROLL, a0=rec, d0=cx, d1=cy)           # display buffer: new edges from the pristine one
        e.call(RESTORE, a0=rec)
        lst = self.entries(bobs)
        e.u.mem_write(LIST, lst)
        e.call(DRAWBOBS, a0=rec, a3=LIST, a5=LIST+len(lst))
        e.call(COPPER, a0=rec, a1=COPLIST, d0=cx, d1=cy)
        e.w32(0xDFF084, COPLIST)
        return e.render()[16:], e.blits, e.blit_words

def main(frames=40):
    assemble()
    total = bad = 0; stats = []
    for level in range(7):
        rnd = random.Random(100+level)
        t = Both(level, rnd)
        W, H = bounds(t.o, level)
        cx, cy = rnd.randrange(0, max(1, W-288)), rnd.randrange(0, max(1, H-256))
        for f in range(frames):
            if f:
                cx = max(0, min(cx+rnd.choice([0, 1, 2, 4, 8, 16, -1, -2, -4, -8, -16, 23]), W-288))
                cy = max(0, min(cy+rnd.choice([0, 0, 1, 2, -1, -2, 5, -5, 16, -16]), max(0, H-256)))
            bobs = []
            for _ in range(rnd.randrange(3, 11)):
                k = rnd.randrange(len(SIZES)); w, h = SIZES[k]
                x = cx + rnd.randrange(-w, 256+16)
                y = cy + 16 + rnd.randrange(-h, 224+8)
                if rnd.random() < 0.3:                   # put some across the ring's wrap line
                    wrap = (cy + 16 + 255) // 256 * 256 - 1   # a world line y with ring line 255
                    y = wrap - rnd.randrange(1, h)
                bobs.append((x, y, k))
            a = t.original(cx, cy, bobs)
            b, nb, nw = t.enhanced(f & 1, cx, cy, bobs)
            total += 1; stats.append((nb, nw, len(bobs)))
            if (a != b).any():
                bad += 1
                print(f'level {level} frame {f} camera ({cx},{cy}): {(a != b).sum()} pixels differ')
                if bad > 5: return 1
    print(f'{total-bad} of {total} frames with BOBs identical to the original display')
    # sweep across the scenery of levels 0 and 2 (right, then back left), checking the
    # gravestones really are in view
    sweep = sweep_bad = with_scenery = 0
    for level, x0, x1, y in ((0, 0, 1900, 0), (2, 0, 1100, 0)):
        rnd = random.Random(level); t = Both(level, rnd)
        bare = Original(level)                           # no items: tells whether scenery is visible
        xs = list(range(x0, x1, 12)) + list(range(x1, x0, -20))
        for i, cx in enumerate(xs):
            a = t.original(cx, y, [])
            b, _, _ = t.enhanced(i & 1, cx, y, [])
            c = bare.show(cx >> 4, y >> 4, cx & 15, y & 15)[16:]
            sweep += 1; with_scenery += bool((a != c).any())
            if (a != b).any():
                sweep_bad += 1; print(f'sweep level {level} x {cx}: {(a != b).sum()} pixels differ')
    print(f'{sweep-sweep_bad} of {sweep} sweep frames identical ({with_scenery} with scenery in view)')
    return 1 if bad or sweep_bad else 0

if __name__ == '__main__':
    sys.exit(main(int(sys.argv[1]) if len(sys.argv) > 1 else 40))
