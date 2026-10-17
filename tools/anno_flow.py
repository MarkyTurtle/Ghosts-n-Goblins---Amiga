# Game flow: the play loop and camera, level set-up, end-of-level key and bonus,
# game over, high-score name entry, attract screens.
# Executed inside anno_db.py after anno_scenes.py.

V(0x7E, 'g_PendFineX', 'camera target X relative to g_NewTileX*16: the fine scroll to use once the pending redraw is shown')
V(0x80, 'g_PendFineY', 'the same for Y')
VAR_RANGES.extend([(0x06, 2), (0x0C, 2), (0xBE, 40), (0x882, 30)])

# --------------------------------------------------------------------------- InGame
HEADERS[0x645E] = """==================================================================
InGame - dispatch on g_SubState:
  0 LoadLevel     load the level's files            -> 1
  1 PlayLevel     g_SubState2: 0 progress map, 1 SetupLevel, 2 start music -> 2
  2 InPlay        PlayFrame every frame; after a death or a finished level decides
                  what comes next
  3 GameOver      'GAME OVER', high-score insertion and name entry
  4 LevelComplete walk off, bonus                   -> 2 (g_LevelDone) -> 0
  5 IntroCutscene once per game, before the first level
  6 Ending        after Astaroth
  7 WeaponUseless Astaroth's guard beaten without the cross
=================================================================="""

N(0x674C, 'InPlay', """Sub state 2 - the normal 'playing' state. Each frame:
  no death and no finished level -> PlayFrame
  level finished (g_LevelDone)   -> sub state 0, load the next level
  Arthur died (g_PlayerDied):
    two players and the other one still has lives -> SwapPlayers; reload the level
      if the other player is on a different one, else straight to sub state 1
    else lives left -> sub state 1 (progress map, set-up) on the same level
    else -> attract mode (g_GameState 1)""")
for a,t in [
 (0x6752,'2 players: does the other player have lives left?'),
 (0x6764,'no lives: back to the attract screens'),
 (0x6784,'switch to the other player'),
 (0x6792,'same level as before? (then no need to reload)'),
 (0x679E,'progress map and level set-up'),
 (0x67B0,'normal frame: no level change pending'),
 (0x67B8,'level finished: load the next one (g_Level already advanced)'),
]: C(a,t)

# --------------------------------------------------------------------------- LoadLevel / PlayLevel / SetupLevel
for a,t in [
 (0x68B0,'first level of a game: skip the progress map (the opening scene comes instead)'),
 (0x68C0,'wait for any redraw in progress'),
]: C(a,t)
HEADERS[0x68DA] = """SetupLevel - PlayLevel step 1: start (or restart) the level.
 - map pointer, boss countdown, bonus-carrier and weapon-drop state
 - start or checkpoint position and time (LevelStartPos / LevelCheckpointPos,
   LevelTimeStart / LevelTimeCheckpoint); at the checkpoint the screen starts
   LevelCheckpointX further right
 - level bounds from LevelBounds (4 bytes, each x 256: origin X, end X, height,
   origin Y); scroll limits reset
 - every Arthur variable cleared: armour on, no frog, no key
 - spawn quotas, then all shot / special / enemy-shot / spawner / item / enemy slots freed
 - first game frame: go to the opening scene instead (sub state 5), which comes back here
 - fill g_Items from LevelItemLists (type, param, x, y; shootable scenery gets 15 hits)
   and g_Enemies from LevelEnemyLists (the placed enemies: type, param, x, y)
 - draw both screen buffers, the HUD (lives, timer, weapon), show Arthur -> step 2"""
for a,t in [
 (0x68EE,'level map'),
 (0x68F2,'boss hits before the key / ending (BossKilled)'),
 (0x68FA,'every 6th spawn carries a bonus prize'),
 (0x691C,'start of the level ...'),
 (0x692A,'... or the checkpoint'),
 (0x694E,'level bounds, in units of 256 px'),
 (0x698A,'checkpoint: start that far into the level'),
 (0x69CC,'force UpdateMapZone to start the first zone'),
 (0x6A24,'colour 19 (sprite palette): $070 on level 0, $079 on the others'),
 (0x6A3A,'16 spawn quotas for this level'),
 (0x6A52,'free all object slots: 4 shots, 2 special objects, 6 enemy shots,'),
 (0x6A82,'16 spawners, 30 items, 40 enemies'),
 (0x6AB2,'opening scene first?'),
 (0x6ACA,'place the items of LevelItemLists'),
 (0x6AF2,'type 1 (shootable scenery): 15 hits (the Magician appears)'),
 (0x6AFE,'size class from the type'),
 (0x6B08,'world position -> level coordinates'),
 (0x6B34,'place the enemies of LevelEnemyLists'),
 (0x6B8E,'draw and show both buffers'),
 (0x6BD0,'HUD'),
 (0x6BEC,'-> step 2: start the music'),
 (0x6C0E,'PlayLevel step 2: the level tune (1MB build only), then play (sub state 2)'),
]: C(a,t)

# --------------------------------------------------------------------------- PlayFrame
HEADERS[0x6C20] = """==================================================================
PlayFrame - one frame of play (sub state 2):
 1 Esc: abandon the game (attract mode). Space: pause until fire is pressed.
 2 ArthurUpdate; then either the boss-key sequence (g_KeyState: 'TAKE A KEY FOR COMING
   IN !' for 36 frames, then EndOfLevelKey - enemies and shots are frozen from here on)
   or all the objects and their collisions, the map zone and the spawners.
 3 Level timer: one 'second' every 64 frames (BCD minutes:seconds in g_TimeLeft).
   At 0:00 Arthur dies; at 0:15 the 1MB build plays a warning tune. Passing
   LevelCheckpointX sets g_Checkpoint and resets the time to LevelTimeCheckpoint.
 4 Every 8 frames the extra-life check; the HUD score when it changed.
 5 Camera (see below), falling off the bottom of the map (death), then - on every
   second frame only - the vertical camera, the redraw decisions and the drawing:
   RestoreBackground, DrawBobs, Arthur's sprite, bitplane pointers, show the buffer.
   So the screen is updated at 25 frames a second while the logic runs at up to 50.
 6 Death: a life is lost (not with the cheat); none left -> sub state 3 (game over).
 7 g_GameFrame++.
Camera. The playfield is a buffer drawn around a tile origin (g_ScrollTileX/Y) and
scrolled by up to 16 px either way (g_ScrollFineX/Y). The camera aims at Arthur - $80
in X (clamped to g_CamMinX..g_LevelWidth) and, vertically, Arthur - $8E (his take-off
height while jumping, so jumps do not scroll). Measured in the emulator: upwards it
moves at most 2 px per camera step (4 while falling); downwards it moves to the target
minus (distance - 2), overshooting by the distance less 2 px - probably a sign slip. When
Arthur falls the view alternates between on target and up to 8 px past it.
Scrolling works by full redraws: the buffer is redrawn around a new tile origin (outside
the interrupts) and then switched to, while the fine scroll covers up to 16 px either way
(rules below, at $6EF2). If the camera would need more than that before the next redraw
is ready, g_SkipLogic stops the game logic until RedrawEntry clears it.
Scrolling back is limited: levels 0, 1 and 3 keep the camera within 256 px of the
furthest point reached (g_CamMinX); levels 4-6 (climbing) within 512 px vertically
(g_CamMinY); level 2 has no limit.
=================================================================="""
for a,t in [
 (0x6C2E,'back to the attract screens, redrawing at the current camera position'),
 (0x6C6A,'paused: wait for fire'),
 (0x6C98,'start a new draw list'),
 (0x6CA0,'boss beaten? (g_KeyState < 0: message, > 0: the key)'),
 (0x6CB2,"'TAKE A KEY FOR COMING IN !' for 36 frames"),
 (0x6CD6,'only the key moves now'),
 (0x6CDC,'bonus prizes and cut-scene objects'),
 (0x6CEC,'items (moving platforms, triggers, scenery)'),
 (0x6CF4,'shots vs shootable scenery (gravestones)'),
 (0x6D00,'zone under the camera: start its spawners'),
 (0x6D04,'run the spawners'),
 (0x6D16,'seconds - 1 (BCD)'),
 (0x6D22,'borrow: 59 and minutes - 1'),
 (0x6D34,'already dying?'),
 (0x6D4E,'15 seconds left?'),
 (0x6D64,'checkpoint not yet reached?'),
 (0x6D8C,'checkpoint: the time is reset'),
 (0x6DAC,'HUD score when it has changed (player 2 at column 22)'),
 (0x6DCC,'keep Arthur within g_CamMinX+10 .. g_LevelWidth+246'),
 (0x6DF2,'camera target X = Arthur - 128, clamped to g_CamMinX .. g_LevelWidth'),
 (0x6E0A,'relative to the pending redraw origin'),
 (0x6E18,'and to the current origin'),
 (0x6E2C,'already dying?'),
 (0x6E36,'1MB build: tune 8, or 7 (game over) on the last life'),
 (0x6E48,'state 7: the 225-frame death; a platform he was on lets go'),
 (0x6E64,'keep Arthur above g_CamMinY'),
 (0x6E76,'even frames: no camera or drawing'),
 (0x6E80,'keep Arthur below g_LevelHeight+240'),
 (0x6E92,'jumping: follow the take-off height, not the jump'),
 (0x6E9C,'camera target Y = Arthur - 142, clamped to g_CamMinY .. g_LevelHeight'),
 (0x6EB4,'more than 2 px above the target: overshoot below it by the distance - 2; below it: rise 2 px (4 falling)'),
 (0x6EE2,'Y relative to the current origin'),
 (0x6EEE,'and to the pending one'),
 (0x6EF2,'classify each offset: 0 (< 8 px), 1 (< 16), 2 (16 or more); d0/d7 = the'),
 (0x6F02,'pending origin is the closer one (X / Y)'),
 (0x6F66,'a finished redraw is waiting: switch to it now? (depends on the distances and'),
 (0x6F6C,'whether he is on the ground or climbing / falling)'),
 (0x6FDA,'stay on this origin: fine scroll = target, clamped to -16..15 ...'),
 (0x6FF4,'... if it had to be clamped, stop the logic until the redraw is shown'),
 (0x7016,'vertically only when falling at full speed'),
 (0x702A,'show the redrawn screen'),
 (0x7044,'is a new redraw needed? (not while one is in progress)'),
 (0x7054,'on the ground: the next origin is chosen ahead of him -'),
 (0x7058,'walking right: one tile on at -2, back at -16; left: on at +16, back below +1;'),
 (0x705C,'standing: +-8'),
 (0x70A0,'vertically +-8'),
 (0x70C2,'climbing or falling: vertical first, by the whole distance'),
 (0x70E6,'falling: any downward offset'),
 (0x7122,'request a redraw at the new origin (RedrawEntry, outside the interrupts)'),
 (0x7132,'camera position in level pixels'),
 (0x714E,'scrolling-back limit (none on level 2)'),
 (0x7160,'levels 0, 1, 3: at most 256 px back from the furthest point'),
 (0x7170,'levels 4-6: at most 512 px down'),
 (0x717E,'draw: restore the backgrounds, draw the BOBs, sprites, show the buffer'),
 (0x7192,'Arthur died this frame?'),
 (0x71AC,'no lives left: game over'),
 (0x71BA,'never true here in practice: LevelComplete sets g_LevelDone and leaves through'),
 (0x71C0,'LogicExit, and InPlay clears it (g_Level is advanced in LevelComplete)'),
 (0x71DC,'frame done'),
]: C(a,t)
N(0x8046, 'CameraJump', """Switch to the screen RedrawScreen has just drawn at g_NewTileX/Y: the pending
offsets become the current ones (fine scroll clamped to -16..15), then the buffers
are rotated (falls into SwapScreens)""")

N(0x5EAC, 'RedrawEntry', """RedrawEntry - the VBL handler patches the return PC to here when a
full redraw is pending (g_RedrawPending). Runs in user mode, outside the interrupt:
  bsr.w RedrawScreen / clr.b g_SkipLogic(a6) (lets the logic run again) / bra *
(kept as bytes: the code is only reached through the patched return address)""")

# --------------------------------------------------------------------------- key and bonus
N(0x79B6, 'EndOfLevelKey', """The key that drops when the boss is beaten (after 'TAKE A KEY FOR COMING IN !').
Runs instead of the enemies and shots, so everything else on screen freezes. Steps
(g_SubState2, the key is special object 0):
 0 wait until Arthur reaches the end of the level (levels 0-3: within 48 px of the
   right edge; 4-6: above the top), then place the key 37 px past the right edge at
   KeyDropY[level]; the 1MB build plays tune 5
 1 30 frames spinning in the air
 2 fall at 1.24 px/frame until it reaches the floor
 3 when Arthur is within 8 px: sound 28, 1000 points, sub state 4 (LevelComplete)""")
for a,n,h in [
 (0x79E2,'Key_Wait',None),(0x7A5A,'Key_Spin',None),(0x7A7A,'Key_Fall',None),(0x7A94,'Key_Take',None),
 (0x7A4E,'KeyDropY',"Per level (0-5): height the key appears at (level coordinates, before g_LevelOriginY)"),
 (0x7ADA,'Key_AnimSpin',"Key spinning: frames 16, 17, 18, 17"),
 (0x7AE4,'Key_AnimFall',"Key falling: frame 19"),
]: N(a,n,h)
OBJ_RANGES.append((0x79B6, 0x7ADA))
TYPE_FIELDS.append((0x79B6, 0x7ADA, {0x1B: ('Key_Timer', 'frames left spinning')}))
for a,t in [
 (0x79E4,'active, not yet on screen'),
 (0x79F8,'spin for 30 frames'),
 (0x79FE,'levels 4-6 end at the top'),
 (0x7A06,'within 48 px of the right edge?'),
 (0x7A12,'key: 37 px right of the edge, at KeyDropY'),
 (0x7A40,'above the top?'),
 (0x7A7A,'fall 1.24 px/frame'),
 (0x7A86,'Z set = landed'),
 (0x7A94,'Arthur within 8 px?'),
 (0x7ABA,'sound 28'),
 (0x7AC0,'1000 points'),
 (0x7AC6,'-> LevelComplete'),
]: C(a,t)

HEADERS[0x648A] = """LevelComplete - sub state 4 (after taking the key). Steps (g_SubState2):
 0 Arthur stands just past the right edge facing right
 1 walks right for 32 frames,
 2 raises his arms (frame 41) for 64 frames while 'BONUS' and the amount are shown
   (5000 for levels 0-1, 10000 for 2-3, 15000 for 4-5); then the bonus is added and
   his armour is restored
 3 walks on for 70 frames; then g_Level + 1 (wrapping after 6), g_LevelDone, and
   sub state 2 -> InPlay loads the next level."""
for a,n in [(0x64A8,'Bonus_Setup'),(0x64E0,'Bonus_Walk'),(0x650E,'Bonus_Show'),(0x65AE,'Bonus_WalkOff')]: N(a,n)
for a,t in [
 (0x64C0,'37 px past the right edge'),
 (0x64F6,'arms raised'),
 (0x652C,'lower on levels 4-6'),
 (0x6558,'add the bonus'),
 (0x6564,'armour back on for the next level'),
 (0x65C4,'next level'),
]: C(a,t)

# --------------------------------------------------------------------------- game over / high scores
HEADERS[0x65EE] = """GameOver - sub state 3. Steps (g_SubState2 / g_SubState3):
 0     'GAME OVER PLAYER ONE' (or TWO) for 200 frames
 1/0   not in the top 10 -> step 2. Otherwise insert the score and three blank initials
       (the lower entries move down), redraw the screen where the camera was and show
       the letter grid; the 1MB build plays tune 3 (1 for a new top score)
 1/1   NameEntry
 1/2   200 frames, then
 2     back to InPlay (g_GameState 0, sub state 2), which switches to the other player
       or returns to the attract screens.
Name entry borrows Arthur's variables: g_ArthurX/Y = cursor column (0-12) / row (0-4),
g_ArthurAux = letters entered, g_Crouching/g_Jumping/g_Falling = the three initials,
g_ShownScore = pointer to the name's slot in g_HiNames."""
for a,t in [
 (0x65FA,'200 frames'),
 (0x6656,'wait'),
 (0x665E,'redraw origin = where the camera is'),
 (0x668A,'rank: first entry the score beats'),
 (0x66A4,'shift the lower scores down and insert'),
 (0x66BA,'and the names (3 bytes each)'),
 (0x66D4,'remember where the initials go'),
 (0x66D8,'1MB build: tune 3, or 1 for a new top score'),
 (0x66F2,'no letters yet; initials = spaces'),
 (0x6704,'cursor on END'),
 (0x6726,'200 frames after the name'),
 (0x6736,'-> InPlay: next player or attract mode'),
]: C(a,t)
N(0x613C, 'NameEntry', """High-score name entry (GameOver step 1/1), at most every 2 frames.
Joystick moves the cursor over the 13 x 5 grid (NameGridLetters); fire on a letter adds
it (up to 3), cell 62 adds a space, 63 rubs out, 64 (END) stores the name:
 ')!(' sets g_CheatOn (lives never decrease, and once his armour is gone nothing can
       hit Arthur) and stores NameCheat instead;
 blank initials are stored as '504' (NameBlank).
A new top score is copied to the HUD's TOP SCORE; the 1MB build plays tune 11 (6 for a
new top score). Then 200 frames to GameOver step 1/2.""")
for a,t in [
 (0x6152,'right'),(0x615A,'left'),(0x6162,'down'),(0x616A,'up'),(0x6172,'fire'),
 (0x617A,'cell = row * 13 + column'),
 (0x6186,'END'),(0x618C,'rub out'),(0x6194,'space'),
 (0x61A4,'three letters already?'),
 (0x61EE,'store the initials'),
 (0x61F8,'1MB build: tune 11 ...'),
 (0x61FE,'new top score: update the HUD'),
 (0x6210,'... or 6'),
 (0x6278,'redraw the screen and the grid'),
]: C(a,t)
N(0x60A6, 'DrawNameGrid', """Draw the 13 x 5 letter grid for name entry, d5 = the cursor's cell (shown in
white on odd frames, so it flashes), then 'INITIAL' and the three letters so far""")
N(0x0B9E3, 'TxtInitial')
N(0x0B988, 'TxtGameOver'); N(0x0B99A, 'TxtOne'); N(0x0B99E, 'TxtTwo')
HEADERS[0xB9A2] = """NameGridLetters - the 65 cells of the name-entry grid: A-Z, a-z, ! ? & , . ( ) / : * @,
then the rub-out ($1E) and END ($1F) glyphs. Cell 62 ('@') enters a space."""

# --------------------------------------------------------------------------- attract screens
N(0x62A6, 'DrawCreditsScreen', """Attract screen 1: the title logo (font characters $80-$D5, 3 rows of 22, then
'tm'), the credits (program R Frankish, graphics D Percival, sound M Cooksey), the
start and control keys, then the copyright lines shared with DrawHiScoreTable""")
N(0x6372, 'DrawHiScoreTable', """Attract screen 2: 'BEST RANKING', the 10 ranks ('TOP', '2ND' ... '10TH') with
'PTS', each player's initials and BCD score, then the Capcom copyright lines""")
N(0x6404, 'DrawCopyright')
for a,n in [(0xB79F,'TxtTopScore'),(0xB7A9,'TxtCopyright'),(0xB7C1,'TxtLicence1'),(0xB7E1,'TxtLicence2'),
            (0xB802,'TxtTrademark1'),(0xB820,'TxtTrademark2'),(0xB841,'TxtCreditProgram'),
            (0xB855,'TxtCreditGraphics'),(0xB869,'TxtCreditSound'),(0xB87C,'TxtBestRanking'),
            (0xB8A9,'TxtRanks'),(0xB8DB,'TxtPts'),(0xB8E0,'TxtPressF1'),(0xB8FD,'TxtPressF2'),
            (0xB91A,'TxtFire1'),(0xB937,'TxtFire2'),(0xB954,'TxtPause'),(0xB96E,'TxtAbort')]:
    N(a,n)
N(0xB88B, 'DefaultHiNames', """Initial high-score names (10 x 3 bytes): Ric, DP, MC, PJC, GB, JCM, GnG x 4 -
the programmer (Richard Frankish), the artist (Dave Percival), the musician (Mark
Cooksey) and others. Every default score is 10000.""")
for a,t in [
 (0x62B8,'title logo: font characters $80-$D5'),
 (0x62D6,"'tm'"),
 (0x6322,"fire starts the mode last chosen (1 or 2 players), F1 / F2 choose"),
]: C(a,t)

HEADERS[0x6EF2] = """Camera: switch to the redrawn screen, or scroll; then request the next redraw.
These rules are written out as a Python model in tools/verify/camera.py, which matches
the real code on 20,000 random states.
 |x| below is the code's (NOT for negatives, so one less); offsets are the camera target
 relative to the current origin (g_CamDeltaX/Y) and to the redrawn one (g_PendFineX/Y);
 a 'class' is 0 under 8 px, 1 under 16, 2 beyond.
Switch (CameraJump), only when a redraw has finished (g_RedrawDone):
 on the ground (or jumping), by the X offset's class:
   2 -> if the new origin is closer in X
   1 -> the same, unless either new offset is class 2
   0 -> if the new origin is closer in Y and its X offset is not class 2
 climbing or falling, by the Y offset's class:
   2 -> if closer in Y
   1 -> if closer in X or Y, unless either new offset is class 2
   0 -> if closer in X and the new Y offset is class 0
Otherwise the fine scroll is the offset clamped to -16..15; if X had to be clamped (or Y,
while falling at 5 px/frame) the logic freezes.
Next redraw, when none is running - the new origin, from the current one:
 on the ground (or jumping), by facing, from the X offset dx: right: dx > -2 -> +1 tile,
 dx < -16 -> -1; left: dx > 15 -> +1, dx < 1 -> -1; standing: dx > 7 -> +1, dx < -8 -> -1.
 Y offset dy: > 7 -> +1, < -8 -> -1.
 climbing or falling: dy > 7 -> + dy/16 + 1 tiles; dy < -8 (while falling: dy < 0) ->
 + floor(dy/16); X as when standing.
 The new origin is compared with the current one, not the one already drawn, so while
 Arthur keeps moving the same origin is redrawn again every camera step until the switch:
 RedrawScreen runs almost all the time.
In practice (tools/verify/camsim.py): walking right the screen is switched every 16 px with
the fine scroll between -8 and +7, and the logic never freezes unless a redraw takes more
than 7 camera steps (14 frames). Falling at full speed (10 px per camera step) freezes
whenever a redraw takes more than one camera step. One redraw is about 14,600
instructions plus 288 blits (around 2-3 frames of CPU time on its own, more while the
game logic is running), so falls cause short freezes and walking does not."""
