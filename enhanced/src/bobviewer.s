;==============================================================================
; bobviewer.s - the test page's BOB viewer (BOB TEST), for machines with 1MB of chip RAM or
; more. It is a file of its own (FID_VIEWER), assembled for VIEWER_ORG - the upper chip RAM
; after the graphics caches - with the program's symbols (viewer_syms.i, which build_game.py
; writes from the program's listing), and loaded only there (CacheGraphics, PF_CACHE): a plain
; 512K machine has none of it. The program calls it through the three branches at its start
; and shows the item only when it is loaded (ViewerOn).
;
; It shows the cached BOB graphics as they are drawn in the game: pre-masked (a mask line after
; every plane line, BuildMaskedGfx), one blit (ScrDrawBob), from the caches the 1MB profile
; builds at start-up - 59 strips in five groups (the enemy sets, the small BOBs, the enemy
; shots, the items and weapons, their tail), each a column of frames as wide as the strip
; (CacheSizes*). Left / right choose the strip, up / down scroll it (VIEW_STEP lines); a window
; of VIEW_LINES lines is drawn in the middle of the title screen.
;==============================================================================
                include "viewer_syms.i"
                org     VIEWER_ORG

                bra.w   ViewInput               ; +0: d2 = joystick bits newly pressed -> d0 = 1: draw again
                bra.w   ViewText                ; +4: -> a3 = the strip's line of text
                bra.w   ViewDraw                ; +8: the strip into the buffer being drawn

VIEW_LINES      equ     64                      ; the window: lines shown ...
VIEW_STEP       equ     16                      ; ... and the scroll step
VIEW_CX         equ     136                     ; its middle, from the camera's left
VIEW_TOP        equ     154                     ; its top line, up from the camera's bottom
VIEW_STRIPS     equ     39+10+3+4+3

; the groups: cached images, their sizes (width, height words), the number of strips, the name
ViewGroups:     dc.l    ENEMY_GFX_CACHE,CacheSizesEnemyGfx
                dc.w    39,VnEnemies-ViewGroups
                dc.l    SMALLBOB_CACHE,CacheSizesSmallBobs
                dc.w    10,VnSmall-ViewGroups
                dc.l    MESHOT_GFX_BUF,CacheSizesEnemyShots
                dc.w    3,VnShots-ViewGroups
                dc.l    MITEM_GFX_BUF,CacheSizesItems
                dc.w    4,VnItems-ViewGroups
                dc.l    MITEM_GFX2_BUF,CacheSizesItemGfx2
                dc.w    3,VnItems2-ViewGroups
VnEnemies:      dc.b    'ENEMIES ',0
VnSmall:        dc.b    'SMALL ',0
VnShots:        dc.b    'SHOTS ',0
VnItems:        dc.b    'ITEMS ',0
VnItems2:       dc.b    'ITEMS2 ',0
                even
ViewSel:        dc.w    0                       ; the strip shown (0 .. VIEW_STRIPS-1)
ViewTop:        dc.w    0                       ; its first line shown
ViewLine:       dcb.b   32,0                    ; the line of text, made up

;------------------------------------------------------------------------------
; ViewFind - the strip ViewSel -> a1 = its cached image, d3 = width (px), d4 = height,
; a2 = its group, d5 = its number in the group; d6 = bytes a line
;------------------------------------------------------------------------------
ViewFind:       lea     ViewGroups(pc),a2
                move.w  ViewSel(pc),d5
.group:         cmp.w   8(a2),d5
                bcs.b   .in
                sub.w   8(a2),d5
                lea     12(a2),a2
                bra.b   .group
.in:            movea.l (a2),a1
                movea.l 4(a2),a3
                moveq   #0,d0
.skip:          move.w  (a3)+,d3                ; width, height
                move.w  (a3)+,d4
                moveq   #15,d6                  ; bytes a line: (width + 15) / 16 words, 10 rows
                add.w   d3,d6                   ; (5 planes, each followed by the mask)
                lsr.w   #4,d6
                mulu.w  #20,d6
                cmp.w   d5,d0
                beq.b   .found
                move.w  d6,d1
                mulu.w  d4,d1
                adda.l  d1,a1                   ; the strips before it
                addq.w  #1,d0
                bra.b   .skip
.found:         rts

;------------------------------------------------------------------------------
; ViewInput - d2 = the joystick's newly pressed bits (b0 down, b1 right, b8 up, b9 left) ->
; d0 = 1 if the strip or its scroll changed (the title is drawn again), else 0
;------------------------------------------------------------------------------
ViewInput:      movem.l d1-d7/a0-a3,-(a7)
                lea     ViewSel(pc),a0
                move.w  (a0),d1
                btst    #1,d2                   ; right: the next strip
                beq.b   .left
                addq.w  #1,d1
                cmp.w   #VIEW_STRIPS,d1
                bcs.b   .sel
                moveq   #0,d1
                bra.b   .sel
.left:          btst    #9,d2                   ; left: the one before
                beq.b   .down
                subq.w  #1,d1
                bpl.b   .sel
                move.w  #VIEW_STRIPS-1,d1
.sel:           move.w  d1,(a0)
                clr.w   ViewTop-ViewSel(a0)
                bra.b   .yes
.down:          bsr.w   ViewFind                ; d4 = height
                lea     ViewTop(pc),a0
                move.w  (a0),d1
                btst    #0,d2                   ; down: further down the strip
                beq.b   .up
                add.w   #VIEW_STEP,d1
                cmp.w   d4,d1
                bcc.b   .no
                bra.b   .top
.up:            btst    #8,d2                   ; up: back up it
                beq.b   .no
                sub.w   #VIEW_STEP,d1
                bmi.b   .no
.top:           move.w  d1,(a0)
.yes:           moveq   #1,d0
                bra.b   .out
.no:            moveq   #0,d0
.out:           movem.l (a7)+,d1-d7/a0-a3
                rts

;------------------------------------------------------------------------------
; ViewText -> a3 = 'GROUP nn  www x hhh  LINE lll', the strip shown and where in it
;------------------------------------------------------------------------------
ViewText:       movem.l d0-d7/a0-a2,-(a7)
                bsr.w   ViewFind
                lea     ViewLine(pc),a3
                lea     ViewGroups(pc),a0
                adda.w  10(a2),a0               ; the group's name
.name:          move.b  (a0)+,(a3)+
                bne.b   .name
                subq.l  #1,a3
                move.w  d5,d0                   ; its number
                moveq   #2,d1
                bsr.b   .dec
                move.b  #' ',(a3)+
                move.b  #' ',(a3)+
                move.w  d3,d0                   ; width x height
                moveq   #0,d1
                bsr.b   .dec
                move.b  #'x',(a3)+
                move.w  d4,d0
                moveq   #0,d1
                bsr.b   .dec
                move.b  #' ',(a3)+
                move.b  #' ',(a3)+
                move.b  #'L',(a3)+
                move.w  ViewTop(pc),d0          ; the first line shown
                moveq   #0,d1
                bsr.b   .dec
                clr.b   (a3)
                lea     ViewLine(pc),a3
                movem.l (a7)+,d0-d7/a0-a2
                rts
; d0 = a number (< 1000) in decimal at a3, at least d1 digits
.dec:           moveq   #0,d7                   ; digits pushed
.div:           ext.l   d0
                divu.w  #10,d0
                swap    d0
                add.b   #'0',d0
                move.b  d0,-(a7)
                addq.w  #1,d7
                clr.w   d0
                swap    d0
                tst.w   d0
                bne.b   .div
.pad:           cmp.w   d1,d7                   ; leading zeros
                bcc.b   .pop
                move.b  #'0',(a3)+
                subq.w  #1,d1
                bra.b   .pad
.pop:           move.b  (a7)+,(a3)+
                subq.w  #1,d7
                bne.b   .pop
                rts

;------------------------------------------------------------------------------
; ViewDraw - EnhShowBackBuffer, on the BOB test: the strip's window into the buffer being
; drawn (brought to the camera first), one pre-masked blit, before the page's text goes in
;------------------------------------------------------------------------------
ViewDraw:       movem.l d0-d7/a0-a5,-(a7)
                bsr.w   ViewFind                ; a1, d3 width, d4 height, d6 bytes a line
                move.w  ViewTop(pc),d0
                mulu.w  d6,d0
                adda.l  d0,a1                   ; from the first line shown
                sub.w   ViewTop(pc),d4
                cmp.w   #VIEW_LINES,d4
                bls.b   .h
                moveq   #VIEW_LINES,d4
.h:             jsr     EnsureDraw
                movea.l (DrawRec).l,a0
                move.l  buf_RListBase(a0),buf_RList(a0) ; (nothing else is drawn on the title)
                jsr     GetCam                  ; d0 = camera x, d1 = camera y
                move.w  d3,d5
                lsr.w   #1,d5
                neg.w   d5
                add.w   #VIEW_CX,d5
                add.w   d0,d5                   ; x: the strip's middle at VIEW_CX
                move.w  d1,d2
                add.w   #VIEW_TOP+1,d2
                sub.w   d4,d2                   ; y of its bottom line (Y up): its top at VIEW_TOP
                move.w  d5,d1
                jsr     ScrDrawBob              ; a0 buffer, a1 image, d1 x, d2 y, d3 w, d4 h
                movem.l (a7)+,d0-d7/a0-a5
                rts
ViewEnd:
