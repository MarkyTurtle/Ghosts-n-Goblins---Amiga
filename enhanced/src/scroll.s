;==============================================================================
; scroll.s - incremental scroller for the enhanced build (prototype, step 1)
;
; Replaces the original full-screen redraw (RedrawScreen) with buffers that are
; updated one tile column / row at a time as the camera moves.
;
; Screen layout (see enhanced/docs/SCROLLER.md):
;  * Separate bitplanes, not line-interleaved. A corkscrew needs each plane to be a
;    continuous run of 36-byte rows, so that scrolling the bitplane pointers one word
;    to the right brings in the next row's first word; with line-interleaved planes
;    that word would belong to the next plane.
;  * Horizontal: corkscrew. A world tile column C is always at byte 2*(C+1) of a
;    row, so the whole level can scroll without moving data; each plane carries
;    COL_SLACK spare bytes for the drift.
;  * Vertical: a ring of RING_LINES lines. World line y (Y up) is ring line
;    (-1-y) & 255; the copper reloads the bitplane pointers where the ring wraps.
;  * Address of (column C, world line y) in plane p:
;       base + p*PLANE_SIZE + 2*(C+1) + 36*((-1-y) & 255)
;    The same for every buffer, so a pristine copy can be blitted straight across.
;
; The tile lookup (map, CellTiles, cell $67, the level-1 second bank) is the same as
; the original RedrawScreen ($BFDE), so the picture is identical.
;
; Calls (a6 = game globals, as everywhere in the game):
;   ScrFullDraw    a0 = buffer record, d0 = camera x, d1 = camera y
;   ScrScrollTo    a0 = buffer record, d0 = camera x, d1 = camera y
;   ScrBuildCopper a0 = buffer record, a1 = copper list, d0 = camera x, d1 = camera y
; Camera (as the original): x = world x of the leftmost visible pixel
; (g_ScrollTileX*16 + g_ScrollFineX); y = g_ScrollTileY*16 + g_ScrollFineY, so the
; visible playfield is world lines y+16 (bottom) .. y+239 (top).
;==============================================================================

ROWBYTES        equ     36              ; 288 px per plane row
RING_LINES      equ     256
COL_SLACK       equ     1040            ; corkscrew drift: 2 bytes per world column (levels <= 512 columns)
PLANE_SIZE      equ     ROWBYTES*RING_LINES+COL_SLACK
FETCH_BYTES     equ     34              ; 17 words fetched per line
DISPLAY_TOP     equ     $44             ; first playfield line (the 16 lines above are the HUD strip)
DISPLAY_END     equ     $124            ; first line after the display window

CUSTOM          equ     $DFF000
DMACONR         equ     $002
BLTCON0         equ     $040
BLTAFWM         equ     $044
BLTAPTH         equ     $050
BLTDPTH         equ     $054
BLTSIZE         equ     $058
BLTAMOD         equ     $064
BLTDMOD         equ     $066
BPLCON1         equ     $102
BPL1MOD         equ     $108
BPL2MOD         equ     $10A
BPL1PTH         equ     $0E0

; game data used (512K build addresses; labels in gng_main.s)
CELLTILES       equ     $1222C
g_MapPtr        equ     $092
g_Level         equ     $09A
g_LevelFileAddr equ     $116

; buffer record
                rsreset
buf_Base        rs.l    1               ; plane 0; plane p at + p*PLANE_SIZE
buf_ColL        rs.w    1               ; drawn tile columns, inclusive
buf_ColR        rs.w    1
buf_RowB        rs.w    1               ; drawn tile rows (Y up), inclusive
buf_RowT        rs.w    1
buf_Valid       rs.w    1               ; 0 = nothing drawn yet
buf_SIZEOF      rs.b    0

WAITBLIT        macro
.wb\@:  btst    #6,CUSTOM+DMACONR
        bne.b   .wb\@
        endm

;------------------------------------------------------------------------------
                org     $7A000
                bra.w   ScrFullDraw
                bra.w   ScrScrollTo
                bra.w   ScrBuildCopper

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
                movem.l d0-d7/a0-a5,-(a7)
                bsr.b   Window
                movem.w d2-d5,buf_ColL(a0)      ; ColL, ColR, RowB, RowT
                move.w  #1,buf_Valid(a0)
                move.w  d4,d0                   ; row
.row:           move.w  d2,d1                   ; first column
                move.w  d3,d6                   ; last column
                bsr.w   DrawRow
                addq.w  #1,d0
                cmp.w   d5,d0
                ble.b   .row
                movem.l (a7)+,d0-d7/a0-a5
                rts

;------------------------------------------------------------------------------
; Bring the buffer up to date for the camera: draw the columns and rows that came
; into view, one at a time. A big jump (or a first call) is a full draw.
;------------------------------------------------------------------------------
ScrScrollTo:
                movem.l d0-d7/a0-a5,-(a7)
                tst.w   buf_Valid(a0)
                beq.w   .full
                bsr.b   Window
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
; columns entering on the right
.right:         cmp.w   buf_ColR(a0),d3
                ble.b   .left
                addq.w  #1,buf_ColR(a0)
                move.w  buf_ColR(a0),d0
                bsr.w   DrawColumnAll
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
                move.w  buf_RowT(a0),d7
                sub.w   buf_RowB(a0),d7
                cmp.w   #15,d7
                ble.b   .down
                subq.w  #1,buf_RowT(a0)
                bra.b   .down
.done:          movem.l (a7)+,d0-d7/a0-a5
                rts
.full:          movem.l (a7)+,d0-d7/a0-a5
                bra.w   ScrFullDraw

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
; Source tile exactly as RedrawScreen; 5 blits, one per plane (16 lines x 1 word).
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
                lea     CELLTILES,a4
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
                mulu.w  #ROWBYTES,d4
                move.w  d1,d5
                addq.w  #1,d5
                add.w   d5,d5
                ext.l   d5
                add.l   d5,d4
                movea.l buf_Base(a0),a4
                adda.l  d4,a4
                ; ---- one blit per plane: A = the tile's plane (modulo 8), D = the plane
                lea     CUSTOM,a2
                WAITBLIT
                move.l  #$09F00000,BLTCON0(a2)  ; A -> D
                move.l  #$FFFFFFFF,BLTAFWM(a2)
                move.w  #8,BLTAMOD(a2)
                move.w  #ROWBYTES-2,BLTDMOD(a2)
                moveq   #4,d7
.plane:         WAITBLIT
                move.l  a3,BLTAPTH(a2)
                move.l  a4,BLTDPTH(a2)
                move.w  #(16<<6)|1,BLTSIZE(a2)
                addq.l  #2,a3
                adda.l  #PLANE_SIZE,a4
                dbra    d7,.plane
                movem.l (a7)+,d0-d7/a2-a4
                rts

;------------------------------------------------------------------------------
; ScrBuildCopper - the playfield part of the copper list (jumped to at line $44):
; bitplane pointers, modulos and fine scroll for the camera, and a pointer reload
; where the 256-line ring wraps.
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
                mulu.w  #ROWBYTES,d6
                move.l  d5,d7
                add.l   d6,d7                   ; d7 = top line
                bsr.b   .pointers
                move.l  #(BPL1MOD<<16)|(ROWBYTES-FETCH_BYTES),(a1)+
                move.l  #(BPL2MOD<<16)|(ROWBYTES-FETCH_BYTES),(a1)+
                move.w  #BPLCON1,(a1)+
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
                add.l   #PLANE_SIZE,d7
                dbra    d1,.pp
                rts
