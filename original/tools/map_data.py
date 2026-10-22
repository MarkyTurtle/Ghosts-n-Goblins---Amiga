"""The map and tile tables as readable source for gen.py's DATA_BLOCKS (512K addresses,
main.bin loaded at $80). build(D) returns a list of (start, end, lines, labels).

  MapBlockIndex  $00A4  112 bytes: per map cell type, TileAttr bank * 8
  BlockTiles     $0114  64 bytes per cell type ($00-$67): the 8 x 8 collision tiles
                        (32 x 32 px), column by column, each column bottom to top
  TileAttr       $1B14  4 banks x 256 tiles x 8 bytes: four quadrant profiles, four flags
  WallProfileR / WallProfileL / FloorProfile  $402A-$432A: 256 bytes each, indexed with a
                        sign-extended profile byte, so the label is in the middle
  WorldMap       $44D6  32 x 11 cells, bottom row first, plus the throne room
  CellTiles      $1222C 256 bytes per cell type ($00-$66): 16 x 16 graphics tiles, top row first
"""
import struct

WM, MBI, BT, TA, WR, CT, CT_END = 0x44D6, 0xA4, 0x114, 0x1B14, 0x40AA, 0x1222C, 0x1892C
LB = 0x4466  # LevelBounds

def build(D, B=0x80):
    rb = lambda a: D[a-B]
    sx = lambda p: p-256 if p & 0x80 else p
    hx = lambda bs: ','.join(f'${b:02X}' for b in bs)
    blocks = []

    # which levels use each map cell type
    # level areas: origin cell from LevelMapTable (offsets from the table at $44BA),
    # size from LevelBounds (x0, x1, y1, y0 in cells)
    areas = []
    for l in range(7):
        off = struct.unpack('>H', D[0x44BA-B+2*l:0x44BA-B+2*l+2])[0] + 0x44BA - WM
        x0, x1, y1, y0 = D[LB-B+4*l:LB-B+4*l+4]
        r0, c0 = divmod(off, 32)
        areas.append((r0, c0, y1-y0+1, x1-x0+1))
    def level_at(r, c):
        return [l for l, (r0, c0, h, w) in enumerate(areas) if l < 6 and r0 <= r < r0+h and c0 <= c < c0+w]
    used = {}
    for r in range(11):
        for c in range(32):
            cell = rb(WM+32*r+c)
            for l in level_at(r, c): used.setdefault(cell, set()).add(l)
    used.setdefault(rb(WM+352), set()).add(6)
    def lv(cell):
        s = sorted(used.get(cell, ()))
        return (('level ' if len(s) == 1 else 'levels ')+', '.join(map(str, s))) if s else 'not inside any level'

    # ---- MapBlockIndex + BlockTiles
    L = ['MapBlockIndex:']
    for i in range(0, 112, 16):
        L.append(f'\tdc.b\t{hx(D[MBI-B+i:MBI-B+i+16])}\t; cells ${i:02X}-${i+15:02X}')
    L.append('BlockTiles:')
    for cell in range(104):
        bank = rb(MBI+cell) >> 3
        L.append(f'; cell ${cell:02X} - TileAttr bank {bank} - {lv(cell)}' + ('  (empty cell)' if cell == 0x67 else ''))
        for col in range(8):
            a = BT+64*cell+8*col
            L.append(f'\tdc.b\t{hx(D[a-B:a-B+8])}\t; column {col}, bottom to top')
    blocks.append((MBI, TA, L, {'MapBlockIndex': MBI, 'BlockTiles': BT}))

    # ---- TileAttr
    FP = 0x42AA
    def quad(p):
        if 0x40 <= p <= 0x7D: return 'L'
        h = rb(FP+sx(p))
        return str(h) if h else '-'
    maxtile = {}
    for cell in range(104):
        bank = rb(MBI+cell) >> 3
        m = max(D[BT-B+64*cell:BT-B+64*cell+64])
        maxtile[bank] = max(maxtile.get(bank, 0), m)
    L = ['TileAttr:']
    for bank in range(4):
        L.append(f'; bank {bank} (tiles used up to ${maxtile.get(bank, 0):02X})')
        for t in range(256):
            a = TA+0x800*bank+8*t
            p, f = D[a-B:a-B+4], D[a-B+4:a-B+8]
            q = ' '.join(f'{quad(x):>2}' for x in p)
            bg = '  bg' if any(x & 0xC0 for x in f) else ''
            un = '  (unused)' if t > maxtile.get(bank, 0) else ''
            L.append(f'\tdc.b\t{hx(p)}, {hx(f)}\t; ${t:02X}  floor {q}{bg}{un}')
    blocks.append((TA, TA+0x2000, L, {'TileAttr': TA}))

    # ---- profile tables
    L = []
    names = [(0x40AA, 'WallProfileR'), (0x41AA, 'WallProfileL'), (0x42AA, 'FloorProfile')]
    for lab, nm in names:
        for i in range(-128, 128, 16):
            if i == 0: L.append(f'{nm}:')
            a = lab+i
            L.append(f'\tdc.b\t{hx(D[a-B:a-B+16])}\t; {nm} profiles ${i & 0xFF:02X}-${(i+15) & 0xFF:02X}')
    blocks.append((0x402A, 0x432A, L, {nm: lab for lab, nm in names}))

    # ---- (width, height) of each graphics set - used only by the 1MB build's BuildMaskedGfx
    sets = [(0x4002, 'CacheSizesSmallBobs', 10, 0x402A),
            (0x432A, 'CacheSizesEnemyGfx', 39, None), (0x43C6, 'CacheSizesItemGfx2', 3, None),
            (0x43D2, 'CacheSizesEnemyShots', 3, None), (0x43DE, 'CacheSizesItems', 4, 0x43EE)]
    cur = None
    for a0, nm, n, end in sets:
        if cur is None: start, L, lab = a0, [], {}
        L.append(f'{nm}:'); lab[nm] = a0
        for k in range(n):
            w, h = struct.unpack('>HH', D[a0-B+4*k:a0-B+4*k+4])
            L.append(f'\tdc.w\t${w:04X},${h:04X}\t; set {k}: {w} x {h} px')
        cur = a0+4*n
        if end is not None:
            assert cur == end
            blocks.append((start, end, L, lab)); cur = None

    # ---- WorldMap
    L = ['WorldMap:']
    for r in range(11):
        a = WM+32*r
        ls = sorted({l for c in range(32) for l in level_at(r, c)})
        L.append(f'\tdc.b\t{hx(D[a-B:a-B+32])}\t; row {r}' + ((' - level ' if len(ls) == 1 else ' - levels ')+', '.join(map(str, ls)) if ls else ''))
    L.append(f'\tdc.b\t${rb(WM+352):02X}\t; the throne room (level 6)')
    blocks.append((WM, WM+353, L, {'WorldMap': WM}))

    # ---- CellTiles
    L = ['CellTiles:']
    for cell in range((CT_END-CT)//256):
        note = '  (level 1 draws these tiles from the second bank: +256)' if cell in (0x1D, 0x1F) else ''
        L.append(f'; cell ${cell:02X} - {lv(cell)}{note}')
        for row in range(16):
            a = CT+256*cell+16*row
            L.append(f'\tdc.b\t{hx(D[a-B:a-B+16])}' + ('\t; top row' if row == 0 else ''))
    blocks.append((CT, CT_END, L, {'CellTiles': CT}))
    return blocks

if __name__ == '__main__':
    import sys
    D = open(sys.argv[1], 'rb').read()
    for s, e, l, lab in build(D):
        print(f'{s:X}-{e:X}: {len(l)} lines')
