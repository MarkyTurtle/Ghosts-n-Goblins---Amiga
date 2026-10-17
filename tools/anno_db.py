# Annotation database for gng_main.s
# NAMES:    address -> label name
# HEADERS:  address -> block comment placed above the label
# COMMENTS: address -> end-of-line comment
# VARS:     a6 offset -> (name, comment)        (a6 = GLOBALS = $1898C)
# MEM:      absolute address -> equate name (fixed buffers outside the image)

NAMES = {}
HEADERS = {}
COMMENTS = {}
VARS = {}
MEM = {}
MEMC = {}

def N(a, name, hdr=None):
    NAMES[a] = name
    if hdr: HEADERS[a] = hdr
def C(a, text): COMMENTS[a] = text
def V(off, name, c=''): VARS[off] = (name, c)
def M(a, name, c=''):
    MEM[a] = name
    if c: MEMC[a] = c

# ---------------------------------------------------------------- memory map
M(0x1898C, 'GLOBALS', 'a6 points here for the whole game (variables block)')
M(0x1899C, 'GLOBALS_P2', 'player-2 view of the per-player block (GLOBALS+$10)')
M(0x1A118, 'COPPER_INIT', 'copper list template ($180 bytes copied from CopperTemplate)')
M(0x1A190, 'COPPER_A1'); M(0x1A1C0, 'COPPER_A2'); M(0x1A1F0, 'COPPER_B1'); M(0x1A220, 'COPPER_B2')
M(0x1A250, 'COPPER_MAP', 'copper list used by the between-level progress map')
M(0x1DE34, 'ARTHUR_SPR_GFX', 'Arthur hardware-sprite frames, 4 planes x $2880 apart, $80 bytes/frame')
M(0x1F334, 'SPR_GFX_B0'); M(0x20734, 'SPR_GFX_A1'); M(0x21C34, 'SPR_GFX_B1')
M(0x23034, 'SPR_GFX_A2'); M(0x24534, 'SPR_GFX_B2'); M(0x25934, 'SPR_GFX_A3'); M(0x26E34, 'SPR_GFX_B3')
M(0x28234, 'MASK_BUF', 'byte-plane extracted from file at tracks 61')
M(0x28E54, 'MUSIC_FILE', 'music/sfx replay file (512K: tracks 126-131)')
M(0x28E74, 'MUSIC_PLAYER', 'replay entry - also stored in vector $60')
M(0x30BB8, 'SPRITE0_DATA'); M(0x30C78, 'SPRITE1_DATA'); M(0x30D38, 'SPRITE2_DATA'); M(0x30DF8, 'SPRITE3_DATA')
M(0x30C3C, 'SPRITE4_DATA'); M(0x30CFC, 'SPRITE5_DATA'); M(0x30DBC, 'SPRITE6_DATA'); M(0x30E7C, 'SPRITE7_DATA')
M(0x311E8, 'BOB_GFX_A', 'file tracks 37 / 62-63 load address')
M(0x341E8, 'BOB_GFX_B')
M(0x37468, 'SCREEN_0', 'also load address of the big graphics file (tracks 38-56) before unpacking')
M(0x42868, 'SCREEN_1')
M(0x4DC68, 'SCREEN_2')
M(0x59068, 'SCREEN_3')
M(0x64468, 'CLEAR_AREA')
M(0x65548, 'LEVEL_FILE', 'per-level data file load address (tracks 84-109)')

# ---------------------------------------------------------------- globals (a6)
V(0x000, 'g_SavedSR', 'VBL handler parks the interrupted SR here')
V(0x002, 'g_FrameStamp', 'frame counter snapshot for timed waits')
V(0x004, 'g_VblCount', 'incremented every vertical blank')
V(0x006, 'g_GameFrame', 'incremented every game-logic frame')
V(0x008, 'g_RawKey', 'last raw keycode (Esc=$45, F1=$50, F2=$51)')
V(0x009, 'g_AsciiKey', 'last key as ASCII (space=$20 pauses)')
V(0x00A, 'g_RandSeed', 'random generator state, seeded $AAAA')
V(0x00C, 'g_TimeLeft', 'level timer, BCD minutes.byte/seconds.byte')
V(0x00E, 'g_LevelDone', 'set when the level is completed')
V(0x00F, 'g_PlayerDied', 'set when Arthur has died this frame')
V(0x018, 'g_BossCountdown', 'hits/frames before boss defeat sequence')
V(0x01A, 'g_MapZone', 'current map zone (MapZoneTable): selects the enemy spawners')
V(0x01B, 'g_MaxMapZone')
V(0x01C, 'g_RedrawPending', 'VBL diverts user mode to RedrawScreen when set')
V(0x01D, 'g_RedrawDone', 'set by RedrawScreen when finished')
V(0x01E, 'g_SkipLogic', 'non-zero: VBL does not trigger the logic interrupt')
V(0x01F, 'g_TextShadow', 'text colour index (shadow/outline)')
V(0x020, 'g_TextInk', 'text colour index (ink)')
V(0x021, 'g_TextPaper', 'text colour index (highlight)')
V(0x027, 'g_TwoPlayer', 'non-zero = two-player game')
V(0x028, 'g_CurPlayer', '0 = player 1, $FF = player 2')
V(0x029, 'g_GameState', '0 = in game, 1/2 = attract screens')
V(0x02A, 'g_SubState', 'in-game sub state (see GameStateTable)')
V(0x02B, 'g_SubState2')
V(0x02C, 'g_SubState3')
V(0x02D, 'g_ArthurVisible', 'hardware sprites 0-3 enabled')
V(0x02E, 'g_Spr47Visible', 'hardware sprites 4-7 enabled')
V(0x02F, 'g_Paused')
V(0x030, 'g_CheatOn', "set by entering ')!(' on the high-score table: no life loss / no damage")
V(0x032, 'g_ScreenFront')
V(0x036, 'g_ScreenBack')
V(0x042, 'g_ScreenSpare1')
V(0x046, 'g_ScreenSpare2')
V(0x04A, 'g_CopperFront')
V(0x04E, 'g_CopperBack')
V(0x052, 'g_CopperSpare1')
V(0x056, 'g_CopperSpare2')
V(0x05A, 'g_Joy', 'joystick: b0 down b1 right b8 up b9 left b15 fire')
V(0x05C, 'g_JoyPrev', 'previous frame joystick')
V(0x05E, 'g_ArthurSprCtl', '4 longs: SPRxPOS/SPRxCTL pairs for sprites 0-3')
V(0x06E, 'g_ScrollTileX', 'scroll position in 16-pixel tiles')
V(0x070, 'g_ScrollTileY')
V(0x072, 'g_ScrollFineX', 'fine scroll -15..15')
V(0x074, 'g_ScrollFineY')
V(0x076, 'g_CameraX', 'camera world position in pixels')
V(0x078, 'g_CameraY')
V(0x07A, 'g_CamDeltaX')
V(0x07C, 'g_CamDeltaY')
V(0x082, 'g_NewTileX')
V(0x084, 'g_NewTileY')
V(0x086, 'g_CamMinX', 'left scroll limit (scrolling is one-way)')
V(0x088, 'g_CamMinY')
V(0x08A, 'g_LevelOriginX')
V(0x08C, 'g_LevelWidth')
V(0x08E, 'g_LevelOriginY')
V(0x090, 'g_LevelHeight')
V(0x092, 'g_MapPtr', 'current level map (block indices)')
V(0x09A, 'g_Level', 'level 0-6 (per-player block starts here, P2 copy at +$10)')
V(0x09C, 'g_Weapon', '0 torch 1 lance 2 axe 3 cross 4 dagger (cross needed on level 6)')
V(0x09E, 'g_Score', 'BCD score')
V(0x0A2, 'g_NextExtraLife', 'BCD score for next extra life (also AddScore accumulator end)')
V(0x0A6, 'g_Lives')
V(0x0A7, 'g_Checkpoint', 'set once the half-way point is passed')
V(0x0A8, 'g_ExtraLives', 'extra lives awarded so far (20000, 70000, then every 70000)')
V(0x0A9, 'g_ShowIntro', 'non-zero: play the opening kidnap cutscene first')
V(0x0BA, 'g_ShownScore', 'score last drawn on the HUD / hi-score name ptr in entry mode')
V(0x0BE, 'g_HiScores', '10 BCD longs, top score first')
V(0x0E6, 'g_ArthurX', 'world X (also cursor column in name entry)')
V(0x0EA, 'g_ArthurY', 'world Y, increasing upwards (cursor row in name entry)')
V(0x0EE, 'g_ArthurAux')
V(0x0F0, 'g_ArthurVelX')
V(0x0F4, 'g_ArthurVelY')
V(0x0F8, 'g_ArthurAnim', 'animation script pointer')
V(0x0FC, 'g_ArthurPlatform', 'platform slot Arthur is riding')
V(0x100, 'g_ArthurShownFrame', 'frame last copied into sprite RAM')
V(0x101, 'g_ArthurFrame', 'requested sprite frame (negative = mirrored)')
V(0x102, 'g_ArthurAnimTimer')
V(0x103, 'g_ArthurDir', '+1 right / -1 left')
V(0x105, 'g_ArthurFacing')
V(0x104, 'g_LadderDir', 'ladder climb direction')
V(0x106, 'g_Crouching', 'down held (also: 3 initials buffer during high-score entry)')
V(0x107, 'g_Jumping', 'airborne, rising')
V(0x108, 'g_Falling', 'airborne, descending / not on floor')
V(0x109, 'g_FireCooldown', 'frames until the next throw')
V(0x10A, 'g_OnPlatform')
V(0x10B, 'g_OnLadder')
V(0x10C, 'g_StateTimer')
V(0x10D, 'g_NoArmour', 'Arthur has lost his armour')
V(0x10E, 'g_ArthurState', '0 normal, 1 hit, 4 time-up death, 7 fell')
V(0x10F, 'g_ArthurFlash', 'invulnerability flashing')
V(0x110, 'g_FrogTimer', 'magician curse: Arthur is a frog while non-zero')
V(0x111, 'g_KeyState', 'end-of-level key sequence')
V(0x112, 'g_LevelFileEnd')
V(0x116, 'g_LevelFileAddr')
V(0x196, 'g_BlitListPtr')
V(0x3DA, 'g_BlitQueueA')
V(0x3DE, 'g_BlitQueueB')
V(0x3EA, 'g_RestoreListA')
V(0x3EE, 'g_RestoreListB')
V(0x872, 'g_SpawnQuota', '16 bytes, one per enemy type: how many more the spawners may create; a handler gives one back when its enemy leaves')
V(0x882, 'g_HiNames', '10 x 3 initials')
V(0x8A0, 'g_SpecialObjs', '2 slots x $20 (key, cutscene actors)')
V(0x8E0, 'g_Shots', '4 weapon slots x $26')
V(0x978, 'g_EnemyShots', '6 slots x $1C')
V(0xA20, 'g_Spawners', '16 enemy spawners x $C, one per enemy type')
V(0xAE0, 'g_Items', '30 slots x $1C - platforms / pickups / pots')
V(0xE28, 'g_Enemies', '40 slots x $3C - enemy objects')
V(0xE64, 'g_Enemy1', 'second enemy slot (used by cut-scenes)')

# ======================================================================
# Routine names, headers and comments
# ======================================================================
N(0x80, 'HunkHeader', """AmigaDOS hunk header, left in place.
The bootblock loads this file raw to $80 and jumps to $A0 (first code byte),
so the header and the HUNK_END at the end are never processed by DOS.
The executable is pre-relocated for $80; there is no reloc hunk.""")
N(0xA0, 'ProgramEntry', "Program entry point (bootblock does JMP $20(a0) with a0=$80).")
N(0xA4, 'MapBlockIndex', """=== DATA: level map / tile tables (to $5A7C) ===
The level map is one byte per 256x256-pixel cell (32 cells per row).
MapBlockIndex ($A4):  cell byte -> 256-byte attribute page in TileAttr
BlockTiles   ($114):  64 bytes per cell = 8x8 grid of 32x32-pixel tiles
TileAttr    ($1B14):  8 bytes per 32x32 tile: bytes 0-3 = profile index of
                      each 16x16 quadrant, bytes 4-7 = their flags
                      (bits 6-7 = solid/ladder)""")
N(0x114, 'BlockTiles'); N(0x1B14, 'TileAttr')
N(0x3B14, 'LevelItemLists', "Per-level item/platform placement lists (word offsets, then count.w + 6-byte entries: type,param,x.w,y.w)")
N(0x3B22, 'LevelEnemyLists', """Per-level enemy placement lists (word offset table for levels 0-6).
Each list: count.w then 6-byte records type.b, param.b, x.w, y.w.
Type distribution (type:count):
 L0 {1:5, 5:1, 17:4}   L1 {1:6, 10:9, 17:2}  L2 {1:11, 5:3, 18:4}
 L3 {5:2, 14:14}       L4 {1:3, 5:1, 6:1, 9:6, 10:5}
 L5 {5:4, 6:2, 9:11}   L6 {13:1}""")
N(0x40AA, 'WallProfileR', "Per-tile wall offsets used when walking right")
N(0x41AA, 'WallProfileL', "Per-tile wall offsets used when walking left")
N(0x42AA, 'FloorProfile', "Per-tile floor height used by ArthurFloorCheck")
N(0x43EE, 'LevelBossCountdown'); N(0x43F6, 'LevelSpawnQuota', "Spawn quota per enemy type (16 bytes per level), copied to g_SpawnQuota at level start")
N(0x4466, 'LevelBounds', "4 bytes per level: originX, width, height, originY (in 256-pixel units)")
N(0x4482, 'LevelTimeStart', "Level time limit (BCD mm:ss word) per level")
N(0x4490, 'LevelTimeCheckpoint', "Level time limit after the half-way checkpoint")
N(0x449E, 'LevelStartPos', "Arthur start X,Y per level (bytes)")
N(0x44AC, 'LevelCheckpointPos', "Arthur restart X,Y after the checkpoint")
N(0x44BA, 'LevelMapTable', "Word offsets to each level map")
N(0x44D6, 'LevelMaps'); N(0x4637, 'MapZoneTable', 'Map zone number for each WorldMap cell (same layout: 32 x 11 + the throne room).\nZone 0 = no spawners. See docs/SPAWNS.md for the decoded zones per level.'); N(0x4798, 'ZoneSpawners', 'Per zone: byte offset to its spawner list (format at UpdateMapZone)'); N(0x48D5, 'SpawnScripts', 'Per enemy type: byte offset to a table of word offsets to its spawn scripts (format at UpdateSpawners)')
N(0x4FB0, 'GamePalette', "32 colour words loaded into COLOR00-31 at start-up")
N(0x53AA, 'SpriteFrameOffsets'); N(0x543C, 'BobFrameOffsets')
N(0x540E, 'ItemBoxSizes'); N(0x5420, 'EnemyBoxClass'); N(0x5426, 'BoxSizeTable', "width,height byte pairs indexed by object +$13")
N(0x5464, 'HudSpriteCtl', "SPRxPOS/CTL words for the HUD sprites 4-7")
N(0x5474, 'HudSpriteDataA'); N(0x54F4, 'HudSpriteDataB'); N(0x5574, 'HudLivesIcon')
N(0x55DC, 'WeaponIcons', "$80 bytes per weapon icon, drawn into HUD sprites")
N(0x585C, 'HudTimerSprA'); N(0x596C, 'HudTimerSprB')

N(0x5A7C, 'MapTileAt', """MapTileAt - find the attribute entry for a world position
In:  d6 = world X, d7 = world Y   (g_MapPtr = current level map)
Out: a1 -> TileAttr entry for the 16x16 quadrant containing the point
     (a1)  = profile index (floor/wall height tables)
     4(a1) = flags, bits 6-7 = solid/ladder""")
N(0x5AE2, 'CrashReset', """CrashReset - target of every CPU exception vector ($8-$2C, $3C).
Writes RESET / JMP $0.L ($4E70 $4EF9 0000) to address 0 and jumps there:
any bus error, illegal instruction, trace etc. reboots the machine.
This doubles as an anti-tamper / anti-debug measure.""")
N(0x5AEE, 'Start', """==================================================================
Start - one-time initialisation
 - point all exception vectors at CrashReset, autovectors at it too
 - a6 = GLOBALS, USP = GLOBALS (user mode stack lives below it)
 - load file $7F9C (tracks 33-36): Arthur sprite graphics, interleave
   and convert into the 8 sprite planes at $1DE34-$26E34
 - build HUD sprite data, load the remaining common files
 - initialise hi-score table, copper lists, screen buffers
 - install interrupts (InitHardware), show the title, then drop
   to user mode and spin: the whole game runs in interrupts.
==================================================================""")
C(0x5B2A, 'USP = globals block (user-mode stack grows down from here)')
C(0x5B30, 'load Arthur sprite file (tracks 33-36) to $37468')
C(0x5CCC, 'load file tracks 57    -> $1CF8E')
C(0x5CD4, 'load file tracks 58    -> $1A298')
C(0x5CDC, 'load file tracks 59-60 -> $1B4CC')
C(0x5CE4, 'load file tracks 61    -> $37468 (font/mask source)')
C(0x5D2E, 'load music/sfx player (tracks 126-131) -> $28E54')
C(0x5D36, 'load copyright screen')
C(0x5DD2, 'unpack title picture (ByteRun1-style RLE) into SCREEN_0')
C(0x5E26, 'clear screen area')
C(0x5E2A, 'InitHardware: copper, DMA, interrupts, CIA keyboard')
C(0x5E32, 'load level-0 graphics file while the title shows')
C(0x5E36, 'wait 500 VBLs (10 s) on the title screen')
C(0x5EA6, 'enter user mode (clear S bit) ...')
C(0x5EAA, '... and idle forever; everything else is interrupt driven')
N(0x5EAA, 'IdleLoop')
N(0x5EAC, 'RedrawEntry', """RedrawEntry - the VBL handler patches the return PC to here when a
full redraw is pending (g_RedrawPending). Runs in user mode, outside
the interrupt, then falls into its own idle loop.""")

N(0x5EB6, 'Level1Logic', """==================================================================
Level1Logic - LEVEL 1 (SOFTINT) handler = the game's main loop
The VBL handler raises SOFTINT each frame unless the previous frame's
logic is still running, so this runs at most once per frame at IPL 1,
letting the VBL/keyboard interrupts pre-empt it.
Dispatches on g_GameState:
   0 -> InGame        1 -> AttractTitle      2 -> AttractHiScores
==================================================================""")
N(0x5ED0, 'GameStateTable')
N(0x5EDC, 'AttractTitle', "Attract state 1: credits/title text, 400 frames")
N(0x5F2E, 'AttractHiScores', "Attract state 2: high-score table, 200 frames")
N(0x5F74, 'CheckGameStart', """Start a game: fire (CIA-A PRA bit 7) starts with the current mode,
F1 = one player, F2 = two players.  Resets both player blocks
(level 0, weapon 1 = lance, 7 lives, intro cut-scene pending).""")
C(0x5F7E, 'F1 pressed?'); C(0x5F8C, 'F2 pressed?')
C(0x5FB6, 'lives = 7'); C(0x5FBC, 'weapon = 1 (lance)'); C(0x5FCE, 'play opening cut-scene')
N(0x6006, 'StartGame')
N(0x60A6, 'DrawNameGrid', "Draw the 13x5 letter grid for high-score name entry (d5 = highlighted cell)")
N(0x6136, 'NameBlank', "Replacement initials '504' used when the player leaves the name blank")
N(0x6139, 'NameCheat', "Initials stored when the cheat is entered")
N(0x613C, 'NameEntry', """High-score name entry (joystick moves cursor, fire selects).
'END' cell (index $40) commits the name.
CHEAT: if the three initials are ')!(' ($29 $21 $28) g_CheatOn is set:
Arthur never loses a life, and once his armour is gone (g_NoArmour) enemies and
enemy shots no longer hit him - he can only lose his armour once.""")
C(0x61D0, "initials == ')!(' ?"); C(0x61D6, 'g_CheatOn = result')
C(0x61E2, "initials blank?")
N(0x62A6, 'DrawCreditsScreen'); N(0x6372, 'DrawHiScoreTable')
N(0x645E, 'InGame', """==================================================================
InGame - dispatch on g_SubState
   0 LoadLevel        1 PlayLevel        2 AfterDeath/NextPlayer
   3 GameOver/HiScore 4 LevelComplete    5 IntroCutscene
   6 Ending           7 WeaponUseless (no cross on level 6 boss)
==================================================================""")
N(0x646A, 'InGameStateTable')
N(0x648A, 'LevelComplete', "Sub state 4: walk Arthur off, show 'BONUS' and award level bonus, advance g_Level (wraps 6->0)")
N(0x6584, 'TxtBonus'); N(0x658A, 'TxtBonusAmounts', "5000,5000,10000,10000,15000,15000 per level")
N(0x657E, 'LevelBonusIndex', "score-table index of the bonus per level")
N(0x65EE, 'GameOver', "Sub state 3: 'GAME OVER PLAYER ONE/TWO', then high-score insertion and name entry")
N(0x674C, 'AfterDeath', "Sub state 2: next life / switch player in 2-player games / back to attract")
N(0x67C4, 'LevelLoadTables')
N(0x682C, 'LoadLevel', """Sub state 0: load the level.
 - file $7FA6 (track 37)      -> BOB_GFX_A ($311E8)
 - file $7FB0 (tracks 38-56)  -> SCREEN_0 area (enemy graphics)
 - level file via index $7F8E -> LEVEL_FILE ($65548)
then builds frame pointer tables with BuildFrameTable.""")
C(0x6834, 'disable copper DMA while loading')
C(0x6850, 'load per-level file (tracks 84-109)')
N(0x68C0, 'PlayLevel', "Sub state 1: in-level play. $2B: 0 = progress map, 1 = set up level, 2 = play")
N(0x68DA, 'SetupLevel', "Initialise map pointer, timer, start position, scroll limits and all object tables")
N(0x6BF2, 'LogicExit', "Common exit: restore registers and RTE")
N(0x6BF8, 'LevelCheckpointX', "world X of the half-way checkpoint per level")
N(0x6C06, 'LevelMusic')
N(0x6C20, 'PlayFrame', """One frame of play:
 Esc aborts, Space pauses (fire resumes), then Arthur, enemies, shots,
 items, collisions, timer, checkpoint, extra lives, HUD score,
 camera/scroll, BOB drawing, sprite positions and buffer swap.""")
C(0x6C20, 'Esc = abort game'); C(0x6C84, 'Space = pause')
C(0x6C94, 'Arthur control / state machine')
C(0x6CDC, 'special objects (key, cut-scene actors)')
C(0x6CE0, 'Arthur weapon shots'); C(0x6CE4, 'enemy projectiles'); C(0x6CE8, 'enemies')
C(0x6CEC, 'items / platforms / pots'); C(0x6CF0, 'enemies vs Arthur')
C(0x6CF4, 'shots vs pots'); C(0x6CF8, 'shots vs enemy projectiles (cross blocks them)')
C(0x6CFC, 'enemy projectiles vs Arthur'); C(0x6D00, 'background zone / animated tiles')
C(0x6D04, 'animate background tiles')
C(0x6D08, 'every 64 frames: tick the BCD level timer')
C(0x6D3E, 'time up: Arthur dies (state 4)')
C(0x6D5E, '0:15 left: warning sound')
C(0x6D80, 'past the half-way point? -> checkpoint')
C(0x6DA8, 'every 8 frames: extra-life check')
C(0x6E24, 'Arthur below the bottom of the map -> fell to death')
C(0x7198, 'cheat: lives never decrease')
N(0x71EC, 'Ending', "Sub state 6: princess rescued - 'CONGRATULATIONS ! THIS STORY HAS A HAPPY ENDING.' then game over")
N(0x7344, 'TxtCongratulations')
N(0x73AC, 'WeaponUseless', "Sub state 7: 'THIS WEAPON IS USELESS ! GET A CRUCIFIX AND TRY AGAIN.' - back to level index 4")
N(0x7402, 'IntroCutscene', "Sub state 5: opening scene - Arthur and the princess, the demon carries her off")
N(0x7736, 'ProgressMap', "Between-level progress map: unpack picture from file $7FE2 (tracks 62-63), scroll across, mark level")
N(0x7810, 'ProgressMapMarkers')
N(0x789A, 'SetBitplanePtrs', "Write bitplane pointers + BPLCON1 fine scroll into the back copper list")
N(0x7920, 'SetMapBitplanePtrs', "Same for the progress-map copper list")
N(0x799A, 'TxtTakeKey')
N(0x79B6, 'EndOfLevelKey', """The key that drops when the boss dies ('TAKE A KEY FOR COMING IN !').
Touching it sets sub state 4 (LevelComplete).""")
N(0x7AEC, 'UpdateMapZone', """Look up the map zone of the cell under the camera (g_ScrollTileX/Y >> 4, in MapZoneTable). On a change, stop the spawners
(except those flagged to keep running) and start the zone's list from ZoneSpawners:
count.b, then per spawner two bytes: hi nibble of byte 1 = enemy type (= spawner slot),
lo nibble of byte 1 / lo nibble of byte 2 = script number, hi nibble of byte 2 = flags
(bit 0 world coordinates, bit 1 run once). Types with ZoneFlags = 0 only spawn in a zone
further on than any reached before (no respawns when walking back).""")
N(0x7BC8, 'ZoneFlags')
N(0x7CD8, 'ClearHudArea')
N(0x7CEA, 'InitHardware', """Display, audio and interrupt set-up:
 BPLCON0 $5200 (5 planes), DDF $40-$C0, DIW $34A1-$24A1, modulos $92
 all audio channels silent, vector $60 = MUSIC_PLAYER
 CIA-A: serial (keyboard) interrupt only
 vectors: $64 L1 = Level1Logic, $68 L2 = KeyboardIRQ, $6C L3 = VblIRQ
 INTENA = SOFTINT|PORTS|VERTB, waits for line $12C before returning""")
N(0x7E0E, 'CopperTemplate'); N(0x7F8E, 'LevelFileIndex', "word offsets (from each entry) to the level file records below, indexed by g_Level")
N(0x7F9C, 'FileTable', """=== File table: dest.L, length.L, start_track.W ===
Passed in a1 to LoadFile.""")
N(0x7FA6, 'FileEnemyGfxA'); N(0x7FB0, 'FileEnemyGfxB'); N(0x7FBA, 'FileTrk57'); N(0x7FC4, 'FileTrk58')
N(0x7FCE, 'FileTrk59'); N(0x7FD8, 'FileTrk61'); N(0x7FE2, 'FileProgressMap'); N(0x7FEC, 'FileMusic')
N(0x7FF6, 'FileTitlePic'); N(0x8000, 'FileLevel0'); N(0x800A, 'FileLevel1'); N(0x8014, 'FileLevel2')
N(0x801E, 'FileLevel3'); N(0x8028, 'FileLevel4'); N(0x8032, 'FileLevel5'); N(0x803C, 'FileLevel6')
N(0x8046, 'CameraJump'); N(0x8082, 'SwapScreens', "Rotate the four screen and copper buffer pointers, reset restore lists")
N(0x80DC, 'ShowBackBuffer', "Wait for the copper interrupt, point COP2LC at the new list and swap draw/display buffers")
N(0x813C, 'ArthurSpritePos', "Compute SPRxPOS/CTL for Arthur's two attached sprite pairs (hidden while flashing)")
N(0x81B8, 'SwapPlayers', "Exchange the two 16-byte per-player blocks and toggle g_CurPlayer")
N(0x81D2, 'ArthurFloorCheck', "Probe the map under Arthur's feet; snaps Y to the floor. Out: N set = in the air")
N(0x8240, 'PlatformSizes')
N(0x824A, 'ArthurOnPlatform', "d3,d4 = probe point. Out: Z clear if standing on a moving platform/item")
N(0x82EE, 'ArthurSetAnim', "a1 = animation table (two variants selected by facing)")
N(0x8302, 'ArthurAnimate', "Step Arthur's animation script; armour-less frames are +$10")
N(0x8348, 'ArmourDebris')
N(0x8354, 'ArthurHit', "State 1: armour flies off as 4 debris 'shots' (sfx 1), or death if already naked")
N(0x83C0, 'ArthurKnockback'); N(0x8408, 'ArthurKnockFly'); N(0x8418, 'ArthurLand', "State 4: lose armour (flash 120 frames) or begin dying")
N(0x847E, 'ArthurDie1'); N(0x849E, 'ArthurDie2'); N(0x84B2, 'ArthurDie3', "Sets g_PlayerDied when the death animation finishes")
N(0x84C2, 'ArthurUpdate', """==================================================================
ArthurUpdate - Arthur's state machine (g_ArthurState)
 0 normal  1 hit  2 knockback  3 knockback flight  4 landed
 5-7 death animation
==================================================================""")
N(0x84F0, 'ArthurNormal'); N(0x8582, 'ArthurFrog', "Normal state while transformed into a frog (g_FrogTimer)")
N(0x8600, 'ArthurJump', "Jump physics: X += velX, Y += velY, velY -= $3D90 per frame")
N(0x8698, 'ArthurFall')
N(0x8744, 'ArthurCrouch')
N(0x8772, 'ArthurReadLeftRight', "Joystick left/right: set direction and walk animation")
N(0x87E6, 'ArthurReadUpDown', "Up: climb ladder or jump (sfx 4). Down: descend ladder or crouch")
N(0x898C, 'MaxShotsPerWeapon', "torch 2, lance 3, axe 2, cross 3, dagger 3")
N(0x8992, 'ArthurFire', "On fire press: spawn a shot of type g_Weapon if a slot is free (sfx 6)")
N(0x8A64, 'ArthurWalk', "Walk 1.125 px/frame with wall checks")
N(0x8ABE, 'WallCheckRight'); N(0x8B16, 'WallCheckLeft')
N(0x8B5C, 'ArthurClimb'); N(0x8B74, 'LadderCheck', "Is there a ladder tile at d6,d7? Snaps X to the ladder")
N(0x8BAC, 'ArthurAnims', "Arthur animation tables")
N(0x8C8A, 'ExtraLifeCheck', "Award a life at 20000, 70000, then every 70000 (BCD compare)")
N(0x8E08, 'EnemyVsArthur', "Enemy bodies vs Arthur (skipped while flashing/dying; cheat skips while armoured)")
N(0x8F4E, 'EnemyShotsVsArthur')
N(0x916A, 'UpdateShots', """Arthur's weapon shots (4 slots x $26 at g_Shots).
Handler = ShotTable[(type*4 + state)]: type 0 torch, 1 lance, 2 axe,
3 cross, 4 dagger, 5 armour debris, 6 special""")
N(0x91A2, 'ShotTable'); N(0x9202, 'ShotSpeeds')
N(0x9360, 'ShotArcMove', "Ballistic fall (torch, axe): X += vx (slowing by $BA1 a frame to 0), Y -= vy\n(vy growing by $FF0 a frame up to 5 px). Ends with ObjectMapCollide: Z set = landed.")
N(0x95D4, 'EnemyHitByShot')
N(0x9704, 'ShotsVsEnemyShots', "Cross (weapon 3) blocks most enemy projectiles; others only hit type 5")
N(0x9842, 'ShotsVsPots', "Shots break item type 1 (pots) to release their contents")
N(0x98FA, 'UpdateSpecialObjs')
N(0x9C58, 'UpdateEnemyShots', "Enemy projectiles (6 slots x $1C at g_EnemyShots)")
N(0xA1E4, 'QueueEnemyDraw'); N(0xA398, 'QueueObjectDraw', "Add object to the BOB list using BoxSizeTable for its origin")
N(0xA3F4, 'UpdateItems', "Items: triggers, pickups, scenery and platforms (30 slots x $1C at g_Items).\nType 0 is drawn only for params 2+, type 1 is drawn into the background instead.")
N(0xA9A6, 'UpdateSpawners', """Enemy spawners (16 slots x $C at g_Spawners, slot = enemy type).
Slot: +0 active, +1 entries left, +2 script pointer, +6 script start, +$A frames to the
next spawn, +$B flags (bit 0 world coords, bit 1 run once, bit 2 new zones only).
Script (SpawnScripts): count.w, then per entry x.w, y.w (camera-relative unless flag
bit 0), param.b, delay.b. A spawn needs a free enemy slot and g_SpawnQuota[type] > 0.
Type 7 (the Magician) appears at the last shootable scenery hit instead; zombies 128 px further
right. Every 6th spawned enemy carries a bonus (special object 0) - see BonusKinds.""")
N(0xAB8E, 'SetBoxClass', "Change object size class keeping its feet on the ground")
N(0xABBC, 'SetAnimIndexed', "a0 = table of word offsets, index = +$12(a5)")
N(0xABC8, 'SetAnim', "Start animation script a0 on object a5")
N(0xABD0, 'Animate', "Step object animation: script = (frame.b, time.b [bit7: loop, offset.w follows])")
N(0xABFC, 'UpdateEnemies', """==================================================================
UpdateEnemies - 40 enemy slots x $3C at g_Enemies.
Slot layout: +0 active  +1 on-screen  +2 param  +3 state (0 main,
1 2nd phase, 2 killed, 3 remove)  +4/+5 sub states  +6 X.l  +$A Y.l (16.16)
+$E move table  +$12 dir/anim index  +$13 size class  +$14 anim ptr
+$18 frame  +$19 anim timer  +$1A type (EnemyTypeTable)  +$1B hp/flags
==================================================================""")
N(0xAC52, 'EnemyTypeTable', """Enemy handler per type (+$1A). (Superseded below by the full list.)""")
N(0xAC9E, 'BossKilled', "Last boss hit: level 6 -> Ending, level 5 without cross -> WeaponUseless, else drop the key")
N(0xACEE, 'OnScreenBoxes')
N(0xAD1A, 'CheckOnScreen', "Set +1(a5) when the object is inside the visible window")
N(0xAD54, 'CheckFarAway', "Mark object for removal (state 3) when far outside the camera")
N(0xAD7E, 'ApplyMoveTable', "Add the (dx,dy) pair selected by +$12 from move table +$E")
N(0xADA4, 'DirectionToArthur', """Out: d0 = 16-way direction from object a5 to Arthur: 0 right, 4 down, 8 left,
12 up (clockwise on screen). Picks one of five 4-entry tables (one entry per quadrant)
by the slope |dy|/|dx|. Data bug: the 45-degree table gives 5 instead of 6 for
'left and below'.""")
N(0xAE26, 'Random', "Out: d0.b = pseudo-random byte (shift register in g_RandSeed)")
N(0xAE42, 'ScoreValues', "BCD score values indexed by AddScore")
N(0xAE9E, 'AddScore', "d0 = index into ScoreValues; BCD add to g_Score")
N(0xAEB4, 'DrawWeaponIcon', "Copy the current weapon's icon into HUD sprites")
N(0xAF26, 'HudDigit'); N(0xAF74, 'DrawLives'); N(0xAF96, 'DrawTimer')
N(0xAFD6, 'PrintBCD', "Print 7-digit BCD d6 at column d1, row d2 (leading zeros blank)")
N(0xB01A, 'PrintString', "Print zero-terminated string a3 at column d1, row d2")
N(0xB026, 'PrintHexByte', "Unreferenced: print d0 as two hex digits (left-over debug helper)")
N(0xB0B0, 'PrintChar', "Draw character d0 using the font at MASK_BUF; colours g_TextShadow/Ink/Paper")
N(0xB798, 'TxtPlayer', "=== Text strings (credits: program R Frankish, graphics D Percival, sound M Cooksey) ===")
N(0xB9A2, 'NameGridLetters')
N(0xB9EC, 'RestoreBackground', "Blit saved background back under last frame's BOBs")
N(0xBA3E, 'DrawBobs'); N(0xBA5C, 'DrawBob', "Masked blit of one BOB (cookie-cut, minterm $FCA)")
N(0xBCBA, 'WaitBlitIRQ', "Unreferenced")
N(0xBCC8, 'PlaySfx', "d0 = effect number: calls MUSIC_PLAYER with command 2")
N(0xBCD8, 'KeyboardIRQ', """Level 2 (PORTS) - CIA-A serial keyboard.
Reads SDR, handshakes via CRA SPMODE for ~85us, decodes the raw
keycode (NOT + ROR 1); key-down codes go to g_RawKey and the ASCII
equivalent from KeyAsciiTable to g_AsciiKey.""")
N(0xBD5A, 'KeyAsciiTable')
N(0xBDC2, 'VblIRQ', """==================================================================
VblIRQ - Level 3 vertical blank
 - removes the interrupted SR from the stack into g_SavedSR
 - sets HUD sprite (4-7) and Arthur sprite (0-3) control words,
   copies Arthur's new frame into sprite RAM when it changes
   (negative frame number = mirrored set at +$2A)
 - g_VblCount++, reads the joystick into g_Joy (fire = bit 15)
 - ticks the music player (vector $60, d0 = 0)
 - if the logic interrupt is not already running and g_SkipLogic is
   clear, raises SOFTINT -> Level1Logic runs next
 - if returning to user mode with g_RedrawPending set, rewrites the
   return address to RedrawEntry so the redraw runs outside IRQs
==================================================================""")
C(0xBF64, 'JOY1DAT -> decode to b0 down, b1 right, b8 up, b9 left')
C(0xBF76, 'fire button -> bit 15')
C(0xBF8E, 'music player tick')
C(0xBFAE, 'INTREQ = SET|SOFTINT -> run Level1Logic')
N(0xBFDE, 'RedrawScreen', "Full redraw of the playfield from the map (used after scroll jumps); sets g_RedrawDone")
N(0xC148, 'CollisionBoxes')
N(0xC15E, 'ObjectMapCollide', """Floor test for object a5: looks for floor under the bottom-left, then the bottom-right\ncorner of its collision box. Floor found: Y is moved up onto it, d0 = 0 (Z set).\nNo floor under either corner: d0 = -1 (Z clear).""")
N(0xC1FC, 'DrawPotsOnRedraw')
N(0xC44E, 'NullRoutine')
N(0xC450, 'BuildFrameTable', "Build frame pointer table from offsets; d0 = bitmask of frames present")
N(0xC476, 'LoadFile', """==================================================================
LoadFile - the game's copy of the bootblock trackloader
In: a1 -> file record: dest.L, length.L, start_track.W
Out: a5 = end of loaded data
Track format: one block per track after DSKSYNC $A245 (set by the
boot loader), track-number word, $62A longs of odd/even MFM data and
a checksum long = NOT(sum). Reads $1900 words into $33FE8 by DMA.
Up to 8 retries per track; a bad track number re-seeks via track 0.
==================================================================""")
N(0xC4FE, 'StepHead', "Pulse the step line, wait 3ms (17ms on direction change) on CIA-B TOD")
N(0xC544, 'WaitDiskReady')
N(0xC54C, 'ReadTrackDMA', "DSKPT = $33FE8, DSKLEN $9900 written twice, wait for DSKBLK")
N(0xC578, 'StepOut', "Unreferenced")
N(0xC580, 'DecodeTrack', "MFM decode into a5 (handles a partial last long); out d1 = stored checksum, d4 = computed, d2 = track number")
N(0xC5F6, 'SeekTrack'); N(0xC632, 'SeekTrack0')
N(0xC646, 'FindFreeEnemyShot', "Out: a4 = free slot in g_EnemyShots (or last slot)")
N(0x1222C, 'TileGfxRefs')
N(0x121FA, 'EnemyData', "=== DATA: enemy animation/movement tables and other data to the end of the code hunk ===")
N(0x1892C, 'HunkEnd', "HUNK_END and padding. The globals block (a6 = $1898C) overlays this area at run time.")

# ---- auto-generated enemy-type regions ----
REGIONS = [
  (0xC65A, 0xCBAC, 'En00_'),
  (0xCBAC, 0xD160, 'En01_'),
  (0xD160, 0xDA38, 'En02_'),
  (0xDA38, 0xDC8C, 'En03_'),
  (0xDC8C, 0xE1FA, 'En04_'),
  (0xE1FA, 0xEE1C, 'En05_'),
  (0xEE1C, 0xF422, 'En06_'),
  (0xF422, 0xF5DC, 'En07_'),
  (0xF5DC, 0x10082, 'En08_'),
  (0x10082, 0x103BA, 'En09_'),
  (0x103BA, 0x109C4, 'En10_'),
  (0x109C4, 0x10CCE, 'En11_'),
  (0x10CCE, 0x11640, 'En12_'),
  (0x11640, 0x119DA, 'En13_'),
  (0x119DA, 0x11B1A, 'En14_'),
  (0x11B1A, 0x11CC8, 'En15_16_17_'),
  (0x11CC8, 0x121FA, 'En18_'),
  (0x91A2, 0x9704, 'Shot_'), (0x993C, 0x9C58, 'Special_'), (0x9C58, 0xA1E4, 'EShot_'),
  (0xA3F4, 0xA9A6, 'Item_'), (0x84C2, 0x8C8A, 'Arthur_'), (0x645E, 0x7736, 'Game_')]
N(0xC65A, 'Enemy00', "Enemy handler for type(s) 0.\nDispatches on state +3(a5): spawn / active / hit / remove.")
N(0xCBAC, 'Enemy01', "Enemy handler for type(s) 1.\nDispatches on state +3(a5): spawn / active / hit / remove.")
N(0xD160, 'Enemy02', "Enemy handler for type(s) 2.\nDispatches on state +3(a5): spawn / active / hit / remove.")
N(0xDA38, 'Enemy03', "Enemy handler for type(s) 3.\nDispatches on state +3(a5): spawn / active / hit / remove.")
N(0xDC8C, 'Enemy04', "Enemy handler for type(s) 4.\nDispatches on state +3(a5): spawn / active / hit / remove.")
N(0xE1FA, 'Enemy05', "Enemy handler for type(s) 5.\nDispatches on state +3(a5): spawn / active / hit / remove.")
N(0xEE1C, 'Enemy06', "Enemy handler for type(s) 6.\nDispatches on state +3(a5): spawn / active / hit / remove.")
N(0xF422, 'Enemy07', "Enemy handler for type(s) 7.\nDispatches on state +3(a5): spawn / active / hit / remove.")
N(0xF5DC, 'Enemy08', "Enemy handler for type(s) 8.\nDispatches on state +3(a5): spawn / active / hit / remove.")
N(0x10082, 'Enemy09', "Enemy handler for type(s) 9.\nDispatches on state +3(a5): spawn / active / hit / remove.")
N(0x103BA, 'Enemy10', "Enemy handler for type(s) 10.\nDispatches on state +3(a5): spawn / active / hit / remove.")
N(0x109C4, 'Enemy11', "Enemy handler for type(s) 11.\nDispatches on state +3(a5): spawn / active / hit / remove.")
N(0x10CCE, 'Enemy12', "Enemy handler for type(s) 12.\nDispatches on state +3(a5): spawn / active / hit / remove.")
N(0x11640, 'Enemy13', "Enemy handler for type(s) 13.\nDispatches on state +3(a5): spawn / active / hit / remove.")
N(0x119DA, 'Enemy14', "Enemy handler for type(s) 14.\nDispatches on state +3(a5): spawn / active / hit / remove.")
N(0x11B1A, 'Enemy15_16_17', "Enemy handler for type(s) 15, 16, 17.\nDispatches on state +3(a5): spawn / active / hit / remove.")
N(0x11CC8, 'Enemy18', "Enemy handler for type(s) 18.\nDispatches on state +3(a5): spawn / active / hit / remove.")
N(0xA444, 'ItemTypeTable', 'Item handlers: 0 touch trigger / pickup, 1 shootable scenery (gravestones), 2-5 moving platforms')
N(0xA45C, 'ItemPickup'); N(0x993C, 'SpecialStateTable'); N(0x9C9C, 'EnemyShotStateTable'); N(0x9CB8, 'EnemyShotTypeTable')

# ---- loader workspace inside the exception vector table ----
M(0x28, 'LDR_TRACK', 'loader: current logical track (Line-A vector slot)')
M(0x2A, 'LDR_CYL', 'loader: cylinder the head is on')
M(0x2C, 'LDR_RETRY', 'loader: retries left (Line-F vector slot)')
M(0x2E, 'LDR_DIRFLAG', 'loader: last step direction')
M(0x3C, 'VEC_UNINIT', 'uninitialised-interrupt vector')
M(0x60, 'VEC_SPURIOUS', 'spurious-interrupt vector - holds MUSIC_PLAYER pointer')
M(0x64, 'VEC_LEVEL1'); M(0x68, 'VEC_LEVEL2'); M(0x6C, 'VEC_LEVEL3')
M(0x0, 'RESET_STUB', 'CrashReset writes RESET/JMP here')
C(0xC476, 'a5 = destination'); C(0xC478, 'd5 = length in bytes'); C(0xC47A, 'start track')
C(0xC490, 'select DF0, motor on')
C(0xC49A, 'tracks = (length + $18A7) / $18A8 (6312 bytes per track)')
C(0xC4A8, '8 attempts per track'); C(0xC4AE, 'seek to LDR_TRACK')
C(0xC4B2, 'DMA one track'); C(0xC4B6, 'decode and checksum')
C(0xC4BA, 'checksum ok?'); C(0xC4CC, 'right track number?')
C(0xC4DC, 'deselect, motor off')
C(0xC4E6, 'too many errors: recalibrate to track 0')
C(0xC54E, 'DSKPT = MFM buffer'); C(0xC556, 'DSKLEN written twice to start DMA ($1900 words)')
C(0xC562, 'wait DSKBLK')
C(0xC59C, 'checksum accumulator = -1, minus each long = NOT(sum)')
C(0xC5A4, 'even bits from second half ($18AC bytes on)')
C(0xC5AA, 'odd bits from first half')
C(0xC5B2, 'stop at the exact file length (last long may be partial)')
C(0x5B06, 'Line-A/Line-F slots ($28/$2C) left free: the loader uses them as variables')
C(0x7D68, 'vector $60 = music player (called through it by VblIRQ and PlaySfx)')
C(0x7DCA, 'level 1 autovector'); C(0x7DD2, 'level 2 autovector'); C(0x7DDA, 'level 3 autovector')
C(0x7DF4, 'INTENA = SET|INTEN|VERTB|PORTS|SOFTINT')
M(0x30EB8, 'SPRITE4B_DATA', 'second HUD sprite block (sprite reused lower down)')
M(0x30F84, 'SPRITE5B_DATA'); M(0x31050, 'SPRITE6B_DATA'); M(0x3111C, 'SPRITE7B_DATA')
M(0x33FE8, 'MFM_BUFFER', 'raw track buffer for LoadFile ($1900 words)')
C(0xBDC2, 'pop the exception SR into the globals (pushed back before RTE)')
C(0xBDD0, 'acknowledge VERTB')
C(0xBE78, 'Arthur frame changed? copy 4 x $80 bytes of sprite data')
C(0xBF5A, 'g_VblCount++'); C(0xBF5E, 'keep previous joystick state for edge detection')
C(0xBF90, 'interrupted code at IPL 1 = logic still running: skip this frame')
C(0xBFCC, 'redirect user-mode return to RedrawEntry')

# ======================================================================
# Pass 2: graphics / level formats confirmed by rendering, enemy names
# confirmed from their graphics, 1MB-build differences.
# ======================================================================
ENEMY = {0:'WoodyPig',1:'Crow',2:'PetiteDevil',3:'FlyingKnight',4:'BlueKiller',5:'RedArremer',6:'Satan',
         7:'Magician',8:'Unicorn',9:'Skeleton',10:'BigMan',11:'Zombie',12:'Dragon',13:'Astaroth',14:'Fire',
         15:'Princess',16:'Unused16',17:'Plant',18:'FirePillar'}
_tbl = {0xC65A:[0],0xCBAC:[1],0xD160:[2],0xDA38:[3],0xDC8C:[4],0xE1FA:[5],0xEE1C:[6],0xF422:[7],0xF5DC:[8],
        0x10082:[9],0x103BA:[10],0x109C4:[11],0x10CCE:[12],0x11640:[13],0x119DA:[14],0x11B1A:[15,16,17],0x11CC8:[18]}
_regs=[]
_st=sorted(_tbl)
for k,a in enumerate(_st):
    ids=_tbl[a]; nm='_'.join(ENEMY[i] for i in ids)
    N(a, 'Enemy_'+nm, f"Enemy handler, type(s) {', '.join(map(str,ids))}: {', '.join(ENEMY[i] for i in ids)}\n"
         "(identity confirmed from the type's BOB graphics set)\nDispatches on state +3(a5): 0 main behaviour, 1 type-specific second phase, 2 killed (set by EnemyHitByShot after scoring), 3 remove.")
    _regs.append((a, _st[k+1] if k+1<len(_st) else 0x121FA, ENEMY[ids[0]] + '_'))
REGIONS = _regs + [(0x91A2,0x9704,'Shot_'),(0x993C,0x9C58,'Special_'),(0x9C58,0xA1E4,'EShot_'),
                   (0xA3F4,0xA9A6,'Item_'),(0x84C2,0x8C8A,'Arthur_'),(0x645E,0x7736,'Game_')]
HEADERS[0xAC52] = """EnemyTypeTable - handler per enemy type (+$1A). Type = graphics set:
  0 Woody Pig      1 Crow (set 19 bat / set 20 red crow by param)
  2 Petite Devil   3 Flying Knight   4 Blue Killer   5 Red Arremer
  6 Satan          7 Magician (frog spell)           8 Unicorn (2-part BOB)
  9 Skeleton      10 Big Man        11 Zombie       12 Dragon
 13 Astaroth      14 Fire           15 Princess     16 (unused)
 17 Man-eater plant                 18 Fire pillar
Only a few enemies are placed (LevelEnemyLists); most are created by the spawners
(UpdateSpawners), one per type, started by the map zone under the camera."""
HEADERS[0x3B22] = """LevelEnemyLists - per-level enemy placement (word offset table, levels 0-6).
Each list: count.w, then 6-byte records: type.b, param.b, x.w, y.w
(world pixels, Y increasing upwards). These are only the placed enemies - the rest come
from the spawners (UpdateSpawners). Per level:
 L0 Crow x5, Red Arremer, Plant x4     L1 Crow x6, Big Man x9, Plant x2
 L2 Crow x11, Red Arremer x3, Fire pillar x4
 L3 Red Arremer x2, Fire x14            L4 Crow x3, Red Arremer, Satan, Skeleton x6, Big Man x5
 L5 Red Arremer x4, Satan x2, Skeleton x11            L6 Astaroth"""
HEADERS[0x3B14] = """LevelItemLists - same record format as LevelEnemyLists.
Item types: 0 touch item (trigger or point pickup), 1 shootable scenery (gravestones),
2-5 platforms - see ItemTypeTable."""
N(0x44D6, 'WorldMap', """WorldMap - ONE map shared by all levels: 32 cells x 11 rows, one byte per
256x256-pixel cell, stored bottom row first. Cell $67 = tile 0 in every position.
Each level is a rectangle of it given by LevelBounds; LevelMapTable gives
each level's map origin. Each cell byte indexes CellTiles.""")
HEADERS[0x4466] = """LevelBounds - per level: x0, x1, y1, y0 (in 256-pixel map cells)
 L0 x0-13 row 0     L1 x14-27 rows 0-1   L2 x0-13 rows 2-5   L3 x14-25 row 2
 L4 x26-28 rows 2-6 L5 x29-30 rows 6-10  L6 x31 row 10"""
N(0x1222C, 'CellTiles', """CellTiles - 256 bytes per map cell type: 16x16 grid of tile numbers
(row-major, top row first). Tile 0 is a real tile (the first in the level
file), not 'empty'. Tile graphics are in the
per-level file (LEVEL_FILE): 160 bytes per 16x16 tile = 16 rows x 5
line-interleaved bitplanes. On level 1 cells $1D/$1F use a second bank
(tile + 256).""")
HEADERS[0xBFDE] = """RedrawScreen - full redraw of the 18x16-tile playfield from the map.
For each tile: cell = WorldMap byte, tile = CellTiles[cell][row][col],
blit LEVEL_FILE + tile*160 (A->D copy, BLTSIZE $1401 = 80 lines x 1 word,
D modulo 34 into the 36-byte-wide line-interleaved screen). Afterwards
copies the screen to the second buffer and sets g_RedrawDone."""
HEADERS[0xBA5C] = """DrawBob - masked blit of one BOB.
In: a1 = frame graphics, d1,d2 = world x,y, d3 = width, d4 = height
Frame graphics are line-interleaved like the screen: each row holds the
5 planes in turn (width/8 bytes each). Colour 0 is transparent: the mask
is built on the fly by OR-ing the 5 planes into $371E8 with two blits
(minterm $FFE), then each plane is cookie-cut (minterm $FCA) into the
screen. The background under the BOB is saved first for RestoreBackground."""
N(0x4FF0, 'BobFrameDescs', """BobFrameDescs - word offsets to a frame-descriptor table per enemy type.
Descriptor (4 bytes per animation frame number +$18):
  offset.w into the type's graphics set, y-adjust.b, height.b
Width comes from the object's size class (BoxSizeTable).""")
N(0x5000, 'BobFrameDescsUnicorn'); N(0x5056, 'BobFrameDescsRedCrow'); N(0x538E, 'BobFrameDescsBat')
HEADERS[0x53AA] = """BobSetOffsets - 21 longs: offset of each graphics set inside the big BOB
file (tracks 38-56). Sets 0-18 = enemy types, 19 = bat, 20 = red crow."""
N(0x67C4, 'BobSetSizes', "21 words: byte size of each BOB graphics set (see BobSetOffsets)")
N(0x6802, 'LevelBobSetMask', """Per-level long bitmask of the BOB sets LoadLevel copies out of the big
graphics file (only the enemies used on that level are kept in memory).""")
N(0x7BD8, 'BitReverseTable', "256-byte bit-reversal table used to build Arthur's mirrored sprite frames")
HEADERS[0x5B34] = """Arthur's sprite graphics (file tracks 33-36, 42 frames of 32x32, 4 planes).
Source rows are 8 words: [L-p0 R-p0 L-p1 R-p1 L-p2 R-p2 L-p3 R-p3].
They are split into four sprite banks $2900 apart: sprites 0+1 = left 16
pixels (attached pair, 16 colours from COLOR16), sprites 2+3 = right half.
Frames: 0-14 armoured poses, 15 frog, 16-31 the same poses without armour (+$10),
32-36 skeleton (death), 37-39 frog, 40 sitting in his underwear (opening scene),
41 arms raised (end of level, ending). The second loop builds mirrored copies
(bit-reversed, halves swapped) of frames 0-39 only - 40 and 41 always face right."""
C(0x5B34, 'second pass: mirrored copies')
# where the 1MB build plays music (calls stripped from this 512K build)
for a in (0x6212,0x66E6,0x6C18,0x6C2A,0x6D3E,0x6D60,0x6E42,0x7442,0x759A,0x79E4,0x83BA,0x8CD6):
    COMMENTS[a] = (COMMENTS.get(a,'')+'  ' if a in COMMENTS else '') + '[1MB build: BSR PlayMusic here - d0 is tune no.; call removed in 512K]'
COMMENTS[0x93A2] = '[1MB build: extra sound effect $B played here]'
HEADERS[0x6C06] = """LevelMusic - tune number per level. Only the 1MB build uses it: there it is
passed to PlayMusic (player command 1). In this 512K build the lookup
is still done but the call was removed, so there is no in-game music."""
del COMMENTS[0x5B34]
C(0x5B6E, 'second pass: build the mirrored frames')
NAMES[0x53AA] = 'BobSetOffsets'
NAMES[0x543C] = 'SmallBobSetOffsets'; HEADERS[0x543C] = "Offsets of the 10 small BOB sets in file track 37 (BOB_GFX_A); pointers kept at $11A(a6)"
N(0x67EE, 'SmallBobSetSizes'); N(0x681E, 'LevelSmallBobMask')

HEADERS[0xC02E] = "cell $67 -> a0 = LEVEL_FILE (tile 0); otherwise look up the tile number.\nNote: tile 0 is still blitted - it is the first tile of the level file."


HEADERS[0x44BA] = """LevelMapTable - per level, a word offset FROM THE TABLE START ($44BA) to the
level's map origin cell (bottom-left) inside WorldMap. Rows go up in steps
of +32. Origins (row,col): L0 0,0  L1 0,14  L2 2,0  L3 2,14  L4 2,26
L5 6,30  L6 = WorldMap+352 (cell $63, the throne room).
Note L5/L6 origins are one cell right of their LevelBounds x0."""
HEADERS[0x44D6] = """WorldMap - ONE map shared by all levels: 32 cells x 11 rows plus one extra
byte (cell $63, level 6's throne room), one byte per 256x256-pixel cell,
bottom row first. Cell $67 = tile 0 in every position.
Each level's origin comes from LevelMapTable; its size from LevelBounds.
Each cell byte indexes CellTiles."""

# ---- sound driver cross-references (see sound/SOUND.md)
HEADERS[0xBCC8] = """PlaySfx - d0 = effect number (0-29). Calls the sound driver through vector $60
with command 2 (d0.l = number<<16 | 2). Driver source: sound/gng_sfx_512k.s.
Effects used here: 1 hit, 4 jump, 5 land, 6 throw, 10/12 weapon hits,
17/20 enemy events, 28 key or item collected."""
MEMC[0x28E54] = 'sound driver + 30 effects (tracks 126-131) - source: sound/gng_sfx_512k.s'
MEMC[0x28E74] = 'driver entry: d0.l = arg<<16 | cmd (0 tick, 1 tune, 2 sfx, 3 user value)'
C(0xBF88, 'command 0 = tick')

# ---- correction: tracks 82-83 are the FAST copyright/anti-piracy screen, not a title picture
NAMES[0x7FF6] = 'FileCopyrightScreen'
COMMENTS[0x5D36] = 'load FAST copyright warning screen (tracks 82-83, RLE packed) -> $4DC68'
COMMENTS[0x5DD2] = 'unpack the copyright screen (ByteRun1-style RLE) into SCREEN_0'
COMMENTS[0x5E36] = 'show the copyright warning for 500 VBLs (10 s)'
NAMES[0x7FBA] = 'FileItemGfx2'; NAMES[0x7FC4] = 'FileEnemyShotGfx'; NAMES[0x7FCE] = 'FileItemGfx'; NAMES[0x7FD8] = 'FileFont'
HEADERS[0x7FBA] = "Track 57: tail of the weapon/item/effect BOB block (follows track 59's data at $1CF8E)"
HEADERS[0x7FC4] = "Track 58: enemy projectile BOBs at $1A298 (frame table $9002)"
HEADERS[0x7FCE] = "Tracks 59-60: weapon, pickup and effect BOBs at $1B4CC (frame table $908E)"
HEADERS[0x7FD8] = "Track 61: font - every other byte is copied to MASK_BUF ($28234) at start-up"
HEADERS[0x5AEE] = HEADERS[0x5AEE].replace('show the title, then drop', 'show the FAST copyright\n   warning screen for 10 s, then drop')
COMMENTS[0x5E32] = 'load level-0 enemy graphics while the copyright screen shows'
COMMENTS[0x5E36] = 'show the copyright warning for 500 VBLs (10 s)'

# ---- pass 3: track 37 identified, HUD icons confirmed (render/out/small_bobs_t037.png, weapon_icons.png)
HEADERS[0x543C] = """SmallBobSetOffsets - 10 longs: offsets of the item/scenery images in file track 37
(BOB_GFX_A, pointers at $11A(a6)); each set is ONE image:
 0 coin  1 money bag  2 stone block  3 grass raft  4 rock  5-7 gravestones
 8 boulder platform  9 ice platform     (heights / y-adjust in SmallBobSizes)"""
N(0xA992, 'SmallBobSizes', "y-adjust.b, height.b for each of the 10 small BOB images")
N(0xA91C, 'DrawItem', "Queue an item/scenery BOB: image = ItemImageTable[type][param] -> SmallBobSets")
N(0x53FE, 'ItemImageTable')
NAMES[0x9842] = 'ShotsVsScenery'
HEADERS[0x9842] = "Shots hit item type 1 (shootable scenery: gravestones, rocks) - may release a pickup"
NAMES[0xC1FC] = 'DrawSceneryOnRedraw'
HEADERS[0xC1FC] = "Draw item type 1 scenery (gravestones etc.) straight into the background (levels 0 and 2)"
HEADERS[0xA444] = "Item handlers: 0 pickup (touch), 1 shootable scenery (gravestone/rock, may hide a pickup), 2-5 moving platforms"
HEADERS[0x55DC] = """WeaponIcons - $80 bytes per weapon (0 torch, 1 lance, 2 axe, 3 cross, 4 dagger):
16x16 pixels, 16 colours, written into two attached HUD sprite pairs (even bytes = left
8 pixels, odd = right; first $40 = planes 0-1, second $40 = planes 2-3)."""

# ---- pass 4: collision format (verified by render/out/level*_collision.png)
HEADERS[0x5A7C] = """MapTileAt - collision lookup for a world position
In:  d6 = X, d7 = Y (level-relative pixels, Y increasing upwards)
cell  = WorldMap byte at g_MapPtr + (X>>8) + (Y>>8)*32
tile  = BlockTiles[cell*64 + ((X>>5)&7)*8 + ((Y>>5)&7)]   (8x8 grid of 32px tiles,
        column-major, rows counted from the bottom of the cell)
rec   = TileAttr + (MapBlockIndex[cell]<<8) + tile*8
Out: a1 = rec + (X bit4 ? 2 : 0) + (Y bit4 ? 1 : 0)   (the 16x16 quadrant)
     (a1)  = profile (SIGN-EXTENDED when indexing the tables below)
             FloorProfile[p] = floor height 1-16 within the quadrant (0 = none)
             WallProfileR/L[p] = wall offsets; p = $40-$7D = ladder
     4(a1) = flags: bits 6-7 set = background / not solid (decorations, water)"""
HEADERS[0x42AA] = "FloorProfile - floor surface height (1-16) within a 16x16 quadrant, 0 = no floor. Indexed with the sign-extended profile byte."
HEADERS[0x40AA] = "WallProfileR - wall offset when walking right (sign-extended profile index)"
HEADERS[0x41AA] = "WallProfileL - wall offset when walking left (sign-extended profile index)"

# ---- pass 5: object structure names + enemy behaviour summaries
OBJ_FIELDS = {0x00:('O_Active','0 = free, 1 = active, 2 = dying (no shot test), bit 7 set = shots pass through'),0x01:('O_OnScreen','set by CheckOnScreen'),0x02:('O_Param','placement parameter / scratch'),
 0x03:('O_State','enemies: 0 start (set-up, for some types also their first behaviour), 1 active, 2 killed (set by EnemyHitByShot after scoring), 3 remove - ST_START .. ST_REMOVE'),0x04:('O_Step','step within the state'),0x05:('O_Step2','second-level step'),
 0x06:('O_X','X pixel (long: 16.16 with O_XFrac)'),0x08:('O_XFrac',''),0x0A:('O_Y','Y pixel, upwards (long with O_YFrac)'),0x0C:('O_YFrac',''),
 0x0E:('O_MoveTable','table of (dx,dy) words, indexed by O_Dir'),0x12:('O_Dir','direction / animation index'),0x13:('O_Size','size class (BoxSizeTable)'),
 0x14:('O_Anim','animation script pointer'),0x18:('O_Frame','current frame (BobFrameDescs index)'),0x19:('O_AnimTimer','ticks left on this frame'),
 0x1A:('O_Type','enemy / shot / item type'),0x1B:('O_HP','hits left (enemies) / flags (items)')}
OBJ_RANGES = [(0x8E08,0xA9A6),(0xAB8E,0xAE26),(0xC15E,0xC1FC),(0xC646,0x121FA)]
N(0x95C0, 'EnemyVulnerability', "Per enemy type: bitmask of weapon types that can hurt it (bit n = weapon n). Astaroth: cross only; Fire: nothing.")
N(0x9528, 'EnemyHitboxes', "Per enemy type, 8 bytes: x offset.w, width.w, y offset.w, height.w")
N(0x96F0, 'EnemyPoints', "Per enemy type: AddScore index awarded when its hit points run out")
HEADERS[0x95D4] = """EnemyHitByShot - test Arthur's shots against enemy a5.
Hitbox from EnemyHitboxes; Astaroth (type 13) can only be hit within +-9 px of his
centre line. If the weapon's bit is clear in EnemyVulnerability the shot bounces off.
Otherwise O_HP is decremented; at 0 the enemy dies (state 2) and EnemyPoints is
awarded. The CROSS (weapon 3) is not used up when it kills an enemy - it carries on."""
HEADERS[0xAE9E] = """AddScore - d0 = index i: adds the BCD long at ScoreValues + 4*(i-1) to g_Score
(the routine pre-decrements from the end of entry i). E.g. 13 = 5000, 18 = 10000."""
_EN = {
 0xC65A: ("Woody Pig", "type 0, 100 pts", "Flying pig of the level-0 forest; created by the spawners, flies in along a movement table and can drop/fire a projectile (FindFreeEnemyShot)."),
 0xCBAC: ("Crow / bat", "type 1, 100 pts", "Waits perched (gravestones on level 0, ledges elsewhere); when Arthur comes near it takes off and swoops towards him (DirectionToArthur) with some randomness. param < 3 uses the bat graphics, param = 3 the red crow. Sound effect 17."),
 0xD160: ("Petite Devil", "type 2, 100 pts", "Small flying devil: homes on Arthur (DirectionToArthur), random changes of direction, fires projectiles."),
 0xDA38: ("Flying Knight", "type 3, 100 pts", "Shielded knight flying in a wave pattern (movement table, random variation). Sound effect 20."),
 0xDC8C: ("Blue Killer", "type 4, 100 pts", "Small winged devil that drops/hops along the scenery (map collision), random behaviour. Sound effect 17."),
 0xE1FA: ("Red Arremer", "type 5, 1000 pts, 3 hits", "The red gargoyle: walks, takes off and dives at Arthur, hovers and shoots; changes size class between standing and flying. Sound effect 12 when hit."),
 0xEE1C: ("Satan", "type 6, 3000 pts, 4 hits (boss)", "Big winged demon boss of levels 4-5: flies at Arthur, fires, and on its last hit calls BossKilled (key drop / weapon check)."),
 0xF422: ("Magician", "type 7, 2000 pts", "Rises from a gravestone Arthur has shot (spawned at g_SceneryHitX/Y), throws off its cloak, casts one spell (enemy shot type 0: turns Arthur into a frog) and fades away. Sound effect 17 when killed."),
 0xF5DC: ("Unicorn (Cyclops)", "type 8, 2000 pts, 10 hits (boss)", "Boss of level 0 (one, at the gate) and level 1 (two); also on level 5. Drawn as two BOBs (legs + body)."),
 0x10082: ("Skeleton", "type 9, 100 pts", "Rises out of the floor (map collision) on the castle levels. Sound effect 17."),
 0x103BA: ("Big Man", "type 10, 500 pts, 10 hits", "Ogre that walks and charges along the floor, pauses at random and throws projectiles."),
 0x109C4: ("Zombie", "type 11, 200 pts", "Spawned at run time near Arthur: rises out of the ground (size class changes as it emerges), shambles along the floor and sinks back. Sound effect 20."),
 0x10CCE: ("Dragon", "type 12, 200 pts per segment", "Flying dragon boss of levels 2-3: a chain of segments led by the head (6 hits); the head aims and breathes fire at Arthur. Sound effects 12/20; awards 1000 extra on defeat."),
 0x11640: ("Astaroth", "type 13, 10000 pts, 10 hits, cross only (final boss)", "Seated final boss in the throne room: fires projectiles; can only be hurt by the cross, in a narrow band (see EnemyHitByShot); its last hit calls BossKilled -> Ending."),
 0x119DA: ("Fire", "type 14, cannot be hurt", "Flames of the level-3 fire bridge/cavern: animated hazard only (grows and dies away)."),
 0x11B1A: ("Princess / (unused 16) / Man-eater plant", "types 15, 16, 17", "Shared stationary handler: animates in place and, for the plant, spits projectiles (eyeballs) at Arthur when on screen. The princess uses it in the cut-scenes."),
 0x11CC8: ("Fire pillar", "type 18, 100 pts, 4 hits", "Column of fire on level 2: rises and falls in place, fires projectiles when on screen."),
}
for _a,(_n,_s,_d) in _EN.items():
    HEADERS[_a] = f"=== {_n} ({_s}) ===\n{_d}\nDispatches on O_State: 0 main behaviour, 1 type-specific second phase, 2 killed (set by EnemyHitByShot after scoring), 3 remove."

# ---- per-enemy fields and detailed handler annotations
TYPE_FIELDS = []   # (lo, hi, {offset: (name, comment)}) - names used for (a5) offsets inside [lo, hi)
import os as _os
exec(open(_os.path.join(_os.path.dirname(_os.path.abspath(__file__)),'anno_bosses.py')).read())
exec(open(_os.path.join(_os.path.dirname(_os.path.abspath(__file__)),'anno_enemies.py')).read())
exec(open(_os.path.join(_os.path.dirname(_os.path.abspath(__file__)),'anno_arthur.py')).read())
# ---- structured data blocks (emitted as readable source instead of dc.b)
import sys as _sys
_sys.path.insert(0,_os.path.dirname(_os.path.abspath(__file__)))
import spawn_data as _spd
_s,_e,_l,_lab = _spd.build(open(_os.path.join(_os.path.dirname(_os.path.abspath(__file__)),'main.bin'),'rb').read())
DATA_BLOCKS = {_s:(_e,_l)}
for _n,_a in _lab.items():
    if _a not in NAMES: NAMES[_a]=_n
import arthur_anims as _aan
_s,_e,_l,_lab = _aan.build(open(_os.path.join(_os.path.dirname(_os.path.abspath(__file__)),'main.bin'),'rb').read())
DATA_BLOCKS[_s]=(_e,_l)
for _n,_a in _lab.items(): NAMES[_a]=_n
exec(open(_os.path.join(_os.path.dirname(_os.path.abspath(__file__)),'anno_scenes.py')).read())
exec(open(_os.path.join(_os.path.dirname(_os.path.abspath(__file__)),'anno_flow.py')).read())
exec(open(_os.path.join(_os.path.dirname(_os.path.abspath(__file__)),'anno_render.py')).read())
# ---- map and tile tables as structured source (map_data.py)
import map_data as _md
HEADERS[0xA4] = """=== DATA: level map and tile tables ===
Two separate tile systems share the map (WorldMap, one byte per 256 x 256-px cell):
 graphics:  cell -> CellTiles: 16 x 16 tiles of 16 x 16 px, drawn from the level file
 collision: cell -> BlockTiles: 8 x 8 tiles of 32 x 32 px -> TileAttr record (bank
            from MapBlockIndex), which gives a profile for each 16 x 16 quadrant ->
            FloorProfile / WallProfileR / WallProfileL (see MapTileAt).
MapBlockIndex: per cell type, TileAttr bank x 8 (the value << 8 is the byte offset
of the bank: 4 banks of 256 tiles x 8 bytes)."""
HEADERS[0x114] = """BlockTiles - per cell type ($00-$67), 64 collision-tile numbers: 8 columns of 8,
each column listed from the bottom of the cell up (index = column*8 + row)"""
HEADERS[0x1B14] = """TileAttr - 4 banks of 256 collision tiles, 8 bytes each:
  profile for the quadrants left-bottom, left-top, right-bottom, right-top, then the
  four flag bytes in the same order. The game only tests flag bits 6-7: either set =
  the quadrant is ignored (background - no floor, wall or ladder).
The comment shows each quadrant's floor height (FloorProfile, 1-16 px from the bottom
of the quadrant), L for a ladder profile ($40-$7D), - for none; 'bg' if any quadrant
is flagged as background, '(unused)' past the highest tile any cell of that bank uses."""
HEADERS[0x4002] = """Graphics-set sizes (width, height in pixels) for the 1MB build's BuildMaskedGfx, which
pre-builds masks for the graphics it keeps in memory. The 512K build has the same tables
(here and after FloorProfile) but never reads them."""
HEADERS[0x402A] = """Profile tables, 256 bytes each. MapTileAt's profile byte is SIGN-EXTENDED before
indexing, so each label is in the middle: profiles $80-$FF are the 128 bytes before it.
 WallProfileR / WallProfileL - how far a wall pushes Arthur back when walking right / left
 FloorProfile - floor surface height (1-16) within the 16 x 16 quadrant, 0 = no floor"""
HEADERS[0x1222C] = """CellTiles - per map cell type ($00-$66), 16 rows of 16 graphics tile numbers, top row
first. Tile graphics are 160 bytes each in the level file (16 lines x 5 interleaved
planes); tile 0 is a real tile. Cell $67 is not in the table: RedrawScreen draws tile 0
everywhere for it. On level 1, cells $1D and $1F take their tiles from a second bank."""
for _s,_e,_l,_lab in _md.build(open(_os.path.join(_os.path.dirname(_os.path.abspath(__file__)),'main.bin'),'rb').read()):
    _hdrlines=[]
    for _ln in _l:
        _m=_ln.split(':')[0] if _ln.endswith(':') and not _ln.startswith(('\t',';')) else None
        if _m and _lab.get(_m) not in (None,_s) and _lab[_m] in HEADERS:
            _hdrlines += ['', ';'+'-'*75] + ['; '+x if x else ';' for x in HEADERS[_lab[_m]].split('\n')] + [';'+'-'*75]
        _hdrlines.append(_ln)
    DATA_BLOCKS[_s]=(_e,_hdrlines)
    for _n,_a in _lab.items(): NAMES[_a]=_n
HEADERS[0x432A] = """More graphics-set sizes for BuildMaskedGfx (1MB build only): enemy graphics (39 sets),
the second item file, enemy shots and items"""
exec(open(_os.path.join(_os.path.dirname(_os.path.abspath(__file__)),'anno_tables.py')).read())
exec(open(_os.path.join(_os.path.dirname(_os.path.abspath(__file__)),'anno_lines.py')).read())
