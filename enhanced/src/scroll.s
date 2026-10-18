;==============================================================================
; scroll.s - incremental scroller for the enhanced build (prototype, step 1)
;
; Replaces the original full-screen redraw (RedrawScreen) with buffers that are
; updated one tile column / row at a time as the camera moves.
;
; Screen layout (see enhanced/docs/SCROLLER.md):
;  * Line-interleaved, as the original: each 180-byte line holds the 5 planes' 36-byte
;    rows, so a tile is still one blit (16 lines x 5 planes).
;  * Horizontal: corkscrew. A world tile column C is always at byte 2*(C+1) of a
;    plane row. Scrolling right moves the bitplane pointers on 2 bytes; a plane's
;    fetch then runs into the start of the next plane row (or, for plane 4, the next
;    line's plane 0) - bytes whose own column has just scrolled off the left, which is
;    exactly where the new right-hand column is drawn. The buffer carries COL_SLACK
;    spare bytes for the drift.
;  * Vertical: a ring of RING_LINES lines. World line y (Y up) is ring line
;    (-1-y) & 255; the copper reloads the bitplane pointers where the ring wraps.
;  * Address of (column C, world line y) in plane p:
;       base + 2*(C+1) + 180*((-1-y) & 255) + 36*p
;    The same for every buffer, so a pristine copy can be blitted straight across.
;  * (C, line, plane p) shares memory with (C+18, line, plane p-1), so at most 18
;    columns are held.
;
; The tile lookup (map, CellTiles, cell $67, the level-1 second bank) is the same as
; the original RedrawScreen ($BFDE), so the picture is identical.
;
; Buffers: a pristine buffer holds the background only (drawn from the tiles); the
; two display buffers copy new edges from it and restore under their BOBs from it.
;
; This file is the core only: it is included by module.s (the game module, loaded by the
; enhanced build) and by scroll_test.s (the unit tests' build at $7A000). The includer
; defines the custom-chip / globals equates (gng_equates.i, with BUILD_1MB for the 1MB build), CellTiles,
; ItemBoxSizes, SmallBobSizes and MASKBUF (a one-plane BOB mask, at most 64 x 80 pixels; 512K
; only). BUILD_1MB selects the 1MB build: its program tables are offsets from g_BaseAddr, and
; its BOB graphics carry their masks, so a BOB is one blit. BUILD_ONE (the one program for every
; machine, gng_game.s): absolute addresses, and the BOB drawing is chosen at run time - masked
; graphics (one blit) with PF_CACHE in Profile, the 512K way otherwise.
;
; Calls (a6 = game globals, as everywhere in the game):
;   ScrFullDraw    a0 = buffer record, d0 = camera x, d1 = camera y
;   ScrScrollTo    a0 = buffer record, d0 = camera x, d1 = camera y
;   ScrBuildCopper a0 = buffer record, a1 = copper list, d0 = camera x, d1 = camera y
;   ScrRestore     a0 = display buffer record: undo its BOBs from the pristine buffer
;   ScrDrawBobs    a0 = display buffer record, a3 = draw list, a5 = its end
;                  (the game's 12-byte entries: x, y, width, height, graphics)
; Camera (as the original): x = world x of the leftmost visible pixel
; (g_ScrollTileX*16 + g_ScrollFineX); y = g_ScrollTileY*16 + g_ScrollFineY, so the
; visible playfield is world lines y+16 (bottom) .. y+239 (top).
;==============================================================================

ROWBYTES        equ     36              ; 288 px per plane row
LINEBYTES       equ     ROWBYTES*5      ; 5 interleaved planes per line
RING_LINES      equ     256
COL_SLACK       equ     1040            ; corkscrew drift: 2 bytes per world column (levels <= 512 columns)
BUF_SIZE        equ     LINEBYTES*RING_LINES+COL_SLACK
COPY_W          equ     40              ; a whole buffer is one blit of COPY_H lines x 40 words
COPY_H          equ     BUF_SIZE/(2*COPY_W)
                ifne    BUF_SIZE-2*COPY_W*COPY_H
                fail    "BUF_SIZE is not a whole number of 80-byte blit lines"
                endif
FETCH_BYTES     equ     34              ; 17 words fetched per line
DISPLAY_TOP     equ     $44             ; first playfield line (the 16 lines above are the HUD strip)
DISPLAY_END     equ     $124            ; first line after the display window
VISIBLE_W       equ     17*16           ; fetched columns

; buffer record
                rsreset
buf_Base        rs.l    1               ; start of the buffer
buf_ColL        rs.w    1               ; drawn tile columns, inclusive
buf_ColR        rs.w    1
buf_RowB        rs.w    1               ; drawn tile rows (Y up), inclusive
buf_RowT        rs.w    1
buf_Valid       rs.w    1               ; 0 = contents unknown: the next update draws (or copies) it all
buf_Source      rs.l    1               ; pristine buffer record to copy from (0: this is the pristine one)
buf_RListBase   rs.l    1               ; restore list: 8-byte entries (address, BLTSIZE, modulo)
buf_RList       rs.l    1               ; next free entry
buf_ClipX0      rs.w    1               ; world x of the first fetched column
buf_ClipY0      rs.w    1               ; visible world lines ClipY0 .. ClipY1-1
buf_ClipY1      rs.w    1
buf_CamX        rs.w    1               ; camera x of the last update
buf_RListEnd    rs.l    1               ; end of the restore list storage (0: no limit)
buf_Copper      rs.l    1               ; this buffer's copper list (used by the game glue)
buf_SIZEOF      rs.b    0

WAITBLIT        macro
.wb\@:  btst    #6,CUSTOM+DMACONR
        bne.b   .wb\@
        endm
; blitter set-up that may run outside the interrupts (RedrawScreen runs in user mode while
; the game logic, which also blits, can interrupt it): hold the interrupts off around it,
; as the original RedrawScreen does
INTSOFF         macro
        move.w  #$4000,CUSTOM+INTENA
        endm
INTSON          macro
        move.w  #$C000,CUSTOM+INTENA
        endm
; the address of a table in the game program: absolute in the 512K build; in the 1MB build
; the program is position independent and its labels are offsets from g_BaseAddr
GAMEADDR        macro
        lea     \1,\2
        ifd     BUILD_1MB
        adda.l  g_BaseAddr(a6),\2
        endif
        endm

; BOB graphics: bytes per image line for each graphics word of width. 512K: 5 plane lines;
; 1MB: 5 plane lines each followed by its mask line (BuildMaskedGfx). GFXMUL reg: reg (a word
; count) times that, as a long
                ifd     BUILD_1MB
GFX_LINE_MUL    equ     20
                else
GFX_LINE_MUL    equ     10
                endif
                ifd     BUILD_1MB               ; masked BOB drawing assembled (1MB, or chosen at run time)
SCR_MASKED      equ     1
                endif
                ifd     BUILD_ONE
SCR_MASKED      equ     1
                endif
GFXMUL          macro
                ifd     BUILD_ONE
                mulu.w  #10,\1
                btst    #PF_CACHE,(Profile).l
                beq.b   .gm\@
                add.l   \1,\1                 ; masked graphics: twice the lines
.gm\@:
                else
                mulu.w  #GFX_LINE_MUL,\1
                endif
                endm

;------------------------------------------------------------------------------
; Window: d0 = camera x, d1 = camera y ->
;   d2 = first column, d3 = last column, d4 = bottom row, d5 = top row
;------------------------------------------------------------------------------
Window:
                move.w  d0,d2
                add.w   #15,d2
                asr.w   #4,d2
                subq.w  #1,d2                   ; first fetched column = ceil(x/16) - 1
                move.w  d2,d3
                add.w   #16,d3                  ; 17 columns
                move.w  d1,d4
                add.w   #16,d4
                asr.w   #4,d4                   ; bottom visible line y+16
                move.w  d1,d5
                add.w   #239,d5
                asr.w   #4,d5                   ; top visible line y+239
                rts

;------------------------------------------------------------------------------
ScrFullDraw:
                tst.l   buf_Source(a0)          ; a display buffer: copy the (current) pristine one
                beq.b   .draw
                bra.w   CopyAll
.draw:          movem.l d0-d7/a0-a5,-(a7)
                clr.w   buf_Valid(a0)           ; (an interrupting update sees 'unknown' and redraws)
                bsr.b   Window
                move.w  d4,d0                   ; row
.row:           move.w  d2,d1                   ; first column
                move.w  d3,d6                   ; last column
                bsr.w   DrawRow
                addq.w  #1,d0
                cmp.w   d5,d0
                ble.b   .row
                movem.w d2-d5,buf_ColL(a0)      ; ColL, ColR, RowB, RowT
                move.w  2(a7),d0                ; camera (saved d0 / d1)
                move.w  6(a7),d1
                bsr.w   SetClip
                move.w  #1,buf_Valid(a0)
                bsr.w   ScrDrawScenery          ; the pristine buffer: add the scenery
                movem.l (a7)+,d0-d7/a0-a5
                rts

;------------------------------------------------------------------------------
; CopyAll - a0 = display buffer: copy the whole pristine buffer into it (one blit) and
; take its window. Its BOBs are gone, so its restore list is emptied.
;------------------------------------------------------------------------------
CopyAll:
                movem.l d0/a1-a2,-(a7)
                movea.l buf_Source(a0),a1
                lea     CUSTOM,a2
                INTSOFF
                WAITBLIT
                move.l  #$09F00000,BLTCON0(a2)
                move.l  #$FFFFFFFF,BLTAFWM(a2)
                move.w  #0,BLTAMOD(a2)
                move.w  #0,BLTDMOD(a2)
                move.l  buf_Base(a1),BLTAPTH(a2)
                move.l  buf_Base(a0),BLTDPTH(a2)
                move.w  #(COPY_H<<6)|COPY_W,BLTSIZE(a2)
                INTSON
                move.l  buf_ColL(a1),buf_ColL(a0)       ; ColL, ColR
                move.l  buf_RowB(a1),buf_RowB(a0)       ; RowB, RowT
                move.l  buf_ClipX0(a1),buf_ClipX0(a0)   ; ClipX0, ClipY0
                move.l  buf_ClipY1(a1),buf_ClipY1(a0)   ; ClipY1, CamX
                move.l  buf_RListBase(a0),buf_RList(a0)
                move.w  #1,buf_Valid(a0)
                movem.l (a7)+,d0/a1-a2
                rts

;------------------------------------------------------------------------------
; Bring the buffer up to date for the camera: draw the columns and rows that came
; into view, one at a time. A big jump (or a first call) is a full draw.
;------------------------------------------------------------------------------
ScrScrollTo:
                movem.l d0-d7/a0-a5,-(a7)
                tst.w   buf_Valid(a0)
                beq.w   .full
                bsr.w   Window
                move.w  d2,d7
                sub.w   buf_ColL(a0),d7
                bpl.b   .p1
                neg.w   d7
.p1:            cmp.w   #4,d7
                bhi.w   .full
                move.w  d4,d7
                sub.w   buf_RowB(a0),d7
                bpl.b   .p2
                neg.w   d7
.p2:            cmp.w   #4,d7
                bhi.w   .full
.edges:         moveq   #0,d6                   ; d6 = something was drawn
; columns entering on the right
.right:         cmp.w   buf_ColR(a0),d3
                ble.b   .left
                addq.w  #1,buf_ColR(a0)
                move.w  buf_ColR(a0),d0
                bsr.w   DrawColumnAll
                moveq   #1,d6
                move.w  buf_ColR(a0),d7
                sub.w   buf_ColL(a0),d7
                cmp.w   #17,d7                  ; at most 18 columns (a 19th would alias)
                ble.b   .right
                addq.w  #1,buf_ColL(a0)
                bra.b   .right
; columns entering on the left
.left:          cmp.w   buf_ColL(a0),d2
                bge.b   .up
                subq.w  #1,buf_ColL(a0)
                move.w  buf_ColL(a0),d0
                bsr.w   DrawColumnAll
                moveq   #1,d6
                move.w  buf_ColR(a0),d7
                sub.w   buf_ColL(a0),d7
                cmp.w   #17,d7
                ble.b   .left
                subq.w  #1,buf_ColR(a0)
                bra.b   .left
; rows entering at the top
.up:            cmp.w   buf_RowT(a0),d5
                ble.b   .down
                addq.w  #1,buf_RowT(a0)
                move.w  buf_RowT(a0),d0
                bsr.w   DrawRowAll
                moveq   #1,d6
                move.w  buf_RowT(a0),d7
                sub.w   buf_RowB(a0),d7
                cmp.w   #15,d7                  ; at most 16 rows in the 256-line ring
                ble.b   .up
                addq.w  #1,buf_RowB(a0)
                bra.b   .up
; rows entering at the bottom
.down:          cmp.w   buf_RowB(a0),d4
                bge.b   .done
                subq.w  #1,buf_RowB(a0)
                move.w  buf_RowB(a0),d0
                bsr.w   DrawRowAll
                moveq   #1,d6
                move.w  buf_RowT(a0),d7
                sub.w   buf_RowB(a0),d7
                cmp.w   #15,d7
                ble.b   .down
                subq.w  #1,buf_RowT(a0)
                bra.b   .down
.done:          movem.w d2-d5,buf_ColL(a0)      ; keep exactly the needed window, so every
                move.w  2(a7),d0                ; buffer holds the same columns as the pristine one
                move.w  6(a7),d1                ; (camera from the saved d0 / d1)
                bsr.w   SetClip
                tst.w   d6                      ; the pristine buffer got new edges: add the scenery
                beq.b   .nodraw
                tst.l   buf_Source(a0)
                bne.b   .nodraw
                bsr.w   ScrDrawScenery
.nodraw:
                movem.l (a7)+,d0-d7/a0-a5
                rts
.full:          tst.l   buf_Source(a0)
                bne.b   .copy
                movem.l (a7)+,d0-d7/a0-a5
                bra.w   ScrFullDraw
.copy:          bsr.w   CopyAll                 ; a display buffer: copy the pristine one, then
                bsr.w   Window                  ; bring it to this camera (normally nothing to do)
                bra.w   .edges

; d0 = camera x, d1 = camera y, d2 = first column -> clip window for BOBs: the fetched
; columns and, in a display buffer, the visible lines; in the pristine buffer every line of
; the tile rows it holds - the scenery drawn there is copied into the display buffers as the
; view moves within those rows, so it must not be cut off at the lines visible when it was drawn
SetClip:        move.w  d0,buf_CamX(a0)
                move.w  d2,d7
                lsl.w   #4,d7
                move.w  d7,buf_ClipX0(a0)
                tst.l   buf_Source(a0)
                bne.b   .visible
                move.w  buf_RowB(a0),d7
                lsl.w   #4,d7
                move.w  d7,buf_ClipY0(a0)
                move.w  buf_RowT(a0),d7
                addq.w  #1,d7
                lsl.w   #4,d7
                move.w  d7,buf_ClipY1(a0)
                rts
.visible:       move.w  d1,d7
                add.w   #16,d7
                move.w  d7,buf_ClipY0(a0)
                add.w   #224,d7
                move.w  d7,buf_ClipY1(a0)
                rts

; d0 = column: draw it over the buffer's rows
DrawColumnAll:
                movem.l d0-d6,-(a7)
                move.w  d0,d1                   ; column
                move.w  buf_RowB(a0),d0         ; row
.r:             bsr.w   DrawTile
                addq.w  #1,d0
                cmp.w   buf_RowT(a0),d0
                ble.b   .r
                movem.l (a7)+,d0-d6
                rts

; d0 = row: draw it over the buffer's columns
DrawRowAll:
                movem.l d0-d6,-(a7)
                move.w  buf_ColL(a0),d1
                move.w  buf_ColR(a0),d6
                bsr.b   DrawRow
                movem.l (a7)+,d0-d6
                rts

; d0 = row, d1 = first column, d6 = last column
DrawRow:
                movem.l d1,-(a7)
.c:             bsr.b   DrawTile
                addq.w  #1,d1
                cmp.w   d6,d1
                ble.b   .c
                movem.l (a7)+,d1
                rts

;------------------------------------------------------------------------------
; DrawTile - a0 = buffer record, d0 = tile row R (Y up), d1 = tile column C.
; Source tile exactly as RedrawScreen; one blit (16 lines x 5 planes x 1 word).
;------------------------------------------------------------------------------
DrawTile:
                movem.l d0-d7/a2-a4,-(a7)
                ; ---- map cell (as RedrawScreen: d3 = 15 - R)
                moveq   #15,d3
                sub.w   d0,d3
                movea.l g_MapPtr(a6),a2
                move.w  d1,d4
                asr.w   #4,d4
                adda.w  d4,a2
                move.w  d3,d5
                andi.w  #$FFF0,d5
                add.w   d5,d5
                suba.w  d5,a2
                moveq   #0,d6
                move.b  (a2),d6                 ; cell
                movea.l g_LevelFileAddr(a6),a3
                cmp.b   #$67,d6
                beq.b   .src                    ; cell $67: tile 0 everywhere
                move.w  d6,d5                   ; tile = CellTiles[cell][row][col]
                lsl.w   #4,d5
                moveq   #15,d4
                and.w   d3,d4
                add.w   d4,d5
                lsl.w   #4,d5
                moveq   #15,d4
                and.w   d1,d4
                add.w   d4,d5
                GAMEADDR CellTiles,a4
                moveq   #0,d7
                move.b  (a4,d5.w),d7
                beq.b   .src                    ; tile 0
                cmpi.w  #1,g_Level(a6)          ; level 1: cells $1F and $1D use the second bank
                bne.b   .mul
                cmp.b   #$1F,d6
                beq.b   .bank
                cmp.b   #$1D,d6
                bne.b   .mul
                cmp.b   #9,d7
                bhi.b   .mul
                bcs.b   .bank
                moveq   #0,d7                   ; tile 9 of cell $1D -> bank tile 0
.bank:          add.w   #$100,d7
.mul:           mulu.w  #160,d7
                adda.l  d7,a3
.src:
                ; ---- destination: base + 2*(C+1) + 36*ring line of the tile's top line
                move.w  d0,d4
                addq.w  #1,d4
                neg.w   d4
                lsl.w   #4,d4
                andi.w  #$FF,d4                 ; ring line = (-16*(R+1)) & 255
                mulu.w  #LINEBYTES,d4
                move.w  d1,d5
                addq.w  #1,d5
                add.w   d5,d5
                ext.l   d5
                add.l   d5,d4
                movea.l buf_Base(a0),a4
                adda.l  d4,a4
                moveq   #0,d5                   ; source modulo: 0 for a tile
                move.l  buf_Source(a0),d6
                beq.b   .blit
                movea.l d6,a3                   ; display buffer: copy the same place of the pristine buffer
                movea.l buf_Base(a3),a3
                adda.l  d4,a3
                moveq   #ROWBYTES-2,d5
.blit:          ; ---- one blit: the tile's 80 plane lines (16 x 5) to rows 36 bytes apart
                lea     CUSTOM,a2
                INTSOFF
                WAITBLIT
                move.l  #$09F00000,BLTCON0(a2)  ; A -> D
                move.l  #$FFFFFFFF,BLTAFWM(a2)
                move.w  d5,BLTAMOD(a2)
                move.w  #ROWBYTES-2,BLTDMOD(a2)
                move.l  a3,BLTAPTH(a2)
                move.l  a4,BLTDPTH(a2)
                move.w  #((16*5)<<6)|1,BLTSIZE(a2)
                INTSON
                movem.l (a7)+,d0-d7/a2-a4
                rts

;------------------------------------------------------------------------------
; ScrBuildCopper - the playfield part of the copper list (jumped to at line $44):
; bitplane pointers and fine scroll for the camera - the same 11 moves as the original
; list, so they are done before the first line's data fetch - and a pointer reload
; where the 256-line ring wraps. The modulos are not set: they are 146 (180 - 34) as
; InitHardware leaves them, the same as the original's.
;------------------------------------------------------------------------------
ScrBuildCopper:
                movem.l d0-d7/a0-a2,-(a7)
                moveq   #15,d2                  ; BPLCON1: delay = (16 - x) & 15, both playfields
                and.w   d0,d2
                neg.w   d2
                andi.w  #15,d2
                move.w  d2,d3
                lsl.w   #4,d3
                or.w    d3,d2
                move.w  d0,d3                   ; first fetched column
                add.w   #15,d3
                asr.w   #4,d3                   ; = first fetched column + 1
                add.w   d3,d3
                ext.l   d3                      ; d3 = 2*(column+1)
                move.w  d1,d4                   ; ring line of the top line y+239
                add.w   #239+1,d4
                neg.w   d4
                andi.w  #$FF,d4
                move.l  buf_Base(a0),d5
                add.l   d3,d5                   ; d5 = row start of ring line 0
                move.w  d4,d6
                mulu.w  #LINEBYTES,d6
                move.l  d5,d7
                add.l   d6,d7                   ; d7 = top line
                bsr.b   .pointers
                move.w  #BPLCON1,(a1)+          ; (the modulos stay 146, as the game sets them)
                move.w  d2,(a1)+
                tst.w   d4                      ; ring wraps inside the display?
                beq.b   .end
                move.w  #DISPLAY_TOP+RING_LINES,d6
                sub.w   d4,d6                   ; display line of ring line 0
                cmp.w   #DISPLAY_END,d6
                bcc.b   .end
                cmp.w   #$100,d6
                bcs.b   .wait
                move.l  #$FFDFFFFE,(a1)+        ; past line 255
.wait:          move.w  d6,d0
                lsl.w   #8,d0
                or.w    #$01,d0
                move.w  d0,(a1)+
                move.w  #$FF00,(a1)+
                move.l  d5,d7
                bsr.b   .pointers
.end:           move.l  #$FFFFFFFE,(a1)+
                movem.l (a7)+,d0-d7/a0-a2
                rts
; d7 = plane 0 address -> 5 pointer pairs
.pointers:      move.w  #BPL1PTH,d0
                moveq   #4,d1
.pp:            move.w  d0,(a1)+
                swap    d7
                move.w  d7,(a1)+
                swap    d7
                addq.w  #2,d0
                move.w  d0,(a1)+
                move.w  d7,(a1)+
                addq.w  #2,d0
                add.l   #ROWBYTES,d7            ; next plane: next 36-byte row
                dbra    d1,.pp
                rts

;------------------------------------------------------------------------------
; ScrRestore - a0 = display buffer: copy back from the pristine buffer every
; rectangle its BOBs covered last time it was drawn, then empty its list.
;------------------------------------------------------------------------------
ScrRestore:
                movem.l d0-d6/a2-a5,-(a7)
                movea.l buf_RListBase(a0),a3
                movea.l buf_RList(a0),a4
                movea.l buf_Source(a0),a5
                move.l  buf_Base(a5),d6
                sub.l   buf_Base(a0),d6         ; pristine - this buffer
                lea     CUSTOM,a2
                WAITBLIT
                move.l  #$09F00000,BLTCON0(a2)
                move.l  #$FFFFFFFF,BLTAFWM(a2)
.next:          cmpa.l  a4,a3
                beq.b   .done
                move.l  (a3)+,d0                ; screen address
                move.w  (a3)+,d1                ; BLTSIZE (5 plane lines per line)
                move.w  (a3)+,d2                ; modulo
                WAITBLIT
                move.w  d2,BLTAMOD(a2)
                move.w  d2,BLTDMOD(a2)
                move.l  d0,BLTDPTH(a2)
                add.l   d6,d0
                move.l  d0,BLTAPTH(a2)
                move.w  d1,BLTSIZE(a2)
                bra.b   .next
.done:          move.l  buf_RListBase(a0),buf_RList(a0)
                movem.l (a7)+,d0-d6/a2-a5
                rts

;------------------------------------------------------------------------------
; ScrDrawBobs - a0 = display buffer, a3 = first entry, a5 = end of the list.
; Same list as the game's DrawBobs (lowest entry drawn first).
;------------------------------------------------------------------------------
ScrDrawBobs:
                movem.l d0-d7/a1-a5,-(a7)
.next:          cmpa.l  a5,a3
                beq.b   .done
                movem.w (a3)+,d1-d4
                movea.l (a3)+,a1
                bsr.b   ScrDrawBob
                bra.b   .next
.done:          movem.l (a7)+,d0-d7/a1-a5
                rts

;------------------------------------------------------------------------------
; ScrDrawBob - masked blit of one BOB, as the game's DrawBob but with the corkscrew /
; ring addressing and no background save (the restore comes from the pristine buffer).
; In: a0 = buffer, a1 = graphics (line-interleaved, 5 planes), d1 = world x,
; d2 = world y of the bottom line (Y up), d3 = width (px), d4 = height.
; Clipped to the 17 fetched columns and the visible lines; a BOB that crosses the
; ring's wrap is drawn in two parts.
;------------------------------------------------------------------------------
ScrDrawBob:
                movem.l d0-d7/a0-a5,-(a7)
                move.l  buf_RListEnd(a0),d0     ; restore list full (room for 2 entries)? then the
                beq.b   .room                   ; BOB is not drawn (as the original's $3000 limit)
                sub.l   buf_RList(a0),d0
                cmp.l   #16,d0
                blt.w   .out
.room:          moveq   #15,d6
                add.w   d3,d6
                lsr.w   #4,d6                   ; d6 = graphics words per plane line
                ifd     BUILD_ONE
                bsr.w   BobMaskFind             ; 512K: this image's one-plane mask, if made (scroller.s)
                endif
                ; ---- vertical clip
                move.w  d2,d7
                add.w   d4,d7                   ; top (exclusive)
                sub.w   buf_ClipY1(a0),d7       ; lines above the view: skip them in the graphics
                ble.b   .nottop
                sub.w   d7,d4
                ble.w   .out
                move.w  d6,d0
                GFXMUL  d0
                mulu.w  d7,d0
                adda.l  d0,a1
.nottop:        move.w  buf_ClipY0(a0),d7       ; lines below the view
                sub.w   d2,d7
                ble.b   .notbot
                sub.w   d7,d4
                ble.w   .out
                add.w   d7,d2
.notbot:        add.w   d4,d2
                neg.w   d2
                andi.w  #$FF,d2                 ; d2 = ring line of the top line
                ; ---- horizontal clip (as DrawBob, against the fetched columns)
                sub.w   buf_ClipX0(a0),d1
                moveq   #15,d0
                and.w   d1,d0
                add.w   d3,d0
                add.w   #15,d0
                lsr.w   #4,d0                   ; d0 = words touched
                moveq   #-1,d5                  ; first / last word masks
                cmp.w   d6,d0
                seq.b   d5
                ext.w   d5
                move.w  d1,d7
                bpl.b   .noleft
                neg.w   d7
                moveq   #15,d3
                and.w   d7,d3
                lsr.w   #4,d7
                sub.w   d7,d0
                ble.w   .out
                adda.w  d7,a1
                adda.w  d7,a1
                swap    d5
                lsr.w   d3,d5
                swap    d5
                move.w  d3,d1
                neg.w   d1
.noleft:        add.w   d3,d7
                sub.w   #VISIBLE_W,d7
                bls.b   .noright
                add.w   #15,d7
                lsr.w   #4,d7
                sub.w   d7,d0
                bls.w   .out
                move.w  #$FFFF,d5
                moveq   #15,d3
                and.w   d1,d3
                beq.b   .noright
                lsl.w   d3,d5
.noright:       moveq   #15,d3
                and.w   d1,d3
                ror.w   #4,d3                   ; d3 = shift << 12
                move.w  d1,d7                   ; destination column
                asr.w   #4,d7
                move.w  buf_ClipX0(a0),d1
                asr.w   #4,d1
                add.w   d1,d7
                addq.w  #1,d7
                add.w   d7,d7
                ext.l   d7
                movea.l buf_Base(a0),a2
                adda.l  d7,a2                   ; a2 = this column on ring line 0
                ; ---- ring wrap: lines d2 .. d2+d4-1
                move.w  #RING_LINES,d7
                sub.w   d2,d7                   ; lines before the wrap
                cmp.w   d4,d7
                bge.b   .one
                move.w  d4,d1
                sub.w   d7,d1                   ; lines after the wrap
                move.w  d7,d4
                bsr.b   .part                   ; top part
                move.w  d6,d7
                GFXMUL  d7
                mulu.w  d4,d7
                adda.l  d7,a1                   ; graphics of the bottom part
                moveq   #0,d2
                move.w  d1,d4
.one:           bsr.b   .part
.out:           movem.l (a7)+,d0-d7/a0-a5
                rts

; a2 = column base, a1 = graphics, d2 = ring line, d4 = lines, d0 = words,
; d3 = shift << 12, d5 = masks, d6 = graphics words per plane line
.part:          movem.l d0-d7/a1-a5,-(a7)
                move.w  d2,d7
                mulu.w  #LINEBYTES,d7
                movea.l a2,a4
                adda.l  d7,a4                   ; a4 = top-left word, plane 0
                move.l  buf_RList(a0),d7        ; restore entry: address, BLTSIZE (5 x lines), modulo
                beq.b   .nolist                 ; (none for the pristine buffer)
                movea.l d7,a3
                move.l  a4,(a3)+
                move.w  d4,d7
                mulu.w  #5,d7
                lsl.w   #6,d7
                or.w    d0,d7
                move.w  d7,(a3)+
                moveq   #ROWBYTES,d7
                sub.w   d0,d7
                sub.w   d0,d7
                move.w  d7,(a3)+
                move.l  a3,buf_RList(a0)
.nolist:        INTSOFF                         ; (the mask buffer is shared: no interruption)
                ifd     BUILD_ONE
                btst    #PF_CACHE,(Profile).l
                beq.w   .p512
                endif
                ifd     SCR_MASKED
                ; ---- 1MB: pre-masked graphics, every plane line followed by its mask line:
                ; one cookie-cut blit draws all 5 planes (5 x lines blitter lines), as the
                ; 1MB DrawBob. A = mask, B = BOB (modulo skips the other line), C/D = screen
                ; (the next 36-byte row is the next plane, then the next line).
                move.w  d4,d2
                mulu.w  #5,d2
                lsl.w   #6,d2
                or.w    d0,d2                   ; BLTSIZE: 5 x lines, d0 words
                move.w  d6,d1
                add.w   d1,d1                   ; d1 = bytes per plane line of the graphics
                move.w  d1,d7
                add.w   d7,d7
                sub.w   d0,d7
                sub.w   d0,d7                   ; d7 = A / B modulo (4 x words - 2 x d0)
                moveq   #ROWBYTES,d4
                sub.w   d0,d4
                sub.w   d0,d4                   ; d4 = C / D modulo
                lea     CUSTOM,a3
                WAITBLIT
                move.w  d3,BLTCON1(a3)
                or.w    #$0FCA,d3
                move.w  d3,BLTCON0(a3)
                move.w  d4,BLTCMOD(a3)
                move.w  d7,BLTBMOD(a3)
                move.w  d7,BLTAMOD(a3)
                move.w  d4,BLTDMOD(a3)
                move.l  d5,BLTAFWM(a3)
                lea     (a1,d1.w),a2
                move.l  a2,BLTAPTH(a3)
                move.l  a1,BLTBPTH(a3)
                move.l  a4,BLTCPTH(a3)
                move.l  a4,BLTDPTH(a3)
                move.w  d2,BLTSIZE(a3)
                endif
                ifd     BUILD_ONE
                bra.w   .pdone
.p512:          ; ---- 512K with the image's one-plane mask made at level load (BuildLevelMasks):
                ; no mask blits, the 5 cookie-cut blits read it. The graphics pointer has moved
                ; by whole lines (clipped at the top, or the bottom part of a ring wrap) and by
                ; bytes (clipped at the left) since BobMaskFind: the mask moves by a fifth of
                ; the lines and by the same bytes.
                move.l  (BobMask).l,d7
                beq.w   .mkmask
                move.l  a1,d1
                sub.l   (BobGfx).l,d1           ; lines x 5 x line bytes + left bytes
                move.w  d6,d2
                add.w   d2,d2
                mulu.w  #5,d2                   ; graphics bytes per image line
                divu.w  d2,d1                   ; d1.w = lines, high word = left bytes
                move.l  d1,d2
                clr.w   d2
                swap    d2                      ; left bytes
                add.l   d2,d7
                mulu.w  d6,d1
                add.l   d1,d1                   ; lines x mask bytes per line
                add.l   d1,d7
                movea.l d7,a5                   ; the mask of this part
                move.w  d4,d2                   ; BLTSIZE for one plane
                lsl.w   #6,d2
                or.w    d0,d2
                move.w  d6,d1
                add.w   d1,d1                   ; d1 = bytes per plane line of the graphics
                move.w  d1,d7
                mulu.w  #5,d7
                sub.w   d0,d7
                sub.w   d0,d7                   ; d7 = graphics modulo
                lea     CUSTOM,a3
                WAITBLIT
                move.w  d7,BLTBMOD(a3)
                move.w  d1,d7
                sub.w   d0,d7
                sub.w   d0,d7
                move.w  d7,BLTAMOD(a3)          ; mask modulo (one line of it per image line)
                bra.w   .cookie
.mkmask:
                endif
                ifnd    BUILD_1MB
                move.w  d4,d2                   ; BLTSIZE for one plane
                lsl.w   #6,d2
                or.w    d0,d2
                move.w  d6,d1
                add.w   d1,d1                   ; d1 = bytes per plane line of the graphics
                move.w  d1,d7
                mulu.w  #5,d7
                sub.w   d0,d7
                sub.w   d0,d7                   ; d7 = graphics modulo
                lea     CUSTOM,a3
                lea     MASKBUF,a5
                WAITBLIT                        ; mask = OR of planes 0-2 ...
                move.l  #$0FFE0000,BLTCON0(a3)
                move.l  #$FFFFFFFF,BLTAFWM(a3)
                move.w  d7,BLTAMOD(a3)
                move.w  d7,BLTBMOD(a3)
                move.w  d7,BLTCMOD(a3)
                move.w  #0,BLTDMOD(a3)
                move.l  a1,BLTAPTH(a3)
                lea     (a1,d1.w),a2
                move.l  a2,BLTBPTH(a3)
                adda.w  d1,a2
                move.l  a2,BLTCPTH(a3)
                move.l  a5,BLTDPTH(a3)
                move.w  d2,BLTSIZE(a3)
                adda.w  d1,a2
                WAITBLIT                        ; ... then planes 3-4
                move.w  #0,BLTAMOD(a3)
                move.l  a5,BLTAPTH(a3)
                move.l  a2,BLTBPTH(a3)
                adda.w  d1,a2
                move.l  a2,BLTCPTH(a3)
                move.l  a5,BLTDPTH(a3)
                move.w  d2,BLTSIZE(a3)
                ifd     BUILD_ONE
.cookie:
                endif
                move.w  #LINEBYTES,d7           ; screen modulo: next line of the same plane
                sub.w   d0,d7
                sub.w   d0,d7
                moveq   #4,d6
                movea.l a1,a2
.plane:         WAITBLIT                        ; cookie-cut: D = mask ? BOB : screen
                move.w  d3,BLTCON1(a3)
                move.w  d3,d4
                or.w    #$0FCA,d4
                move.w  d4,BLTCON0(a3)
                move.w  d7,BLTCMOD(a3)
                move.w  d7,BLTDMOD(a3)
                move.l  d5,BLTAFWM(a3)
                move.l  a5,BLTAPTH(a3)
                move.l  a2,BLTBPTH(a3)
                move.l  a4,BLTCPTH(a3)
                move.l  a4,BLTDPTH(a3)
                move.w  d2,BLTSIZE(a3)
                adda.w  d1,a2
                adda.w  #ROWBYTES,a4
                dbra    d6,.plane
                endif
.pdone:         INTSON
                movem.l (a7)+,d0-d7/a1-a5
                rts

;------------------------------------------------------------------------------
; ScrDrawScenery - a0 = pristine buffer: draw the shootable scenery (item type 1,
; the gravestones) into the background, as DrawSceneryOnRedraw does on a redraw:
; only on level 0 left of tile column $70 and level 2 left of $40. Drawing an item
; again over itself changes nothing, so every item is simply drawn again whenever
; new edges come in; ScrDrawBob clips it to the window.
;------------------------------------------------------------------------------
ScrDrawScenery:
                movem.l d0-d7/a1-a5,-(a7)
                move.w  buf_CamX(a0),d1
                asr.w   #4,d1                   ; tile column of the camera
                move.w  g_Level(a6),d0
                bne.b   .l2
                cmp.w   #$70,d1
                blt.b   .draw
                bra.b   .out
.l2:            cmp.w   #2,d0
                bne.b   .out
                cmp.w   #$40,d1
                bge.b   .out
.draw:          lea     g_Items(a6),a5
                moveq   #29,d7
.item:          tst.b   (a5)
                beq.b   .next
                cmpi.b  #1,$1A(a5)              ; O_Type 1
                bne.b   .next
                moveq   #-16,d1                 ; x = O_X - 16, width 32
                add.w   6(a5),d1
                moveq   #16,d2                  ; bottom = O_Y + 16 - SmallBobSizes (y offset, height)
                add.w   $A(a5),d2
                move.b  2(a5),d0                ; image = ItemBoxSizes[O_Param]
                ext.w   d0
                GAMEADDR ItemBoxSizes,a1
                move.b  (a1,d0.w),d0
                GAMEADDR SmallBobSizes,a1
                add.w   d0,d0
                move.b  (a1,d0.w),d3
                ext.w   d3
                sub.w   d3,d2
                move.b  1(a1,d0.w),d4
                ext.w   d4
                sub.w   d4,d2
                moveq   #32,d3
                lea     g_SmallBobSets(a6),a1   ; graphics g_SmallBobSets[image]
                add.w   d0,d0
                movea.l (a1,d0.w),a1
                bsr.w   ScrDrawBob
.next:          lea     $1C(a5),a5
                dbra    d7,.item
.out:           movem.l (a7)+,d0-d7/a1-a5
                rts
