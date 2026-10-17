# Cut-scenes: the opening scene, the ending, 'weapon useless' and the progress map.
# Executed inside anno_db.py after anno_arthur.py.
OBJ_RANGES.append((0x71EC, 0x7736))
TYPE_FIELDS.append((0x71EC, 0x7736, {
 0x1C: ('Scn_Target', "ending: the princess's stopping X, then the message timer"),
 0x30: ('Scn_Timer', 'opening scene: frame countdown on the demon'),
}))

HEADERS[0x71EC] = """==================================================================
Ending - sub state 6, entered when Astaroth is beaten with the cross (BossKilled).
Steps (g_SubState2):
 0 Arthur (armour on) faces right at Y $4E; the princess (type 15, g_Enemy1) starts at
   X $F3. They meet a third of the way from Arthur: g_ArthurAux = his stop X, the
   princess stops 16 px to its right.
 1 both walk towards each other at 1.125 px/frame; Arthur raises his arms (frame 41)
   when he arrives.
 2 the princess takes frame 5 (size 3); hold for 550 frames.
 3 'CONGRATULATIONS !' / 'THIS STORY HAS A HAPPY ENDING.'; when the timer runs out,
   award 50000 (AddScore 21), print the score, and end the game: no lives left,
   sub state 3 (game over and high-score entry).
==================================================================="""
for a,n,h in [
 (0x720E,'Ending_Setup',None),
 (0x7276,'Ending_Walk',None),
 (0x72B4,'Ending_Embrace',None),
 (0x72CC,'Ending_Message',None),
 (0x732E,'Ending_Draw',"Queue the princess, then the shared scene exit (redraw and show the screen)"),
 (0x733E,'Princess_AnimWalk',"Princess walking: frames 3, 4"),
 (0x7356,'TxtHappyEnding',None),
 (0x7375,'TxtWeaponUseless',None),
 (0x738E,'TxtGetCrucifix',None),
 (0x7440,'Intro_Setup',None),
 (0x7514,'Princess_AnimSit',"Princess frame 1 (held)"),
 (0x7516,'Princess_AnimStand',"Princess frame 0 (held): as the demon appears"),
 (0x7518,'Princess_AnimCarried',"Princess frame 2 (held): in the demon's grip"),
 (0x751A,'Intro_DemonAppears',None),
 (0x756C,'Intro_DemonWait',None),
 (0x758A,'Intro_DemonHover',None),
 (0x75AA,'Intro_DemonSwoop',None),
 (0x75EE,'Intro_Abduction',None),
 (0x7664,'Intro_Pause',None),
 (0x7672,'Intro_DemonGone',None),
 (0x768A,'Intro_WalkToArmour',None),
 (0x76B8,'Intro_WalkOn',None),
 (0x76E0,'Intro_Finish',None),
 (0x76FE,'Intro_Draw',"Queue the princess, the demon and the armour (each only if active and on\nscreen), then the shared scene exit"),
 (0x7848,'ProgressMap_Scroll',None),
 (0x7880,'ProgressMap_Wait',None),
]:
    N(a,n,h)

HEADERS[0x7402] = """==================================================================
IntroCutscene - sub state 5, the opening scene (shown once per game: g_ShowIntro).
Objects: the princess in g_Enemy1 (type 15), the demon in g_Enemies slot 0 (type 6, the
Satan graphics and animations), and Arthur's armour on the ground in special object 0.
Steps (g_SubState3):
  0 Arthur sits with the princess in his underwear (frame 40) at X $60; his armour
    lies at X $50. Draw both screens; wait 60 frames. (1MB build: tune 14.)
  1 the demon appears top right ($C5,$A0), the princess changes to frame 0; wait 20 frames.
  2 the demon flaps for 64 frames,
  3 then turns to dive (the 1MB build stops the music: tune 0).
  4 it dives down-left at (-0.33, -6) px/frame until it reaches the floor; it grabs the
    princess and Arthur is hit (ArthurState 1, pushed left).
  5 Arthur is knocked back by the normal ArthurUpdate (g_NoArmour is clear, so it takes
    the 'armour flies off' path; the pieces are never drawn here) while the demon carries the princess up and
    right at (+1.125, +4.19) until Y $A0, where the princess is removed.
  6-7 32 frames, then the demon is removed.
  8 Arthur walks to his armour at X $50 and puts it on (g_NoArmour cleared),
  9 walks on to X $60, stands (frame 4) for 30 frames,
 10 and the game starts: sub state 1, progress map skipped (g_SubState2 = 1).
==================================================================="""
HEADERS[0x7736] = """==================================================================
ProgressMap - sub state 1 / g_SubState2 0, before each level (and after a life lost).
 0 load FileProgressMap and unpack it into the spare screen: 80 lines x 5 planes,
   each plane line RLE-packed to $2C bytes (n >= 0: copy n+1 bytes; n < 0: repeat the
   next byte -n+1 times; -128: nothing), with blank borders. Point the map copper list
   ($1A250) at it, and place a flashing Arthur marker from ProgressMapMarkers.
 1 scroll the map 144 px to the left, one pixel a frame; the marker stops flashing.
 2 hold for 100 frames, then on to level set-up (g_SubState2 = 1).
The 1MB build stops the music and unpacks the copy kept at PROGRESS_MAP_CACHE instead
of loading the file.
==================================================================="""
HEADERS[0x7810] = """ProgressMapMarkers - per level, two (x.w, y.w) points on the map: level start and
checkpoint (used when g_Checkpoint is set). The marker is drawn 8 px right and 8 px
higher. Levels 4-6 use the same point for both."""

for a,t in [
 # ending
 (0x720E,'meet a third of the way from Arthur to the princess'),
 (0x7224,"the princess stops 16 px to Arthur's right"),
 (0x723E,'armour on'),
 (0x724A,'princess: active, at ($F3,$4E), type 15, size 1'),
 (0x7280,'Arthur walks right 1.125 px/frame'),
 (0x728E,'arrived: arms raised (frame 41)'),
 (0x729E,'princess walks left 1.125 px/frame'),
 (0x72B4,'princess frame 5, size 3 - together'),
 (0x72C0,'550 frames (about 11 seconds)'),
 (0x72CC,'white on the background colour'),
 (0x72FA,'50000 points'),
 (0x7300,"print the score in the player's HUD position"),
 (0x7314,'game over: lives gone, sub state 3 (high-score table / name entry)'),
 # weapon useless
 (0x73B4,'ink 13 on paper 6'),
 (0x73E8,'g_StateTimer set by BossKilled'),
 (0x73F0,'back to level index 4 (the start of the last two levels)'),
 # intro
 (0x7446,'Arthur at ($60,$40), sitting (frame 40), facing right'),
 (0x7474,'60 frames'),
 (0x747A,'demon slot free for now'),
 (0x7480,'g_Enemy1 = princess: active, on screen, state 1, size 1, type 15, at ($70,$40)'),
 (0x74B0,'special object 0 = the armour on the ground: at ($50,$38), frame 2'),
 (0x74D4,'draw and show both screen buffers before the scene starts'),
 (0x74EC,'bitplane DMA on'),
 (0x7522,'the demon: type 6 graphics, size 4, at ($C5,$A0)'),
 (0x754A,'wait 20 frames'),
 (0x7550,'Satan anim: wings spread'),
 (0x755C,'princess frame 0'),
 (0x7574,'flap'),
 (0x757C,'for 64 frames'),
 (0x75AA,'dive: X -0.33, Y -6 px/frame'),
 (0x75BE,'Z set = reached the floor'),
 (0x75D2,'the princess is grabbed'),
 (0x75DA,'Arthur hit, pushed to the left'),
 (0x75EE,'Arthur: knockback flight until he lands'),
 (0x75F8,'landed: face right'),
 (0x7612,'the demon flies off up-right with the princess, X +1.125, Y +4.19 px/frame'),
 (0x7648,'off the top (Y >= $A0)?'),
 (0x765A,'princess gone'),
 (0x7664,'32 frames'),
 (0x767A,'demon gone'),
 (0x7692,'walk right'),
 (0x76A0,'reached the armour: pick it up'),
 (0x76A6,'armour on'),
 (0x76CE,'stand (frame 4) for 30 frames'),
 (0x76E6,'intro done; start the game at level set-up (no progress map)'),
 (0x7732,'shared scene exit (as Ending/WeaponUseless)'),
 # progress map
 (0x7744,'load the packed map picture'),
 (0x7754,'unpack into the lower of the two spare screens'),
 (0x7766,'clear $7D00 bytes'),
 (0x7770,'$2C bytes per plane line; 80 lines'),
 (0x7774,'5 planes'),
 (0x7778,'4 blank bytes at the left'),
 (0x777E,'n < 0: run'),
 (0x7780,'n >= 0: n+1 literal bytes'),
 (0x778A,'-n+1 copies of the next byte (-128: none)'),
 (0x779C,'2 blank bytes at the right (line = $32 bytes)'),
 (0x77A6,'blank area below the picture'),
 (0x77BA,'map copper list'),
 (0x77C6,'marker = ProgressMapMarkers[level][checkpoint]'),
 (0x7804,'marker flashes while the map scrolls'),
 (0x7858,'drives the marker flash'),
 (0x785C,'scroll 1 px a frame up to 144 px'),
 (0x7876,'then hold for 100 frames'),
]:
    C(a,t)
