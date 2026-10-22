"""Enemy / shot animation scripts, direction tables, movement tables and hit boxes as
readable source for gen.py's DATA_BLOCKS (512K addresses, main.bin loaded at $80).

Animation script (Animate): entries of frame.b, ticks.b. Ticks with bit 7 set end the
script: a word offset follows and the script continues at that address (a loop, or a
jump into another script). Written with the AF / AL macros (prelude.s).
Direction table: word offsets, each relative to itself, indexed by O_Dir (SetAnimIndexed
and friends): dc.w Target-*.
Movement table (ApplyMoveTable): (dx, dy) words in 8.8 pixels per frame, Y up, indexed by
O_Dir; the 16-direction tables go clockwise on screen from 0 = right (4 down, 8 left, 12 up).
Box table: (x offset, width, y offset, height) words per type: hit when
(x - x2 + xoff) <= width (unsigned) and the same for y.
build(D) returns a list of (start, end, lines, labels)."""
import struct

ANIM_REGIONS = [
 # start, end, {table address: entries}, {address: name}
 (0x922E, 0x92A6, {0x922E: 2, 0x9252: 2, 0x925E: 2, 0x9276: 2, 0x9282: 2, 0x928E: 4},
  {0x922E: 'Torch_Anim', 0x9246: 'Torch_AnimBurn', 0x924C: 'Torch_AnimBurnSmall',
   0x9252: 'Lance_Anim', 0x925E: 'Axe_Anim', 0x9276: 'Cross_Anim', 0x9282: 'Dagger_Anim',
   0x928E: 'Debris_Anim'}),
 (0xC83E, 0xC87E, {},
  {0xC83E: 'WoodyPig_AnimEmergeA', 0xC848: 'WoodyPig_AnimFlyA', 0xC84E: 'WoodyPig_AnimTurnA',
   0xC856: 'WoodyPig_AnimDropA', 0xC85E: 'WoodyPig_AnimEmergeB', 0xC868: 'WoodyPig_AnimFlyB',
   0xC86E: 'WoodyPig_AnimTurnB', 0xC876: 'WoodyPig_AnimDropB'}),
 (0xD058, 0xD160, {0xD058: 2, 0xD07C: 2, 0xD080: 2, 0xD084: 2, 0xD088: 4, 0xD090: 4,
                   0xD0F0: 2, 0xD0F4: 2, 0xD0F8: 4, 0xD100: 4},
  {0xD058: 'Bat_AnimFly', 0xD062: 'Bat_AnimTakeOffA', 0xD072: 'Bat_AnimTakeOffB',
   0xD07C: 'Crow_AnimFlyHigh', 0xD080: 'Crow_AnimFly', 0xD084: 'Bat_PoseTables',
   0xD088: 'Bat_PosesR', 0xD090: 'Bat_PosesL', 0xD0F0: 'Crow_UnrefTable',
   0xD0F4: 'Crow_PoseTables', 0xD0F8: 'Crow_PosesR', 0xD100: 'Crow_PosesL'}),
 (0xD8D4, 0xD960, {0xD8D4: 8},
  {0xD8D4: 'PetiteDevil_TurnAnims', 0xD8E4: 'PetiteDevil_AnimA', 0xD8F2: 'PetiteDevil_AnimB',
   0xD900: 'PetiteDevil_AnimLegs', 0xD922: 'PetiteDevil_AnimStartA',
   0xD926: 'PetiteDevil_AnimRecoilA', 0xD930: 'PetiteDevil_AnimStartB',
   0xD934: 'PetiteDevil_AnimRecoilB', 0xD93E: 'PetiteDevil_AnimFly'}),
 (0xE152, 0xE18E, {0xE152: 2, 0xE176: 2},
  {0xE152: 'BlueKiller_AnimWalk', 0xE16A: 'BlueKiller_AnimDrop', 0xE170: 'BlueKiller_AnimAppear',
   0xE176: 'BlueKiller_AnimWalk2'}),
 (0x12210, 0x1222C, {},
  {0x12210: 'EnemyDie_AnimA', 0x1221E: 'EnemyDie_AnimB'}),
]

MOVE_REGIONS = [
 # start, end, [(address, name or None, entries)], {table address: entries} (direction tables)
 (0xD960, 0xDA38, [(0xD960, 'PetiteDevilMoveTable', 6), (0xD978, 'PetiteDevilMove16', 16),
                   (0xD9B8, 'PetiteDevilMove16Fast', 16), (0xD9F8, 'PetiteDevilMove16Slow', 16)], {}),
 (0xE18E, 0xE1F6, [(0xE196, None, 6), (0xE1AE, None, 6), (0xE1C6, None, 6), (0xE1DE, None, 6)],
  {0xE18E: ('BlueKillerSwoopA', 2), 0xE192: ('BlueKillerSwoopB', 2)}),
]

BOX_TABLES = [
 (0x8E8E, 0x8EEE, 'EnemyShotBoxes', 'enemy shot type'),
 (0x8EEE, 0x8F4E, 'EnemyShotBoxesCrouch', 'enemy shot type'),
 (0x97AA, 0x9842, 'EnemyShotBlockBoxes', 'enemy shot type'),
]


# The named animation sets of the other enemies, shots and props: (start, end, {table: entries}).
# Their labels come from the annotation database (names= in build).
ANIM_REGIONS2 = [
 (0x733E, 0x7344, {}), (0x7514, 0x751A, {}), (0x7ADA, 0x7AEC, {}), (0x951A, 0x9528, {}),
 (0x9BDC, 0x9C58, {0x9BE0: 20}), (0x9EDE, 0x9FBC, {0x9EDE: 12}), (0xDA78, 0xDA84, {}),
 (0xEDAA, 0xEE1C, {0xEDB0: 2, 0xEDC8: 2, 0xEDE0: 2, 0xEDE4: 2, 0xEDF8: 2, 0xEE04: 2, 0xEE10: 2}),
 (0xF3F2, 0xF422, {0xF3F2: 2, 0xF40A: 2, 0xF416: 2}),
 (0xF5C4, 0xF5DC, {0xF5C4: 2, 0xF5C8: 2}),
 (0x10024, 0x10082, {0x10024: 3, 0x1003E: 3, 0x1004C: 3, 0x10066: 3, 0x10074: 3}),
 (0x10398, 0x103BA, {}),
 (0x10958, 0x109C4, {0x10958: 2, 0x10970: 2, 0x10984: 2, 0x10998: 2, 0x109A4: 2, 0x109B8: 2}),
 (0x10C76, 0x10CCE, {0x10C76: 2, 0x10C7A: 2, 0x10CB6: 2}),
 (0x1160C, 0x11640, {0x1160C: 2, 0x11610: 2, 0x11628: 2}),
 (0x119A6, 0x119DA, {0x119A6: 2, 0x119AA: 3, 0x119B0: 3}),
 (0x11ADA, 0x11B1A, {}), (0x11C9C, 0x11CC8, {0x11C9C: 2, 0x11CB0: 2}),
 (0x1209C, 0x120CC, {0x1209C: 5, 0x120B2: 5}),
]

def build(D, B=0x80, names=None):
    regions = list(ANIM_REGIONS)
    if names:
        for s, e, t in ANIM_REGIONS2:
            regions.append((s, e, t, {a: n for a, n in names.items() if s <= a < e}))
    rb = lambda a: D[a-B]
    rw = lambda a: struct.unpack('>h', D[a-B:a-B+2])[0]
    px = lambda v: f'{v/256:+.2f}'
    blocks = []

    for s, e, tables, names in regions:
        names = dict(names)
        # pass 1: find every target
        targets = {}
        a = s
        while a < e:
            if a in tables:
                for i in range(tables[a]):
                    t = a+2*i+rw(a+2*i); targets.setdefault(t, (a, i))
                a += 2*tables[a]; continue
            if rb(a+1) & 0x80:
                t = a+2+rw(a+2); targets.setdefault(t, None); a += 4
            else:
                a += 2
        assert a == e, hex(a)
        for t, src in sorted(targets.items()):
            assert s <= t < e, f'target {t:X} outside {s:X}-{e:X}'
            if t in names: continue
            if src is not None and src[0] in names:
                names[t] = f'{names[src[0]]}_{src[1]}'
            else:
                owner = max(x for x in names if x <= t)
                names[t] = f'{names[owner]}_{t-owner}'
        # pass 2: emit
        L = []; a = s
        while a < e:
            if a in names: L.append(f'{names[a]}:')
            if a in tables:
                for i in range(tables[a]):
                    t = a+2*i+rw(a+2*i)
                    L.append(f'\tdc.w\t{names[t]}-*\t; {i}')
                a += 2*tables[a]; continue
            f, t = rb(a), rb(a+1)
            if t & 0x80:
                tg = a+2+rw(a+2)
                L.append(f'\tAL\t${f:02X},{t & 0x7F},{names[tg]}'); a += 4
            else:
                L.append(f'\tAF\t${f:02X},{t}'); a += 2
        blocks.append((s, e, L, {v: k for k, v in names.items()}))

    for s, e, tabs, dtabs in MOVE_REGIONS:
        names = {}
        for a0, nm, n in tabs:
            names[a0] = nm or None
        # direction tables name their targets
        for a0, (nm, n) in dtabs.items():
            names[a0] = nm
            for i in range(n):
                t = a0+2*i+rw(a0+2*i)
                if names.get(t) is None: names[t] = f'{nm}_{i}'
        L = []; a = s
        tabinfo = {a0: n for a0, nm, n in tabs}
        while a < e:
            if names.get(a): L.append(f'{names[a]}:')
            if a in dtabs:
                for i in range(dtabs[a][1]):
                    t = a+2*i+rw(a+2*i)
                    L.append(f'\tdc.w\t{names[t]}-*\t; {i}')
                a += 2*dtabs[a][1]; continue
            n = tabinfo[a]
            for i in range(n):
                dx, dy = rw(a+4*i), rw(a+4*i+2)
                L.append(f'\tdc.w\t{dx},{dy}\t; {i:2d}: dx {px(dx)}, dy {px(dy)}')
            a += 4*n
        assert a == e
        blocks.append((s, e, L, {v: k for k, v in names.items() if v}))

    for s, e, nm, what in BOX_TABLES:
        L = [f'{nm}:']
        for i, a in enumerate(range(s, e, 8)):
            xo, w, yo, h = (rw(a+2*k) for k in range(4))
            L.append(f'\tdc.w\t{xo},{w},{yo},{h}\t; {what} {i}')
        blocks.append((s, e, L, {nm: s}))
    return blocks

if __name__ == '__main__':
    import sys
    for s, e, l, lab in build(open(sys.argv[1], 'rb').read()):
        print(f'{s:X}-{e:X} {len(l)} lines')
        print('\n'.join(l[:14]))
