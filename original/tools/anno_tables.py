# Structured data tables (anim_data.py) and names for the remaining small tables.
# Executed inside anno_db.py after the map tables.
import anim_data as _ad
HEADERS[0x922E] = """Weapon and armour-debris animations (shot types 0-5). Direction tables: one script per
O_Dir. AF frame,ticks / AL frame,ticks,next (see anim_data.py)."""
HEADERS[0xC83E] = """Woody Pig animations, one set per facing (A / B): emerge from the tree, fly, turn
(ends flying the other way), drop pose"""
HEADERS[0xD058] = """Bat / crow animations. Direction tables (by O_Dir) for flying; Crow_Pose picks a
pose table by facing, then a random pose (CrowPoses). Crow_UnrefTable is not used by
any code found."""
HEADERS[0xD8D4] = """Petite Devil animations. PetiteDevil_TurnAnims is indexed by PD_Turn (+4 while
recoiling from a shot)."""
HEADERS[0xD960] = """Petite Devil movement tables (dx, dy in 8.8 px/frame, Y up, by O_Dir): six special
moves, then 16 directions at 1.65, 2.5 and 0.38 px/frame"""
HEADERS[0xE152] = "Blue Killer animations"
HEADERS[0xE18E] = """Blue Killer swoops: two sets (BK_SwoopSet), each a direction table of two 6-step
movement tables - falling at 1.71 px/frame while the sideways speed builds up"""
HEADERS[0x12210] = "Explosion animation for a dying enemy (one per facing): frames $1B-$20"
HEADERS[0x8E8E] = """Enemy shot boxes against Arthur, per enemy-shot type: x offset, width, y offset,
height (EnemyShotsVsArthur); the second table is used while he crouches"""
HEADERS[0x97AA] = """Boxes for Arthur's shots against enemy shots, per enemy-shot type (ShotsVsEnemyShots)"""
import tables_data as _td
_D0=open(_os.path.join(_os.path.dirname(_os.path.abspath(__file__)),'main.bin'),'rb').read()


for _a,_n,_h in [
 (0x8245,'PlatformHeights',"Per moving-platform type (1-5): height of its top surface (PlatformSizes = widths)"),
 (0xAE12,'DirTabLow',"""DirectionToArthur results (0 right, 4 down, 8 left, 12 up) by quadrant: Arthur
right-above, left-above, right-below, left-below. One table per slope band |dy|/|dx|:
the slope is taken as the integer quotient q = |dy| div |dx|: Steep q >= 6, 60 2 <= q < 6,
45 q = 1, and for q = 0 Low when |dy| >= |dx| / 4, else Flat (checked in the emulator).
The code's x100 thresholds (75, 150, 600) only see whole quotients, so the 1.5 step never
happens."""),
 (0xAE16,'DirTabFlat',None),(0xAE1A,'DirTab60',None),(0xAE1E,'DirTabSteep',None),
 (0xAE22,'DirTab45',"45-degree band: the last entry is 5 where 6 is expected (the data bug)"),
 (0xD711,'PetiteDevilTurnLeft',"(mode, direction, wanted direction) when level with Arthur and he is to the left"),
 (0xE874,'RedArremer_HoverThreat',"(offset, range) for RedArremer_ShotThreat while hovering. With these values the\ndistance test passes unless Arthur is more than about 570 px to the right, so in\npractice the dodge check always runs."),
 (0xF1C6,'SatanDiveSpeedFast',"X speed by O_Dir for the second half of the dive: -2.25 / +2.25 px/frame (8.8)"),
 (0xF400,'Satan_AnimFlap',"Satan flapping: frames 0, 1, 2, 1 (also the opening scene's demon)"),
 (0xF41E,'Satan_AnimWings',"Satan, wings spread (frame 4, held)"),
 (0xFB5A,'Unicorn_JumpChoicesAfter1',"Next jump type after a type-1 jump (random pick of 4)"),
 (0x110A6,'DragonWaitTimesL5',"Dragon wait times on level 5 (DragonWaitTimes elsewhere)"),
 (0x1898C,'FileTail',"Bytes after HUNK_END to the end of the loaded file. The globals block (GLOBALS,\n$1898C) is placed over them at run time."),
 (0x1899C,'FileTailP2',None),
]:
    N(_a,_n,_h)
for _a,_t in [(0xAE16,''),]: pass

# ---- remaining raw object offsets
OBJ_RANGES.extend([(0x824A, 0x82EE), (0x8354, 0x83C0), (0xC1FC, 0xC44E), (0xA9A6, 0xAAEC)])
TYPE_FIELDS.append((0x824A, 0x82EE, {0x18: ('Itm_Rider', 'platform items: set while Arthur stands on it')}))
TYPE_FIELDS.append((0x7AEC, 0x7BC8, {0x0B: ('Spn_Flags', 'spawner flags: bit 0 world coordinates, bit 1 runs once, bit 2 keeps running when the zone changes')}))
TYPE_FIELDS.append((0x91A2, 0x94A0, {
 0x1C: ('Shot_StartX', 'X where the shot was thrown (range check)'),
 0x1E: ('Shot_VX', 'arc speed X (16.16) once a torch or axe starts to fall'),
 0x22: ('Shot_VY', 'arc speed Y (16.16)')}))
TYPE_FIELDS.append((0x9A10, 0x9A50, {0x1C: ('Spc_VY', 'fall speed (16.16), gravity 0.07 px/frame^2')}))
TYPE_FIELDS.append((0xC65A, 0xCBAC, {0x31: ('Pig_Unused31', 'cleared at set-up, never read'),
 0x32: ('Pig_Unused32', 'cleared at set-up, never read'), 0x33: ('Pig_Unused33', 'cleared at set-up, never read')}))
TYPE_FIELDS.append((0xDC8C, 0xE1FA, {0x31: ('BK_Unused31', 'cleared, never read')}))
TYPE_FIELDS.append((0x103BA, 0x109C4, {0x37: ('BM_FlinchTime', 'frames of the flinch after a hit (6)')}))
TYPE_FIELDS.append((0x11640, 0x119A6, {0x21: ('Ast_WalkTimeLo', 'low byte of the Ast_WalkTime word (set to a random number)'),
 0x23: ('Ast_StandInLo', 'low byte of the Ast_StandIn word (set to a random number)')}))
TYPE_FIELDS.append((0xD160, 0xD8D4, {0x24: ('PD_PathPos', 'position in the current PetiteDevilPath list'),
 0x28: ('PD_PathSeg', 'current path segment')}))
N(0x8240, 'PlatformSizes', "Per item type 1-5 (shootable scenery, then the platforms): width Arthur can stand on")
N(0x8245, 'PlatformHeights', "Per item type 1-5: height (Arthur stands on the top). Item type 1 - gravestones and\nother shootable scenery - is solid too; only types 2-5 carry him (Itm_Rider).")

# ---- remaining raw globals
V(0xAA, 'g_OtherPlayer', "the other player's copy of g_Level .. g_ShowIntro (16 bytes), exchanged by SwapPlayers")
V(0x632, 'g_RestoreBufB', 'restore list storage: list A grows down from here, list B from g_SpawnQuota')
VAR_RANGES.extend([(0x04, 2), (0x0A, 2), (0x5E, 16), (0x9C, 2), (0xE6, 4), (0x8A0, 0x40), (0xA20, 0xC0)])

# ---- clearer notes on some early-named globals
V(0x018, 'g_BossCountdown', 'bosses left to beat on this level before the key / ending (LevelBossCountdown)')
V(0x01B, 'g_MaxMapZone', 'furthest map zone reached (spawners with ZoneFlags 0 only start beyond it)')
V(0x01C, 'g_RedrawPending', 'set to request a full redraw: the VBL diverts user mode to RedrawEntry')
V(0x01F, 'g_TextShadow', 'text colour where only the first font plane is set')
V(0x020, 'g_TextInk', 'text colour where only the second font plane is set')
V(0x021, 'g_TextPaper', 'text colour where both font planes are set')
V(0x02B, 'g_SubState2', 'step within the sub state')
V(0x02C, 'g_SubState3', 'step within g_SubState2')

# ---- headers for the tables decoded by tables2_data.py
HEADERS[0x4FF0] = """BobFrameDescs - per enemy type (O_Type) a word offset, from the entry, to the type's frame
table (QueueEnemyDraw). A frame (FRAME, indexed by O_Frame): offset of its graphics in the type's
set (g_BobSets), y adjust (signed) and height in lines; the width comes from the size class
(BoxSizeTable). Type 16 has none. The Crow takes BobFrameDescsBat with param 0-2, and with param 3
its own table with the red-crow graphics set. The Unicorn's table holds the legs (frames 0-7)
and the body (8+): QueueEnemyDraw draws it as two BOBs."""
HEADERS[0x7E0E] = """CopperTemplate - $180 bytes copied to COPPER_INIT at start-up. First the COP1 list: the
16 lines above line $44 from $64468, the eight sprite pointers, then at line $44 the copper
interrupt and a jump to COP2. Then the four playfield lists that COP2 rotates through
(g_CopperFront / g_CopperBack / spares; their plane pointers are rewritten for the scroll) and
the progress-map list. Bitplanes are line-interleaved: 5 planes of 36 bytes per 180-byte line."""
HEADERS[0x9002] = """EnemyShotFrames - FRAME entries (offset, y adjust, height) for the enemy-shot graphics at
$1A298 (track 58), indexed by the shot's frame number."""
HEADERS[0x908E] = """EffectFrames - FRAME entries for the weapon / pickup / effect graphics at $1B4CC
(tracks 59-60): Arthur's shots, prizes, sparks and the explosion tiles (QueueExplosionDraw)."""
HEADERS[0xA72E] = """ItemPaths - moving platforms (item types 2-5, Item_PathStart): per type a word offset to a
table per param, each entry an offset to a step table of (dx, dy) moves in pixels x 256 a frame
(Item_PathMove). Steps: 0 still, 1 right, 2 down, 3 left, 4 up. Types 0 and 1 never start a path."""
HEADERS[0xA7FC] = """ItemPathScripts - the platforms' scripts, indexed the same way: (step, frames) pairs (ISTEP);
the last has bit 7 on frames and an offset back to the start (ILOOP), read by Item_PathScript.
Types 2 and 3 have only a param-0 entry: the one type-3 platform with param 1 (level 1) reads the
next word and so runs type 4's first script with its own steps (ItemSteps3_1, 3 px a frame up
and down). Type 1's entry points into type 4's scripts but is never used."""
HEADERS[0xD2D0] = """PetiteDevilPath (unused) - nine word offsets, each from its entry to a list: count, then
that many (x, y) world positions where the devil may appear.
BUG (in the unused PetiteDevil_PathUnused): PetiteDevil_PathNext adds the offset after
stepping past it, so it lands 2 bytes on: the first X is taken as the count and the segment
pointer starts at a Y. The lists only work when read from the entry itself."""
HEADERS[0x10F46] = """DragonEntrancePath - (frames, direction) steps flown on arrival (DSTEP; directions as
DragonMoveTable: 0 right, 4 down, 8 left, 12 up), ended by a zero word. Then DragonPatrolPath."""
HEADERS[0x11302] = """DragonDescend / DragonClimb - one (frames, direction) step for each facing (right, left),
used by Dragon_SeekHeight to move towards Arthur's height."""
HEADERS[0x11408] = """DragonPatrolPath - an offset to the patrol taken after the entrance. Two endless patrols,
(frames, direction) steps with a loop (DLOOP): DragonPatrolLeftward weaves to the left and
DragonPatrolRightward to the right. The turn tables below (Dragon_Turn, by facing, then upper / lower half of the
screen) curl round and then join the patrol in the new direction."""
HEADERS.pop(0x11306, None)
HEADERS[0x114B2] = """DragonTurnRight - turn paths when facing right: upper / lower half of the screen."""
HEADERS[0x114D0] = """DragonTurnLeft - turn paths when facing left: upper / lower half of the screen."""
HEADERS[0xBD5A] = """KeyAsciiTable - ASCII for raw key codes $00-$67 (0 = no character): the main block in
US order, keypad digits at $0F, $1D-$1F, $2D-$2F and '.' at $3C (keypad 7-9 give nothing); $40 space, $41 backspace,
$42 tab, $43 / $44 enter / return, $45 Esc, $46 Del."""

HEADERS[0x7F8E] = """LevelFileIndex - per level a word offset, from the entry, to its tile file in FileTable
(LoadLevel)."""
HEADERS[0x7F9C] = """FileTable - every file the program loads (FENTRY: load address, length in bytes, first
track; a1 points at an entry for LoadFile, which reads length / 6,312 tracks, rounded up).
The bootblock loads the rest: the loading screen and the main program. tools/disk/mkdisk.py
reads this table (from the assembled binaries of both builds) to lay out the disk."""
for _a in (0x7FBA, 0x7FC4, 0x7FCE, 0x7FD8): HEADERS.pop(_a, None)
NAMES[0x7FA6] = 'FileSmallBobs'; NAMES[0x7FB0] = 'FileEnemyBobs'

# ---- build the data blocks last, so every name above is known
for _s,_e,_l,_lab in _ad.build(_D0,names=NAMES)+_td.build(_D0)+__import__('tables2_data').build(_D0,names=NAMES):
    _out=[]
    for _ln in _l:
        _m=_ln[:-1] if _ln.endswith(':') and not _ln.startswith(('\t',';')) else None
        if _m and _lab.get(_m) not in (None,_s) and _lab[_m] in HEADERS:
            _out += ['', ';'+'-'*75] + ['; '+x if x else ';' for x in HEADERS[_lab[_m]].split('\n')] + [';'+'-'*75]
        _out.append(_ln)
    DATA_BLOCKS[_s]=(_e,_out)
    for _n,_a in _lab.items(): NAMES[_a]=_n
