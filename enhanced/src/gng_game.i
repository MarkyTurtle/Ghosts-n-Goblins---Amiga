; Ghosts'n Goblins - hardware, globals and memory-map equates (both builds; BUILD_1MB selects the 1MB memory map)

CUSTOM		equ	$DFF000	; custom chip base
; custom chip register offsets
BLTDDAT     	equ	$000
DMACONR     	equ	$002
VPOSR       	equ	$004
VHPOSR      	equ	$006
DSKDATR     	equ	$008
JOY0DAT     	equ	$00A
JOY1DAT     	equ	$00C
CLXDAT      	equ	$00E
ADKCONR     	equ	$010
POT0DAT     	equ	$012
POT1DAT     	equ	$014
POTGOR      	equ	$016
SERDATR     	equ	$018
DSKBYTR     	equ	$01A
INTENAR     	equ	$01C
INTREQR     	equ	$01E
DSKPTH      	equ	$020
DSKPTL      	equ	$022
DSKLEN      	equ	$024
DSKDAT      	equ	$026
REFPTR      	equ	$028
VPOSW       	equ	$02A
VHPOSW      	equ	$02C
COPCON      	equ	$02E
SERDAT      	equ	$030
SERPER      	equ	$032
POTGO       	equ	$034
JOYTEST     	equ	$036
BLTCON0     	equ	$040
BLTCON1     	equ	$042
BLTAFWM     	equ	$044
BLTALWM     	equ	$046
BLTCPTH     	equ	$048
BLTCPTL     	equ	$04A
BLTBPTH     	equ	$04C
BLTBPTL     	equ	$04E
BLTAPTH     	equ	$050
BLTAPTL     	equ	$052
BLTDPTH     	equ	$054
BLTDPTL     	equ	$056
BLTSIZE     	equ	$058
BLTCMOD     	equ	$060
BLTBMOD     	equ	$062
BLTAMOD     	equ	$064
BLTDMOD     	equ	$066
BLTCDAT     	equ	$070
BLTBDAT     	equ	$072
BLTADAT     	equ	$074
DSKSYNC     	equ	$07E
COP1LCH     	equ	$080
COP1LCL     	equ	$082
COP2LCH     	equ	$084
COP2LCL     	equ	$086
COPJMP1     	equ	$088
COPJMP2     	equ	$08A
COPINS      	equ	$08C
DIWSTRT     	equ	$08E
DIWSTOP     	equ	$090
DDFSTRT     	equ	$092
DDFSTOP     	equ	$094
DMACON      	equ	$096
CLXCON      	equ	$098
INTENA      	equ	$09A
INTREQ      	equ	$09C
ADKCON      	equ	$09E
AUD0LCH     	equ	$0A0
AUD0LCL     	equ	$0A2
AUD0LEN     	equ	$0A4
AUD0PER     	equ	$0A6
AUD0VOL     	equ	$0A8
AUD0DAT     	equ	$0AA
AUD1LCH     	equ	$0B0
AUD1LCL     	equ	$0B2
AUD1LEN     	equ	$0B4
AUD1PER     	equ	$0B6
AUD1VOL     	equ	$0B8
AUD1DAT     	equ	$0BA
AUD2LCH     	equ	$0C0
AUD2LCL     	equ	$0C2
AUD2LEN     	equ	$0C4
AUD2PER     	equ	$0C6
AUD2VOL     	equ	$0C8
AUD2DAT     	equ	$0CA
AUD3LCH     	equ	$0D0
AUD3LCL     	equ	$0D2
AUD3LEN     	equ	$0D4
AUD3PER     	equ	$0D6
AUD3VOL     	equ	$0D8
AUD3DAT     	equ	$0DA
BPL1PTH     	equ	$0E0
BPL1PTL     	equ	$0E2
BPL2PTH     	equ	$0E4
BPL2PTL     	equ	$0E6
BPL3PTH     	equ	$0E8
BPL3PTL     	equ	$0EA
BPL4PTH     	equ	$0EC
BPL4PTL     	equ	$0EE
BPL5PTH     	equ	$0F0
BPL5PTL     	equ	$0F2
BPL6PTH     	equ	$0F4
BPL6PTL     	equ	$0F6
BPLCON0     	equ	$100
BPLCON1     	equ	$102
BPLCON2     	equ	$104
BPL1MOD     	equ	$108
BPL2MOD     	equ	$10A
BPL1DAT     	equ	$110
BPL2DAT     	equ	$112
BPL3DAT     	equ	$114
BPL4DAT     	equ	$116
BPL5DAT     	equ	$118
BPL6DAT     	equ	$11A
SPR0PTH     	equ	$120
SPR0PTL     	equ	$122
SPR1PTH     	equ	$124
SPR1PTL     	equ	$126
SPR2PTH     	equ	$128
SPR2PTL     	equ	$12A
SPR3PTH     	equ	$12C
SPR3PTL     	equ	$12E
SPR4PTH     	equ	$130
SPR4PTL     	equ	$132
SPR5PTH     	equ	$134
SPR5PTL     	equ	$136
SPR6PTH     	equ	$138
SPR6PTL     	equ	$13A
SPR7PTH     	equ	$13C
SPR7PTL     	equ	$13E
SPR0POS     	equ	$140
SPR0CTL     	equ	$142
SPR0DATA    	equ	$144
SPR0DATB    	equ	$146
SPR1POS     	equ	$148
SPR1CTL     	equ	$14A
SPR1DATA    	equ	$14C
SPR1DATB    	equ	$14E
SPR2POS     	equ	$150
SPR2CTL     	equ	$152
SPR2DATA    	equ	$154
SPR2DATB    	equ	$156
SPR3POS     	equ	$158
SPR3CTL     	equ	$15A
SPR3DATA    	equ	$15C
SPR3DATB    	equ	$15E
SPR4POS     	equ	$160
SPR4CTL     	equ	$162
SPR4DATA    	equ	$164
SPR4DATB    	equ	$166
SPR5POS     	equ	$168
SPR5CTL     	equ	$16A
SPR5DATA    	equ	$16C
SPR5DATB    	equ	$16E
SPR6POS     	equ	$170
SPR6CTL     	equ	$172
SPR6DATA    	equ	$174
SPR6DATB    	equ	$176
SPR7POS     	equ	$178
SPR7CTL     	equ	$17A
SPR7DATA    	equ	$17C
SPR7DATB    	equ	$17E
COLOR00     	equ	$180
COLOR01     	equ	$182
COLOR02     	equ	$184
COLOR03     	equ	$186
COLOR04     	equ	$188
COLOR05     	equ	$18A
COLOR06     	equ	$18C
COLOR07     	equ	$18E
COLOR08     	equ	$190
COLOR09     	equ	$192
COLOR10     	equ	$194
COLOR11     	equ	$196
COLOR12     	equ	$198
COLOR13     	equ	$19A
COLOR14     	equ	$19C
COLOR15     	equ	$19E
COLOR16     	equ	$1A0
COLOR17     	equ	$1A2
COLOR18     	equ	$1A4
COLOR19     	equ	$1A6
COLOR20     	equ	$1A8
COLOR21     	equ	$1AA
COLOR22     	equ	$1AC
COLOR23     	equ	$1AE
COLOR24     	equ	$1B0
COLOR25     	equ	$1B2
COLOR26     	equ	$1B4
COLOR27     	equ	$1B6
COLOR28     	equ	$1B8
COLOR29     	equ	$1BA
COLOR30     	equ	$1BC
COLOR31     	equ	$1BE

; CIA-A (base $BFE001, odd addresses)
CIAA_PRA    	equ	$BFE002
CIAA_PRB    	equ	$BFE102
CIAA_DDRA   	equ	$BFE202
CIAA_DDRB   	equ	$BFE302
CIAA_TALO   	equ	$BFE402
CIAA_TAHI   	equ	$BFE502
CIAA_TBLO   	equ	$BFE602
CIAA_TBHI   	equ	$BFE702
CIAA_TODLO  	equ	$BFE802
CIAA_TODMID 	equ	$BFE902
CIAA_TODHI  	equ	$BFEA02
CIAA_SDR    	equ	$BFEC02
CIAA_ICR    	equ	$BFED02
CIAA_CRA    	equ	$BFEE02
CIAA_CRB    	equ	$BFEF02

; CIA-B (base $BFD000, even addresses)
CIAB_PRA    	equ	$BFD000
CIAB_PRB    	equ	$BFD100
CIAB_DDRA   	equ	$BFD200
CIAB_DDRB   	equ	$BFD300
CIAB_TALO   	equ	$BFD400
CIAB_TAHI   	equ	$BFD500
CIAB_TBLO   	equ	$BFD600
CIAB_TBHI   	equ	$BFD700
CIAB_TODLO  	equ	$BFD800
CIAB_TODMID 	equ	$BFD900
CIAB_TODHI  	equ	$BFDA00
CIAB_SDR    	equ	$BFDC00
CIAB_ICR    	equ	$BFDD00
CIAB_CRA    	equ	$BFDE00
CIAB_CRB    	equ	$BFDF00

; ---- Memory map (fixed buffers outside the program image) ----
; [1MB] ---- Memory map (1MB build). Values used with adda g_BaseAddr are offsets from the load address;
; [1MB] ---- the rest (screens, copper lists, sprites: chip RAM) are absolute. [512K value] in comments.
RESET_STUB          	equ	$00000	; CrashReset writes RESET/JMP here
LDR_TRACK           	equ	$00028	; loader: current logical track (Line-A vector slot)
LDR_CYL             	equ	$0002A	; loader: cylinder the head is on
LDR_RETRY           	equ	$0002C	; loader: retries left (Line-F vector slot)
LDR_DIRFLAG         	equ	$0002E	; loader: last step direction
VEC_UNINIT          	equ	$0003C	; uninitialised-interrupt vector
VEC_SPURIOUS        	equ	$00060	; spurious-interrupt vector - holds MUSIC_PLAYER pointer
VEC_LEVEL1          	equ	$00064
VEC_LEVEL2          	equ	$00068
VEC_LEVEL3          	equ	$0006C
GLOBALS             	equ	GlobalsBlock	; a6 points here for the whole game (variables block; $1898C)
GLOBALS_P2          	equ	GLOBALS+$10	; player-2 view of the per-player block ($1899C)
GLOBALS_SIZE        	equ	$178C	; the globals block and the object slots
	ifd	MAP_FIX			; (build_game.py's relocation pass: the program assembled
MAP_LOW             	equ	MAP_FIX	; somewhere else, the memory map where it is at $80)
	else
MAP_LOW             	equ	GLOBALS+GLOBALS_SIZE	; ($1A118) the memory map below starts here, right after
                    			; the globals, so it moves with the program
	endc
SFX_AREA            	equ	$7D64	; the 512K effects package (at MUSIC_FILE), then the rest of the map: offsets as
                    			; the original's with the package moved to the front
COPPER_INIT         	equ	MAP_LOW+SFX_AREA+$00000	; $1A118: copper list template ($180 bytes copied from CopperTemplate)
COPPER_A1           	equ	MAP_LOW+SFX_AREA+$00078	; $1A190
COPPER_A2           	equ	MAP_LOW+SFX_AREA+$000A8	; $1A1C0
COPPER_B1           	equ	MAP_LOW+SFX_AREA+$000D8	; $1A1F0
COPPER_B2           	equ	MAP_LOW+SFX_AREA+$00108	; $1A220
COPPER_MAP          	equ	MAP_LOW+SFX_AREA+$00138	; $1A250: copper list used by the between-level progress map
ARTHUR_SPR_GFX      	equ	MAP_LOW+SFX_AREA+$03D1C	; $1DE34: Arthur hardware-sprite frames, 4 planes x $2880 apart, $80 bytes/frame
SPR_GFX_B0          	equ	MAP_LOW+SFX_AREA+$0521C	; $1F334
SPR_GFX_A1          	equ	MAP_LOW+SFX_AREA+$0661C	; $20734
SPR_GFX_B1          	equ	MAP_LOW+SFX_AREA+$07B1C	; $21C34
SPR_GFX_A2          	equ	MAP_LOW+SFX_AREA+$08F1C	; $23034
SPR_GFX_B2          	equ	MAP_LOW+SFX_AREA+$0A41C	; $24534
SPR_GFX_A3          	equ	MAP_LOW+SFX_AREA+$0B81C	; $25934
SPR_GFX_B3          	equ	MAP_LOW+SFX_AREA+$0CD1C	; $26E34
MASK_BUF            	equ	MAP_LOW+SFX_AREA+$0E11C	; $28234: byte-plane extracted from file at tracks 61
MUSIC_FILE          	equ	MAP_LOW	; first in the map (LoadSound runs first: whole tracks run on into what is loaded after it); sound driver + 30 effects (tracks 126-131) - source: sound/gng_sfx_512k.s
MUSIC_PLAYER        	equ	MAP_LOW+$00020	; $28E74: driver entry: d0.l = arg<<16 | cmd (0 tick, 1 tune, 2 sfx, 3 user value)
SPRITE0_DATA        	equ	MAP_LOW+$16AA0	; $30BB8
SPRITE4_DATA        	equ	MAP_LOW+$16B24	; $30C3C
SPRITE1_DATA        	equ	MAP_LOW+$16B60	; $30C78
SPRITE5_DATA        	equ	MAP_LOW+$16BE4	; $30CFC
SPRITE2_DATA        	equ	MAP_LOW+$16C20	; $30D38
SPRITE6_DATA        	equ	MAP_LOW+$16CA4	; $30DBC
SPRITE3_DATA        	equ	MAP_LOW+$16CE0	; $30DF8
SPRITE7_DATA        	equ	MAP_LOW+$16D64	; $30E7C
SPRITE4B_DATA       	equ	MAP_LOW+$16DA0	; $30EB8: second HUD sprite block (sprite reused lower down)
SPRITE5B_DATA       	equ	MAP_LOW+$16E6C	; $30F84
SPRITE6B_DATA       	equ	MAP_LOW+$16F38	; $31050
SPRITE7B_DATA       	equ	MAP_LOW+$17004	; $3111C
BOB_GFX_A           	equ	MAP_LOW+$170D0	; $311E8: file tracks 37 / 62-63 load address
MFM_BUFFER          	equ	MAP_LOW+$19ED0	; $33FE8: raw track buffer for LoadFile ($1900 words)
BOB_GFX_B           	equ	MAP_LOW+$1A0D0	; $341E8
SCREEN_0            	equ	MAP_LOW+$1D350	; $37468: also load address of the big graphics file (tracks 38-56) before unpacking
SCREEN_1            	equ	MAP_LOW+$28750	; $42868
SCREEN_2            	equ	MAP_LOW+$33B50	; $4DC68
SCREEN_3            	equ	MAP_LOW+$3EF50	; $59068
CLEAR_AREA          	equ	SCREEN_0+$26700	; (the original: SCREEN_0+$2D000, $64468) the HUD's planes:
                    			; moved down into the old fourth screen, which the scroller
                    			; leaves free above its storage (SCROLL_STORE, scroller.s) ...
	ifnd	TBL_SLOTS			; (build_game.py: the per-level map tables)
TBL_SLOTS           	equ	48
TBLLEN0	equ	0
TBLLEN1	equ	0
TBLLEN2	equ	0
TBLLEN3	equ	0
TBLLEN4	equ	0
TBLLEN5	equ	0
TBLLEN6	equ	0
TBLTRK0	equ	18
TBLTRK1	equ	20
TBLTRK2	equ	22
TBLTRK3	equ	24
TBLTRK4	equ	26
TBLTRK5	equ	28
TBLTRK6	equ	30
	endc
LEVEL_TABLES        	equ	CLEAR_AREA+$10E0	; the level's map tables (LoadLevelTables): at most TBL_SLOTS cells
LEVEL_SLOTS         	equ	LEVEL_TABLES	;   cell -> slot (256 bytes)
LEVEL_BLOCKS        	equ	LEVEL_SLOTS+256	;   the slots' BlockTiles (64 bytes each)
LEVEL_CELLS         	equ	LEVEL_BLOCKS+TBL_SLOTS*64	;   the slots' CellTiles (256 bytes each)
LEVEL_TABLES_END    	equ	LEVEL_CELLS+TBL_SLOTS*256
BlockTiles          	equ	LEVEL_BLOCKS	; (the names the original's code uses)
CellTiles           	equ	LEVEL_CELLS
LEVEL_FILE          	equ	LEVEL_TABLES_END	; ... and the per-level data file after them (tracks 84-109;
                    			; the level's BOB sets are copied after it): the program has
                    			; grown, and stage 2 (file $C120 + sets $DE76) must end below
                    			; $7F4DE as in the original (build_game.py checks)
ESHOT_GFX_BUF       	equ	MAP_LOW+SFX_AREA+$00180	; $1A298: enemy projectile graphics (file track 58)
ITEM_GFX_BUF        	equ	MAP_LOW+SFX_AREA+$013B4	; $1B4CC: item and explosion graphics (file track 59)
ITEM_GFX2_BUF       	equ	MAP_LOW+SFX_AREA+$02E76	; $1CF8E: item graphics 2 (file track 57)
SAVE_BUF_A          	equ	MAP_LOW+$170D0	; $311E8: background save area A ($3000 bytes; g_SaveBufA) - also BOB_GFX_A
SAVE_BUF_B          	equ	MAP_LOW+$1A0D0	; $341E8: background save area B - also BOB_GFX_B
MASK_LINE_BUF       	equ	MAP_LOW+$1D0D0	; $371E8: DrawBob: the mask built for one BOB (512K build; 640 bytes)

; ---- Global variables: offsets from a6 (GLOBALS = $1898C) ----
; [1MB] ---- Global variables: offsets from a6 (GLOBALS = load address + $1893A; offsets >= 2 are 4 more than in the 512K build) ----
g_SavedSR           	equ	$000	; VBL handler parks the interrupted SR here
G_SHIFT             	equ	0	; added to the offsets of the globals (4 in the 1MB build: g_BaseAddr comes first)
g_FrameStamp        	equ	G_SHIFT+$002	; frame counter snapshot for timed waits
g_VblCount          	equ	G_SHIFT+$004	; incremented every vertical blank
g_GameFrame         	equ	G_SHIFT+$006	; incremented every game-logic frame
g_RawKey            	equ	G_SHIFT+$008	; last raw keycode (Esc=$45, F1=$50, F2=$51)
g_AsciiKey          	equ	G_SHIFT+$009	; last key as ASCII (space=$20 pauses)
g_RandSeed          	equ	G_SHIFT+$00A	; random generator state, seeded $AAAA
g_TimeLeft          	equ	G_SHIFT+$00C	; level timer, BCD minutes.byte/seconds.byte
g_LevelDone         	equ	G_SHIFT+$00E	; set when the level is completed
g_PlayerDied        	equ	G_SHIFT+$00F	; set when Arthur has died this frame
g_BonusEvery        	equ	G_SHIFT+$010	; counts down from 6: every 6th spawned enemy carries a bonus
g_BonusCycle        	equ	G_SHIFT+$011	; 0-6: which kind of bonus the next carrier gets (BonusKinds)
g_BonusRoll         	equ	G_SHIFT+$012	; +21 per treasure bonus; on carry the treasure is the rare kind 12
g_WeaponOdds        	equ	G_SHIFT+$013	; 5 accumulators, one per weapon (bonus weapon choice); ends at $17
g_BossCountdown     	equ	G_SHIFT+$018	; bosses left to beat on this level before the key / ending (LevelBossCountdown)
g_BigEnemyCount     	equ	G_SHIFT+$019	; Red Arremer / Satan / Unicorn / Dragon currently engaged (+1 on activation, -1 on removal; never tested)
g_MapZone           	equ	G_SHIFT+$01A	; current map zone (MapZoneTable): selects the enemy spawners
g_MaxMapZone        	equ	G_SHIFT+$01B	; furthest map zone reached (spawners with ZoneFlags 0 only start beyond it)
g_RedrawPending     	equ	G_SHIFT+$01C	; set to request a full redraw: the VBL diverts user mode to RedrawEntry
g_RedrawDone        	equ	G_SHIFT+$01D	; set by RedrawScreen when finished
g_SkipLogic         	equ	G_SHIFT+$01E	; non-zero: VBL does not trigger the logic interrupt
g_TextShadow        	equ	G_SHIFT+$01F	; text colour where only the first font plane is set
g_TextInk           	equ	G_SHIFT+$020	; text colour where only the second font plane is set
g_TextPaper         	equ	G_SHIFT+$021	; text colour where both font planes are set
g_TwoPlayer         	equ	G_SHIFT+$027	; non-zero = two-player game
g_CurPlayer         	equ	G_SHIFT+$028	; 0 = player 1, $FF = player 2
g_GameState         	equ	G_SHIFT+$029	; 0 = in game, 1/2 = attract screens
g_SubState          	equ	G_SHIFT+$02A	; in-game sub state (see GameStateTable)
g_SubState2         	equ	G_SHIFT+$02B	; step within the sub state
g_SubState3         	equ	G_SHIFT+$02C	; step within g_SubState2
g_ArthurVisible     	equ	G_SHIFT+$02D	; hardware sprites 0-3 enabled
g_Spr47Visible      	equ	G_SHIFT+$02E	; hardware sprites 4-7 enabled
g_Paused            	equ	G_SHIFT+$02F
g_CheatOn           	equ	G_SHIFT+$030	; set by entering ')!(' on the high-score table: no life loss / no damage
g_ScreenFront       	equ	G_SHIFT+$032
g_ScreenBack        	equ	G_SHIFT+$036
g_ScreenSpare1      	equ	G_SHIFT+$042
g_ScreenSpare2      	equ	G_SHIFT+$046
g_CopperFront       	equ	G_SHIFT+$04A
g_CopperBack        	equ	G_SHIFT+$04E
g_CopperSpare1      	equ	G_SHIFT+$052
g_CopperSpare2      	equ	G_SHIFT+$056
g_Joy               	equ	G_SHIFT+$05A	; joystick: b0 down b1 right b8 up b9 left b15 fire
g_JoyPrev           	equ	G_SHIFT+$05C	; previous frame joystick
g_ArthurSprCtl      	equ	G_SHIFT+$05E	; 4 longs: SPRxPOS/SPRxCTL pairs for sprites 0-3
g_ScrollTileX       	equ	G_SHIFT+$06E	; scroll position in 16-pixel tiles
g_ScrollTileY       	equ	G_SHIFT+$070
g_ScrollFineX       	equ	G_SHIFT+$072	; fine scroll -15..15
g_ScrollFineY       	equ	G_SHIFT+$074
g_CameraX           	equ	G_SHIFT+$076	; camera world position in pixels
g_CameraY           	equ	G_SHIFT+$078
g_CamDeltaX         	equ	G_SHIFT+$07A
g_CamDeltaY         	equ	G_SHIFT+$07C
g_PendFineX         	equ	G_SHIFT+$07E	; camera target X relative to g_NewTileX*16: the fine scroll to use once the pending redraw is shown
g_PendFineY         	equ	G_SHIFT+$080	; the same for Y
g_NewTileX          	equ	G_SHIFT+$082
g_NewTileY          	equ	G_SHIFT+$084
g_CamMinX           	equ	G_SHIFT+$086	; left scroll limit (scrolling is one-way)
g_CamMinY           	equ	G_SHIFT+$088
g_LevelOriginX      	equ	G_SHIFT+$08A
g_LevelWidth        	equ	G_SHIFT+$08C
g_LevelOriginY      	equ	G_SHIFT+$08E
g_LevelHeight       	equ	G_SHIFT+$090
g_MapPtr            	equ	G_SHIFT+$092	; current level map (block indices)
g_SceneryHitX       	equ	G_SHIFT+$096	; where shootable scenery was last hit: spawn point for the Magician (type 7)
g_SceneryHitY       	equ	G_SHIFT+$098
g_Level             	equ	G_SHIFT+$09A	; level 0-6 (per-player block starts here, P2 copy at +$10)
g_Weapon            	equ	G_SHIFT+$09C	; 0 torch 1 lance 2 axe 3 cross 4 dagger (cross needed on level 6)
g_Score             	equ	G_SHIFT+$09E	; BCD score
g_NextExtraLife     	equ	G_SHIFT+$0A2	; BCD score for next extra life (also AddScore accumulator end)
g_Lives             	equ	G_SHIFT+$0A6
g_Checkpoint        	equ	G_SHIFT+$0A7	; set once the half-way point is passed
g_ExtraLives        	equ	G_SHIFT+$0A8	; extra lives awarded so far (20000, 70000, then every 70000)
g_ShowIntro         	equ	G_SHIFT+$0A9	; non-zero: play the opening kidnap cutscene first
g_OtherPlayer       	equ	G_SHIFT+$0AA	; the other player's copy of g_Level .. g_ShowIntro (16 bytes), exchanged by SwapPlayers
g_ShownScore        	equ	G_SHIFT+$0BA	; score last drawn on the HUD / hi-score name ptr in entry mode
g_HiScores          	equ	G_SHIFT+$0BE	; 10 BCD longs, top score first
g_ArthurX           	equ	G_SHIFT+$0E6	; world X (also cursor column in name entry)
g_ArthurY           	equ	G_SHIFT+$0EA	; world Y, increasing upwards (cursor row in name entry)
g_ArthurAux         	equ	G_SHIFT+$0EE
g_ArthurVelX        	equ	G_SHIFT+$0F0
g_ArthurVelY        	equ	G_SHIFT+$0F4
g_ArthurAnim        	equ	G_SHIFT+$0F8	; animation script pointer
g_ArthurPlatform    	equ	G_SHIFT+$0FC	; platform slot Arthur is riding
g_ArthurShownFrame  	equ	G_SHIFT+$100	; frame last copied into sprite RAM
g_ArthurFrame       	equ	G_SHIFT+$101	; requested sprite frame (negative = mirrored)
g_ArthurAnimTimer   	equ	G_SHIFT+$102
g_ArthurDir         	equ	G_SHIFT+$103	; +1 right / -1 left
g_LadderDir         	equ	G_SHIFT+$104	; ladder climb direction
g_ArthurFacing      	equ	G_SHIFT+$105
g_Crouching         	equ	G_SHIFT+$106	; down held (also: 3 initials buffer during high-score entry)
g_Jumping           	equ	G_SHIFT+$107	; airborne, rising
g_Falling           	equ	G_SHIFT+$108	; airborne, descending / not on floor
g_FireCooldown      	equ	G_SHIFT+$109	; frames until the next throw
g_OnPlatform        	equ	G_SHIFT+$10A
g_OnLadder          	equ	G_SHIFT+$10B
g_StateTimer        	equ	G_SHIFT+$10C
g_NoArmour          	equ	G_SHIFT+$10D	; Arthur has lost his armour
g_ArthurState       	equ	G_SHIFT+$10E	; 0 normal, 1 hit, 4 time-up death, 7 fell
g_ArthurFlash       	equ	G_SHIFT+$10F	; invulnerability flashing
g_FrogTimer         	equ	G_SHIFT+$110	; magician curse: Arthur is a frog while non-zero
g_KeyState          	equ	G_SHIFT+$111	; end-of-level key sequence
g_LevelFileEnd      	equ	G_SHIFT+$112
g_LevelFileAddr     	equ	G_SHIFT+$116
g_SmallBobSets      	equ	G_SHIFT+$11A	; 10 pointers to the small BOB graphics sets (items, scenery), filled by LoadLevel
g_BobSets           	equ	G_SHIFT+$142	; 21 pointers to the enemy BOB graphics sets: one per enemy type, then the bat (+76) and red crow (+80)
g_BlitListPtr       	equ	G_SHIFT+$196
g_SaveBufA          	equ	G_SHIFT+$3DA	; background save area of the buffer being drawn (its address in a6 is also the top of the BOB draw list, which grows down from here to g_BlitListPtr)
g_SaveBufB          	equ	G_SHIFT+$3DE	; background save area of the other buffer
g_SavePtr           	equ	G_SHIFT+$3E2	; next free byte in g_SaveBufA (limit $3000 bytes a frame)
g_SavePtrB          	equ	G_SHIFT+$3E6	; the same for the other buffer
g_RestoreListA      	equ	G_SHIFT+$3EA	; restore list of the buffer being drawn: 12-byte entries (BLTSIZE, modulo, screen address, save address) growing down from $632; 0 ends it
g_RestoreListB      	equ	G_SHIFT+$3EE	; restore list of the other buffer (grows down from $872)
g_RestoreBufB       	equ	G_SHIFT+$632	; restore list storage: list A grows down from here, list B from g_SpawnQuota
g_SpawnQuota        	equ	G_SHIFT+$872	; 16 bytes, one per enemy type: how many more the spawners may create; a handler gives one back when its enemy leaves
g_HiNames           	equ	G_SHIFT+$882	; 10 x 3 initials
g_SpecialObjs       	equ	G_SHIFT+$8A0	; 2 slots x $20 (key, cutscene actors)
g_Shots             	equ	G_SHIFT+$8E0	; 4 weapon slots x $26
g_EnemyShots        	equ	G_SHIFT+$978	; 6 slots x $1C
g_Spawners          	equ	G_SHIFT+$A20	; 16 enemy spawners x $C, one per enemy type
g_Items             	equ	G_SHIFT+$AE0	; 30 slots x $1C - platforms / pickups / pots
g_Enemies           	equ	G_SHIFT+$E28	; 40 slots x $3C - enemy objects
g_Enemy1            	equ	G_SHIFT+$E64	; second enemy slot (used by cut-scenes)

; ---- Object slot fields (enemies $3C, shots $26, items $1C share this header) ----
O_Active            	equ	$00	; 0 = free, 1 = active, 2 = dying (no shot test), bit 7 set = shots pass through
O_OnScreen          	equ	$01	; set by CheckOnScreen
O_Param             	equ	$02	; placement parameter / scratch
O_State             	equ	$03	; enemies: 0 start (set-up, for some types also their first behaviour), 1 active, 2 killed (set by EnemyHitByShot after scoring), 3 remove - ST_START .. ST_REMOVE
O_Step              	equ	$04	; step within the state
O_Step2             	equ	$05	; second-level step
O_X                 	equ	$06	; X pixel (long: 16.16 with O_XFrac)
O_XFrac             	equ	$08
O_Y                 	equ	$0A	; Y pixel, upwards (long with O_YFrac)
O_YFrac             	equ	$0C
O_MoveTable         	equ	$0E	; table of (dx,dy) words, indexed by O_Dir
O_Dir               	equ	$12	; direction / animation index
O_Size              	equ	$13	; size class (BoxSizeTable)
O_Anim              	equ	$14	; animation script pointer
O_Frame             	equ	$18	; current frame (BobFrameDescs index)
O_AnimTimer         	equ	$19	; ticks left on this frame
O_Type              	equ	$1A	; enemy / shot / item type
O_HP                	equ	$1B	; hits left (enemies) / flags (items)

; ---- Per-enemy fields (slot offsets $1C-$3B differ by enemy type) ----
Uni_ChargeX         	equ	$1C	; charge target X (Arthur +-16)
Uni_JumpType        	equ	$1E	; facing (1 right, 2 left) / jump type index into Unicorn_JumpSpeedX
Uni_AnimSet         	equ	$20	; current animation pair (right, left)
Uni_ShotPtr         	equ	$24	; position in Unicorn_ShotScript
Uni_WalkPtr         	equ	$28	; position in the current Unicorn_WalkScripts entry
Uni_VelY            	equ	$2C	; vertical speed while jumping (16.16, up = positive)
Uni_Timer           	equ	$30	; fire wind-up / recovery timer; death timer
Uni_Aiming          	equ	$31	; 1 = in the fire pose, shot pending
Uni_Angry           	equ	$32	; set when Uni_AngerTimer runs out: next move is a charge or a jump at Arthur
Uni_Approach        	equ	$33	; wanted walk direction to keep its distance from Arthur (0 = happy)
Uni_Gravity         	equ	$34	; jump phase: selects the gravity pair in Unicorn_Gravity
Uni_Delay           	equ	$35	; start delay, in 16-frame units
Uni_JumpNext        	equ	$36	; 1 = jump instead of walking on the next decision
Uni_Variant         	equ	$37	; spawn parameter: 0 normal, 1 / 3 start with a long jump, 4 = 0 after a short delay, 2 = keeps to its arena (level 5)
Uni_ShotWait        	equ	$38	; frames until the next shot (from Unicorn_ShotScript)
Uni_WalkTime        	equ	$39	; frames left of the current walk-script step
Uni_AngerTimer      	equ	$3A	; frames until Uni_Angry is set (random, Unicorn_AngerDelays)
Uni_Pause           	equ	$3B	; pause after landing
Sat_TargetX         	equ	$1C	; Arthur X when the dive started
Sat_ArcDepth        	equ	$1E	; current depth of the dive below Sat_ArcBaseY (word)
Sat_FlySpeed        	equ	$20	; horizontal speed pair for the dive (left, right)
Sat_ArcBaseY        	equ	$24	; Y at the start of the dive (word)
Sat_ArcHeight       	equ	$26	; half the depth of the dive
Sat_ArcPhase        	equ	$27	; 0-255 through the dive (sine table index)
Sat_Returning       	equ	$30	; 1 = off screen, flying back in
Sat_Hold            	equ	$31	; cleared at start and never set: would make it only count down
Sat_WakeDelay       	equ	$32	; x 64 frames before a parameter-1 Satan wakes up
Sat_Timer           	equ	$33	; hovering: frames left (180); diving: phase step per frame
Sat_FirePhase       	equ	$34	; 0 shooting, 1 guarding (shots pass through), 2 back to shooting
Sat_GuardTime       	equ	$35	; frames of guarding (30)
Sat_FireTime        	equ	$36	; frames of shooting before it guards (SatanFireTimes)
Sat_Swoop           	equ	$37	; 1 = level with Arthur: fly across, then climb out of the dive
Sat_Drift           	equ	$38	; hover drift: 0 right, 1 left, 2 up, 3 down (new every 128 frames)
Sat_ShotWait        	equ	$39	; frames to the next shot (SatanShotGaps)
Sat_ReturnDir       	equ	$3A	; which way to fly back on screen: 0 right, 1 left, 2 up, 3 down
Sat_ReturnTime      	equ	$3B	; frames of flying back
Drg_PathPtr         	equ	$1C	; head: position in the current path script ((frames, direction) pairs)
Drg_HomeY           	equ	$20	; head: start Y (word); level 5 keeps within 256 px of it
Drg_Next            	equ	$24	; next segment towards the tail (long, 0 = this is the tail)
Drg_Prev            	equ	$28	; previous segment towards the head (long)
Drg_Facing          	equ	$30	; head: 0 right, 1 left
Drg_PathTime        	equ	$31	; head: frames left on the current path step; also the death timer
Drg_Aggro           	equ	$32	; head: attack when (random & 15) <= this (2: 3 in 16)
Drg_Firing          	equ	$33	; head: 1 while the mouth is open after a shot
Drg_Pending         	equ	$34	; segment: a new direction is waiting in Drg_NewDir; head: mouth-open timer
Drg_Frozen          	equ	$35	; 1 = segment does not move (while the dragon waits to attack)
Drg_Part            	equ	$36	; 0 head, 1 body, 2 tail
Drg_Index           	equ	$37	; position in the chain: 8 head ... 0 tail
Drg_NewDir          	equ	$38	; direction to take when Drg_Delay runs out
Drg_Delay           	equ	$39	; frames until Drg_NewDir is taken
Drg_Wait            	equ	$3A	; head: x 16 frames before the attack starts
Drg_HeadDead        	equ	$3B	; 1 = the head was killed: boss handling on removal
Ast_ArenaL          	equ	$1C	; left end of its walk (camera X + 96 when it woke)
Ast_ArenaR          	equ	$1E	; right end (camera X + 224)
Ast_WalkTime        	equ	$20	; frames to walk before turning (word, 0-1023)
Ast_StandIn         	equ	$22	; frames until the stand-and-fire phase (word, 256-767)
Ast_StandTime       	equ	$24	; length of the stand-and-fire phase (word, 64-191)
Ast_Facing          	equ	$30	; 0 Arthur to the right, 1 to the left
Ast_Turning         	equ	$31	; 1 = between walks
Ast_Standing        	equ	$32	; 1 = stand-and-fire phase (see the bug note)
Ast_HighShot        	equ	$33	; 1 = next shot from the upper firing point; death timer
Ast_ShotWait        	equ	$34	; frames to the next shot (AstarothShotGaps)
Ast_TurnWait        	equ	$37	; set to 143-190 before turning, but only tested once
Ast_Far             	equ	$38	; 1 = Arthur more than 80 px away
RA_CentreX          	equ	$1C	; swoop: Arthur X at the start (word); blink timer in mode 2
RA_BaseY            	equ	$1E	; Y the flight curves are measured from (word); perch timer
RA_WalkPtr          	equ	$20	; position in RedArremerWalkScript
RA_ShotPtr          	equ	$24	; position in RedArremerShotTimes
RA_SwoopPtr         	equ	$28	; position in RedArremerSwoopTimes
RA_FlyPtr           	equ	$2C	; position in RedArremerTakeOffTimes
RA_RadiusX          	equ	$30	; swoop: horizontal radius; death timer
RA_Rage             	equ	$31	; aggression level: 0 at first, 1 after its rage (faster tables)
RA_ShotTime         	equ	$32	; frames to the next shot; wind-up timer
RA_SwoopTime        	equ	$33	; frames to the next swoop at Arthur
RA_Phase            	equ	$34	; flight: sine index; walking: x 8 frames to the next take-off
RA_RageTime         	equ	$35	; x 32 frames of walking before it rages (from 50)
RA_RadiusY          	equ	$36	; height of the current flight curve
RA_Return           	equ	$37	; step to go back to after a shot
RA_Temp             	equ	$38	; distance to Arthur / dodge height / glide frames
RA_ArthurLeft       	equ	$39	; 1 = Arthur is to its left
RA_WalkDir          	equ	$3A	; walk / flight direction (negative = stand)
RA_WalkTime         	equ	$3B	; frames left of the walk step
BM_ShotPtr          	equ	$1C	; position in BigManShotTimes
BM_WalkPtr          	equ	$20	; position in BigManWalkTimes
BM_Timer            	equ	$30	; pause after shooting down; death timer
BM_EdgeDir          	equ	$31	; direction it was walking when it found the edge; wind-up timer
BM_AtEdge           	equ	$32	; 1 = no floor just ahead
BM_EdgeTurn         	equ	$33	; already turned back from this edge
BM_Crouched         	equ	$34	; starts crouching (from O_Param)
BM_ShotTime         	equ	$35	; frames to the next shot
BM_WalkTime         	equ	$36	; frames to the next pause
BM_CrouchTime       	equ	$38	; x 64 frames of crouching
BM_PauseTime        	equ	$39	; frames of the current pause
Mag_Timer           	equ	$30	; rise / fade timer (60 frames)
Mag_Cast            	equ	$31	; frames before and after the spell (20)
Skl_VelY            	equ	$1C	; vertical speed (16.16, up = positive)
Skl_BaseY           	equ	$20	; Y where the leap started (word)
Skl_LeapDX          	equ	$24	; horizontal speed of the leap (16.16)
Skl_Hops            	equ	$30	; hops left before the leap (2)
Skl_Pause           	equ	$31	; frames of pause after landing (6)
Skl_Phase           	equ	$32	; leap: sine index
Zmb_SizePtr         	equ	$1C	; next entry in the emerge / sink size-class list
Zmb_Timer           	equ	$30	; frames before emerging; frames to walk on after passing Arthur
Zmb_WalkTime        	equ	$31	; walk time, counted every other frame (180 = 360 frames)
Zmb_Steps           	equ	$32	; size-class steps left while emerging / sinking
Crw_WaitList        	equ	$1C	; list of 8 random waits (CrowWaits)
Crw_BaseY           	equ	$20	; centre line of the wavy flight / arc (word)
Crw_Phase           	equ	$24	; sine phase (word, high byte = table index)
Crw_Amp             	equ	$30	; height of the arc / wave
Crw_Crow            	equ	$31	; 1 = crow graphics and speeds (param 3+)
Crw_Wait            	equ	$32	; frames before it takes off
Crw_Look            	equ	$33	; perched: frames of the current look-around; flying: half-wave count
Crw_Speed           	equ	$34	; wave speed index (always 0)
Pig_TurnPtr         	equ	$1C	; position in WoodyPigLoopTimes
Pig_Bomb            	equ	$20	; enemy shot slot it is carrying (long, 0 = none)
Pig_Drop            	equ	$30	; 1 = pick up a shot next frame
Pig_LoopAcc         	equ	$34	; adds WoodyPigLoopOdds every 16 frames; a loop when it carries
Pig_TurnAcc         	equ	$35	; accumulator deciding the loop direction when level with Arthur
Pig_Loops           	equ	$36	; loops left (0-7, from the frame counter)
Pig_Turns           	equ	$37	; turn steps left in the loop (8); emerging animation delay
Pig_TurnDir         	equ	$38	; +1 or -1: which way it turns
Pig_TurnTime        	equ	$39	; frames to the next 1/16 turn
Pig_Timer           	equ	$3A	; frames of the drop animation
PD_MoveTable        	equ	$1C	; its normal 16-way move table (restored after special moves)
PD_TargetY          	equ	$20	; Arthur Y when this leg started (word)
PD_TurnWait         	equ	$22	; frames to the next 1/16 turn
PD_TurnRate         	equ	$23	; reload for PD_TurnWait (slower turns further away)
PD_Fine             	equ	$30	; 1 = halve the turn wait again (param 1)
PD_Shot             	equ	$31	; 1 = has fired its one shot
PD_Legs             	equ	$32	; hunting legs left (4)
PD_Turn             	equ	$33	; turn mode 0-3: which way it turns (DevilTurnModes)
PD_EarlyShot        	equ	$34	; 0 = may fire as it arrives (PetiteDevilArriveShot)
PD_ShotTime         	equ	$35	; frames before it may fire (64-95)
PD_Time             	equ	$36	; frames left of the current leg
PD_LegLen           	equ	$37	; length of the arrival leg
PD_Ready            	equ	$38	; 1 = may fire now
PD_WantDir          	equ	$39	; direction it is turning towards
PD_StepTime         	equ	$3A	; frames per step of the recoil turn
PD_ShotDir          	equ	$3B	; direction of its shot (selects the recoil)
FK_BaseY            	equ	$1C	; centre line of its wave (word)
FK_Phase            	equ	$31	; sine index, +6 a frame (43 frames per half wave)
BK_BaseY            	equ	$1C	; start Y of a hop (word)
BK_Phase            	equ	$1E	; hop phase (word, +$400 a frame)
BK_Morph            	equ	$20	; frames until it turns into a Red Arremer (word, 3600)
BK_HopHeight        	equ	$30	; hop height: 32 or 48 px
BK_CurveWait        	equ	$32	; frames to the next 1/16 turn of the swoop
BK_CurveRate        	equ	$33	; reload for BK_CurveWait: (Y - Arthur Y) / 8
BK_Appear           	equ	$34	; frames before a dropping Blue Killer becomes hittable (10)
BK_WalkTime         	equ	$35	; frames of the current walk
BK_Delay            	equ	$36	; frames before a dropping Blue Killer starts (40)
BK_SwoopMode        	equ	$37	; 0/1 curve right/left, 2 straight down
BK_SwoopSet         	equ	$38	; which pair of swoop tables
Fir_SizePtr         	equ	$1C	; position in the size-class list of the current flare
Fir_WaitPtr         	equ	$20	; position in FireWaits
Fir_Wait            	equ	$30	; x 32 frames to the next flare-up
Plt_WaitPtr         	equ	$1C	; position in PlantWaits
Plt_Wait            	equ	$30	; frames to the next spit
Plt_Mouth           	equ	$31	; frames of the open mouth before it spits (24)
Pil_LowPtr          	equ	$1C	; position in FirePillarTimes for the lower shot
Pil_HighPtr         	equ	$20	; position in FirePillarTimes for the upper shot
Pil_LowWait         	equ	$30	; frames to the next lower shot; death timer
Pil_HighWait        	equ	$31	; frames to the next upper shot
Pil_Fire            	equ	$33	; bit 1 lower shot due, bit 0 upper shot due
Pil_Timer           	equ	$34	; wind-up / after-shot timer
Pil_Flick           	equ	$35	; index into FirePillarFlicker
Pil_Flick2          	equ	$36	; index used by the upper / double shot (never advanced)
Pil_FlickA          	equ	$37	; written from FirePillarFlicker, never read
Pil_FlickB          	equ	$38	; written, never read
Pil_FlickC          	equ	$39	; written, never read
Scn_Target          	equ	$1C	; ending: the princess's stopping X, then the message timer
Scn_Timer           	equ	$30	; opening scene: frame countdown on the demon
Key_Timer           	equ	$1B	; frames left spinning
Itm_Rider           	equ	$18	; platform items: set while Arthur stands on it
Spn_Flags           	equ	$0B	; spawner flags: bit 0 world coordinates, bit 1 runs once, bit 2 keeps running when the zone changes
Shot_StartX         	equ	$1C	; X where the shot was thrown (range check)
Shot_VX             	equ	$1E	; arc speed X (16.16) once a torch or axe starts to fall
Shot_VY             	equ	$22	; arc speed Y (16.16)
Spc_VY              	equ	$1C	; fall speed (16.16), gravity 0.07 px/frame^2
Pig_Unused31        	equ	$31	; cleared at set-up, never read
Pig_Unused32        	equ	$32	; cleared at set-up, never read
Pig_Unused33        	equ	$33	; cleared at set-up, never read
BK_Unused31         	equ	$31	; cleared, never read
BM_FlinchTime       	equ	$37	; frames of the flinch after a hit (6)
Ast_WalkTimeLo      	equ	$21	; low byte of the Ast_WalkTime word (set to a random number)
Ast_StandInLo       	equ	$23	; low byte of the Ast_StandIn word (set to a random number)
PD_PathPos          	equ	$24	; position in the current PetiteDevilPath list
PD_PathSeg          	equ	$28	; current path segment

; ---- One program for every machine (enhanced branch) ----------------------------------
BUILD_ONE           	equ	1	; (scroll.s: absolute addresses, BOB drawing chosen at run time)
MACHINE_INFO        	equ	$7FB00	; the bootblock's machine description (32 bytes, 'GNGM'):
MI_MAGIC            	equ	0	;   'GNGM'
MI_CHIP_UPPER       	equ	12	;   end of chip RAM (+8 start, +12 end)
PF_CACHE            	equ	0	; Profile bits: 1MB+ of chip RAM - caches in the upper 512K
PF_MUSIC            	equ	1	;   the 1MB music package is loaded
PF_EVERY            	equ	2	;   draw every frame (no odd-frame test)

; Upper chip RAM ($80000-$FFFFF), used only with PF_CACHE. Every buffer the blitter or Paula
; reads must be chip RAM. The masked caches are twice their files (a mask line after every
; plane line).
UPPER_CHIP          	equ	$80000
MUSIC1M_FILE        	equ	UPPER_CHIP	; the 1MB music package ($1B394), assembled for here
MUSIC1M_PLAYER      	equ	MUSIC1M_FILE+$20	; its driver entry
MUSICB_FILE         	equ	$80	; ... or, with the program moved out of chip RAM (EnhRelocate),
                    			; loaded here, where the program was, and relocated
PROGRESS_MAP_CACHE  	equ	MUSIC1M_FILE+$1B400	; the packed progress map ($1D5C)
ENEMY_GFX_CACHE     	equ	PROGRESS_MAP_CACHE+$1E00	; enemy BOB sets with masks (2 x $1D042); the
                    			; level's frame tables point into it (BuildFrameTable)
SMALLBOB_CACHE      	equ	ENEMY_GFX_CACHE+$3A100	; small BOB sets with masks (2 x $D20)
MESHOT_GFX_BUF      	equ	SMALLBOB_CACHE+$1A80	; enemy shots with masks (2 x $1234)
MITEM_GFX_BUF       	equ	MESHOT_GFX_BUF+$2480	; items / effects with masks (2 x $1AC2) ...
MITEM_GFX2_BUF      	equ	MITEM_GFX_BUF+2*$1AC2	; ... followed by file 57 (2 x $EA6), as in memory
MITEM_GFX_END       	equ	MITEM_GFX2_BUF+2*$EA6	; end of the upper chip RAM used
	ifgt	MITEM_GFX_END-$100000
	fail	"the upper chip RAM caches do not fit below $100000"
	endc
