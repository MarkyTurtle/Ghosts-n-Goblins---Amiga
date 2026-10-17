"""How much enemy graphics each part of a level needs at once - for a cache that builds masked
graphics on demand. For every camera cell (256 x 256 px) of a level, the enemy types that can be
on screen are taken from: the spawners of the zones within +-RADIUS cells, the placed enemies
(LevelEnemyLists) within +-RADIUS cells, plus a few rules from the code: a Blue Killer can turn
into a Red Arremer, the Magician appears from shot gravestones (item type 1), the Crow's
graphics set depends on its param (0-2 bat, 3 red crow), and level 0 opens with the Satan /
Princess cut-scene. Spawners of the types that keep running across zones (ZoneFlags 0: bosses,
Red Arremer, Big Man) are counted from their zone to the end of the level ("sticky").
   python3 tools/budget/enemy_windows.py [radius in cells, default 1]
This is an estimate from the tables, not a trace of play."""
import struct, sys
D = open('bin/main_512k.bin', 'rb').read(); B = 0x80
R = int(sys.argv[1]) if len(sys.argv) > 1 else 1
rb = lambda a: D[a-B]
rw = lambda a: struct.unpack('>h', D[a-B:a-B+2])[0]
ruw = lambda a: struct.unpack('>H', D[a-B:a-B+2])[0]
rl = lambda a: struct.unpack('>L', D[a-B:a-B+4])[0]
WM, MZT, ZS, LMT, LB, ET, IT = 0x44D6, 0x4637, 0x4798, 0x44BA, 0x4466, 0x3B22, 0x3B14
SIZES = [ruw(0x67C4+2*i) for i in range(21)]
STICKY = {5, 6, 8, 10, 12, 13}             # Red Arremer, Satan, Unicorn, Big Man, Dragon, Astaroth
NAMES = ['WoodyPig', 'Crow', 'PetiteDevil', 'FlyingKnight', 'BlueKiller', 'RedArremer', 'Satan',
         'Magician', 'Unicorn', 'Skeleton', 'BigMan', 'Zombie', 'Dragon', 'Astaroth', 'Fire',
         'Princess', 'Type16', 'Plant', 'FirePillar', 'bat', 'red crow']

def sets_of(t, param=None, levelmask=0):
    if t == 1:                                # the Crow: bat / red crow / own set by param
        if param is None: return {s for s in (1, 19, 20) if levelmask >> s & 1}
        return {19} if param < 3 else {20} if param == 3 else {1}
    out = {t}
    if t == 4: out.add(5)                     # a Blue Killer turns into a Red Arremer
    return out

def placements(table, l):
    a = table+2*l+rw(table+2*l); n = ruw(a)
    return [(rb(a+2+6*k), rb(a+3+6*k), ruw(a+4+6*k), ruw(a+6+6*k)) for k in range(n)]

print(f'radius {R} cell(s) around the camera; sizes are the graphics as stored (pre-masked = x2)')
print('level  all sets  peak window  (x2 pre-masked: all / peak)  peak at cell  types in the peak window')
for l in range(7):
    mask = rl(0x6802+4*l)
    off = rw(LMT+2*l)+LMT-WM; r0, c0 = divmod(off, 32)
    x0, x1, y1, y0 = D[LB-B+4*l:LB-B+4*l+4]
    h, w = y1-y0+1, x1-x0+1
    if l == 6:                                # the throne room: its own map cell, world cell (y0, x0)
        cellsxy = [(y0, x0)]; zone = lambda r, c: rb(MZT+352)
    else:
        cellsxy = [(r, c) for r in range(r0, min(r0+h, 11)) for c in range(c0, min(c0+w, 32))]
        zone = lambda r, c: rb(MZT+32*r+c)
    def zone_sets(z):
        la = ZS+z+rb(ZS+z); out = set()
        for k in range(rb(la)):
            t = rb(la+1+2*k) >> 4
            out |= sets_of(t, None, mask)
        return out
    enemies = placements(ET, l); items = placements(IT, l)
    sticky = set(); best = (0, None, set())
    for (r, c) in sorted(cellsxy, key=lambda rc: (rc[1], rc[0])):
        win = set()
        for (r2, c2) in cellsxy:
            if abs(r2-r) <= R and abs(c2-c) <= R:
                zs = zone_sets(zone(r2, c2))
                win |= zs
                if (r2, c2) == (r, c): sticky |= zs & STICKY
        near = lambda x, y: abs(x//256-c) <= R and abs(y//256-r) <= R    # placements are in world pixels
        for t, p, x, y in enemies:
            if near(x, y): win |= sets_of(t, p, mask)
        for t, p, x, y in items:
            if t == 1 and near(x, y): win.add(7)
        if l == 0 and c == c0: win |= {6, 15}       # the opening cut-scene
        win |= sticky
        win &= {s for s in range(21) if mask >> s & 1}
        size = sum(SIZES[s] for s in win)
        if size > best[0]: best = (size, (r, c), win)
    allsz = sum(SIZES[s] for s in range(21) if mask >> s & 1)
    print(f'{l:5d} {allsz:9,d} {best[0]:12,d}   {2*allsz:9,d} / {2*best[0]:9,d}      {str(best[1]):12s} '
          + ', '.join(NAMES[s] for s in sorted(best[2])))
