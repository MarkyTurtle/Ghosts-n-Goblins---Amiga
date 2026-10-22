"""Redundancy in the graphics and map tables, for the space-saving notes in enhanced/docs/TODO.md:
enemy BOB frames that are exact mirror images of another frame of the same set, mirrored level
tiles, and how far CellTiles / TileAttr would shrink when recoded.   python3 tools/budget/gfx_redundancy.py"""
import struct, glob
D = open('bin/main_512k.bin', 'rb').read(); B = 0x80
G = open('disk/files/t038-056_enemy_bobs.bin', 'rb').read()
rw = lambda a: struct.unpack('>h', D[a-B:a-B+2])[0]
ruw = lambda a: struct.unpack('>H', D[a-B:a-B+2])[0]
rl = lambda a: struct.unpack('>L', D[a-B:a-B+4])[0]
REV = bytes(int(f'{b:08b}'[::-1], 2) for b in range(256))
def hflip(d, wb, lines):
    return b''.join(d[l*wb:(l+1)*wb][::-1].translate(REV) for l in range(lines))

# ---- enemy BOB sets: frames that mirror another frame
S = 0x4FF0                                         # BobFrameDescs; set 19 bat, 20 red crow
NAMES = ['WoodyPig', 'Crow', 'PetiteDevil', 'FlyingKnight', 'BlueKiller', 'RedArremer', 'Satan',
         'Magician', 'Unicorn', 'Skeleton', 'BigMan', 'Zombie', 'Dragon', 'Astaroth', 'Fire',
         'Princess', 'Type16', 'Plant', 'FirePillar', 'bat', 'red crow']
sizes = [ruw(0x67C4+2*i) for i in range(21)]; offs = [rl(0x53AA+4*i) for i in range(21)]
tables = {i: S+2*i+rw(S+2*i) for i in range(19) if rw(S+2*i)}
tables[19], tables[20] = 0x538E, 0x5056
ends = sorted(set(tables.values())) + [0x53AA]
print('enemy BOB set   bytes  frames  bytes that mirror another frame')
total = saved = 0
for s in range(21):
    if s not in tables: continue
    t = tables[s]; n = (min(x for x in ends if x > t)-t)//4
    fr = {ruw(t+4*k): D[t+4*k+3-B] for k in range(n)}
    blk = G[offs[s]:offs[s]+sizes[s]]; so = sorted(fr) + [sizes[s]]
    imgs = {}
    for i, o in enumerate(so[:-1]):
        size, h = so[i+1]-o, fr[o]
        if h and size % (5*h) == 0: imgs[o] = (size//(5*h), h, blk[o:o+size])
    keys = {(wb, h, d): o for o, (wb, h, d) in imgs.items()}
    mirrored = {o for o, (wb, h, d) in imgs.items()
                if keys.get((wb, h, hflip(d, wb, 5*h)), o) != o}
    m = sum(len(imgs[o][2]) for o in mirrored)//2    # one of each pair can go
    total += sizes[s]; saved += m
    print(f'{NAMES[s]:14s} {sizes[s]:6,d} {n:6d} {m:9,d}')
print(f'{"all":14s} {total:6,d} {"":6s} {saved:9,d}  ({100*saved/total:.0f}%)')

# ---- level tiles that mirror an earlier tile
print('\nlevel tile file              tiles  mirrors of an earlier tile')
for f in sorted(glob.glob('disk/files/t*_level*_tiles.bin')):
    d = open(f, 'rb').read(); tiles = [d[160*i:160*i+160] for i in range(len(d)//160)]
    seen = set(); m = 0
    for t in tiles:
        fl = hflip(t, 2, 80)
        if fl in seen and fl != t: m += 1
        seen.add(t)
    print(f'{f.split("/")[-1]:28s} {len(tiles):6d} {m:6d}')

# ---- CellTiles recoded as metatiles
CT = 0x1222C
cells = [D[CT-B+256*c:CT-B+256*c+256] for c in range(103)]
for k in (2, 4):
    blocks = {bytes(c[16*(y+j)+x+i] for j in range(k) for i in range(k))
              for c in cells for y in range(0, 16, k) for x in range(0, 16, k)}
    idx = 1 if len(blocks) <= 256 else 2
    print(f'CellTiles 26,368 bytes as {k}x{k} metatiles: {len(blocks)} distinct, '
          f'{103*(16//k)**2*idx + k*k*len(blocks):,d} bytes')
MBI, BT, TA = 0xA4, 0x114, 0x1B14
used = {(D[MBI-B+c] >> 3, t) for c in range(104) for t in D[BT-B+64*c:BT-B+64*c+64]}
recs = {D[TA-B+0x800*b+8*t:TA-B+0x800*b+8*t+8] for b, t in used}
print(f'TileAttr 8,192 bytes: {len(used)} records used, {len(recs)} distinct')
