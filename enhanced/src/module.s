;==============================================================================
; module.s - the enhanced build's scroller module.
;
; Loaded by the patched main program (patches.s: Start loads it from its own track
; with LoadFile, before the copyright screen) to MODULE_ORG, in the screen area the
; four original buffers used to fill. The main program's display routines are patched
; to jump here (jump table below); the rest of the game is unchanged.
;
; Memory (512K build):
;   $37468  pristine buffer   47,120 bytes  (the background: tiles and scenery)
;   $42B78  display buffer A  47,120
;   $4E288  display buffer B  47,120        (ends $59998)
;   $5C000  this module: code, records, copper lists, restore lists, PrintChar scratch
; The four original screen pointers (g_ScreenFront ...) keep their values; only the
; progress map still uses them (as raw memory: it unpacks its picture at $4DC68 ..
; $5B6A8, below this module), and the level loader still stages the enemy graphics
; at $37468 .. $544AA. Both happen while no playfield is shown, and the game redraws
; (RedrawScreen) afterwards.
;
; How the original routines map onto the scroller:
;   RedrawScreen     draw the pristine buffer at g_NewTileX/Y (full draw, + scenery);
;                    sets g_RedrawDone as before
;   SwapScreens      adopt g_NewTileX/Y; both display buffers become 'unknown' (they
;                    are copied from the pristine buffer when next used - not here,
;                    because the progress map calls SwapScreens with its picture in
;                    the same memory)
;   RestoreBackground  bring the pristine buffer and the buffer being drawn to the
;                    camera (new edges only), then undo that buffer's BOBs
;   DrawBobs         the game's draw list into the buffer being drawn
;   SetBitplanePtrs  build the buffer's copper list (pointers, ring wrap, fine scroll)
;   ShowBackBuffer   wait for the copper interrupt, show it, swap the two buffers
;   PrintChar        (playfield text) into the buffer being drawn, through the ring
;   CameraJump       the original's origin switch, without rotating buffers
;   RedrawEntry      (the background redraw the camera asks for) nothing to draw: done
; The camera logic itself is the original's, so the tile origin (g_ScrollTileX/Y, which
; also selects the enemy spawn zones) moves exactly as before.
;==============================================================================
                include "gng_equates.i"
                include "orig_syms.i"   ; the original program's labels (generated)

MODULE_ORG      equ     $5C000
MASKBUF         equ     $371E8          ; the original DrawBob's mask area (640 bytes)
BUF_P           equ     $37468
RLIST_ENTRIES   equ     256             ; restore entries per display buffer
COPPER_BYTES    equ     128

                org     MODULE_ORG
; ---- jump table (patches.s jumps to these)
                bra.w   EnhInit                 ; +0  set up the records (called once by Start)
                bra.w   EnhRedrawScreen         ; +4
                bra.w   EnhSwapScreens          ; +8
                bra.w   EnhSetBitplanePtrs      ; +12
                bra.w   EnhShowBackBuffer       ; +16
                bra.w   EnhRestoreBackground    ; +20
                bra.w   EnhDrawBobs             ; +24
                bra.w   EnhPrintField           ; +28 (jumped to from inside PrintChar)
                bra.w   EnhRedrawBackground     ; +32
                bra.w   EnhCameraJump           ; +36

                include "scroll.s"

;------------------------------------------------------------------------------
; EnhInit - the three buffer records; A is drawn first, B is shown.
;------------------------------------------------------------------------------
EnhInit:
                movem.l d0/a0-a2,-(a7)
                lea     ModuleFileEnd(pc),a0    ; clear the storage
                move.w  #(ModuleEnd-ModuleFileEnd)/2-1,d0
.clr:           clr.w   (a0)+
                dbra    d0,.clr
                lea     RecP(pc),a2
                move.l  #BUF_P,buf_Base(a2)
                lea     RecA(pc),a0
                move.l  #BUF_P+BUF_SIZE,buf_Base(a0)
                lea     CopperA(pc),a1
                move.l  a1,buf_Copper(a0)
                lea     RListA(pc),a1
                bsr.b   .disp
                move.l  a0,DrawRec
                lea     RecB(pc),a0
                move.l  #BUF_P+2*BUF_SIZE,buf_Base(a0)
                lea     CopperB(pc),a1
                move.l  a1,buf_Copper(a0)
                lea     RListB(pc),a1
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
                lea     RecP(pc),a0
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
                lea     RecP(pc),a0
                bsr.w   ScrFullDraw
                st.b    g_RedrawDone(a6)
                rts

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
                lea     RecA(pc),a1
                clr.w   buf_Valid(a1)
                lea     RecB(pc),a1
                clr.w   buf_Valid(a1)
                rts

;------------------------------------------------------------------------------
EnhSetBitplanePtrs:
                bsr.w   EnsureCurrent
                bsr.w   GetCam
                movea.l DrawRec(pc),a0
                movea.l buf_Copper(a0),a1
                bra.w   ScrBuildCopper

;------------------------------------------------------------------------------
EnhShowBackBuffer:
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
                rts

;------------------------------------------------------------------------------
EnhRestoreBackground:
                bsr.w   EnsureCurrent
                movea.l DrawRec(pc),a0
                bra.w   ScrRestore

;------------------------------------------------------------------------------
EnhDrawBobs:
                bsr.w   EnsureCurrent
                move.l  g_SaveBufA(a6),g_SavePtr(a6)    ; as the original
                movea.l g_BlitListPtr(a6),a3
                lea     g_SaveBufA(a6),a5
                movea.l DrawRec(pc),a0
                bra.w   ScrDrawBobs

;------------------------------------------------------------------------------
; EnhPrintField - PrintChar on the playfield. Jumped to from PrintChar ($B0D6) with
; a0 = the character's font data, d1 = byte column, d2 = line (32 = top of the
; playfield when the fine scroll is 0), d7 = $FF (transparent); on the stack, as
; PrintChar pushed them: d1-d7, a0-a5, the return address.
; The 8 lines can cross the ring's wrap, so they are copied to a scratch area laid
; out like the original buffer, the original code prints there (from $B0E2), and
; they are copied back. The original buffer line is d2 - 16 + fine Y; it shows world
; line 16*tileY + 255 - that, which is ring line (d2 - 16 + fineY - 16*tileY) & 255;
; byte b of an original line is byte 2*tileX + b in the corkscrew.
;------------------------------------------------------------------------------
EnhPrintField:
                move.l  52(a7),PrRet            ; come back here after the print
                move.l  #.back,52(a7)
                bsr.w   EnsureCurrent
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
                moveq   #0,d6                   ; copy in
                bsr.w   PrCopy
                lea     PrScratch(pc),a1
                moveq   #0,d1
                moveq   #0,d2
                jmp     l_0B0E2                 ; the original print, into the scratch area
.back:          movem.l d0-d7/a0-a5,-(a7)       ; (PrintChar's registers, as it returns them)
                moveq   #1,d6                   ; copy out
                bsr.w   PrCopy
                movem.l (a7)+,d0-d7/a0-a5
                move.l  PrRet(pc),-(a7)
                rts

; d6 = 0: ring -> scratch, 1: scratch -> ring. 8 lines x 5 planes x 1 byte.
PrCopy:         movea.l DrawRec(pc),a3
                movea.l buf_Base(a3),a3
                adda.l  PrOff(pc),a3            ; byte column on ring line 0
                lea     PrScratch+2(pc),a4
                move.w  PrRing(pc),d4
                moveq   #7,d5
.line:          move.w  d4,d0
                andi.w  #$FF,d0
                mulu.w  #LINEBYTES,d0
                lea     (a3,d0.l),a2
                moveq   #0,d0
                moveq   #4,d3
.pl:            tst.w   d6
                bne.b   .out
                move.b  (a2,d0.w),(a4,d0.w)
                bra.b   .nx
.out:           move.b  (a4,d0.w),(a2,d0.w)
.nx:            add.w   #ROWBYTES,d0
                dbra    d3,.pl
                addq.w  #1,d4
                lea     LINEBYTES(a4),a4
                dbra    d5,.line
                rts

;------------------------------------------------------------------------------
                cnop    0,4
DrawRec:        dc.l    0               ; the buffer being drawn (the original's g_ScreenFront)
ShowRec:        dc.l    0               ; the buffer on screen
PrRet:          dc.l    0
PrOff:          dc.l    0
PrRing:         dc.w    0
                cnop    0,4
ModuleFileEnd:                          ; the file ends here; the storage below is cleared by EnhInit
                rsset   ModuleFileEnd
RecP            rs.b    buf_SIZEOF
RecA            rs.b    buf_SIZEOF
RecB            rs.b    buf_SIZEOF
CopperA         rs.b    COPPER_BYTES
CopperB         rs.b    COPPER_BYTES
RListA          rs.b    8*RLIST_ENTRIES
RListB          rs.b    8*RLIST_ENTRIES
PrScratch       rs.b    2+8*LINEBYTES
ModuleEnd       rs.b    0
                ifgt    ModuleEnd-CLEAR_AREA
                fail    "the module runs into the HUD area"
                endif
