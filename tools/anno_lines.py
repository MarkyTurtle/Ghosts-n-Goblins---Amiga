# Line comments for the routines that only had headers. Executed inside anno_db.py last.
N(0x82F8, 'ArthurSetScript', "Start Arthur's animation script a1 as it is (no facing table) and show its first frame")

# ---------------------------------------------------------------- QueueExplosionDraw
HEADERS[0x9FBC] = """QueueExplosionDraw - a dying enemy's explosion. While the frame is below $1B the frame
from EffectFrames ($1B4CC graphics) is queued as a grid of 16 x 16 tiles around the
enemy, by size class: below 4 a 2 x 2 square, 4 a 3 x 3, above 4 a 4 x 4 (walked as a
snake, each step moving the last position by 16 px). From frame $1B on (the final puff,
EnemyDie_Anim) it is drawn once, as a normal object."""
for a,t in [
 (0x9FBC,'the final puff: one BOB'),
 (0x9FC6,'(BoxSizeTable is looked up but not used)'),
 (0x9FDC,'one 16 x 16 tile, centred on the enemy'),
 (0x9FEE,'explosion graphics + this frame'),
 (0xA006,'grid step 16 px'),
 (0xA008,'size class 4: 3 x 3; above: 4 x 4'),
 (0xA014,'2 x 2'),(0xA054,'3 x 3'),(0xA0E4,'4 x 4'),
]: C(a,t)

# ---------------------------------------------------------------- UpdateMapZone
for a,t in [
 (0x7AEC,'map cell under the camera: column ...'),
 (0x7AF6,'... and row (32 cells a row)'),
 (0x7B02,'-> offset into WorldMap -> zone from MapZoneTable'),
 (0x7B16,'same zone as last frame: nothing to do'),
 (0x7B22,'zone changed: stop every spawner not flagged to keep running'),
 (0x7B3A,"the zone's spawner list (ZoneSpawners: byte offset to count + entries)"),
 (0x7B4E,'entry: type (high nibble of byte 1), script number, flags (high nibble of byte 2)'),
 (0x7B60,'SpawnScripts: per type a byte offset to a word-offset table of scripts'),
 (0x7B70,'empty script: skip'),
 (0x7B74,'start the spawner of this type: active, first spawn in 10 frames,'),
 (0x7B88,'script start and position, entries left, flags'),
 (0x7B9C,'types with ZoneFlags = 0 (bosses, Red Arremer, Big Man) keep running and only'),
 (0x7BA4,'start in a zone beyond any reached before'),
]: C(a,t)

# ---------------------------------------------------------------- UpdateSpawners
for a,t in [
 (0xA9A6,'a2 = spawner slot ($C bytes), d7 = its enemy type'),
 (0xA9B2,'entries left?'),
 (0xA9B8,"script finished: a 'run once' spawner stops, the others start again"),
 (0xA9DA,'restart the script: count and first entry'),
 (0xA9E8,'count down to the next spawn'),
 (0xA9F0,'find a free enemy slot (none: stop for this frame)'),
 (0xAA14,'new enemy: active, state 0, type = spawner number'),
 (0xAA38,'script entry: x, y, param, frames to the next spawn'),
 (0xAA5A,'flag bit 0: world coordinates; otherwise relative to the camera'),
 (0xAA92,'special object 0 free? it becomes the bonus this enemy carries'),
 (0xAAB2,'next kind in the 7-step cycle (BonusKinds)'),
 (0xAAD4,'next script entry'),
 (0xAADC,'next spawner'),
]: C(a,t)
for a,t in [
 (0xAB08,'treasure: 6 + level, or kind 12 when g_BonusRoll carries (+21 a time)'),
 (0xAB1A,"weapon: add the level's weights to the five g_WeaponOdds accumulators"),
 (0xAB3C,'the first weapon whose accumulator carried ...'),
 (0xAB4A,"... unless it is Arthur's weapon: then try again"),
]: C(a,t)

# ---------------------------------------------------------------- collisions
for a,t in [
 (0x8F4E,'not while flashing or already hit'),
 (0x8F5E,'boxes by enemy-shot type (smaller set while crouching)'),
 (0x8F72,'each active, on-screen enemy shot'),
 (0x8F86,'X inside the box? d1 = side it came from (knock-back direction)'),
 (0x8F9E,'Y inside the box?'),
 (0x8FCE,'cheat on and no armour: no harm'),
 (0x8FDA,'hit: knocked back away from the shot'),
 (0x8FE4,'the shot is used up'),
]: C(a,t)
HEADERS[0x9704] = """ShotsVsEnemyShots - Arthur's shots against enemy shots.
 Without the cross only fire-pillar shots (type 5) collide, and only Arthur's shot is
 stopped. With the cross every enemy shot except the frog spell (0) and Astaroth's (10)
 collides, and both shots are destroyed.
 BUG: the box pointer a0 is set once per enemy shot and advanced by each test, so after
 a miss the next of Arthur's shots is tested against the following words of the table
 (another type's box). With one shot on screen it makes no difference."""
for a,t in [
 (0x9714,'d1 = 0 no collision, 1 Arthur\'s shot stops, 2 both destroyed'),
 (0x9722,'not the cross: only fire-pillar shots'),
 (0x972C,'cross: all but the frog spell and Astaroth\'s shots'),
 (0x973C,'box for this enemy-shot type (a0 advances through it below)'),
 (0x9752,'X test'),(0x9760,'Y test'),
 (0x9772,'cross: the enemy shot is destroyed too'),
 (0x9784,"Arthur's shot: state 2, step 1"),
]: C(a,t)
HEADERS[0x97AA] = """Boxes for Arthur's shots against enemy shots, per enemy-shot type (ShotsVsEnemyShots).
Only types 0-11 exist; entries 12-18 are never used."""
for a,t in [
 (0x95D4,'weapon bitmask and hit box of this enemy type'),
 (0x95EE,"each of Arthur's active, on-screen shots"),
 (0x95F8,'Astaroth: within 32 px, and only a 9-px band either side of his centre'),
 (0x9628,'outside the band: deflected'),
 (0x963C,'inside the hit box?'),
 (0x9662,'weapon bit set in EnemyVulnerability?'),
 (0x966C,'active byte bit 7: shots pass through (deflected)'),
 (0x9670,'hit points (0 counts as 1)'),
 (0x967C,'hurt, not dead: O_Param = 1 (hit reaction)'),
 (0x9684,'killed: points, state 2'),
 (0x96B2,'the shot ends: step 0 normally, 3 (a hit spark) if the enemy survived'),
]: C(a,t)
for a,t in [
 (0x8250,'each on-screen item of type 1-5'),
 (0x8262,'width and height of this item type'),
 (0x8270,'probe X within the width?'),
 (0x8282,'probe Y within the height?'),
 (0x8290,'falling: only when he is above its middle'),
 (0x82A0,'within 3 px of the top: snap onto it'),
 (0x82BE,'type 2-5 (moving): it carries him - mark it as his platform'),
]: C(a,t)

# ---------------------------------------------------------------- VblIRQ / InitHardware
for a,t in [
 (0xBDD6,'HUD sprites 4-7: the control words, or nothing'),
 (0xBE42,"Arthur's sprites 0-3: control words from ArthurSpritePos, or nothing"),
 (0xBE92,'negative frame ~n: the mirrored copy, stored after the 42 normal frames'),
 (0xBE98,'$80 bytes a frame in each of the four sprite banks ($2900 apart)'),
 (0xBFB4,'interrupted user mode with a redraw pending?'),
 (0xBFCA,'replace the return address; reset the user stack'),
]: C(a,t)
for a,t in [
 (0x7CF0,'bitplane DMA off while setting up'),
 (0x7CF6,'5 bitplanes, lores'),
 (0x7D08,'modulo 146: 180-byte interleaved lines, 34 bytes fetched'),
 (0x7D14,'fetch 17 words (272 px: one more than shown, for the scroll)'),
 (0x7D20,'display window: 240 lines from line 52, 256 px wide'),
 (0x7D2C,'audio: silent, period 1'),
 (0x7D7E,'CIA-A: all interrupts off, then the keyboard (SP) on'),
 (0x7D8A,'CIA-A CRA: keep only bit 7'),
 (0x7DB2,'copper: COP1 = the init list at COPPER_INIT, COP2 = the front list'),
 (0x7DC4,'all interrupts off before installing the vectors'),
 (0x7DE2,'clear the long before COPPER_INIT'),
 (0x7DE8,'DMA on: blitter priority, master, bitplanes, copper, blitter, sprites, disk'),
 (0x7DFA,'wait for raster line 300'),
]: C(a,t)
for a,t in [
 (0x7920,'the unpacked map picture (address kept in g_ArthurAnim)'),
 (0x7924,'+ the scroll in words'),
 (0x7938,'5 planes, $32 bytes apart (one map line is $32 x 5 bytes)'),
 (0x789A,'front screen'),
 (0x789E,'+ the scroll in words'),
 (0x78AE,'+ (16 - fine Y) lines of 180 bytes'),
 (0x78BE,'5 planes, 36 bytes apart (line-interleaved)'),
]: C(a,t)

# ---------------------------------------------------------------- ArthurReadUpDown
for a,t in [
 (0x87E6,'up / down only count when held for two VBL samples'),
 (0x8800,'neither: not on a ladder move'),
 (0x8808,'up: a frog cannot climb, he jumps'),
 (0x881C,'already climbing up: carry on'),
 (0x8822,'start climbing up'),
 (0x8840,'no ladder at his feet: at the top of one?'),
 (0x8870,'off the ladder: standing'),
 (0x8884,'up and not on a ladder: jump (not while climbing)'),
 (0x88E6,'down: a frog cannot climb'),
 (0x88FC,'already on a ladder going down: carry on'),
 (0x891C,'stepping down from the top: run the getting-on poses'),
 (0x8938,"BUG: compares d0 ($FF from LadderCheck) instead of g_StateTimer, so the"),
 (0x8940,'second pose (ArthurAnimLadderTop1 at step 10) never shows going down'),
 (0x8960,'poses done: climbing'),
]: C(a,t)

# ---------------------------------------------------------------- DrawSceneryOnRedraw
for a,t in [
 (0xC1FC,'every active item of type 1'),
 (0xC214,'image and size from ItemBoxSizes / SmallBobSizes'),
 (0xC244,'graphics: g_SmallBobSets[image]'),
 (0xC24E,'into the redrawn buffer, relative to the new origin'),
 (0xC266,'clipping as in DrawBob'),
 (0xC2F4,'screen address and BLTSIZE'),
 (0xC316,'mask, then 5 cookie-cut blits (no background save)'),
]: C(a,t)

# ---------------------------------------------------------------- Unicorn / Petite Devil
for a,t in [
 (0xFA66,'rising script for this jump type (types 2+ use the second entry)'),
 (0xFAB4,'random next jump type (Unicorn_JumpChoicesAfter1 after a type-1 jump)'),
 (0xFAE2,'level 1: left of world X $1A60 an even jump type becomes a standing landing'),
 (0xFB06,'level 5: the same left of $1DA8 ...'),
 (0xFB1E,'... and right of $1E38 an odd type (or type 0)'),
 (0xFAF8,'no jump: step 2.5 (land on the spot)'),
 (0xFB34,'jump: next step'),
]: C(a,t)
for a,t in [
 (0xD7DC,'count down to the next shot'),
 (0xD7E8,'one shot at a time, when ready, if an enemy-shot slot is free'),
 (0xD7FA,'within 16 px above Arthur and 50 px either side: shoot sideways'),
 (0xD82A,'or within 5 px of his X and up to 60 px above: shoot down'),
 (0xD850,'sideways, towards Arthur'),
 (0xD862,'straight down'),
 (0xD868,'the shot: type 8, 10 px below the devil'),
]: C(a,t)
for a,t in [
 (0xD244,'path list entry: offset to a segment set, then its turn count'),
 (0xD252,'PD_Time 0 picks the alternative set (one entry back)'),
 (0xD266,'is the segment start on screen (camera X .. +256, Y + 32 .. + 224)?'),
 (0xD294,'yes: appear there'),
 (0xD2A8,'no: try the next segment (or the alternative)'),
 (0xD2B6,'after PD_TurnWait tries take the next entry; when PD_TurnRate runs out, give up'),
]: C(a,t)
N(0xAD82, 'ApplyMoveA0', "ApplyMoveTable with the movement table already in a0")
