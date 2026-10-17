"""Readability pass over the generated source (used by gen.py and the 1MB gen1m.py).
 - drops generic labels (l_/jtab_/sub_) that nothing refers to
 - replaces magic numbers with named constants where the meaning is certain:
   sound effects and tunes (the value in d0 for PlaySfx / PlayMusic), AddScore indices,
   game / in-game states, Arthur's state, enemy types and enemy object states,
   and DMACON / INTENA / INTREQ bit masks.
The constants are defined in the prelude (equates()); the bytes do not change."""
import re

SFX = {1: 'SFX_ARTHUR_HIT', 4: 'SFX_JUMP', 5: 'SFX_LAND', 6: 'SFX_THROW', 9: 'SFX_THUD', 10: 'SFX_DEFLECT',
       11: 'SFX_TORCH_FLAME', 12: 'SFX_ENEMY_HIT', 14: 'SFX_EXTRA_LIFE', 17: 'SFX_ENEMY_DIE', 18: 'SFX_WOODY_PIG',
       19: 'SFX_HURT', 20: 'SFX_ENEMY_DIE2', 22: 'SFX_SKELETON_HOP', 23: 'SFX_FIRE_FLARE', 24: 'SFX_STOMP',
       27: 'SFX_CROW', 28: 'SFX_PICKUP'}
TUNE = {0: 'TUNE_START', 1: 'TUNE_HISCORE_TOP', 2: 'TUNE_LEVEL_0_1', 3: 'TUNE_HISCORE', 4: 'TUNE_HURRY_UP',
        5: 'TUNE_BOSS_BEATEN', 6: 'TUNE_NAME_TOP', 7: 'TUNE_GAME_OVER', 8: 'TUNE_LIFE_LOST', 9: 'TUNE_ASTAROTH_BEATEN',
        11: 'TUNE_NAME_ENTERED', 12: 'TUNE_LEVEL_5_6', 13: 'TUNE_LEVEL_2_4', 14: 'TUNE_INTRO'}
SCORE = {1: 10, 2: 50, 3: 100, 4: 200, 5: 300, 6: 400, 7: 500, 8: 800, 9: 1000, 10: 2000, 11: 3000, 12: 4000,
         13: 5000, 14: 6000, 15: 7000, 18: 10000, 19: 20000, 20: 30000, 21: 50000, 22: 100000, 23: 15000}
GAMESTATE = {0: 'GS_INGAME', 1: 'GS_TITLE', 2: 'GS_HISCORES'}
SUBSTATE = {0: 'SS_LOADLEVEL', 1: 'SS_PLAYLEVEL', 2: 'SS_INPLAY', 3: 'SS_GAMEOVER', 4: 'SS_LEVELCOMPLETE',
            5: 'SS_INTRO', 6: 'SS_ENDING', 7: 'SS_WEAPONUSELESS'}
ARTHUR = {0: 'AS_NORMAL', 1: 'AS_HIT', 2: 'AS_KNOCKBACK', 3: 'AS_KNOCKFLY', 4: 'AS_LANDED', 5: 'AS_DIE1',
          6: 'AS_DIE2', 7: 'AS_DIE3'}
OSTATE = {0: 'ST_START', 1: 'ST_ACTIVE', 2: 'ST_KILLED', 3: 'ST_REMOVE'}
ENEMY = ['E_WOODYPIG', 'E_CROW', 'E_PETITEDEVIL', 'E_FLYINGKNIGHT', 'E_BLUEKILLER', 'E_REDARREMER', 'E_SATAN',
         'E_MAGICIAN', 'E_UNICORN', 'E_SKELETON', 'E_BIGMAN', 'E_ZOMBIE', 'E_DRAGON', 'E_ASTAROTH', 'E_FIRE',
         'E_PRINCESS', 'E_TYPE16', 'E_PLANT', 'E_FIREPILLAR']
DMAF = [(0x8000, 'DMAF_SETCLR'), (0x400, 'DMAF_BLITHOG'), (0x200, 'DMAF_MASTER'), (0x100, 'DMAF_RASTER'),
        (0x80, 'DMAF_COPPER'), (0x40, 'DMAF_BLITTER'), (0x20, 'DMAF_SPRITE'), (0x10, 'DMAF_DISK'),
        (8, 'DMAF_AUD3'), (4, 'DMAF_AUD2'), (2, 'DMAF_AUD1'), (1, 'DMAF_AUD0')]
INTF = [(0x8000, 'INTF_SETCLR'), (0x4000, 'INTF_INTEN'), (0x2000, 'INTF_EXTER'), (0x1000, 'INTF_DSKSYNC'),
        (0x800, 'INTF_RBF'), (0x400, 'INTF_AUD3'), (0x200, 'INTF_AUD2'), (0x100, 'INTF_AUD1'), (0x80, 'INTF_AUD0'),
        (0x40, 'INTF_BLIT'), (0x20, 'INTF_VERTB'), (0x10, 'INTF_COPER'), (8, 'INTF_PORTS'), (4, 'INTF_SOFTINT'),
        (2, 'INTF_DSKBLK'), (1, 'INTF_TBE')]
ENEMY_PREFIX = ('Enemy', 'WoodyPig', 'Crow', 'Bat', 'PetiteDevil', 'FlyingKnight', 'BlueKiller', 'RedArremer',
                'Satan', 'Magician', 'Unicorn', 'Skeleton', 'BigMan', 'Zombie', 'Dragon', 'Astaroth', 'Fire',
                'Princess', 'Plant', 'Intro', 'Ending', 'UpdateEnemies', 'QueueEnemyDraw', 'EnemyVsArthur',
                'BossKilled', 'EnemyExplode', 'SetBoxClass', 'CheckFarAway')

def equates():
    out = ['; ---- named constants (the source uses these instead of bare numbers)',
           '; sound effects: d0 for PlaySfx (see sound/SOUND.md)']
    out += [f'{n}\tequ\t{v}' for v, n in sorted(SFX.items())]
    out += ['; tunes: d0 for PlayMusic (1MB build; the 512K build still loads d0 before the removed call)']
    out += [f'{n}\tequ\t{v}' for v, n in sorted(TUNE.items())]
    out += ['; AddScore indices (ScoreValues)'] + [f'PTS_{p}\tequ\t{i}' for i, p in sorted(SCORE.items())]
    out += ['; g_GameState'] + [f'{n}\tequ\t{v}' for v, n in sorted(GAMESTATE.items())]
    out += ['; g_SubState (InGame)'] + [f'{n}\tequ\t{v}' for v, n in sorted(SUBSTATE.items())]
    out += ['; g_ArthurState'] + [f'{n}\tequ\t{v}' for v, n in sorted(ARTHUR.items())]
    out += ['; O_State of an enemy'] + [f'{n}\tequ\t{v}' for v, n in sorted(OSTATE.items())]
    out += ['; DMACON bits'] + [f'{n}\tequ\t${v:04X}' for v, n in DMAF]
    out += ['; INTENA / INTREQ bits'] + [f'{n}\tequ\t${v:04X}' for v, n in INTF]
    return out

def bits(v, table):
    names = []; rest = v
    for b, n in table:
        if rest & b: names.append(n); rest &= ~b
    if rest or not names: return None
    return '|'.join(names)

REDUNDANT = re.compile(r'^(sound \d+(: [^;]*)?|-> state \d \([^)]*\)|[\d,]+ points|start animation)$')
LINE = re.compile(r'^(\s+)(\S+)(\s+)(\S+)(\s*)(; [0-9A-F]{5}.*)?$')

def process(lines):
    text_refs = None
    # ---- 1. unreferenced generic labels
    body = '\n'.join(l for l in lines if not re.match(r'^[A-Za-z_]\w*:', l))
    used = set(re.findall(r'\b((?:l|jtab|sub)_[0-9A-F]{5})\b', body))
    out = []
    for l in lines:
        m = re.match(r'^((?:l|jtab|sub)_[0-9A-F]{5}):\s*$', l)
        if m and m.group(1) not in used: continue
        out.append(l)
    # ---- 1b. jump tables take the name of the routine they belong to
    routine = ''; ren = {}; count = {}
    for l in out:
        m = re.match(r'^([A-Za-z_]\w*):', l)
        if not m: continue
        n = m.group(1)
        if n.startswith('jtab_') and routine:
            count[routine] = count.get(routine, 0) + 1
            ren[n] = f'{routine}_Jumps' + ('' if count[routine] == 1 else str(count[routine]))
        elif not re.match(r'(l|jtab|sub|dat)_', n): routine = n
    taken = {re.match(r'^([A-Za-z_]\w*):', l).group(1) for l in out if re.match(r'^[A-Za-z_]\w*:', l)}
    ren = {k: v for k, v in ren.items() if v not in taken}
    if ren:
        pat = re.compile(r'\b(' + '|'.join(map(re.escape, ren)) + r')\b')
        out = [pat.sub(lambda mm: ren[mm.group(1)], l) for l in out]
    # ---- 2. named constants
    routine = ''
    res = []
    for i, l in enumerate(out):
        m = re.match(r'^([A-Za-z_]\w*):', l)
        if m and not re.match(r'(l|jtab|sub|dat)_', m.group(1)): routine = m.group(1)
        mm = LINE.match(l)
        if not mm or l.startswith(';'):
            res.append(l); continue
        ind, op, sp, args, sp2, cmt = mm.groups()
        cmt = cmt or ''
        nxt = ''
        for j in range(i+1, min(i+4, len(out))):
            if LINE.match(out[j]): nxt = out[j]; break
        new = args
        q = re.match(r'#\$([0-9a-f]+),d0$', args)
        if op == 'moveq' and q:
            v = int(q.group(1), 16)
            if re.search(r'\b(bsr|bra)\.[wb]\s+PlaySfx\b', nxt) and v in SFX: new = f'#{SFX[v]},d0'
            elif (re.search(r'\b(bsr|bra)\.[wb]\s+PlayMusic\b', nxt) or 'PlayMusic here' in nxt) and v in TUNE:
                new = f'#{TUNE[v]},d0'
            elif re.search(r'\b(bsr|bra)\.[wb]\s+AddScore\b', nxt) and v in SCORE: new = f'#PTS_{SCORE[v]},d0'
        q = re.match(r'#\$([0-9a-f]+),(g_GameState|g_SubState|g_ArthurState)\(a6\)$', args)
        if q:
            v = int(q.group(1), 16); t = {'g_GameState': GAMESTATE, 'g_SubState': SUBSTATE, 'g_ArthurState': ARTHUR}[q.group(2)]
            if v in t: new = f'#{t[v]},{q.group(2)}(a6)'
        if routine.startswith(ENEMY_PREFIX):
            q = re.match(r'#\$([0-9a-f]+),(O_Type|O_State)\(a5\)$', args)
            if q:
                v = int(q.group(1), 16)
                if q.group(2) == 'O_Type' and v < len(ENEMY): new = f'#{ENEMY[v]},O_Type(a5)'
                if q.group(2) == 'O_State' and v in OSTATE: new = f'#{OSTATE[v]},O_State(a5)'
        q = re.match(r'#\$([0-9a-f]+),(.*\b(DMACON|INTENA|INTREQ)\b.*|\$9c\(a0\)|\$96\(a0\))$', args)
        if q and op.startswith('move'):
            v = int(q.group(1), 16)
            reg = q.group(3) or {'$9c(a0)': 'INTREQ', '$96(a0)': 'DMACON'}[q.group(2)]
            b = bits(v, INTF if reg in ('INTENA', 'INTREQ') else DMAF)
            if b: new = f'#{b},{q.group(2)}'
        if new == args and cmt and len(f'{ind}{op}{sp}{args}') < 48 and l[48:50] != '; ':
            l = f'{ind}{op}{sp}{args}'.ljust(48) + cmt          # realign after a rename
        if new != args:
            # a comment that only restated the number is no longer needed
            cm = re.match(r'^(; [0-9A-F]{5})\s+(.*)$', cmt)
            if cm and REDUNDANT.match(cm.group(2)): cmt = cm.group(1)
            code = f'{ind}{op}{sp}{new}'
            l = (code.ljust(48) + cmt) if cmt else code
        res.append(l)
    return res

def with_equates(prelude):
    """Insert the named constants into the prelude, before its org line."""
    prelude = with_guide(prelude)
    i = prelude.index('\torg')
    return prelude[:i] + '\n'.join(equates()) + '\n\n' + prelude[i:]

GUIDE = r"""
; ===========================================================================
; HOW TO READ THIS FILE
;  a6      always points at the globals block (GLOBALS); globals are g_Name(a6).
;  a5      the object being handled. Every object slot starts with the O_ fields
;          (O_Active, O_State, O_X, O_Y, O_Type ...); from +$1C each enemy type has its
;          own fields, named with a prefix (Pig_, Crw_, PD_, FK_, BK_, RA_, Sat_, Mag_,
;          Uni_, Skl_, BM_, Zmb_, Drg_, Ast_, Fir_, Plt_, Pil_ ...). See docs/GLOBALS.md.
;  X, Y    level pixels with Y increasing UPWARDS; speeds and positions are 16.16
;          fixed point (the long at O_X / g_ArthurX), movement tables 8.8.
;  Labels  named routines and tables; l_XXXXX = a branch target at address XXXXX,
;          jtab_XXXXX = a jump table, sub_XXXXX = an unnamed subroutine.
;  Numbers named constants are used where the meaning is certain (SFX_, TUNE_, PTS_,
;          GS_, SS_, AS_, ST_, E_, I_, DMAF_, INTF_ - defined below).
;  Comments the address of each instruction, then what it does. Block headers describe
;          each routine; '(no references found)' marks code nothing calls.
;  Data    animation scripts use AF/AL, Arthur's AFRAME/ALOOP, spawn tables SPAWNER/
;          SPAWN, placement lists PLACE; maps and tables are written out row by row.
;
; CONTENTS (search for the name)
;  Start-up / interrupts  ProgramEntry Start InitHardware CrashReset VblIRQ KeyboardIRQ
;                         Level1Logic RedrawEntry
;  Attract screens        AttractTitle AttractHiScores CheckGameStart DrawCreditsScreen
;                         DrawHiScoreTable
;  Game flow              InGame LoadLevel PlayLevel ProgressMap SetupLevel InPlay
;                         PlayFrame CameraJump GameOver NameEntry LevelComplete
;                         EndOfLevelKey IntroCutscene Ending WeaponUseless
;  Arthur                 ArthurUpdate ArthurNormal ArthurJump ArthurFall ArthurReadUpDown
;                         ArthurFire ArthurHit ArthurOnPlatform ArthurSpritePos
;  Objects                UpdateShots UpdateSpecialObjs UpdateEnemyShots UpdateItems
;                         UpdateEnemies (one handler per enemy type: EnemyTypeTable)
;  Spawning               UpdateMapZone UpdateSpawners MapZoneTable ZoneSpawners SpawnScripts
;  Collisions / scoring   EnemyVsArthur EnemyShotsVsArthur ShotsVsScenery ShotsVsEnemyShots
;                         EnemyHitByShot BossKilled ExtraLifeCheck AddScore
;  Helpers                DirectionToArthur Random MapTileAt ObjectMapCollide LadderCheck
;  Drawing                RestoreBackground DrawBobs DrawBob QueueEnemyDraw QueueObjectDraw
;                         QueueExplosionDraw RedrawScreen DrawSceneryOnRedraw SwapScreens
;                         ShowBackBuffer SetBitplanePtrs PrintChar PrintString PrintBCD
;  Disk / sound           LoadFile PlaySfx
;  Level data             WorldMap CellTiles BlockTiles TileAttr LevelItemLists LevelEnemyLists
; ===========================================================================
"""

def with_guide(prelude):
    i = prelude.index('\tinclude')
    return prelude[:i] + GUIDE.lstrip('\n') + '\n' + prelude[i:]
