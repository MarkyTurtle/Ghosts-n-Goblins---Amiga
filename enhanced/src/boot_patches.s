;==============================================================================
; boot_patches.s - the enhanced bootblock: the original (gng_boot.s) plus a memory
; survey. Applied in place by tools/build_enh.py like patches.s (each block replaces the
; bytes from its first address up to the second; a block may use the labels of the
; blocks before it). Everything else in the bootblock is unchanged, including how it
; chooses the 512K or 1MB program.
;
; MemDetect runs first, while Kickstart's structures are still intact (a6 = ExecBase, as
; Kickstart calls a bootblock), and leaves a machine description at MACHINE_INFO for the
; game to read. The game copies it at start-up (the enhanced module's EnhInit), since the
; address is only safe until then. Layout (version 1, 32 bytes):
;
;   +0  'GNGM'
;   +4  version.b (1)
;   +5  VBlankFrequency.b (ExecBase $212: 50 PAL, 60 NTSC)
;   +6  AttnFlags.w (ExecBase $128: bit 0 68010, 1 68020, 2 68030, 3 68040, 4 68881...)
;   +8  chip RAM: mh_Lower.l, mh_Upper.l (the upper end: $80000 = 512K, $100000 = 1MB)
;   +16 slow RAM ($C00000-$DBFFFF): mh_Lower.l, mh_Upper.l (0, 0 if none)
;   +24 fast RAM (any other non-chip memory; the last one listed): mh_Lower.l, mh_Upper.l
; (mh_Lower is the first free byte after the region's MemHeader, so a region's size is
; mh_Upper - mh_Lower plus a few dozen bytes.)
;
; MACHINE_INFO = $7FB00: chip RAM above the loader's track buffer ($7C000-$7F200) and below
; the loader copy ($7FC00) and its stack; the game's own data stays below it (the highest,
; level 1's graphics, ends at $7F4DE) until EnhInit has copied the block.
;==============================================================================

MACHINE_INFO    equ     $7FB00

;@patch $3A2 $400
; the free space after the loading-screen palette (only its 16 colours are used); not
; part of the loader copied to $7FC00 - MemDetect only runs from the bootblock itself.
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
.done:          lea     $dff000.l,a0            ; the instruction MemDetect's call replaced
                rts

;@patch $00C $012
; BootEntry's first instruction (lea $dff000.l,a0) becomes the call; MemDetect does it.
                bsr.w   MemDetect
                nop
