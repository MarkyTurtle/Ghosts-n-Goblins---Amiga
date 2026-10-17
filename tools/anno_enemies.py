# Detailed annotations of the ordinary enemy handlers. Executed inside anno_db.py after anno_bosses.py.

# =====================================================================================
# Big Man - type 10 (levels 1 and 4)
# =====================================================================================
TYPE_FIELDS.append((0x103BA, 0x109C4, {
 0x1C:('BM_ShotPtr',  'position in BigManShotTimes'),
 0x20:('BM_WalkPtr',  'position in BigManWalkTimes'),
 0x30:('BM_Timer',    'pause after shooting down; death timer'),
 0x31:('BM_EdgeDir',  'direction it was walking when it found the edge; wind-up timer'),
 0x32:('BM_AtEdge',   '1 = no floor just ahead'),
 0x33:('BM_EdgeTurn', 'already turned back from this edge'),
 0x34:('BM_Crouched', 'starts crouching (from O_Param)'),
 0x35:('BM_ShotTime', 'frames to the next shot'),
 0x36:('BM_WalkTime', 'frames to the next pause'),
 0x38:('BM_CrouchTime','x 64 frames of crouching'),
 0x39:('BM_PauseTime','frames of the current pause'),
}))
HEADERS[0x103BA] = HEADERS.get(0x103BA,'') + """

Behaviour, as coded:
  * Walks at 0.53 px/frame, turning back at the edge of a floor, and pauses (70 or 100
    frames, random) after each walk time in BigManWalkTimes, then picks a random direction.
  * When Arthur is on its level (10 px below to 45 px above), it fights: paces to and
    fro across him (turning 40 px past him), charges at 2 px/frame, and throws enemy
    shot type 3 on BigManShotTimes (10-frame wind-up).
  * When Arthur is directly below (within 10 px across) it crouches and throws down
    every 30 frames.
  * Each hit makes it flinch for 6 frames. Only acts while on screen."""
for a,n,h in [
 (0x103D6,'BigMan_Init',"State 0: 10 HP, size 3, face Arthur, start the scripts; wait until on screen"),
 (0x10440,'BigMan_WaitVisible',None),
 (0x10455,'BigManShotTimes',"frames between shots: 45, 35, 20, 20, 42, 60, 35, 50, 28 (bit 7 = loop)"),
 (0x10460,'BigManWalkTimes',"frames of walking between pauses: 190, 100, 163, 230, 98, 156, 120, 160, 120"),
 (0x1046C,'BigManMoveTable',"O_Dir 0/1: +-0.53 walking; 2/3: +-2.0 charging"),
 (0x1047C,'BigMan_Active',"State 1 (on screen only). O_Step: 0 walk, 1 fight, 2 shoot down, 3 flinch"),
 (0x104BC,'BigMan_Flinch',"6 frames after a hit, then walk"),
 (0x104E2,'BigMan_Walk',"O_Step2: 0 start, 1 walk, 2 pause, 3-4 crouch"),
 (0x10504,'BigMan_WalkStart',None),
 (0x1053A,'BigManCrouchTimes',"x 64 frames: 2, 3, 3, 2"),
 (0x1053E,'BigMan_Walking',"Arthur on its level: fight. Directly below it: shoot down. Otherwise walk,\nturn at floor edges, and pause when the walk time runs out."),
 (0x10614,'BigMan_Pause',"then a random direction"),
 (0x1062E,'BigMan_CrouchWait',"Waits until Arthur is within 16 px of it vertically (one unsigned compare:\nO_Y - Arthur Y + 16 <= 32), then counts BM_CrouchTime"),
 (0x10646,'BigMan_Crouching',None),
 (0x1065C,'BigMan_CheckEdge',"Is there floor 2 px below? No: BM_AtEdge = 1 and remember the direction"),
 (0x10688,'BigMan_Fight',"O_Step2: 0 face Arthur, 1 pace, 2 charge, 3 wind up, 4 throw"),
 (0x106AA,'BigMan_FightStart',None),
 (0x106CA,'BigMan_Pace',"Arthur left its level: walk. Otherwise turn when 40 px past him."),
 (0x1072E,'BigMan_Charge',"Run at 2 px/frame (not over the edge), and count down to the next shot"),
 (0x107C8,'BigMan_WindUp',"10 frames, then the throw animation"),
 (0x107E2,'BigMan_Throw',None),
 (0x107F6,'BigMan_ShootDown',"O_Step2: 0 crouch, 1 check, 2 throw (frame 10 of 30), 3 pause 20"),
 (0x10814,'BigMan_CrouchStart',None),
 (0x10832,'BigMan_ShootDownCheck',None),
 (0x1088C,'BigMan_ShootDownThrow',None),
 (0x108AA,'BigMan_ShootDownPause',None),
 (0x108B8,'BigMan_Fire',"Enemy shot type 3: fighting, 16 px ahead the way it faces; shooting down, from\n8 px below, direction 2"),
 (0x1091E,'BigMan_Dying',"State 2: sound 20, EnemyBurst, 112 frames"),
 (0x10950,'BigMan_Free',"State 3: give the spawn quota back, free the slot"),
 (0x10958,'BigMan_AnimWalk',None), (0x10970,'BigMan_AnimPauseA',None), (0x10984,'BigMan_AnimPauseB',None),
 (0x10998,'BigMan_AnimThrow',None), (0x109A4,'BigMan_AnimCrouch',None), (0x109B8,'BigMan_AnimFlinch',None),
]:
    N(a,n,h)
for a,t in [
 (0x10494,'hit (EnemyHitByShot set O_Param): flinch'),
 (0x10542,'Arthur from 10 below to 45 above it: fight'),
 (0x10562,'Arthur within 10 px across and below: shoot down'),
 (0x105A0,'every 16 frames: floor ahead?'),
 (0x105B4,'at the edge and still facing it: turn round'),
 (0x105F8,'pause 100 frames'),
 (0x10608,'or 70'),
 (0x10774,'charge speed: O_Dir + 2 in the move table'),
 (0x108E8,'move.w copies O_Dir and O_Size into the shot'),
 (0x10916,'enemy shot type 3'),
]:
    C(a,t)

# =====================================================================================
# Magician - type 7 (previously labelled "Ghost")
# =====================================================================================
TYPE_FIELDS.append((0xF422, 0xF5C4, {
 0x30:('Mag_Timer',  'rise / fade timer (60 frames)'),
 0x31:('Mag_Cast',   'frames before and after the spell (20)'),
}))
HEADERS[0xF422] = HEADERS.get(0xF422,'') + """

Behaviour, as coded: the spawner puts it where Arthur last shot a gravestone. It rises
cloaked for 60 + 20 frames (shots pass through: O_Active 2), throws off the cloak and
becomes hittable (size class 9), casts one spell at Arthur - enemy shot type 0, which turns
him into a frog (EnemyShotsVsArthur) - waits 20 frames, then cloaks again and blinks out
over 60 frames. The graphics are the hooded figure (frames 0-1) and the winged figure
(frames 2-3)."""
for a,n,h in [
 (0xF43E,'Magician_Init',"State 0: shots pass through (O_Active 2), size 3, face Arthur, cloaked"),
 (0xF460,'Magician_FaceArthur',"O_Dir 0 if Arthur is to the right, 1 if to the left"),
 (0xF472,'Magician_Active',"State 1. O_Step: 0 rise, 1 cast, 2 fade"),
 (0xF48A,'Magician_Rise',"60 frames, turning to face Arthur"),
 (0xF4AC,'Magician_Cast',None),
 (0xF4C4,'Magician_CastStart',None),
 (0xF4CE,'Magician_Reveal',"After 20 frames: hittable, size 9, the winged figure, and cast the spell"),
 (0xF4F8,'Magician_AfterCast',"20 frames, then fade"),
 (0xF50A,'Magician_Spell',"Enemy shot type 0 (the frog spell) from 10 px below its centre, the way it faces"),
 (0xF53C,'Magician_Fade',"Cloak again, shots pass through, blink for 60 frames, then remove"),
 (0xF588,'Magician_Dying',"State 2: sound 17, EnemyDieFacing, 63 frames"),
 (0xF5BC,'Magician_Free',"State 3: give the spawn quota back, free the slot"),
 (0xF5C4,'Magician_AnimCloak',None), (0xF5C8,'Magician_AnimReveal',None),
]:
    N(a,n,h)
C(0xF4D4,'hittable from now on')
C(0xF536,'enemy shot type 0: the frog spell')
C(0xF548,'shots pass through again')
C(0xF570,'invisible every other 2 frames')
N(0x8F4E,'EnemyShotsVsArthur',"Enemy shots against Arthur. Shot type 0 (the Magician's spell) turns him into a frog\n(g_FrogTimer = 8); any other hits him (g_ArthurState 1), except when the cheat is on\nand g_NoArmour is set. A shot that hits is removed. Skipped while Arthur flashes or is\nalready hit; crouching uses the smaller box table.")
C(0x8FAC,'type 0: the frog spell')

# =====================================================================================
# Skeleton - type 9 (castle levels 4-5)
# =====================================================================================
TYPE_FIELDS.append((0x10082, 0x103BA, {
 0x1C:('Skl_VelY',   'vertical speed (16.16, up = positive)'),
 0x20:('Skl_BaseY',  'Y where the leap started (word)'),
 0x24:('Skl_LeapDX', 'horizontal speed of the leap (16.16)'),
 0x30:('Skl_Hops',   'hops left before the leap (2)'),
 0x31:('Skl_Pause',  'frames of pause after landing (6)'),
 0x32:('Skl_Phase',  'leap: sine index'),
}))
HEADERS[0x10082] = HEADERS.get(0x10082,'') + """

Behaviour, as coded: lies as a pile of bones (size class 0) until Arthur comes within
32 px of it, then rises out of the floor and hops: two small hops (3 px/frame up, 0.8
px/frame across), turning towards Arthur when he is 64+ px away, then a big leap that
lands where Arthur was (dx / 42 per frame, a sine arc about 80 px high), then hops again.
It does not give its spawn quota back when it is removed (the others do)."""
for a,n,h in [
 (0x1009E,'Skeleton_Init',"State 0: lie dormant until Arthur is within 32 px both ways"),
 (0x100B6,'Skeleton_Dormant',None),
 (0x100F0,'Skeleton_Active',"State 1. O_Step: 0 rise, 1 hop, 2 leap"),
 (0x1010C,'Skeleton_Rise',None),
 (0x10124,'Skeleton_RiseStart',"Start rising at 3.5 px/frame"),
 (0x1014E,'Skeleton_Rising1',None),
 (0x1015C,'Skeleton_Rising2',"when the animation ends: size 3, start hopping"),
 (0x10176,'Skeleton_RiseStep',"Y += speed, speed -= 0.16"),
 (0x1018A,'Skeleton_Hop',"O_Step2: 0 start, 1 take off, 2 rise, 3 fall, 4-5 pause and aim"),
 (0x101AE,'Skeleton_HopStart',"2 hops before the leap"),
 (0x101C2,'Skeleton_TakeOff',"3 px/frame upwards"),
 (0x101D6,'Skeleton_HopRise',"gravity 0.165 px/frame^2 until the top"),
 (0x101EE,'Skeleton_HopFall',"down to -3 px/frame until it lands"),
 (0x1020C,'Skeleton_Land',None),
 (0x10216,'Skeleton_LandPause',"6 frames, aim, then hop again or leap"),
 (0x10238,'Skeleton_Aim',"Arthur 64+ px away: face him (O_Dir 1 right, 3 left); closer: keep going"),
 (0x10262,'Skeleton_HopMove',"X += move table dx for O_Dir, Y += Skl_VelY"),
 (0x10288,'Skeleton_Leap',"O_Step2: 0 aim, 1 up, 2 down, 3-4 pause"),
 (0x102A8,'Skeleton_LeapStart',"Skl_LeapDX = (Arthur X - X) / 42: lands on his spot after 42 frames"),
 (0x102D8,'Skeleton_LeapUp',"phase += 6 until the top"),
 (0x102F0,'Skeleton_LeapDown',"until the phase wraps, or it lands (checked near the end)"),
 (0x1031C,'Skeleton_LeapLand',None),
 (0x10326,'Skeleton_LeapPause',None),
 (0x1033E,'Skeleton_LeapY',"Y = Skl_BaseY + sin(phase) x 2 x 80 / 256"),
 (0x1035E,'Skeleton_Dying',"State 2: sound 17, EnemyDieFacing"),
 (0x10380,'Skeleton_Free',"State 3: free the slot (no spawn quota given back)"),
 (0x10384,'SkeletonMoveTable',"(dx, dy) 8.8: 0 still, 1 right 0.8, 2 down, 3 left 0.8, 4 up (only dx is used)"),
 (0x10398,'Skeleton_AnimBones',None), (0x1039C,'Skeleton_AnimRise',None), (0x103A2,'Skeleton_AnimHop',None),
 (0x103AE,'Skeleton_AnimLeap',None),
]:
    N(a,n,h)

# =====================================================================================
# Zombie - type 11 (graveyard; from spawners)
# =====================================================================================
TYPE_FIELDS.append((0x109C4, 0x10CB6, {
 0x1C:('Zmb_SizePtr', 'next entry in the emerge / sink size-class list'),
 0x30:('Zmb_Timer',   'frames before emerging; frames to walk on after passing Arthur'),
 0x31:('Zmb_WalkTime','walk time, counted every other frame (180 = 360 frames)'),
 0x32:('Zmb_Steps',   'size-class steps left while emerging / sinking'),
}))
HEADERS[0x109C4] = HEADERS.get(0x109C4,'') + """

Behaviour, as coded: created hidden (shots pass through), drops onto the floor, waits a
random 12-187 frames (parameter 1: no wait), then rises out of the ground, its size class
growing with the animation. It shambles towards Arthur at 0.81 px/frame; once past him it
walks on for 40-110 frames, then sinks back into the ground (also after 360 frames, or
when the floor ends). Shots pass through it while it rises and sinks."""
for a,n,h in [
 (0x109F0,'Zombie_Init',"State 0. O_Step 0: O_Step2 0 hide, 1 drop to the floor, 2 wait, 3 start rising;\nO_Step 1: rise"),
 (0x109E0,'ZombieInitSteps',None),
 (0x10A06,'Zombie_Hide',"shots pass through, size 0, invisible"),
 (0x10A18,'Zombie_Drop',"Move down 2 px a frame until there is floor; parameter 1 starts at once"),
 (0x10A58,'Zombie_WaitRise',None),
 (0x10A64,'Zombie_StartRise',"face Arthur, rising animation"),
 (0x10A8C,'Zombie_NoFloor',None),
 (0x10A94,'Zombie_Rise',"Size class follows ZombieRiseSizes as the animation runs; then active and hittable"),
 (0x10AF2,'ZombieWalkSteps',None),
 (0x10AFE,'Zombie_Active',"State 1. O_Step 0 walk (O_Step2 0 start, 1 to Arthur, 2 past him), 1 sink"),
 (0x10B14,'Zombie_WalkStart',None),
 (0x10B5C,'Zombie_WalkToArthur',None),
 (0x10BA8,'Zombie_WalkPast',None),
 (0x10BC0,'Zombie_Sink',"Shots pass through; size class follows ZombieSinkSizes, then remove"),
 (0x10C14,'Zombie_Dying',"State 2: sound 20, EnemyDieFacing"),
 (0x10C36,'Zombie_Free',"State 3: free the slot, give the spawn quota back"),
 (0x10C3E,'ZombieRiseDelays',"16 random delays before rising (frames)"),
 (0x10C4E,'ZombieRiseSizes',"size class at each step of rising"),
 (0x10C57,'ZombieSinkSizes',"size class at each step of sinking"),
 (0x10C5E,'ZombieWalkOn',"frames to walk on after passing Arthur: 40, 90, 110, 80, 70, 100, 90, 50"),
 (0x10C66,'ZombieMoveTable',"O_Dir 0/1: +-0.81 px/frame (2/3: +-1.63, unused)"),
 (0x10C76,'Zombie_AnimRise',None), (0x10C7A,'Zombie_AnimSink',None), (0x10CB6,'Zombie_AnimWalk',None),
]:
    N(a,n,h)
C(0x10A4C,'walk for 180 x 2 frames at most')
C(0x10B96,'every other frame')

# =====================================================================================
# Crow / bat - type 1. O_Param picks the behaviour.
# =====================================================================================
TYPE_FIELDS.append((0xCBAC, 0xD058, {
 0x1C:('Crw_WaitList', 'list of 8 random waits (CrowWaits)'),
 0x20:('Crw_BaseY',    'centre line of the wavy flight / arc (word)'),
 0x24:('Crw_Phase',    'sine phase (word, high byte = table index)'),
 0x30:('Crw_Amp',      'height of the arc / wave'),
 0x31:('Crw_Crow',     '1 = crow graphics and speeds (param 3+)'),
 0x32:('Crw_Wait',     'frames before it takes off'),
 0x33:('Crw_Look',     'perched: frames of the current look-around; flying: half-wave count'),
 0x34:('Crw_Speed',    'wave speed index (always 0)'),
}))
HEADERS[0xCBAC] = HEADERS.get(0xCBAC,'') + """

Behaviour, as coded - by O_Param:
  0, 1  do nothing (never used).
  2     bat (levels 2, 4): hangs until on screen and a random wait has passed, then
        flies off in one arc 52-122 px high (85 frames; 3 in 16 turn round first), then
        flies on in a wave of random height.
  3     crow (level 1): perches, looking about (random poses) and turning to face Arthur;
        after a random wait it dives straight at him in 16 directions at 1.7 px/frame.
  4     crow flying in from the edge of the screen at double speed, then in a wave.
  5     crow (level 0, on the gravestones): perches as 3, then flies off in a wave.
O_Dir: 1 = right (towards Arthur when he is to the right), 0 = left."""
for a,n,h in [
 (0xCBC8,'CrowWaits',"8 random waits before taking off (frames)"),
 (0xCBD0,'BatMoveTable',"O_Dir 0/1: -1.3 / +1.06 px/frame"),
 (0xCBE0,'CrowMoveTable',"O_Dir 0/1: -1.25 / +1.25 px/frame"),
 (0xCBF0,'Crow_Init',"State 0: graphics, size class and move table for the parameter"),
 (0xCC7A,'Crow_Active',"State 1: dispatch on O_Param"),
 (0xCCA4,'Bat_Active',"Param 2. O_Step: 0 hang, 1 take off, 2 arc, 3 wave"),
 (0xCCC0,'Bat_Hang',None),
 (0xCCF4,'Bat_TakeOff',None),
 (0xCD10,'BatArcHeights',"16 random arc heights (px)"),
 (0xCD20,'Bat_Arc',"One arc: phase += 3/256 of a turn per frame; then the wave"),
 (0xCD9C,'Bat_Wave',None),
 (0xCDC4,'Crow_Perched',"Params 3 and 5. O_Step 0 perch (O_Step2 0 wait, 1 pose, 2 look), 1 dive"),
 (0xCDE4,'Crow_PerchStart',None),
 (0xCE02,'CrowPoses',"random look-around pose numbers"),
 (0xCE0A,'CrowPoseTimes',"frames per pose: 58-75"),
 (0xCE12,'Crow_Pose',None),
 (0xCE5C,'Crow_Look',"Hold the pose; turn when Arthur passes; take off when Crw_Wait runs out"),
 (0xCE98,'Crow_Dive',"Dive straight at Arthur (16-way, CrowDiveTable) until far off screen"),
 (0xCEB6,'Crow_FlyAnim',None),
 (0xCEEC,'Crow_FlyIn',"Param 4. O_Step 0: fly in at double speed until 16 px inside the screen;\n1: wave"),
 (0xCEF2,'Crow_WaveStart',None),
 (0xCF48,'Crow_PerchThenWave',"Param 5: perch as param 3, then fly off in a wave"),
 (0xCF52,'CrowWaveSpeeds',None),
 (0xCF62,'CrowWaveHeights',"16 random wave heights (px)"),
 (0xCF72,'Crow_WaveY',"Y = Crw_BaseY +- sin x 2 x Crw_Amp; a new random height at every half wave"),
 (0xCFE6,'CrowWaveMove',"-1.25 / +1.25 px/frame"),
 (0xCFEE,'CrowDiveTable',"16-way (dx, dy) at 1.7 px/frame, 0 = right"),
 (0xD02E,'Crow_Dying',"State 2: sound 17, EnemyDieFacing"),
 (0xD050,'Crow_Free',"State 3: free the slot, give the spawn quota back"),
]:
    N(a,n,h)
C(0xCC2E,'param 3+: crow')
C(0xCC44,'param 4: 16 px higher')
C(0xCD34,'3 in 16: turn round')

# =====================================================================================
# Woody Pig - type 0 (level 0 forest; from spawners)
# =====================================================================================
TYPE_FIELDS.append((0xC65A, 0xCBAC, {
 0x1C:('Pig_TurnPtr',  'position in WoodyPigLoopTimes'),
 0x20:('Pig_Bomb',     'enemy shot slot it is carrying (long, 0 = none)'),
 0x30:('Pig_Drop',     '1 = pick up a shot next frame'),
 0x34:('Pig_LoopAcc',  'adds WoodyPigLoopOdds every 16 frames; a loop when it carries'),
 0x35:('Pig_TurnAcc',  'accumulator deciding the loop direction when level with Arthur'),
 0x36:('Pig_Loops',    'loops left (0-7, from the frame counter)'),
 0x37:('Pig_Turns',    'turn steps left in the loop (8); emerging animation delay'),
 0x38:('Pig_TurnDir',  '+1 or -1: which way it turns'),
 0x39:('Pig_TurnTime', 'frames to the next 1/16 turn'),
 0x3A:('Pig_Timer',    'frames of the drop animation'),
}))
HEADERS[0xC65A] = HEADERS.get(0xC65A,'') + """

Behaviour, as coded: flies in 16 directions at 1.55 px/frame (1 in 4 use the faster
WoodyPigMoveFast table). O_Param 0: flies in from the edge of the screen at double speed;
1-2: emerges in place (size class 0 growing to 2). While Arthur is within 128 px it may loop
the loop (8 turns of 1/16, up to 0-7 loops per pig, more likely the closer he is). When it
is above Arthur but not over him and no enemy shot is in flight, it picks one up (enemy shot
type 4, carried in Pig_Bomb) and drops it after a short animation (26 + 10 frames). If it is
killed while carrying, the shot is let go (state 3)."""
for a,n,h in [
 (0xC676,'WoodyPig_Init',"State 0. O_Step 0 set up, 1 fly in, 2-3 emerge"),
 (0xC694,'WoodyPig_Setup',"Shots pass through until it is on screen; O_Dir 1 (right) or 9 (left); O_Step = param + 1"),
 (0xC706,'WoodyPig_FlyIn',"Double speed until inside the screen (16-240 px from its left edge)"),
 (0xC754,'WoodyPig_Emerge',"Emerging animation (12-frame delay first); hittable at frame 4"),
 (0xC7B6,'WoodyPigMoveTable',"16 directions, 1 = right, 5 = down, 9 = left, 13 = up, 1.55 px/frame (0 = still)"),
 (0xC7FA,'WoodyPigMoveFast',"The same at 2.25 px/frame"),
 (0xC87E,'WoodyPig_Active',"State 1. O_Step: 0 fly, 1 loop, 2 drop"),
 (0xC898,'WoodyPigLoopOdds',"Added to Pig_LoopAcc by |dx| / 32 (0-3): $4C, $50, $26, $19; nothing at 128+"),
 (0xC8A0,'WoodyPig_Fly',"Fly; maybe loop; pick up a shot when above Arthur and none is in flight"),
 (0xC96E,'WoodyPig_PickUp',"Enemy shot type 4, held by the pig (state 0) until dropped"),
 (0xC9AA,'WoodyPigLoopTimes',"Frames per 1/16 turn of a loop (two variants, by slot number)"),
 (0xC9BA,'WoodyPig_Loop',"O_Step2: 0 start, 1 choose turn direction, 2 turn, 3 again?, 4 end"),
 (0xC9DC,'WoodyPig_LoopStart',None),
 (0xCA06,'WoodyPig_LoopDir',"Turn up or down depending on its height relative to Arthur"),
 (0xCA54,'WoodyPig_Turn',"8 steps of 1/16 turn (directions wrap 16 -> 1)"),
 (0xCA98,'WoodyPig_LoopAgain',"Still heading the same way in the same half of the screen: loop again"),
 (0xCABC,'WoodyPig_LoopEnd',None),
 (0xCAC6,'WoodyPig_Drop',"O_Step2: 0 face Arthur (26 frames), 1 throw pose (10), 2 let go, 3 10 frames"),
 (0xCAE4,'WoodyPig_DropStart',None),
 (0xCB06,'WoodyPig_DropPose',None),
 (0xCB30,'WoodyPig_LetGo',"Set the carried shot to state 1 (falling)"),
 (0xCB5A,'WoodyPig_DropWait',None),
 (0xCB6A,'WoodyPig_Dying',"State 2: let go of any carried shot, sound 20, EnemyBurst"),
 (0xCBA4,'WoodyPig_Free',"State 3: free the slot, give the spawn quota back"),
]:
    N(a,n,h)
C(0xC94C,'count the enemy shots in flight: d0 = 6 - free slots')
C(0xC962,'none in flight: pick one up')
C(0xC988,'enemy shot type 4')

# =====================================================================================
# Petite Devil - type 2 (from spawners)
# =====================================================================================
TYPE_FIELDS.append((0xD160, 0xD8D4, {
 0x1C:('PD_MoveTable', 'its normal 16-way move table (restored after special moves)'),
 0x20:('PD_TargetY',   'Arthur Y when this leg started (word)'),
 0x22:('PD_TurnWait',  'frames to the next 1/16 turn'),
 0x23:('PD_TurnRate',  'reload for PD_TurnWait (slower turns further away)'),
 0x30:('PD_Fine',      '1 = halve the turn wait again (param 1)'),
 0x31:('PD_Shot',      '1 = has fired its one shot'),
 0x32:('PD_Legs',      'hunting legs left (4)'),
 0x33:('PD_Turn',      'turn mode 0-3: which way it turns (DevilTurnModes)'),
 0x34:('PD_EarlyShot', '0 = may fire as it arrives (PetiteDevilArriveShot)'),
 0x35:('PD_ShotTime',  'frames before it may fire (64-95)'),
 0x36:('PD_Time',      'frames left of the current leg'),
 0x37:('PD_LegLen',    'length of the arrival leg'),
 0x38:('PD_Ready',     '1 = may fire now'),
 0x39:('PD_WantDir',   'direction it is turning towards'),
 0x3A:('PD_StepTime',  'frames per step of the recoil turn'),
 0x3B:('PD_ShotDir',   'direction of its shot (selects the recoil)'),
}))
HEADERS[0xD160] = HEADERS.get(0xD160,'') + """

Behaviour, as coded: flies in for 80-111 frames (shots pass through for the first 32),
then hunts Arthur in up to 4 legs of 48-111 frames: at the start of each leg it picks a
direction towards him and a turn rate from the vertical distance, then turns 1/16 at a time
towards it. It fires one shot only (enemy shot type 8): sideways at Arthur when level with
him (within 16 px up, 50 px across), or straight down when directly above (5 px across,
60 px above), and then recoils in a turning sweep. After its legs it leaves. It never flies
below Y = 54 (world).
Bug (checked in the emulator, tools/verify): the turning code (PetiteDevil_TurnCW/CCW)
works out the new direction in d0 and then stores #1 instead, so once a devil starts
turning it flies in direction 1 - right and a little down - whatever it was turning to."""
for a,n,h in [
 (0xD17C,'PetiteDevil_Init',"State 0, by O_Param: 0 fly in, 1 fly in (finer turns), 2 random timers"),
 (0xD194,'PetiteDevil_Init0',None),
 (0xD1DC,'PetiteDevil_Setup',"Size 0, move table, 4 legs, aim at Arthur's height, go to state 1"),
 (0xD216,'PetiteDevil_PathUnused',"Unused: follow a list of map positions (PetiteDevilPath) and appear at the first\none that is on screen"),
 (0xD244,'PetiteDevil_PathNext',None),
 (0xD2D0,'PetiteDevilPath',None),
 (0xD35C,'PetiteDevil_Init1',None),
 (0xD384,'PetiteDevil_Init2',"Random early-shot flag and 64-95 frames before it may fire"),
 (0xD3E4,'PetiteDevilArriveShot',None),
 (0xD3F4,'PetiteDevilFlyIn',"move table after the first 32 frames"),
 (0xD400,'PetiteDevil_Active',"State 1. O_Step: 0 arrive, 1 hunt, 2 recoil, 3 leave. Param 0: removed when off screen."),
 (0xD420,'PetiteDevil_RemoveOffScreen',None),
 (0xD43E,'PetiteDevil_Arrive',None),
 (0xD4AE,'PetiteDevil_Hunt',"O_Step2: 0-1 a leg towards Arthur, 2-3 a further leg, then the next"),
 (0xD4CC,'PetiteDevil_LegStart',"Out of legs: leave"),
 (0xD518,'PetiteDevil_Leg',None),
 (0xD540,'PetiteDevil_Leg2Start',None),
 (0xD560,'PetiteDevil_Leg2',None),
 (0xD582,'PetiteDevilTurnModes',None),
 (0xD592,'PetiteDevil_TurnCW',"Every PD_TurnRate frames turn one step towards PD_WantDir.\nBug: stores #1 into O_Dir instead of the new direction in d0."),
 (0xD5B6,'PetiteDevil_TurnCCW',"As PetiteDevil_TurnCW, the other way (same bug)"),
 (0xD5DA,'PetiteDevil_Recoil',"After its shot: sweep the direction round (by the shot's direction), then hunt"),
 (0xD5F8,'PetiteDevil_RecoilStart',None),
 (0xD642,'PetiteDevil_RecoilDown',None),
 (0xD668,'PetiteDevil_RecoilUp',None),
 (0xD682,'PetiteDevil_RecoilBack',None),
 (0xD69C,'PetiteDevil_Leave',"Fly off in a fixed direction"),
 (0xD6BA,'PetiteDevilLeaveDirs',None),
 (0xD6BE,'PetiteDevil_Move',"Move; keep Y >= 54; param 0 past world X $11ED and ahead of Arthur: leave"),
 (0xD70E,'PetiteDevilTurnLevel',"(mode, direction, wanted direction) when level with Arthur, facing right / left"),
 (0xD714,'PetiteDevilTurnTable',"by DirectionToArthur: (mode, direction, wanted direction)"),
 (0xD734,'PetiteDevil_Aim',"Turn rate from the vertical distance; direction and turn mode towards Arthur;\nslow turning (10) when it is above him within 30 px across"),
 (0xD7DC,'PetiteDevil_TryShoot',"Fire once (enemy shot type 8): sideways when level with Arthur, down when above him"),
 (0xD8AC,'PetiteDevil_Dying',"State 2: sound 20, EnemyBurst"),
 (0xD8CC,'PetiteDevil_Free',"State 3: give the spawn quota back, free the slot"),
 (0xD960,'PetiteDevilMoveTable',None),
]:
    N(a,n,h)
C(0xD40C,'d0 is overwritten at once (a sound call removed in both builds)')
C(0xD488,'after 32 frames: hittable, normal move table')
C(0xD5A8,'BUG?: d0 (the new direction) is discarded - move.b d0,O_Dir(a5) intended?')
C(0xD5CC,'BUG?: as above')
C(0xD6C2,'never below Y 54')
C(0xD88E,'enemy shot type 8')

# =====================================================================================
# Flying Knight - type 3
# =====================================================================================
TYPE_FIELDS.append((0xDA38, 0xDB8C, {
 0x1C:('FK_BaseY', 'centre line of its wave (word)'),
 0x31:('FK_Phase', 'sine index, +6 a frame (43 frames per half wave)'),
}))
HEADERS[0xDA38] = HEADERS.get(0xDA38,'') + """

Behaviour, as coded: flies left at 1.06 px/frame in a wave about 50 px up and down from
where it started (random first half-wave up or down). Its shield makes it immune
(O_Active $81, shots pass through) until it has flown past Arthur - only then can it be hit
(from behind)."""
for a,n,h in [
 (0xDA54,'FlyingKnight_Init',"State 0: size 1, move table, wave"),
 (0xDA78,'FlyingKnight_AnimUp',None), (0xDA7E,'FlyingKnight_AnimDown',None),
 (0xDA84,'FlyingKnightMove',"-1.06 px/frame for both halves of the wave"),
 (0xDA8C,'FlyingKnightSteps',None),
 (0xDA98,'FlyingKnight_Active',"State 1. O_Step: 0 start, 1 upper half-wave, 2 lower half-wave"),
 (0xDAB6,'FlyingKnight_Start',"Shielded ($81); random first half-wave"),
 (0xDAE8,'FlyingKnight_WaveUp',None),
 (0xDB0A,'FlyingKnight_WaveDown',None),
 (0xDB30,'FlyingKnight_Move',"Move, animate; drop the shield once past Arthur; d0 = sin(phase) x 2 x 50 / 256"),
 (0xDB62,'FlyingKnight_Dying',"State 2: sound 20, EnemyBurst"),
 (0xDB84,'FlyingKnight_Free',"State 3: free the slot, give the spawn quota back"),
 (0xDB8C,'SineTable',"256 bytes: 127 x sin(pi x i / 256) - a half sine, 0 up to 127 and back.\nShared by most flying enemies for their arcs and waves."),
 (0xDC0C,'SineTableFalling',"SineTable + 128 (127 down to 0): used as a cosine for the Red Arremer's dive"),
]:
    N(a,n,h)
C(0xDAC0,'shield up: shots pass through')
C(0xDB46,'past Arthur: can be hit')

# =====================================================================================
# Blue Killer - type 4 (turns into a Red Arremer)
# =====================================================================================
TYPE_FIELDS.append((0xDC8C, 0xE1FA, {
 0x1C:('BK_BaseY',    'start Y of a hop (word)'),
 0x1E:('BK_Phase',    'hop phase (word, +$400 a frame)'),
 0x20:('BK_Morph',    'frames until it turns into a Red Arremer (word, 3600)'),
 0x30:('BK_HopHeight','hop height: 32 or 48 px'),
 0x32:('BK_CurveWait','frames to the next 1/16 turn of the swoop'),
 0x33:('BK_CurveRate','reload for BK_CurveWait: (Y - Arthur Y) / 8'),
 0x34:('BK_Appear',   'frames before a dropping Blue Killer becomes hittable (10)'),
 0x35:('BK_WalkTime', 'frames of the current walk'),
 0x36:('BK_Delay',    'frames before a dropping Blue Killer starts (40)'),
 0x37:('BK_SwoopMode','0/1 curve right/left, 2 straight down'),
 0x38:('BK_SwoopSet', 'which pair of swoop tables'),
}))
HEADERS[0xDC8C] = HEADERS.get(0xDC8C,'') + """

Behaviour, as coded:
  * Parameter 0: walks in from the edge of the screen. Other parameters: drops from above
    (shots pass through until it appears), swooping down in a curve towards Arthur, or
    straight down when it is over him, then lands.
  * On the floor it walks towards Arthur at 1.43 px/frame for random times (16-180
    frames), hopping (32 or 48 px, 64 frames) out of the way when one of Arthur's shots
    comes at it while he is more than 128 px away, and hopping off ledges.
  * After 3600 frames (72 s) it turns into a Red Arremer (O_Type 5, O_Param 2: the blink-in
    start mode, which then takes 26,352 frames - see Enemy_RedArremer)."""
for a,n,h in [
 (0xDCA8,'BlueKiller_Init',"State 0. Parameter 0: walk in from the screen edge; otherwise drop from above"),
 (0xDCB4,'BlueKiller_Setup',None),
 (0xDCE6,'BlueKiller_WalkIn',"Animate until 16-240 px inside the screen, then start the 3600-frame timer"),
 (0xDD0C,'BlueKiller_DropInit',None),
 (0xDD3C,'BlueKiller_DropSetup',"Shots pass through; curve rate from the height above Arthur; step 4 (param 2: 5)"),
 (0xDD9C,'BlueKiller_FaceArthur',"O_Dir 0 if Arthur is to the right, 1 if to the left"),
 (0xDDAE,'BlueKiller_Active',"State 1. O_Step: 0 walk, 1 walk 2, 2 hop up, 3 hop down, 4 drop, 5 swoop"),
 (0xDDC6,'BlueKiller_MorphTimer',"After 3600 frames: become a Red Arremer (type 5, parameter 2), from state 0"),
 (0xDDFE,'BlueKillerWalkTimes',"120, 160, 60, 16 frames"),
 (0xDE02,'BlueKillerDodgeRange',"dodge only when Arthur is more than 128 px away"),
 (0xDE06,'BlueKiller_Walk',None),
 (0xDE2C,'BlueKiller_WalkStart',None),
 (0xDE4E,'BlueKiller_Walking',"Walk; no floor ahead: hop down"),
 (0xDE7A,'BlueKillerWalkTimes2',"60, 90, 120, 180 frames"),
 (0xDE7E,'BlueKiller_Walk2',None),
 (0xDEA4,'BlueKiller_Walk2Start',None),
 (0xDEBE,'BlueKiller_Walking2',None),
 (0xDED6,'BlueKiller_HopUp',"Size 2; hop 32 or 48 px high"),
 (0xDF2A,'BlueKiller_HopY',"Y = BK_BaseY + sin(phase) x 2 x BK_HopHeight / 256"),
 (0xDF52,'BlueKiller_HopDown',"Second half of the hop, then fall 2 px/frame until it lands"),
 (0xDFA2,'BlueKiller_Drop',"O_Step2: 0 wait to be on screen, 1 40 frames, 2 appear, 3-5 swoop down"),
 (0xDFC8,'BlueKiller_DropWait',None),
 (0xDFDA,'BlueKiller_DropDelay',None),
 (0xDFEC,'BlueKiller_Appear',"After 10 frames: hittable, size 2; straight down if Arthur is within 10 px across,\nno curve if within 64 px"),
 (0xE062,'BlueKiller_SwoopStart',None),
 (0xE06A,'BlueKiller_Swoop',"Curve down (direction 0 -> 5, one step every BK_CurveRate frames) until it lands"),
 (0xE098,'BlueKillerSwoopModes',None),
 (0xE114,'BlueKiller_Swoop2',None),
 (0xE120,'BlueKiller_Dying',"State 2: sound 17, EnemyDieFacing"),
 (0xE142,'BlueKiller_Free',"State 3: free the slot, give the spawn quota back"),
 (0xE14A,'BlueKillerMoveTable',"O_Dir 0/1: +-1.43 px/frame"),
 (0xE1F6,'BlueKillerFallTable',"straight down at 1.71 px/frame"),
]:
    N(a,n,h)
C(0xDDCC,'turn into a Red Arremer')
C(0xDDD2,'start mode 2 (blink in)')

# =====================================================================================
# Fire - type 14 (level 3), and the plant - types 15-17
# =====================================================================================
TYPE_FIELDS.append((0x119DA, 0x11AE6, {
 0x1C:('Fir_SizePtr', 'position in the size-class list of the current flare'),
 0x20:('Fir_WaitPtr', 'position in FireWaits'),
 0x30:('Fir_Wait',    'x 32 frames to the next flare-up'),
}))
HEADERS[0x119DA] = HEADERS.get(0x119DA,'') + """

Behaviour, as coded: a small flame (size class 1) that flares up while on screen, after
FireWaits x 32 frames: its size class steps up to 8 and 10 and back with the animation
(FireFlareSizes), so its collision box grows with the flame. It cannot be hurt."""
for a,n,h in [
 (0x11A08,'Fire_Init',None),
 (0x11A36,'Fire_Active',"Every 32 frames count down; flare up; size class follows the list as it animates"),
 (0x11AA2,'FireIdleSizes',None),
 (0x11AA6,'FireFlareSizes',"size class per animation step of a flare (bit 7 = loop back to idle)"),
 (0x11AC5,'FireWaits',"x 32 frames between flares: 4, 6, 2, 6, 4, 6, 8, 2 (loop)"),
 (0x11AD0,'Fire_Dying',"Never reached: fire cannot be hurt"),
 (0x11AD6,'Fire_Free',None),
 (0x11ADA,'Fire_AnimIdle',None), (0x11AE0,'Fire_AnimFlare',None),
]:
    N(a,n,h)

TYPE_FIELDS.append((0x11B1A, 0x11CB0, {
 0x1C:('Plt_WaitPtr', 'position in PlantWaits'),
 0x30:('Plt_Wait',    'frames to the next spit'),
 0x31:('Plt_Mouth',   'frames of the open mouth before it spits (24)'),
}))
HEADERS[0x11B1A] = HEADERS.get(0x11B1A,'') + """

Behaviour, as coded: faces Arthur; while on screen it waits PlantWaits frames, opens its
mouth for 24 frames and spits enemy shot type 6, then waits again."""
for a,n,h in [
 (0x11B48,'Plant_Init',None),
 (0x11B81,'PlantWaits',"frames between spits (bit 7 = loop)"),
 (0x11B98,'Plant_Active',"State 1. O_Step: 0 wait to be on screen, 1 wait, 2 spit"),
 (0x11BB0,'Plant_WaitSeen',None),
 (0x11BBC,'Plant_Wait',None),
 (0x11C1A,'Plant_Spit',"Enemy shot type 6"),
 (0x11C76,'Plant_Dying',"State 2: sound 20, EnemyBurst"),
 (0x11C98,'Plant_Free',"State 3: free the slot (no spawn quota given back)"),
 (0x11C9C,'Plant_AnimIdle',None), (0x11CB0,'Plant_AnimSpit',None),
]:
    N(a,n,h)
C(0x11C64,'enemy shot type 6')

# =====================================================================================
# Fire pillar - type 18 (level 2)
# =====================================================================================
TYPE_FIELDS.append((0x11CC8, 0x120E8, {
 0x1C:('Pil_LowPtr',  'position in FirePillarTimes for the lower shot'),
 0x20:('Pil_HighPtr', 'position in FirePillarTimes for the upper shot'),
 0x30:('Pil_LowWait', 'frames to the next lower shot; death timer'),
 0x31:('Pil_HighWait','frames to the next upper shot'),
 0x33:('Pil_Fire',    'bit 1 lower shot due, bit 0 upper shot due'),
 0x34:('Pil_Timer',   'wind-up / after-shot timer'),
 0x35:('Pil_Flick',   'index into FirePillarFlicker'),
 0x36:('Pil_Flick2',  'index used by the upper / double shot (never advanced)'),
 0x37:('Pil_FlickA',  'written from FirePillarFlicker, never read'),
 0x38:('Pil_FlickB',  'written, never read'),
 0x39:('Pil_FlickC',  'written, never read'),
}))
HEADERS[0x11CC8] = HEADERS.get(0x11CC8,'') + """

Behaviour, as coded: a column (size class 8) that cannot be hurt (O_Active $81) while it is
idle. Once on screen and with Arthur within 48 px vertically, two timers from
FirePillarTimes (started at random points) decide when it fires enemy shot type 5 at him
from its lower end (16 px below its centre), its upper end (7 px above), or both. While it
winds up (30 frames) and fires it can be hit (4 hits). Pil_FlickA-C are written during
shots from a table of frame numbers but nothing reads them - a removed effect."""
for a,n,h in [
 (0x11CF6,'FirePillar_Init',"State 0: size 8, face Arthur, 4 HP, random start in the timer script"),
 (0x11D50,'FirePillar_Active',"State 1. O_Step: 0 wait to be on screen, 1 idle, 2 lower shot, 3 upper shot, 4 both"),
 (0x11D70,'FirePillar_WaitSeen',None),
 (0x11D7C,'FirePillar_Idle',"O_Step2: 0 shield up, wait for Arthur's height; 1-2 run the timers; 3 choose"),
 (0x11D9A,'FirePillar_Shield',None),
 (0x11DD8,'FirePillar_LowTimer',None),
 (0x11E00,'FirePillar_HighTimer',None),
 (0x11E28,'FirePillar_Choose',"Shot due: hittable, O_Step = 1 + Pil_Fire"),
 (0x11E3E,'FirePillar_ShootLow',"O_Step2: 0-1 wind up 30 frames, 2 fire, 3 32 frames, 4 10 frames"),
 (0x11E60,'FirePillar_WindUp',None),
 (0x11E6C,'FirePillar_WindUpAnim',None),
 (0x11E82,'FirePillar_FireLow',None),
 (0x11E9A,'FirePillarFlicker',None),
 (0x11EB2,'FirePillar_AfterLow',None),
 (0x11EE8,'FirePillar_ShotEnd',None),
 (0x11EFC,'FirePillar_SpawnLow',"Enemy shot type 5 from 16 px below its centre, towards Arthur"),
 (0x11F32,'FirePillar_SpawnHigh',"Enemy shot type 5 from 7 px above its centre"),
 (0x11F68,'FirePillar_ShootHigh',None),
 (0x11F8A,'FirePillar_FireHigh',None),
 (0x11FA2,'FirePillar_AfterHigh',"(advances Pil_Flick but reads Pil_Flick2)"),
 (0x11FE2,'FirePillar_ShootBoth',None),
 (0x12004,'FirePillar_FireBoth',None),
 (0x12028,'FirePillar_AfterBoth',None),
 (0x12068,'FirePillar_Dying',"State 2: sound 20, EnemyBurst, 63 frames"),
 (0x12098,'FirePillar_Free',"State 3: free the slot (no spawn quota given back)"),
 (0x1209C,'FirePillar_AnimIdle',None), (0x120B2,'FirePillar_AnimFire',None),
 (0x120CD,'FirePillarTimes',"frames between shots (bit 7 = loop): 22, 30, 8, 52, 8, 25, 30, 45, 60, 70, 100, ..."),
]:
    N(a,n,h)
C(0x11D9A,'shield: shots pass through')
C(0x11E2E,'hittable while it shoots')
C(0x11F2A,'enemy shot type 5')

# =====================================================================================
# Enemy projectiles (g_EnemyShots)
# =====================================================================================
HEADERS[0x9C58] = """UpdateEnemyShots - 6 slots x $1C at g_EnemyShots. O_State: 0 start (by type), 1 fly,
2 hit Arthur (set by EnemyShotsVsArthur), 3 free. O_Type = who fired it:
   0 Magician's frog spell     1 Unicorn          2 (unused)        3 Big Man
   4 Woody Pig's bomb          5 fire pillar      6 plant           7 Red Arremer
   8 Petite Devil              9 Dragon's fire   10 Astaroth       11 Satan
Move table and animation per type come from EnemyShotMoves / EnemyShotAnims (O_Dir
selects the entry). Types 4 and 10 stop when they reach the floor."""
for a,n,h in [
 (0x9CAC,'EShot_Start',"State 0: per type"),
 (0x9CEA,'EShot_StartSpell',"Frog spell: size class 3"),
 (0x9CF4,'EShot_Carried',"Woody Pig's bomb while carried (it stays in state 0 until the pig lets go): not\ndrawn or hit; aims along the longer axis towards Arthur"),
 (0x9D4A,'EShot_StartAimed',"Plant: aimed at Arthur in 16 directions"),
 (0x9D54,'EShot_StartAimedAnim',"Red Arremer: aimed at Arthur in 16 directions"),
 (0x9D5E,'EShot_StartSub',"Petite Devil / Astaroth: the move table entry selects a sub-table"),
 (0x9D78,'EShot_StartPlain',None),
 (0x9D88,'EShot_StartDir',"Generic: size 0, move and animation for O_Dir"),
 (0x9D98,'EShot_Tables',"a0 = animation, O_MoveTable = move table for O_Type"),
 (0x9DB6,'EShot_Fly',"State 1: move, animate, remove when far off screen; types 4 and 10 stop at the floor"),
 (0x9DF4,'EShot_Hit',None),
 (0x9DFA,'EShot_Free',None),
 (0x9DFE,'EnemyShotMoves',"word offsets per type to its move table"),
 (0x9EDE,'EnemyShotAnims',"word offsets per type to its animations"),
 (0xA33C,'QueueEnemyShotDraw',"Queue an enemy shot BOB (graphics at $1A298, frame table EnemyShotFrames)"),
]:
    N(a,n,h)
N(0x9002,'EnemyShotFrames',"Frame descriptors for the enemy projectile graphics at $1A298 (track 58):\noffset.w, y-adjust.b, height.b - 35 entries")
N(0x908E,'EffectFrames',"Frame descriptors for the weapon / pickup / effect graphics at $1B4CC (tracks 59-60)")
N(0x9FBC,'QueueExplosionDraw',"A dying enemy's explosion: frames from $1B (EffectFrames) are drawn as a grid of\n16 x 16 tiles - 2 x 2 for size classes below 4, larger grids for 4 and above")
N(0xA1E4,'QueueEnemyDraw',"Queue an enemy for drawing; during the explosion step of dying enemies (and the\nDragon's steps 2 / 5) use QueueExplosionDraw")

# =====================================================================================
# Arthur's shots (g_Shots, 4 slots x $26)
# =====================================================================================
HEADERS[0x91A2] = """ShotTable - Arthur's shots, dispatched on O_Type x 4 + O_State.
O_Type = weapon: 0 torch, 1 lance, 2 axe, 3 cross, 4 dagger; 5 = the pieces of armour that
fly off when Arthur is hit (ArthurHit puts 4 of them in the shot slots). O_State: 0 start, 1 fly, 2 hit / end, 3 free.
  torch  4.19 px/frame for 48 px, then falls in an arc (ShotArcMove) and burns on the ground
         for 2 x 32 frames (a bigger flame, then a smaller one)
  lance  4.19 px/frame for 192 px
  axe    4.19 px/frame for 48 px, then falls in an arc
  cross  4.19 px/frame for 48 px only - but it is not used up when it kills
  dagger 5.63 px/frame for 197 px
State 2 (set by EnemyHitByShot): step 1 deflected (sound 10, 15 frames), step 3 hit an enemy
that survives (sound 12, 8 frames), step 0 gone."""
for a,n,h in [
 (0x920E,'DaggerSpeeds',None),
 (0x921A,'ArmourDebrisSpeeds',"type 5 (armour pieces): diagonal directions at 2.3 px/frame"),
 (0x92A6,'Torch_Start',None), (0x92B4,'Lance_Start',"size class 2"), (0x92C4,'Axe_Start',None),
 (0x92D2,'Cross_Start',None), (0x92E0,'Dagger_Start',None), (0x92EE,'ArmourDebris_Start',None),
 (0x92FA,'Shot_StartCommon',"Animation for the direction, move table, remember the start X, fly"),
 (0x9316,'Torch_Fly',"O_Step: 0 straight, 1 start the fall, 2 fall, 3 big flame, 4 small flame, 5 end"),
 (0x9340,'Shot_StartFall',"vx 2.93, vy 1.01 px/frame"),
 (0x9356,'Torch_Fall',None),
 (0x93A2,'Torch_Burn',"Landed: size class 3 flame for 32 frames"),
 (0x93BE,'Torch_BurnSmall',"then size class 0 for 32 frames"),
 (0x93E2,'Torch_BurnEnd',None),
 (0x93F6,'Lance_Fly',None),
 (0x9410,'Shot_End',None),
 (0x941C,'Axe_Fly',"O_Step: 0 straight, 1 start the fall, 2 fall, 3 end"),
 (0x943A,'Axe_Fall',None),
 (0x9446,'Cross_Fly',"Cross and dagger: straight to their range"),
 (0x9472,'ArmourDebris_Fly',None),
 (0x947A,'Shot_Straight',"Move; next step once ShotRanges[type] px from the start X"),
 (0x94A0,'ShotRanges',"px before the next step: torch 48, lance 192, axe 48, cross 48, dagger 197, armour 38"),
 (0x94A6,'Shot_Hit',"State 2. O_Step: 0 gone, 1-2 deflected, 3-4 hit"),
 (0x94C8,'Shot_Gone',None),
 (0x94D0,'Shot_Deflected',"sound 10, 15 frames"),
 (0x94EE,'Shot_HitWait',None),
 (0x94F8,'Shot_HitEnemy',"sound 12, 8 frames"),
 (0x9516,'Shot_Free',None),
 (0x951A,'Shot_AnimHit',None), (0x9520,'Shot_AnimDeflect',None),
]:
    N(a,n,h)
C(0x96AA,'the cross carries on after a kill (except on Astaroth)')
C(0x96D2,'deflected: the enemy is immune to this weapon or shots pass through it')

# =====================================================================================
# Items (g_Items, 30 slots x $1C): triggers, point pickups, scenery, platforms
# =====================================================================================
HEADERS[0xA444] = """Item handlers by O_Type (placed from LevelItemLists):
  0  touch item. Param 0 and 1 are invisible trigger points: param 0 calls a special
     object (type 1) 100 px ahead - only if Arthur has lost his armour; param 1 calls one
     100 px ahead and 128 px up. Param 2 / 3 are point pickups (sound 28, 200 / 500 points).
  1  shootable scenery (gravestones etc.) - nothing to do here; see ShotsVsScenery
  2  moving platform on a scripted path (ItemPaths / ItemPathScripts)
  3  platform that starts moving once Arthur stands on it, until it is below the level
  4  platform that waits until Arthur reaches X $980, then moves
  5  solid moving block: pushes Arthur sideways and stops him jumping up through it
A platform carries Arthur while he stands on it (its O_Frame byte is used as the rider flag, Itm_Rider, set by ArthurOnPlatform)."""
for a,n,h in [
 (0xA45C,'Item_Touch',"Arthur within 12 px across and 8 px vertically: collect / trigger"),
 (0xA4A8,'Item_TriggerArmour',"Param 0: no armour? call special object type 1 at X + 100"),
 (0xA4E0,'Item_TriggerCall',"Param 1: call special object type 1 (param $13) at X + 100, Y + 128"),
 (0xA51A,'Item_Coin',"Param 2: 200 points"),
 (0xA52A,'Item_MoneyBag',"Param 3: 500 points"),
 (0xA53A,'Item_Scenery',None),
 (0xA53C,'Item_Platform',None),
 (0xA54A,'Item_RidePlatform',None),
 (0xA560,'Item_WaitPlatform',"Waits until Arthur X >= $980"),
 (0xA580,'Item_Block',"Solid block: bump Arthur's head when he jumps up into it (Y - 20); push him out\nsideways when he walks into it; turn him round once"),
 (0xA614,'Item_BlockPush',None),
 (0xA666,'Item_PathStart',"O_Anim = step table, O_MoveTable = script for the type and param"),
 (0xA6B0,'Item_PathScript',"Next (step, frames) pair from the script; bit 7 = loop"),
 (0xA6D2,'Item_PathMove',"Move by the step's (dx, dy); carry Arthur if he is on it"),
 (0xA710,'Item_RideMove',None),
 (0xA72E,'ItemPaths',"per type and param: tables of (dx, dy) steps (8.8)"),
 (0xA7FC,'ItemPathScripts',"per type and param: (step, frames) scripts"),
]:
    N(a,n,h)
C(0xA51A,'sound 28')
C(0xA520,'200 points')
C(0xA530,'500 points')
C(0xA5BA,'head bump: push Arthur 20 px down')
C(0xA60A,'walked into it: turn Arthur round')

# =====================================================================================
# Special objects (g_SpecialObjs, 2 x $20): bonus prizes
# =====================================================================================
HEADERS[0x98FA] = """UpdateSpecialObjs - 2 slots x $20: bonus prizes.
Slot 0 (O_Type 0) is the prize carried by every 6th spawned enemy (UpdateSpawners): it rides
on the enemy (O_MoveTable = the enemy's slot) and drops when the enemy is killed; if the
enemy leaves instead, the prize goes with it. Slot 1 (O_Type 1) is called by an invisible
trigger item and falls from above.
O_State: 0 attach, 1 prize (O_Step 0 ride, 1 fall, 2 reveal, 3 wait to be touched),
2 collected (30 frames), 3 free.
O_Param = what it is: 0 armour, 1-5 weapon (g_Weapon = param - 1), 6-11 the level's
treasure (200 points on level 0, 400 elsewhere), 12 rare treasure (4000), 13-19 points:
200, 500, 800, 1000, 2000, 5000, 10000. Sound 28 when collected (not for weapons)."""
for a,n,h in [
 (0x994C,'Special_Attach',"Type 0: wait for the carrier to become active; type 1: start falling"),
 (0x998A,'Special_Prize',None),
 (0x99AA,'SpecialRideOffsets',"Y offset of the prize on its carrier, per enemy type"),
 (0x99BA,'Special_Ride',"Follow the carrier; it is killed (state 2): fall; it is gone: remove"),
 (0x9A10,'Special_Fall',"Fall (gravity 0.07 px/frame^2, up to 4 px/frame) until it lands"),
 (0x9A50,'Special_Reveal',"10 frames, then show the prize for O_Param"),
 (0x9A8E,'SpecialPrizeSizes',None),
 (0x9AA2,'Special_Wait',"Touched (within 8 px both ways): collect"),
 (0x9AF4,'SpecialCollect',None),
 (0x9B44,'Special_Armour',"armour back on"),
 (0x9B54,'Special_Weapon',"new weapon = param - 1"),
 (0x9B6E,'Special_Treasure',"param 12: 4000; otherwise 200 on level 0, 400 elsewhere"),
 (0x9B9C,'Special_Points',"params 13-19: SpecialPoints"),
 (0x9BB4,'SpecialPoints',"AddScore indices: 200, 500, 800, 1000, 2000, 5000, 10000"),
 (0x9BBC,'Special_Collected',"30 frames"),
 (0x9BD8,'Special_Free',None),
 (0x9BDC,'Special_AnimPot',None),
 (0x9BE0,'Special_AnimPrizes',None),
]:
    N(a,n,h)
C(0x98A8,'scenery hit counter (15 for gravestones)')
C(0x98B4,'counter ran out: start the Magician spawner (slot 7) with its one-entry script')
N(0x9842,'ShotsVsScenery',"Arthur's shots against shootable scenery (item type 1, gravestones): the shot is\nstopped (deflected), and every hit counts down the item's counter (+$1B, 15 at level\nstart). When it runs out, the Magician's spawner is started at the gravestone\n(g_SceneryHitX/Y, 16 px higher).")
