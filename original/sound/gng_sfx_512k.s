; =========================================================================
; Ghosts'n Goblins (Elite, 1990) - sound driver + data: gng_sfx_512k
; Source file: sfx_512k.hunk  (loaded raw at $28E54, called at $28E54+$20)
; Driver: Richard Frankish's music player; music/sfx: Mark Cooksey.
; Assemble: vasmm68k_mot -Fbin -m68000 -no-opt -o gng_sfx_512k.bin gng_sfx_512k.s
; The music data below is written with the bytecode macros; samples are
; included from samples/*.raw.
; =========================================================================

CUSTOM		equ	$DFF000
INTREQR		equ	$01E
DMACON		equ	$096
INTENA		equ	$09A
INTREQ		equ	$09C
COLOR00		equ	$180
CIAA_PRA	equ	$BFE001

; Paula channel registers relative to CUSTOM + channel*16
AUD_LC            equ	$0A0
AUD_LEN           equ	$0A4
AUD_PER           equ	$0A6
AUD_VOL           equ	$0A8
AUD_DAT           equ	$0AA

; driver variables (offsets from DriverVars)
DRV_Owns          equ	$000	; current voice may write to Paula
DRV_SfxChans      equ	$001	; bit n = channel n held by a sound effect
DRV_UserValue     equ	$002	; set by command 3, never read
DRV_Mus0          equ	$004
DRV_Mus1          equ	$06C
DRV_Mus2          equ	$0D4
DRV_Mus3          equ	$13C
DRV_Sfx0          equ	$1A4
DRV_Sfx1          equ	$20C
DRV_Sfx2          equ	$274
DRV_Sfx3          equ	$2DC
DRV_SilentPtr     equ	$344	; address of the silent sample
DRV_VOICE_SIZE	equ	$68

; voice structure
VC_DataPtr        equ	$000	; current position in the bytecode (0 = voice idle)
VC_Instrument     equ	$004
VC_Spare          equ	$005	; 4th note byte (always 0, unused)
VC_AttackPtr      equ	$006
VC_LoopPtr        equ	$00A
VC_AttackLen      equ	$00E
VC_LoopLen        equ	$010
VC_AttackMul      equ	$012
VC_LoopMul        equ	$014
VC_StackPtr       equ	$01A	; call stack pointer (stack: $1E-$45, 4 frames x 10 bytes)
VC_Duration       equ	$046	; ticks left (also stack top)
VC_ChanVolume     equ	$048	; VOLUME command value 0-255
VC_Volume         equ	$04A	; current volume 0-255 (AUDxVOL = /4)
VC_InsVolume      equ	$04C
VC_VolEnvPtr      equ	$04E
VC_VolEnvSpeed    equ	$052
VC_VolEnvCount    equ	$053
VC_PitchEnvPtr    equ	$054
VC_PitchEnvSpeed  equ	$058
VC_PitchEnvCount  equ	$059
VC_Pitch          equ	$05A	; current pitch, 1/4 semitones
VC_TargetPitch    equ	$05C	; note pitch, 1/4 semitones
VC_Transpose      equ	$05E
VC_GlideFrom      equ	$060
VC_GlideTime      equ	$062
VC_GlideStep      equ	$064
VC_GlideOn        equ	$066
VC_InAttack       equ	$067	; -1 while the attack part plays

; ---- note names: C_4 = note 48 etc. (driver note numbers, octave = n/12)
C_0	equ	0
Cs0	equ	1
D_0	equ	2
Ds0	equ	3
E_0	equ	4
F_0	equ	5
Fs0	equ	6
G_0	equ	7
Gs0	equ	8
A_0	equ	9
As0	equ	10
B_0	equ	11
C_1	equ	12
Cs1	equ	13
D_1	equ	14
Ds1	equ	15
E_1	equ	16
F_1	equ	17
Fs1	equ	18
G_1	equ	19
Gs1	equ	20
A_1	equ	21
As1	equ	22
B_1	equ	23
C_2	equ	24
Cs2	equ	25
D_2	equ	26
Ds2	equ	27
E_2	equ	28
F_2	equ	29
Fs2	equ	30
G_2	equ	31
Gs2	equ	32
A_2	equ	33
As2	equ	34
B_2	equ	35
C_3	equ	36
Cs3	equ	37
D_3	equ	38
Ds3	equ	39
E_3	equ	40
F_3	equ	41
Fs3	equ	42
G_3	equ	43
Gs3	equ	44
A_3	equ	45
As3	equ	46
B_3	equ	47
C_4	equ	48
Cs4	equ	49
D_4	equ	50
Ds4	equ	51
E_4	equ	52
F_4	equ	53
Fs4	equ	54
G_4	equ	55
Gs4	equ	56
A_4	equ	57
As4	equ	58
B_4	equ	59
C_5	equ	60
Cs5	equ	61
D_5	equ	62
Ds5	equ	63
E_5	equ	64
F_5	equ	65
Fs5	equ	66
G_5	equ	67
Gs5	equ	68
A_5	equ	69
As5	equ	70
B_5	equ	71
C_6	equ	72
Cs6	equ	73
D_6	equ	74
Ds6	equ	75
E_6	equ	76
F_6	equ	77
Fs6	equ	78
G_6	equ	79
Gs6	equ	80
A_6	equ	81
As6	equ	82
B_6	equ	83
C_7	equ	84
Cs7	equ	85
D_7	equ	86
Ds7	equ	87
E_7	equ	88
F_7	equ	89
Fs7	equ	90
G_7	equ	91
Gs7	equ	92
A_7	equ	93
As7	equ	94
B_7	equ	95

; ---- music bytecode
NOTE	macro			; note,instrument,duration
	dc.b	\1,\2,\3,0
	endm
REST	macro			; duration (16-bit)
	dc.b	$60,(\1)>>8,(\1)&$FF,0
	endm
VOLUME	macro			; 0-255
	dc.b	$63,\1
	endm
CALL	macro			; pattern,transpose
	dc.b	$64,\1,\2
	endm
CALLN	macro			; pattern,transpose,count (plays count+1 times)
	dc.b	$65,\1,\2,\3
	endm
RETURN	macro
	dc.b	$66
	endm
ENDTRACK macro
	dc.b	$67
	endm
JUMP	macro			; label (offset is relative to the $68 byte)
jmp\@	dc.b	$68,((\1-jmp\@)>>8)&$FF,(\1-jmp\@)&$FF
	endm
PORTA_ON macro			; glide time in ticks
	dc.b	$69,\1
	endm
PORTA_OFF macro
	dc.b	$6B
	endm

	ifd	SND_ORG	; (assembled for another address: -DSND_ORG=...)
	org	SND_ORG
	else
	org	$28E54
	endc

HunkHeader:
        dc.l    $000003F3                   ; 00000  HUNK_HEADER
        dc.l    $00000000                   ; 00004  no resident libraries
        dc.l    $00000001                   ; 00008  table size 1
        dc.l    $00000000                   ; 0000C  first hunk 0
        dc.l    $00000000                   ; 00010  last hunk 0
        dc.l    $00001F51                   ; 00014  hunk 0 size (longs)
        dc.l    $000003E9                   ; 00018  HUNK_CODE
        dc.l    $00001F51                   ; 0001C  size (longs)

;----------------------------------------------------------------------------
; =====================================================================
; Ghosts'n Goblins sound driver - Richard Frankish's music player,
; music & sound effects by Mark Cooksey (Elite, 1990).
; Loaded raw (hunk header left in place); entry = file+$20.
;
; Call with d0.l = (argument << 16) | command:
;    0  CmdTick          - call once per vertical blank (VblIRQ does)
;    1  CmdPlayTune      - start tune <argument> on the 4 music voices
;    2  CmdPlaySfx       - start effect <argument> on the 4 sfx voices
;    3  CmdSetUserValue  - store <argument> in DRV_UserValue (never read)
; The game reaches this through vector $60 (MUSIC_PLAYER).
;
; 8 voices: 4 music (DRV_Mus0-3) + 4 sound effect (DRV_Sfx0-3); voice n
; plays on Paula channel n&3. While an sfx voice is active on a channel
; the music voice for that channel keeps running silently (it still
; advances through its data but does not touch the hardware).
; =====================================================================
;----------------------------------------------------------------------------
SndEntry:
        add.w   d0,d0                       ; 00020
        add.w   d0,d0                       ; 00022
        jmp     SndCommandTable(pc,d0.w)    ; 00024  dispatch on command

;----------------------------------------------------------------------------
; Command dispatch: 4-byte entries indexed by command*4
;----------------------------------------------------------------------------
SndCommandTable:
        bra.w   CmdTick                     ; 00028
c002C:
        bra.w   CmdPlayTune                 ; 0002C
c0030:
        bra.w   CmdPlaySfx                  ; 00030
c0034:
        bra.w   CmdSetUserValue             ; 00034

;----------------------------------------------------------------------------
; CmdPlayTune - a1 = MusicTable + tune*16 (4 self-relative longs, one per
; channel, 0 = channel unused). Each used voice gets its data pointer,
; duration 0 (start next tick) and an empty call stack.
;----------------------------------------------------------------------------
CmdPlayTune:
        swap    d0                          ; 00038
        movem.l a0-a4,-(a7)                 ; 0003A
        lea.l   DriverVars(pc),a3           ; 0003E  a3 = driver variables
        lea.l   CUSTOM,a0                   ; 00042
        lea.l   MusicTable(pc),a1           ; 00048  a1 = MusicTable
        lsl.w   #$4,d0                      ; 0004C  16 bytes per tune
        adda.w  d0,a1                       ; 0004E
        move.l  (a1)+,d0                    ; 00050  channel 0 data (self-relative long)
        beq.b   c006C                       ; 00052
        add.l   a1,d0                       ; 00054
        subq.l  #$4,d0                      ; 00056
        lea.l   DRV_Mus0(a3),a4             ; 00058
        move.l  d0,VC_DataPtr(a4)           ; 0005C  voice data pointer
        clr.w   VC_Duration(a4)             ; 00060  duration 0: start next tick
        lea.l   VC_Duration(a4),a2          ; 00064  empty call stack
        move.l  a2,VC_StackPtr(a4)          ; 00068
c006C:
        move.l  (a1)+,d0                    ; 0006C
        beq.b   c0088                       ; 0006E
        add.l   a1,d0                       ; 00070
        subq.l  #$4,d0                      ; 00072
        lea.l   DRV_Mus1(a3),a4             ; 00074
        move.l  d0,VC_DataPtr(a4)           ; 00078
        clr.w   VC_Duration(a4)             ; 0007C
        lea.l   VC_Duration(a4),a2          ; 00080
        move.l  a2,VC_StackPtr(a4)          ; 00084
c0088:
        move.l  (a1)+,d0                    ; 00088
        beq.b   c00A4                       ; 0008A
        add.l   a1,d0                       ; 0008C
        subq.l  #$4,d0                      ; 0008E
        lea.l   DRV_Mus2(a3),a4             ; 00090
        move.l  d0,VC_DataPtr(a4)           ; 00094
        clr.w   VC_Duration(a4)             ; 00098
        lea.l   VC_Duration(a4),a2          ; 0009C
        move.l  a2,VC_StackPtr(a4)          ; 000A0
c00A4:
        move.l  (a1)+,d0                    ; 000A4
        beq.b   c00C0                       ; 000A6
        add.l   a1,d0                       ; 000A8
        subq.l  #$4,d0                      ; 000AA
        lea.l   DRV_Mus3(a3),a4             ; 000AC
        move.l  d0,VC_DataPtr(a4)           ; 000B0
        clr.w   VC_Duration(a4)             ; 000B4
        lea.l   VC_Duration(a4),a2          ; 000B8
        move.l  a2,VC_StackPtr(a4)          ; 000BC
c00C0:
        movem.l (a7)+,a0-a4                 ; 000C0
        rts                                 ; 000C4

;----------------------------------------------------------------------------
; CmdPlaySfx - same, from SfxTable, into the four sfx voices
;----------------------------------------------------------------------------
CmdPlaySfx:
        swap    d0                          ; 000C6
        movem.l a0-a4,-(a7)                 ; 000C8
        lea.l   DriverVars(pc),a3           ; 000CC
        lea.l   CUSTOM,a0                   ; 000D0
        lea.l   MusicTable(pc),a1           ; 000D6  a1 = SfxTable
        lsl.w   #$4,d0                      ; 000DA
        adda.w  d0,a1                       ; 000DC
        move.l  (a1)+,d0                    ; 000DE
        beq.b   c00FA                       ; 000E0
        add.l   a1,d0                       ; 000E2
        subq.l  #$4,d0                      ; 000E4
        lea.l   DRV_Sfx0(a3),a4             ; 000E6
        move.l  d0,VC_DataPtr(a4)           ; 000EA
        clr.w   VC_Duration(a4)             ; 000EE
        lea.l   VC_Duration(a4),a2          ; 000F2
        move.l  a2,VC_StackPtr(a4)          ; 000F6
c00FA:
        move.l  (a1)+,d0                    ; 000FA
        beq.b   c0116                       ; 000FC
        add.l   a1,d0                       ; 000FE
        subq.l  #$4,d0                      ; 00100
        lea.l   DRV_Sfx1(a3),a4             ; 00102
        move.l  d0,VC_DataPtr(a4)           ; 00106
        clr.w   VC_Duration(a4)             ; 0010A
        lea.l   VC_Duration(a4),a2          ; 0010E
        move.l  a2,VC_StackPtr(a4)          ; 00112
c0116:
        move.l  (a1)+,d0                    ; 00116
        beq.b   c0132                       ; 00118
        add.l   a1,d0                       ; 0011A
        subq.l  #$4,d0                      ; 0011C
        lea.l   DRV_Sfx2(a3),a4             ; 0011E
        move.l  d0,VC_DataPtr(a4)           ; 00122
        clr.w   VC_Duration(a4)             ; 00126
        lea.l   VC_Duration(a4),a2          ; 0012A
        move.l  a2,VC_StackPtr(a4)          ; 0012E
c0132:
        move.l  (a1)+,d0                    ; 00132
        beq.b   c014E                       ; 00134
        add.l   a1,d0                       ; 00136
        subq.l  #$4,d0                      ; 00138
        lea.l   DRV_Sfx3(a3),a4             ; 0013A
        move.l  d0,VC_DataPtr(a4)           ; 0013E
        clr.w   VC_Duration(a4)             ; 00142
        lea.l   VC_Duration(a4),a2          ; 00146
        move.l  a2,VC_StackPtr(a4)          ; 0014A
c014E:
        movem.l (a7)+,a0-a4                 ; 0014E
        rts                                 ; 00152

;----------------------------------------------------------------------------
; CmdSetUserValue - stores the argument in DRV_UserValue. Nothing reads it.
;----------------------------------------------------------------------------
CmdSetUserValue:
        swap    d0                          ; 00154
        move.l  a3,-(a7)                    ; 00156
        lea.l   DriverVars(pc),a3           ; 00158
        move.w  d0,DRV_UserValue(a3)        ; 0015C
        movea.l (a7)+,a3                    ; 00160
        rts                                 ; 00162

;----------------------------------------------------------------------------
; CmdTick - run every voice once per frame.
; d7 = $70,$60..$00: voice index = d7>>4 (7..0), channel = (d7>>4)&3,
; bit 2 of the index = sound-effect voice. Sfx voices (7-4) are done
; first so they can claim their channel (DRV_SfxChans) before the music
; voice for that channel runs. a2 = CUSTOM, a3 = DriverVars,
; a4 = CUSTOM + channel*16 (so AUD_xx(a4) = AUDnxx), a5 = voice.
;----------------------------------------------------------------------------
CmdTick:
        swap    d0                          ; 00164
        movem.l d1-d7/a0-a5,-(a7)           ; 00166
        lea.l   CUSTOM,a2                   ; 0016A
        lea.l   DriverVars(pc),a3           ; 00170
        lea.l   SampleBase(pc),a1           ; 00174  silent sample for stopped channels
        move.l  a1,DRV_SilentPtr(a3)        ; 00178
        moveq   #$70,d7                     ; 0017C  start with voice 7 (sfx, channel 3)
        lea.l   DRV_Sfx3(a3),a5             ; 0017E
TickVoiceLoop:
        moveq   #$30,d0                     ; 00182
        and.w   d7,d0                       ; 00184
        movea.l a2,a4                       ; 00186
        adda.w  d0,a4                       ; 00188
        subq.w  #$1,VC_Duration(a5)         ; 0018A  note still sounding?
        bhi.w   VoiceEffects                ; 0018E

;----------------------------------------------------------------------------
; Duration expired: fetch the next event.
; DRV_Owns = this voice may write to its Paula channel:
;   sfx voice   - always (and marks the channel busy in DRV_SfxChans)
;   music voice - only when no sfx voice holds the channel
; NOTE: DRV_Owns is only refreshed here, so the per-tick effects below
; use the value left by the last voice that read an event.
;----------------------------------------------------------------------------
VoiceNextEvent:
        move.w  d7,d1                       ; 00192
        lsr.w   #$4,d1                      ; 00194
        bclr    #$2,d1                      ; 00196  sound-effect voice?
        beq.b   MusicVoiceEvent             ; 0019A
        move.l  VC_DataPtr(a5),d0           ; 0019C
        beq.b   c01AC                       ; 001A0
        st.b    DRV_Owns(a3)                ; 001A2  sfx voice owns its channel
        bset    d1,DRV_SfxChans(a3)         ; 001A6  mark channel taken by sfx
        bra.b   ReadBytecode                ; 001AA
c01AC:
        bclr    d1,DRV_SfxChans(a3)         ; 001AC
        bra.w   NextVoice                   ; 001B0
MusicVoiceEvent:
        move.l  VC_DataPtr(a5),d0           ; 001B4
        beq.w   NextVoice                   ; 001B8
        btst    d1,DRV_SfxChans(a3)         ; 001BC  channel free of sfx?
        seq.b   DRV_Owns(a3)                ; 001C0

;----------------------------------------------------------------------------
; ReadBytecode - one byte: $00-$5F = note, $60-$7F = command
; (bit 7 is masked off, so $E0-$FF alias $60-$7F; never used).
;----------------------------------------------------------------------------
ReadBytecode:
        movea.l d0,a0                       ; 001C4
        moveq   #$0,d0                      ; 001C6
        move.b  (a0)+,d0                    ; 001C8
        moveq   #$7f,d1                     ; 001CA
        and.b   d0,d1                       ; 001CC
        subi.b  #$60,d1                     ; 001CE  command byte?
        bcs.w   BcNote                      ; 001D2
        add.w   d1,d1                       ; 001D6
        add.w   d1,d1                       ; 001D8
        jmp     BytecodeTable(pc,d1.w)      ; 001DA  jump to command handler
BcNop:
        bra.b   VoiceNextEvent              ; 001DE

;----------------------------------------------------------------------------
; Bytecode commands ($60 + index):
;  $60 REST dur.w,0     $63 VOLUME v        $64 CALL pat,transpose
;  $65 CALLN pat,tr,n   $66 RETURN          $67 END
;  $68 JUMP rel.w       $69 PORTA_ON time   $6B PORTA_OFF
;  $61,$62,$6A,$6C-$7F = no-op
;----------------------------------------------------------------------------
BytecodeTable:
        bra.w   BcRest                      ; 001E0
c01E4:
        bra.w   BcNop                       ; 001E4
c01E8:
        bra.w   BcNop                       ; 001E8
c01EC:
        bra.w   BcVolume                    ; 001EC
c01F0:
        bra.w   BcCall                      ; 001F0
c01F4:
        bra.w   BcCallN                     ; 001F4
c01F8:
        bra.w   BcReturn                    ; 001F8
c01FC:
        bra.w   BcEnd                       ; 001FC
c0200:
        bra.w   BcJump                      ; 00200
c0204:
        bra.w   BcPortaOn                   ; 00204
c0208:
        bra.w   BcNop                       ; 00208
c020C:
        bra.w   BcPortaOff                  ; 0020C
c0210:
        bra.w   BcNop                       ; 00210
c0214:
        bra.w   BcNop                       ; 00214
c0218:
        bra.w   BcNop                       ; 00218
c021C:
        bra.w   BcNop                       ; 0021C
c0220:
        bra.w   BcNop                       ; 00220
c0224:
        bra.w   BcNop                       ; 00224
c0228:
        bra.w   BcNop                       ; 00228
c022C:
        bra.w   BcNop                       ; 0022C
c0230:
        bra.w   BcNop                       ; 00230
c0234:
        bra.w   BcNop                       ; 00234
c0238:
        bra.w   BcNop                       ; 00238
c023C:
        bra.w   BcNop                       ; 0023C
c0240:
        bra.w   BcNop                       ; 00240
c0244:
        bra.w   BcNop                       ; 00244
c0248:
        bra.w   BcNop                       ; 00248
c024C:
        bra.w   BcNop                       ; 0024C
c0250:
        bra.w   BcNop                       ; 00250
c0254:
        bra.w   BcNop                       ; 00254
c0258:
        bra.w   BcNop                       ; 00258
c025C:
        bra.w   BcNop                       ; 0025C

;----------------------------------------------------------------------------
; REST: duration.w, spare byte; mutes the channel (AUDxVOL = 0) if owned
;----------------------------------------------------------------------------
BcRest:
        move.b  (a0)+,d0                    ; 00260
        lsl.w   #$8,d0                      ; 00262
        move.b  (a0)+,d0                    ; 00264
        move.w  d0,VC_Duration(a5)          ; 00266
        move.b  (a0)+,VC_Spare(a5)          ; 0026A
        tst.b   DRV_Owns(a3)                ; 0026E
        beq.b   c0278                       ; 00272
        clr.w   AUD_VOL(a4)                 ; 00274
c0278:
        move.l  a0,VC_DataPtr(a5)           ; 00278
        bra.w   NextVoice                   ; 0027C

;----------------------------------------------------------------------------
; END: voice stops; channel gets the silent sample, volume 0
;----------------------------------------------------------------------------
BcEnd:
        clr.l   VC_DataPtr(a5)              ; 00280
        tst.b   DRV_Owns(a3)                ; 00284
        beq.b   c029A                       ; 00288
        move.l  DRV_SilentPtr(a3),AUD_LC(a4); 0028A
        move.w  #$20,AUD_LEN(a4)            ; 00290
        clr.w   AUD_VOL(a4)                 ; 00296
c029A:
        bra.w   NextVoice                   ; 0029A

;----------------------------------------------------------------------------
; VOLUME: channel volume 0-255 (multiplied with the instrument volume)
;----------------------------------------------------------------------------
BcVolume:
        moveq   #$0,d0                      ; 0029E
        move.b  (a0)+,d0                    ; 002A0
        move.w  d0,VC_ChanVolume(a5)        ; 002A2
        move.l  a0,VC_DataPtr(a5)           ; 002A6
        bra.w   VoiceNextEvent              ; 002AA

;----------------------------------------------------------------------------
; JUMP: signed 16-bit offset relative to the $68 byte
;----------------------------------------------------------------------------
BcJump:
        move.b  (a0)+,d0                    ; 002AE
        lsl.w   #$8,d0                      ; 002B0
        move.b  (a0)+,d0                    ; 002B2
        lea.l   -$3(a0,d0.w),a0             ; 002B4
        move.l  a0,VC_DataPtr(a5)           ; 002B8
        bra.w   VoiceNextEvent              ; 002BC

;----------------------------------------------------------------------------
; PORTA_ON: following notes glide from the previous pitch over <time> ticks
;----------------------------------------------------------------------------
BcPortaOn:
        st.b    VC_GlideOn(a5)              ; 002C0
        clr.w   d1                          ; 002C4
        move.b  (a0)+,d1                    ; 002C6
        move.w  d1,VC_GlideTime(a5)         ; 002C8
        move.l  a0,VC_DataPtr(a5)           ; 002CC
        bra.w   VoiceNextEvent              ; 002D0
BcPortaOff:
        clr.b   VC_GlideOn(a5)              ; 002D4
        move.l  a0,VC_DataPtr(a5)           ; 002D8
        bra.w   VoiceNextEvent              ; 002DC

;----------------------------------------------------------------------------
; CALL pattern,transpose (play once)
;----------------------------------------------------------------------------
BcCall:
        clr.w   d2                          ; 002E0
        move.b  (a0)+,d0                    ; 002E2
        move.b  (a0)+,d1                    ; 002E4
        bra.b   BcCallPush                  ; 002E6

;----------------------------------------------------------------------------
; CALLN pattern,transpose,count - plays count+1 times.
; Call stack frame (10 bytes, grows down from VC_Duration): count.w,
; pattern start.l, return address.l - room for 4 nested calls.
; Patterns are found through PatternTable (signed self-relative words).
;----------------------------------------------------------------------------
BcCallN:
        clr.w   d2                          ; 002E8
        move.b  (a0)+,d0                    ; 002EA
        move.b  (a0)+,d1                    ; 002EC
        move.b  (a0)+,d2                    ; 002EE
BcCallPush:
        ext.w   d1                          ; 002F0
        move.w  d1,VC_Transpose(a5)         ; 002F2
        movea.l VC_StackPtr(a5),a1          ; 002F6
        move.l  a0,-(a1)                    ; 002FA  push return address
        lea.l   PatternTable(pc),a0         ; 002FC
        add.w   d0,d0                       ; 00300
        adda.w  d0,a0                       ; 00302
        adda.w  (a0),a0                     ; 00304
        move.l  a0,VC_DataPtr(a5)           ; 00306
        move.l  a0,-(a1)                    ; 0030A  push pattern start
        move.w  d2,-(a1)                    ; 0030C  push repeat count
        move.l  a1,VC_StackPtr(a5)          ; 0030E
        bra.w   VoiceNextEvent              ; 00312

;----------------------------------------------------------------------------
; RETURN: repeat the pattern while the count lasts, else pop and clear transpose
;----------------------------------------------------------------------------
BcReturn:
        movea.l VC_StackPtr(a5),a1          ; 00316
        subq.w  #$1,(a1)+                   ; 0031A
        bmi.b   BcReturnPop                 ; 0031C
        move.l  (a1),VC_DataPtr(a5)         ; 0031E
        bra.w   VoiceNextEvent              ; 00322
BcReturnPop:
        addq.l  #$4,a1                      ; 00326
        move.l  (a1)+,VC_DataPtr(a5)        ; 00328
        move.l  a1,VC_StackPtr(a5)          ; 0032C
        clr.w   VC_Transpose(a5)            ; 00330
        bra.w   VoiceNextEvent              ; 00334

;----------------------------------------------------------------------------
; NOTE: note.b, instrument.b, duration.b, spare.b
; pitch = (note + transpose) * 4  (PitchTable has 4 steps per semitone)
; With portamento on, the glide step = ((new-old)<<4) / time.
;----------------------------------------------------------------------------
BcNote:
        add.w   VC_Transpose(a5),d0         ; 00338
        add.w   d0,d0                       ; 0033C  quarter-semitone pitch index
        add.w   d0,d0                       ; 0033E
        clr.w   VC_GlideStep(a5)            ; 00340
        tst.b   VC_GlideOn(a5)              ; 00344
        beq.b   NoteNoGlide                 ; 00348
        move.w  VC_TargetPitch(a5),d1       ; 0034A
        move.w  d1,VC_GlideFrom(a5)         ; 0034E
        move.w  d1,VC_Pitch(a5)             ; 00352
        move.w  d0,d1                       ; 00356
        sub.w   VC_GlideFrom(a5),d1         ; 00358
        ext.l   d1                          ; 0035C
        asl.l   #$4,d1                      ; 0035E
        divs.w  VC_GlideTime(a5),d1         ; 00360
        move.w  d1,VC_GlideStep(a5)         ; 00364
        bra.b   NoteSetTarget               ; 00368
NoteNoGlide:
        move.w  d0,VC_GlideFrom(a5)         ; 0036A
        move.w  d0,VC_Pitch(a5)             ; 0036E

;----------------------------------------------------------------------------
; Load the instrument record (InstrumentTable -> 28 bytes):
;  +0  attack sample offset.l (from SampleBase, 0 = none)
;  +4  loop sample offset.l   (0 = none: silence after the attack)
;  +8  volume envelope.l (self-relative)   +12 pitch envelope.l (self-rel.)
;  +16 attack length.w  +18 loop length.w (words, = AUDxLEN)
;  +20 attack period multiplier.w   +22 loop period multiplier.w
;  +24 volume env speed.b  +25 pitch env speed.b  +26 volume.w (0-256)
;----------------------------------------------------------------------------
NoteSetTarget:
        move.w  d0,VC_TargetPitch(a5)       ; 00372
        clr.w   d1                          ; 00376
        move.b  (a0)+,d1                    ; 00378
        move.b  d1,VC_Instrument(a5)        ; 0037A
        clr.w   d0                          ; 0037E
        move.b  (a0)+,d0                    ; 00380
        move.w  d0,VC_Duration(a5)          ; 00382
        move.b  (a0)+,VC_Spare(a5)          ; 00386
        move.l  a0,VC_DataPtr(a5)           ; 0038A
        lea.l   InstrumentTable(pc),a0      ; 0038E
        add.w   d1,d1                       ; 00392
        adda.w  d1,a0                       ; 00394
        adda.w  (a0),a0                     ; 00396
        lea.l   SampleBase(pc),a1           ; 00398
        move.l  (a0)+,d0                    ; 0039C
        beq.b   c03A2                       ; 0039E
        add.l   a1,d0                       ; 003A0
c03A2:
        move.l  d0,VC_AttackPtr(a5)         ; 003A2
        move.l  (a0)+,d0                    ; 003A6
        beq.b   c03AC                       ; 003A8
        add.l   a1,d0                       ; 003AA
c03AC:
        move.l  d0,VC_LoopPtr(a5)           ; 003AC
        move.l  (a0)+,d0                    ; 003B0
        beq.b   c03B8                       ; 003B2
        add.l   a0,d0                       ; 003B4
        subq.l  #$4,d0                      ; 003B6
c03B8:
        move.l  d0,VC_VolEnvPtr(a5)         ; 003B8
        move.l  (a0)+,d0                    ; 003BC
        beq.b   c03C4                       ; 003BE
        add.l   a0,d0                       ; 003C0
        subq.l  #$4,d0                      ; 003C2
c03C4:
        move.l  d0,VC_PitchEnvPtr(a5)       ; 003C4
        move.w  (a0)+,VC_AttackLen(a5)      ; 003C8
        move.w  (a0)+,VC_LoopLen(a5)        ; 003CC
        move.w  (a0)+,VC_AttackMul(a5)      ; 003D0
        move.w  (a0)+,VC_LoopMul(a5)        ; 003D4
        move.b  (a0)+,VC_VolEnvSpeed(a5)    ; 003D8
        move.b  (a0)+,VC_PitchEnvSpeed(a5)  ; 003DC
        move.w  (a0)+,VC_InsVolume(a5)      ; 003E0
        clr.b   VC_VolEnvCount(a5)          ; 003E4
        clr.b   VC_PitchEnvCount(a5)        ; 003E8
        move.w  VC_InsVolume(a5),d2         ; 003EC  volume = ins vol * chan vol >> 8
        mulu.w  VC_ChanVolume(a5),d2        ; 003F0
        lsr.w   #$8,d2                      ; 003F4
        move.w  d2,VC_Volume(a5)            ; 003F6
        lsr.w   #$2,d2                      ; 003FA  0-255 -> 0-63
        tst.b   DRV_Owns(a3)                ; 003FC
        beq.b   NoteStartSound              ; 00400
        move.w  d2,AUD_VOL(a4)              ; 00402

;----------------------------------------------------------------------------
; Period = PitchTable[pitch] * multiplier >> 16. An instrument without an
; attack sample just changes the loop sample/period (legato).
;----------------------------------------------------------------------------
NoteStartSound:
        lea.l   PatternTable(pc),a0         ; 00406
        move.w  VC_TargetPitch(a5),d0       ; 0040A
        add.w   d0,d0                       ; 0040E
        move.w  (a0,d0.w),d2                ; 00410
        move.l  VC_AttackPtr(a5),d0         ; 00414
        bne.b   StartChannelDMA             ; 00418
        mulu.w  VC_LoopMul(a5),d2           ; 0041A  no attack sample: just retune
        swap    d2                          ; 0041E
        st.b    VC_InAttack(a5)             ; 00420
        tst.b   DRV_Owns(a3)                ; 00424
        beq.b   c043A                       ; 00428
        move.l  VC_LoopPtr(a5),AUD_LC(a4)   ; 0042A
        move.w  VC_LoopLen(a5),AUD_LEN(a4)  ; 00430
        move.w  d2,AUD_PER(a4)              ; 00436
c043A:
        bra.w   VoiceEffects                ; 0043A

;----------------------------------------------------------------------------
; Start the sample: with interrupts off, stop the channel's DMA, set a
; period of 1 and wait for the channel's audio interrupt twice so Paula
; is idle, load attack LC/LEN/PER, enable DMA, wait for the interrupt
; that says Paula has latched it, then load the loop part (or the
; silent sample) so it plays after the attack.
;----------------------------------------------------------------------------
StartChannelDMA:
        tst.b   DRV_Owns(a3)                ; 0043E
        beq.w   VoiceEffects                ; 00442
        moveq   #$30,d1                     ; 00446
        and.w   d7,d1                       ; 00448
        lsr.w   #$4,d1                      ; 0044A
        clr.w   d3                          ; 0044C
        bset    d1,d3                       ; 0044E
        move.w  #$4000,INTENA(a2)           ; 00450  INTENA: master off
        move.w  d3,DMACON(a2)               ; 00456  DMACON: channel DMA off
        move.w  #$1,AUD_PER(a4)             ; 0045A  period 1
        clr.w   d4                          ; 00460
        addq.w  #$7,d1                      ; 00462
        bset    d1,d4                       ; 00464
        move.w  d4,INTREQ(a2)               ; 00466  clear AUDn interrupt request
        clr.w   AUD_DAT(a4)                 ; 0046A
c046E:
        move.w  INTREQR(a2),d1              ; 0046E  wait for AUDn interrupt (DMA stopped)
        and.w   d4,d1                       ; 00472
        beq.b   c046E                       ; 00474
        move.w  d4,INTREQ(a2)               ; 00476
        clr.w   AUD_DAT(a4)                 ; 0047A
c047E:
        move.w  INTREQR(a2),d1              ; 0047E
        and.w   d4,d1                       ; 00482
        beq.b   c047E                       ; 00484
        move.w  d4,INTREQ(a2)               ; 00486
        mulu.w  VC_AttackMul(a5),d2         ; 0048A
        swap    d2                          ; 0048E
        move.l  d0,AUD_LC(a4)               ; 00490  attack sample
        move.w  VC_AttackLen(a5),AUD_LEN(a4); 00494
        move.w  d2,AUD_PER(a4)              ; 0049A
        bset    #$f,d3                      ; 0049E
        move.w  d4,INTREQ(a2)               ; 004A2
        move.w  d3,DMACON(a2)               ; 004A6  DMACON: channel DMA on
        move.w  d4,INTREQ(a2)               ; 004AA
c04AE:
        move.w  INTREQR(a2),d1              ; 004AE  wait until Paula has latched the attack
        and.w   d4,d1                       ; 004B2
        beq.b   c04AE                       ; 004B4
        sf.b    VC_InAttack(a5)             ; 004B6
        move.l  VC_LoopPtr(a5),d1           ; 004BA
        beq.b   NoLoopPart                  ; 004BE
        move.w  VC_LoopLen(a5),AUD_LEN(a4)  ; 004C0
        move.l  d1,AUD_LC(a4)               ; 004C6  loop sample follows the attack
        move.w  #$c000,INTENA(a2)           ; 004CA  INTENA: master on
        bra.b   VoiceEffects                ; 004D0
NoLoopPart:
        move.w  #$20,AUD_LEN(a4)            ; 004D2
        move.l  DRV_SilentPtr(a3),AUD_LC(a4); 004D8  no loop: silent sample
        move.w  #$c000,INTENA(a2)           ; 004DE

;----------------------------------------------------------------------------
; Per-tick effects (also runs while a note is held):
; volume envelope - every <speed> ticks the next byte n gives
;   vol = (n+1) * channel volume * instrument volume >> 16; 0 ends it
;----------------------------------------------------------------------------
VoiceEffects:
        move.l  VC_VolEnvPtr(a5),d0         ; 004E4
        beq.b   DoPortamento                ; 004E8
        subq.b  #$1,VC_VolEnvCount(a5)      ; 004EA
        bhi.b   DoPortamento                ; 004EE
        move.b  VC_VolEnvSpeed(a5),VC_VolEnvCount(a5); 004F0
        movea.l d0,a0                       ; 004F6
        moveq   #$0,d0                      ; 004F8
        move.b  (a0)+,d0                    ; 004FA
        bne.b   c0504                       ; 004FC  envelope byte 0 = end
        clr.l   VC_VolEnvPtr(a5)            ; 004FE
        bra.b   DoPortamento                ; 00502
c0504:
        move.l  a0,VC_VolEnvPtr(a5)         ; 00504
        addq.w  #$1,d0                      ; 00508
        mulu.w  VC_ChanVolume(a5),d0        ; 0050A
        mulu.w  VC_InsVolume(a5),d0         ; 0050E
        swap    d0                          ; 00512
        move.w  d0,VC_Volume(a5)            ; 00514
        lsr.w   #$2,d0                      ; 00518
        tst.b   DRV_Owns(a3)                ; 0051A
        beq.b   DoPortamento                ; 0051E
        move.w  d0,AUD_VOL(a4)              ; 00520

;----------------------------------------------------------------------------
; Portamento: move the current pitch (x16 fixed point) towards the target
;----------------------------------------------------------------------------
DoPortamento:
        move.w  VC_GlideStep(a5),d1         ; 00524
        beq.b   DoPitchEnvelope             ; 00528
        move.w  VC_Pitch(a5),d0             ; 0052A
        lsl.w   #$4,d0                      ; 0052E
        add.w   d1,d0                       ; 00530
        bpl.b   c0536                       ; 00532
        clr.w   d0                          ; 00534
c0536:
        lsr.w   #$4,d0                      ; 00536
        tst.w   d1                          ; 00538
        bmi.b   c054E                       ; 0053A
        cmp.w   VC_TargetPitch(a5),d0       ; 0053C
        bcs.b   c0560                       ; 00540
        move.w  VC_TargetPitch(a5),VC_Pitch(a5); 00542
        clr.w   VC_GlideStep(a5)            ; 00548
        bra.b   DoPitchEnvelope             ; 0054C
c054E:
        cmp.w   VC_TargetPitch(a5),d0       ; 0054E
        bhi.b   c0560                       ; 00552
        move.w  VC_TargetPitch(a5),VC_Pitch(a5); 00554
        clr.w   VC_GlideStep(a5)            ; 0055A
        bra.b   DoPitchEnvelope             ; 0055E
c0560:
        move.w  d0,VC_Pitch(a5)             ; 00560

;----------------------------------------------------------------------------
; Pitch envelope: every <speed> ticks subtract the next signed byte (1/4 semitones) from the pitch; $80 ends it
;----------------------------------------------------------------------------
DoPitchEnvelope:
        move.l  VC_PitchEnvPtr(a5),d0       ; 00564
        beq.b   NoPitchEnvelope             ; 00568
        subq.b  #$1,VC_PitchEnvCount(a5)    ; 0056A
        bhi.b   NoPitchEnvelope             ; 0056E
        move.b  VC_PitchEnvSpeed(a5),VC_PitchEnvCount(a5); 00570
        movea.l d0,a0                       ; 00576
        move.b  (a0)+,d0                    ; 00578
        neg.b   d0                          ; 0057A
        bvc.b   c0584                       ; 0057C  $80 (overflow on neg) = end
        clr.l   VC_PitchEnvPtr(a5)          ; 0057E
        bra.b   NoPitchEnvelope             ; 00582
c0584:
        move.l  a0,VC_PitchEnvPtr(a5)       ; 00584
        ext.w   d0                          ; 00588
        move.w  VC_Pitch(a5),d1             ; 0058A
        sub.w   d0,d1                       ; 0058E
        bra.b   WritePeriod                 ; 00590
NoPitchEnvelope:
        move.w  VC_GlideFrom(a5),d1         ; 00592
        cmp.w   VC_TargetPitch(a5),d1       ; 00596
        beq.b   NextVoice                   ; 0059A
        move.w  VC_Pitch(a5),d1             ; 0059C

;----------------------------------------------------------------------------
; Write the period for the current pitch (attack or loop multiplier)
;----------------------------------------------------------------------------
WritePeriod:
        tst.b   DRV_Owns(a3)                ; 005A0
        beq.b   NextVoice                   ; 005A4
        add.w   d1,d1                       ; 005A6
        lea.l   PatternTable(pc),a0         ; 005A8
        move.w  (a0,d1.w),d0                ; 005AC
        tst.b   VC_InAttack(a5)             ; 005B0
        beq.b   c05BC                       ; 005B4
        mulu.w  VC_LoopMul(a5),d0           ; 005B6
        bra.b   c05C0                       ; 005BA
c05BC:
        mulu.w  VC_AttackMul(a5),d0         ; 005BC
c05C0:
        swap    d0                          ; 005C0
        move.w  d0,AUD_PER(a4)              ; 005C2
NextVoice:
        lea.l   -$68(a5),a5                 ; 005C6
        subi.l  #$10,d7                     ; 005CA  next voice
        bpl.w   TickVoiceLoop               ; 005D0  until voice 0 done
        movem.l (a7)+,d1-d7/a0-a5           ; 005D4
        rts                                 ; 005D8

;----------------------------------------------------------------------------
; DebugWaitMouse - NOT CALLED. Developer breakpoint left in the driver:
; shows colour d6 in COLOR00 until the left mouse button is pressed, then
; waits for release (with delays).
;----------------------------------------------------------------------------
DebugWaitMouse:
        move.w  d0,-(a7)                    ; 005DA
c05DC:
        move.w  d6,CUSTOM+COLOR00           ; 005DC
        btst    #$6,CIAA_PRA                ; 005E2
        bne.w   c05DC                       ; 005EA
        move.w  #$ffff,d0                   ; 005EE
c05F2:
        nop                                 ; 005F2
        dbra    d0,c05F2                    ; 005F4
c05F8:
        btst    #$6,CIAA_PRA                ; 005F8
        beq.w   c05F8                       ; 00600
        move.w  #$ffff,d0                   ; 00604
c0608:
        nop                                 ; 00608
        dbra    d0,c0608                    ; 0060A
        move.w  (a7)+,d0                    ; 0060E
        rts                                 ; 00610
SfxTable:
MusicTable:
        dc.l    0                           ; 00612  sfx  0  
        dc.l    0                           ; 00616
        dc.l    0                           ; 0061A
        dc.l    Sfx00_Ch3-*                 ; 0061E
        dc.l    0                           ; 00622  sfx  1  Arthur hit (armour lost)
        dc.l    0                           ; 00626
        dc.l    0                           ; 0062A
        dc.l    Sfx01_Ch3-*                 ; 0062E
        dc.l    0                           ; 00632  sfx  2  
        dc.l    0                           ; 00636
        dc.l    0                           ; 0063A
        dc.l    Sfx02_Ch3-*                 ; 0063E
        dc.l    0                           ; 00642  sfx  3  
        dc.l    0                           ; 00646
        dc.l    0                           ; 0064A
        dc.l    Sfx03_Ch3-*                 ; 0064E
        dc.l    0                           ; 00652  sfx  4  jump
        dc.l    0                           ; 00656
        dc.l    0                           ; 0065A
        dc.l    Sfx04_Ch3-*                 ; 0065E
        dc.l    0                           ; 00662  sfx  5  land
        dc.l    0                           ; 00666
        dc.l    0                           ; 0066A
        dc.l    Sfx05_Ch3-*                 ; 0066E
        dc.l    0                           ; 00672  sfx  6  throw weapon
        dc.l    0                           ; 00676
        dc.l    0                           ; 0067A
        dc.l    Sfx06_Ch3-*                 ; 0067E
        dc.l    0                           ; 00682  sfx  7  
        dc.l    0                           ; 00686
        dc.l    0                           ; 0068A
        dc.l    Sfx07_Ch3-*                 ; 0068E
        dc.l    0                           ; 00692  sfx  8  
        dc.l    0                           ; 00696
        dc.l    0                           ; 0069A
        dc.l    Sfx08_Ch3-*                 ; 0069E
        dc.l    0                           ; 006A2  sfx  9  
        dc.l    0                           ; 006A6
        dc.l    0                           ; 006AA
        dc.l    Sfx09_Ch3-*                 ; 006AE
        dc.l    0                           ; 006B2  sfx 10  weapon shot event
        dc.l    0                           ; 006B6
        dc.l    0                           ; 006BA
        dc.l    Sfx10_Ch3-*                 ; 006BE
        dc.l    0                           ; 006C2  sfx 11  torch flame (1MB build)
        dc.l    0                           ; 006C6
        dc.l    0                           ; 006CA
        dc.l    Sfx11_Ch3-*                 ; 006CE
        dc.l    0                           ; 006D2  sfx 12  weapon / boss hit
        dc.l    0                           ; 006D6
        dc.l    0                           ; 006DA
        dc.l    Sfx12_Ch3-*                 ; 006DE
        dc.l    0                           ; 006E2  sfx 13  
        dc.l    0                           ; 006E6
        dc.l    0                           ; 006EA
        dc.l    Sfx13_Ch3-*                 ; 006EE
        dc.l    0                           ; 006F2  sfx 14  
        dc.l    0                           ; 006F6
        dc.l    0                           ; 006FA
        dc.l    Sfx14_Ch3-*                 ; 006FE
        dc.l    0                           ; 00702  sfx 15  
        dc.l    0                           ; 00706
        dc.l    0                           ; 0070A
        dc.l    Sfx15_Ch3-*                 ; 0070E
        dc.l    0                           ; 00712  sfx 16  
        dc.l    0                           ; 00716
        dc.l    0                           ; 0071A
        dc.l    Sfx16_Ch3-*                 ; 0071E
        dc.l    0                           ; 00722  sfx 17  enemy event (crow, blue killer, ghost, skeleton)
        dc.l    0                           ; 00726
        dc.l    0                           ; 0072A
        dc.l    Sfx17_Ch3-*                 ; 0072E
        dc.l    0                           ; 00732  sfx 18  
        dc.l    0                           ; 00736
        dc.l    0                           ; 0073A
        dc.l    Sfx18_Ch3-*                 ; 0073E
        dc.l    0                           ; 00742  sfx 19  
        dc.l    0                           ; 00746
        dc.l    0                           ; 0074A
        dc.l    Sfx19_Ch3-*                 ; 0074E
        dc.l    0                           ; 00752  sfx 20  enemy event (flying knight, zombie, Astaroth)
        dc.l    0                           ; 00756
        dc.l    0                           ; 0075A
        dc.l    Sfx20_Ch3-*                 ; 0075E
        dc.l    0                           ; 00762  sfx 21  
        dc.l    0                           ; 00766
        dc.l    0                           ; 0076A
        dc.l    Sfx21_Ch3-*                 ; 0076E
        dc.l    0                           ; 00772  sfx 22  
        dc.l    0                           ; 00776
        dc.l    0                           ; 0077A
        dc.l    Sfx22_Ch3-*                 ; 0077E
        dc.l    0                           ; 00782  sfx 23  
        dc.l    0                           ; 00786
        dc.l    0                           ; 0078A
        dc.l    Sfx23_Ch3-*                 ; 0078E
        dc.l    0                           ; 00792  sfx 24  
        dc.l    0                           ; 00796
        dc.l    0                           ; 0079A
        dc.l    Sfx24_Ch3-*                 ; 0079E
        dc.l    0                           ; 007A2  sfx 25  
        dc.l    0                           ; 007A6
        dc.l    0                           ; 007AA
        dc.l    Sfx25_Ch3-*                 ; 007AE
        dc.l    0                           ; 007B2  sfx 26  
        dc.l    0                           ; 007B6
        dc.l    0                           ; 007BA
        dc.l    Sfx26_Ch3-*                 ; 007BE
        dc.l    0                           ; 007C2  sfx 27  
        dc.l    0                           ; 007C6
        dc.l    0                           ; 007CA
        dc.l    Sfx27_Ch3-*                 ; 007CE
        dc.l    0                           ; 007D2  sfx 28  key / item collected
        dc.l    0                           ; 007D6
        dc.l    0                           ; 007DA
        dc.l    Sfx28_Ch3-*                 ; 007DE
        dc.l    0                           ; 007E2  sfx 29  
        dc.l    0                           ; 007E6
        dc.l    0                           ; 007EA
        dc.l    Sfx29_Ch3-*                 ; 007EE
InstrumentTable:
        dc.w    Ins00-*                     ; 007F2  instrument 0
        dc.w    Ins00-*                     ; 007F4  instrument 1
        dc.w    Ins00-*                     ; 007F6  instrument 2
        dc.w    Ins00-*                     ; 007F8  instrument 3
        dc.w    Ins00-*                     ; 007FA  instrument 4
        dc.w    Ins00-*                     ; 007FC  instrument 5
        dc.w    Ins00-*                     ; 007FE  instrument 6
        dc.w    Ins00-*                     ; 00800  instrument 7
        dc.w    Ins00-*                     ; 00802  instrument 8
        dc.w    Ins00-*                     ; 00804  instrument 9
        dc.w    Ins10-*                     ; 00806  instrument 10
        dc.w    Ins11-*                     ; 00808  instrument 11
        dc.w    Ins12-*                     ; 0080A  instrument 12
        dc.w    Ins13-*                     ; 0080C  instrument 13
        dc.w    Ins14-*                     ; 0080E  instrument 14
        dc.w    Ins15-*                     ; 00810  instrument 15
        dc.w    Ins16-*                     ; 00812  instrument 16
        dc.w    Ins17-*                     ; 00814  instrument 17
        dc.w    Ins18-*                     ; 00816  instrument 18
        dc.w    Ins19-*                     ; 00818  instrument 19
        dc.w    Ins20-*                     ; 0081A  instrument 20
        dc.w    Ins21-*                     ; 0081C  instrument 21
        dc.w    Ins22-*                     ; 0081E  instrument 22
        dc.w    Ins23-*                     ; 00820  instrument 23
        dc.w    Ins24-*                     ; 00822  instrument 24
        dc.w    Ins25-*                     ; 00824  instrument 25
        dc.w    Ins26-*                     ; 00826  instrument 26
        dc.w    Ins27-*                     ; 00828  instrument 27
        dc.w    Ins28-*                     ; 0082A  instrument 28
        dc.w    Ins29-*                     ; 0082C  instrument 29
        dc.w    Ins30-*                     ; 0082E  instrument 30
        dc.w    Ins31-*                     ; 00830  instrument 31
        dc.w    Ins32-*                     ; 00832  instrument 32
        dc.w    Ins33-*                     ; 00834  instrument 33
        dc.w    Ins34-*                     ; 00836  instrument 34
        dc.w    Ins35-*                     ; 00838  instrument 35
        dc.w    Ins36-*                     ; 0083A  instrument 36
        dc.w    Ins37-*                     ; 0083C  instrument 37
Ins00:
        dc.l    Smp00-SampleBase            ; 0083E  attack sample (offset from SampleBase)
        dc.l    0                           ; 00842  loop sample (offset from SampleBase)
        dc.l    0                           ; 00846  volume envelope (self-relative)
        dc.l    0                           ; 0084A  pitch envelope (self-relative)
        dc.w    $0472,$0000                 ; 0084E  attack / loop length (words) = 2276 / 0 bytes
        dc.w    $5999,$0000                 ; 00852  period multipliers (PitchTable * mul >> 16)
        dc.b    0,0                         ; 00856  volume / pitch envelope speed (ticks per step)
        dc.w    256                         ; 00858  instrument volume (x channel volume >> 8; /4 -> AUDxVOL)
Ins10:
        dc.l    Smp01-SampleBase            ; 0085A  attack sample (offset from SampleBase)
        dc.l    0                           ; 0085E  loop sample (offset from SampleBase)
        dc.l    0                           ; 00862  volume envelope (self-relative)
        dc.l    0                           ; 00866  pitch envelope (self-relative)
        dc.w    $0457,$0000                 ; 0086A  attack / loop length (words) = 2222 / 0 bytes
        dc.w    $5999,$0000                 ; 0086E  period multipliers (PitchTable * mul >> 16)
        dc.b    0,0                         ; 00872  volume / pitch envelope speed (ticks per step)
        dc.w    256                         ; 00874  instrument volume (x channel volume >> 8; /4 -> AUDxVOL)
Ins11:
        dc.l    Smp01-SampleBase            ; 00876  attack sample (offset from SampleBase)
        dc.l    0                           ; 0087A  loop sample (offset from SampleBase)
        dc.l    0                           ; 0087E  volume envelope (self-relative)
        dc.l    0                           ; 00882  pitch envelope (self-relative)
        dc.w    $0D39,$0000                 ; 00886  attack / loop length (words) = 6770 / 0 bytes
        dc.w    $8000,$0000                 ; 0088A  period multipliers (PitchTable * mul >> 16)
        dc.b    0,0                         ; 0088E  volume / pitch envelope speed (ticks per step)
        dc.w    256                         ; 00890  instrument volume (x channel volume >> 8; /4 -> AUDxVOL)
Ins12:
        dc.l    Smp01-SampleBase            ; 00892  attack sample (offset from SampleBase)
        dc.l    0                           ; 00896  loop sample (offset from SampleBase)
        dc.l    0                           ; 0089A  volume envelope (self-relative)
        dc.l    0                           ; 0089E  pitch envelope (self-relative)
        dc.w    $03CF,$0000                 ; 008A2  attack / loop length (words) = 1950 / 0 bytes
        dc.w    $5999,$0000                 ; 008A6  period multipliers (PitchTable * mul >> 16)
        dc.b    0,0                         ; 008AA  volume / pitch envelope speed (ticks per step)
        dc.w    256                         ; 008AC  instrument volume (x channel volume >> 8; /4 -> AUDxVOL)
Ins13:
        dc.l    Smp02-SampleBase            ; 008AE  attack sample (offset from SampleBase)
        dc.l    0                           ; 008B2  loop sample (offset from SampleBase)
        dc.l    0                           ; 008B6  volume envelope (self-relative)
        dc.l    0                           ; 008BA  pitch envelope (self-relative)
        dc.w    $02C2,$0000                 ; 008BE  attack / loop length (words) = 1412 / 0 bytes
        dc.w    $5999,$0000                 ; 008C2  period multipliers (PitchTable * mul >> 16)
        dc.b    0,0                         ; 008C6  volume / pitch envelope speed (ticks per step)
        dc.w    256                         ; 008C8  instrument volume (x channel volume >> 8; /4 -> AUDxVOL)
Ins14:
        dc.l    Smp03-SampleBase            ; 008CA  attack sample (offset from SampleBase)
        dc.l    0                           ; 008CE  loop sample (offset from SampleBase)
        dc.l    0                           ; 008D2  volume envelope (self-relative)
        dc.l    0                           ; 008D6  pitch envelope (self-relative)
        dc.w    $03C1,$0000                 ; 008DA  attack / loop length (words) = 1922 / 0 bytes
        dc.w    $5999,$0000                 ; 008DE  period multipliers (PitchTable * mul >> 16)
        dc.b    0,0                         ; 008E2  volume / pitch envelope speed (ticks per step)
        dc.w    256                         ; 008E4  instrument volume (x channel volume >> 8; /4 -> AUDxVOL)
Ins15:
        dc.l    Smp04-SampleBase            ; 008E6  attack sample (offset from SampleBase)
        dc.l    0                           ; 008EA  loop sample (offset from SampleBase)
        dc.l    0                           ; 008EE  volume envelope (self-relative)
        dc.l    0                           ; 008F2  pitch envelope (self-relative)
        dc.w    $0A2A,$0000                 ; 008F6  attack / loop length (words) = 5204 / 0 bytes
        dc.w    $7000,$0000                 ; 008FA  period multipliers (PitchTable * mul >> 16)
        dc.b    0,0                         ; 008FE  volume / pitch envelope speed (ticks per step)
        dc.w    256                         ; 00900  instrument volume (x channel volume >> 8; /4 -> AUDxVOL)
Ins16:
        dc.l    Smp04-SampleBase            ; 00902  attack sample (offset from SampleBase)
        dc.l    0                           ; 00906  loop sample (offset from SampleBase)
        dc.l    0                           ; 0090A  volume envelope (self-relative)
        dc.l    0                           ; 0090E  pitch envelope (self-relative)
        dc.w    $095A,$0000                 ; 00912  attack / loop length (words) = 4788 / 0 bytes
        dc.w    $7000,$0000                 ; 00916  period multipliers (PitchTable * mul >> 16)
        dc.b    0,0                         ; 0091A  volume / pitch envelope speed (ticks per step)
        dc.w    256                         ; 0091C  instrument volume (x channel volume >> 8; /4 -> AUDxVOL)
Ins17:
        dc.l    Smp04-SampleBase            ; 0091E  attack sample (offset from SampleBase)
        dc.l    0                           ; 00922  loop sample (offset from SampleBase)
        dc.l    0                           ; 00926  volume envelope (self-relative)
        dc.l    0                           ; 0092A  pitch envelope (self-relative)
        dc.w    $082A,$0000                 ; 0092E  attack / loop length (words) = 4180 / 0 bytes
        dc.w    $7000,$0000                 ; 00932  period multipliers (PitchTable * mul >> 16)
        dc.b    0,0                         ; 00936  volume / pitch envelope speed (ticks per step)
        dc.w    256                         ; 00938  instrument volume (x channel volume >> 8; /4 -> AUDxVOL)
Ins18:
        dc.l    Smp04-SampleBase            ; 0093A  attack sample (offset from SampleBase)
        dc.l    0                           ; 0093E  loop sample (offset from SampleBase)
        dc.l    0                           ; 00942  volume envelope (self-relative)
        dc.l    0                           ; 00946  pitch envelope (self-relative)
        dc.w    $063C,$0000                 ; 0094A  attack / loop length (words) = 3192 / 0 bytes
        dc.w    $7000,$0000                 ; 0094E  period multipliers (PitchTable * mul >> 16)
        dc.b    0,0                         ; 00952  volume / pitch envelope speed (ticks per step)
        dc.w    256                         ; 00954  instrument volume (x channel volume >> 8; /4 -> AUDxVOL)
Ins19:
        dc.l    Smp05-SampleBase            ; 00956  attack sample (offset from SampleBase)
        dc.l    0                           ; 0095A  loop sample (offset from SampleBase)
        dc.l    0                           ; 0095E  volume envelope (self-relative)
        dc.l    0                           ; 00962  pitch envelope (self-relative)
        dc.w    $06F1,$0000                 ; 00966  attack / loop length (words) = 3554 / 0 bytes
        dc.w    $7000,$0000                 ; 0096A  period multipliers (PitchTable * mul >> 16)
        dc.b    0,0                         ; 0096E  volume / pitch envelope speed (ticks per step)
        dc.w    256                         ; 00970  instrument volume (x channel volume >> 8; /4 -> AUDxVOL)
Ins20:
        dc.l    Smp05-SampleBase            ; 00972  attack sample (offset from SampleBase)
        dc.l    0                           ; 00976  loop sample (offset from SampleBase)
        dc.l    0                           ; 0097A  volume envelope (self-relative)
        dc.l    0                           ; 0097E  pitch envelope (self-relative)
        dc.w    $06B1,$0000                 ; 00982  attack / loop length (words) = 3426 / 0 bytes
        dc.w    $7000,$0000                 ; 00986  period multipliers (PitchTable * mul >> 16)
        dc.b    0,0                         ; 0098A  volume / pitch envelope speed (ticks per step)
        dc.w    256                         ; 0098C  instrument volume (x channel volume >> 8; /4 -> AUDxVOL)
Ins21:
        dc.l    Smp06-SampleBase            ; 0098E  attack sample (offset from SampleBase)
        dc.l    0                           ; 00992  loop sample (offset from SampleBase)
        dc.l    0                           ; 00996  volume envelope (self-relative)
        dc.l    0                           ; 0099A  pitch envelope (self-relative)
        dc.w    $063C,$0000                 ; 0099E  attack / loop length (words) = 3192 / 0 bytes
        dc.w    $7000,$0000                 ; 009A2  period multipliers (PitchTable * mul >> 16)
        dc.b    0,0                         ; 009A6  volume / pitch envelope speed (ticks per step)
        dc.w    256                         ; 009A8  instrument volume (x channel volume >> 8; /4 -> AUDxVOL)
Ins22:
        dc.l    Smp06-SampleBase            ; 009AA  attack sample (offset from SampleBase)
        dc.l    0                           ; 009AE  loop sample (offset from SampleBase)
        dc.l    0                           ; 009B2  volume envelope (self-relative)
        dc.l    0                           ; 009B6  pitch envelope (self-relative)
        dc.w    $08FD,$0000                 ; 009BA  attack / loop length (words) = 4602 / 0 bytes
        dc.w    $7000,$0000                 ; 009BE  period multipliers (PitchTable * mul >> 16)
        dc.b    0,0                         ; 009C2  volume / pitch envelope speed (ticks per step)
        dc.w    256                         ; 009C4  instrument volume (x channel volume >> 8; /4 -> AUDxVOL)
Ins23:
        dc.l    Smp06-SampleBase            ; 009C6  attack sample (offset from SampleBase)
        dc.l    0                           ; 009CA  loop sample (offset from SampleBase)
        dc.l    0                           ; 009CE  volume envelope (self-relative)
        dc.l    0                           ; 009D2  pitch envelope (self-relative)
        dc.w    $09B4,$0000                 ; 009D6  attack / loop length (words) = 4968 / 0 bytes
        dc.w    $7000,$0000                 ; 009DA  period multipliers (PitchTable * mul >> 16)
        dc.b    0,0                         ; 009DE  volume / pitch envelope speed (ticks per step)
        dc.w    256                         ; 009E0  instrument volume (x channel volume >> 8; /4 -> AUDxVOL)
Ins24:
        dc.l    Smp06-SampleBase            ; 009E2  attack sample (offset from SampleBase)
        dc.l    0                           ; 009E6  loop sample (offset from SampleBase)
        dc.l    0                           ; 009EA  volume envelope (self-relative)
        dc.l    0                           ; 009EE  pitch envelope (self-relative)
        dc.w    $0129,$0000                 ; 009F2  attack / loop length (words) = 594 / 0 bytes
        dc.w    $5999,$0000                 ; 009F6  period multipliers (PitchTable * mul >> 16)
        dc.b    0,0                         ; 009FA  volume / pitch envelope speed (ticks per step)
        dc.w    256                         ; 009FC  instrument volume (x channel volume >> 8; /4 -> AUDxVOL)
Ins25:
        dc.l    Smp06-SampleBase            ; 009FE  attack sample (offset from SampleBase)
        dc.l    0                           ; 00A02  loop sample (offset from SampleBase)
        dc.l    0                           ; 00A06  volume envelope (self-relative)
        dc.l    0                           ; 00A0A  pitch envelope (self-relative)
        dc.w    $075D,$0000                 ; 00A0E  attack / loop length (words) = 3770 / 0 bytes
        dc.w    $7000,$0000                 ; 00A12  period multipliers (PitchTable * mul >> 16)
        dc.b    0,0                         ; 00A16  volume / pitch envelope speed (ticks per step)
        dc.w    256                         ; 00A18  instrument volume (x channel volume >> 8; /4 -> AUDxVOL)
Ins26:
        dc.l    Smp07-SampleBase            ; 00A1A  attack sample (offset from SampleBase)
        dc.l    0                           ; 00A1E  loop sample (offset from SampleBase)
        dc.l    0                           ; 00A22  volume envelope (self-relative)
        dc.l    0                           ; 00A26  pitch envelope (self-relative)
        dc.w    $1158,$0000                 ; 00A2A  attack / loop length (words) = 8880 / 0 bytes
        dc.w    $7148,$0000                 ; 00A2E  period multipliers (PitchTable * mul >> 16)
        dc.b    0,0                         ; 00A32  volume / pitch envelope speed (ticks per step)
        dc.w    256                         ; 00A34  instrument volume (x channel volume >> 8; /4 -> AUDxVOL)
Ins27:
        dc.l    Smp07-SampleBase            ; 00A36  attack sample (offset from SampleBase)
        dc.l    0                           ; 00A3A  loop sample (offset from SampleBase)
        dc.l    0                           ; 00A3E  volume envelope (self-relative)
        dc.l    0                           ; 00A42  pitch envelope (self-relative)
        dc.w    $03C0,$0000                 ; 00A46  attack / loop length (words) = 1920 / 0 bytes
        dc.w    $5999,$0000                 ; 00A4A  period multipliers (PitchTable * mul >> 16)
        dc.b    0,0                         ; 00A4E  volume / pitch envelope speed (ticks per step)
        dc.w    256                         ; 00A50  instrument volume (x channel volume >> 8; /4 -> AUDxVOL)
Ins28:
        dc.l    Smp07-SampleBase            ; 00A52  attack sample (offset from SampleBase)
        dc.l    0                           ; 00A56  loop sample (offset from SampleBase)
        dc.l    0                           ; 00A5A  volume envelope (self-relative)
        dc.l    0                           ; 00A5E  pitch envelope (self-relative)
        dc.w    $05CE,$0000                 ; 00A62  attack / loop length (words) = 2972 / 0 bytes
        dc.w    $5999,$0000                 ; 00A66  period multipliers (PitchTable * mul >> 16)
        dc.b    0,0                         ; 00A6A  volume / pitch envelope speed (ticks per step)
        dc.w    256                         ; 00A6C  instrument volume (x channel volume >> 8; /4 -> AUDxVOL)
Ins29:
        dc.l    Smp08-SampleBase            ; 00A6E  attack sample (offset from SampleBase)
        dc.l    0                           ; 00A72  loop sample (offset from SampleBase)
        dc.l    0                           ; 00A76  volume envelope (self-relative)
        dc.l    0                           ; 00A7A  pitch envelope (self-relative)
        dc.w    $0526,$0000                 ; 00A7E  attack / loop length (words) = 2636 / 0 bytes
        dc.w    $5999,$0000                 ; 00A82  period multipliers (PitchTable * mul >> 16)
        dc.b    0,0                         ; 00A86  volume / pitch envelope speed (ticks per step)
        dc.w    256                         ; 00A88  instrument volume (x channel volume >> 8; /4 -> AUDxVOL)
Ins30:
        dc.l    Smp08-SampleBase            ; 00A8A  attack sample (offset from SampleBase)
        dc.l    0                           ; 00A8E  loop sample (offset from SampleBase)
        dc.l    0                           ; 00A92  volume envelope (self-relative)
        dc.l    0                           ; 00A96  pitch envelope (self-relative)
        dc.w    $012A,$0000                 ; 00A9A  attack / loop length (words) = 596 / 0 bytes
        dc.w    $5999,$0000                 ; 00A9E  period multipliers (PitchTable * mul >> 16)
        dc.b    0,0                         ; 00AA2  volume / pitch envelope speed (ticks per step)
        dc.w    256                         ; 00AA4  instrument volume (x channel volume >> 8; /4 -> AUDxVOL)
Ins31:
        dc.l    Smp08-SampleBase            ; 00AA6  attack sample (offset from SampleBase)
        dc.l    0                           ; 00AAA  loop sample (offset from SampleBase)
        dc.l    0                           ; 00AAE  volume envelope (self-relative)
        dc.l    0                           ; 00AB2  pitch envelope (self-relative)
        dc.w    $011D,$0000                 ; 00AB6  attack / loop length (words) = 570 / 0 bytes
        dc.w    $5999,$0000                 ; 00ABA  period multipliers (PitchTable * mul >> 16)
        dc.b    0,0                         ; 00ABE  volume / pitch envelope speed (ticks per step)
        dc.w    256                         ; 00AC0  instrument volume (x channel volume >> 8; /4 -> AUDxVOL)
Ins32:
        dc.l    Smp08-SampleBase            ; 00AC2  attack sample (offset from SampleBase)
        dc.l    0                           ; 00AC6  loop sample (offset from SampleBase)
        dc.l    0                           ; 00ACA  volume envelope (self-relative)
        dc.l    0                           ; 00ACE  pitch envelope (self-relative)
        dc.w    $1065,$0000                 ; 00AD2  attack / loop length (words) = 8394 / 0 bytes
        dc.w    $7148,$0000                 ; 00AD6  period multipliers (PitchTable * mul >> 16)
        dc.b    0,0                         ; 00ADA  volume / pitch envelope speed (ticks per step)
        dc.w    256                         ; 00ADC  instrument volume (x channel volume >> 8; /4 -> AUDxVOL)
Ins33:
        dc.l    Smp08-SampleBase            ; 00ADE  attack sample (offset from SampleBase)
        dc.l    0                           ; 00AE2  loop sample (offset from SampleBase)
        dc.l    0                           ; 00AE6  volume envelope (self-relative)
        dc.l    0                           ; 00AEA  pitch envelope (self-relative)
        dc.w    $0279,$0000                 ; 00AEE  attack / loop length (words) = 1266 / 0 bytes
        dc.w    $5999,$0000                 ; 00AF2  period multipliers (PitchTable * mul >> 16)
        dc.b    0,0                         ; 00AF6  volume / pitch envelope speed (ticks per step)
        dc.w    256                         ; 00AF8  instrument volume (x channel volume >> 8; /4 -> AUDxVOL)
Ins34:
        dc.l    Smp08-SampleBase            ; 00AFA  attack sample (offset from SampleBase)
        dc.l    0                           ; 00AFE  loop sample (offset from SampleBase)
        dc.l    0                           ; 00B02  volume envelope (self-relative)
        dc.l    0                           ; 00B06  pitch envelope (self-relative)
        dc.w    $083C,$0000                 ; 00B0A  attack / loop length (words) = 4216 / 0 bytes
        dc.w    $7000,$0000                 ; 00B0E  period multipliers (PitchTable * mul >> 16)
        dc.b    0,0                         ; 00B12  volume / pitch envelope speed (ticks per step)
        dc.w    256                         ; 00B14  instrument volume (x channel volume >> 8; /4 -> AUDxVOL)
Ins35:
        dc.l    Smp08-SampleBase            ; 00B16  attack sample (offset from SampleBase)
        dc.l    0                           ; 00B1A  loop sample (offset from SampleBase)
        dc.l    0                           ; 00B1E  volume envelope (self-relative)
        dc.l    0                           ; 00B22  pitch envelope (self-relative)
        dc.w    $063F,$0000                 ; 00B26  attack / loop length (words) = 3198 / 0 bytes
        dc.w    $5999,$0000                 ; 00B2A  period multipliers (PitchTable * mul >> 16)
        dc.b    0,0                         ; 00B2E  volume / pitch envelope speed (ticks per step)
        dc.w    256                         ; 00B30  instrument volume (x channel volume >> 8; /4 -> AUDxVOL)
Ins36:
        dc.l    Smp08-SampleBase            ; 00B32  attack sample (offset from SampleBase)
        dc.l    0                           ; 00B36  loop sample (offset from SampleBase)
        dc.l    0                           ; 00B3A  volume envelope (self-relative)
        dc.l    0                           ; 00B3E  pitch envelope (self-relative)
        dc.w    $0C3C,$0000                 ; 00B42  attack / loop length (words) = 6264 / 0 bytes
        dc.w    $5999,$0000                 ; 00B46  period multipliers (PitchTable * mul >> 16)
        dc.b    0,0                         ; 00B4A  volume / pitch envelope speed (ticks per step)
        dc.w    256                         ; 00B4C  instrument volume (x channel volume >> 8; /4 -> AUDxVOL)
Ins37:
        dc.l    Smp05_834-SampleBase        ; 00B4E  attack sample (offset from SampleBase)
        dc.l    0                           ; 00B52  loop sample (offset from SampleBase)
        dc.l    0                           ; 00B56  volume envelope (self-relative)
        dc.l    0                           ; 00B5A  pitch envelope (self-relative)
        dc.w    $0297,$0000                 ; 00B5E  attack / loop length (words) = 1326 / 0 bytes
        dc.w    $7000,$0000                 ; 00B62  period multipliers (PitchTable * mul >> 16)
        dc.b    0,0                         ; 00B66  volume / pitch envelope speed (ticks per step)
        dc.w    256                         ; 00B68  instrument volume (x channel volume >> 8; /4 -> AUDxVOL)
Sfx00_Ch3:
        ENDTRACK                            ; 00B6A
Sfx01_Ch3:
        VOLUME  255                         ; 00B6B
        NOTE    A_5,9,96                    ; 00B6D  n=$45 ins 9 dur 96
        ENDTRACK                            ; 00B71
Sfx02_Ch3:
        VOLUME  255                         ; 00B72
        NOTE    A_5,10,10                   ; 00B74  n=$45 ins 10 dur 10
        NOTE    A_5,10,12                   ; 00B78  n=$45 ins 10 dur 12
        NOTE    A_5,10,24                   ; 00B7C  n=$45 ins 10 dur 24
        ENDTRACK                            ; 00B80
Sfx03_Ch3:
        VOLUME  255                         ; 00B81
        NOTE    A_5,11,96                   ; 00B83  n=$45 ins 11 dur 96
        ENDTRACK                            ; 00B87
Sfx04_Ch3:
        VOLUME  255                         ; 00B88
        NOTE    A_5,12,96                   ; 00B8A  n=$45 ins 12 dur 96
        ENDTRACK                            ; 00B8E
Sfx05_Ch3:
        VOLUME  255                         ; 00B8F
        NOTE    A_5,13,96                   ; 00B91  n=$45 ins 13 dur 96
        ENDTRACK                            ; 00B95
Sfx06_Ch3:
        VOLUME  255                         ; 00B96
        NOTE    A_5,14,96                   ; 00B98  n=$45 ins 14 dur 96
        ENDTRACK                            ; 00B9C
Sfx07_Ch3:
        VOLUME  255                         ; 00B9D
        NOTE    A_5,15,96                   ; 00B9F  n=$45 ins 15 dur 96
        ENDTRACK                            ; 00BA3
Sfx08_Ch3:
        VOLUME  255                         ; 00BA4
        NOTE    A_5,16,96                   ; 00BA6  n=$45 ins 16 dur 96
        ENDTRACK                            ; 00BAA
Sfx09_Ch3:
        VOLUME  255                         ; 00BAB
        NOTE    A_5,17,96                   ; 00BAD  n=$45 ins 17 dur 96
        ENDTRACK                            ; 00BB1
Sfx10_Ch3:
        VOLUME  255                         ; 00BB2
        NOTE    A_5,18,96                   ; 00BB4  n=$45 ins 18 dur 96
        ENDTRACK                            ; 00BB8
Sfx11_Ch3:
        VOLUME  255                         ; 00BB9
        NOTE    A_5,19,96                   ; 00BBB  n=$45 ins 19 dur 96
        ENDTRACK                            ; 00BBF
Sfx12_Ch3:
        VOLUME  255                         ; 00BC0
        NOTE    A_5,20,96                   ; 00BC2  n=$45 ins 20 dur 96
        ENDTRACK                            ; 00BC6
Sfx13_Ch3:
        VOLUME  255                         ; 00BC7
        NOTE    A_5,21,96                   ; 00BC9  n=$45 ins 21 dur 96
        ENDTRACK                            ; 00BCD
Sfx14_Ch3:
        VOLUME  255                         ; 00BCE
        NOTE    A_5,22,96                   ; 00BD0  n=$45 ins 22 dur 96
        ENDTRACK                            ; 00BD4
Sfx15_Ch3:
        VOLUME  255                         ; 00BD5
        NOTE    As5,23,96                   ; 00BD7  n=$46 ins 23 dur 96
        ENDTRACK                            ; 00BDB
Sfx16_Ch3:
        VOLUME  255                         ; 00BDC
        NOTE    A_5,24,96                   ; 00BDE  n=$45 ins 24 dur 96
        ENDTRACK                            ; 00BE2
Sfx17_Ch3:
        VOLUME  255                         ; 00BE3
        NOTE    A_5,25,96                   ; 00BE5  n=$45 ins 25 dur 96
        ENDTRACK                            ; 00BE9
Sfx18_Ch3:
        VOLUME  255                         ; 00BEA
        NOTE    A_5,26,96                   ; 00BEC  n=$45 ins 26 dur 96
        ENDTRACK                            ; 00BF0
Sfx19_Ch3:
        VOLUME  255                         ; 00BF1
        NOTE    A_5,27,96                   ; 00BF3  n=$45 ins 27 dur 96
        ENDTRACK                            ; 00BF7
Sfx20_Ch3:
        VOLUME  255                         ; 00BF8
        NOTE    A_5,28,96                   ; 00BFA  n=$45 ins 28 dur 96
        ENDTRACK                            ; 00BFE
Sfx21_Ch3:
        VOLUME  255                         ; 00BFF
        NOTE    A_5,29,12                   ; 00C01  n=$45 ins 29 dur 12
        NOTE    A_5,29,12                   ; 00C05  n=$45 ins 29 dur 12
        NOTE    A_5,29,24                   ; 00C09  n=$45 ins 29 dur 24
        ENDTRACK                            ; 00C0D
Sfx22_Ch3:
        VOLUME  255                         ; 00C0E
        NOTE    A_5,30,6                    ; 00C10  n=$45 ins 30 dur 6
        NOTE    As5,30,6                    ; 00C14  n=$46 ins 30 dur 6
        NOTE    A_5,30,6                    ; 00C18  n=$45 ins 30 dur 6
        NOTE    As5,30,6                    ; 00C1C  n=$46 ins 30 dur 6
        NOTE    A_5,30,6                    ; 00C20  n=$45 ins 30 dur 6
        NOTE    As5,30,6                    ; 00C24  n=$46 ins 30 dur 6
        ENDTRACK                            ; 00C28
Sfx23_Ch3:
        VOLUME  255                         ; 00C29
        NOTE    A_5,31,96                   ; 00C2B  n=$45 ins 31 dur 96
        ENDTRACK                            ; 00C2F
Sfx24_Ch3:
        VOLUME  255                         ; 00C30
        NOTE    A_5,32,96                   ; 00C32  n=$45 ins 32 dur 96
        ENDTRACK                            ; 00C36
Sfx25_Ch3:
        VOLUME  255                         ; 00C37
        NOTE    A_5,33,96                   ; 00C39  n=$45 ins 33 dur 96
        ENDTRACK                            ; 00C3D
Sfx26_Ch3:
        VOLUME  255                         ; 00C3E
        NOTE    A_5,34,96                   ; 00C40  n=$45 ins 34 dur 96
        ENDTRACK                            ; 00C44
Sfx27_Ch3:
        VOLUME  255                         ; 00C45
        NOTE    A_5,35,96                   ; 00C47  n=$45 ins 35 dur 96
        ENDTRACK                            ; 00C4B
Sfx28_Ch3:
        VOLUME  255                         ; 00C4C
        NOTE    A_5,36,96                   ; 00C4E  n=$45 ins 36 dur 96
        ENDTRACK                            ; 00C52
Sfx29_Ch3:
        VOLUME  255                         ; 00C53
        NOTE    D_5,37,24                   ; 00C55  n=$3E ins 37 dur 24
        ENDTRACK                            ; 00C59
PitchTable:
PatternTable:
        dc.w    $D745,$D42A,$D124,$CE24,$CB30,$C846,$C567,$C292; 00C5A  semitone 0 (octave 0)
        dc.w    $BFC8,$BD08,$BA53,$B7A7,$B505,$B26C,$AFDD,$AD58; 00C6A  semitone 2
        dc.w    $AADC,$A869,$A5FF,$A39D,$A145,$9EF5,$9CAE,$9A6E; 00C7A  semitone 4
        dc.w    $9838,$9609,$93E2,$91C4,$8FAD,$8D9D,$8B96,$8995; 00C8A  semitone 6
        dc.w    $879C,$85AB,$83C0,$81DC,$7FA6,$7E2A,$7C5B,$7A92; 00C9A  semitone 8
        dc.w    $78D1,$761B,$7560,$73B1,$7209,$7066,$6ECA,$6D33; 00CAA  semitone 10
        dc.w    $6BA2,$6A15,$6892,$6712,$6598,$6423,$62B3,$6149; 00CBA  semitone 12 (octave 1)
        dc.w    $5FE4,$5E84,$5D29,$5BD3,$5A82,$5936,$57EE,$56AC; 00CCA  semitone 14
        dc.w    $556E,$5434,$52FF,$51CE,$50A2,$4F7A,$4E57,$4D37; 00CDA  semitone 16
        dc.w    $4C1C,$4B04,$49F1,$48E2,$47D6,$46CE,$45CB,$44CA; 00CEA  semitone 18
        dc.w    $43CE,$42D5,$41E0,$40EE,$3FD3,$3F15,$3E2D,$3D49; 00CFA  semitone 20
        dc.w    $3C68,$3B0D,$3AB0,$39D8,$3904,$3833,$3765,$3699; 00D0A  semitone 22
        dc.w    $35D1,$350A,$3449,$3389,$32CC,$3211,$3159,$30A4; 00D1A  semitone 24 (octave 2)
        dc.w    $2FF2,$2F42,$2E94,$2DE9,$2D41,$2C9B,$2BF7,$2B56; 00D2A  semitone 26
        dc.w    $2AB7,$2A1A,$297F,$28E7,$2851,$27BD,$272B,$269B; 00D3A  semitone 28
        dc.w    $260E,$2582,$24F8,$2471,$23EB,$2367,$22E5,$2265; 00D4A  semitone 30
        dc.w    $21E7,$216A,$20F0,$2077,$1FE9,$1F8A,$1F16,$1EA4; 00D5A  semitone 32
        dc.w    $1E34,$1D86,$1D58,$1CEC,$1C82,$1C19,$1BB2,$1B4C; 00D6A  semitone 34
        dc.w    $1AE8,$1A85,$1A24,$19C4,$1966,$1908,$18AC,$1852; 00D7A  semitone 36 (octave 3)
        dc.w    $17F9,$17A1,$174A,$16F4,$16A0,$164D,$15FB,$15AB; 00D8A  semitone 38
        dc.w    $155B,$150D,$14BF,$1473,$1428,$13DE,$1395,$134D; 00D9A  semitone 40
        dc.w    $1307,$12C1,$127C,$1238,$11F5,$11B3,$1172,$1132; 00DAA  semitone 42
        dc.w    $10F3,$10B5,$1078,$103B,$0FF4,$0FC5,$0F8B,$0F52; 00DBA  semitone 44
        dc.w    $0F1A,$0EC3,$0EAC,$0E76,$0E41,$0E0C,$0DD9,$0DA6; 00DCA  semitone 46
        dc.w    $0D74,$0D42,$0D12,$0CE2,$0CB3,$0C84,$0C56,$0C29; 00DDA  semitone 48 (octave 4)
        dc.w    $0BFC,$0BD0,$0BA5,$0B7A,$0B50,$0B26,$0AFD,$0AD5; 00DEA  semitone 50
        dc.w    $0AAD,$0A86,$0A5F,$0A39,$0A14,$09EF,$09CA,$09A6; 00DFA  semitone 52
        dc.w    $0983,$0960,$093E,$091C,$08FA,$08D9,$08B9,$0899; 00E0A  semitone 54
        dc.w    $0879,$085A,$083C,$081D,$07FA,$07E2,$07C5,$07A9; 00E1A  semitone 56
        dc.w    $078D,$0761,$0756,$073B,$0720,$0706,$06EC,$06D3; 00E2A  semitone 58
        dc.w    $06BA,$06A1,$0689,$0671,$0659,$0642,$062B,$0614; 00E3A  semitone 60 (octave 5)
        dc.w    $05FE,$05E8,$05D2,$05BD,$05A8,$0593,$057E,$056A; 00E4A  semitone 62
        dc.w    $0556,$0543,$052F,$051C,$050A,$04F7,$04E5,$04D3; 00E5A  semitone 64
        dc.w    $04C1,$04B0,$049F,$048E,$047D,$046C,$045C,$044C; 00E6A  semitone 66
        dc.w    $043C,$042D,$041E,$040E,$03FD,$03F1,$03E2,$03D4; 00E7A  semitone 68
        dc.w    $03C6,$03B0,$03AB,$039D,$0390,$0383,$0376,$0369; 00E8A  semitone 70
        dc.w    $035D,$0350,$0344,$0338,$032C,$0321,$0315,$030A; 00E9A  semitone 72 (octave 6)
        dc.w    $02FF,$02F4,$02E9,$02DE,$02D4,$02C9,$02BF,$02B5; 00EAA  semitone 74
        dc.w    $02AB,$02A1,$0297,$028E,$0285,$027B,$0272,$0269; 00EBA  semitone 76
        dc.w    $0260,$0258,$024F,$0247,$023E,$0236,$022E,$0226; 00ECA  semitone 78
        dc.w    $021E,$0216,$020F,$0207,$01FE,$01F8,$01F1,$01EA; 00EDA  semitone 80
        dc.w    $01E3,$01D8,$01D5,$01CE,$01C8,$01C1,$01BB,$01B4; 00EEA  semitone 82
        dc.w    $01AE,$01A8,$01A2,$019C,$0196,$0190,$018A,$0185; 00EFA  semitone 84 (octave 7)
        dc.w    $017F,$017A,$0174,$016F,$016A,$0164,$015F,$015A; 00F0A  semitone 86
        dc.w    $0155,$0150,$014B,$0147,$0142,$013D,$0139,$0134; 00F1A  semitone 88
        dc.w    $0130,$012C,$0127,$0123,$011F,$011B,$0117,$0113; 00F2A  semitone 90
        dc.w    $010F,$010B,$0107,$0103,$00FF,$00FC,$00F8,$00F5; 00F3A  semitone 92
        dc.w    $00F1,$00EC,$00EA,$00E7,$00E4,$00E0,$00DD,$00DA; 00F4A  semitone 94
DriverVars:
        dcb.b   $34E,0                      ; 00F5A  driver variables (see DRV_* / VC_* equates)
NullSample:
SampleBase:
        dcb.b   64,0                        ; 012A8  silent 32-word sample used for stopped channels
SmpHdr00:
        dc.b    $00,$00,$08,$E4,$27,$10     ; 012E8  sample 0 header: length 2276 bytes, 10000 Hz (not used by the driver)
Smp00:
        incbin  "samples/gng_sfx_512k_smp00.raw",0,2276; 012EE  2276 bytes
SmpHdr01:
        dc.b    $00,$00,$07,$9E,$27,$10     ; 01BD2  sample 1 header: length 1950 bytes, 10000 Hz (not used by the driver)
Smp01:
        incbin  "samples/gng_sfx_512k_smp01.raw",0,1950; 01BD8  1950 bytes
SmpHdr02:
        dc.b    $00,$00,$05,$84,$27,$10     ; 02376  sample 2 header: length 1412 bytes, 10000 Hz (not used by the driver)
Smp02:
        incbin  "samples/gng_sfx_512k_smp02.raw",0,1412; 0237C  1412 bytes
SmpHdr03:
        dc.b    $00,$00,$07,$82,$27,$10     ; 02900  sample 3 header: length 1922 bytes, 10000 Hz (not used by the driver)
Smp03:
        incbin  "samples/gng_sfx_512k_smp03.raw",0,1922; 02906  1922 bytes
SmpHdr04:
        dc.b    $00,$00,$0C,$7E,$1F,$40     ; 03088  sample 4 header: length 3198 bytes, 8000 Hz (not used by the driver)
Smp04:
        incbin  "samples/gng_sfx_512k_smp04.raw",0,3198; 0308E  3198 bytes
SmpHdr05:
        dc.b    $00,$00,$0D,$68,$1F,$40     ; 03D0C  sample 5 header: length 3432 bytes, 8000 Hz (not used by the driver)
Smp05:
        incbin  "samples/gng_sfx_512k_smp05.raw",0,2100; 03D12  2100 bytes
Smp05_834:
        incbin  "samples/gng_sfx_512k_smp05.raw",2100,1332; 04546  1332 bytes
SmpHdr06:
        dc.b    $00,$00,$0E,$BE,$1F,$40     ; 04A7A  sample 6 header: length 3774 bytes, 8000 Hz (not used by the driver)
Smp06:
        incbin  "samples/gng_sfx_512k_smp06.raw",0,3774; 04A80  3774 bytes
SmpHdr07:
        dc.b    $00,$00,$0B,$9C,$27,$10     ; 0593E  sample 7 header: length 2972 bytes, 10000 Hz (not used by the driver)
Smp07:
        incbin  "samples/gng_sfx_512k_smp07.raw",0,2972; 05944  2972 bytes
SmpHdr08:
        dc.b    $00,$00,$18,$7E,$27,$10     ; 064E0  sample 8 header: length 6270 bytes, 10000 Hz (not used by the driver)
Smp08:
        incbin  "samples/gng_sfx_512k_smp08.raw",0,6270; 064E6  6270 bytes
