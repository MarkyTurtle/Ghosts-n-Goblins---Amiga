"""Level, placement, scoring and box tables as readable source for gen.py's DATA_BLOCKS
(512K addresses, main.bin loaded at $80). build(D) returns a list of (start, end, lines,
labels). Enemy and item types are written with the E_ / I_ equates from prelude.s."""
import struct

ENEMY = ['E_WOODYPIG', 'E_CROW', 'E_PETITEDEVIL', 'E_FLYINGKNIGHT', 'E_BLUEKILLER', 'E_REDARREMER',
         'E_SATAN', 'E_MAGICIAN', 'E_UNICORN', 'E_SKELETON', 'E_BIGMAN', 'E_ZOMBIE', 'E_DRAGON',
         'E_ASTAROTH', 'E_FIRE', 'E_PRINCESS', 'E_TYPE16', 'E_PLANT', 'E_FIREPILLAR']
ITEM = ['I_TOUCH', 'I_SCENERY', 'I_PLATFORM2', 'I_PLATFORM3', 'I_PLATFORM4', 'I_PLATFORM5']
WEAPON = ['torch', 'lance', 'axe', 'cross', 'dagger']

def equates():
    out = ['; enemy types (O_Type of enemies)']
    out += [f'{n}\tequ\t{i}' for i, n in enumerate(ENEMY)]
    out += ['; item types (O_Type of items): touch trigger / pickup, shootable scenery, platforms']
    out += [f'{n}\tequ\t{i}' for i, n in enumerate(ITEM)]
    return out

def build(D, B=0x80):
    rb = lambda a: D[a-B]
    rw = lambda a: struct.unpack('>h', D[a-B:a-B+2])[0]
    ruw = lambda a: struct.unpack('>H', D[a-B:a-B+2])[0]
    rl = lambda a: struct.unpack('>L', D[a-B:a-B+4])[0]
    blocks = []

    # ---- placement lists: two offset tables, then the lists, items and enemies interleaved
    IT, ET, END = 0x3B14, 0x3B22, 0x4002
    lists = {}
    for l in range(7):
        lists[IT+2*l+rw(IT+2*l)] = ('Items', l)
        lists[ET+2*l+rw(ET+2*l)] = ('Enemies', l)
    lab = {a: f'Level{l}{k}' for a, (k, l) in lists.items()}
    L = ['LevelItemLists:'] + [f'\tdc.w\t{lab[IT+2*l+rw(IT+2*l)]}-*' for l in range(7)]
    L += ['LevelEnemyLists:'] + [f'\tdc.w\t{lab[ET+2*l+rw(ET+2*l)]}-*' for l in range(7)]
    a = ET+14
    for la in sorted(lists):
        assert la == a, (hex(la), hex(a))
        kind, l = lists[la]
        n = ruw(la)
        L.append(f'{lab[la]}:'); L.append(f'\tdc.w\t{n}')
        a = la+2
        for k in range(n):
            t, p, x, y = rb(a), rb(a+1), ruw(a+2), ruw(a+4)
            tn = (ITEM if kind == 'Items' else ENEMY)[t] if t < (6 if kind == 'Items' else 19) else f'${t:02X}'
            L.append(f'\tPLACE\t{tn},{p},${x:04X},${y:04X}')
            a += 6
    assert a == END, hex(a)
    labs = {'LevelItemLists': IT, 'LevelEnemyLists': ET}
    labs.update({v: k for k, v in lab.items()})
    blocks.append((IT, END, L, labs))

    # ---- level tables $43EE-$44D6
    L = ['LevelBossCountdown:', '\tdc.b\t'+','.join(str(rb(0x43EE+i)) for i in range(7))+f',{rb(0x43F5)}\t; levels 0-6, pad']
    L.append('LevelSpawnQuota:')
    for l in range(7):
        a = 0x43F6+16*l
        L.append('\tdc.b\t'+','.join(str(rb(a+i)) for i in range(16))+f'\t; level {l}')
    L.append('LevelBounds:')
    for l in range(7):
        a = 0x4466+4*l; x0, x1, y1, y0 = (rb(a+i) for i in range(4))
        L.append(f'\tdc.b\t{x0},{x1},{y1},{y0}\t; level {l}: cells x {x0}-{x1}, y {y0}-{y1}')
    for nm, a0 in [('LevelTimeStart', 0x4482), ('LevelTimeCheckpoint', 0x4490)]:
        L.append(f'{nm}:')
        L.append('\tdc.w\t'+','.join(f'${ruw(a0+2*l):04X}' for l in range(7))+'\t; BCD m:ss: '+
                 ' '.join(f'{ruw(a0+2*l)>>8:x}:{ruw(a0+2*l)&0xFF:02x}' for l in range(7)))
    for nm, a0 in [('LevelStartPos', 0x449E), ('LevelCheckpointPos', 0x44AC)]:
        L.append(f'{nm}:')
        L.append('\tdc.b\t'+','.join(f'${rb(a0+i):02X}' for i in range(14))+'\t; (x, y) per level')
    L.append('LevelMapTable:')
    L.append('\tdc.w\t'+','.join(f'WorldMap+{ruw(0x44BA+2*l)-0x1C}-LevelMapTable' for l in range(7)) +
             '\t; levels 0-6: origin cell, from the table start')
    L.append('\tdc.w\t'+','.join(f'${ruw(0x44C8+2*l):04X}' for l in range(7))+'\t; not read by any code found')
    blocks.append((0x43EE, 0x44D6, L, {'LevelBossCountdown': 0x43EE, 'LevelSpawnQuota': 0x43F6,
        'LevelBounds': 0x4466, 'LevelTimeStart': 0x4482, 'LevelTimeCheckpoint': 0x4490,
        'LevelStartPos': 0x449E, 'LevelCheckpointPos': 0x44AC, 'LevelMapTable': 0x44BA}))

    # ---- per enemy type tables
    def boxes(a0, nm):
        L = [f'{nm}:']
        for t in range(19):
            a = a0+8*t
            L.append(f'\tdc.w\t'+','.join(str(rw(a+2*k)) for k in range(4))+f'\t; {ENEMY[t]}')
        return L
    blocks.append((0x8CD8, 0x8E08, boxes(0x8CD8, 'EnemyContactBoxes')+boxes(0x8D70, 'EnemyContactBoxesCrouch'),
                   {'EnemyContactBoxes': 0x8CD8, 'EnemyContactBoxesCrouch': 0x8D70}))
    L = boxes(0x9528, 'EnemyHitboxes') + ['EnemyVulnerability:']
    for t in range(19):
        v = rb(0x95C0+t)
        w = ', '.join(WEAPON[i] for i in range(5) if v >> i & 1) or 'nothing'
        L.append(f'\tdc.b\t%{v:08b}\t; {ENEMY[t]}: {w}')
    L.append(f'\tdc.b\t{rb(0x95D3)}\t; pad')
    blocks.append((0x9528, 0x95D4, L, {'EnemyHitboxes': 0x9528, 'EnemyVulnerability': 0x95C0}))

    sv = {i+1: rl(0xAE42+4*i) for i in range(23)}
    L = ['EnemyPoints:']
    for t in range(19):
        i = rb(0x96F0+t)
        L.append(f'\tdc.b\t{i}\t; {ENEMY[t]}: {sv[i]:x}')
    L.append(f'\tdc.b\t{rb(0x9703)}\t; pad')
    blocks.append((0x96F0, 0x9704, L, {'EnemyPoints': 0x96F0}))
    L = ['ScoreValues:']
    for i in range(1, 24):
        v = sv[i]
        note = f'{v:x}' if v < 0x10000000 else 'not valid BCD - no index uses it'
        L.append(f'\tdc.l\t${v:08X}\t; {i:2d}: {note}')
    blocks.append((0xAE42, 0xAE9E, L, {'ScoreValues': 0xAE42}))

    # ---- size classes
    for a0, nm in [(0x5426, 'BoxSizeTable'), (0xC148, 'CollisionBoxes')]:
        L = [f'{nm}:']
        for k in range(11):
            L.append(f'\tdc.b\t{rb(a0+2*k)},{rb(a0+2*k+1)}\t; size class {k}: width, height')
        blocks.append((a0, a0+22, L, {nm: a0}))
    L = ['LevelCheckpointX:', '\tdc.w\t'+','.join(f'${ruw(0x6BF8+2*l):04X}' for l in range(7))+'\t; levels 0-6',
         'LevelMusic:', '\tdc.b\t'+','.join(str(rb(0x6C06+i)) for i in range(8))+'\t; levels 0-6 (1MB tune numbers), pad']
    blocks.append((0x6BF8, 0x6C0E, L, {'LevelCheckpointX': 0x6BF8, 'LevelMusic': 0x6C06}))
    return blocks

if __name__ == '__main__':
    import sys
    for s, e, l, lab in build(open(sys.argv[1], 'rb').read()):
        print(f'{s:X}-{e:X} {len(l)}'); print('\n'.join(l[:12]))
