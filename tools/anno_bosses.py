# Detailed annotations of the boss handlers. Executed inside anno_db.py (N, C, V, HEADERS available).

V(0x19, 'g_BigEnemyCount', 'Red Arremer / Satan / Unicorn / Dragon currently engaged (+1 on activation, -1 on removal; never tested)')
VAR_RANGES = [(0x872,16),(0x13,5)]
V(0x10, 'g_BonusEvery', 'counts down from 6: every 6th spawned enemy carries a bonus')
V(0x11, 'g_BonusCycle', '0-6: which kind of bonus the next carrier gets (BonusKinds)')
V(0x12, 'g_BonusRoll', '+21 per treasure bonus; on carry the treasure is the rare kind 12')
V(0x13, 'g_WeaponOdds', '5 accumulators, one per weapon (bonus weapon choice); ends at $17')
N(0xAB5C, 'WeaponOddsTable', 'Per level: word offset to 5 weights (one per weapon) for BonusKinds')
V(0x96, 'g_SceneryHitX', 'where shootable scenery was last hit: spawn point for the Magician (type 7)')
V(0x98, 'g_SceneryHitY', '')
N(0xAAEC, 'BonusKinds', """Kind of bonus for the next carrier, cycling 0-6: treasure, treasure, weapon,
treasure, kind 13, treasure, weapon. Treasure = 6 + level (kind 12 when g_BonusRoll
carries); weapon = 1 + weapon number, picked by adding the level's weights (WeaponOddsTable) to
the five g_WeaponOdds accumulators: the first that carries and is not Arthur's weapon.""")
C(0xAA06, 'quota for this enemy type used up?')
C(0xAA48, 'type 7 (Magician): at the last scenery hit, spawner stops')
C(0xAA62, 'zombies (11): 128 px further right')
C(0xAA86, 'every 6th spawn carries a bonus')
C(0xAAAE, 'special object 0 follows the new enemy')

LEFTOVER_SFX = 'd0 is not used by what follows. [1MB build: PlaySfx here, effect 9 (footstep); the call was removed in 512K]'
LEFTOVER_SFX24 = 'd0 is not used by what follows. [1MB build: PlaySfx here, effect 24; the call was removed in 512K]'

# =====================================================================================
# Unicorn (Cyclops) - type 8. Boss of levels 0 and 1, also appears on level 5.
# =====================================================================================
TYPE_FIELDS.append((0xF5DC, 0x10024, {
 0x1C:('Uni_ChargeX',  'charge target X (Arthur +-16)'),
 0x1E:('Uni_JumpType', 'facing (1 right, 2 left) / jump type index into Unicorn_JumpSpeedX'),
 0x20:('Uni_AnimSet',  'current animation pair (right, left)'),
 0x24:('Uni_ShotPtr',  'position in Unicorn_ShotScript'),
 0x28:('Uni_WalkPtr',  'position in the current Unicorn_WalkScripts entry'),
 0x2C:('Uni_VelY',     'vertical speed while jumping (16.16, up = positive)'),
 0x30:('Uni_Timer',    'fire wind-up / recovery timer; death timer'),
 0x31:('Uni_Aiming',   '1 = in the fire pose, shot pending'),
 0x32:('Uni_Angry',    'set when Uni_AngerTimer runs out: next move is a charge or a jump at Arthur'),
 0x33:('Uni_Approach', 'wanted walk direction to keep its distance from Arthur (0 = happy)'),
 0x34:('Uni_Gravity',  'jump phase: selects the gravity pair in Unicorn_Gravity'),
 0x35:('Uni_Delay',    'start delay, in 16-frame units'),
 0x36:('Uni_JumpNext', '1 = jump instead of walking on the next decision'),
 0x37:('Uni_Variant',  'spawn parameter: 0 normal, 1 / 3 start with a long jump, 4 = 0 after a short delay, 2 = keeps to its arena (level 5)'),
 0x38:('Uni_ShotWait', 'frames until the next shot (from Unicorn_ShotScript)'),
 0x39:('Uni_WalkTime', 'frames left of the current walk-script step'),
 0x3A:('Uni_AngerTimer','frames until Uni_Angry is set (random, Unicorn_AngerDelays)'),
 0x3B:('Uni_Pause',    'pause after landing'),
}))

HEADERS[0xF5DC] = HEADERS.get(0xF5DC,'') + """

Behaviour, as coded:
  * Waits (Uni_Delay x 16 frames) once Arthur is near its level, then walks to a walk
    script, turning back at the edges of its arena (Unicorn_ChooseWalkDir).
  * Fires a shot (enemy shot type 1, straight ahead) whenever Unicorn_ShotScript says so:
    fire pose for 40 frames, shot, 25 frames recovery.
  * Jumps over Arthur's weapons: any of Arthur's shots flying towards it within 56 pixels
    starts a jump (Unicorn_CheckThreats).
  * Keeps its distance: Uni_Approach asks to walk towards Arthur when he is 120+ pixels away
    and away from him when closer than 32 (unicorn on the left) / 56 (on the right).
  * After a random 51-130 frames it gets angry: next it either charges at Arthur
    (Unicorn_Charge) or jumps at him (Unicorn_JumpAt), 50/50 (always the charge for variant 2)."""

for a,n,h in [
 (0xF5F8,'Unicorn_Init',"State 0: set up the slot (10 HP, size class 4, scripts, start delay) then wait\nuntil it is on screen."),
 (0xF69C,'Unicorn_WaitVisible',None),
 (0xF6B3,'Unicorn_ShotScript',"Shot timing script: one byte per shot = frames to wait; bit 7 set = last entry,\nfollowed by a word offset back to the loop point."),
 (0xF6C6,'Unicorn_StartDelays',"Start delay per spawn (x 16 frames), picked with the frame counter"),
 (0xF6CA,'Unicorn_Active',"State 1. Does nothing while Arthur is 128+ pixels above it (variant != 0).\nO_Step: 0 wait, 1 walk, 2 jump, 3 charge, 4 reposition, 5 fire."),
 (0xF708,'Unicorn_Wait',"Step 0: snap onto the floor, then count down Uni_Delay (every 16 frames).\nLevel 5: does not start until Arthur is on its level. Starts at once after a hit (HP 6)."),
 (0xF758,'Unicorn_WalkStep',"Step 1: walk and shoot. Removed if it ends up far off screen."),
 (0xF79E,'Unicorn_ShotTimer',"Count down to the next shot; then take the fire pose for 40 frames and go to step 5"),
 (0xF814,'Unicorn_WalkScripts',"4 walk scripts (word offsets, picked with the frame counter), each a list of\n(direction, frames) pairs; direction 0 stand, 1 right, 2 left; bit 7 = loop (offset follows)"),
 (0xF850,'Unicorn_WalkMove',"Move table for walking: (dx, dy) per direction, 8.8 fixed point (0, +0.53, -0.53)"),
 (0xF85C,'Unicorn_AngerDelays',"8 random delays (frames) before the unicorn gets angry"),
 (0xF864,'Unicorn_WalkStart',"Start walking: pick a walk script and anger delay, face Arthur.\nVariants other than 0 and 2 jump straight away."),
 (0xF8E6,'Unicorn_Walk',"One frame of walking; then work out Uni_Approach from the distance to Arthur\n(only while no scripted walk step is running)."),
 (0xF97C,'Unicorn_ChooseWalkDir',"Keep the unicorn in its arena (world X $1A18-... on level 1, $1D98-$1E48 for\nvariant 2 on level 5, the level's right end otherwise): walk back in for 64 frames\nwhen outside it; otherwise follow the walk script."),
 (0xFA1E,'Unicorn_JumpStep',"Step 2: jump. O_Step2: 0 take off, 1-2 rise, 3 apex, 4 fall, 5 land, 6 pause,\n7 take off towards Arthur."),
 (0xFA4C,'Unicorn_JumpStart',"Take off at 6 px/frame. Jump type (horizontal speed): variants 1/3 jump the long\nway (types 15/16), after Uni_JumpNext a short hop away from Arthur (5/6), otherwise random from\nUnicorn_JumpChoices (straight up or forward). Jumps that would leave the arena become a standing landing."),
 (0xFB3A,'Unicorn_JumpRise',None),
 (0xFB56,'Unicorn_JumpChoices',"Random jump types: 4 for facing left, 4 for facing right"),
 (0xFB5E,'Unicorn_Gravity',"Gravity pairs (acceleration.w, max fall speed.w in px): $5000 (0.31 px/frame^2) up to\n6 px/frame for the main rise and fall, $1900 (0.1) up to 1 near the apex"),
 (0xFB66,'Unicorn_RiseStep',"Y += Uni_VelY, then slow it by the gravity for this phase"),
 (0xFB84,'Unicorn_JumpApproachApex',None),
 (0xFBA0,'Unicorn_JumpApex',None),
 (0xFBAE,'Unicorn_FallStep',"Y -= Uni_VelY, speeding up to the limit for this phase"),
 (0xFBE0,'Unicorn_MoveX',"X += Unicorn_JumpSpeedX[Uni_JumpType] (8.8)"),
 (0xFBFA,'Unicorn_JumpSpeedX',"Horizontal speed per jump type, 8.8: odd = right, even = left, growing with the type"),
 (0xFC1C,'Unicorn_JumpFall',"Fall until there is floor under it"),
 (0xFC34,'Unicorn_JumpLand',"Landed: face Arthur. A pending shot is fired at once; otherwise pause 15 frames."),
 (0xFC96,'Unicorn_LandPause',"After the pause: angry -> walk again from scratch (Unicorn_WalkStart), else carry on walking"),
 (0xFCBC,'Unicorn_JumpAt',"Take off towards Arthur: jump type from the distance ((dx & $70) >> 4)"),
 (0xFD22,'Unicorn_ChargeMove',"Move table for the charge: +-1.8 px/frame"),
 (0xFD2E,'Unicorn_Charge',"Step 3: charge to just past Arthur (his X +-16) with double-speed animation, then walk"),
 (0xFDB6,'Unicorn_Reposition',"Step 4: move the way Uni_Approach asks, still dodging and shooting.\nO_Step2: 0 decide, 1 moving left, 2 moving right. Both usually end within a frame or two,\nand the walk step re-evaluates Uni_Approach every frame, so this nudges it to its distance."),
 (0xFDE6,'Unicorn_RepositionStart',"Moving right: 50% chance (never variant 2) of a short hop away from Arthur instead"),
 (0xFE54,'Unicorn_RepoLeft',"Moving left: back to walking once within 112 pixels of Arthur"),
 (0xFE7C,'Unicorn_RepoRight',"Moving right: back to walking once 96+ pixels from Arthur or past the right of the screen"),
 (0xFEBE,'Unicorn_CheckThreats',"Angry -> charge (step 3) or jump at Arthur (step 2/7), 50/50; variant 2 always charges.\nOtherwise, unless aiming: jump over any of Arthur's 4 shots that is close;\nthen reposition if Uni_Approach asks for it."),
 (0xFF32,'Unicorn_ShotNear',"Shot slot a0 active, on screen, not flying the way the unicorn faces and within\n+-56 pixels horizontally -> d1+1 and start a jump"),
 (0xFF64,'Unicorn_Fire',"Step 5: after the wind-up, spawn enemy shot type 1 at the unicorn moving the way it\nfaces, then walk on (or charge if angry)"),
 (0xFFD6,'Unicorn_Dying',"State 2: sound effect 12, the shared explosion (EnemyExplode), then 63 frames"),
 (0x10008,'Unicorn_Free',"State 3: free the slot. Level 1: the boss is beaten (BossKilled)."),
 (0x10024,'Unicorn_AnimStand',None),
 (0x1003E,'Unicorn_AnimJump',None),
 (0x1004C,'Unicorn_AnimAim',None),
 (0x10066,'Unicorn_AnimJumpAim',None),
 (0x10074,'Unicorn_AnimFire',None),
]:
    N(a,n,h)
for a,t in [
 (0xF620,'variant from the spawn parameter'),(0xF634,'face Arthur: O_Dir = 1 (right) if he is to the right, else 2 (left)'),
 (0xF65C,'10 hits'),(0xF666,'variant 4: becomes variant 0, delay 10'),(0xF66C,'variant 3: becomes variant 2, delay 10'),
 (0xF680,'otherwise a delay of 2-4 x 16 frames'),
 (0xF6D4,'Arthur 128+ pixels above it?'),
 (0xF70E,'first frame: snap onto the floor'),
 (0xF718,'level 5: wait until Arthur is no more than 16 pixels below it'),
 (0xF72E,'already hit (6 HP left)? start at once'),
 (0xF742,'every 16 frames'),
 (0xF748,'one more big enemy engaged'),
 (0xF758,'more than 256 px left / 768 right of the camera, or 160 below / 416 above it: remove'),
 (0xF7B0,'bit 7: last entry, loop'),
 (0xF7DE,'fire pose for 40 frames'),
 (0xF7FE,'25 frames of recovery after the shot'),
 (0xF8BC,'random anger delay'),
 (0xF8CA,'variants 1 and 3 start with a jump'),
 (0xF8EA,'O_Dir 0 = stand still'),
 (0xF8FC,LEFTOVER_SFX24),
 (0xF91E,'anger timer'),
 (0xF92E,'scripted walk running: no approach decision'),
 (0xF944,'Arthur to the right: <= 32 px -> walk away (2), 120+ -> walk to him (1)'),
 (0xF962,'Arthur to the left: 120+ px -> walk to him (2), <= 56 -> walk away (1)'),
 (0xF9A0,'walk back for 64 frames'),
 (0xF9FC,'next (direction, frames) pair'),
 (0xFA4C,'take-off speed 6 px/frame'),
 (0xFA82,'variants 1/3: one long jump, then behave as variant 0/2'),
 (0xFAD2,'level 5 / level 1: do not jump out of the arena'),
 (0xFB44,'until the upward speed is below 1 px/frame'),
 (0xFB8E,'until it is below 0.1 px/frame'),
 (0xFC28,'floor under it?'),
 (0xFCF8,'(d0 already holds X - ArthurX from the compare above)'),
 (0xFD74,LEFTOVER_SFX),
 (0xFDD0,LEFTOVER_SFX),
 (0xFF06,'variant 2 always charges'),
 (0xFF24,'jump at Arthur'),
 (0xFF3E,'shot flying the way the unicorn faces (away from it)? ignore'),
 (0xFF72,'shot starts at the unicorn'),
 (0xFF98,'enemy shot type 1 (unicorn fireball)'),
 (0xFFEA,'sound effect 12'),
 (0x10008,'give the unicorn spawn quota back'),
 (0x10012,'one big enemy fewer'),
 (0x10018,'on level 5 it is not the boss'),
]:
    C(a,t)
N(0x1211A,'EnemyExplode',"Shared death explosion (used by Satan, Unicorn and Dragon): 3 frames at size\nclass 3, then 18 at size 4, then the caller's next step. O_Dir is used as the timer.")

# =====================================================================================
# Satan - type 6. Boss of level 4, two on level 5.
# =====================================================================================
TYPE_FIELDS.append((0xEE1C, 0xF41E, {
 0x1C:('Sat_TargetX',  'Arthur X when the dive started'),
 0x1E:('Sat_ArcDepth', 'current depth of the dive below Sat_ArcBaseY (word)'),
 0x20:('Sat_FlySpeed', 'horizontal speed pair for the dive (left, right)'),
 0x24:('Sat_ArcBaseY', 'Y at the start of the dive (word)'),
 0x26:('Sat_ArcHeight','half the depth of the dive'),
 0x27:('Sat_ArcPhase', '0-255 through the dive (sine table index)'),
 0x30:('Sat_Returning','1 = off screen, flying back in'),
 0x31:('Sat_Hold',     'cleared at start and never set: would make it only count down'),
 0x32:('Sat_WakeDelay','x 64 frames before a parameter-1 Satan wakes up'),
 0x33:('Sat_Timer',    'hovering: frames left (180); diving: phase step per frame'),
 0x34:('Sat_FirePhase','0 shooting, 1 guarding (shots pass through), 2 back to shooting'),
 0x35:('Sat_GuardTime','frames of guarding (30)'),
 0x36:('Sat_FireTime', 'frames of shooting before it guards (SatanFireTimes)'),
 0x37:('Sat_Swoop',    '1 = level with Arthur: fly across, then climb out of the dive'),
 0x38:('Sat_Drift',    'hover drift: 0 right, 1 left, 2 up, 3 down (new every 128 frames)'),
 0x39:('Sat_ShotWait', 'frames to the next shot (SatanShotGaps)'),
 0x3A:('Sat_ReturnDir','which way to fly back on screen: 0 right, 1 left, 2 up, 3 down'),
 0x3B:('Sat_ReturnTime','frames of flying back'),
}))
HEADERS[0xEE1C] = HEADERS.get(0xEE1C,'') + """

Behaviour, as coded:
  * Sleeps until it is in view (parameter 1: for a further 6 x 64 frames, during which
    it can be hit; 3 hits wake it, but its HP is then reset to 4).
  * Hovers for 180 frames, drifting slowly (one of 4 directions, re-chosen every
    128 frames; always down when Arthur is 64+ pixels below), turning to face Arthur.
    While hovering it fires (enemy shot type 11, aimed in 16 directions) every 45-65
    frames, and every 47-90 frames folds its wings for 30 frames, when shots pass
    through it (O_Active bit 7).
  * Then attacks: from above, a U-shaped dive (sine curve) down to around Arthur's
    height and up again while flying across at 2-2.25 px/frame; level with Arthur, it
    flies across and climbs out of the second half of the dive; from below, it flies
    straight at him at 3.5 px/frame. Then it hovers again.
  * If it leaves the screen it flies back in for 16-31 frames, then attacks again.
Bug: the dying state waits for its timer to reach 0 the wrong way round (beq instead
of bne), so the 63-frame pause after the explosion is skipped."""
for a,n,h in [
 (0xEE38,'Satan_Init',"State 0: 4 HP, size class 4, face Arthur, then sleep until in view"),
 (0xEE76,'Satan_Sleep',"Shots pass through while it sleeps ($81). Wake when inside the camera window\n(0-256, 0-240); parameter 1 waits a further Sat_WakeDelay x 64 frames."),
 (0xEED4,'Satan_Active',"State 1. O_Step 0 = hover (O_Step2 0 count, 1 set up, 2 face, 3 hover),\nO_Step 1 = attack (O_Step2 0 aim, 1 dive, 2 fly to the dive point, 3 fly straight)."),
 (0xEEFA,'Satan_Engage',None),
 (0xEF04,'Satan_HoverStart',"180 frames of hovering"),
 (0xEF3A,'Satan_Face',None),
 (0xEF46,'Satan_Hover',None),
 (0xEFD8,'Satan_DriftSpeed',"Hover drift (8.8): +-0.44 px/frame horizontally (0, 1), vertically (2, 3)"),
 (0xEFE0,'Satan_FireCycle',"Shoot every Sat_ShotWait frames for Sat_FireTime frames, then guard for 30 frames\n(shots pass through), then start again"),
 (0xF054,'Satan_RandomFireTime',None),
 (0xF062,'Satan_RandomShotGap',None),
 (0xF070,'SatanFireTimes',"47, 60, 90, 47 frames"),
 (0xF074,'SatanShotGaps',"65, 60, 50, 45 frames"),
 (0xF078,'Satan_DiveAnim',"Dive animation for its 16-way direction (facing left for directions 5-12)"),
 (0xF094,'Satan_SetAnim',None),
 (0xF098,'Satan_MoveX',"X += word table a0[O_Dir] (8.8)"),
 (0xF0AE,'Satan_MoveY',"Y += word table a0[d0] (8.8)"),
 (0xF0C0,'Satan_Attack',None),
 (0xF0F4,'Satan_Aim',"Choose the attack. Level with Arthur (direction 0 or 8): swoop. Below him: fly\nstraight at him. Above him: dive to his Y +-24/32 (random), with the phase step\nworked out from the height so a deeper dive takes longer."),
 (0xF1C2,'SatanDiveSpeed',"Horizontal dive speed, 8.8: first half -2/+2, second half -2.25/+2.25 (0 = left)"),
 (0xF1CA,'SatanDiveOffsets',"Random Y offset from Arthur for the bottom of the dive: -24, +24, +32, +24"),
 (0xF1DA,'SatanFlyTable',"16-way flight (dx, dy) at 3.5 px/frame, direction 0 = right, 4 = down"),
 (0xF21A,'Satan_Dive',"Y = Sat_ArcBaseY - Sat_ArcHeight x 2 x sin(phase); ends when the phase wraps.\nFalls through into Satan_FlyToDive, so it moves sideways twice per frame."),
 (0xF27C,'Satan_FlyToDive',"Fly sideways until within 16 px of Sat_TargetX, then dive"),
 (0xF2A2,'Satan_FlyStraight',"Fly in its 16-way direction until it leaves the screen"),
 (0xF2B0,'Satan_Shoot',"Enemy shot type 11 aimed at Arthur (16 directions)"),
 (0xF2E2,'Satan_KeepAboveGround',"Near the bottom of the level (camera Y <= 46): keep Y >= 65 - camera Y"),
 (0xF2FC,'Satan_KeepOnScreen',"Off screen (32 px left, 32 right, below or above the camera): fly back in for\n16-31 frames, then attack again"),
 (0xF382,'Satan_MoveDir',"d0 < 2: move X, else move Y, from word table a0"),
 (0xF39E,'SatanReturnTimes',"31, 21, 26, 16 frames"),
 (0xF3A2,'SatanReturnSpeed',"+3, -3 px/frame in X; +4, -4 in Y"),
 (0xF3AA,'Satan_Dying',"State 2: sound 12, EnemyExplode, then (should) wait 63 frames"),
 (0xF3DC,'Satan_Free',"State 3: free the slot, BossKilled, give the spawn quota back"),
 (0xF3F2,'Satan_AnimHover',None), (0xF40A,'Satan_AnimDive',None), (0xF40E,'Satan_AnimReturnL',None),
 (0xF412,'Satan_AnimReturnR',None), (0xF416,'Satan_AnimGuard',None),
]:
    N(a,n,h)
for a,t in [
 (0xEE52,'O_Dir 0 if Arthur is to the right, 1 if to the left'),
 (0xEE76,'active, shots pass through'),
 (0xEEA0,'parameter 1 is hittable while it waits: down to 1 HP wakes it at once'),
 (0xEEA8,'every 64 frames'),
 (0xEEBA,'4 hits (damage taken while waiting is forgotten)'),
 (0xEF0E,'guard 30 frames'),
 (0xEF5A,'turn round when Arthur passes it'),
 (0xEF9A,'every 128 frames pick a new drift'),
 (0xEFA6,'Arthur 64+ px below: drift down'),
 (0xEFEC,'shot gap'),
 (0xF018,'guarding: shots pass through'),
 (0xF026,'hittable again'),
 (0xF0FA,'directions 0 / 8: level with Arthur'),
 (0xF104,'below Arthur?'),
 (0xF140,'d0 = |dy| / 2'),
 (0xF14A,'phase step = 127 / d0: the whole dive takes about |dy| frames'),
 (0xF160,'O_Dir 0 = fly left, 1 = fly right'),
 (0xF1A2,'swoop: start at the bottom of a 96-pixel dive'),
 (0xF224,'second half of the dive: 2.25 px/frame'),
 (0xF238,'sine table (shared with the Blue Killer)'),
 (0xF268,'phase wrapped: hover again'),
 (0xF2DA,'enemy shot type 11'),
 (0xF3CE,'BUG: beq should be bne - goes to state 3 after one frame'),
]:
    C(a,t)

# =====================================================================================
# Dragon - type 12. Boss of levels 2 and 3, also on level 5. A chain of 9 enemy slots.
# =====================================================================================
TYPE_FIELDS.append((0x10CCE, 0x11640, {
 0x1C:('Drg_PathPtr',  'head: position in the current path script ((frames, direction) pairs)'),
 0x20:('Drg_HomeY',    'head: start Y (word); level 5 keeps within 256 px of it'),
 0x24:('Drg_Next',     'next segment towards the tail (long, 0 = this is the tail)'),
 0x28:('Drg_Prev',     'previous segment towards the head (long)'),
 0x30:('Drg_Facing',   'head: 0 right, 1 left'),
 0x31:('Drg_PathTime', 'head: frames left on the current path step; also the death timer'),
 0x32:('Drg_Aggro',    'head: attack when (random & 15) <= this (2: 3 in 16)'),
 0x33:('Drg_Firing',   'head: 1 while the mouth is open after a shot'),
 0x34:('Drg_Pending',  'segment: a new direction is waiting in Drg_NewDir; head: mouth-open timer'),
 0x35:('Drg_Frozen',   '1 = segment does not move (while the dragon waits to attack)'),
 0x36:('Drg_Part',     '0 head, 1 body, 2 tail'),
 0x37:('Drg_Index',    'position in the chain: 8 head ... 0 tail'),
 0x38:('Drg_NewDir',   'direction to take when Drg_Delay runs out'),
 0x39:('Drg_Delay',    'frames until Drg_NewDir is taken'),
 0x3A:('Drg_Wait',     'head: x 16 frames before the attack starts'),
 0x3B:('Drg_HeadDead', '1 = the head was killed: boss handling on removal'),
}))
HEADERS[0x10CCE] = HEADERS.get(0x10CCE,'') + """

Behaviour, as coded:
  * The placed head (parameter 0) builds the body: 7 segments (parameter 1) and a tail
    (parameter 2) in free enemy slots, linked through Drg_Next / Drg_Prev.
  * The head steers along path scripts of (frames, direction) pairs in 16 directions
    at 2 px/frame. Each direction change is handed down the chain with a 6-frame
    delay per segment (7 for the tail), which makes the body follow the head's path.
  * Entrance: a short S-curve, then it waits frozen until it is on screen and Arthur
    is no more than 32 px below it, for a further 2-5 x 16 frames, then attacks.
  * Attack: when a path step ends it may (3 in 16) dive at Arthur if he is 24+ px in
    front of it; otherwise it turns round once it is 94+ px past him (turn paths for the
    upper and lower half of the screen), and climbs or descends towards his height.
  * Every 32 frames, if Arthur is within 72 px vertically, it breathes fire (enemy shot
    type 9) and opens its mouth for 10 frames.
  * Hits: each hit on any segment scores 200. Hitting the tail kills it; hitting a body
    segment kills the tail instead, so the dragon shortens from the tail. The head takes
    6 hits; killing it kills every segment, scores a further 1000 and ends the boss.
  * Off levels 2-3 it is removed when it gets far off screen."""
for a,n,h in [
 (0x10CEA,'Dragon_Init',"State 0: by part (O_Param): head / body segment / tail"),
 (0x10D02,'Dragon_InitHead',None),
 (0x10D1A,'Dragon_HeadSetup',"Face Arthur, size 3, 6 HP, 16-way move table, start the entrance path"),
 (0x10D96,'Dragon_BuildBody',"Allocate 7 body segments and the tail behind the head, each linked to the one\nbefore it (14 px apart, the first 20 px). Tries again next frame if the table is full."),
 (0x10E6C,'Dragon_BuildExit',None),
 (0x10E6E,'Dragon_NumberChain',"Drg_Index: 8 for the head down to 0 for the tail"),
 (0x10E92,'Dragon_InitBody',"Body segment: size 1, 1 HP, Drg_Part 1"),
 (0x10EEC,'Dragon_InitTail',"Tail: size 0, 1 HP, Drg_Part 2"),
 (0x10F46,'DragonEntrancePath',"(frames, direction) pairs, 0 ends"),
 (0x10F54,'DragonMoveTable',"16-way (dx, dy) at 2 px/frame (8.8), 0 = right, 4 = down"),
 (0x10F94,'Dragon_Active',"State 1: head or segment; then remove it when far off screen (not on levels 2-3)"),
 (0x10FE6,'Dragon_Head',"O_Step 0 = entrance (O_Step2 0 start, 1 path, 2 pick wait, 3 wait to be seen,\n4 wait for Arthur), O_Step 1 = attack."),
 (0x1100E,'Dragon_EntranceStart',None),
 (0x1102A,'Dragon_EntrancePath',"Follow the entrance path, handing each new direction to the next segment.\nAt its end: freeze every segment and load the patrol path."),
 (0x110A2,'DragonWaitTimes',"x 16 frames: 3, 2, 3, 2 (level 5: 5, 2, 5, 4)"),
 (0x110AA,'Dragon_PickWait',None),
 (0x110D0,'Dragon_WaitSeen',None),
 (0x110DC,'Dragon_WaitArthur',"Count down Drg_Wait (every 16 frames) while Arthur is no more than 32 px below;\nthen unfreeze the chain and attack"),
 (0x11120,'Dragon_Attack',"Flap every 128 frames, steer, breathe fire, move"),
 (0x11158,'Dragon_Steer',"When the path step ends: maybe dive at Arthur, turn round, or climb / descend\ntowards his height (level 5: stay near Drg_HomeY)"),
 (0x11186,'Dragon_DiveAtArthur',"Head for Arthur (not straight down) for 40 frames, 18 if it is in the bottom 96 px of the screen"),
 (0x111BE,'Dragon_TurnCheck',None),
 (0x111FC,'Dragon_Turn',"Turn round: path for the upper or lower half of the screen, flip Drg_Facing"),
 (0x1123E,'Dragon_NextPathStep',"Next (frames, direction) pair; bit 7 = loop (offset follows)"),
 (0x11250,'Dragon_SetPathStep',"Take a (frames, direction) step and hand the direction to the next segment\n(10-frame delay)"),
 (0x11280,'Dragon_SeekHeight',"160+ px above Arthur: descend; below him: climb; else carry on (36-frame steps)"),
 (0x11302,'DragonDescend',"(36 frames, down-right) / (36, down-left)"),
 (0x11306,'DragonClimb',"(36 frames, up-right) / (36, up-left)"),
 (0x1130A,'Dragon_Segment',"Body / tail: unless frozen, take the pending direction and move"),
 (0x11316,'Dragon_PassDirection',"When Drg_Delay runs out take Drg_NewDir and hand it to the next segment\n(6 frames later, 7 for the tail)"),
 (0x11352,'Dragon_Breathe',"Every 32 frames, if Arthur is within 72 px vertically: fire (enemy shot type 9)\nfrom the mouth, mouth open for 10 frames"),
 (0x11408,'DragonPatrolPath',None),
 (0x114B2,'DragonTurnRight',"Turn paths when facing right: upper / lower half of the screen"),
 (0x114D0,'DragonTurnLeft',"Turn paths when facing left: upper / lower half of the screen"),
 (0x114EE,'Dragon_Dying',"State 2. O_Step: 0 decide, 1 head: sound 12, 2 explode, 3 wait then +1000,\n4 segment: sound 20, 5 explode, 6 wait"),
 (0x11516,'Dragon_HitSegment',"Head: every segment dies with it. Tail: unlink it. Body segment: it lives on and\nthe tail dies instead."),
 (0x11596,'Dragon_HeadDies',None),
 (0x115B2,'Dragon_HeadWait',None),
 (0x115C6,'Dragon_SegmentDies',None),
 (0x115E0,'Dragon_SegmentWait',None),
 (0x115EE,'Dragon_Free',"State 3: free the slot; if it was the head (not on level 5): BossKilled"),
 (0x1160C,'Dragon_AnimFly',None), (0x11610,'Dragon_AnimFlap',None), (0x11628,'Dragon_AnimFire',None),
 (0x11638,'Dragon_AnimBody',None), (0x1163C,'Dragon_AnimTail',None),
]:
    N(a,n,h)
for a,t in [
 (0x10D30,'Arthur to the left: direction 8, facing left'),
 (0x10D6E,'attack chance 3 in 16'),
 (0x10DB8,'first segment: 20 px behind the head, 3 px lower'),
 (0x10E08,'link back to the previous segment'),
 (0x10FA2,'levels 2 and 3: never removed'),
 (0x11074,'patrol path'),
 (0x110E4,'Arthur more than 32 px below it: wait'),
 (0x11106,'one more big enemy engaged'),
 (0x11160,'level 5: never dives'),
 (0x11168,'3 in 16 chance to dive'),
 (0x11178,'facing left: Arthur must be 24+ px to the left'),
 (0x1118A,'not straight down'),
 (0x111DA,'past the right end of the level, or 94+ px past Arthur: turn'),
 (0x11296,'more than 160 px above him?'),
 (0x112B4,'level 5: more than 256 px from its start height, or 94+ px from Arthur: head back'),
 (0x1137C,'d0 not used by FindFreeEnemyShot'),
 (0x113A8,'shot direction = facing'),
 (0x113E0,'enemy shot type 9 (dragon fire)'),
 (0x1151E,'the head?'),
 (0x11524,'a body segment: find the tail'),
 (0x1152E,'kill the tail instead (O_Active 2)'),
 (0x11530,'and this segment carries on'),
 (0x1154A,'unlink the dying segment: the one before it becomes the tail'),
 (0x1155E,'state 2, step 4: segment death'),
 (0x11574,'every segment: state 2 step 4'),
 (0x115BA,'+1000 for the head'),
 (0x115F0,'only the head counts for the boss'),
]:
    C(a,t)

# =====================================================================================
# Astaroth - type 13. Final boss (level 6). Only the cross hurts it.
# =====================================================================================
TYPE_FIELDS.append((0x11640, 0x119A6, {
 0x1C:('Ast_ArenaL',  'left end of its walk (camera X + 96 when it woke)'),
 0x1E:('Ast_ArenaR',  'right end (camera X + 224)'),
 0x20:('Ast_WalkTime','frames to walk before turning (word, 0-1023)'),
 0x22:('Ast_StandIn', 'frames until the stand-and-fire phase (word, 256-767)'),
 0x24:('Ast_StandTime','length of the stand-and-fire phase (word, 64-191)'),
 0x30:('Ast_Facing',  '0 Arthur to the right, 1 to the left'),
 0x31:('Ast_Turning', '1 = between walks'),
 0x32:('Ast_Standing','1 = stand-and-fire phase (see the bug note)'),
 0x33:('Ast_HighShot','1 = next shot from the upper firing point; death timer'),
 0x34:('Ast_ShotWait','frames to the next shot (AstarothShotGaps)'),
 0x37:('Ast_TurnWait','set to 143-190 before turning, but only tested once'),
 0x38:('Ast_Far',     '1 = Arthur more than 80 px away'),
}))
HEADERS[0x11640] = HEADERS.get(0x11640,'') + """

Behaviour, as coded:
  * Waits until on screen, then walks to and fro in a 128-pixel arena (camera X + 96
    to + 224), at a random 0.18 or 0.41 px/frame, turning at the ends and after a
    random 0-1023 frames, always facing Arthur.
  * Fires enemy shot type 10 the way it faces, from a lower (Y-5) or upper (Y+12)
    point, every 70-180 frames (AstarothShotGaps). While Arthur is within 80 px the shot
    timer runs at a quarter of the speed and shots come from the lower point; further
    away they come from whichever point was chosen last.
  * A stand-and-fire phase (every 256-767 frames, faster shots from AstarothFastGaps)
    is coded, but the branch that should keep it going is the wrong way round: the
    phase ends in the same frame it starts.
  * 10 hits, by the cross only (EnemyVulnerability)."""
for a,n,h in [
 (0x1165C,'Astaroth_Init',"State 0: size 6, 10 HP, then wait to be on screen and fix the arena"),
 (0x1169C,'Astaroth_Wake',None),
 (0x116C4,'Astaroth_Walk',"Walk with its move table; stop and turn at the arena ends"),
 (0x11700,'Astaroth_Active',"State 1. O_Step 0 start a walk, 1 walk, 2 turn"),
 (0x11718,'Astaroth_WalkStart',None),
 (0x11738,'Astaroth_Walking',None),
 (0x11772,'Astaroth_Turn',"New random speed, turn round, walk again. (Ast_TurnWait is decremented once\nand only ends the step if it reaches 0, which it never does.)"),
 (0x11786,'Astaroth_RandomSpeed',None),
 (0x1179C,'AstarothSpeedPick',"Random choice of move table: 0 slow, 8 fast"),
 (0x117AC,'AstarothMoveTables',"(dx, dy) 8.8 for O_Dir 0 right / 1 left: +-0.18 (slow), +-0.41 (fast)"),
 (0x117BC,'Astaroth_Think',"Face Arthur, run the stand phase timer, and shoot"),
 (0x117DA,'Astaroth_NextShotTime',None),
 (0x117F8,'AstarothFastGaps',"Shot gaps in the stand phase: 30, 50, 80, 20, 60, 15, 25, 40 frames"),
 (0x11800,'AstarothShotGaps',"Shot gaps: 100, 150, 180, 160, 70, 150, 115, 80 frames"),
 (0x11808,'Astaroth_NextStand',"Ast_StandIn = 256-767 frames"),
 (0x11820,'Astaroth_StandPhase',None),
 (0x1187A,'Astaroth_ShotTimer',None),
 (0x1188A,'Astaroth_CheckFar',None),
 (0x118A8,'Astaroth_FaceArthur',None),
 (0x118C4,'Astaroth_SetAnim',"Animation for its facing (walking / standing)"),
 (0x118E2,'Astaroth_Near',"Arthur within 80 px: 1 frame in 4 runs the shot timer (lower point); the others\nonly select the upper point"),
 (0x11902,'Astaroth_Shoot',"Enemy shot type 10 the way it faces: lower point (X+-4, Y-5) or upper (X-+10, Y+12)"),
 (0x11970,'Astaroth_Dying',"State 2: the large explosion, then 63 frames"),
 (0x1199E,'Astaroth_Free',"State 3: free the slot - BossKilled starts the ending"),
 (0x119A6,'Astaroth_Anims',None),
 (0x1216A,'EnemyExplodeLarge',"As EnemyExplode, ending at size class 6 (Astaroth)"),
]:
    N(a,n,h)
for a,t in [
 (0x116A2,'arena: camera X + 96 ... + 224'),
 (0x116D0,LEFTOVER_SFX),
 (0x11756,'143-190 frames'),
 (0x1177A,'turn round'),
 (0x1182C,'stand-and-fire phase starts'),
 (0x11846,'shoot at once'),
 (0x11858,'BUG: bne should be beq - the phase ends here on its first frame'),
 (0x11896,'more than 80 px away?'),
 (0x11922,'enemy shot type 10'),
 (0x11984,'[1MB build: PlayMusic tune 9 (final boss beaten) here; the call was removed in 512K]'),
]:
    C(a,t)

N(0x120E8,'EnemyBurst',"Shared death burst: 36 frames at size class 3, then the caller's next step\n(Woody Pig, Petite Devil, Flying Knight, Red Arremer, Big Man, Dragon segments, plant). O_Dir is used as the timer.")
N(0x121BA,'EnemyDieFacing',"Shared death animation facing Arthur: 18 frames at size class 3, then the caller's\nnext step (Crow, Blue Killer, Magician, Skeleton, Zombie)")

# =====================================================================================
# Red Arremer - type 5. The red gargoyle, on levels 0 and 2-5 (and from spawners).
# =====================================================================================
TYPE_FIELDS.append((0xE1FA, 0xEE1C, {
 0x1C:('RA_CentreX',  'swoop: Arthur X at the start (word); blink timer in mode 2'),
 0x1E:('RA_BaseY',    'Y the flight curves are measured from (word); perch timer'),
 0x20:('RA_WalkPtr',  'position in RedArremerWalkScript'),
 0x24:('RA_ShotPtr',  'position in RedArremerShotTimes'),
 0x28:('RA_SwoopPtr', 'position in RedArremerSwoopTimes'),
 0x2C:('RA_FlyPtr',   'position in RedArremerTakeOffTimes'),
 0x30:('RA_RadiusX',  'swoop: horizontal radius; death timer'),
 0x31:('RA_Rage',     'aggression level: 0 at first, 1 after its rage (faster tables)'),
 0x32:('RA_ShotTime', 'frames to the next shot; wind-up timer'),
 0x33:('RA_SwoopTime','frames to the next swoop at Arthur'),
 0x34:('RA_Phase',    'flight: sine index; walking: x 8 frames to the next take-off'),
 0x35:('RA_RageTime', 'x 32 frames of walking before it rages (from 50)'),
 0x36:('RA_RadiusY',  'height of the current flight curve'),
 0x37:('RA_Return',   'step to go back to after a shot'),
 0x38:('RA_Temp',     'distance to Arthur / dodge height / glide frames'),
 0x39:('RA_ArthurLeft','1 = Arthur is to its left'),
 0x3A:('RA_WalkDir',  'walk / flight direction (negative = stand)'),
 0x3B:('RA_WalkTime', 'frames left of the walk step'),
}))
HEADERS[0xE1FA] = HEADERS.get(0xE1FA,'') + """

Behaviour, as coded. O_Param: bits 0-1 = start mode (1 perched, 2 blink in, 0/3 at
once), bits 2+ = starting aggression.
  * Perched (mode 1): crouches until Arthur comes within 96 px across and 48 px up or
    down, or it is shot at, then wakes after 16 frames.
  * On the ground (O_Step 0) it walks to RedArremerWalkScript, and four timers decide
    what it does next: shoot (enemy shot type 7) on RedArremerShotTimes, swoop at
    Arthur on RedArremerSwoopTimes, take off and hover on RedArremerTakeOffTimes (x 8
    frames), and - once only - rage after 50 x 32 frames: it flashes for 76 frames,
    then uses the faster tables (RA_Rage 1).
  * It glides away when Arthur is within 48 px, and towards him when he is 112+ px away.
  * Dodging: when one of Arthur's shots is flying at it at its height (and Arthur is
    84+ px away) it jumps up out of the way and hovers.
  * Swoop: from above, an elliptical dive onto the spot where Arthur stood, then up and
    away; from level or below, a fast flight past him.
  * Flying states use size class 9, standing 3. Removed when far above or below the
    camera.
Mode 2 (used when a Blue Killer turns into a Red Arremer) counts $F0 down by $61 a frame
and waits for exactly 0, twice, which takes 2 x 26,352 frames (about 17 minutes) during
which it blinks and shots pass through it - presumably a bug. The placed Red Arremers use
mode 1."""
for a,n,h in [
 (0xE216,'RedArremer_Init',"State 0. O_Step 0 decode O_Param, 1 perched, 2 blink in, 3 set up"),
 (0xE232,'RedArremer_Decode',None),
 (0xE256,'RedArremer_Perched',None),
 (0xE26E,'RedArremer_PerchStart',None),
 (0xE28E,'RedArremer_PerchWait',"Wake when Arthur is within +-96 px across and +-48 px vertically, or when hit\n(EnemyHitByShot sets O_Param)"),
 (0xE2BE,'RedArremer_PerchWake',"16 frames, then set up"),
 (0xE2D0,'RedArremer_BlinkIn',"Mode 2 (a Blue Killer that has turned): shots pass through (O_Active 2) and it\nblinks until RA_CentreX reaches 0, twice"),
 (0xE2F0,'RedArremer_BlinkStart',None),
 (0xE2FE,'RedArremer_Blink',"Blink every 16 frames; RA_CentreX -= $61 until it is exactly 0 (26,352 frames)"),
 (0xE328,'RedArremer_BlinkSize',None),
 (0xE342,'RedArremer_BlinkDone',None),
 (0xE352,'RedArremerWalkScript',"(direction word, frames) pairs; direction -1 = stand; 0 = loop (offset follows)"),
 (0xE377,'RedArremerShotTimes',"frames between shots: 90, 100, 220, 130, 160, 180, 200, 120 (0 = loop)"),
 (0xE383,'RedArremerSwoopTimes',"frames between swoops: 72, 136, 85, 92, 108, 144, 70, 49"),
 (0xE38F,'RedArremerTakeOffTimes',"x 8 frames between take-offs: 10, 20, 30, 40, 50, 60"),
 (0xE398,'RedArremer_Setup',"3 HP, size 3, face Arthur, start the four scripts, rage in 50 x 32 frames"),
 (0xE406,'RedArremer_Active',"State 1. O_Step: 0 walk, 1 fly, 2 shoot, 3 glide, 4 rage, 5 dodge / hover, 6 swoop.\nThen the hit flinch, and removal when it is far above or below the camera."),
 (0xE44C,'RedArremerWalkMove',"walking: +-0.8 px/frame"),
 (0xE450,'RedArremer_Walk',"Step 0: walk, and check the shot, swoop, take-off, distance, dodge and rage timers"),
 (0xE474,'RedArremer_WalkStart',None),
 (0xE4A0,'RedArremer_Walking',"Walk; if there is no floor under it any more, fly"),
 (0xE4BE,'RedArremer_Fly',"Step 1: O_Step2 0 take off, 1 rise, 2 fly to Arthur, 3 fly past him, 4 hover,\n5 come down, 6 drop. Shoots and swoops while flying."),
 (0xE4FC,'RedArremerFlySpeed',"+-1.75 px/frame (calm), +-2.0 (after its rage)"),
 (0xE504,'RedArremerFlyHeights',"Random heights of the flight curve: 64, 72, 84, 68, 76, 56, 80, 88"),
 (0xE50C,'RedArremer_TakeOff',None),
 (0xE55E,'RedArremer_Rise',"Rise along the sine curve (phase += 8 up to $A0)"),
 (0xE566,'RedArremer_FlyToArthur',"Fly on until it is over Arthur, then turn"),
 (0xE5A8,'RedArremer_FlyPast',"Fly until 80+ px past him"),
 (0xE5CA,'RedArremer_Hover',"5 frames"),
 (0xE5DE,'RedArremer_Descend',"Come down along the curve; land if there is floor, else drop"),
 (0xE5EA,'RedArremer_Drop',"Fall 4 px/frame until it lands, then walk"),
 (0xE5F6,'RedArremer_Shoot',"Step 2: wind up 6 frames, fire enemy shot type 7, 6 frames, then go back"),
 (0xE612,'RedArremer_ShootStart',None),
 (0xE630,'RedArremer_WindUp',None),
 (0xE63E,'RedArremer_Fire',None),
 (0xE672,'RedArremer_ShootEnd',"Next shot time; back to the step it came from (RedArremerResume)"),
 (0xE698,'RedArremerResume',"(step, step2) to resume after a shot, by the step it came from"),
 (0xE6A6,'RedArremer_Glide',"Step 3: glide (no height change) towards Arthur if he is 80+ px away, else away"),
 (0xE6BA,'RedArremer_GlideStart',None),
 (0xE70C,'RedArremer_Gliding',None),
 (0xE724,'RedArremerGlideTimes',"frames: 15, 12, 20, 25, 18, 8, 27, 7"),
 (0xE72C,'RedArremerGlideSpeed',"+-2.13 px/frame (calm), +-2.25 (raging)"),
 (0xE734,'RedArremer_Rage',"Step 4 (once): O_Active 2 so shots do not register, 76 frames, then RA_Rage + 1"),
 (0xE74C,'RedArremer_RageStart',None),
 (0xE75A,'RedArremer_Rage1',"9 x 4 frames (a removed effect left a NOP here)"),
 (0xE786,'RedArremer_Rage2',"10 x 4 frames"),
 (0xE7B2,'RedArremer_Dodge',"Step 5: jump up out of the way of Arthur's shot, then hover and come down"),
 (0xE7EC,'RedArremer_DodgeStart',None),
 (0xE84A,'RedArremer_DodgeRise',None),
 (0xE86A,'RedArremerDodgeSpeed',"+-1.13 / +-1.38 px/frame"),
 (0xE872,'RedArremerDodgeChecks',"Thresholds for the dodge test while in the air (these bytes look like stray data)"),
 (0xE878,'RedArremer_DodgeTop',"Still threatened: jump again; otherwise on to hovering"),
 (0xE892,'RedArremer_AirHover',"Hover, walking to its script in the air, for up to 64 frames"),
 (0xE8CE,'RedArremer_Swoop',"Step 6: O_Step2 0 choose, 1-2 fly past at Arthur's level, 3-5 dive from above"),
 (0xE8F2,'RedArremer_SwoopStart',None),
 (0xE92A,'RedArremer_FlyLevel',None),
 (0xE946,'RedArremerSwoopSpeed',"+-2.13 / +-2.38 px/frame"),
 (0xE94E,'RedArremer_FlyOn',"until 64+ px past him, then turn and walk"),
 (0xE974,'RedArremer_DiveStart',"Dive onto Arthur's spot: radii = |dx|, |dy| (too far across: hover instead)"),
 (0xE9BC,'RedArremer_DiveDown',"Quarter ellipse down onto the spot (phase += 3 up to $80)"),
 (0xEA36,'RedArremer_DiveUp',"and up the other side, then hover"),
 (0xEA90,'RedArremer_MoveX',"X += move table[RA_WalkDir] unless flinching (RA_WalkDir < 0: stand)"),
 (0xEAB8,'RedArremer_WalkScriptStep',None),
 (0xEAD4,'RedArremer_CheckDodge',None),
 (0xEAF4,'RedArremer_ShotThreat',"a0 -> (offset, range): when Arthur is far enough away, is one of his shots past\nhim, at our height and on our side? Carry set = dodge. Two bugs (checked in the\nemulator): only the first shot slot's active flag is tested, so a free slot's old\nposition still counts; and 'our side' compares bit 7 of the low bytes of the two\ndistances (eor.b), not their signs, so it is only right while both are under 128 px."),
 (0xEB50,'RedArremerDodgeRange',"dodge only when Arthur is 84+ px away (76+ raging)"),
 (0xEB58,'RedArremer_Flinch',"After a hit (O_Param 1): flinch animation until it ends"),
 (0xEB94,'RedArremer_ShotTimer',None),
 (0xEBC6,'RedArremer_SwoopTimer',None),
 (0xEBF2,'RedArremer_TakeOffTimer',None),
 (0xEC24,'RedArremerGlideRange',"glide when |dx| < 48 or > 112 (raging: < 40 or > 112)"),
 (0xEC2C,'RedArremer_CheckGlide',None),
 (0xEC64,'RedArremer_RageTimer',None),
 (0xEC88,'RedArremer_CurveDown',None),
 (0xECBA,'RedArremer_Fall',None),
 (0xECD6,'RedArremer_TooLow',"Within 48 px of the bottom of the screen: back to RA_BaseY and fly again"),
 (0xECF8,'RedArremer_FaceArthur',None),
 (0xED10,'RedArremer_CurveUp',None),
 (0xED2E,'RedArremer_CurveY',"Y = RA_BaseY + RA_RadiusY x 2 x sin(RA_Phase) / 256"),
 (0xED52,'RedArremer_TooFarToDive',None),
 (0xED66,'RedArremer_Dying',"State 2: sound 12, EnemyBurst, 63 frames"),
 (0xED98,'RedArremer_Free',"State 3: free, give the spawn quota back"),
 (0xEDAA,'RedArremer_AnimPerch',None), (0xEDB0,'RedArremer_AnimWalk',None), (0xEDC8,'RedArremer_AnimFly',None),
 (0xEDE0,'RedArremer_AnimShoot',None), (0xEE04,'RedArremer_AnimFlinch',None), (0xEE10,'RedArremer_AnimFlinchAir',None),
]:
    N(a,n,h)
for a,t in [
 (0xE232,'starting aggression = O_Param >> 2'),
 (0xE23E,'start mode = O_Param & 3 (0 -> 3)'),
 (0xE2F0,'O_Active 2: not hit by shots'),
 (0xE398,'one more big enemy engaged'),
 (0xE416,'more than 64 px below or 320 above the camera: remove'),
 (0xE546,'size class 9 while flying'),
 (0xE644,'enemy shot type 7'),
 (0xE74C,'O_Active 1 -> 2: shots do not register'),
 (0xE76A,'NOP: something removed here (flash?)'),
 (0xE7A6,'faster from now on'),
 (0xE7AE,'O_Active back to 1'),
 (0xEB04,'BUG?: only the first shot slot is tested for being active'),
 (0xEC76,'every 32 frames, only before its rage'),
]:
    C(a,t)
C(0x10592, LEFTOVER_SFX)
C(0x1078C, LEFTOVER_SFX)
C(0xC8AC, "d0 is not used by what follows. [1MB build: PlaySfx here, effect 18; the call was removed in 512K]")
