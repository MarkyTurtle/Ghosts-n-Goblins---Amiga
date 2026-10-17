# Arthur's movement and states. Executed inside anno_db.py after anno_enemies.py.
HEADERS[0x84C2] = """==================================================================
ArthurUpdate - Arthur's state machine (g_ArthurState):
 0 normal (walk / jump / fall / crouch / ladder / frog)   1 hit
 2 knockback start   3 knockback flight   4 landed after the knockback
 5-7 death animation
Positions and speeds are 16.16 fixed point, Y increasing upwards.
  walk     1.125 px/frame (ArthurWalk)
  jump     up 4.25 px/frame, gravity 0.24 px/frame^2 (falls at up to 5 px/frame):
           rises for 17 frames, about 39 px high; forward jumps start at 0.5 px/frame and
           speed up by 0.06 px/frame while rising - about 44 px over a 35-frame jump.
           Direction is fixed for the whole jump.
  ladder   1.375 px/frame up or down
  frog     g_FrogTimer x 64 frames (8 = 512 frames); can walk and jump, not climb or fire
==================================================================="""
for a,n,h in [
 (0x8354,'ArthurHit',"State 1. With armour: it flies off as 4 pieces (shot type 5, sound 1) and he is knocked\nback. Without: he dies (the 1MB build plays tune 8, or 7 on the last life)."),
 (0x83C0,'ArthurKnockback',"State 2: thrown up and away from the enemy (the same launch as a jump: 4.25 up,\n0.5 across), facing it"),
 (0x8408,'ArthurKnockFly',"State 3: fly until he lands"),
 (0x8418,'ArthurLand',"State 4: landed. Armour lost now: flash (invulnerable) for 120 frames and carry on in\nhis underwear; already without armour: start dying (20 + 40 + 225 frames)"),
 (0x847E,'ArthurDie1',None), (0x849E,'ArthurDie2',None),
 (0x84F0,'ArthurNormal',"State 0: frog / jumping / falling / crouching / ladder / walking. Order: up or down\n(ladder, jump, crouch), climb, fire, left / right, then the floor test (walking off an\nedge starts a fall) and the platform test."),
 (0x8600,'ArthurJump',"Jump (and knockback) physics. Rising: X += vx (if moving), Y += vy, vx += $FA0,\nvy -= $3D90; below $3DFF it starts to fall: Y -= vy, vy += $3D90 up to 5 px/frame.\nWalls stop the horizontal part. Leaving a platform drops it."),
 (0x8698,'ArthurFall',"Falling (off an edge or after a jump's top): sideways at vx (growing), down at vy\n(up to 5 px/frame); lands on a platform or the floor (sound 5)"),
 (0x8744,'ArthurCrouch',"Crouching: no walking; up / down and fire still read"),
 (0x8772,'ArthurReadLeftRight',"Left / right held: face that way and walk; neither: stand (or keep crouching)"),
 (0x87E6,'ArthurReadUpDown',"Up: climb a ladder he stands at (or carry on climbing / step off at the top), else\njump (sound 4). Down: step onto a ladder 18 px below his feet (moving 14 px down), carry\non down, else crouch. Out: d0 nonzero = up or down was acted on."),
 (0x8A64,'ArthurWalk',"Walk 1.125 px/frame unless firing; stopped by platforms and walls"),
 (0x8ABE,'WallCheckRight',"Wall 16 px to the right at knee height (Y - 7)? Push him out of it (WallProfileR);\nif that leaves him within 10 px of the right edge of the screen he stops walking.\nOut: Z clear = wall."),
 (0x8B16,'WallCheckLeft',"The same to the left (WallProfileL) and the left edge of the screen"),
 (0x8B5C,'ArthurClimb',"1.375 px/frame up (g_LadderDir > 0) or down"),
 (0x8B74,'LadderCheck',"Ladder tile at d6, d7 (profile $40-$7D, not background)? Snap X to its 16-px column\n(the profile's bit 0 says which half)."),
]:
    if n: N(a,n,h)
for a,t in [
 (0x8354,'no longer a frog'),
 (0x8398,'shot type 5: a piece of armour'),
 (0x83A6,'sound 1: hit'),
 (0x83AE,'no armour: dying. d0 = tune for the 1MB build: 8, or 7 (game over) on the last life'),
 (0x83C0,'face the enemy (the opposite of the way he is pushed)'),
 (0x83E0,'0.5 px/frame away'),
 (0x83E8,'4.25 px/frame up'),
 (0x8452,'flash for 120 frames: enemies cannot hurt him'),
 (0x845C,'armour gone'),
 (0x84A6,'225 frames'),
 (0x84BC,'tell the game loop'),
 (0x84FE,'invulnerable flash counting down'),
 (0x8530,'fire (ArthurFire) before moving'),
 (0x855A,'floor under his feet? no: start falling'),
 (0x8594,'every 64 frames'),
 (0x859A,'back to normal'),
 (0x8616,'jumping left'),
 (0x8642,'vx grows while rising'),
 (0x864A,'gravity'),
 (0x865C,'top of the jump: falling from now on'),
 (0x8682,'fall speed limit 5 px/frame'),
 (0x8702,'landed'),
 (0x871E,'sound 5: land'),
 (0x877A,'right held (bit 1)'),
 (0x8780,'left held (bit 9)'),
 (0x87F2,'up held (bit 8)'),
 (0x87F8,'down held (bit 0)'),
 (0x8816,'ladder here?'),
 (0x8846,'at the top of a ladder: getting-off animation steps (0, 10, 17)'),
 (0x888A,'jump'),
 (0x88AC,'sound 4: jump'),
 (0x88BC,'0.5 px/frame forward if he is moving, else straight up'),
 (0x88CE,'4.25 px/frame up'),
 (0x88F0,'ladder 18 px below his feet?'),
 (0x890C,'step down onto it'),
 (0x896C,'crouch'),
 (0x899A,'can fire again once the cooldown is down to 5'),
 (0x89A4,'fire newly pressed?'),
 (0x89BA,'slots this weapon may use'),
 (0x89E6,'shot type = g_Weapon (low byte)'),
 (0x89EC,'from 9 px above his feet, or 3 below when crouching'),
 (0x8A0A,'facing left: from his X, direction 2'),
 (0x8A12,'facing right: 15 px ahead, direction 1'),
 (0x8A22,'15-frame cooldown with the throw animation'),
 (0x8A3A,'sound 6: throw'),
 (0x8A8C,'1.125 px/frame right'),
 (0x8AB2,'1.125 px/frame left'),
 (0x8B60,'1.375 px/frame'),
]:
    C(a,t)
HEADERS[0x8BAC] = """Arthur's animations. Each table has offsets to the facing-right and facing-left scripts;
ArthurSetAnim picks one by g_ArthurFacing. Frame numbers (sprite frames, tracks 33-36):
  0-3 walk  4 stand  5 jump forward  6 jump up  7 crouch  8-9 throw  10-11 throw crouching
  12 climb  13-14 top of a ladder  15 and 37-39 frog  31 knocked back (armour gone)
  32-36 skeleton (dying)
~n is the mirrored copy of frame n (built at start-up). ArthurAnimate adds 16 to frames
0-15 when he has lost his armour (the frames in his underwear)."""
N(0x8E08,'EnemyVsArthur',"Enemy bodies against Arthur (boxes per enemy type: EnemyContactBoxes, smaller when he\ncrouches). Skipped while he flashes or is already hit. Fire (type 14) only hurts at its full\nflare (size class 10). A touch knocks him back (g_ArthurState 1, pushed away from the enemy),\nexcept with the cheat on once his armour is gone.")
N(0x8CD8,'EnemyContactBoxes',"Per enemy type, 8 bytes: x offset, width, y offset, height (standing)")
N(0x8D70,'EnemyContactBoxesCrouch',"The same while Arthur crouches")
C(0x8E3C,'fire: only at full flare')
C(0x8E6C,'cheat: no effect once the armour is gone')
C(0x81D2,'probe 8 px left of centre, 16 px below')
C(0x8202,'then 8 px right')
