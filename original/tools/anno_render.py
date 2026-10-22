# Rendering: BOB draw lists, background save/restore, the masked blit, full redraws,
# buffer rotation and the text renderer. Executed inside anno_db.py after anno_flow.py.

V(0x11A, 'g_SmallBobSets', '10 pointers to the small BOB graphics sets (items, scenery), filled by LoadLevel')
V(0x142, 'g_BobSets', '21 pointers to the enemy BOB graphics sets: one per enemy type, then the bat (+76) and red crow (+80)')
V(0x3DA, 'g_SaveBufA', "background save area of the buffer being drawn (its address in a6 is also the top of the BOB draw list, which grows down from here to g_BlitListPtr)")
V(0x3DE, 'g_SaveBufB', 'background save area of the other buffer')
V(0x3E2, 'g_SavePtr', 'next free byte in g_SaveBufA (limit $3000 bytes a frame)')
V(0x3E6, 'g_SavePtrB', 'the same for the other buffer')
V(0x3EA, 'g_RestoreListA', 'restore list of the buffer being drawn: 12-byte entries (BLTSIZE, modulo, screen address, save address) growing down from $632; 0 ends it')
V(0x3EE, 'g_RestoreListB', 'restore list of the other buffer (grows down from $872)')
VAR_RANGES.extend([(0x11A, 40), (0x142, 84)])

HEADERS[0xBA3E] = """DrawBobs - draw this frame's BOB list. The Queue*Draw routines push 12-byte entries
(x.w, y.w, width.w, height.w, graphics.l) downwards from g_SaveBufA's address in the
globals; this walks them from g_BlitListPtr back up, so the last queued is drawn first
and the first queued ends up on top. g_SavePtr restarts at g_SaveBufA."""
HEADERS[0xB9EC] = """RestoreBackground - undo last time's BOBs in this buffer: copy each saved rectangle
back (A->D blits) from the restore list, then reset the list"""
HEADERS[0xBA5C] = """DrawBob - masked blit of one BOB into the back buffer.
In: a1 = frame graphics, d1,d2 = level x,y (y up), d3 = width, d4 = height.
The screen buffer is 288 x 256 (18 x 16 tiles) plus a 16-px margin on the left,
line-interleaved: each 180-byte line holds the 5 planes of 36 bytes. Y is measured up
from the bottom of the buffer.
 - clip left, right (288 px) and top/bottom (256 lines), adjusting the graphics
   pointer and the first/last-word masks
 - if the background save area would pass $3000 bytes this frame, the BOB is
   not drawn at all (so a very busy screen loses BOBs rather than corrupting)
 - save the background under it (A->D) and add a restore-list entry
 - mask = OR of the 5 planes (colour 0 transparent), built in two blits at $371E8
   (A|B|C, then mask|B|C), minterm $FE
 - 5 cookie-cut blits (minterm $CA: D = A ? B : C) with the X shift in BLTCON0/1."""
for a,t in [
 (0xBA5C,'level -> buffer coordinates (16-px left margin)'),
 (0xBA70,'d6 = width in words; d0 = words touched at this X'),
 (0xBA84,'last-word mask: all ones unless the shift needs an extra word'),
 (0xBA8C,'off the left edge: skip whole words of graphics, mask the first'),
 (0xBAAC,'off the right edge (288 px)?'),
 (0xBACC,'Y: line = 256 - y - height; clip at the top ...'),
 (0xBAE0,'... and at the bottom (skip graphics lines)'),
 (0xBAFE,'X shift for BLTCON0/1'),
 (0xBB04,'screen address of the top-left word'),
 (0xBB16,'BLTSIZE for one plane, and for the 5-plane save (5 x the lines)'),
 (0xBB2A,'screen modulo = 36 - width'),
 (0xBB30,'room in the save area ($3000 bytes)?'),
 (0xBB42,'no: the BOB is skipped'),
 (0xBB48,'restore-list entry: save address, screen address, modulo, BLTSIZE'),
 (0xBB68,'save the background (A->D copy)'),
 (0xBB9C,'build the mask at $371E8 from planes 0-2 ...'),
 (0xBBD8,'... then planes 3-4'),
 (0xBC04,'cookie-cut plane 0: D = mask ? BOB : screen'),
 (0xBC3C,'plane 1'),(0xBC5C,'plane 2'),(0xBC7C,'plane 3'),(0xBC9C,'plane 4'),
]: C(a,t)
for a,t in [
 (0xB9FA,'A->D copy, no masking'),
 (0xBA12,'entry: BLTSIZE (0 = end), modulo, screen address, save address'),
 (0xBA3E,'rewind the save area'),
 (0xBA44,'walk the draw list up to its top'),
]: C(a,t)

HEADERS[0xA1E4] = """QueueEnemyDraw - queue enemy a5 for DrawBobs.
Dying enemies (state 2) are drawn as an explosion (QueueExplosionDraw) during the step
that shows it; removed ones (state 3) not at all. Position = O_X/O_Y less half the
BoxSizeTable size; graphics = g_BobSets[type] (the Crow / bat uses the bat or red-crow
set by O_Param) + the frame's offset from BobFrameDescs, whose entries are
(offset.w, y adjust.b, height.b). The Unicorn (type 8) is two BOBs: body
(48 x 32, frame / 8 + 8) and legs (48 x 16, frame & 7)."""
for a,t in [
 (0xA1E4,'dying: explosion; removed: nothing'),
 (0xA1EE,"Dragon: during its steps 2 and 5"),
 (0xA21A,'Unicorn: two BOBs'),
 (0xA224,'box size: the BOB is centred on O_X / O_Y'),
 (0xA24E,'Crow / bat: param < 3 bat graphics, 3 red crow'),
 (0xA276,'graphics set of this enemy type, frame table of the type'),
 (0xA28A,'frame entry: offset.w, y adjust.b, height.b'),
 (0xA2A6,'push (x, y, w, h, graphics) on the draw list'),
 (0xA2B6,'Unicorn body: 48 x 32 at (x-24, y-8)'),
 (0xA2F4,'Unicorn legs: 48 x 16 at (x-24, y-24)'),
]: C(a,t)
HEADERS[0xA398] = """QueueObjectDraw - queue a special object (bonus prize, key, cut-scene armour): graphics
at $1B4CC, frame from EffectFrames, centred with BoxSizeTable"""

HEADERS[0xBFDE] = """RedrawScreen - full redraw of the playfield at the new origin g_NewTileX/Y, into
g_ScreenSpare1, then copied to g_ScreenSpare2 (CameraJump / SwapScreens show them).
18 x 16 tiles of 16 x 16, from the bottom row up: cell = map byte (the map is in
16 x 16-tile cells), tile = CellTiles[cell][row][col], blitted from the level file
(160 bytes a tile: 16 lines x 5 planes, BLTSIZE $1401, D modulo 34). Interrupts are
held off (INTENA) around each blit. Cell $67 always gives tile 0.
On level 1, map cells $1F and $1D (its tiles 0-9) take their tiles from a second bank
(tile + 256). Levels 0 (before tile column $70) and 2 (before $40) then draw the
shootable scenery into the background (DrawSceneryOnRedraw).
Finally sets g_RedrawDone. Runs outside the interrupts, from RedrawEntry, or directly
during set-up."""
for a,t in [
 (0xBFE2,'start at the bottom row: 240 lines down'),
 (0xC002,'level 1: second tile bank for some cells'),
 (0xC00A,'16 rows'),
 (0xC00C,'18 columns'),
 (0xC00E,'map cell of this tile; d4 / d3 = column / row within the cell'),
 (0xC03A,'tile = CellTiles[cell][row][col]'),
 (0xC068,'160 bytes a tile'),
 (0xC070,'interrupts off for the blit'),
 (0xC07C,'A->D copy, 80 lines x 1 word, D modulo 34'),
 (0xC09E,'interrupts back on'),
 (0xC0A8,'up one tile row'),
 (0xC0B0,'level 0 (before column $70) or 2 (before $40): draw the scenery items'),
 (0xC0D0,'copy the whole buffer to the second spare (46080 bytes)'),
 (0xC142,'done'),
]: C(a,t)
HEADERS[0xC1FC] = """DrawSceneryOnRedraw - draw every active item of type 1 (gravestones and other
shootable scenery) into the freshly redrawn background, with the same clipping and
masked blits as DrawBob but without saving the background, so they cost nothing per
frame (levels 0 and 2)"""

HEADERS[0x8082] = """SwapScreens - adopt the new tile origin (g_NewTileX/Y) and rotate the four screen
buffers and copper lists: the two just redrawn become the working pair, the old pair
the spares for the next redraw. Both restore lists are emptied."""
HEADERS[0x80DC] = """ShowBackBuffer - wait for the copper interrupt (INTREQ bit 4, raised by the copper
list), point COP2LC at the copper list just built, then swap front and back screens,
save areas, restore lists and save pointers for the next frame"""
C(0x80F0, 'wait for the copper interrupt')
C(0x8110, 'swap the save-area pointers, restore lists and save areas')

HEADERS[0xB0B0] = """PrintChar - draw character d0 at byte column d1, line d2 (line < 32: the HUD
area, CLEAR_AREA; otherwise the playfield, allowing for the fine scroll).
The font (MASK_BUF, 16 bytes a character) has two bit-planes, 8 lines of 2 bytes, so
4 colours: first plane only = g_TextShadow, second only = g_TextInk, both =
g_TextPaper, neither = transparent on the playfield (the background shows) or colour 0
in the HUD. Each of the 5 screen planes is worked out bit by bit from the three
colour numbers (fully unrolled)."""
C(0x5D76, "background save areas, $3000 bytes each: the load buffers BOB_GFX_A / B are free once")
C(0x5D7E, "LoadLevel has copied the graphics sets it needs to the end of the level file")
C(0x5D86, 'empty restore lists (they grow down from $632 and $872)')
# start-up details
C(0x5AEE, 'CPU exceptions $08-$24 (bus error ... trace) -> CrashReset')
C(0x5B10, 'autovectors $60-$7C -> CrashReset, except level 3 (kept for now)')
C(0x5B92, '40 frames (0-39) are mirrored')
C(0x5C1E, 'HudTimerSprA / B into the lower HUD sprite blocks')
C(0x5C52, "lives icon into sprites 4-7")
C(0x5C92, 'HudSpriteDataA / B into the second blocks of sprites 4-7')
C(0x5CE8, 'the font: every other byte of the file (one plane pair) into MASK_BUF')
C(0x5D04, 'high-score table: all 10000, names from DefaultHiNames')
C(0x5DB2, 'the four screen buffers')
C(0x5E14, 'colours 0-3 for the copyright screen')
