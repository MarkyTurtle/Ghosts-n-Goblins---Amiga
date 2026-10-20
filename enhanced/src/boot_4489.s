;==============================================================================
; boot_4489.s - the bootblock of the one program's disk (build_game.py). The disk is an
; ordinary 880K AmigaDOS-format
; disk (11 sectors a track, $4489 sync) with no filesystem ("NDOS"):
;
;   $000-$3FF   this bootblock
;   $400-$5FF   the file table (FILE_TABLE): 'GNGF', version.w, count.w, 8 bytes free, then
;               per file (file id = index) its offset on the disk and its length, longs
;   $600-       the files, one after another
;
; Every load goes through the 4489_byteloader (byteloader.i): any number of bytes from any
; offset, read a track at a time into an MFM buffer of $1760 words and checked.
;
; As the original bootblock (gng_boot.s), from which the take-over, the fade and the
; loading picture's display come:
;   1. MemDetect (while Kickstart's structures are intact; a6 = ExecBase): the machine
;      description at MACHINE_INFO for the game (as src/boot_patches.s; test_bootinfo.py)
;   2. take over: interrupts and DMA off, supervisor mode, stack at $80000
;   3. copy the loader to LOADER ($7FB20) and run it there
;   4. fade COLOR00 out, read the file table, load the loading picture (file 1) to $60000
;      and show it (HAM, interlaced; two copper lists swapped by a level 3 interrupt)
;   5. load the program (file 0) to $80, set $4.w = $80 and enter it at $A0 ($20 past
;      the start of the file: the original's hunk header), as the original did on 512K
; A load that fails is tried again; after 8 failures COLOR00 flashes red while it goes on
; trying (a disk error: the drive or the disk).
;==============================================================================

MACHINE_INFO    equ     $7FB00
LOADER          equ     $7FB20                  ; the loader runs here: after the machine description, below the stack
MFM_BUF         equ     $7C000                  ; $1760 words, to $7EEC0
FILE_TABLE      equ     $7F000                  ; the file table read from the disk ($200)
PICTURE         equ     $60000
PROGRAM         equ     $80
FID_MAIN        equ     0                       ; (build_game.py's file ids)
FID_LOADPIC     equ     1
FT_OFFSET       equ     $400                    ; the file table on the disk
FT_ENTRIES      equ     16

	org	0
	dc.b	'DOS',0
	dc.l	0                               ; checksum (build_game.py)
	dc.l	880                             ; root block (no filesystem: NDOS)

;------------------------------------------------------------------------------
; Kickstart calls here with a6 = ExecBase (a1 = the boot IORequest, not used).
BootEntry:
        bsr.w   MemDetect                       ; (at $0C: test_bootinfo.py runs it to $12)
        nop
        move.w  #$7fff,$9a(a0)                  ; INTENA: all off
        move.w  #$7fff,$96(a0)                  ; DMACON: all off
        lea     .super(pc),a1                   ; privilege violation -> the next instruction
        move.l  a1,$20.w
.super:         move.w  #$2000,sr               ; supervisor (or a trap that lands here), IPL 0
        lea     $80000,a7
        lea     Loader(pc),a1                   ; the loader, up out of the way
        lea     LOADER,a2
        movea.l a2,a3
        move.w  #(LoaderEnd-Loader)/4,d0
.copy:          move.l  (a1)+,(a2)+
        dbra    d0,.copy
        jmp     (a3)

;------------------------------------------------------------------------------
; MemDetect - the machine description (see src/boot_patches.s for its layout). Returns
; with a0 = $DFF000.
MemDetect:      lea     MACHINE_INFO,a2
                movea.l a2,a1
                moveq   #7,d0
.clr:           clr.l   (a1)+
                dbra    d0,.clr
                move.l  #'GNGM',(a2)+
                addq.b  #1,(a2)+                ; version 1
                move.b  $212(a6),(a2)+          ; VBlankFrequency
                move.w  $128(a6),(a2)+          ; AttnFlags
                lea     $142(a6),a3             ; MemList (lh_Head first)
.next:          movea.l (a3),a3
                tst.l   (a3)                    ; ln_Succ = 0: the list's tail
                beq.b   .done
                movem.l 20(a3),d0-d1            ; mh_Lower, mh_Upper
                movea.l a2,a1                   ; chip slot
                btst    #1,15(a3)               ; mh_Attributes: MEMF_CHIP
                bne.b   .store
                addq.l  #8,a1                   ; slow slot, if in $C00000-$DBFFFF
                cmp.l   #$C00000,d0
                blo.b   .fast
                cmp.l   #$DC0000,d0
                blo.b   .store
.fast:          addq.l  #8,a1                   ; fast slot
.store:         movem.l d0-d1,(a1)              ; (the last region of each kind is kept)
                bra.b   .next
.done:          lea     $dff000,a0
                rts

;------------------------------------------------------------------------------
; The loader, run at LOADER. a0 = $DFF000.
	cnop	0,4
Loader:
        lea     $180(a0),a1                     ; fade COLOR00 from white to black
        move.w  #$fff,d1
.fade:          move.w  $1e(a0),d0              ; (one step a frame)
        andi.w  #$20,d0
        beq.b   .fade
        move.w  d0,$9c(a0)
        move.w  d1,(a1)
        subi.w  #$111,d1
        bpl.b   .fade
        move.l  #FT_OFFSET,d0                   ; the file table
        move.l  #FT_ENTRIES*8+16,d1
        lea     FILE_TABLE,a0
        bsr.w   LoadIt
        lea     FILE_TABLE+16+FID_LOADPIC*8,a2  ; the loading picture
        movem.l (a2),d0-d1
        lea     PICTURE,a0
        bsr.w   LoadIt
        lea     $dff000,a0                      ; show it, as the original
        lea     Palette(pc),a3
        lea     $180(a0),a4
        moveq   #$f,d0
.pal:           move.w  (a3)+,(a4)+
        dbra    d0,.pal
        move.w  #$200,$96(a0)
        move.w  #$6804,$100(a0)                 ; 6 planes, HAM, interlaced
        move.w  #$0,$102(a0)
        move.w  #$24,$104(a0)
        move.w  #$15e,$108(a0)
        move.w  #$15e,$10a(a0)
        move.w  #$48,$92(a0)
        move.w  #$c8,$94(a0)
        move.w  #$2ca1,$8e(a0)
        move.w  #$2ea1,$90(a0)
        lea     CopperA(pc),a3
        move.l  a3,$80(a0)
        lea     CopperB(pc),a3
        move.l  a3,$84(a0)
        move.w  $88(a0),d0
        lea     Level3(pc),a3
        move.l  a3,$6c.w
        move.w  #$c020,$9a(a0)                  ; VERTB on
        move.w  #$8380,$96(a0)                  ; bitplanes and copper on
        lea     FILE_TABLE+16+FID_MAIN*8,a2     ; the program
        movem.l (a2),d0-d1
        lea     PROGRAM,a0
        bsr.w   LoadIt
        move.l  #PROGRAM,$4.w                   ; as the original's loader leaves it
        movea.l $4.w,a0
        jmp     $20(a0)                         ; past the hunk header

; LoadIt - d0 = offset, d1 = length, a0 = destination: the byteloader, tried until it works
LoadIt:         moveq   #0,d6                   ; failures
.try:           movem.l d0-d1/d6/a0,-(a7)
        moveq   #0,d2                           ; DF0
        lea     MFM_BUF,a1
        bsr.w   ByteLoader
        move.l  d0,d7
        movem.l (a7)+,d0-d1/d6/a0
        tst.l   d7
        beq.b   .ok
        addq.w  #1,d6                           ; after 8 failures: flash red while trying
        cmp.w   #8,d6
        bcs.b   .try
        move.w  #$f00,$dff180
        bra.b   .try
.ok:            rts

Level3:         move.l  a0,-(a7)                ; the original's: acknowledge, and the copper
        lea     $dff000,a0                      ; list for this field (interlace)
        move.w  #$70,$9c(a0)
        tst.w   $4(a0)
        bmi.b   .long
        tst.w   $8a(a0)
.long:          movea.l (a7)+,a0
        rte

; the loading picture's two copper lists (interlace: the level 3 interrupt shows CopperA on a
; long field, CopperB on a short one): the 6 bitplane pointers of the picture at $60000 - a
; line's plane rows are 32 bytes apart, and CopperB starts one line (192 bytes) on: the other field
CopperA:        dc.w    $00E0,$0006,$00E2,$0000,$00E4,$0006,$00E6,$0020
        dc.w    $00E8,$0006,$00EA,$0040,$00EC,$0006,$00EE,$0060
        dc.w    $00F0,$0006,$00F2,$0080,$00F4,$0006,$00F6,$00A0
        dc.w    $FFFF,$FFFE
CopperB:        dc.w    $00E0,$0006,$00E2,$00C0,$00E4,$0006,$00E6,$00E0
        dc.w    $00E8,$0006,$00EA,$0100,$00EC,$0006,$00EE,$0120
        dc.w    $00F0,$0006,$00F2,$0140,$00F4,$0006,$00F6,$0160
        dc.w    $FFFF,$FFFE
; the loading picture's 16 colours (the original bootblock's, at its $382)
Palette:        dc.w    $0000,$0FFF,$0002,$0003,$0501,$0227,$0467,$0838
        dc.w    $026B,$0E55,$0F37,$07BC,$0F5A,$0F97,$0FE7,$0EFC

; the 4489_byteloader (byteloader.i): d0 = offset on the disk, d1 = length, d2 = drive,
; a0 = destination, a1 = MFM buffer -> d0 = 0 if it worked; uses every register
ByteLoader:
	include "byteloader.i"
	cnop	0,4
LoaderEnd:                                      ; (the loader copied to LOADER ends here)

	ifgt	*-1024
	fail	the bootblock is over 1024 bytes
	endc
	ifgt	LOADER+LoaderEnd-Loader-$7FF00
	fail	the loader runs into its stack
	endc
	dcb.b	1024-*,0
