"""Per-level memory needs of the 512K build: the map / tile tables each level uses (now all
resident in the main program), its tile file, its enemy BOB sets (as stored, and doubled if
pre-masked as in the 1MB build) and its small BOBs.   python3 tools/budget/level_sizes.py
Addresses are the 512K program's (bin/main_512k.bin, loaded at $80); see gng_main.s."""
import struct, sys
D = open(sys.argv[1] if len(sys.argv) > 1 else 'bin/main_512k.bin', 'rb').read(); B = 0x80
rb = lambda a: D[a-B]
rw = lambda a: struct.unpack('>H', D[a-B:a-B+2])[0]
rl = lambda a: struct.unpack('>L', D[a-B:a-B+4])[0]
WM, MBI, BT, LMT, LB = 0x44D6, 0xA4, 0x114, 0x44BA, 0x4466      # WorldMap, MapBlockIndex, BlockTiles, LevelMapTable, LevelBounds
BOBSIZES, LEVELBOBS, SMALLSIZES, LEVELSMALL, FILES = 0x67C4, 0x6802, 0x67EE, 0x681E, 0x8000   # FileLevel0
print('level  cells  CellTiles  BlockTiles  TileAttr  tables | tile file  enemy BOBs  pre-masked  1-plane mask  small BOBs')
tot_tables = 26368 + 6656 + 8192
for l in range(7):
    r0, c0 = divmod(rw(LMT+2*l) + LMT - WM, 32)
    x0, x1, y1, y0 = D[LB-B+4*l:LB-B+4*l+4]
    cells = {rb(WM+32*r+c) for r in range(r0, min(r0+y1-y0+1, 11)) for c in range(c0, min(c0+x1-x0+1, 32))}
    if l == 6: cells.add(rb(WM+352))                                   # the throne room cell
    tiles = {(rb(MBI+c) >> 3, t) for c in cells for t in D[BT-B+64*c:BT-B+64*c+64]}
    ct, bt, ta = 256*len([c for c in cells if c < 0x67]), 64*len(cells), 8*len(tiles)
    m = rl(LEVELBOBS+4*l); eb = sum(rw(BOBSIZES+2*i) for i in range(21) if m >> i & 1)
    sm = rw(LEVELSMALL+2*l); sb = sum(rw(SMALLSIZES+2*i) for i in range(10) if sm >> i & 1)
    tf = rl(FILES+10*l+4)
    print(f'{l:5d} {len(cells):6d} {ct:10,d} {bt:11,d} {ta:9,d} {ct+bt+ta:7,d} | {tf:9,d} {eb:11,d} {2*eb:11,d} {eb//5:13,d} {sb:11,d}')
print(f'all levels resident today: CellTiles 26,368 + BlockTiles 6,656 + TileAttr 8,192 = {tot_tables:,d} bytes')
