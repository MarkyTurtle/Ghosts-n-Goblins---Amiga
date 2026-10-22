# How the game works

A guided tour of the main program, with the routine names to search for in `gng_main.s`.
Diagrams are Mermaid (they render on GitHub and in most Markdown viewers).

## 1. Everything runs in interrupts

After `Start` has loaded the common files and set up the hardware, the CPU drops to user
mode and spins in `IdleLoop`. The game itself runs in three interrupts:

```mermaid
flowchart LR
  VBL["VblIRQ (level 3, every 1/50 s)<br/>sprites, joystick, music tick"] -->|"raise SOFTINT unless the<br/>logic is still running<br/>or g_SkipLogic is set"| L1["Level1Logic (level 1)<br/>one logic frame"]
  VBL -->|"g_RedrawPending: change the<br/>user-mode return address"| RE["RedrawEntry (user mode)<br/>RedrawScreen, clear g_SkipLogic"]
  KB["KeyboardIRQ (level 2)"] --> K["g_RawKey / g_AsciiKey"]
  L1 --> GS{g_GameState}
  GS -->|GS_TITLE| AT[AttractTitle]
  GS -->|GS_HISCORES| AH[AttractHiScores]
  GS -->|GS_INGAME| IG[InGame]
```

The logic runs up to 50 times a second; the camera and drawing happen on every second logic
frame (`PlayFrame`), so the screen updates at 25 frames a second.

## 2. The in-game state machine

`InGame` dispatches on `g_SubState` (constants `SS_...`); each state has its own steps in
`g_SubState2` / `g_SubState3`.

```mermaid
stateDiagram-v2
  [*] --> SS_LOADLEVEL: CheckGameStart
  SS_LOADLEVEL --> SS_PLAYLEVEL: LoadLevel
  SS_PLAYLEVEL --> SS_INTRO: first level of a game
  SS_INTRO --> SS_PLAYLEVEL: IntroCutscene
  SS_PLAYLEVEL --> SS_INPLAY: ProgressMap, SetupLevel, level tune
  SS_INPLAY --> SS_INPLAY: PlayFrame every frame
  SS_INPLAY --> SS_LEVELCOMPLETE: key taken (EndOfLevelKey)
  SS_LEVELCOMPLETE --> SS_INPLAY: bonus, g_Level + 1, g_LevelDone
  SS_INPLAY --> SS_LOADLEVEL: g_LevelDone
  SS_INPLAY --> SS_PLAYLEVEL: Arthur died, lives left (or the other player, same level)
  SS_INPLAY --> SS_LOADLEVEL: the other player, on another level
  SS_INPLAY --> SS_GAMEOVER: no lives left
  SS_GAMEOVER --> SS_INPLAY: NameEntry, then back
  SS_INPLAY --> [*]: no player left - attract screens
  SS_INPLAY --> SS_ENDING: Astaroth beaten with the cross
  SS_INPLAY --> SS_WEAPONUSELESS: Astaroth beaten without it
  SS_WEAPONUSELESS --> SS_LOADLEVEL: back to level index 4
  SS_ENDING --> SS_GAMEOVER: 50,000 points, game over
```

## 3. One frame of play (`PlayFrame`)

```mermaid
flowchart TD
  A[Esc / pause] --> B[ArthurUpdate]
  B --> C{boss beaten?<br/>g_KeyState}
  C -->|no| D["UpdateSpecialObjs, UpdateShots, UpdateEnemyShots,<br/>UpdateEnemies, UpdateItems"]
  D --> E["EnemyVsArthur, ShotsVsScenery,<br/>ShotsVsEnemyShots, EnemyShotsVsArthur"]
  E --> F["UpdateMapZone, UpdateSpawners"]
  C -->|yes| K["'TAKE A KEY...' then EndOfLevelKey<br/>(everything else frozen)"]
  F --> T[timer, checkpoint, extra life, score]
  K --> T
  T --> CAM["camera X; fell off the map?"]
  CAM --> ODD{odd frame?}
  ODD -->|yes| DRAW["camera Y, switch / scroll / request redraw,<br/>RestoreBackground, DrawBobs, sprites, ShowBackBuffer"]
  ODD -->|no| END
  DRAW --> END[life lost? level done? g_GameFrame + 1]
```

## 4. Objects

All moving things live in fixed slot arrays in the globals block, and share the `O_` field
layout (`docs/GLOBALS.md`):

| Array | Slots | Handler |
|---|---|---|
| `g_Enemies` | 40 x `$3C` | `UpdateEnemies` -> `EnemyTypeTable` (one handler per enemy type) |
| `g_EnemyShots` | 6 x `$1C` | `UpdateEnemyShots` |
| `g_Shots` (Arthur's) | 4 x `$26` | `UpdateShots` |
| `g_Items` | 30 x `$1C` | `UpdateItems` (triggers, scenery, platforms) |
| `g_SpecialObjs` | 2 x `$20` | `UpdateSpecialObjs` (bonus prizes, the key, cut-scene props) |
| `g_Spawners` | 16 x `$C` | `UpdateSpawners` (one per enemy type) |

An enemy's life:

```mermaid
stateDiagram-v2
  [*] --> ST_START: placed (LevelEnemyLists) or spawned (UpdateSpawners)
  ST_START --> ST_ACTIVE: set-up done
  ST_ACTIVE --> ST_KILLED: EnemyHitByShot - hit points gone, EnemyPoints scored
  ST_ACTIVE --> ST_REMOVE: far off screen (CheckFarAway)
  ST_KILLED --> ST_REMOVE: explosion (QueueExplosionDraw)
  ST_REMOVE --> [*]: slot freed, spawn quota given back
```

## 5. Where enemies come from

```mermaid
flowchart LR
  CAM["cell under the camera"] --> MZ[MapZoneTable] --> Z{"zone changed?<br/>(UpdateMapZone)"}
  Z -->|yes| ZS["ZoneSpawners: start spawners<br/>(type, script, flags)"]
  ZS --> SP["UpdateSpawners: each entry of the script<br/>(x, y, param, delay)"]
  SP -->|"free slot and g_SpawnQuota > 0"| EN[new enemy]
  SP -->|"every 6th spawn"| BON["bonus prize carried<br/>(special object 0, BonusKinds)"]
```

`docs/SPAWNS.md` lists every level's zones and scripts.

## 6. Drawing a frame

```mermaid
flowchart LR
  Q["Queue*Draw: push (x, y, w, h, graphics)<br/>on the draw list"] --> RB["RestoreBackground:<br/>undo last time's BOBs"]
  RB --> DB["DrawBobs -> DrawBob:<br/>save background, mask, 5 cookie-cut blits"]
  DB --> AS["ArthurSpritePos:<br/>Arthur is 4 hardware sprites"]
  AS --> SB["ShowBackBuffer: wait for the copper,<br/>swap screens, save areas, restore lists"]
```

The background is not scrolled pixel by pixel: `RedrawScreen` redraws the whole playfield
around a new 16-px tile origin in the background (user mode), and the hardware fine scroll covers
up to 16 px either way until the display switches to it (`CameraJump`). The exact rules are in the
source at the camera header in `PlayFrame`, and as a checked model in `tools/verify/camera.py`.

## 7. The level data

```mermaid
flowchart LR
  WM["WorldMap: one byte per 256 x 256 cell"] --> CT["CellTiles: 16 x 16 graphics tiles<br/>-> level file, 160 bytes a tile"]
  WM --> BT["BlockTiles: 8 x 8 collision tiles"] --> TA["TileAttr: 4 quadrant profiles + flags"]
  TA --> FP["FloorProfile / WallProfileR / WallProfileL<br/>(MapTileAt, ObjectMapCollide, LadderCheck)"]
```

`render/out/worldmap_cells.png` shows the whole map with every cell number.

## 8. Checking it

`tools/verify/checks.py` runs pieces of the original program in a 68000 emulator and checks the
bug notes and the camera rules against what the code really does.
