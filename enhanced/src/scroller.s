;==============================================================================
; scroller.s - the enhanced game's own code that is not the original game's: the incremental
; scroller and its glue, faster BOB drawing, playfield text, the title menu. Included by
; gng_game.s (BUILD_ONE); tools/make_game.py puts the calls into the game's routines (see
; enhanced/docs/FEATURES.md for what each feature does):
;
;   the scroller (scroll.s, included here: ScrFullDraw, ScrScrollTo, ScrPrepare / ScrPrepareRow,
;   ScrRestore, ScrDrawBobs, ScrBuildCopper, CopyAll) and its glue, called in place of the
;   original's RedrawScreen, RedrawEntry, SwapScreens, SetBitplanePtrs, ShowBackBuffer,
;   RestoreBackground, DrawBobs, CameraJump:      EnhInit, Enh* below
;   BOB masks on 512K (one-plane masks, pre-masked copies): BuildLevelMasks, BobMaskFind
;   playfield text (PrintChar's playfield path): EnhPrintField, TextReplay, TextFlush, PrFast,
;   DrawStrip (a line of text as one pre-masked BOB)
;   the title menu and test page: EnhMenu (CheckGameStart), EnhTitleText (DrawCreditsScreen),
;   EnhShowMachine (the memory line), StopMusic (the sound test), EnhTitleSprite (the sprite
;   test's Arthur); JumpButton (the jump input), MenuPage, MenuItem
;   the timing build (RASTER_BUILD): EnhLogicStart / EnhLogicEnd, the RASTER macro
;
; Memory, in the program's memory map (it moves with the program; enhanced/docs/MEMORY.md):
;   SCREEN_0 + 0          pristine buffer   BUF_SIZE (47,120) bytes: the background, tiles and scenery
;            + BUF_SIZE   display buffer A
;            + 2*BUF_SIZE display buffer B
;   SCROLL_STORE          records, copper lists, restore lists, text queue, glyph cache,
;                         the machine description's copy (cleared by EnhInit)
; Between levels the progress map unpacks its picture into the original screen area (SCREEN_2 ..
; SCREEN_2 + $DA40) and a level's graphics files load into the buffers, while no playfield is
; shown; the game draws the level again afterwards.
;==============================================================================
BUF_P           equ     SCREEN_0
MASKBUF         equ     MASK_LINE_BUF   ; the original DrawBob's mask area (640 bytes)
SCROLL_STORE    equ     SCREEN_0+$24B98 ; (where the module was: above the progress map's picture)
RLIST_ENTRIES   equ     256             ; restore entries per display buffer
TEXTQ_MAX       equ     64              ; playfield characters remembered per frame (TextReplay)
TEXTQ_ENTRY     equ     14              ; font.l, ring.w, offset.l, shadow, ink, paper, pad
COPPER_BYTES    equ     128

; the timing build (RASTER_BUILD): COLOR00 shows which part of the frame is running
RASTER          macro
                ifd     RASTER_BUILD
                move.w  #\1,CUSTOM+$180
                endif
                endm

                include "scroll.s"

;------------------------------------------------------------------------------
; EnhInit - the three buffer records; A is drawn first, B is shown.
;------------------------------------------------------------------------------
EnhInit:
                movem.l d0/a0-a2,-(a7)
                lea     (SCROLL_STORE).l,a0     ; clear the storage
                move.w  #(ScrollStoreEnd-SCROLL_STORE)/2-1,d0
.clr:           clr.w   (a0)+
                dbra    d0,.clr
                lea     (GLYPH_CACHE).l,a0      ; no glyphs yet
                moveq   #GLYPH_SLOTS-1,d0
.gl:            move.l  #-1,(a0)
                lea     GLYPH_SIZE(a0),a0
                dbra    d0,.gl
                lea     MACHINE_INFO,a0         ; the bootblock's machine description, if it
                cmpi.l  #'GNGM',(a0)            ; left one (boot_patches.s): kept here, as its
                bne.b   .nomachine              ; address is only safe until the game starts
                lea     (EnhMachine).l,a1
                moveq   #7,d0
.mach:          move.l  (a0)+,(a1)+
                dbra    d0,.mach
.nomachine:     lea     (RecP).l,a2
                move.l  #BUF_P,buf_Base(a2)
                lea     (RecA).l,a0
                move.l  #BUF_P+BUF_SIZE,buf_Base(a0)
                lea     (CopperA).l,a1
                move.l  a1,buf_Copper(a0)
                lea     (RListA).l,a1
                bsr.b   .disp
                move.l  a0,DrawRec
                lea     (RecB).l,a0
                move.l  #BUF_P+2*BUF_SIZE,buf_Base(a0)
                lea     (CopperB).l,a1
                move.l  a1,buf_Copper(a0)
                lea     (RListB).l,a1
                bsr.b   .disp
                move.l  a0,ShowRec
                movem.l (a7)+,d0/a0-a2
                rts
; a0 = display record, a1 = its restore list storage, a2 = the pristine record
.disp:          move.l  a2,buf_Source(a0)
                move.l  a1,buf_RListBase(a0)
                move.l  a1,buf_RList(a0)
                lea     8*RLIST_ENTRIES(a1),a1
                move.l  a1,buf_RListEnd(a0)
                movea.l buf_Copper(a0),a1       ; an empty list until the first SetBitplanePtrs
                move.l  #$FFFFFFFE,(a1)
                clr.w   buf_Valid(a0)
                rts

; d0 = camera x, d1 = camera y (as the original: tile * 16 + fine)
GetCam:         move.w  g_ScrollTileX(a6),d0
                lsl.w   #4,d0
                add.w   g_ScrollFineX(a6),d0
                move.w  g_ScrollTileY(a6),d1
                lsl.w   #4,d1
                add.w   g_ScrollFineY(a6),d1
                rts

; the pristine buffer, then the buffer being drawn, brought to the camera
EnsureCurrent:  movem.l d0-d1/a0,-(a7)
                bsr.w   GetCam
                lea     (RecP).l,a0
                bsr.w   ScrScrollTo
                movea.l DrawRec(pc),a0
                bsr.w   ScrScrollTo
                movem.l (a7)+,d0-d1/a0
                rts

;------------------------------------------------------------------------------
EnhRedrawScreen:
                move.w  g_NewTileX(a6),d0
                lsl.w   #4,d0
                add.w   g_ScrollFineX(a6),d0
                move.w  g_NewTileY(a6),d1
                lsl.w   #4,d1
                add.w   g_ScrollFineY(a6),d1
                lea     (RecP).l,a0
                bsr.w   ScrFullDraw
                st.b    g_RedrawDone(a6)
                rts

;------------------------------------------------------------------------------
; EnhRedrawSame - NameEntry's redraw, at every cursor move: the camera has not moved, so the
; pristine buffer is kept when it already holds this window (the full draw was 255 tile
; blits a move; the buffers being drawn are still copied afresh from it, SwapScreens)
;------------------------------------------------------------------------------
EnhRedrawSame:
                movem.l d0-d5/a0,-(a7)
                lea     (RecP).l,a0
                tst.w   buf_Valid(a0)
                beq.b   .full
                move.w  g_NewTileX(a6),d0       ; the camera, as EnhRedrawScreen
                lsl.w   #4,d0
                add.w   g_ScrollFineX(a6),d0
                move.w  g_NewTileY(a6),d1
                lsl.w   #4,d1
                add.w   g_ScrollFineY(a6),d1
                cmp.w   buf_CamX(a0),d0
                bne.b   .full
                bsr.w   Window
                cmp.w   buf_ColL(a0),d2
                bne.b   .full
                cmp.w   buf_ColR(a0),d3
                bne.b   .full
                cmp.w   buf_RowB(a0),d4
                bne.b   .full
                cmp.w   buf_RowT(a0),d5
                bne.b   .full
                movem.l (a7)+,d0-d5/a0
                st.b    g_RedrawDone(a6)
                rts
.full:          movem.l (a7)+,d0-d5/a0
                bra.w   EnhRedrawScreen

;------------------------------------------------------------------------------
; EnhRedrawBackground - the background redraw RedrawEntry runs (in user mode) when the
; game asks for one: the camera code asks at almost every camera step, and the attract
; screens ask to clear their text. Neither needs drawing now: the pristine buffer is
; kept at the camera by every update, and text only goes into the display buffers.
; Only the 'done' flag the game waits for.
;------------------------------------------------------------------------------
EnhRedrawBackground:
                st.b    g_RedrawDone(a6)
                rts

;------------------------------------------------------------------------------
; EnhCameraJump - as CameraJump: the fine scroll becomes the offset from the new origin
; (clamped to -16..15) and the origin the new one. The original then fell into
; SwapScreens to rotate the four buffers; here the buffers simply follow the camera.
;------------------------------------------------------------------------------
EnhCameraJump:
                move.w  g_PendFineX(a6),d0
                move.w  d0,g_CamDeltaX(a6)
                bsr.b   .clamp
                move.w  d0,g_ScrollFineX(a6)
                move.w  g_PendFineY(a6),d0
                move.w  d0,g_CamDeltaY(a6)
                bsr.b   .clamp
                move.w  d0,g_ScrollFineY(a6)
                move.w  g_NewTileX(a6),g_ScrollTileX(a6)
                move.w  g_NewTileY(a6),g_ScrollTileY(a6)
                rts
.clamp:         cmp.w   #15,d0
                ble.b   .lo
                moveq   #15,d0
.lo:            cmp.w   #-16,d0
                bge.b   .ok
                moveq   #-16,d0
.ok:            rts

;------------------------------------------------------------------------------
EnhSwapScreens:
                move.w  g_NewTileX(a6),g_ScrollTileX(a6)
                move.w  g_NewTileY(a6),g_ScrollTileY(a6)
                lea     g_RestoreBufB(a6),a1    ; the original's restore lists, emptied as before
                clr.w   -(a1)
                move.l  a1,g_RestoreListA(a6)
                lea     g_SpawnQuota(a6),a1
                clr.w   -(a1)
                move.l  a1,g_RestoreListB(a6)
                lea     (RecA).l,a1
                clr.w   buf_Valid(a1)
                lea     (RecB).l,a1
                clr.w   buf_Valid(a1)
                lea     (TextQ).l,a1
                clr.w   (a1)
                clr.w   (TextDone).l
                rts

;------------------------------------------------------------------------------
EnhSetBitplanePtrs:
                RASTER  $FF0                    ; yellow: copper list
                bsr.w   EnsureCurrent
                bsr.w   GetCam
                movea.l DrawRec(pc),a0
                movea.l buf_Copper(a0),a1
                bsr.w   ScrBuildCopper
                RASTER  $888
                rts

;------------------------------------------------------------------------------
; EnhDisplayOff / EnhDisplayOn - the bitplanes off / on, only in the vertical blank (the beam
; above or below the display window), so no frame is shown cut in two. Off around a change of
; display whose screens are rewritten while they would be on show (the progress map unpacked
; into the scroller's buffers, the level drawn into them while the map is shown); on once the
; new copper list is in place. Each does nothing if the bitplanes are already off / on. The
; sprites and the colours are left as they are. Keep every register.
;------------------------------------------------------------------------------
EnhDisplayOff:  btst    #0,CUSTOM+$002          ; DMACONR bit 8: bitplanes on?
                beq.b   .out
                bsr.b   WaitBlank
                move.w  #$0100,CUSTOM+$096      ; DMACON: bitplanes off
.out:           rts

EnhDisplayOn:   btst    #0,CUSTOM+$002
                bne.b   .out
                bsr.b   WaitBlank
                move.w  #$8100,CUSTOM+$096      ; DMACON: bitplanes on
.out:           rts

; WaitBlank - until the beam is on a line above the display ($00-$2B) or below it ($125 on,
; PAL; an NTSC frame ends before, so it waits for the top there)
WaitBlank:      move.l  d0,-(a7)
.wait:          move.l  CUSTOM+$004,d0          ; VPOSR, VHPOSR: bit 16 V8, bits 15-8 V7-V0
                lsr.l   #8,d0
                andi.w  #$1FF,d0
                cmpi.w  #$2C,d0
                bcs.b   .out
                cmpi.w  #$125,d0
                bcs.b   .wait
.out:           move.l  (a7)+,d0
                rts

;------------------------------------------------------------------------------
EnhShowBackBuffer:
                cmpi.b  #PAGE_BOBS,(MenuPage).l ; the BOB test: its strip (bobviewer.s: ViewDraw)
                bne.b   .nobob
                jsr     (VIEWER_ORG+8).l
.nobob:         bsr.w   TextFlush               ; text not drawn yet goes in before it is shown
                RASTER  $0F0                    ; green: waiting for the copper interrupt
                lea     CUSTOM,a0
                movea.l DrawRec(pc),a1
                move.l  buf_Copper(a1),d1
.wait:          moveq   #$10,d0                 ; wait for the copper interrupt (line $44)
                and.w   INTREQR(a0),d0
                beq.b   .wait
                move.l  d1,COP2LCH(a0)          ; shown from the next frame
                move.w  #$0010,INTREQ(a0)
                move.l  ShowRec(pc),DrawRec     ; swap
                move.l  a1,ShowRec
                movea.l g_ScreenFront(a6),a1    ; and the original's pointers, as before
                move.l  g_ScreenBack(a6),g_ScreenFront(a6)
                move.l  a1,g_ScreenBack(a6)
                movea.l g_CopperBack(a6),a1
                move.l  g_CopperFront(a6),g_CopperBack(a6)
                move.l  a1,g_CopperFront(a6)
                movea.l g_SavePtr(a6),a1
                move.l  g_SavePtrB(a6),g_SavePtr(a6)
                move.l  a1,g_SavePtrB(a6)
                movea.l g_RestoreListA(a6),a1
                move.l  g_RestoreListB(a6),g_RestoreListA(a6)
                move.l  a1,g_RestoreListB(a6)
                movea.l g_SaveBufA(a6),a1
                move.l  g_SaveBufB(a6),g_SaveBufA(a6)
                move.l  a1,g_SaveBufB(a6)
                lea     (TextQ).l,a1            ; this frame's text is on screen now
                clr.w   (a1)
                clr.w   (TextDone).l
                RASTER  $888
                rts

;------------------------------------------------------------------------------
EnhRestoreBackground:
                RASTER  $F00                    ; red: new edges, restore
                bsr.w   EnsureCurrent
                movea.l DrawRec(pc),a0
                bsr.w   ScrRestore
                lea     (RecP).l,a0             ; the look-ahead column and row: the pristine
                bsr.w   ScrPrepare              ; buffer, then the buffer being drawn
                bsr.w   ScrPrepareRow
                movea.l DrawRec(pc),a0
                bsr.w   ScrPrepare
                bsr.w   ScrPrepareRow
                RASTER  $F80                    ; orange: text replay
                bsr.w   TextReplay
                RASTER  $888                    ; back to the logic's grey
                rts

;------------------------------------------------------------------------------
; the timing build's logic start / end (raster_patches.s)
EnhLogicStart:  move.w  #$0004,CUSTOM+INTREQ      ; INTF_SOFTINT
                RASTER  $888                    ; grey: game logic
                rts
EnhLogicEnd:    RASTER  $000                    ; black: idle
                movem.l (a7)+,d0-d7/a0-a5
                jmp     IrqExit1                ; (rte, with the interrupted a6)

;------------------------------------------------------------------------------
EnhDrawBobs:
                RASTER  $00F                    ; blue: BOBs
                bsr.w   EnsureCurrent
                move.l  g_SaveBufA(a6),g_SavePtr(a6)    ; as the original
                movea.l g_BlitListPtr(a6),a3
                lea     g_SaveBufA(a6),a5
                movea.l DrawRec(pc),a0
                bsr.w   ScrDrawBobs
                RASTER  $888
                rts

;------------------------------------------------------------------------------
; Playfield text. PrintChar on the playfield ($B0D6) jumps to EnhPrintField with a0 = the
; character's font data (MASK_BUF + 16 x character: 8 lines of 2 bytes), d1 = byte column,
; d2 = line (32 = top of the playfield when the fine scroll is 0); on the stack, as
; PrintChar pushed them: d1-d7, a0-a5, the return address.
;
; The character is not drawn there: it goes into the frame's text queue (TextQ), and is
; drawn once, either by TextReplay after the restore of the buffer being drawn (in play:
; the restore may cut through text, so text has always been drawn again there - the game
; prints its in-play messages every frame, before the restore, so drawing it when printed
; as well was wasted) or, for text printed after that or on screens with no restore (title,
; high scores, name entry), by TextFlush just before the buffer is shown. Only when the
; queue is full is a character drawn at once.
;
; Drawing (PrFast) goes straight into the ring buffer, from a glyph cache (GLYPH_CACHE, in the
; scroller's storage):
; per character and colours, 8 lines of a mask byte and the 5 plane bytes, worked out once
; as the original PrintBody does (plane p: shadow bit p where only font plane 0 is set, ink
; bit p where only plane 1 is, paper bit p where both are; transparent elsewhere).
;
; The original buffer line is d2 - 16 + fine Y; it shows world line 16*tileY + 255 - that,
; which is ring line (d2 - 16 + fineY - 16*tileY) & 255; byte b of an original line is byte
; 2*tileX + b in the corkscrew.
;------------------------------------------------------------------------------
GLYPH_SLOTS     equ     29              ; slot = character code mod 29 (a prime: 'TAKE A KEY FOR
                                        ; COMING IN !' takes 15 different slots)
GLYPH_SIZE      equ     4+8*6           ; tag (char, shadow, ink, paper), 8 x (mask, 5 planes)

EnhPrintField:
                move.w  d2,d0
                sub.w   #16,d0
                add.w   g_ScrollFineY(a6),d0
                move.w  g_ScrollTileY(a6),d3
                lsl.w   #4,d3
                sub.w   d3,d0
                andi.w  #$FF,d0
                move.w  d0,PrRing
                move.w  g_ScrollTileX(a6),d3
                add.w   d3,d3
                add.w   d1,d3
                addq.w  #2,d3
                ext.l   d3
                move.l  d3,PrOff
                move.b  g_TextShadow(a6),PrCol
                move.b  g_TextInk(a6),PrCol+1
                move.b  g_TextPaper(a6),PrCol+2
                lea     (TextQ).l,a1
                move.w  (a1),d0
                cmp.w   #TEXTQ_MAX,d0
                bhs.b   .now
                addq.w  #1,(a1)+                ; queue it
                mulu.w  #TEXTQ_ENTRY,d0
                adda.l  d0,a1
                move.l  a0,(a1)+                ; font data
                move.w  PrRing(pc),(a1)+
                move.l  PrOff(pc),(a1)+
                move.b  PrCol(pc),(a1)+
                move.b  PrCol+1(pc),(a1)+
                move.b  PrCol+2(pc),(a1)+
                bra.b   .ret
.now:           bsr.w   EnsureDraw              ; queue full: draw it now
                bsr.w   PrFast
.ret:           movem.l (a7)+,d1-d7             ; return as PrintChar does: the next column
                addq.w  #1,d1                   ; (after column $21, column 2 of the next line)
                cmp.w   #$22,d1
                bcs.b   .col
                moveq   #2,d1
                addq.w  #8,d2
.col:           movem.l (a7)+,a0-a5
                move.w  #$B4,d0                 ; (PrintBody leaves the line length in d0)
                rts

; EnsureDraw - the buffer being drawn brought to the camera, unless it is there already
; (EnsureCurrent costs a window check per buffer; text comes a character at a time)
EnsureDraw:     movem.l d0-d1/a0,-(a7)
                bsr.w   GetCam
                movea.l DrawRec(pc),a0
                tst.w   buf_Valid(a0)
                beq.b   .update
                cmp.w   buf_CamX(a0),d0
                bne.b   .update
                add.w   #16,d1
                cmp.w   buf_ClipY0(a0),d1
                beq.b   .ok
.update:        bsr.w   EnsureCurrent
.ok:            movem.l (a7)+,d0-d1/a0
                rts

;------------------------------------------------------------------------------
; TextReplay - after the restore of the buffer being drawn: draw the frame's queued
; characters, each with a restore entry, so that text the game stops printing goes away
; like a BOB. TextDone: how many of the queue are drawn.
;------------------------------------------------------------------------------
TextReplay:
                movem.l d0-d7/a0-a5,-(a7)
                lea     (TextQ).l,a4
                move.w  (a4)+,d5
                move.w  d5,(TextDone).l
                beq.w   .out
.next:          movea.l a4,a5                   ; d6 = the run of characters from here on one
                moveq   #1,d6                   ; line, one after the other, in one colour set
.run:           cmp.w   d5,d6
                beq.b   .rundone
                move.w  4(a5),d0                ; ring line
                cmp.w   4+TEXTQ_ENTRY(a5),d0
                bne.b   .rundone
                move.l  6(a5),d0                ; byte column + 1
                addq.l  #1,d0
                cmp.l   6+TEXTQ_ENTRY(a5),d0
                bne.b   .rundone
                move.l  10(a5),d0               ; colours
                move.l  10+TEXTQ_ENTRY(a5),d1
                clr.b   d0
                clr.b   d1
                cmp.l   d1,d0
                bne.b   .rundone
                lea     TEXTQ_ENTRY(a5),a5
                addq.w  #1,d6
                bra.b   .run
.rundone:       cmp.w   #STRIP_MIN,d6
                blt.b   .char
                cmp.w   #STRIP_MAX,d6
                bgt.b   .char
                bsr.w   DrawStrip               ; a line of text: one blit (a BOB)
                move.w  d6,d0
                mulu.w  #TEXTQ_ENTRY,d0
                adda.l  d0,a4
                sub.w   d6,d5
                bne.b   .next
                bra.b   .out
.char:          bsr.w   TextEntry               ; one character
                bsr.w   PrFast
                bsr.w   .restore
                subq.w  #1,d5
                bne.b   .next
.out:           movem.l (a7)+,d0-d7/a0-a5
                rts
; a restore entry for the character at PrRing / PrOff (its word, 8 lines; two entries
; when it crosses the ring's wrap)
.restore:       movea.l DrawRec(pc),a0
                movea.l buf_RList(a0),a1
                move.l  buf_RListEnd(a0),d0
                sub.l   a1,d0
                cmp.l   #16,d0
                blt.b   .full
                move.l  PrOff(pc),d1
                bclr    #0,d1                   ; its word
                add.l   buf_Base(a0),d1
                move.w  PrRing(pc),d2
                move.w  #RING_LINES,d3
                sub.w   d2,d3                   ; lines before the wrap
                moveq   #8,d4
                cmp.w   d4,d3
                bhs.b   .one
                move.w  d4,d6
                sub.w   d3,d6                   ; lines after it, from ring line 0
                move.l  d1,(a1)+
                move.w  d6,d7
                mulu.w  #5,d7
                lsl.w   #6,d7
                addq.w  #1,d7
                move.w  d7,(a1)+
                move.w  #ROWBYTES-2,(a1)+
                move.w  d3,d4
.one:           mulu.w  #LINEBYTES,d2
                add.l   d2,d1
                move.l  d1,(a1)+
                mulu.w  #5,d4
                lsl.w   #6,d4
                addq.w  #1,d4
                move.w  d4,(a1)+
                move.w  #ROWBYTES-2,(a1)+
                move.l  a1,buf_RList(a0)
.full:          rts

;------------------------------------------------------------------------------
; DrawStrip - a4 = the first of d6 queued characters on one line, one after the other, in
; one set of colours (the game's messages: 'TAKE A KEY FOR COMING IN !' every frame): drawn
; as one BOB (ScrDrawBob, pre-masked: one blit and one restore entry) from a strip made from
; their glyphs in TEXT_STRIP, made again only when the line changes (StripLen, StripCol,
; StripFonts). The strip is in the 1MB BOB format: per line, each plane's row followed by
; the mask's (1: the text, where either font plane is set).
;------------------------------------------------------------------------------
STRIP_MIN       equ     4               ; characters: shorter runs are drawn one by one
TEXT_STRIP      equ     SCREEN_2+$DA40  ; chip RAM the progress map's picture stops short of,
STRIP_MAXW      equ     (SCROLL_STORE-TEXT_STRIP)/(10*8*2)      ; up to SCROLL_STORE
STRIP_MAX       equ     2*STRIP_MAXW

DrawStrip:      movem.l d0-d7/a0-a5,-(a7)
                move.w  d6,d5
                addq.w  #1,d5
                lsr.w   #1,d5                   ; d5 = words per plane row
                move.l  10(a4),d7
                clr.b   d7                      ; d7 = colours
                cmp.w   StripLen(pc),d6         ; the strip made last time?
                bne.b   .make
                cmp.l   StripCol(pc),d7
                bne.b   .make
                movea.l a4,a5
                lea     StripFonts(pc),a1
                move.w  d6,d0
                subq.w  #1,d0
.cmp:           move.l  (a5),d1
                cmp.l   (a1)+,d1
                bne.b   .make
                lea     TEXTQ_ENTRY(a5),a5
                dbra    d0,.cmp
                bra.w   .draw
.make:          move.w  d6,StripLen             ; the key
                move.l  d7,StripCol
                lea     (TEXT_STRIP).l,a1       ; clear the strip: 8 lines x 10 rows x d5 words
                move.w  d5,d0
                mulu.w  #8*10,d0
                subq.w  #1,d0
.clr:           clr.w   (a1)+
                dbra    d0,.clr
                move.w  d5,d4
                add.w   d4,d4                   ; d4 = bytes per row
                movea.l a4,a5
                lea     StripFonts(pc),a2
                moveq   #0,d3                   ; character
.ch:            bsr.w   TextEntry0              ; a5 = entry -> a0 = font data, PrCol
                move.l  a0,(a2)+
                bsr.w   PrGlyph                 ; a3 = its glyph
                lea     (TEXT_STRIP).l,a1
                adda.w  d3,a1                   ; its byte in each row
                moveq   #7,d2
.gl:            move.b  (a3)+,d0
                not.b   d0                      ; the text's pixels
                movea.l a1,a0
                moveq   #4,d1
.gp:            move.b  (a3)+,(a0)              ; plane row
                adda.w  d4,a0
                move.b  d0,(a0)                 ; then the mask row
                adda.w  d4,a0
                dbra    d1,.gp
                adda.w  d4,a1                   ; next line: 10 rows on
                adda.w  d4,a1
                adda.w  d4,a1
                adda.w  d4,a1
                adda.w  d4,a1
                adda.w  d4,a1
                adda.w  d4,a1
                adda.w  d4,a1
                adda.w  d4,a1
                adda.w  d4,a1
                dbra    d2,.gl
                lea     TEXTQ_ENTRY(a5),a5
                addq.w  #1,d3
                cmp.w   d6,d3
                bne.b   .ch
.draw:          bsr.w   GetCam                  ; d0 = camera x, d1 = camera y
                move.w  4(a4),d2                ; ring line of the top line -> world line:
                addq.w  #1,d2                   ; the one = -1 - ring (mod 256) among the
                neg.w   d2                      ; 256 from the bottom visible line up
                add.w   #16,d1
                sub.w   d1,d2
                andi.w  #$FF,d2
                add.w   d1,d2                   ; top line
                subq.w  #7,d2                   ; bottom line
                move.l  6(a4),d1                ; byte column -> world x: 8 x byte - 16
                lsl.w   #3,d1
                sub.w   #16,d1
                move.w  d5,d3
                lsl.w   #4,d3                   ; width
                moveq   #8,d4
                movea.l DrawRec(pc),a0
                lea     (TEXT_STRIP).l,a1
                st.b    (BobForce).l            ; pre-masked as it is
                bsr.w   ScrDrawBob
                sf.b    (BobForce).l
                movem.l (a7)+,d0-d7/a0-a5
                rts

; TextEntry0 - as TextEntry, a5 = the entry (a5 kept)
TextEntry0:     move.l  a4,-(a7)
                movea.l a5,a4
                bsr.b   TextEntry
                movea.l (a7)+,a4
                rts

; TextEntry - a4 = a queue entry -> a0 = font data, PrRing, PrOff, PrCol; a4 = the next
TextEntry:      movea.l (a4)+,a0
                move.w  (a4)+,PrRing
                move.l  (a4)+,PrOff
                move.b  (a4)+,PrCol
                move.b  (a4)+,PrCol+1
                move.b  (a4)+,PrCol+2
                addq.l  #1,a4                   ; (pad: entries stay word aligned)
                rts

;------------------------------------------------------------------------------
; TextFlush - EnhShowBackBuffer, before the swap: draw the queued characters not drawn yet
; (printed after this frame's TextReplay, or on a screen with no restore)
;------------------------------------------------------------------------------
TextFlush:      movem.l d0-d7/a0-a5,-(a7)
                lea     (TextQ).l,a4
                move.w  (a4)+,d5
                move.w  (TextDone).l,d0
                sub.w   d0,d5                   ; not drawn yet
                ble.b   .out
                mulu.w  #TEXTQ_ENTRY,d0
                adda.l  d0,a4
                bsr.w   EnsureDraw
                subq.w  #1,d5
.char:          bsr.w   TextEntry
                bsr.w   PrFast
                dbra    d5,.char
.out:           movem.l (a7)+,d0-d7/a0-a5
                rts

;------------------------------------------------------------------------------
; PrGlyph - a0 = font data, colours PrCol -> a3 = its glyph (GLYPH_CACHE): 8 lines of the
; mask byte (1: background) and the 5 plane bytes; worked out if it is not there
;------------------------------------------------------------------------------
PrGlyph:        movem.l d0-d7/a0-a2/a4-a5,-(a7)
                move.l  a0,d0                   ; the character code ...
                sub.l   #MASK_BUF,d0
                lsr.l   #4,d0
                move.b  d0,d3                   ; ... and the colours: the glyph's tag
                lsl.l   #8,d3
                move.b  PrCol(pc),d3
                lsl.l   #8,d3
                move.b  PrCol+1(pc),d3
                lsl.l   #8,d3
                move.b  PrCol+2(pc),d3
                andi.l  #$FF,d0
                divu.w  #GLYPH_SLOTS,d0
                swap    d0                      ; code mod GLYPH_SLOTS
                mulu.w  #GLYPH_SIZE,d0
                lea     (GLYPH_CACHE).l,a2
                adda.l  d0,a2                   ; its slot
                cmp.l   (a2),d3
                beq.w   .done
                move.l  d3,(a2)                 ; not there: work it out
                lea     -16(a7),a7              ; 5 plane selectors, then 8 unions
                movea.l a7,a4
                lea     8(a7),a5
                move.b  PrCol(pc),d4            ; shadow
                move.b  PrCol+1(pc),d5          ; ink
                move.b  PrCol+2(pc),d6          ; paper
                moveq   #4,d7                   ; plane p: selector = shadow bit p + 2 x ink bit p
.sel:           moveq   #0,d0                   ; + 4 x paper bit p
                lsr.b   #1,d6
                addx.b  d0,d0
                lsr.b   #1,d5
                addx.b  d0,d0
                lsr.b   #1,d4
                addx.b  d0,d0
                move.b  d0,(a4)+
                dbra    d7,.sel
                subq.l  #5,a4
                lea     4(a2),a3
                lea     16(a0),a1               ; end of the font data
                moveq   #0,d4
                clr.b   (a5)                    ; union 0: nothing
.line:          move.b  (a0)+,d0                ; font plane 0
                move.b  (a0)+,d1                ; font plane 1
                move.b  d0,d2
                and.b   d1,d2                   ; C: both (paper)
                eor.b   d2,d0                   ; A: plane 0 only (shadow)
                eor.b   d2,d1                   ; B: plane 1 only (ink)
                move.b  d0,1(a5)                ; unions by selector: A, B, A|B, C, A|C, B|C, all
                move.b  d1,2(a5)
                move.b  d0,d3
                or.b    d1,d3
                move.b  d3,3(a5)
                move.b  d2,4(a5)
                move.b  d0,d3
                or.b    d2,d3
                move.b  d3,5(a5)
                move.b  d1,d3
                or.b    d2,d3
                move.b  d3,6(a5)
                or.b    d0,d3
                move.b  d3,7(a5)
                not.b   d3
                move.b  d3,(a3)+                ; mask: where the background shows
                move.b  (a4),d4                 ; the 5 planes
                move.b  (a5,d4.w),(a3)+
                move.b  1(a4),d4
                move.b  (a5,d4.w),(a3)+
                move.b  2(a4),d4
                move.b  (a5,d4.w),(a3)+
                move.b  3(a4),d4
                move.b  (a5,d4.w),(a3)+
                move.b  4(a4),d4
                move.b  (a5,d4.w),(a3)+
                cmpa.l  a1,a0
                bne.b   .line
                lea     16(a7),a7
.done:          lea     4(a2),a3
                movem.l (a7)+,d0-d7/a0-a2/a4-a5
                rts

;------------------------------------------------------------------------------
; PrFast - a0 = font data: the character at PrRing / PrOff in the colours PrCol, drawn into
; the buffer being drawn, transparent where the font is 0 (as PrintBody on the playfield)
;------------------------------------------------------------------------------
PrFast:         movem.l d0-d7/a0-a5,-(a7)
                bsr.w   PrGlyph
                WAITBLIT                        ; (a blit may still be writing this buffer: CopyAll)
                movea.l DrawRec(pc),a0
                move.l  buf_Base(a0),d0
                add.l   PrOff(pc),d0
                movea.l d0,a4                   ; this byte column on ring line 0
                move.w  PrRing(pc),d1
                move.w  d1,d0
                mulu.w  #LINEBYTES,d0
                lea     (a4,d0.l),a1            ; the first line
                moveq   #7,d7
.dl:            move.b  (a3)+,d2                ; mask
                move.b  (a1),d3
                and.b   d2,d3
                or.b    (a3)+,d3
                move.b  d3,(a1)
                move.b  ROWBYTES(a1),d3
                and.b   d2,d3
                or.b    (a3)+,d3
                move.b  d3,ROWBYTES(a1)
                move.b  2*ROWBYTES(a1),d3
                and.b   d2,d3
                or.b    (a3)+,d3
                move.b  d3,2*ROWBYTES(a1)
                move.b  3*ROWBYTES(a1),d3
                and.b   d2,d3
                or.b    (a3)+,d3
                move.b  d3,3*ROWBYTES(a1)
                move.b  4*ROWBYTES(a1),d3
                and.b   d2,d3
                or.b    (a3)+,d3
                move.b  d3,4*ROWBYTES(a1)
                lea     LINEBYTES(a1),a1
                addq.b  #1,d1                   ; next ring line: at the wrap, line 0
                bne.b   .nw
                movea.l a4,a1
.nw:            dbra    d7,.dl
                movem.l (a7)+,d0-d7/a0-a5
                rts

;------------------------------------------------------------------------------
; BOB graphics on 512K, made at level load (BuildLevelMasks) in the level data area:
;  * pre-masked images, as the 1MB cache (BuildMaskedGfx: every plane line followed by its
;    mask line), drawn in one blit: as many of the level's images as the memory up to
;    LEVEL_GFX_LIMIT holds, chosen in the order of GfxPriority;
;  * one-plane masks for the rest, drawn in 5 blits (the 2 blits that made the mask of
;    every BOB, every frame, are gone). A mask line is the OR of an image line's 5 plane
;    lines, so a region's masks are a fifth of its size and an image's mask is at
;        mask base + (graphics - region base) / 5.
; The game keeps its own image addresses (the frame tables are not changed): a converted
; image's pointer (g_BobSets, g_SmallBobSets, EShotGfxPtr, ItemGfxPtr) is a key in
; [KeyBase, KeyBase + KeyLen), and its masked copy is at KeyBase + 2 x (key - KeyBase), as
; the 1MB program doubles its offsets. Layout from g_LevelFileEnd (= KeyBase):
;    masked copies (2 x KeyLen) | the other sets' copies (region 2) | their masks |
;    the masks of the items, weapons and shots (region 1, always made)
; With the cache (PF_CACHE) every image is pre-masked and none of this runs.
;------------------------------------------------------------------------------
ESHOT_LEN       equ     $1234                   ; enemy shots
ITEM_LEN        equ     $1AC2+$EA6              ; items, weapons, effects (ITEM_GFX_BUF, ITEM_GFX2_BUF)
ITEMS_GFX_LEN   equ     ESHOT_LEN+ITEM_LEN      ; region 1: contiguous in memory from ESHOT_GFX_BUF
LEVEL_GFX_LIMIT equ     LEVEL_TOP               ; the level data's end ($7FB00): up to the bootblock's machine
                                                ; description (copied by EnhInit, so free after it, as is
                                                ; the loader above it); the supervisor stack comes down
                                                ; from $80000 (318 bytes deep at most, measured). The
                                                ; original's level data ended at $7F4DE

; BobMaskFind - ScrDrawBob, at the start: a1 = the image. Pre-masked (the cache, or a key of
; a converted image): BobMasked set and a1 = the masked copy. Otherwise BobMasked clear,
; BobGfx = a1 and BobMask = its one-plane mask (0: none; the BOB is then drawn the old way).
; Other registers kept.
BobMaskFind:    move.l  d0,-(a7)
                tst.b   (BobForce).l            ; (a text strip: DrawStrip)
                bne.b   .masked
                btst    #PF_CACHE,(Profile).l
                bne.b   .masked
                move.l  a1,d0
                sub.l   (KeyBase).l,d0          ; a converted image? (unsigned compare)
                cmp.l   (KeyLen).l,d0
                bcc.b   .plain
                adda.l  d0,a1                   ; KeyBase + 2 x (key - KeyBase)
.masked:        st.b    (BobMasked).l
                move.l  (a7)+,d0
                rts
.plain:         sf.b    (BobMasked).l
                move.l  a1,(BobGfx).l
                move.l  a1,d0
                sub.l   (MaskG2).l,d0           ; region 2: the level's other sets
                cmp.l   (MaskL2).l,d0           ; (unsigned: below the region is huge)
                bcs.b   .r2
                move.l  a1,d0
                sub.l   #ESHOT_GFX_BUF,d0       ; region 1: items, weapons, shots
                cmp.l   (MaskL1).l,d0
                bcc.b   .none
                divu.w  #5,d0
                swap    d0
                tst.w   d0                      ; (an image starts on a line: no remainder)
                bne.b   .none
                clr.w   d0
                swap    d0
                add.l   (MaskM1).l,d0
                bra.b   .set
.r2:            divu.w  #5,d0
                swap    d0
                tst.w   d0
                bne.b   .none
                clr.w   d0
                swap    d0
                add.l   (MaskM2).l,d0
                bra.b   .set
.none:          moveq   #0,d0
.set:           move.l  d0,(BobMask).l
                move.l  (a7)+,d0
                rts

; GfxPriority - the order in which images are pre-masked while memory lasts: the enemy shots
; (small, so the 4 blits saved are a large part of their cost), the small BOB sets, the
; dragon (9 BOBs at once), the items / weapons / effects, then the other enemy sets,
; smallest first. 0-20: enemy set, $20+n: small set n, $40: shots, $41: items; -1 ends.
GfxPriority:    dc.b    $40,$20,$21,$22,$23,$24,$25,$26,$27,$28,$29,12,$41
                dc.b    3,9,15,19,14,1,20,17,7,18,4,0,2,11,10,6,8,5,13,-1
                even

; BuildLevelMasks - LoadLevel, after BuildFrameTable (whose copies of the level's sets are
; replaced: every set of the level is marked 1 until it is placed): the sets are taken again from the files still in memory (enemy sets at
; SCREEN_0, small sets at SMALLBOB_LOAD) and laid out as above.
BuildLevelMasks:
                clr.w   StripLen                ; (the text strip is made again)
                btst    #PF_CACHE,(Profile).l
                bne.w   .out
                movem.l d0-d7/a0-a5,-(a7)
                clr.l   (MaskL1).l              ; (no lookups match while it is all being made)
                clr.l   (MaskL2).l
                clr.l   (KeyLen).l
                move.l  g_LevelFileEnd(a6),(KeyBase).l
                move.l  #ESHOT_GFX_BUF,(EShotGfxPtr).l
                move.l  #ITEM_GFX_BUF,(ItemGfxPtr).l
                ; ---- the room left with no image pre-masked: d5
                moveq   #0,d4                   ; the level's sets, total size
                lea     g_BobSets(a6),a4
                lea     (BobSetSizes).l,a0
                moveq   #21-1,d7
.sz1:           moveq   #0,d0
                move.w  (a0)+,d0
                tst.l   (a4)
                beq.b   .sz1n
                move.l  #1,(a4)                 ; in this level, not copied yet
                add.l   d0,d4
.sz1n:          addq.l  #4,a4
                dbra    d7,.sz1
                lea     g_SmallBobSets(a6),a4
                lea     (SmallBobSetSizes).l,a0
                moveq   #10-1,d7
.sz2:           moveq   #0,d0
                move.w  (a0)+,d0
                tst.l   (a4)
                beq.b   .sz2n
                move.l  #1,(a4)                 ; in this level, not copied yet
                add.l   d0,d4
.sz2n:          addq.l  #4,a4
                dbra    d7,.sz2
                move.l  d4,d0
                divu.w  #5,d0                   ; their masks
                andi.l  #$FFFF,d0
                add.l   d4,d0
                add.l   #ITEMS_GFX_LEN/5+4,d0   ; region 1's masks (+ a little)
                add.l   g_LevelFileEnd(a6),d0
                move.l  #LEVEL_GFX_LIMIT,d5
                sub.l   d0,d5                   ; (never negative: build_game.py checks)
                ; ---- pre-mask in GfxPriority's order what fits: a5 = next masked copy
                movea.l g_LevelFileEnd(a6),a5
                lea     GfxPriority(pc),a0
.pri:           moveq   #0,d0
                move.b  (a0)+,d0
                bmi.w   .copies
                movem.l d5/a0,-(a7)
                cmp.b   #$40,d0
                bcc.w   .region1
                cmp.b   #$20,d0
                bcc.b   .small
                lea     g_BobSets(a6),a4        ; enemy set d0
                lea     (BobSetSizes).l,a0
                lea     (BobSetOffsets).l,a1
                lea     (CacheSizesEnemyGfx).l,a3
                lea     (SCREEN_0).l,a2
                bra.b   .set
.small:         sub.b   #$20,d0                 ; small set d0
                lea     g_SmallBobSets(a6),a4
                lea     (SmallBobSetSizes).l,a0
                lea     (SmallBobSetOffsets).l,a1
                lea     (CacheSizesSmallBobs).l,a3
                lea     (SMALLBOB_LOAD).l,a2
.set:           add.w   d0,d0
                moveq   #0,d2
                move.w  (a0,d0.w),d2            ; d2 = size
                beq.w   .skip
                add.w   d0,d0
                adda.w  d0,a4
                tst.l   (a4)                    ; not in this level
                beq.w   .skip
                move.l  (a1,d0.w),d1            ; d1 = offset in the file
                move.l  d2,d3
                divu.w  #5,d3
                andi.l  #$FFFF,d3
                neg.l   d3
                add.l   d2,d3                   ; cost: the copy's size again less its mask
                cmp.l   (a7),d3
                bgt.w   .skip
                sub.l   d3,(a7)
                bsr.w   .r1key                  ; the key: KeyBase + KeyLen
                move.l  d0,(a4)
                adda.l  d1,a2                   ; the set in the file
                moveq   #0,d0                   ; its strips: skip those before it
                movea.l a3,a4
.find:          cmp.l   d1,d0
                bcc.b   .found
                bsr.w   .stripsize
                add.l   d4,d0
                addq.l  #4,a4
                bra.b   .find
.found:         movea.l a4,a3                   ; the set's first strip
                add.l   d2,d1                   ; its end in the file
                moveq   #-1,d7                  ; strips - 1
.count:         cmp.l   d1,d0
                bcc.b   .counted
                bsr.w   .stripsize
                add.l   d4,d0
                addq.l  #4,a4
                addq.w  #1,d7
                bra.b   .count
.counted:       add.l   d2,(KeyLen).l
                movea.l a2,a1
                movea.l a5,a2
                adda.l  d2,a5
                adda.l  d2,a5
                jsr     BuildMaskedGfx
                bra.w   .skip
.region1:       bne.w   .items                  ; $40: the enemy shots, $41: the items
                move.l  #2*ESHOT_LEN,d3
                cmp.l   (a7),d3
                bgt.w   .skip
                sub.l   d3,(a7)
                bsr.w   .r1key
                move.l  d0,(EShotGfxPtr).l
                add.l   #ESHOT_LEN,(KeyLen).l
                lea     (ESHOT_GFX_BUF).l,a1
                movea.l a5,a2
                lea     2*ESHOT_LEN(a5),a5
                lea     (CacheSizesEnemyShots).l,a3
                moveq   #3-1,d7
                jsr     BuildMaskedGfx
                bra.w   .skip
.items:         move.l  #2*ITEM_LEN,d3
                cmp.l   (a7),d3
                bgt.w   .skip
                sub.l   d3,(a7)
                bsr.w   .r1key
                move.l  d0,(ItemGfxPtr).l
                add.l   #ITEM_LEN,(KeyLen).l
                lea     (ITEM_GFX_BUF).l,a1
                movea.l a5,a2
                lea     (CacheSizesItems).l,a3
                moveq   #4-1,d7
                jsr     BuildMaskedGfx
                lea     (ITEM_GFX2_BUF).l,a1    ; then the second file, after it
                lea     2*$1AC2(a5),a2
                lea     (CacheSizesItemGfx2).l,a3
                moveq   #3-1,d7
                jsr     BuildMaskedGfx
                lea     2*ITEM_LEN(a5),a5
.skip:          movem.l (a7)+,d5/a0
                bra.w   .pri
                ; ---- the other sets: copied after the masked copies (region 2)
.copies:        move.l  a5,(MaskG2).l
                lea     g_BobSets(a6),a4
                lea     (BobSetSizes).l,a0
                lea     (BobSetOffsets).l,a1
                lea     (SCREEN_0).l,a2
                moveq   #21-1,d7
                bsr.w   .copy
                lea     g_SmallBobSets(a6),a4
                lea     (SmallBobSetSizes).l,a0
                lea     (SmallBobSetOffsets).l,a1
                lea     (SMALLBOB_LOAD).l,a2
                moveq   #10-1,d7
                bsr.w   .copy
                move.l  a5,d1
                sub.l   (MaskG2).l,d1
                move.l  d1,(MaskL2).l
                move.l  a5,(MaskM2).l
                movea.l a5,a2
                lea     g_BobSets(a6),a4        ; their masks: enemy sets ...
                lea     (BobSetOffsets).l,a5
                lea     (BobSetSizes).l,a0
                lea     (CacheSizesEnemyGfx).l,a3
                moveq   #21-1,d6
                moveq   #39-1,d5
                bsr.w   MasksForSets
                lea     g_SmallBobSets(a6),a4   ; ... small sets
                lea     (SmallBobSetOffsets).l,a5
                lea     (SmallBobSetSizes).l,a0
                lea     (CacheSizesSmallBobs).l,a3
                moveq   #10-1,d6
                moveq   #10-1,d5
                bsr.w   MasksForSets
                move.l  (MaskL2).l,d0           ; region 1 after region 2's masks
                divu.w  #5,d0
                andi.l  #$FFFF,d0
                add.l   (MaskM2).l,d0
                addq.l  #1,d0
                andi.w  #$FFFE,d0
                move.l  d0,(MaskM1).l
                movea.l d0,a2
                lea     (ESHOT_GFX_BUF).l,a1
                lea     (CacheSizesEnemyShots).l,a3
                moveq   #3-1,d7
                bsr.w   MakeMasks
                lea     (ITEM_GFX_BUF).l,a1
                lea     (CacheSizesItems).l,a3
                moveq   #4-1,d7
                bsr.w   MakeMasks
                lea     (ITEM_GFX2_BUF).l,a1
                lea     (CacheSizesItemGfx2).l,a3
                moveq   #3-1,d7
                bsr.w   MakeMasks
                move.l  a2,(MaskEnd).l          ; (the highest address the level's data uses)
                move.l  #ITEMS_GFX_LEN,(MaskL1).l
                movem.l (a7)+,d0-d7/a0-a5
.out:           rts
; d0 = the key of a region 1 image now pre-masked at a5 (KeyBase + KeyLen)
.r1key:         move.l  (KeyLen).l,d0
                add.l   g_LevelFileEnd(a6),d0
                rts
; a4 = a strip (width px, lines) -> d4 = its size: words x 2 x 5 x lines
.stripsize:     moveq   #15,d4
                add.w   (a4),d4
                lsr.w   #4,d4
                mulu.w  2(a4),d4
                mulu.w  #10,d4
                rts
; a4 = the sets' pointers, a0 = sizes, a1 = file offsets, a2 = the file, d7 = sets - 1:
; every set of the level not pre-masked (its pointer not a key) copied to a5
.copy:          moveq   #0,d0
                move.w  (a0)+,d0
                move.l  (a1)+,d1
                cmpi.l  #1,(a4)                 ; in this level and not pre-masked?
                bne.b   .cnext
                move.l  a5,(a4)
                lea     (a2,d1.l),a3
                lsr.w   #1,d0
                subq.w  #1,d0
                bmi.b   .cnext
.cw:            move.w  (a3)+,(a5)+
                dbra    d0,.cw
.cnext:         addq.l  #4,a4
                dbra    d7,.copy
                rts

; MasksForSets - a4 = the sets' copies (longs, 0: not in this level; below MaskG2: a key,
; pre-masked), a5 = their offsets in the graphics file (longs), a0 = their sizes (words),
; a3 = the file's strips (width px, lines), d6 = sets - 1, d5 = strips - 1. Each strip of a
; copied set gets its masks.
MasksForSets:
.set:           move.l  (a4)+,d0                ; the copy
                move.l  (a5)+,d1                ; its offset in the file
                moveq   #0,d2
                move.w  (a0)+,d2                ; its size
                tst.l   d0
                beq.b   .next
                cmp.l   (MaskG2).l,d0
                bcs.b   .next
                add.l   d1,d2                   ; its end in the file
                movem.l d5-d6/a0/a3-a5,-(a7)
                moveq   #0,d3                   ; strip offset in the file
.strip:         cmp.l   d1,d3
                bcs.b   .skip
                cmp.l   d2,d3
                bcc.b   .done
                movem.l d0-d3/d5/a3,-(a7)
                movea.l d0,a1
                adda.l  d3,a1
                suba.l  d1,a1                   ; the strip in the copy
                move.l  a1,d7
                sub.l   (MaskG2).l,d7
                divu.w  #5,d7
                andi.l  #$FFFF,d7
                add.l   (MaskM2).l,d7
                movea.l d7,a2                   ; its masks
                moveq   #0,d7                   ; one strip
                bsr.w   MakeMasks
                movem.l (a7)+,d0-d3/d5/a3
.skip:          moveq   #15,d4                  ; the strip's size: words x 2 x 5 x lines
                add.w   (a3)+,d4
                lsr.w   #4,d4
                mulu.w  (a3)+,d4
                mulu.w  #10,d4
                add.l   d4,d3
                dbra    d5,.strip
.done:          movem.l (a7)+,d5-d6/a0/a3-a5
.next:          dbra    d6,.set
                rts

; MakeMasks - a1 = graphics strips, a2 = where their masks go, a3 = the strips (width px,
; lines), d7 = strips - 1. Per image line: the OR of the 5 plane lines. a1, a2 and a3 end
; after the strips.
MakeMasks:
.strip:         moveq   #15,d4
                add.w   (a3)+,d4
                lsr.w   #4,d4                   ; words per plane line
                move.w  (a3)+,d5
                subq.w  #1,d5                   ; lines - 1
                move.w  d4,d6
                add.w   d6,d6                   ; bytes per plane line
                subq.w  #1,d4
.line:          move.w  d4,d3
.word:          movea.l a1,a4
                move.w  (a4),d0
                adda.w  d6,a4
                or.w    (a4),d0
                adda.w  d6,a4
                or.w    (a4),d0
                adda.w  d6,a4
                or.w    (a4),d0
                adda.w  d6,a4
                or.w    (a4),d0
                move.w  d0,(a2)+
                addq.l  #2,a1
                dbra    d3,.word
                move.w  d6,d0                   ; past planes 1-4 of this line
                add.w   d0,d0
                add.w   d0,d0
                adda.w  d0,a1
                dbra    d5,.line
                dbra    d7,.strip
                rts

;------------------------------------------------------------------------------
; The title menu (replaces the original's start and key instructions), chosen with the
; joystick (up / down move, fire chooses; left / right or fire change a setting) or keys:
;   title  (PAGE_TITLE):  PLAYER 1 START, PLAYER 2 START, INPUT - JUMP ON UP / BUTTON 2, TEST MENU
;   test   (PAGE_TEST):   the memory the bootblock found (EnhShowMachine), MUSIC (OFF, 00-14:
;                         left / right choose, fire plays or stops), EFFECT (00-29: fire plays),
;                         INPUT TEST, SPRITE TEST, CHEAT OFF / ON, EXIT
;   input test (PAGE_INPUT): the joystick's directions and both buttons, lit while held, and
;                         the last key pressed (its raw code)
;   sprite test (PAGE_SPRITE): Arthur's sprite frames (left / right: the frame, fire: the
;                         mirrored copy) on screen, with the frame's number
;   BOB test (PAGE_BOBS; 1MB of chip RAM or more only: the viewer file, bobviewer.s, is loaded
;                         at VIEWER_ORG by CacheGraphics, ViewerOn): the cached BOB graphics,
;                         left / right the strip, up / down scroll it
; The input, sprite and BOB tests go back to the test page with Esc, or with fire held 3 seconds.
; F1 / F2 start a 1 / 2 player game at once, J switches the jump input, C the cheat (as
; before). Any change draws the title again (GS_TITLE from step 0: double-buffered, and its
; 400-frame time-out to the high scores starts again; only the title page has a time-out). On
; the high-score page the joystick goes back to the title.
;------------------------------------------------------------------------------
PAGE_TITLE      equ     0
PAGE_TEST       equ     1
PAGE_INPUT      equ     2
PAGE_SPRITE     equ     3
PAGE_BOBS       equ     4
MENU_ITEMS      equ     4               ; title page
TEST_ITEMS      equ     7               ; test page: MUSIC, EFFECT, INPUT TEST, SPRITE TEST, BOB TEST,
TEST_INPUT      equ     2               ;   CHEAT, EXIT - the items' numbers (BOB TEST only with
TEST_SPRITE     equ     3               ;   ViewerOn: without it the items after it move up one)
TEST_BOBS       equ     4
TEST_CHEAT      equ     5
TUNES           equ     15              ; tunes 0-14 (TestMusic -1: off)
EFFECTS         equ     30              ; effects 0-29
HOLD_EXIT       equ     150             ; frames of fire held that leave a test (3 s)
KEY_ESC         equ     $45             ; raw key codes
KEY_F1          equ     $50
KEY_F2          equ     $51
KEY_J           equ     $26
KEY_C           equ     $33
ARTHUR_FRAMES   equ     42              ; Arthur's frames (0-39 have mirrored copies)
SPR_X           equ     113             ; the sprite test: Arthur's place from the camera
SPR_Y           equ     128             ;   (x from its left, y up from its bottom)

; EnhMenu - CheckGameStart (the title and high-score screens): -> d0 nonzero = start a game
; (g_TwoPlayer set); 0 = carry on
EnhMenu:
                move.b  (MenuPage).l,d0
                cmpi.b  #PAGE_INPUT,d0
                beq.w   .input
                cmpi.b  #PAGE_SPRITE,d0
                beq.w   .sprite
                cmpi.b  #PAGE_BOBS,d0
                beq.w   .bobs
                move.b  g_RawKey(a6),d1
                cmpi.b  #KEY_F1,d1
                beq.w   .one
                cmpi.b  #KEY_F2,d1
                beq.w   .two
                cmpi.b  #KEY_J,d1
                beq.w   .jump
                cmpi.b  #KEY_C,d1
                beq.w   .cheat
                bsr.w   .edges
                beq.w   .none
                cmpi.b  #GS_TITLE,g_GameState(a6)
                bne.w   .title                  ; the high scores: back to the menu
                lea     (MenuItem).l,a0
                moveq   #MENU_ITEMS,d4
                tst.b   (MenuPage).l
                beq.w   .main
                moveq   #TEST_ITEMS,d4
                tst.b   (ViewerOn).l
                bne.b   .main
                subq.w  #1,d4                   ; (no BOB TEST)
.main:          move.b  (a0),d1
                btst    #8,d2                   ; up
                beq.w   .down
                subq.b  #1,d1
                bpl.w   .moved
                move.b  d4,d1
                subq.b  #1,d1
                bra.w   .moved
.down:          btst    #0,d2
                beq.w   .choose
                addq.b  #1,d1
                cmp.b   d4,d1
                bcs.w   .moved
                moveq   #0,d1
.moved:         move.b  d1,(a0)
                bra.w   .redraw
.choose:        tst.b   (MenuPage).l
                bne.w   .testpg
                cmpi.b  #2,d1                   ; INPUT: fire, left or right switch it
                beq.w   .jump
                tst.w   d2                      ; the others: fire only
                bpl.w   .none
                tst.b   d1
                beq.w   .one
                cmpi.b  #1,d1
                beq.w   .two
                move.b  #PAGE_TEST,(MenuPage).l ; TEST MENU
                clr.b   (a0)
                bra.w   .redraw
.testpg:        bsr.w   .tid                    ; the item's number as if BOB TEST were there
                tst.b   d1
                beq.w   .music
                cmpi.b  #1,d1
                beq.w   .effect
                cmpi.b  #TEST_CHEAT,d1
                beq.w   .cheat                  ; CHEAT: fire, left or right
                tst.w   d2                      ; the others: fire only
                bpl.w   .none
                cmpi.b  #TEST_INPUT,d1
                beq.w   .toinput
                cmpi.b  #TEST_SPRITE,d1
                beq.w   .tosprite
                cmpi.b  #TEST_BOBS,d1
                beq.w   .tobobs
                bsr.w   StopMusic               ; EXIT: the music off,
                move.b  #3,(a0)                 ; back on TEST MENU
.title:         clr.b   (MenuPage).l
                bra.w   .redraw
.music:         lea     (TestMusic).l,a1        ; MUSIC: left / right choose (OFF, 0-14) ...
                moveq   #TUNES,d4
                bsr.w   .lr
                bne.w   .redraw
                tst.w   d2                      ; ... fire plays it (or stops the music)
                bpl.w   .none
                move.b  (a1),d1
                bmi.w   .stop
                moveq   #0,d0                   ; (PlayMusic: the tune in the low word only)
                move.b  d1,d0
                jsr     PlayMusic
                bra.w   .none
.stop:          bsr.w   StopMusic
                bra.w   .none
.effect:        lea     (TestEffect).l,a1       ; EFFECT: left / right choose, fire plays it
                moveq   #EFFECTS-1,d4
                bsr.w   .lr
                bne.w   .redraw
                tst.w   d2
                bpl.w   .none
                moveq   #0,d0
                move.b  (a1),d0
                jsr     PlaySfx
                bra.w   .none
.toinput:       move.b  #PAGE_INPUT,(MenuPage).l
                move.w  #-1,(InputShown).l      ; (draws at once)
                clr.b   (InputKey).l
                clr.b   (InputKeyShown).l
                bra.w   .test
.tosprite:      move.b  #PAGE_SPRITE,(MenuPage).l
                bra.w   .test
.tobobs:        move.b  #PAGE_BOBS,(MenuPage).l
.test:          clr.w   (HoldTime).l
                bra.w   .redraw
.one:           clr.b   g_TwoPlayer(a6)
                bra.w   .start
.two:           st.b    g_TwoPlayer(a6)
.start:         bsr.w   StopMusic
                clr.b   (MenuPage).l
                moveq   #1,d0
                rts
.jump:          not.b   (JumpButton).l
                bra.w   .redraw
.cheat:         not.b   g_CheatOn(a6)
                bra.w   .redraw

; the input test: show what is held, back with Esc or fire held
.input:         bsr.w   .leave
                bne.w   .back
                move.b  g_RawKey(a6),d1         ; a key: shown as its raw code
                beq.w   .in2
                move.b  d1,(InputKey).l
                clr.w   g_RawKey(a6)
.in2:           cmpi.b  #1,g_SubState(a6)       ; (not while the title is being drawn)
                bne.w   .none
                move.w  g_Joy(a6),d0
                andi.w  #$C303,d0               ; directions and both buttons
                move.b  (InputKey).l,d1
                cmp.w   (InputShown).l,d0
                bne.w   .in3
                cmp.b   (InputKeyShown).l,d1
                beq.w   .none
.in3:           move.w  d0,(InputShown).l       ; changed: show it
                move.b  d1,(InputKeyShown).l
                bra.w   .redraw

; the sprite test: left / right the frame, fire the mirrored copy; back with Esc or fire held
.sprite:        bsr.w   .leave
                bne.w   .back
                bsr.w   .edges
                beq.w   .none
                lea     (SprFrame).l,a1
                moveq   #ARTHUR_FRAMES-1,d4
                bsr.w   .lr
                bne.w   .redraw
                tst.w   d2
                bpl.w   .none
                not.b   (SprMirror).l
                bra.w   .redraw
;- the BOB test: the viewer takes the joystick (bobviewer.s); back with Esc or fire held
.bobs:          bsr.w   .leave
                bne.w   .back
                bsr.w   .edges
                beq.w   .none
                jsr     (VIEWER_ORG).l          ; ViewInput -> d0 = 1: changed
                tst.b   d0
                bne.w   .redraw
                bra.w   .none
.back:          move.b  #PAGE_TEST,(MenuPage).l ; back to the test page, on the test left
                clr.w   (HoldTime).l
                bra.w   .redraw

; d1 = a test page item -> d1 = its number as if BOB TEST were there (TEST_*)
.tid:           tst.b   (ViewerOn).l
                bne.b   .tid1
                cmpi.b  #TEST_BOBS,d1
                bcs.b   .tid1
                addq.b  #1,d1
.tid1:          rts
; d2 = the joystick bits newly pressed (b0 down, b1 right, b8 up, b9 left, b15 fire); Z if none
.edges:         move.w  g_JoyPrev(a6),d2
                not.w   d2
                and.w   g_Joy(a6),d2
                andi.w  #$8303,d2
                rts
; left / right: the byte at a1 one down / up, round from d4 (TUNES: from -1, OFF) -> Z if neither
.lr:            move.b  (a1),d0
                btst    #9,d2                   ; left
                beq.w   .lr1
                subq.b  #1,d0
                cmpi.b  #TUNES,d4
                beq.w   .lrm
                tst.b   d0
                bpl.w   .lrset
                move.b  d4,d0                   ; (round to the last)
                bra.w   .lrset
.lrm:           cmpi.b  #-2,d0                  ; (MUSIC: OFF is -1, below it the last tune)
                bne.w   .lrset
                moveq   #TUNES-1,d0
                bra.w   .lrset
.lr1:           btst    #1,d2                   ; right
                beq.w   .lrno
                addq.b  #1,d0
                cmpi.b  #TUNES,d4
                bne.w   .lr2
                cmp.b   d4,d0                   ; (MUSIC: after the last tune, OFF)
                blt.w   .lrset
                moveq   #-1,d0
                bra.w   .lrset
.lr2:           cmp.b   d4,d0
                bls.w   .lrset
                moveq   #0,d0
.lrset:         move.b  d0,(a1)
                moveq   #1,d0                   ; (NZ: changed)
                rts
.lrno:          moveq   #0,d0
                rts
; leave a test? Esc, or fire held for HOLD_EXIT frames -> NZ
.leave:         cmpi.b  #KEY_ESC,g_RawKey(a6)
                beq.w   .lvyes
                tst.w   g_Joy(a6)               ; fire held
                bpl.w   .lvno
                addq.w  #1,(HoldTime).l
                cmpi.w  #HOLD_EXIT,(HoldTime).l
                bcc.w   .lvyes
                moveq   #0,d0
                rts
.lvno:          clr.w   (HoldTime).l
                moveq   #0,d0
                rts
.lvyes:         clr.w   g_RawKey(a6)
                moveq   #1,d0
                rts
.redraw:        clr.w   g_RawKey(a6)
                move.b  #GS_TITLE,g_GameState(a6)       ; the title again
                clr.b   g_SubState(a6)
.none:          moveq   #0,d0
                rts

;------------------------------------------------------------------------------
; StopMusic - the test page: silence the tune playing. The driver has no command for it, so
; each music voice is pointed at an end of track ($67: the voice stops and its channel gets
; the silent sample at the next tick), as CmdPlayTune points them at a tune. The driver
; workspace is found from its code (CmdPlayTune's lea DriverVars(pc),a3 at entry + $1E: the
; same driver in every package). All registers kept.
;------------------------------------------------------------------------------
DRV_MUS0        equ     $004            ; the driver's music voices (sound/gng_music_*.s)
DRV_VOICE       equ     $068
VC_DATAPTR      equ     $000
VC_STACKPTR     equ     $01A
VC_DURATION     equ     $046
StopMusic:
                movem.l d0/a0-a2,-(a7)
                movea.l (VEC_SPURIOUS).w,a0     ; the driver's entry
                cmpi.w  #$47FA,$1E(a0)          ; lea d16(pc),a3 there?
                bne.b   .out
                lea     $20(a0),a0
                adda.w  (a0),a0                 ; DriverVars
                lea     DRV_MUS0(a0),a0
                move    sr,-(a7)
                ori     #$0700,sr               ; (not while the vertical blank ticks the driver)
                moveq   #3,d0
.voice:         move.l  #EndTrack,VC_DATAPTR(a0)
                clr.w   VC_DURATION(a0)
                lea     VC_DURATION(a0),a1
                move.l  a1,VC_STACKPTR(a0)
                lea     DRV_VOICE(a0),a0
                dbra    d0,.voice
                move    (a7)+,sr
.out:           movem.l (a7)+,d0/a0-a2
                rts
EndTrack:       dc.b    $67                     ; ENDTRACK
                even

;------------------------------------------------------------------------------
; EnhTitleSprite - the title's step 0, after the text (in place of clearing g_ArthurVisible):
; Arthur hidden, except on the sprite test: shown at the middle of the screen in the frame
; chosen (SprFrame; its mirrored copy ~n with SprMirror, frames 0-39), placed from the camera
; as ArthurSpritePos (called next) expects
;------------------------------------------------------------------------------
EnhTitleSprite:
                clr.b   g_ArthurVisible(a6)
                cmpi.b  #PAGE_SPRITE,(MenuPage).l
                bne.b   .out
                st.b    g_ArthurVisible(a6)
                clr.b   g_ArthurFlash(a6)
                move.w  g_ScrollTileX(a6),d0    ; the camera
                lsl.w   #4,d0
                add.w   g_ScrollFineX(a6),d0
                add.w   #SPR_X,d0
                move.w  d0,g_ArthurX(a6)
                move.w  g_ScrollTileY(a6),d0
                lsl.w   #4,d0
                add.w   g_ScrollFineY(a6),d0
                add.w   #SPR_Y,d0
                move.w  d0,g_ArthurY(a6)
                move.b  (SprFrame).l,d0
                tst.b   (SprMirror).l
                beq.b   .frame
                cmpi.b  #39,d0
                bhi.b   .frame
                not.b   d0                      ; ~n: the mirrored copy
.frame:         move.b  d0,g_ArthurFrame(a6)
                move.b  #$7F,g_ArthurShownFrame(a6)     ; (the vertical blank copies it in)
.out:           rts

; EnhTitleText - DrawCreditsScreen, after the logo: the page's text
EnhTitleText:
                movem.l d0-d7/a0-a5,-(a7)
                move.b  (MenuPage).l,d0
                beq.w   .titlepg
                cmpi.b  #PAGE_TEST,d0
                beq.w   .test
                cmpi.b  #PAGE_INPUT,d0
                beq.w   .input
                cmpi.b  #PAGE_BOBS,d0
                beq.w   .bobs
                bra.w   .sprite
.titlepg:       bsr.w   .credcol
                lea     TxtCreditProgram,a3
                moveq   #6,d1
                moveq   #$48,d2
                jsr     PrintString
                lea     TxtCreditGraphics,a3
                moveq   #6,d1
                moveq   #$58,d2
                jsr     PrintString
                lea     TxtCreditSound,a3
                moveq   #6,d1
                moveq   #$68,d2
                jsr     PrintString
                move.w  #$80,(ItemRow).l
                move.w  #4,(ItemStep).l         ; (16 lines apart)
                lea     TxtMenu1(pc),a1
                moveq   #0,d6                   ; item
                bsr.w   .item
                lea     TxtMenu2(pc),a1
                bsr.w   .item
                lea     TxtMenuInput(pc),a1
                lea     TxtJumpUp(pc),a2
                tst.b   (JumpButton).l
                beq.w   .in
                lea     TxtJumpB2(pc),a2
.in:            bsr.w   .item2
                lea     TxtMenuTest(pc),a1
                bsr.w   .item
                lea     TxtKeys(pc),a3          ; the keys in play
                moveq   #0,d5
                move.w  #$C2,d2
                bsr.w   .line
                bra.w   .out
.test:          lea     TxtMenuTest(pc),a3
                bsr.w   .heading
                bsr.w   EnhShowMachine          ; the memory, at $58
                move.w  #$6C,(ItemRow).l
                move.w  #3,(ItemStep).l         ; (seven items: 12 lines apart, see .item)
                moveq   #0,d6
                lea     TxtMusicItem(pc),a1     ; MUSIC  OFF / nn
                lea     TxtOff(pc),a2
                move.b  (TestMusic).l,d0
                bmi.w   .mus
                bsr.w   .number
.mus:           bsr.w   .item2
                lea     TxtEffect(pc),a1        ; EFFECT nn
                move.b  (TestEffect).l,d0
                bsr.w   .number
                bsr.w   .item2
                lea     TxtInputTest(pc),a1
                bsr.w   .item
                lea     TxtSpriteTest(pc),a1
                bsr.w   .item
                tst.b   (ViewerOn).l
                beq.b   .nobobs
                lea     TxtBobTest(pc),a1
                bsr.w   .item
.nobobs:        lea     TxtCheatItem(pc),a1
                lea     TxtOff(pc),a2
                tst.b   g_CheatOn(a6)
                beq.w   .ch
                lea     TxtOn(pc),a2
.ch:            bsr.w   .item2
                lea     TxtExit(pc),a1
                bsr.w   .item
                bra.w   .out
.input:         lea     TxtInputTest(pc),a3
                bsr.w   .heading
                move.w  g_Joy(a6),d7            ; (what is held now)
                lea     InputLabels(pc),a4
.inl:           move.w  (a4)+,d4                ; the bit, then column, row, text
                bmi.w   .inkey
                move.b  (a4)+,d1
                move.b  (a4)+,d2
                ext.w   d1
                andi.w  #$FF,d2
                move.w  (a4)+,d0
                lea     InputLabels(pc),a3
                adda.w  d0,a3
                btst    d4,d7
                sne     d5
                bsr.w   .col
                jsr     PrintString
                bra.w   .inl
.inkey:         lea     TxtKey(pc),a1           ; KEY $nn (the last key's raw code), or KEY --
                lea     (NumText).l,a2
                move.b  (InputKey).l,d0
                beq.w   .nokey
                move.b  #'$',(a2)+
                moveq   #2,d3
                bsr.w   .hex
                lea     (NumText).l,a2
                st      d5
                bra.w   .keyl
.nokey:         lea     TxtNone(pc),a2
                moveq   #0,d5
.keyl:          bsr.w   .compose
                move.w  #$B8,d2
                bsr.w   .line
                lea     TxtLeave(pc),a3
                moveq   #0,d5
                move.w  #$C4,d2
                bsr.w   .line
                bra.w   .out
.bobs:          lea     TxtBobTest(pc),a3       ; the BOB test: its name, the strip (bobviewer.s:
                bsr.w   .heading                ; ViewText; the strip is drawn by ViewDraw), the keys
                jsr     (VIEWER_ORG+4).l
                st      d5
                moveq   #$58,d2
                bsr.w   .line
                lea     TxtBobKeys(pc),a3
                moveq   #0,d5
                move.w  #$B8,d2
                bsr.w   .line
                lea     TxtLeave(pc),a3
                moveq   #0,d5
                move.w  #$C4,d2
                bsr.w   .line
                bra.w   .out
.sprite:        lea     TxtSpriteTest(pc),a3
                bsr.w   .heading
                move.b  (SprFrame).l,d0         ; ARTHUR FRAME nn (MIRRORED)
                bsr.w   .number
                lea     (OptText).l,a3
                lea     TxtFrame(pc),a1
                bsr.w   .append
                movea.l a2,a1
                bsr.w   .append
                tst.b   (SprMirror).l
                beq.w   .spr1
                cmpi.b  #39,(SprFrame).l
                bhi.w   .spr1
                lea     TxtMirrored(pc),a1      ; (only frames 0-39 have one)
                bsr.w   .append
.spr1:          clr.b   (a3)
                lea     (OptText).l,a3
                st      d5
                moveq   #$58,d2
                bsr.w   .line
                lea     TxtSpriteKeys(pc),a3
                moveq   #0,d5
                move.w  #$B8,d2
                bsr.w   .line
                lea     TxtLeave(pc),a3
                moveq   #0,d5
                move.w  #$C4,d2
                bsr.w   .line
.out:           movem.l (a7)+,d0-d7/a0-a5
                rts
.heading:       moveq   #-1,d5                  ; a3 = a page's name, centred at $48
                moveq   #$48,d2
                bra.w   .line
.credcol:       move.b  #$18,g_TextShadow(a6)   ; the credits' colours
                move.b  #$0D,g_TextInk(a6)
                move.b  #$1F,g_TextPaper(a6)
                rts
; d0 = a number 0-99 -> a2 = NumText, its two decimal digits
.number:        lea     (NumText).l,a2
                andi.w  #$FF,d0
                divu.w  #10,d0
                add.b   #'0',d0
                move.b  d0,(a2)+
                swap    d0
                add.b   #'0',d0
                move.b  d0,(a2)+
                clr.b   (a2)
                lea     (NumText).l,a2
                rts
; d0 = a byte -> d3 hex digits at a2 (d3 = 2)
.hex:           rol.b   #4,d0
                move.b  d0,d1
                andi.b  #$0F,d1
                add.b   #'0',d1
                cmpi.b  #'9',d1
                bls.w   .hx
                addq.b  #'A'-'9'-1,d1
.hx:            move.b  d1,(a2)+
                subq.w  #1,d3
                bne.w   .hex
                clr.b   (a2)
                rts
; item d6 (then d6 + 1): text a1 (.item2: and a2), at row ItemRow + 16 x d6, '> ... <' and in
; the credits' colours when it is the one chosen
.item:          suba.l  a2,a2
.item2:         lea     (OptText).l,a3
                moveq   #0,d5
                cmp.b   (MenuItem).l,d6
                seq     d5
                bne.w   .i1
                move.b  #'>',(a3)+
                move.b  #' ',(a3)+
.i1:            bsr.w   .append
                move.l  a2,d0
                beq.w   .i3
                movea.l a2,a1
                bsr.w   .append
.i3:            tst.b   d5
                beq.w   .i4
                move.b  #' ',(a3)+
                move.b  #'<',(a3)+
.i4:            clr.b   (a3)
                move.w  d6,d2                   ; row: ItemRow + d6 x (ItemStep x 4)
                mulu.w  (ItemStep).l,d2
                lsl.w   #2,d2
                add.w   (ItemRow).l,d2
                addq.w  #1,d6
                lea     (OptText).l,a3
                bra.w   .line
; a1 then a2 into OptText -> a3 = OptText
.compose:       lea     (OptText).l,a3
                bsr.w   .append
                movea.l a2,a1
                bsr.w   .append
                clr.b   (a3)
                lea     (OptText).l,a3
                rts
.append:        move.b  (a1)+,(a3)+             ; a1's text to a3 (a3 left on its end)
                bne.w   .append
                subq.l  #1,a3
                rts
; a3 = text, centred at row d2; d5 nonzero: the credits' colours, else the instructions' ones
.line:          movea.l a3,a0
.len:           tst.b   (a0)+
                bne.w   .len
                suba.l  a3,a0
                moveq   #33,d1                  ; (length + 1 counted)
                sub.w   a0,d1
                lsr.w   #1,d1
                bsr.w   .col
                jmp     PrintString
.col:           tst.b   d5                      ; the colours for d5
                bne.w   .credcol
                move.b  #$1F,g_TextShadow(a6)   ; the instructions' colours
                move.b  #$01,g_TextInk(a6)
                move.b  #$19,g_TextPaper(a6)
                rts

; the input test's labels: the g_Joy bit, the column, the row, the text (from InputLabels)
InputLabels:    dc.w    8
                dc.b    15,$70
                dc.w    TxtUp-InputLabels
                dc.w    9
                dc.b    8,$80
                dc.w    TxtLeft-InputLabels
                dc.w    1
                dc.b    19,$80
                dc.w    TxtRight-InputLabels
                dc.w    0
                dc.b    14,$90
                dc.w    TxtDown-InputLabels
                dc.w    15
                dc.b    8,$A4
                dc.w    TxtFire-InputLabels
                dc.w    14
                dc.b    18,$A4
                dc.w    TxtFire2-InputLabels
                dc.w    -1
TxtUp:          dc.b    'UP',0
TxtLeft:        dc.b    'LEFT',0
TxtRight:       dc.b    'RIGHT',0
TxtDown:        dc.b    'DOWN',0
TxtFire:        dc.b    'FIRE',0
TxtFire2:       dc.b    'FIRE 2',0
TxtKey:         dc.b    'KEY ',0
TxtNone:        dc.b    '--',0
TxtLeave:       dc.b    'Esc or hold fire: back',0
TxtMenu1:       dc.b    'PLAYER 1 START',0
TxtMenu2:       dc.b    'PLAYER 2 START',0
TxtMenuInput:   dc.b    'INPUT - ',0
TxtJumpUp:      dc.b    'JUMP ON UP',0
TxtJumpB2:      dc.b    'JUMP ON BUTTON 2',0
TxtMenuTest:    dc.b    'TEST MENU',0
TxtKeys:        dc.b    'SPACE pause   Esc abort',0
TxtMusicItem:   dc.b    'MUSIC  ',0
TxtEffect:      dc.b    'EFFECT ',0
TxtInputTest:   dc.b    'INPUT TEST',0
TxtSpriteTest:  dc.b    'SPRITE TEST',0
TxtFrame:       dc.b    'ARTHUR FRAME ',0
TxtMirrored:    dc.b    ' MIRRORED',0
TxtSpriteKeys:  dc.b    'left/right frame  fire mirror',0
TxtBobTest:     dc.b    'BOB TEST',0
TxtBobKeys:     dc.b    'left/right strip  up/down scroll',0
TxtCheatItem:   dc.b    'CHEAT ',0
TxtOff:         dc.b    'OFF',0
TxtOn:          dc.b    'ON',0
TxtExit:        dc.b    'EXIT',0
MenuPage:       dc.b    0                       ; PAGE_TITLE, PAGE_TEST, PAGE_INPUT, PAGE_SPRITE
MenuItem:       dc.b    0                       ; the item chosen on the page
JumpButton:     dc.b    0                       ; nonzero: jump on the joystick's second button
TestMusic:      dc.b    -1                      ; the test page's tune (-1: OFF) ...
TestEffect:     dc.b    0                       ; ... and effect
InputKey:       dc.b    0                       ; the input test: the last key's raw code (0: none)
InputKeyShown:  dc.b    0                       ;   ... and the one the page shows
SprFrame:       dc.b    0                       ; the sprite test: Arthur's frame ...
SprMirror:      dc.b    0                       ; ... and its mirrored copy
ViewerOn:       dc.b    0                       ; the BOB viewer is loaded (1MB of chip RAM: CacheGraphics)
                even
ItemRow:        dc.w    0                       ; the row of a page's first item ...
ItemStep:       dc.w    4                       ; ... and the lines between items / 4
InputShown:     dc.w    0                       ; the input test: the state the page shows
HoldTime:       dc.w    0                       ; frames fire has been held (a test's exit)
NumText:        dcb.b   4,0                     ; a number, made up
OptText:        dcb.b   40,0                    ; a line, made up

;------------------------------------------------------------------------------
; EnhShowMachine - the test page: one line with the memory the bootblock found, for example
;       CHIP 512K SLOW 512K FAST 0K
; Nothing is printed when the bootblock left no description (the original bootblock).
; Sizes: chip = its upper end; slow / fast = upper end - the 64K boundary below mh_Lower.
EnhShowMachine:
                movem.l d0-d7/a0-a5,-(a7)
                lea     (EnhMachine).l,a4
                cmpi.l  #'GNGM',(a4)
                bne.b   .out
                lea     (MachText).l,a3
                lea     TxtChip(pc),a1
                move.l  12(a4),d0               ; chip: upper end
                bsr.b   .item
                lea     TxtSlow(pc),a1
                movem.l 16(a4),d0-d1            ; slow: lower, upper
                bsr.b   .region
                lea     TxtFast(pc),a1
                movem.l 24(a4),d0-d1            ; fast
                bsr.b   .region
                clr.b   -(a3)                   ; (no space after the last item)
                lea     (MachText).l,a0
                suba.l  a0,a3                   ; length
                moveq   #32,d1                  ; centred on the 32 columns shown
                sub.w   a3,d1
                bpl.b   .fits
                moveq   #0,d1
.fits:          lsr.w   #1,d1                   ; column
                move.b  #$18,g_TextShadow(a6)   ; the credits' colours
                move.b  #$0D,g_TextInk(a6)
                move.b  #$1F,g_TextPaper(a6)
                lea     (MachText).l,a3
                moveq   #$58,d2                 ; under 'TEST MENU'
                jsr     PrintString
.out:           movem.l (a7)+,d0-d7/a0-a5
                rts
; d0 = mh_Lower, d1 = mh_Upper (0: none) -> d0 = size
.region:        exg     d0,d1
                tst.l   d0
                beq.b   .item
                clr.w   d1
                sub.l   d1,d0
; a1 = label, d0 = size in bytes: 'LABEL nnnK '
.item:          move.b  (a1)+,(a3)+
                bne.b   .item
                subq.l  #1,a3
                moveq   #10,d1
                lsr.l   d1,d0                   ; KB (< 655360: one divu per digit is enough)
                moveq   #0,d2                   ; digits pushed
.div:           divu.w  #10,d0
                swap    d0
                add.b   #'0',d0
                move.b  d0,-(a7)
                addq.w  #1,d2
                clr.w   d0
                swap    d0
                tst.l   d0
                bne.b   .div
.pop:           move.b  (a7)+,(a3)+
                subq.w  #1,d2
                bne.b   .pop
                move.b  #'K',(a3)+
                move.b  #' ',(a3)+
                rts

TxtChip:        dc.b    'CHIP ',0
TxtSlow:        dc.b    'SLOW ',0
TxtFast:        dc.b    'FAST ',0
                even

;------------------------------------------------------------------------------
                cnop    0,4
DrawRec:        dc.l    0               ; the buffer being drawn (the original's g_ScreenFront)
ShowRec:        dc.l    0               ; the buffer on screen
PrOff:          dc.l    0               ; the character being drawn: byte offset, ring line, colours
PrRing:         dc.w    0
PrCol:          dc.b    0,0,0,0         ; shadow, ink, paper (, pad)
StripLen:       dc.w    0               ; the text strip (DrawStrip): characters (0: none), ...
StripCol:       dc.l    0               ; ... colours, ...
StripFonts:     ds.l    STRIP_MAX       ; ... and their font data
BobForce:       dc.b    0               ; ScrDrawBob: the image is pre-masked as it is (BobMaskFind)
                even
                cnop    0,4
BobGfx:         dc.l    0               ; the image ScrDrawBob is drawing (BobMaskFind) ...
BobMask:        dc.l    0               ; ... and its one-plane mask (0: none)
KeyBase:        dc.l    0               ; pre-masked images' keys: [KeyBase, KeyBase + KeyLen) ...
KeyLen:         dc.l    0               ; ... their copies at KeyBase + 2 x (key - KeyBase)
MaskG2:         dc.l    0               ; region 2 (the level's sets): start, length, masks
MaskL2:         dc.l    0
MaskM2:         dc.l    0
MaskL1:         dc.l    0               ; region 1 (items, weapons, shots): length, masks
MaskM1:         dc.l    0
MaskEnd:        dc.l    0               ; end of the masks
BobMasked:      dc.b    0               ; this BOB is pre-masked: one blit (BobMaskFind)
                even
                cnop    0,4
                rsset   SCROLL_STORE            ; (cleared by EnhInit)
RecP            rs.b    buf_SIZEOF
RecA            rs.b    buf_SIZEOF
RecB            rs.b    buf_SIZEOF
CopperA         rs.b    COPPER_BYTES
CopperB         rs.b    COPPER_BYTES
RListA          rs.b    8*RLIST_ENTRIES
RListB          rs.b    8*RLIST_ENTRIES
TextQ           rs.b    2+TEXTQ_MAX*TEXTQ_ENTRY
TextDone        rs.w    1               ; how many of TextQ are drawn (TextReplay, TextFlush)
GLYPH_CACHE     rs.b    GLYPH_SLOTS*GLYPH_SIZE  ; playfield text glyphs (PrFast; tags -1 at start)
EnhMachine      rs.b    32              ; the bootblock's machine description (or zeros)
MachText        rs.b    48
ScrollStoreEnd  rs.b    0               ; (build_game.py checks: buffers < SCROLL_STORE, this <= CLEAR_AREA)
SCROLL_BUF_END  equ     BUF_P+3*BUF_SIZE
