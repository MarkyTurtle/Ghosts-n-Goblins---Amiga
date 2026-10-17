; Ghosts'n Goblins (Elite, 1990, v3) - bootblock (track 0, sectors 0-1)
; Assemble: vasmm68k_mot -Fbin -m68000 -no-opt -o boot.bin gng_boot.s

	org	0

	dc.b	'DOS',0			; DOS bootblock id
	dc.l	$7007B32C		; bootblock checksum
	dc.l	0			; root block (unused)

;----------------------------------------------------------------------
; Bootblock entry - called by Kickstart's boot code with a6 = ExecBase.
; Kills all interrupts and DMA. Points the privilege-violation vector ($20)
; at the next instruction, then executes MOVE #$2000,SR: in supervisor mode
; that simply sets SR, in user mode it traps to the same place - so either
; way the CPU continues in supervisor mode at IPL 0. Then works out where
; the main program can go, copies the loader to $7FC00 and jumps to it.
;----------------------------------------------------------------------
BootEntry:
        lea.l   $dff000.l,a0                ; 00C
        move.w  #$7fff,$9a(a0)              ; 012  INTENA: disable all
        move.w  #$7fff,$96(a0)              ; 018  DMACON: disable all
        lea.l   .L028(pc),a1                ; 01E  privilege-violation vector -> next instr
        move.l  a1,$20.l                    ; 022
.L028:
        move.w  #$2000,sr                   ; 028  supervisor, IPL 0
        move.l  $4.w,d0                     ; 02C  ExecBase
        andi.l  #$fff80000,d0               ; 030  Exec above 512K? use that region
        bne.b   .L046                       ; 036
        cmpa.l  #$80000,a7                  ; 038  stack above $80000? (1MB chip)
        bls.b   .L046                       ; 03E
        move.l  #$80000,d0                  ; 040  -> load main program at $80000
.L046:
        move.l  d0,$4.w                     ; 046  $4.w = main program base (0 = load at $80)
        lea.l   $80000.l,a7                 ; 04A  stack = $80000 + base
        adda.l  d0,a7                       ; 050
        lea.l   Loader(pc),a1               ; 052  copy $CE longs of loader to $7FC00
        lea.l   $7fc00.l,a2                 ; 056
        movea.l a2,a3                       ; 05C
        move.w  #$cd,d0                     ; 05E
.L062:
        move.l  (a1)+,(a2)+                 ; 062
        dbra    d0,.L062                    ; 064
        jmp     (a3)                        ; 068  run the loader

;----------------------------------------------------------------------
; Loader - runs from $7FC00 (copied from bootblock offset $6A).
;  1. fade COLOR00 from white to black over 16 frames
;  2. set up CIA-B drive control, select DF0, motor on, seek to track 0
;  3. load $18300 bytes from track 1 to $60000 (loading picture)
;  4. show it: HAM6 interlaced (BPLCON0 $6804), two copper lists
;     swapped on the long-frame bit by Level3IRQ
;  5. load $18A80 bytes of main program:
;       $4.w == 0 (512K):   from track 110 to $80
;       otherwise:          from track 17 to the address in $4.w
;  6. motor off and JMP $20(base) - first code byte after the hunk header
;----------------------------------------------------------------------
Loader:
        lea.l   $180(a0),a1                 ; 06A
        move.w  #$fff,d1                    ; 06E  COLOR00 = white, fade down
.L072:
        move.w  $1e(a0),d0                  ; 072
        andi.w  #$20,d0                     ; 076
        beq.b   .L072                       ; 07A
        move.w  d0,$9c(a0)                  ; 07C  wait VBL
        move.w  d1,(a1)                     ; 080
        subi.w  #$111,d1                    ; 082
        bpl.b   .L072                       ; 086
        lea.l   $bfe001.l,a1                ; 088
        lea.l   $bfd100.l,a2                ; 08E
        bclr    #$7,$e00(a2)                ; 094  CIA-B CRB: TOD counts
        clr.b   $900(a2)                    ; 09A
        clr.b   $800(a2)                    ; 09E
        clr.b   $700(a2)                    ; 0A2
        st.b    (a2)                        ; 0A6  deselect all drives
        bclr    #$7,(a2)                    ; 0A8  motor on
        bclr    #$3,(a2)                    ; 0AC  select DF0
        bsr.w   SeekTrack0                  ; 0B0  seek track 0
        lea.l   $60000.l,a5                 ; 0B4  loading screen -> $60000
        move.l  #$18300,d5                  ; 0BA  $18300 bytes
        move.l  d5,d7                       ; 0C0
        addi.l  #$18a7,d7                   ; 0C2
        divu.w  #$18a8,d7                   ; 0C8  /6312 bytes per track
        subq.w  #$1,d7                      ; 0CC
        move.w  #$1,$28.w                   ; 0CE  start at track 1
        bsr.w   LoadTracks                  ; 0D4
        lea.l   LoadScreenPalette(pc),a3    ; 0D8
        lea.l   $180(a0),a4                 ; 0DC
        moveq   #$f,d0                      ; 0E0
.L0E2:
        move.w  (a3)+,(a4)+                 ; 0E2
        dbra    d0,.L0E2                    ; 0E4
        move.w  #$200,$96(a0)               ; 0E8  BPLEN off
        move.w  #$6804,$100(a0)             ; 0EE  BPLCON0 $6804: 6 planes, HAM, interlace
        move.w  #$0,$102(a0)                ; 0F4
        move.w  #$24,$104(a0)               ; 0FA
        move.w  #$15e,$108(a0)              ; 100
        move.w  #$15e,$10a(a0)              ; 106
        move.w  #$48,$92(a0)                ; 10C
        move.w  #$c8,$94(a0)                ; 112
        move.w  #$2ca1,$8e(a0)              ; 118
        move.w  #$2ea1,$90(a0)              ; 11E
        lea.l   CopperListA(pc),a3          ; 124
        move.l  a3,$80(a0)                  ; 128  COP1LC = list A
        lea.l   CopperListB(pc),a3          ; 12C
        move.l  a3,$84(a0)                  ; 130  COP2LC = list B
        move.w  $88(a0),d0                  ; 134
        lea.l   Level3IRQ(pc),a3            ; 138
        move.l  a3,$6c.l                    ; 13C  level 3 vector
        move.w  #$c020,$9a(a0)              ; 142  enable VERTB
        move.w  #$8380,$96(a0)              ; 148  DMA: bitplanes + copper
        move.l  #$18a80,d5                  ; 14E  main program: $18A80 bytes
        move.l  d5,d7                       ; 154
        addi.l  #$18a7,d7                   ; 156
        divu.w  #$18a8,d7                   ; 15C
        subq.w  #$1,d7                      ; 160
        move.l  $4.w,d0                     ; 162  $4.w == 0 -> 512K machine
        bne.b   .L17A                       ; 166
        lea.l   $80.l,a5                    ; 168  load to $80
        move.l  a5,$4.w                     ; 16E
        move.w  #$6e,$28.w                  ; 172  from track 110
        bra.b   .L182                       ; 178
.L17A:
        movea.l d0,a5                       ; 17A  expanded memory: load to base
        move.w  #$11,$28.w                  ; 17C  from track 17
.L182:
        bsr.w   LoadTracks                  ; 182
        st.b    (a2)                        ; 186  motor off
        bclr    #$3,(a2)                    ; 188
        st.b    (a2)                        ; 18C
        movea.l $4.w,a0                     ; 18E
        jmp     $20(a0)                     ; 192  enter main program

;----------------------------------------------------------------------
; Step outward until CIA-A PRA bit 4 (/TRK0) goes low; LDR cylinder = 0
;----------------------------------------------------------------------
SeekTrack0:
        btst    #$4,(a1)                    ; 196
        beq.b   .L1A6                       ; 19A
        bset    #$1,(a2)                    ; 19C
        bsr.w   StepHead                    ; 1A0
        bra.b   SeekTrack0                  ; 1A4
.L1A6:
        clr.w   $2a.l                       ; 1A6
        rts                                 ; 1AC

;----------------------------------------------------------------------
; Seek to cylinder ($28.w >> 1) and select head ($28.w bit 0)
;----------------------------------------------------------------------
SeekTrack:
        move.w  $28.w,d4                    ; 1AE
        bset    #$2,(a2)                    ; 1B2
        btst    #$0,d4                      ; 1B6
        beq.b   .L1C0                       ; 1BA
        bclr    #$2,(a2)                    ; 1BC
.L1C0:
        bclr    #$1,(a2)                    ; 1C0
        lsr.w   #$1,d4                      ; 1C4
        sub.w   $2a.l,d4                    ; 1C6
        beq.b   .L1E0                       ; 1CC
        bpl.b   .L1D6                       ; 1CE
        neg.w   d4                          ; 1D0
        bset    #$1,(a2)                    ; 1D2
.L1D6:
        subq.w  #$1,d4                      ; 1D6
.L1D8:
        bsr.w   StepHead                    ; 1D8
        dbra    d4,.L1D8                    ; 1DC
.L1E0:
        move.w  $28.w,d4                    ; 1E0
        lsr.w   #$1,d4                      ; 1E4
        move.w  d4,$2a.l                    ; 1E6
        rts                                 ; 1EC

;----------------------------------------------------------------------
; One step pulse, then wait on CIA-B TOD: $2F ticks, $11D after a direction change
;----------------------------------------------------------------------
StepHead:
        btst    #$1,(a2)                    ; 1EE
        seq.b   d0                          ; 1F2
        cmp.b   $2e.w,d0                    ; 1F4
        beq.b   .L206                       ; 1F8
        move.l  #$11d,d1                    ; 1FA
        not.b   $2e.w                       ; 200
        bra.b   .L208                       ; 204
.L206:
        moveq   #$2f,d1                     ; 206
.L208:
        moveq   #$0,d0                      ; 208
        move.b  $900(a2),d0                 ; 20A
        lsl.w   #$8,d0                      ; 20E
        move.b  $800(a2),d0                 ; 210
        lsl.l   #$8,d0                      ; 214
        move.b  $700(a2),d0                 ; 216
        cmp.l   d1,d0                       ; 21A
        bls.b   .L208                       ; 21C
        bclr    #$0,(a2)                    ; 21E
        bset    #$0,(a2)                    ; 222
        clr.b   $900(a2)                    ; 226
        clr.b   $800(a2)                    ; 22A
        clr.b   $700(a2)                    ; 22E
        rts                                 ; 232

;----------------------------------------------------------------------
; LoadTracks - a5 = destination, d7 = tracks-1, $28.w = first track
; DSKSYNC $A245, MFM read of $1900 words to $7C000 per track.
; Track block: track number word, $62A longs data (odd then even bits,
; $18AC bytes apart), checksum long = NOT(sum of data).
; 8 tries per track; wrong track number -> recalibrate and retry.
;----------------------------------------------------------------------
LoadTracks:
        move.w  #$8,$2c.w                   ; 234
        bsr.w   SeekTrack                   ; 23A
.L23E:
        btst    #$5,(a1)                    ; 23E
        bne.b   .L23E                       ; 242
        move.w  #$0,$24(a0)                 ; 244
        move.w  #$8210,$96(a0)              ; 24A
        move.w  #$8400,$9e(a0)              ; 250
        move.w  #$a245,$7e(a0)              ; 256  DSKSYNC = $A245
        move.l  #$7c000,$20(a0)             ; 25C  DSKPT = $7C000
        move.w  #$9900,$24(a0)              ; 264  DSKLEN = $1900 words (written twice)
        move.w  #$9900,$24(a0)              ; 26A
.L270:
        move.w  $1e(a0),d0                  ; 270  wait DSKBLK
        andi.w  #$2,d0                      ; 274
        beq.b   .L270                       ; 278
        move.w  d0,$9c(a0)                  ; 27A
        move.w  #$0,$24(a0)                 ; 27E
        lea.l   $7c002.l,a3                 ; 284
        movea.l a5,a4                       ; 28A
        move.l  #$55555555,d3               ; 28C
        move.w  (a3)+,d2                    ; 292
        move.w  (a3)+,d6                    ; 294
        and.w   d3,d2                       ; 296
        and.w   d3,d6                       ; 298
        add.w   d2,d2                       ; 29A
        or.w    d2,d6                       ; 29C
        swap    d6                          ; 29E
        moveq   #$0,d4                      ; 2A0
        move.w  #$629,d6                    ; 2A2  $62A longs
.L2A6:
        move.l  $18ac(a3),d1                ; 2A6
        and.l   d3,d1                       ; 2AA
        move.l  (a3)+,d2                    ; 2AC
        and.l   d3,d2                       ; 2AE
        add.l   d2,d2                       ; 2B0
        or.l    d2,d1                       ; 2B2
        add.l   d1,d4                       ; 2B4
        move.l  d1,(a4)+                    ; 2B6
        dbra    d6,.L2A6                    ; 2B8
        move.l  $18ac(a3),d1                ; 2BC
        and.l   d3,d1                       ; 2C0
        move.l  (a3)+,d2                    ; 2C2
        and.l   d3,d2                       ; 2C4
        add.l   d2,d2                       ; 2C6
        or.l    d2,d1                       ; 2C8
        not.l   d4                          ; 2CA  checksum = NOT(sum)
        cmp.l   d4,d1                       ; 2CC
        beq.b   .L2E2                       ; 2CE
        subq.w  #$1,$2c.w                   ; 2D0
        bne.w   .L23E                       ; 2D4
        bra.b   .L2E2                       ; 2D8
        bsr.w   SeekTrack0                  ; 2DA
        bra.w   LoadTracks                  ; 2DE
.L2E2:
        swap    d6                          ; 2E2
        cmp.w   $28.w,d6                    ; 2E4  expected track?
        beq.b   .L2F2                       ; 2E8
        bsr.w   SeekTrack0                  ; 2EA
        bra.w   LoadTracks                  ; 2EE
.L2F2:
        movea.l a4,a5                       ; 2F2
        addq.w  #$1,$28.w                   ; 2F4
        dbra    d7,LoadTracks               ; 2F8
        rts                                 ; 2FC

;----------------------------------------------------------------------
; Level 3 IRQ: acknowledge, select copper list by the long-frame bit (interlace)
;----------------------------------------------------------------------
Level3IRQ:
        move.l  a0,-(a7)                    ; 2FE
        lea.l   $dff000.l,a0                ; 300
        move.w  #$70,$9c(a0)                ; 306
        tst.w   $4(a0)                      ; 30C
        bmi.b   .L316                       ; 310
        tst.w   $8a(a0)                     ; 312
.L316:
        movea.l (a7)+,a0                    ; 316
        rte                                 ; 318

;----------------------------------------------------------------------
; Copper lists: bitplane pointers for even/odd fields of the interlaced picture
;----------------------------------------------------------------------
CopperListA:
	dc.w	$00E0,$0006,$00E2,$0000,$00E4,$0006,$00E6,$0020
	dc.w	$00E8,$0006,$00EA,$0040,$00EC,$0006,$00EE,$0060
	dc.w	$00F0,$0006,$00F2,$0080,$00F4,$0006,$00F6,$00A0
	dc.w	$FFFF,$FFFE
CopperListB:
	dc.w	$00E0,$0006,$00E2,$00C0,$00E4,$0006,$00E6,$00E0
	dc.w	$00E8,$0006,$00EA,$0100,$00EC,$0006,$00EE,$0120
	dc.w	$00F0,$0006,$00F2,$0140,$00F4,$0006,$00F6,$0160
	dc.w	$FFFF,$FFFE

;----------------------------------------------------------------------
; Loading-screen palette (16 colours)
;----------------------------------------------------------------------
LoadScreenPalette:
	dc.w	$0000,$0FFF,$0002,$0003,$0501,$0227,$0467,$0838
	dc.w	$026B,$0E55,$0F37,$07BC,$0F5A,$0F97,$0FE7,$0EFC
	dc.w	$0000,$0000,$03F2,$0000,$0000,$0000,$0000,$0000
	dc.w	$0000,$0000,$0000,$0000,$0000,$0000,$0000,$0000
	dc.w	$0000,$0000,$0000,$0000,$0000,$0000,$0000,$0000
	dc.w	$0000,$0000,$0000,$0000,$0000,$0000,$0000,$0000
	dc.w	$0000,$0000,$0000,$0000,$0000,$0000,$0000,$0000
	dc.w	$0000,$0000,$0000,$0000,$0000,$0000,$0000
