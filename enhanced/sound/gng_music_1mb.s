; =========================================================================
; Ghosts'n Goblins (Elite, 1990) - sound driver + data: gng_music_1mb
; Source file: music_1mb.hunk  (loaded raw at $3604C, called at $3604C+$20)
; Driver: Richard Frankish's music player; music/sfx: Mark Cooksey.
; Assemble: vasmm68k_mot -Fbin -m68000 -no-opt -o gng_music_1mb.bin gng_music_1mb.s
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
	org	$3604C
	endc

HunkHeader:
        dc.l    $000003F3                   ; 00000  HUNK_HEADER
        dc.l    $00000000                   ; 00004  no resident libraries
        dc.l    $00000001                   ; 00008  table size 1
        dc.l    $00000000                   ; 0000C  first hunk 0
        dc.l    $00000000                   ; 00010  last hunk 0
        dc.l    $00006CDD                   ; 00014  hunk 0 size (longs)
        dc.l    $000003E9                   ; 00018  HUNK_CODE
        dc.l    $00006CDD                   ; 0001C  size (longs)

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
        lea.l   SfxTable(pc),a1             ; 000D6  a1 = SfxTable
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
        lea.l   PitchTable(pc),a0           ; 00406
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
        lea.l   PitchTable(pc),a0           ; 005A8
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
MusicTable:
        dc.l    Mus00_Ch0-*                 ; 00612  tune  0  start-of-game fanfare (after the intro)
        dc.l    Mus00_Ch1-*                 ; 00616
        dc.l    Mus00_Ch2-*                 ; 0061A
        dc.l    Mus00_Ch3-*                 ; 0061E
        dc.l    Mus01_Ch0-*                 ; 00622  tune  1  name entry - new top score
        dc.l    Mus01_Ch1-*                 ; 00626
        dc.l    Mus01_Ch2-*                 ; 0062A
        dc.l    Mus01_Ch3-*                 ; 0062E
        dc.l    Mus02_Ch0-*                 ; 00632  tune  2  level music, levels 0-1
        dc.l    Mus02_Ch1-*                 ; 00636
        dc.l    Mus02_Ch2-*                 ; 0063A
        dc.l    Mus02_Ch3-*                 ; 0063E
        dc.l    Mus03_Ch0-*                 ; 00642  tune  3  name entry - high score
        dc.l    Mus03_Ch1-*                 ; 00646
        dc.l    Mus03_Ch2-*                 ; 0064A
        dc.l    Mus03_Ch3-*                 ; 0064E
        dc.l    Mus04_Ch0-*                 ; 00652  tune  4  hurry up! (0:15 left, loops)
        dc.l    Mus04_Ch1-*                 ; 00656
        dc.l    Mus04_Ch2-*                 ; 0065A
        dc.l    Mus04_Ch3-*                 ; 0065E
        dc.l    Mus05_Ch0-*                 ; 00662  tune  5  boss beaten - key appears
        dc.l    Mus05_Ch1-*                 ; 00666
        dc.l    Mus05_Ch2-*                 ; 0066A
        dc.l    Mus05_Ch3-*                 ; 0066E
        dc.l    Mus06_Ch0-*                 ; 00672  tune  6  name entered
        dc.l    Mus06_Ch1-*                 ; 00676
        dc.l    Mus06_Ch2-*                 ; 0067A
        dc.l    Mus06_Ch3-*                 ; 0067E
        dc.l    Mus07_Ch0-*                 ; 00682  tune  7  game over (also Esc abort)
        dc.l    Mus07_Ch1-*                 ; 00686
        dc.l    Mus07_Ch2-*                 ; 0068A
        dc.l    Mus07_Ch3-*                 ; 0068E
        dc.l    Mus08_Ch0-*                 ; 00692  tune  8  life lost
        dc.l    Mus08_Ch1-*                 ; 00696
        dc.l    Mus08_Ch2-*                 ; 0069A
        dc.l    Mus08_Ch3-*                 ; 0069E
        dc.l    Mus09_Ch0-*                 ; 006A2  tune  9  not referenced by the game
        dc.l    Mus09_Ch1-*                 ; 006A6
        dc.l    Mus09_Ch2-*                 ; 006AA
        dc.l    Mus09_Ch3-*                 ; 006AE
        dc.l    Mus10_Ch0-*                 ; 006B2  tune 10  not referenced by the game
        dc.l    Mus10_Ch1-*                 ; 006B6
        dc.l    Mus10_Ch2-*                 ; 006BA
        dc.l    Mus10_Ch3-*                 ; 006BE
        dc.l    Mus11_Ch0-*                 ; 006C2  tune 11  not referenced by the game
        dc.l    Mus11_Ch1-*                 ; 006C6
        dc.l    Mus11_Ch2-*                 ; 006CA
        dc.l    Mus11_Ch3-*                 ; 006CE
        dc.l    Mus12_Ch0-*                 ; 006D2  tune 12  level music, levels 5-6
        dc.l    Mus12_Ch1-*                 ; 006D6
        dc.l    Mus12_Ch2-*                 ; 006DA
        dc.l    Mus12_Ch3-*                 ; 006DE
        dc.l    Mus13_Ch0-*                 ; 006E2  tune 13  level music, levels 2-4
        dc.l    Mus13_Ch1-*                 ; 006E6
        dc.l    Mus13_Ch2-*                 ; 006EA
        dc.l    Mus13_Ch3-*                 ; 006EE
        dc.l    Mus14_Ch0-*                 ; 006F2  tune 14  intro cut-scene
        dc.l    Mus14_Ch1-*                 ; 006F6
        dc.l    Mus14_Ch2-*                 ; 006FA
        dc.l    Mus14_Ch3-*                 ; 006FE
SfxTable:
        dc.l    0                           ; 00702  sfx  0  
        dc.l    0                           ; 00706
        dc.l    0                           ; 0070A
        dc.l    Sfx00_Ch3-*                 ; 0070E
        dc.l    0                           ; 00712  sfx  1  Arthur hit (armour lost)
        dc.l    0                           ; 00716
        dc.l    0                           ; 0071A
        dc.l    Sfx01_Ch3-*                 ; 0071E
        dc.l    0                           ; 00722  sfx  2  
        dc.l    0                           ; 00726
        dc.l    0                           ; 0072A
        dc.l    Sfx02_Ch3-*                 ; 0072E
        dc.l    0                           ; 00732  sfx  3  
        dc.l    0                           ; 00736
        dc.l    0                           ; 0073A
        dc.l    Sfx03_Ch3-*                 ; 0073E
        dc.l    0                           ; 00742  sfx  4  jump
        dc.l    0                           ; 00746
        dc.l    0                           ; 0074A
        dc.l    Sfx04_Ch3-*                 ; 0074E
        dc.l    0                           ; 00752  sfx  5  land
        dc.l    0                           ; 00756
        dc.l    0                           ; 0075A
        dc.l    Sfx05_Ch3-*                 ; 0075E
        dc.l    0                           ; 00762  sfx  6  throw weapon
        dc.l    0                           ; 00766
        dc.l    0                           ; 0076A
        dc.l    Sfx06_Ch3-*                 ; 0076E
        dc.l    0                           ; 00772  sfx  7  
        dc.l    0                           ; 00776
        dc.l    0                           ; 0077A
        dc.l    Sfx07_Ch3-*                 ; 0077E
        dc.l    0                           ; 00782  sfx  8  
        dc.l    0                           ; 00786
        dc.l    0                           ; 0078A
        dc.l    Sfx08_Ch3-*                 ; 0078E
        dc.l    0                           ; 00792  sfx  9  
        dc.l    0                           ; 00796
        dc.l    0                           ; 0079A
        dc.l    Sfx09_Ch3-*                 ; 0079E
        dc.l    0                           ; 007A2  sfx 10  weapon shot event
        dc.l    0                           ; 007A6
        dc.l    0                           ; 007AA
        dc.l    Sfx10_Ch3-*                 ; 007AE
        dc.l    0                           ; 007B2  sfx 11  torch flame (1MB build)
        dc.l    0                           ; 007B6
        dc.l    0                           ; 007BA
        dc.l    Sfx11_Ch3-*                 ; 007BE
        dc.l    0                           ; 007C2  sfx 12  weapon / boss hit
        dc.l    0                           ; 007C6
        dc.l    0                           ; 007CA
        dc.l    Sfx12_Ch3-*                 ; 007CE
        dc.l    0                           ; 007D2  sfx 13  
        dc.l    0                           ; 007D6
        dc.l    0                           ; 007DA
        dc.l    Sfx13_Ch3-*                 ; 007DE
        dc.l    0                           ; 007E2  sfx 14  
        dc.l    0                           ; 007E6
        dc.l    0                           ; 007EA
        dc.l    Sfx14_Ch3-*                 ; 007EE
        dc.l    0                           ; 007F2  sfx 15  
        dc.l    0                           ; 007F6
        dc.l    0                           ; 007FA
        dc.l    Sfx15_Ch3-*                 ; 007FE
        dc.l    0                           ; 00802  sfx 16  
        dc.l    0                           ; 00806
        dc.l    0                           ; 0080A
        dc.l    Sfx16_Ch3-*                 ; 0080E
        dc.l    0                           ; 00812  sfx 17  enemy event (crow, blue killer, ghost, skeleton)
        dc.l    0                           ; 00816
        dc.l    0                           ; 0081A
        dc.l    Sfx17_Ch3-*                 ; 0081E
        dc.l    0                           ; 00822  sfx 18  
        dc.l    0                           ; 00826
        dc.l    0                           ; 0082A
        dc.l    Sfx18_Ch3-*                 ; 0082E
        dc.l    0                           ; 00832  sfx 19  
        dc.l    0                           ; 00836
        dc.l    0                           ; 0083A
        dc.l    Sfx19_Ch3-*                 ; 0083E
        dc.l    0                           ; 00842  sfx 20  enemy event (flying knight, zombie, Astaroth)
        dc.l    0                           ; 00846
        dc.l    0                           ; 0084A
        dc.l    Sfx20_Ch3-*                 ; 0084E
        dc.l    0                           ; 00852  sfx 21  
        dc.l    0                           ; 00856
        dc.l    0                           ; 0085A
        dc.l    Sfx21_Ch3-*                 ; 0085E
        dc.l    0                           ; 00862  sfx 22  
        dc.l    0                           ; 00866
        dc.l    0                           ; 0086A
        dc.l    Sfx22_Ch3-*                 ; 0086E
        dc.l    0                           ; 00872  sfx 23  
        dc.l    0                           ; 00876
        dc.l    0                           ; 0087A
        dc.l    Sfx23_Ch3-*                 ; 0087E
        dc.l    0                           ; 00882  sfx 24  
        dc.l    0                           ; 00886
        dc.l    0                           ; 0088A
        dc.l    Sfx24_Ch3-*                 ; 0088E
        dc.l    0                           ; 00892  sfx 25  
        dc.l    0                           ; 00896
        dc.l    0                           ; 0089A
        dc.l    Sfx25_Ch3-*                 ; 0089E
        dc.l    0                           ; 008A2  sfx 26  
        dc.l    0                           ; 008A6
        dc.l    0                           ; 008AA
        dc.l    Sfx26_Ch3-*                 ; 008AE
        dc.l    0                           ; 008B2  sfx 27  
        dc.l    0                           ; 008B6
        dc.l    0                           ; 008BA
        dc.l    Sfx27_Ch3-*                 ; 008BE
        dc.l    0                           ; 008C2  sfx 28  key / item collected
        dc.l    0                           ; 008C6
        dc.l    0                           ; 008CA
        dc.l    Sfx28_Ch3-*                 ; 008CE
        dc.l    0                           ; 008D2  sfx 29  
        dc.l    0                           ; 008D6
        dc.l    0                           ; 008DA
        dc.l    Sfx29_Ch3-*                 ; 008DE
InstrumentTable:
        dc.w    Ins00-*                     ; 008E2  instrument 0
        dc.w    Ins01-*                     ; 008E4  instrument 1
        dc.w    Ins02-*                     ; 008E6  instrument 2
        dc.w    Ins03-*                     ; 008E8  instrument 3
        dc.w    Ins04-*                     ; 008EA  instrument 4
        dc.w    Ins05-*                     ; 008EC  instrument 5
        dc.w    Ins06-*                     ; 008EE  instrument 6
        dc.w    Ins07-*                     ; 008F0  instrument 7
        dc.w    Ins08-*                     ; 008F2  instrument 8
        dc.w    Ins09-*                     ; 008F4  instrument 9
        dc.w    Ins10-*                     ; 008F6  instrument 10
        dc.w    Ins11-*                     ; 008F8  instrument 11
        dc.w    Ins12-*                     ; 008FA  instrument 12
        dc.w    Ins13-*                     ; 008FC  instrument 13
        dc.w    Ins14-*                     ; 008FE  instrument 14
        dc.w    Ins15-*                     ; 00900  instrument 15
        dc.w    Ins16-*                     ; 00902  instrument 16
        dc.w    Ins17-*                     ; 00904  instrument 17
        dc.w    Ins18-*                     ; 00906  instrument 18
        dc.w    Ins19-*                     ; 00908  instrument 19
        dc.w    Ins20-*                     ; 0090A  instrument 20
        dc.w    Ins21-*                     ; 0090C  instrument 21
        dc.w    Ins22-*                     ; 0090E  instrument 22
        dc.w    Ins23-*                     ; 00910  instrument 23
        dc.w    Ins24-*                     ; 00912  instrument 24
        dc.w    Ins25-*                     ; 00914  instrument 25
        dc.w    Ins26-*                     ; 00916  instrument 26
        dc.w    Ins27-*                     ; 00918  instrument 27
        dc.w    Ins28-*                     ; 0091A  instrument 28
        dc.w    Ins29-*                     ; 0091C  instrument 29
        dc.w    Ins30-*                     ; 0091E  instrument 30
        dc.w    Ins31-*                     ; 00920  instrument 31
        dc.w    Ins32-*                     ; 00922  instrument 32
        dc.w    Ins33-*                     ; 00924  instrument 33
        dc.w    Ins34-*                     ; 00926  instrument 34
        dc.w    Ins35-*                     ; 00928  instrument 35
        dc.w    Ins36-*                     ; 0092A  instrument 36
        dc.w    Ins37-*                     ; 0092C  instrument 37
Ins00:
        dc.l    Smp04-SampleBase            ; 0092E  attack sample (offset from SampleBase)
        dc.l    Smp04-SampleBase            ; 00932  loop sample (offset from SampleBase)
        dc.l    VolEnv_2DCF-*               ; 00936  volume envelope (self-relative)
        dc.l    0                           ; 0093A  pitch envelope (self-relative)
        dc.w    $003A,$003A                 ; 0093E  attack / loop length (words) = 116 / 116 bytes
        dc.w    $8080,$8080                 ; 00942  period multipliers (PitchTable * mul >> 16)
        dc.b    1,0                         ; 00946  volume / pitch envelope speed (ticks per step)
        dc.w    128                         ; 00948  instrument volume (x channel volume >> 8; /4 -> AUDxVOL)
Ins01:
        dc.l    Smp03-SampleBase            ; 0094A  attack sample (offset from SampleBase)
        dc.l    Smp03-SampleBase            ; 0094E  loop sample (offset from SampleBase)
        dc.l    VolEnv_2DCF-*               ; 00952  volume envelope (self-relative)
        dc.l    0                           ; 00956  pitch envelope (self-relative)
        dc.w    $0055,$0055                 ; 0095A  attack / loop length (words) = 170 / 170 bytes
        dc.w    $8080,$8080                 ; 0095E  period multipliers (PitchTable * mul >> 16)
        dc.b    1,0                         ; 00962  volume / pitch envelope speed (ticks per step)
        dc.w    128                         ; 00964  instrument volume (x channel volume >> 8; /4 -> AUDxVOL)
Ins02:
        dc.l    Smp02-SampleBase            ; 00966  attack sample (offset from SampleBase)
        dc.l    Smp02-SampleBase            ; 0096A  loop sample (offset from SampleBase)
        dc.l    VolEnv_2DCF-*               ; 0096E  volume envelope (self-relative)
        dc.l    0                           ; 00972  pitch envelope (self-relative)
        dc.w    $007C,$007C                 ; 00976  attack / loop length (words) = 248 / 248 bytes
        dc.w    $8080,$8080                 ; 0097A  period multipliers (PitchTable * mul >> 16)
        dc.b    1,0                         ; 0097E  volume / pitch envelope speed (ticks per step)
        dc.w    128                         ; 00980  instrument volume (x channel volume >> 8; /4 -> AUDxVOL)
Ins03:
        dc.l    Smp01-SampleBase            ; 00982  attack sample (offset from SampleBase)
        dc.l    Smp01-SampleBase            ; 00986  loop sample (offset from SampleBase)
        dc.l    VolEnv_2DCF-*               ; 0098A  volume envelope (self-relative)
        dc.l    0                           ; 0098E  pitch envelope (self-relative)
        dc.w    $00BA,$00BA                 ; 00992  attack / loop length (words) = 372 / 372 bytes
        dc.w    $8080,$8080                 ; 00996  period multipliers (PitchTable * mul >> 16)
        dc.b    1,0                         ; 0099A  volume / pitch envelope speed (ticks per step)
        dc.w    128                         ; 0099C  instrument volume (x channel volume >> 8; /4 -> AUDxVOL)
Ins04:
        dc.l    Smp00-SampleBase            ; 0099E  attack sample (offset from SampleBase)
        dc.l    Smp00-SampleBase            ; 009A2  loop sample (offset from SampleBase)
        dc.l    VolEnv_2DCF-*               ; 009A6  volume envelope (self-relative)
        dc.l    0                           ; 009AA  pitch envelope (self-relative)
        dc.w    $0174,$0174                 ; 009AE  attack / loop length (words) = 744 / 744 bytes
        dc.w    $8080,$8080                 ; 009B2  period multipliers (PitchTable * mul >> 16)
        dc.b    1,0                         ; 009B6  volume / pitch envelope speed (ticks per step)
        dc.w    128                         ; 009B8  instrument volume (x channel volume >> 8; /4 -> AUDxVOL)
Ins05:
        dc.l    Smp08-SampleBase            ; 009BA  attack sample (offset from SampleBase)
        dc.l    Smp08-SampleBase            ; 009BE  loop sample (offset from SampleBase)
        dc.l    0                           ; 009C2  volume envelope (self-relative)
        dc.l    0                           ; 009C6  pitch envelope (self-relative)
        dc.w    $1A73,$1A73                 ; 009CA  attack / loop length (words) = 13542 / 13542 bytes
        dc.w    $7E40,$7E40                 ; 009CE  period multipliers (PitchTable * mul >> 16)
        dc.b    0,0                         ; 009D2  volume / pitch envelope speed (ticks per step)
        dc.w    255                         ; 009D4  instrument volume (x channel volume >> 8; /4 -> AUDxVOL)
Ins06:
        dc.l    Smp05-SampleBase            ; 009D6  attack sample (offset from SampleBase)
        dc.l    Smp07-SampleBase            ; 009DA  loop sample (offset from SampleBase)
        dc.l    0                           ; 009DE  volume envelope (self-relative)
        dc.l    0                           ; 009E2  pitch envelope (self-relative)
        dc.w    $1128,$07C1                 ; 009E6  attack / loop length (words) = 8784 / 3970 bytes
        dc.w    $8000,$8000                 ; 009EA  period multipliers (PitchTable * mul >> 16)
        dc.b    0,0                         ; 009EE  volume / pitch envelope speed (ticks per step)
        dc.w    255                         ; 009F0  instrument volume (x channel volume >> 8; /4 -> AUDxVOL)
Ins07:
        dc.l    Smp06-SampleBase            ; 009F2  attack sample (offset from SampleBase)
        dc.l    Smp10-SampleBase            ; 009F6  loop sample (offset from SampleBase)
        dc.l    0                           ; 009FA  volume envelope (self-relative)
        dc.l    0                           ; 009FE  pitch envelope (self-relative)
        dc.w    $0E9F,$0B9D                 ; 00A02  attack / loop length (words) = 7486 / 5946 bytes
        dc.w    $8000,$8000                 ; 00A06  period multipliers (PitchTable * mul >> 16)
        dc.b    0,0                         ; 00A0A  volume / pitch envelope speed (ticks per step)
        dc.w    255                         ; 00A0C  instrument volume (x channel volume >> 8; /4 -> AUDxVOL)
Ins08:
        dc.l    Smp06-SampleBase            ; 00A0E  attack sample (offset from SampleBase)
        dc.l    Smp09-SampleBase            ; 00A12  loop sample (offset from SampleBase)
        dc.l    VolEnv_2E48-*               ; 00A16  volume envelope (self-relative)
        dc.l    0                           ; 00A1A  pitch envelope (self-relative)
        dc.w    $0664,$062B                 ; 00A1E  attack / loop length (words) = 3272 / 3158 bytes
        dc.w    $8000,$8000                 ; 00A22  period multipliers (PitchTable * mul >> 16)
        dc.b    1,0                         ; 00A26  volume / pitch envelope speed (ticks per step)
        dc.w    255                         ; 00A28  instrument volume (x channel volume >> 8; /4 -> AUDxVOL)
Ins09:
        dc.l    Smp10-SampleBase            ; 00A2A  attack sample (offset from SampleBase)
        dc.l    0                           ; 00A2E  loop sample (offset from SampleBase)
        dc.l    0                           ; 00A32  volume envelope (self-relative)
        dc.l    0                           ; 00A36  pitch envelope (self-relative)
        dc.w    $0472,$0000                 ; 00A3A  attack / loop length (words) = 2276 / 0 bytes
        dc.w    $5999,$0000                 ; 00A3E  period multipliers (PitchTable * mul >> 16)
        dc.b    0,0                         ; 00A42  volume / pitch envelope speed (ticks per step)
        dc.w    256                         ; 00A44  instrument volume (x channel volume >> 8; /4 -> AUDxVOL)
Ins10:
        dc.l    Smp11-SampleBase            ; 00A46  attack sample (offset from SampleBase)
        dc.l    0                           ; 00A4A  loop sample (offset from SampleBase)
        dc.l    0                           ; 00A4E  volume envelope (self-relative)
        dc.l    0                           ; 00A52  pitch envelope (self-relative)
        dc.w    $0457,$0000                 ; 00A56  attack / loop length (words) = 2222 / 0 bytes
        dc.w    $5999,$0000                 ; 00A5A  period multipliers (PitchTable * mul >> 16)
        dc.b    0,0                         ; 00A5E  volume / pitch envelope speed (ticks per step)
        dc.w    256                         ; 00A60  instrument volume (x channel volume >> 8; /4 -> AUDxVOL)
Ins11:
        dc.l    Smp11-SampleBase            ; 00A62  attack sample (offset from SampleBase)
        dc.l    0                           ; 00A66  loop sample (offset from SampleBase)
        dc.l    0                           ; 00A6A  volume envelope (self-relative)
        dc.l    0                           ; 00A6E  pitch envelope (self-relative)
        dc.w    $0D39,$0000                 ; 00A72  attack / loop length (words) = 6770 / 0 bytes
        dc.w    $8000,$0000                 ; 00A76  period multipliers (PitchTable * mul >> 16)
        dc.b    0,0                         ; 00A7A  volume / pitch envelope speed (ticks per step)
        dc.w    256                         ; 00A7C  instrument volume (x channel volume >> 8; /4 -> AUDxVOL)
Ins12:
        dc.l    Smp11-SampleBase            ; 00A7E  attack sample (offset from SampleBase)
        dc.l    0                           ; 00A82  loop sample (offset from SampleBase)
        dc.l    0                           ; 00A86  volume envelope (self-relative)
        dc.l    0                           ; 00A8A  pitch envelope (self-relative)
        dc.w    $03CF,$0000                 ; 00A8E  attack / loop length (words) = 1950 / 0 bytes
        dc.w    $5999,$0000                 ; 00A92  period multipliers (PitchTable * mul >> 16)
        dc.b    0,0                         ; 00A96  volume / pitch envelope speed (ticks per step)
        dc.w    256                         ; 00A98  instrument volume (x channel volume >> 8; /4 -> AUDxVOL)
Ins13:
        dc.l    Smp12-SampleBase            ; 00A9A  attack sample (offset from SampleBase)
        dc.l    0                           ; 00A9E  loop sample (offset from SampleBase)
        dc.l    0                           ; 00AA2  volume envelope (self-relative)
        dc.l    0                           ; 00AA6  pitch envelope (self-relative)
        dc.w    $02C2,$0000                 ; 00AAA  attack / loop length (words) = 1412 / 0 bytes
        dc.w    $5999,$0000                 ; 00AAE  period multipliers (PitchTable * mul >> 16)
        dc.b    0,0                         ; 00AB2  volume / pitch envelope speed (ticks per step)
        dc.w    256                         ; 00AB4  instrument volume (x channel volume >> 8; /4 -> AUDxVOL)
Ins14:
        dc.l    Smp13-SampleBase            ; 00AB6  attack sample (offset from SampleBase)
        dc.l    0                           ; 00ABA  loop sample (offset from SampleBase)
        dc.l    0                           ; 00ABE  volume envelope (self-relative)
        dc.l    0                           ; 00AC2  pitch envelope (self-relative)
        dc.w    $03C1,$0000                 ; 00AC6  attack / loop length (words) = 1922 / 0 bytes
        dc.w    $5999,$0000                 ; 00ACA  period multipliers (PitchTable * mul >> 16)
        dc.b    0,0                         ; 00ACE  volume / pitch envelope speed (ticks per step)
        dc.w    256                         ; 00AD0  instrument volume (x channel volume >> 8; /4 -> AUDxVOL)
Ins15:
        dc.l    Smp14-SampleBase            ; 00AD2  attack sample (offset from SampleBase)
        dc.l    0                           ; 00AD6  loop sample (offset from SampleBase)
        dc.l    0                           ; 00ADA  volume envelope (self-relative)
        dc.l    0                           ; 00ADE  pitch envelope (self-relative)
        dc.w    $0A2A,$0000                 ; 00AE2  attack / loop length (words) = 5204 / 0 bytes
        dc.w    $7000,$0000                 ; 00AE6  period multipliers (PitchTable * mul >> 16)
        dc.b    0,0                         ; 00AEA  volume / pitch envelope speed (ticks per step)
        dc.w    256                         ; 00AEC  instrument volume (x channel volume >> 8; /4 -> AUDxVOL)
Ins16:
        dc.l    Smp14-SampleBase            ; 00AEE  attack sample (offset from SampleBase)
        dc.l    0                           ; 00AF2  loop sample (offset from SampleBase)
        dc.l    0                           ; 00AF6  volume envelope (self-relative)
        dc.l    0                           ; 00AFA  pitch envelope (self-relative)
        dc.w    $095A,$0000                 ; 00AFE  attack / loop length (words) = 4788 / 0 bytes
        dc.w    $7000,$0000                 ; 00B02  period multipliers (PitchTable * mul >> 16)
        dc.b    0,0                         ; 00B06  volume / pitch envelope speed (ticks per step)
        dc.w    256                         ; 00B08  instrument volume (x channel volume >> 8; /4 -> AUDxVOL)
Ins17:
        dc.l    Smp14-SampleBase            ; 00B0A  attack sample (offset from SampleBase)
        dc.l    0                           ; 00B0E  loop sample (offset from SampleBase)
        dc.l    0                           ; 00B12  volume envelope (self-relative)
        dc.l    0                           ; 00B16  pitch envelope (self-relative)
        dc.w    $082A,$0000                 ; 00B1A  attack / loop length (words) = 4180 / 0 bytes
        dc.w    $7000,$0000                 ; 00B1E  period multipliers (PitchTable * mul >> 16)
        dc.b    0,0                         ; 00B22  volume / pitch envelope speed (ticks per step)
        dc.w    256                         ; 00B24  instrument volume (x channel volume >> 8; /4 -> AUDxVOL)
Ins18:
        dc.l    Smp15-SampleBase            ; 00B26  attack sample (offset from SampleBase)
        dc.l    0                           ; 00B2A  loop sample (offset from SampleBase)
        dc.l    0                           ; 00B2E  volume envelope (self-relative)
        dc.l    0                           ; 00B32  pitch envelope (self-relative)
        dc.w    $063C,$0000                 ; 00B36  attack / loop length (words) = 3192 / 0 bytes
        dc.w    $7000,$0000                 ; 00B3A  period multipliers (PitchTable * mul >> 16)
        dc.b    0,0                         ; 00B3E  volume / pitch envelope speed (ticks per step)
        dc.w    256                         ; 00B40  instrument volume (x channel volume >> 8; /4 -> AUDxVOL)
Ins19:
        dc.l    Smp16-SampleBase            ; 00B42  attack sample (offset from SampleBase)
        dc.l    0                           ; 00B46  loop sample (offset from SampleBase)
        dc.l    0                           ; 00B4A  volume envelope (self-relative)
        dc.l    0                           ; 00B4E  pitch envelope (self-relative)
        dc.w    $06F1,$0000                 ; 00B52  attack / loop length (words) = 3554 / 0 bytes
        dc.w    $7000,$0000                 ; 00B56  period multipliers (PitchTable * mul >> 16)
        dc.b    0,0                         ; 00B5A  volume / pitch envelope speed (ticks per step)
        dc.w    256                         ; 00B5C  instrument volume (x channel volume >> 8; /4 -> AUDxVOL)
Ins20:
        dc.l    Smp17-SampleBase            ; 00B5E  attack sample (offset from SampleBase)
        dc.l    0                           ; 00B62  loop sample (offset from SampleBase)
        dc.l    0                           ; 00B66  volume envelope (self-relative)
        dc.l    0                           ; 00B6A  pitch envelope (self-relative)
        dc.w    $06B1,$0000                 ; 00B6E  attack / loop length (words) = 3426 / 0 bytes
        dc.w    $7000,$0000                 ; 00B72  period multipliers (PitchTable * mul >> 16)
        dc.b    0,0                         ; 00B76  volume / pitch envelope speed (ticks per step)
        dc.w    256                         ; 00B78  instrument volume (x channel volume >> 8; /4 -> AUDxVOL)
Ins21:
        dc.l    Smp18-SampleBase            ; 00B7A  attack sample (offset from SampleBase)
        dc.l    0                           ; 00B7E  loop sample (offset from SampleBase)
        dc.l    0                           ; 00B82  volume envelope (self-relative)
        dc.l    0                           ; 00B86  pitch envelope (self-relative)
        dc.w    $063C,$0000                 ; 00B8A  attack / loop length (words) = 3192 / 0 bytes
        dc.w    $7000,$0000                 ; 00B8E  period multipliers (PitchTable * mul >> 16)
        dc.b    0,0                         ; 00B92  volume / pitch envelope speed (ticks per step)
        dc.w    256                         ; 00B94  instrument volume (x channel volume >> 8; /4 -> AUDxVOL)
Ins22:
        dc.l    Smp18-SampleBase            ; 00B96  attack sample (offset from SampleBase)
        dc.l    0                           ; 00B9A  loop sample (offset from SampleBase)
        dc.l    0                           ; 00B9E  volume envelope (self-relative)
        dc.l    0                           ; 00BA2  pitch envelope (self-relative)
        dc.w    $08FD,$0000                 ; 00BA6  attack / loop length (words) = 4602 / 0 bytes
        dc.w    $7000,$0000                 ; 00BAA  period multipliers (PitchTable * mul >> 16)
        dc.b    0,0                         ; 00BAE  volume / pitch envelope speed (ticks per step)
        dc.w    256                         ; 00BB0  instrument volume (x channel volume >> 8; /4 -> AUDxVOL)
Ins23:
        dc.l    Smp19-SampleBase            ; 00BB2  attack sample (offset from SampleBase)
        dc.l    0                           ; 00BB6  loop sample (offset from SampleBase)
        dc.l    0                           ; 00BBA  volume envelope (self-relative)
        dc.l    0                           ; 00BBE  pitch envelope (self-relative)
        dc.w    $09B4,$0000                 ; 00BC2  attack / loop length (words) = 4968 / 0 bytes
        dc.w    $7000,$0000                 ; 00BC6  period multipliers (PitchTable * mul >> 16)
        dc.b    0,0                         ; 00BCA  volume / pitch envelope speed (ticks per step)
        dc.w    256                         ; 00BCC  instrument volume (x channel volume >> 8; /4 -> AUDxVOL)
Ins24:
        dc.l    Smp19-SampleBase            ; 00BCE  attack sample (offset from SampleBase)
        dc.l    0                           ; 00BD2  loop sample (offset from SampleBase)
        dc.l    0                           ; 00BD6  volume envelope (self-relative)
        dc.l    0                           ; 00BDA  pitch envelope (self-relative)
        dc.w    $0129,$0000                 ; 00BDE  attack / loop length (words) = 594 / 0 bytes
        dc.w    $5999,$0000                 ; 00BE2  period multipliers (PitchTable * mul >> 16)
        dc.b    0,0                         ; 00BE6  volume / pitch envelope speed (ticks per step)
        dc.w    256                         ; 00BE8  instrument volume (x channel volume >> 8; /4 -> AUDxVOL)
Ins25:
        dc.l    Smp19-SampleBase            ; 00BEA  attack sample (offset from SampleBase)
        dc.l    0                           ; 00BEE  loop sample (offset from SampleBase)
        dc.l    0                           ; 00BF2  volume envelope (self-relative)
        dc.l    0                           ; 00BF6  pitch envelope (self-relative)
        dc.w    $075D,$0000                 ; 00BFA  attack / loop length (words) = 3770 / 0 bytes
        dc.w    $7000,$0000                 ; 00BFE  period multipliers (PitchTable * mul >> 16)
        dc.b    0,0                         ; 00C02  volume / pitch envelope speed (ticks per step)
        dc.w    256                         ; 00C04  instrument volume (x channel volume >> 8; /4 -> AUDxVOL)
Ins26:
        dc.l    Smp20-SampleBase            ; 00C06  attack sample (offset from SampleBase)
        dc.l    0                           ; 00C0A  loop sample (offset from SampleBase)
        dc.l    0                           ; 00C0E  volume envelope (self-relative)
        dc.l    0                           ; 00C12  pitch envelope (self-relative)
        dc.w    $1158,$0000                 ; 00C16  attack / loop length (words) = 8880 / 0 bytes
        dc.w    $7148,$0000                 ; 00C1A  period multipliers (PitchTable * mul >> 16)
        dc.b    0,0                         ; 00C1E  volume / pitch envelope speed (ticks per step)
        dc.w    256                         ; 00C20  instrument volume (x channel volume >> 8; /4 -> AUDxVOL)
Ins27:
        dc.l    Smp21-SampleBase            ; 00C22  attack sample (offset from SampleBase)
        dc.l    0                           ; 00C26  loop sample (offset from SampleBase)
        dc.l    0                           ; 00C2A  volume envelope (self-relative)
        dc.l    0                           ; 00C2E  pitch envelope (self-relative)
        dc.w    $03C0,$0000                 ; 00C32  attack / loop length (words) = 1920 / 0 bytes
        dc.w    $5999,$0000                 ; 00C36  period multipliers (PitchTable * mul >> 16)
        dc.b    0,0                         ; 00C3A  volume / pitch envelope speed (ticks per step)
        dc.w    256                         ; 00C3C  instrument volume (x channel volume >> 8; /4 -> AUDxVOL)
Ins28:
        dc.l    Smp22-SampleBase            ; 00C3E  attack sample (offset from SampleBase)
        dc.l    0                           ; 00C42  loop sample (offset from SampleBase)
        dc.l    0                           ; 00C46  volume envelope (self-relative)
        dc.l    0                           ; 00C4A  pitch envelope (self-relative)
        dc.w    $05CE,$0000                 ; 00C4E  attack / loop length (words) = 2972 / 0 bytes
        dc.w    $5999,$0000                 ; 00C52  period multipliers (PitchTable * mul >> 16)
        dc.b    0,0                         ; 00C56  volume / pitch envelope speed (ticks per step)
        dc.w    256                         ; 00C58  instrument volume (x channel volume >> 8; /4 -> AUDxVOL)
Ins29:
        dc.l    Smp23-SampleBase            ; 00C5A  attack sample (offset from SampleBase)
        dc.l    0                           ; 00C5E  loop sample (offset from SampleBase)
        dc.l    0                           ; 00C62  volume envelope (self-relative)
        dc.l    0                           ; 00C66  pitch envelope (self-relative)
        dc.w    $0526,$0000                 ; 00C6A  attack / loop length (words) = 2636 / 0 bytes
        dc.w    $5999,$0000                 ; 00C6E  period multipliers (PitchTable * mul >> 16)
        dc.b    0,0                         ; 00C72  volume / pitch envelope speed (ticks per step)
        dc.w    256                         ; 00C74  instrument volume (x channel volume >> 8; /4 -> AUDxVOL)
Ins30:
        dc.l    Smp23-SampleBase            ; 00C76  attack sample (offset from SampleBase)
        dc.l    0                           ; 00C7A  loop sample (offset from SampleBase)
        dc.l    0                           ; 00C7E  volume envelope (self-relative)
        dc.l    0                           ; 00C82  pitch envelope (self-relative)
        dc.w    $012A,$0000                 ; 00C86  attack / loop length (words) = 596 / 0 bytes
        dc.w    $5999,$0000                 ; 00C8A  period multipliers (PitchTable * mul >> 16)
        dc.b    0,0                         ; 00C8E  volume / pitch envelope speed (ticks per step)
        dc.w    256                         ; 00C90  instrument volume (x channel volume >> 8; /4 -> AUDxVOL)
Ins31:
        dc.l    Smp24-SampleBase            ; 00C92  attack sample (offset from SampleBase)
        dc.l    0                           ; 00C96  loop sample (offset from SampleBase)
        dc.l    0                           ; 00C9A  volume envelope (self-relative)
        dc.l    0                           ; 00C9E  pitch envelope (self-relative)
        dc.w    $011D,$0000                 ; 00CA2  attack / loop length (words) = 570 / 0 bytes
        dc.w    $5999,$0000                 ; 00CA6  period multipliers (PitchTable * mul >> 16)
        dc.b    0,0                         ; 00CAA  volume / pitch envelope speed (ticks per step)
        dc.w    256                         ; 00CAC  instrument volume (x channel volume >> 8; /4 -> AUDxVOL)
Ins32:
        dc.l    Smp25-SampleBase            ; 00CAE  attack sample (offset from SampleBase)
        dc.l    0                           ; 00CB2  loop sample (offset from SampleBase)
        dc.l    0                           ; 00CB6  volume envelope (self-relative)
        dc.l    0                           ; 00CBA  pitch envelope (self-relative)
        dc.w    $1065,$0000                 ; 00CBE  attack / loop length (words) = 8394 / 0 bytes
        dc.w    $7148,$0000                 ; 00CC2  period multipliers (PitchTable * mul >> 16)
        dc.b    0,0                         ; 00CC6  volume / pitch envelope speed (ticks per step)
        dc.w    256                         ; 00CC8  instrument volume (x channel volume >> 8; /4 -> AUDxVOL)
Ins33:
        dc.l    Smp26-SampleBase            ; 00CCA  attack sample (offset from SampleBase)
        dc.l    0                           ; 00CCE  loop sample (offset from SampleBase)
        dc.l    0                           ; 00CD2  volume envelope (self-relative)
        dc.l    0                           ; 00CD6  pitch envelope (self-relative)
        dc.w    $0279,$0000                 ; 00CDA  attack / loop length (words) = 1266 / 0 bytes
        dc.w    $5999,$0000                 ; 00CDE  period multipliers (PitchTable * mul >> 16)
        dc.b    0,0                         ; 00CE2  volume / pitch envelope speed (ticks per step)
        dc.w    256                         ; 00CE4  instrument volume (x channel volume >> 8; /4 -> AUDxVOL)
Ins34:
        dc.l    Smp26-SampleBase            ; 00CE6  attack sample (offset from SampleBase)
        dc.l    0                           ; 00CEA  loop sample (offset from SampleBase)
        dc.l    0                           ; 00CEE  volume envelope (self-relative)
        dc.l    0                           ; 00CF2  pitch envelope (self-relative)
        dc.w    $083C,$0000                 ; 00CF6  attack / loop length (words) = 4216 / 0 bytes
        dc.w    $7000,$0000                 ; 00CFA  period multipliers (PitchTable * mul >> 16)
        dc.b    0,0                         ; 00CFE  volume / pitch envelope speed (ticks per step)
        dc.w    256                         ; 00D00  instrument volume (x channel volume >> 8; /4 -> AUDxVOL)
Ins35:
        dc.l    Smp26-SampleBase            ; 00D02  attack sample (offset from SampleBase)
        dc.l    0                           ; 00D06  loop sample (offset from SampleBase)
        dc.l    0                           ; 00D0A  volume envelope (self-relative)
        dc.l    0                           ; 00D0E  pitch envelope (self-relative)
        dc.w    $063F,$0000                 ; 00D12  attack / loop length (words) = 3198 / 0 bytes
        dc.w    $5999,$0000                 ; 00D16  period multipliers (PitchTable * mul >> 16)
        dc.b    0,0                         ; 00D1A  volume / pitch envelope speed (ticks per step)
        dc.w    256                         ; 00D1C  instrument volume (x channel volume >> 8; /4 -> AUDxVOL)
Ins36:
        dc.l    Smp27-SampleBase            ; 00D1E  attack sample (offset from SampleBase)
        dc.l    0                           ; 00D22  loop sample (offset from SampleBase)
        dc.l    0                           ; 00D26  volume envelope (self-relative)
        dc.l    0                           ; 00D2A  pitch envelope (self-relative)
        dc.w    $0C3C,$0000                 ; 00D2E  attack / loop length (words) = 6264 / 0 bytes
        dc.w    $5999,$0000                 ; 00D32  period multipliers (PitchTable * mul >> 16)
        dc.b    0,0                         ; 00D36  volume / pitch envelope speed (ticks per step)
        dc.w    256                         ; 00D38  instrument volume (x channel volume >> 8; /4 -> AUDxVOL)
Ins37:
        dc.l    Smp17_834-SampleBase        ; 00D3A  attack sample (offset from SampleBase)
        dc.l    0                           ; 00D3E  loop sample (offset from SampleBase)
        dc.l    0                           ; 00D42  volume envelope (self-relative)
        dc.l    0                           ; 00D46  pitch envelope (self-relative)
        dc.w    $0297,$0000                 ; 00D4A  attack / loop length (words) = 1326 / 0 bytes
        dc.w    $7000,$0000                 ; 00D4E  period multipliers (PitchTable * mul >> 16)
        dc.b    0,0                         ; 00D52  volume / pitch envelope speed (ticks per step)
        dc.w    256                         ; 00D54  instrument volume (x channel volume >> 8; /4 -> AUDxVOL)
Mus00_Ch0:
        VOLUME  140                         ; 00D56
        NOTE    G_7,6,6                     ; 00D58  n=$5B ins 6 dur 6
        NOTE    G_7,6,36                    ; 00D5C  n=$5B ins 6 dur 36
        NOTE    Gs7,6,12                    ; 00D60  n=$5C ins 6 dur 12
        NOTE    A_7,6,12                    ; 00D64  n=$5D ins 6 dur 12
        NOTE    Gs7,6,12                    ; 00D68  n=$5C ins 6 dur 12
        NOTE    G_7,6,12                    ; 00D6C  n=$5B ins 6 dur 12
        NOTE    Fs7,6,12                    ; 00D70  n=$5A ins 6 dur 12
        NOTE    G_7,6,18                    ; 00D74  n=$5B ins 6 dur 18
        NOTE    G_6,6,6                     ; 00D78  n=$4F ins 6 dur 6
        NOTE    G_6,6,96                    ; 00D7C  n=$4F ins 6 dur 96
        ENDTRACK                            ; 00D80
Mus00_Ch1:
        VOLUME  120                         ; 00D81
        NOTE    Ds7,6,6                     ; 00D83  n=$57 ins 6 dur 6
        NOTE    Ds7,6,36                    ; 00D87  n=$57 ins 6 dur 36
        NOTE    Ds7,6,12                    ; 00D8B  n=$57 ins 6 dur 12
        NOTE    Ds7,6,12                    ; 00D8F  n=$57 ins 6 dur 12
        NOTE    Ds7,6,12                    ; 00D93  n=$57 ins 6 dur 12
        NOTE    Ds7,6,12                    ; 00D97  n=$57 ins 6 dur 12
        NOTE    Ds7,6,12                    ; 00D9B  n=$57 ins 6 dur 12
        NOTE    B_5,6,18                    ; 00D9F  n=$47 ins 6 dur 18
        NOTE    B_5,6,6                     ; 00DA3  n=$47 ins 6 dur 6
        NOTE    B_5,6,96                    ; 00DA7  n=$47 ins 6 dur 96
        ENDTRACK                            ; 00DAB
Mus00_Ch2:
        VOLUME  100                         ; 00DAC
        NOTE    C_7,6,6                     ; 00DAE  n=$54 ins 6 dur 6
        NOTE    C_7,6,36                    ; 00DB2  n=$54 ins 6 dur 36
        NOTE    C_7,6,12                    ; 00DB6  n=$54 ins 6 dur 12
        NOTE    C_7,6,12                    ; 00DBA  n=$54 ins 6 dur 12
        NOTE    C_7,6,12                    ; 00DBE  n=$54 ins 6 dur 12
        NOTE    C_7,6,12                    ; 00DC2  n=$54 ins 6 dur 12
        NOTE    C_7,6,12                    ; 00DC6  n=$54 ins 6 dur 12
        NOTE    F_7,6,18                    ; 00DCA  n=$59 ins 6 dur 18
        NOTE    D_6,6,6                     ; 00DCE  n=$4A ins 6 dur 6
        NOTE    D_6,6,96                    ; 00DD2  n=$4A ins 6 dur 96
        ENDTRACK                            ; 00DD6
Mus00_Ch3:
        VOLUME  255                         ; 00DD7
        NOTE    C_7,5,6                     ; 00DD9  n=$54 ins 5 dur 6
        NOTE    C_7,5,36                    ; 00DDD  n=$54 ins 5 dur 36
        NOTE    C_7,5,12                    ; 00DE1  n=$54 ins 5 dur 12
        NOTE    D_7,5,12                    ; 00DE5  n=$56 ins 5 dur 12
        NOTE    Ds7,5,12                    ; 00DE9  n=$57 ins 5 dur 12
        NOTE    F_7,5,12                    ; 00DED  n=$59 ins 5 dur 12
        NOTE    Fs7,5,12                    ; 00DF1  n=$5A ins 5 dur 12
        NOTE    G_7,5,18                    ; 00DF5  n=$5B ins 5 dur 18
        NOTE    G_6,5,6                     ; 00DF9  n=$4F ins 5 dur 6
        NOTE    G_6,5,96                    ; 00DFD  n=$4F ins 5 dur 96
        ENDTRACK                            ; 00E01
Mus01_Ch0:
        VOLUME  52                          ; 00E02
Loop_0E04:
        CALL    18,0                        ; 00E04  pattern, transpose
        JUMP    Loop_0E04                   ; 00E07
        ENDTRACK                            ; 00E0A  unreachable: follows a JUMP
Mus01_Ch1:
        VOLUME  255                         ; 00E0B
Loop_0E0D:
        NOTE    F_6,5,72                    ; 00E0D  n=$4D ins 5 dur 72
        NOTE    E_6,5,24                    ; 00E11  n=$4C ins 5 dur 24
        NOTE    D_6,5,96                    ; 00E15  n=$4A ins 5 dur 96
        NOTE    G_6,5,72                    ; 00E19  n=$4F ins 5 dur 72
        NOTE    F_6,5,24                    ; 00E1D  n=$4D ins 5 dur 24
        NOTE    E_6,5,48                    ; 00E21  n=$4C ins 5 dur 48
        NOTE    C_6,5,24                    ; 00E25  n=$48 ins 5 dur 24
        NOTE    D_6,5,12                    ; 00E29  n=$4A ins 5 dur 12
        NOTE    E_6,5,12                    ; 00E2D  n=$4C ins 5 dur 12
        NOTE    F_6,5,72                    ; 00E31  n=$4D ins 5 dur 72
        NOTE    E_6,5,24                    ; 00E35  n=$4C ins 5 dur 24
        NOTE    D_6,5,96                    ; 00E39  n=$4A ins 5 dur 96
        NOTE    G_6,5,72                    ; 00E3D  n=$4F ins 5 dur 72
        NOTE    F_6,5,24                    ; 00E41  n=$4D ins 5 dur 24
        NOTE    E_6,5,48                    ; 00E45  n=$4C ins 5 dur 48
        NOTE    Gs6,5,48                    ; 00E49  n=$50 ins 5 dur 48
        NOTE    A_6,5,60                    ; 00E4D  n=$51 ins 5 dur 60
        NOTE    E_6,5,12                    ; 00E51  n=$4C ins 5 dur 12
        NOTE    A_6,5,12                    ; 00E55  n=$51 ins 5 dur 12
        NOTE    C_7,5,12                    ; 00E59  n=$54 ins 5 dur 12
        NOTE    Gs6,5,48                    ; 00E5D  n=$50 ins 5 dur 48
        NOTE    B_6,5,24                    ; 00E61  n=$53 ins 5 dur 24
        NOTE    E_7,5,24                    ; 00E65  n=$58 ins 5 dur 24
        NOTE    Cs6,5,60                    ; 00E69  n=$49 ins 5 dur 60
        NOTE    As5,5,12                    ; 00E6D  n=$46 ins 5 dur 12
        NOTE    Cs6,5,12                    ; 00E71  n=$49 ins 5 dur 12
        NOTE    E_6,5,12                    ; 00E75  n=$4C ins 5 dur 12
        NOTE    D_6,5,48                    ; 00E79  n=$4A ins 5 dur 48
        NOTE    F_6,5,24                    ; 00E7D  n=$4D ins 5 dur 24
        NOTE    A_6,5,24                    ; 00E81  n=$51 ins 5 dur 24
        NOTE    Fs6,5,48                    ; 00E85  n=$4E ins 5 dur 48
        NOTE    A_6,5,24                    ; 00E89  n=$51 ins 5 dur 24
        NOTE    C_7,5,24                    ; 00E8D  n=$54 ins 5 dur 24
        NOTE    B_6,5,48                    ; 00E91  n=$53 ins 5 dur 48
        NOTE    Cs7,5,24                    ; 00E95  n=$55 ins 5 dur 24
        NOTE    D_7,5,24                    ; 00E99  n=$56 ins 5 dur 24
        NOTE    E_6,5,72                    ; 00E9D  n=$4C ins 5 dur 72
        NOTE    D_7,5,24                    ; 00EA1  n=$56 ins 5 dur 24
        NOTE    Cs7,5,36                    ; 00EA5  n=$55 ins 5 dur 36
        NOTE    A_6,5,24                    ; 00EA9  n=$51 ins 5 dur 24
        NOTE    A_6,5,12                    ; 00EAD  n=$51 ins 5 dur 12
        NOTE    Gs6,5,12                    ; 00EB1  n=$50 ins 5 dur 12
        NOTE    G_6,5,12                    ; 00EB5  n=$4F ins 5 dur 12
        JUMP    Loop_0E0D                   ; 00EB9
        ENDTRACK                            ; 00EBC  unreachable: follows a JUMP
Mus01_Ch2:
        VOLUME  80                          ; 00EBD
Loop_0EBF:
        NOTE    F_6,6,72                    ; 00EBF  n=$4D ins 6 dur 72
        NOTE    E_6,6,24                    ; 00EC3  n=$4C ins 6 dur 24
        NOTE    D_6,6,96                    ; 00EC7  n=$4A ins 6 dur 96
        NOTE    G_6,6,72                    ; 00ECB  n=$4F ins 6 dur 72
        NOTE    F_6,6,24                    ; 00ECF  n=$4D ins 6 dur 24
        NOTE    E_6,6,48                    ; 00ED3  n=$4C ins 6 dur 48
        NOTE    C_6,6,24                    ; 00ED7  n=$48 ins 6 dur 24
        NOTE    D_6,6,12                    ; 00EDB  n=$4A ins 6 dur 12
        NOTE    E_6,6,12                    ; 00EDF  n=$4C ins 6 dur 12
        NOTE    F_6,6,72                    ; 00EE3  n=$4D ins 6 dur 72
        NOTE    E_6,6,24                    ; 00EE7  n=$4C ins 6 dur 24
        NOTE    D_6,6,96                    ; 00EEB  n=$4A ins 6 dur 96
        NOTE    G_6,6,72                    ; 00EEF  n=$4F ins 6 dur 72
        NOTE    F_6,6,24                    ; 00EF3  n=$4D ins 6 dur 24
        NOTE    E_6,6,48                    ; 00EF7  n=$4C ins 6 dur 48
        NOTE    Gs6,6,48                    ; 00EFB  n=$50 ins 6 dur 48
        NOTE    A_6,6,60                    ; 00EFF  n=$51 ins 6 dur 60
        NOTE    E_6,6,12                    ; 00F03  n=$4C ins 6 dur 12
        NOTE    A_6,6,12                    ; 00F07  n=$51 ins 6 dur 12
        NOTE    C_7,6,12                    ; 00F0B  n=$54 ins 6 dur 12
        NOTE    Gs6,6,48                    ; 00F0F  n=$50 ins 6 dur 48
        NOTE    B_6,6,24                    ; 00F13  n=$53 ins 6 dur 24
        NOTE    E_7,6,24                    ; 00F17  n=$58 ins 6 dur 24
        NOTE    Cs6,6,60                    ; 00F1B  n=$49 ins 6 dur 60
        NOTE    As5,6,12                    ; 00F1F  n=$46 ins 6 dur 12
        NOTE    Cs6,6,12                    ; 00F23  n=$49 ins 6 dur 12
        NOTE    E_6,6,12                    ; 00F27  n=$4C ins 6 dur 12
        NOTE    D_6,6,48                    ; 00F2B  n=$4A ins 6 dur 48
        NOTE    F_6,6,24                    ; 00F2F  n=$4D ins 6 dur 24
        NOTE    A_6,6,24                    ; 00F33  n=$51 ins 6 dur 24
        NOTE    Fs6,6,48                    ; 00F37  n=$4E ins 6 dur 48
        NOTE    A_6,6,24                    ; 00F3B  n=$51 ins 6 dur 24
        NOTE    C_7,6,24                    ; 00F3F  n=$54 ins 6 dur 24
        NOTE    B_6,6,48                    ; 00F43  n=$53 ins 6 dur 48
        NOTE    Cs7,6,24                    ; 00F47  n=$55 ins 6 dur 24
        NOTE    D_7,6,24                    ; 00F4B  n=$56 ins 6 dur 24
        NOTE    E_6,6,72                    ; 00F4F  n=$4C ins 6 dur 72
        NOTE    D_7,6,24                    ; 00F53  n=$56 ins 6 dur 24
        NOTE    Cs7,6,36                    ; 00F57  n=$55 ins 6 dur 36
        NOTE    A_6,6,24                    ; 00F5B  n=$51 ins 6 dur 24
        NOTE    A_6,6,12                    ; 00F5F  n=$51 ins 6 dur 12
        NOTE    Gs6,6,12                    ; 00F63  n=$50 ins 6 dur 12
        NOTE    G_6,6,12                    ; 00F67  n=$4F ins 6 dur 12
        JUMP    Loop_0EBF                   ; 00F6B
        ENDTRACK                            ; 00F6E  unreachable: follows a JUMP
Mus01_Ch3:
        VOLUME  44                          ; 00F6F
        REST    3                           ; 00F71
Loop_0F75:
        CALL    18,0                        ; 00F75  pattern, transpose
        JUMP    Loop_0F75                   ; 00F78
Pat18:
        NOTE    A_6,6,6                     ; 00F7B  n=$51 ins 6 dur 6
        NOTE    C_7,6,6                     ; 00F7F  n=$54 ins 6 dur 6
        NOTE    F_7,6,6                     ; 00F83  n=$59 ins 6 dur 6
        NOTE    C_7,6,6                     ; 00F87  n=$54 ins 6 dur 6
        NOTE    A_6,6,6                     ; 00F8B  n=$51 ins 6 dur 6
        NOTE    C_7,6,6                     ; 00F8F  n=$54 ins 6 dur 6
        NOTE    F_7,6,6                     ; 00F93  n=$59 ins 6 dur 6
        NOTE    C_7,6,6                     ; 00F97  n=$54 ins 6 dur 6
        NOTE    A_6,6,6                     ; 00F9B  n=$51 ins 6 dur 6
        NOTE    C_7,6,6                     ; 00F9F  n=$54 ins 6 dur 6
        NOTE    F_7,6,6                     ; 00FA3  n=$59 ins 6 dur 6
        NOTE    C_7,6,6                     ; 00FA7  n=$54 ins 6 dur 6
        NOTE    A_6,6,6                     ; 00FAB  n=$51 ins 6 dur 6
        NOTE    C_7,6,6                     ; 00FAF  n=$54 ins 6 dur 6
        NOTE    F_7,6,6                     ; 00FB3  n=$59 ins 6 dur 6
        NOTE    C_7,6,6                     ; 00FB7  n=$54 ins 6 dur 6
        NOTE    A_6,6,6                     ; 00FBB  n=$51 ins 6 dur 6
        NOTE    D_7,6,6                     ; 00FBF  n=$56 ins 6 dur 6
        NOTE    F_7,6,6                     ; 00FC3  n=$59 ins 6 dur 6
        NOTE    D_7,6,6                     ; 00FC7  n=$56 ins 6 dur 6
        NOTE    A_6,6,6                     ; 00FCB  n=$51 ins 6 dur 6
        NOTE    D_7,6,6                     ; 00FCF  n=$56 ins 6 dur 6
        NOTE    F_7,6,6                     ; 00FD3  n=$59 ins 6 dur 6
        NOTE    D_7,6,6                     ; 00FD7  n=$56 ins 6 dur 6
        NOTE    A_6,6,6                     ; 00FDB  n=$51 ins 6 dur 6
        NOTE    D_7,6,6                     ; 00FDF  n=$56 ins 6 dur 6
        NOTE    F_7,6,6                     ; 00FE3  n=$59 ins 6 dur 6
        NOTE    D_7,6,6                     ; 00FE7  n=$56 ins 6 dur 6
        NOTE    A_6,6,6                     ; 00FEB  n=$51 ins 6 dur 6
        NOTE    D_7,6,6                     ; 00FEF  n=$56 ins 6 dur 6
        NOTE    F_7,6,6                     ; 00FF3  n=$59 ins 6 dur 6
        NOTE    D_7,6,6                     ; 00FF7  n=$56 ins 6 dur 6
        NOTE    As6,6,6                     ; 00FFB  n=$52 ins 6 dur 6
        NOTE    D_7,6,6                     ; 00FFF  n=$56 ins 6 dur 6
        NOTE    G_7,6,6                     ; 01003  n=$5B ins 6 dur 6
        NOTE    D_7,6,6                     ; 01007  n=$56 ins 6 dur 6
        NOTE    As6,6,6                     ; 0100B  n=$52 ins 6 dur 6
        NOTE    D_7,6,6                     ; 0100F  n=$56 ins 6 dur 6
        NOTE    G_7,6,6                     ; 01013  n=$5B ins 6 dur 6
        NOTE    D_7,6,6                     ; 01017  n=$56 ins 6 dur 6
        NOTE    As6,6,6                     ; 0101B  n=$52 ins 6 dur 6
        NOTE    D_7,6,6                     ; 0101F  n=$56 ins 6 dur 6
        NOTE    G_7,6,6                     ; 01023  n=$5B ins 6 dur 6
        NOTE    D_7,6,6                     ; 01027  n=$56 ins 6 dur 6
        NOTE    As6,6,6                     ; 0102B  n=$52 ins 6 dur 6
        NOTE    D_7,6,6                     ; 0102F  n=$56 ins 6 dur 6
        NOTE    G_7,6,6                     ; 01033  n=$5B ins 6 dur 6
        NOTE    D_7,6,6                     ; 01037  n=$56 ins 6 dur 6
        NOTE    C_7,6,6                     ; 0103B  n=$54 ins 6 dur 6
        NOTE    E_7,6,6                     ; 0103F  n=$58 ins 6 dur 6
        NOTE    G_7,6,6                     ; 01043  n=$5B ins 6 dur 6
        NOTE    E_7,6,6                     ; 01047  n=$58 ins 6 dur 6
        NOTE    C_7,6,6                     ; 0104B  n=$54 ins 6 dur 6
        NOTE    E_7,6,6                     ; 0104F  n=$58 ins 6 dur 6
        NOTE    G_7,6,6                     ; 01053  n=$5B ins 6 dur 6
        NOTE    E_7,6,6                     ; 01057  n=$58 ins 6 dur 6
        NOTE    C_7,6,6                     ; 0105B  n=$54 ins 6 dur 6
        NOTE    E_7,6,6                     ; 0105F  n=$58 ins 6 dur 6
        NOTE    G_7,6,6                     ; 01063  n=$5B ins 6 dur 6
        NOTE    E_7,6,6                     ; 01067  n=$58 ins 6 dur 6
        NOTE    C_7,6,6                     ; 0106B  n=$54 ins 6 dur 6
        NOTE    E_7,6,6                     ; 0106F  n=$58 ins 6 dur 6
        NOTE    G_7,6,6                     ; 01073  n=$5B ins 6 dur 6
        NOTE    E_7,6,6                     ; 01077  n=$58 ins 6 dur 6
        NOTE    A_6,6,6                     ; 0107B  n=$51 ins 6 dur 6
        NOTE    C_7,6,6                     ; 0107F  n=$54 ins 6 dur 6
        NOTE    F_7,6,6                     ; 01083  n=$59 ins 6 dur 6
        NOTE    C_7,6,6                     ; 01087  n=$54 ins 6 dur 6
        NOTE    A_6,6,6                     ; 0108B  n=$51 ins 6 dur 6
        NOTE    C_7,6,6                     ; 0108F  n=$54 ins 6 dur 6
        NOTE    F_7,6,6                     ; 01093  n=$59 ins 6 dur 6
        NOTE    C_7,6,6                     ; 01097  n=$54 ins 6 dur 6
        NOTE    A_6,6,6                     ; 0109B  n=$51 ins 6 dur 6
        NOTE    C_7,6,6                     ; 0109F  n=$54 ins 6 dur 6
        NOTE    F_7,6,6                     ; 010A3  n=$59 ins 6 dur 6
        NOTE    C_7,6,6                     ; 010A7  n=$54 ins 6 dur 6
        NOTE    A_6,6,6                     ; 010AB  n=$51 ins 6 dur 6
        NOTE    C_7,6,6                     ; 010AF  n=$54 ins 6 dur 6
        NOTE    F_7,6,6                     ; 010B3  n=$59 ins 6 dur 6
        NOTE    C_7,6,6                     ; 010B7  n=$54 ins 6 dur 6
        NOTE    A_6,6,6                     ; 010BB  n=$51 ins 6 dur 6
        NOTE    D_7,6,6                     ; 010BF  n=$56 ins 6 dur 6
        NOTE    F_7,6,6                     ; 010C3  n=$59 ins 6 dur 6
        NOTE    D_7,6,6                     ; 010C7  n=$56 ins 6 dur 6
        NOTE    A_6,6,6                     ; 010CB  n=$51 ins 6 dur 6
        NOTE    D_7,6,6                     ; 010CF  n=$56 ins 6 dur 6
        NOTE    F_7,6,6                     ; 010D3  n=$59 ins 6 dur 6
        NOTE    D_7,6,6                     ; 010D7  n=$56 ins 6 dur 6
        NOTE    A_6,6,6                     ; 010DB  n=$51 ins 6 dur 6
        NOTE    D_7,6,6                     ; 010DF  n=$56 ins 6 dur 6
        NOTE    F_7,6,6                     ; 010E3  n=$59 ins 6 dur 6
        NOTE    D_7,6,6                     ; 010E7  n=$56 ins 6 dur 6
        NOTE    A_6,6,6                     ; 010EB  n=$51 ins 6 dur 6
        NOTE    D_7,6,6                     ; 010EF  n=$56 ins 6 dur 6
        NOTE    F_7,6,6                     ; 010F3  n=$59 ins 6 dur 6
        NOTE    D_7,6,6                     ; 010F7  n=$56 ins 6 dur 6
        NOTE    As6,6,6                     ; 010FB  n=$52 ins 6 dur 6
        NOTE    D_7,6,6                     ; 010FF  n=$56 ins 6 dur 6
        NOTE    G_7,6,6                     ; 01103  n=$5B ins 6 dur 6
        NOTE    D_7,6,6                     ; 01107  n=$56 ins 6 dur 6
        NOTE    As6,6,6                     ; 0110B  n=$52 ins 6 dur 6
        NOTE    D_7,6,6                     ; 0110F  n=$56 ins 6 dur 6
        NOTE    G_7,6,6                     ; 01113  n=$5B ins 6 dur 6
        NOTE    D_7,6,6                     ; 01117  n=$56 ins 6 dur 6
        NOTE    As6,6,6                     ; 0111B  n=$52 ins 6 dur 6
        NOTE    D_7,6,6                     ; 0111F  n=$56 ins 6 dur 6
        NOTE    G_7,6,6                     ; 01123  n=$5B ins 6 dur 6
        NOTE    D_7,6,6                     ; 01127  n=$56 ins 6 dur 6
        NOTE    As6,6,6                     ; 0112B  n=$52 ins 6 dur 6
        NOTE    D_7,6,6                     ; 0112F  n=$56 ins 6 dur 6
        NOTE    G_7,6,6                     ; 01133  n=$5B ins 6 dur 6
        NOTE    D_7,6,6                     ; 01137  n=$56 ins 6 dur 6
        NOTE    C_7,6,6                     ; 0113B  n=$54 ins 6 dur 6
        NOTE    E_7,6,6                     ; 0113F  n=$58 ins 6 dur 6
        NOTE    G_7,6,6                     ; 01143  n=$5B ins 6 dur 6
        NOTE    E_7,6,6                     ; 01147  n=$58 ins 6 dur 6
        NOTE    C_7,6,6                     ; 0114B  n=$54 ins 6 dur 6
        NOTE    E_7,6,6                     ; 0114F  n=$58 ins 6 dur 6
        NOTE    G_7,6,6                     ; 01153  n=$5B ins 6 dur 6
        NOTE    E_7,6,6                     ; 01157  n=$58 ins 6 dur 6
        NOTE    Gs7,6,6                     ; 0115B  n=$5C ins 6 dur 6
        NOTE    E_7,6,6                     ; 0115F  n=$58 ins 6 dur 6
        NOTE    B_6,6,6                     ; 01163  n=$53 ins 6 dur 6
        NOTE    E_7,6,6                     ; 01167  n=$58 ins 6 dur 6
        NOTE    Gs7,6,6                     ; 0116B  n=$5C ins 6 dur 6
        NOTE    E_7,6,6                     ; 0116F  n=$58 ins 6 dur 6
        NOTE    B_6,6,6                     ; 01173  n=$53 ins 6 dur 6
        NOTE    E_7,6,6                     ; 01177  n=$58 ins 6 dur 6
        NOTE    A_7,6,6                     ; 0117B  n=$5D ins 6 dur 6
        NOTE    E_7,6,6                     ; 0117F  n=$58 ins 6 dur 6
        NOTE    C_7,6,6                     ; 01183  n=$54 ins 6 dur 6
        NOTE    E_7,6,6                     ; 01187  n=$58 ins 6 dur 6
        NOTE    A_7,6,6                     ; 0118B  n=$5D ins 6 dur 6
        NOTE    E_7,6,6                     ; 0118F  n=$58 ins 6 dur 6
        NOTE    C_7,6,6                     ; 01193  n=$54 ins 6 dur 6
        NOTE    E_7,6,6                     ; 01197  n=$58 ins 6 dur 6
        NOTE    A_7,6,6                     ; 0119B  n=$5D ins 6 dur 6
        NOTE    E_7,6,6                     ; 0119F  n=$58 ins 6 dur 6
        NOTE    C_7,6,6                     ; 011A3  n=$54 ins 6 dur 6
        NOTE    E_7,6,6                     ; 011A7  n=$58 ins 6 dur 6
        NOTE    A_7,6,6                     ; 011AB  n=$5D ins 6 dur 6
        NOTE    E_7,6,6                     ; 011AF  n=$58 ins 6 dur 6
        NOTE    C_7,6,6                     ; 011B3  n=$54 ins 6 dur 6
        NOTE    E_7,6,6                     ; 011B7  n=$58 ins 6 dur 6
        NOTE    Gs7,6,6                     ; 011BB  n=$5C ins 6 dur 6
        NOTE    E_7,6,6                     ; 011BF  n=$58 ins 6 dur 6
        NOTE    B_6,6,6                     ; 011C3  n=$53 ins 6 dur 6
        NOTE    E_7,6,6                     ; 011C7  n=$58 ins 6 dur 6
        NOTE    Gs7,6,6                     ; 011CB  n=$5C ins 6 dur 6
        NOTE    E_7,6,6                     ; 011CF  n=$58 ins 6 dur 6
        NOTE    B_6,6,6                     ; 011D3  n=$53 ins 6 dur 6
        NOTE    E_7,6,6                     ; 011D7  n=$58 ins 6 dur 6
        NOTE    Gs7,6,6                     ; 011DB  n=$5C ins 6 dur 6
        NOTE    E_7,6,6                     ; 011DF  n=$58 ins 6 dur 6
        NOTE    B_6,6,6                     ; 011E3  n=$53 ins 6 dur 6
        NOTE    E_7,6,6                     ; 011E7  n=$58 ins 6 dur 6
        NOTE    Gs7,6,6                     ; 011EB  n=$5C ins 6 dur 6
        NOTE    E_7,6,6                     ; 011EF  n=$58 ins 6 dur 6
        NOTE    B_6,6,6                     ; 011F3  n=$53 ins 6 dur 6
        NOTE    E_7,6,6                     ; 011F7  n=$58 ins 6 dur 6
        NOTE    Cs7,6,6                     ; 011FB  n=$55 ins 6 dur 6
        NOTE    E_7,6,6                     ; 011FF  n=$58 ins 6 dur 6
        NOTE    A_7,6,6                     ; 01203  n=$5D ins 6 dur 6
        NOTE    E_7,6,6                     ; 01207  n=$58 ins 6 dur 6
        NOTE    Cs7,6,6                     ; 0120B  n=$55 ins 6 dur 6
        NOTE    E_7,6,6                     ; 0120F  n=$58 ins 6 dur 6
        NOTE    A_7,6,6                     ; 01213  n=$5D ins 6 dur 6
        NOTE    E_7,6,6                     ; 01217  n=$58 ins 6 dur 6
        NOTE    Cs7,6,6                     ; 0121B  n=$55 ins 6 dur 6
        NOTE    E_7,6,6                     ; 0121F  n=$58 ins 6 dur 6
        NOTE    As7,6,6                     ; 01223  n=$5E ins 6 dur 6
        NOTE    E_7,6,6                     ; 01227  n=$58 ins 6 dur 6
        NOTE    Cs7,6,6                     ; 0122B  n=$55 ins 6 dur 6
        NOTE    E_7,6,6                     ; 0122F  n=$58 ins 6 dur 6
        NOTE    As7,6,6                     ; 01233  n=$5E ins 6 dur 6
        NOTE    E_7,6,6                     ; 01237  n=$58 ins 6 dur 6
        NOTE    D_7,6,6                     ; 0123B  n=$56 ins 6 dur 6
        NOTE    F_7,6,6                     ; 0123F  n=$59 ins 6 dur 6
        NOTE    B_7,6,6                     ; 01243  n=$5F ins 6 dur 6
        NOTE    F_7,6,6                     ; 01247  n=$59 ins 6 dur 6
        NOTE    D_7,6,6                     ; 0124B  n=$56 ins 6 dur 6
        NOTE    F_7,6,6                     ; 0124F  n=$59 ins 6 dur 6
        NOTE    B_7,6,6                     ; 01253  n=$5F ins 6 dur 6
        NOTE    F_7,6,6                     ; 01257  n=$59 ins 6 dur 6
        NOTE    D_7,6,6                     ; 0125B  n=$56 ins 6 dur 6
        NOTE    F_7,6,6                     ; 0125F  n=$59 ins 6 dur 6
        NOTE    B_7,6,6                     ; 01263  n=$5F ins 6 dur 6
        NOTE    F_7,6,6                     ; 01267  n=$59 ins 6 dur 6
        NOTE    D_7,6,6                     ; 0126B  n=$56 ins 6 dur 6
        NOTE    F_7,6,6                     ; 0126F  n=$59 ins 6 dur 6
        NOTE    B_7,6,6                     ; 01273  n=$5F ins 6 dur 6
        NOTE    F_7,6,6                     ; 01277  n=$59 ins 6 dur 6
        NOTE    Ds7,6,6                     ; 0127B  n=$57 ins 6 dur 6
        NOTE    A_7,6,6                     ; 0127F  n=$5D ins 6 dur 6
        NOTE    C_7,6,6                     ; 01283  n=$54 ins 6 dur 6
        NOTE    A_7,6,6                     ; 01287  n=$5D ins 6 dur 6
        NOTE    Ds7,6,6                     ; 0128B  n=$57 ins 6 dur 6
        NOTE    A_7,6,6                     ; 0128F  n=$5D ins 6 dur 6
        NOTE    C_7,6,6                     ; 01293  n=$54 ins 6 dur 6
        NOTE    A_7,6,6                     ; 01297  n=$5D ins 6 dur 6
        NOTE    Ds7,6,6                     ; 0129B  n=$57 ins 6 dur 6
        NOTE    A_7,6,6                     ; 0129F  n=$5D ins 6 dur 6
        NOTE    C_7,6,6                     ; 012A3  n=$54 ins 6 dur 6
        NOTE    A_7,6,6                     ; 012A7  n=$5D ins 6 dur 6
        NOTE    Ds7,6,6                     ; 012AB  n=$57 ins 6 dur 6
        NOTE    A_7,6,6                     ; 012AF  n=$5D ins 6 dur 6
        NOTE    C_7,6,6                     ; 012B3  n=$54 ins 6 dur 6
        NOTE    A_7,6,6                     ; 012B7  n=$5D ins 6 dur 6
        NOTE    Gs7,6,6                     ; 012BB  n=$5C ins 6 dur 6
        NOTE    E_7,6,6                     ; 012BF  n=$58 ins 6 dur 6
        NOTE    B_6,6,6                     ; 012C3  n=$53 ins 6 dur 6
        NOTE    E_7,6,6                     ; 012C7  n=$58 ins 6 dur 6
        NOTE    Gs7,6,6                     ; 012CB  n=$5C ins 6 dur 6
        NOTE    E_7,6,6                     ; 012CF  n=$58 ins 6 dur 6
        NOTE    B_6,6,6                     ; 012D3  n=$53 ins 6 dur 6
        NOTE    E_7,6,6                     ; 012D7  n=$58 ins 6 dur 6
        NOTE    Gs7,6,6                     ; 012DB  n=$5C ins 6 dur 6
        NOTE    E_7,6,6                     ; 012DF  n=$58 ins 6 dur 6
        NOTE    B_6,6,6                     ; 012E3  n=$53 ins 6 dur 6
        NOTE    E_7,6,6                     ; 012E7  n=$58 ins 6 dur 6
        NOTE    Gs7,6,6                     ; 012EB  n=$5C ins 6 dur 6
        NOTE    E_7,6,6                     ; 012EF  n=$58 ins 6 dur 6
        NOTE    B_6,6,6                     ; 012F3  n=$53 ins 6 dur 6
        NOTE    E_7,6,6                     ; 012F7  n=$58 ins 6 dur 6
        NOTE    A_6,6,6                     ; 012FB  n=$51 ins 6 dur 6
        NOTE    Cs7,6,6                     ; 012FF  n=$55 ins 6 dur 6
        NOTE    E_7,6,6                     ; 01303  n=$58 ins 6 dur 6
        NOTE    Cs7,6,6                     ; 01307  n=$55 ins 6 dur 6
        NOTE    A_6,6,6                     ; 0130B  n=$51 ins 6 dur 6
        NOTE    Cs7,6,6                     ; 0130F  n=$55 ins 6 dur 6
        NOTE    E_7,6,6                     ; 01313  n=$58 ins 6 dur 6
        NOTE    Cs7,6,6                     ; 01317  n=$55 ins 6 dur 6
        NOTE    A_6,6,6                     ; 0131B  n=$51 ins 6 dur 6
        NOTE    Cs7,6,6                     ; 0131F  n=$55 ins 6 dur 6
        NOTE    E_7,6,6                     ; 01323  n=$58 ins 6 dur 6
        NOTE    Cs7,6,6                     ; 01327  n=$55 ins 6 dur 6
        NOTE    A_6,6,6                     ; 0132B  n=$51 ins 6 dur 6
        NOTE    Cs7,6,6                     ; 0132F  n=$55 ins 6 dur 6
        NOTE    E_7,6,6                     ; 01333  n=$58 ins 6 dur 6
        NOTE    Cs7,6,6                     ; 01337  n=$55 ins 6 dur 6
        NOTE    A_6,6,6                     ; 0133B  n=$51 ins 6 dur 6
        NOTE    Cs7,6,6                     ; 0133F  n=$55 ins 6 dur 6
        NOTE    E_7,6,6                     ; 01343  n=$58 ins 6 dur 6
        NOTE    Cs7,6,6                     ; 01347  n=$55 ins 6 dur 6
        NOTE    A_6,6,6                     ; 0134B  n=$51 ins 6 dur 6
        NOTE    Cs7,6,6                     ; 0134F  n=$55 ins 6 dur 6
        NOTE    E_7,6,6                     ; 01353  n=$58 ins 6 dur 6
        NOTE    Cs7,6,6                     ; 01357  n=$55 ins 6 dur 6
        NOTE    A_6,6,6                     ; 0135B  n=$51 ins 6 dur 6
        NOTE    Cs7,6,6                     ; 0135F  n=$55 ins 6 dur 6
        NOTE    E_7,6,6                     ; 01363  n=$58 ins 6 dur 6
        NOTE    Cs7,6,6                     ; 01367  n=$55 ins 6 dur 6
        NOTE    A_6,6,6                     ; 0136B  n=$51 ins 6 dur 6
        NOTE    Cs7,6,6                     ; 0136F  n=$55 ins 6 dur 6
        NOTE    E_7,6,6                     ; 01373  n=$58 ins 6 dur 6
        NOTE    Cs7,6,6                     ; 01377  n=$55 ins 6 dur 6
        RETURN                              ; 0137B
Mus02_Ch0:
        VOLUME  64                          ; 0137C
        CALL    0,0                         ; 0137E  pattern, transpose
        CALL    0,0                         ; 01381  pattern, transpose
        CALL    3,0                         ; 01384  pattern, transpose
        CALL    6,0                         ; 01387  pattern, transpose
        JUMP    Mus02_Ch0                   ; 0138A
        ENDTRACK                            ; 0138D  unreachable: follows a JUMP
Mus02_Ch1:
        VOLUME  48                          ; 0138E
        CALL    1,0                         ; 01390  pattern, transpose
        CALL    1,0                         ; 01393  pattern, transpose
        CALL    4,0                         ; 01396  pattern, transpose
        CALL    7,0                         ; 01399  pattern, transpose
        JUMP    Mus02_Ch1                   ; 0139C
        ENDTRACK                            ; 0139F  unreachable: follows a JUMP
Mus02_Ch2:
        VOLUME  128                         ; 013A0
        CALL    2,0                         ; 013A2  pattern, transpose
        CALL    2,0                         ; 013A5  pattern, transpose
        CALL    5,0                         ; 013A8  pattern, transpose
        CALL    8,0                         ; 013AB  pattern, transpose
        JUMP    Mus02_Ch2                   ; 013AE
        ENDTRACK                            ; 013B1  unreachable: follows a JUMP
Mus02_Ch3:
        VOLUME  255                         ; 013B2
        ENDTRACK                            ; 013B4
Pat00:
        REST    24                          ; 013B5
        NOTE    A_6,8,24                    ; 013B9  n=$51 ins 8 dur 24
        NOTE    Gs6,8,16                    ; 013BD  n=$50 ins 8 dur 16
        NOTE    G_6,8,24                    ; 013C1  n=$4F ins 8 dur 24
        NOTE    Fs6,8,24                    ; 013C5  n=$4E ins 8 dur 24
        NOTE    F_6,8,16                    ; 013C9  n=$4D ins 8 dur 16
        NOTE    E_6,8,16                    ; 013CD  n=$4C ins 8 dur 16
        NOTE    Ds6,8,8                     ; 013D1  n=$4B ins 8 dur 8
        NOTE    E_6,8,16                    ; 013D5  n=$4C ins 8 dur 16
        NOTE    Ds6,8,8                     ; 013D9  n=$4B ins 8 dur 8
        NOTE    E_6,8,48                    ; 013DD  n=$4C ins 8 dur 48
        REST    32                          ; 013E1
        RETURN                              ; 013E5
Pat03:
        NOTE    A_6,8,8                     ; 013E6  n=$51 ins 8 dur 8
        NOTE    A_6,8,8                     ; 013EA  n=$51 ins 8 dur 8
        NOTE    Gs6,8,8                     ; 013EE  n=$50 ins 8 dur 8
        NOTE    A_6,8,32                    ; 013F2  n=$51 ins 8 dur 32
        REST    8                           ; 013F6
        NOTE    A_6,8,8                     ; 013FA  n=$51 ins 8 dur 8
        NOTE    A_6,8,8                     ; 013FE  n=$51 ins 8 dur 8
        NOTE    Gs6,8,8                     ; 01402  n=$50 ins 8 dur 8
        NOTE    A_6,8,32                    ; 01406  n=$51 ins 8 dur 32
        NOTE    Gs6,8,8                     ; 0140A  n=$50 ins 8 dur 8
        NOTE    A_6,8,8                     ; 0140E  n=$51 ins 8 dur 8
        NOTE    A_6,8,8                     ; 01412  n=$51 ins 8 dur 8
        NOTE    Gs6,8,8                     ; 01416  n=$50 ins 8 dur 8
        NOTE    A_6,8,32                    ; 0141A  n=$51 ins 8 dur 32
        NOTE    Gs6,8,8                     ; 0141E  n=$50 ins 8 dur 8
        NOTE    A_6,8,8                     ; 01422  n=$51 ins 8 dur 8
        NOTE    A_6,8,8                     ; 01426  n=$51 ins 8 dur 8
        NOTE    Gs6,8,8                     ; 0142A  n=$50 ins 8 dur 8
        NOTE    A_6,8,32                    ; 0142E  n=$51 ins 8 dur 32
        REST    8                           ; 01432
        NOTE    E_6,8,8                     ; 01436  n=$4C ins 8 dur 8
        NOTE    E_6,8,8                     ; 0143A  n=$4C ins 8 dur 8
        NOTE    E_6,8,48                    ; 0143E  n=$4C ins 8 dur 48
        NOTE    E_6,8,8                     ; 01442  n=$4C ins 8 dur 8
        NOTE    E_6,8,8                     ; 01446  n=$4C ins 8 dur 8
        NOTE    E_6,8,32                    ; 0144A  n=$4C ins 8 dur 32
        NOTE    E_6,8,4                     ; 0144E  n=$4C ins 8 dur 4
        NOTE    Fs6,8,4                     ; 01452  n=$4E ins 8 dur 4
        NOTE    Gs6,8,4                     ; 01456  n=$50 ins 8 dur 4
        NOTE    A_6,8,4                     ; 0145A  n=$51 ins 8 dur 4
        RETURN                              ; 0145E
Pat06:
        NOTE    C_7,8,64                    ; 0145F  n=$54 ins 8 dur 64
        REST    16                          ; 01463
        NOTE    Ds7,8,8                     ; 01467  n=$57 ins 8 dur 8
        NOTE    E_7,8,16                    ; 0146B  n=$58 ins 8 dur 16
        NOTE    Ds7,8,8                     ; 0146F  n=$57 ins 8 dur 8
        NOTE    E_7,8,16                    ; 01473  n=$58 ins 8 dur 16
        NOTE    B_6,8,64                    ; 01477  n=$53 ins 8 dur 64
        REST    16                          ; 0147B
        NOTE    Ds7,8,8                     ; 0147F  n=$57 ins 8 dur 8
        NOTE    E_7,8,16                    ; 01483  n=$58 ins 8 dur 16
        NOTE    Ds7,8,8                     ; 01487  n=$57 ins 8 dur 8
        NOTE    E_7,8,16                    ; 0148B  n=$58 ins 8 dur 16
        NOTE    C_7,8,64                    ; 0148F  n=$54 ins 8 dur 64
        REST    16                          ; 01493
        NOTE    Ds7,8,8                     ; 01497  n=$57 ins 8 dur 8
        NOTE    E_7,8,16                    ; 0149B  n=$58 ins 8 dur 16
        NOTE    Ds7,8,8                     ; 0149F  n=$57 ins 8 dur 8
        NOTE    E_7,8,16                    ; 014A3  n=$58 ins 8 dur 16
        NOTE    B_6,8,64                    ; 014A7  n=$53 ins 8 dur 64
        REST    32                          ; 014AB
        NOTE    E_6,8,4                     ; 014AF  n=$4C ins 8 dur 4
        NOTE    Fs6,8,4                     ; 014B3  n=$4E ins 8 dur 4
        NOTE    Gs6,8,4                     ; 014B7  n=$50 ins 8 dur 4
        NOTE    A_6,8,4                     ; 014BB  n=$51 ins 8 dur 4
        NOTE    B_6,8,4                     ; 014BF  n=$53 ins 8 dur 4
        NOTE    C_7,8,4                     ; 014C3  n=$54 ins 8 dur 4
        NOTE    D_7,8,4                     ; 014C7  n=$56 ins 8 dur 4
        NOTE    E_7,8,4                     ; 014CB  n=$58 ins 8 dur 4
        RETURN                              ; 014CF
Pat01:
        NOTE    A_6,6,8                     ; 014D0  n=$51 ins 6 dur 8
        NOTE    C_7,6,8                     ; 014D4  n=$54 ins 6 dur 8
        NOTE    E_7,6,8                     ; 014D8  n=$58 ins 6 dur 8
        NOTE    A_6,6,8                     ; 014DC  n=$51 ins 6 dur 8
        NOTE    C_7,6,8                     ; 014E0  n=$54 ins 6 dur 8
        NOTE    E_7,6,8                     ; 014E4  n=$58 ins 6 dur 8
        NOTE    A_6,6,8                     ; 014E8  n=$51 ins 6 dur 8
        NOTE    C_7,6,8                     ; 014EC  n=$54 ins 6 dur 8
        NOTE    A_6,6,8                     ; 014F0  n=$51 ins 6 dur 8
        NOTE    C_7,6,8                     ; 014F4  n=$54 ins 6 dur 8
        NOTE    E_7,6,8                     ; 014F8  n=$58 ins 6 dur 8
        NOTE    A_6,6,8                     ; 014FC  n=$51 ins 6 dur 8
        NOTE    C_7,6,8                     ; 01500  n=$54 ins 6 dur 8
        NOTE    E_7,6,8                     ; 01504  n=$58 ins 6 dur 8
        NOTE    A_6,6,8                     ; 01508  n=$51 ins 6 dur 8
        NOTE    C_7,6,8                     ; 0150C  n=$54 ins 6 dur 8
        NOTE    Gs6,6,8                     ; 01510  n=$50 ins 6 dur 8
        NOTE    B_6,6,8                     ; 01514  n=$53 ins 6 dur 8
        NOTE    E_7,6,8                     ; 01518  n=$58 ins 6 dur 8
        NOTE    Gs6,6,8                     ; 0151C  n=$50 ins 6 dur 8
        NOTE    B_6,6,8                     ; 01520  n=$53 ins 6 dur 8
        NOTE    E_7,6,8                     ; 01524  n=$58 ins 6 dur 8
        NOTE    Gs6,6,8                     ; 01528  n=$50 ins 6 dur 8
        NOTE    B_6,6,8                     ; 0152C  n=$53 ins 6 dur 8
        NOTE    Gs6,6,8                     ; 01530  n=$50 ins 6 dur 8
        NOTE    B_6,6,8                     ; 01534  n=$53 ins 6 dur 8
        NOTE    E_7,6,8                     ; 01538  n=$58 ins 6 dur 8
        NOTE    Gs6,6,8                     ; 0153C  n=$50 ins 6 dur 8
        NOTE    B_6,6,8                     ; 01540  n=$53 ins 6 dur 8
        NOTE    E_7,6,8                     ; 01544  n=$58 ins 6 dur 8
        NOTE    Gs6,6,8                     ; 01548  n=$50 ins 6 dur 8
        NOTE    B_6,6,8                     ; 0154C  n=$53 ins 6 dur 8
        RETURN                              ; 01550
Pat04:
        NOTE    A_6,6,8                     ; 01551  n=$51 ins 6 dur 8
        NOTE    Cs7,6,8                     ; 01555  n=$55 ins 6 dur 8
        NOTE    E_7,6,8                     ; 01559  n=$58 ins 6 dur 8
        NOTE    A_6,6,8                     ; 0155D  n=$51 ins 6 dur 8
        NOTE    Cs7,6,8                     ; 01561  n=$55 ins 6 dur 8
        NOTE    E_7,6,8                     ; 01565  n=$58 ins 6 dur 8
        NOTE    A_6,6,8                     ; 01569  n=$51 ins 6 dur 8
        NOTE    Cs7,6,8                     ; 0156D  n=$55 ins 6 dur 8
        NOTE    A_6,6,8                     ; 01571  n=$51 ins 6 dur 8
        NOTE    Cs7,6,8                     ; 01575  n=$55 ins 6 dur 8
        NOTE    E_7,6,8                     ; 01579  n=$58 ins 6 dur 8
        NOTE    A_6,6,8                     ; 0157D  n=$51 ins 6 dur 8
        NOTE    Cs7,6,8                     ; 01581  n=$55 ins 6 dur 8
        NOTE    E_7,6,8                     ; 01585  n=$58 ins 6 dur 8
        NOTE    A_6,6,8                     ; 01589  n=$51 ins 6 dur 8
        NOTE    Cs7,6,8                     ; 0158D  n=$55 ins 6 dur 8
        NOTE    A_6,6,8                     ; 01591  n=$51 ins 6 dur 8
        NOTE    D_7,6,8                     ; 01595  n=$56 ins 6 dur 8
        NOTE    F_7,6,8                     ; 01599  n=$59 ins 6 dur 8
        NOTE    A_6,6,8                     ; 0159D  n=$51 ins 6 dur 8
        NOTE    D_7,6,8                     ; 015A1  n=$56 ins 6 dur 8
        NOTE    F_7,6,8                     ; 015A5  n=$59 ins 6 dur 8
        NOTE    A_6,6,8                     ; 015A9  n=$51 ins 6 dur 8
        NOTE    D_7,6,8                     ; 015AD  n=$56 ins 6 dur 8
        NOTE    A_6,6,8                     ; 015B1  n=$51 ins 6 dur 8
        NOTE    Ds7,6,8                     ; 015B5  n=$57 ins 6 dur 8
        NOTE    Fs7,6,8                     ; 015B9  n=$5A ins 6 dur 8
        NOTE    A_6,6,8                     ; 015BD  n=$51 ins 6 dur 8
        NOTE    Ds7,6,8                     ; 015C1  n=$57 ins 6 dur 8
        NOTE    Fs7,6,8                     ; 015C5  n=$5A ins 6 dur 8
        NOTE    A_6,6,8                     ; 015C9  n=$51 ins 6 dur 8
        NOTE    Ds7,6,8                     ; 015CD  n=$57 ins 6 dur 8
        NOTE    Gs6,6,8                     ; 015D1  n=$50 ins 6 dur 8
        NOTE    B_6,6,8                     ; 015D5  n=$53 ins 6 dur 8
        NOTE    E_7,6,8                     ; 015D9  n=$58 ins 6 dur 8
        NOTE    Gs6,6,8                     ; 015DD  n=$50 ins 6 dur 8
        NOTE    B_6,6,8                     ; 015E1  n=$53 ins 6 dur 8
        NOTE    E_7,6,8                     ; 015E5  n=$58 ins 6 dur 8
        NOTE    Gs6,6,8                     ; 015E9  n=$50 ins 6 dur 8
        NOTE    B_6,6,8                     ; 015ED  n=$53 ins 6 dur 8
        NOTE    Gs7,6,8                     ; 015F1  n=$5C ins 6 dur 8
        NOTE    Gs7,6,8                     ; 015F5  n=$5C ins 6 dur 8
        NOTE    Gs7,8,48                    ; 015F9  n=$5C ins 8 dur 48
        RETURN                              ; 015FD
Pat07:
        NOTE    A_6,6,8                     ; 015FE  n=$51 ins 6 dur 8
        NOTE    C_7,6,8                     ; 01602  n=$54 ins 6 dur 8
        NOTE    E_7,6,8                     ; 01606  n=$58 ins 6 dur 8
        NOTE    A_6,6,8                     ; 0160A  n=$51 ins 6 dur 8
        NOTE    C_7,6,8                     ; 0160E  n=$54 ins 6 dur 8
        NOTE    E_7,6,8                     ; 01612  n=$58 ins 6 dur 8
        NOTE    A_6,6,8                     ; 01616  n=$51 ins 6 dur 8
        NOTE    C_7,6,8                     ; 0161A  n=$54 ins 6 dur 8
        NOTE    A_6,6,8                     ; 0161E  n=$51 ins 6 dur 8
        NOTE    C_7,6,8                     ; 01622  n=$54 ins 6 dur 8
        NOTE    E_7,6,8                     ; 01626  n=$58 ins 6 dur 8
        NOTE    A_6,6,8                     ; 0162A  n=$51 ins 6 dur 8
        NOTE    C_7,6,8                     ; 0162E  n=$54 ins 6 dur 8
        NOTE    E_7,6,8                     ; 01632  n=$58 ins 6 dur 8
        NOTE    A_6,6,8                     ; 01636  n=$51 ins 6 dur 8
        NOTE    C_7,6,8                     ; 0163A  n=$54 ins 6 dur 8
        NOTE    Gs6,6,8                     ; 0163E  n=$50 ins 6 dur 8
        NOTE    B_6,6,8                     ; 01642  n=$53 ins 6 dur 8
        NOTE    E_7,6,8                     ; 01646  n=$58 ins 6 dur 8
        NOTE    Gs6,6,8                     ; 0164A  n=$50 ins 6 dur 8
        NOTE    B_6,6,8                     ; 0164E  n=$53 ins 6 dur 8
        NOTE    E_7,6,8                     ; 01652  n=$58 ins 6 dur 8
        NOTE    Gs6,6,8                     ; 01656  n=$50 ins 6 dur 8
        NOTE    B_6,6,8                     ; 0165A  n=$53 ins 6 dur 8
        NOTE    Gs6,6,8                     ; 0165E  n=$50 ins 6 dur 8
        NOTE    B_6,6,8                     ; 01662  n=$53 ins 6 dur 8
        NOTE    E_7,6,8                     ; 01666  n=$58 ins 6 dur 8
        NOTE    Gs6,6,8                     ; 0166A  n=$50 ins 6 dur 8
        NOTE    B_6,6,8                     ; 0166E  n=$53 ins 6 dur 8
        NOTE    E_7,6,8                     ; 01672  n=$58 ins 6 dur 8
        NOTE    Gs6,6,8                     ; 01676  n=$50 ins 6 dur 8
        NOTE    B_6,6,8                     ; 0167A  n=$53 ins 6 dur 8
        NOTE    A_6,6,8                     ; 0167E  n=$51 ins 6 dur 8
        NOTE    C_7,6,8                     ; 01682  n=$54 ins 6 dur 8
        NOTE    E_7,6,8                     ; 01686  n=$58 ins 6 dur 8
        NOTE    A_6,6,8                     ; 0168A  n=$51 ins 6 dur 8
        NOTE    C_7,6,8                     ; 0168E  n=$54 ins 6 dur 8
        NOTE    E_7,6,8                     ; 01692  n=$58 ins 6 dur 8
        NOTE    A_6,6,8                     ; 01696  n=$51 ins 6 dur 8
        NOTE    C_7,6,8                     ; 0169A  n=$54 ins 6 dur 8
        NOTE    A_6,6,8                     ; 0169E  n=$51 ins 6 dur 8
        NOTE    C_7,6,8                     ; 016A2  n=$54 ins 6 dur 8
        NOTE    E_7,6,8                     ; 016A6  n=$58 ins 6 dur 8
        NOTE    A_6,6,8                     ; 016AA  n=$51 ins 6 dur 8
        NOTE    C_7,6,8                     ; 016AE  n=$54 ins 6 dur 8
        NOTE    E_7,6,8                     ; 016B2  n=$58 ins 6 dur 8
        NOTE    A_6,6,8                     ; 016B6  n=$51 ins 6 dur 8
        NOTE    C_7,6,8                     ; 016BA  n=$54 ins 6 dur 8
        NOTE    Gs6,6,8                     ; 016BE  n=$50 ins 6 dur 8
        NOTE    B_6,6,8                     ; 016C2  n=$53 ins 6 dur 8
        NOTE    E_7,6,8                     ; 016C6  n=$58 ins 6 dur 8
        NOTE    Gs6,6,8                     ; 016CA  n=$50 ins 6 dur 8
        NOTE    B_6,6,8                     ; 016CE  n=$53 ins 6 dur 8
        NOTE    E_7,6,8                     ; 016D2  n=$58 ins 6 dur 8
        NOTE    Gs6,6,8                     ; 016D6  n=$50 ins 6 dur 8
        NOTE    B_6,6,8                     ; 016DA  n=$53 ins 6 dur 8
        NOTE    Gs6,6,8                     ; 016DE  n=$50 ins 6 dur 8
        NOTE    B_6,6,8                     ; 016E2  n=$53 ins 6 dur 8
        NOTE    E_7,6,8                     ; 016E6  n=$58 ins 6 dur 8
        NOTE    Gs6,6,8                     ; 016EA  n=$50 ins 6 dur 8
        NOTE    B_6,6,8                     ; 016EE  n=$53 ins 6 dur 8
        NOTE    E_7,6,8                     ; 016F2  n=$58 ins 6 dur 8
        NOTE    Gs6,6,8                     ; 016F6  n=$50 ins 6 dur 8
        NOTE    B_6,6,8                     ; 016FA  n=$53 ins 6 dur 8
        RETURN                              ; 016FE
Pat02:
        NOTE    A_6,5,24                    ; 016FF  n=$51 ins 5 dur 24
        NOTE    A_6,5,24                    ; 01703  n=$51 ins 5 dur 24
        NOTE    E_7,5,16                    ; 01707  n=$58 ins 5 dur 16
        NOTE    A_6,5,24                    ; 0170B  n=$51 ins 5 dur 24
        NOTE    A_7,5,24                    ; 0170F  n=$5D ins 5 dur 24
        NOTE    E_7,5,16                    ; 01713  n=$58 ins 5 dur 16
        NOTE    Gs6,5,24                    ; 01717  n=$50 ins 5 dur 24
        NOTE    Gs6,5,24                    ; 0171B  n=$50 ins 5 dur 24
        NOTE    E_6,5,16                    ; 0171F  n=$4C ins 5 dur 16
        NOTE    Gs6,5,16                    ; 01723  n=$50 ins 5 dur 16
        NOTE    E_6,5,16                    ; 01727  n=$4C ins 5 dur 16
        NOTE    Fs6,5,16                    ; 0172B  n=$4E ins 5 dur 16
        NOTE    Gs6,5,16                    ; 0172F  n=$50 ins 5 dur 16
        RETURN                              ; 01733
Pat05:
        NOTE    A_6,5,24                    ; 01734  n=$51 ins 5 dur 24
        NOTE    A_6,5,24                    ; 01738  n=$51 ins 5 dur 24
        NOTE    E_7,5,16                    ; 0173C  n=$58 ins 5 dur 16
        NOTE    A_6,5,24                    ; 01740  n=$51 ins 5 dur 24
        NOTE    A_6,5,24                    ; 01744  n=$51 ins 5 dur 24
        NOTE    E_7,5,16                    ; 01748  n=$58 ins 5 dur 16
        NOTE    A_6,5,24                    ; 0174C  n=$51 ins 5 dur 24
        NOTE    A_6,5,24                    ; 01750  n=$51 ins 5 dur 24
        NOTE    F_7,5,16                    ; 01754  n=$59 ins 5 dur 16
        NOTE    A_6,5,24                    ; 01758  n=$51 ins 5 dur 24
        NOTE    A_6,5,24                    ; 0175C  n=$51 ins 5 dur 24
        NOTE    Fs7,5,16                    ; 01760  n=$5A ins 5 dur 16
        NOTE    E_6,5,8                     ; 01764  n=$4C ins 5 dur 8
        NOTE    E_6,5,8                     ; 01768  n=$4C ins 5 dur 8
        NOTE    E_6,5,48                    ; 0176C  n=$4C ins 5 dur 48
        NOTE    E_6,5,8                     ; 01770  n=$4C ins 5 dur 8
        NOTE    E_7,5,8                     ; 01774  n=$58 ins 5 dur 8
        NOTE    E_6,5,48                    ; 01778  n=$4C ins 5 dur 48
        RETURN                              ; 0177C
Pat08:
        NOTE    A_6,5,16                    ; 0177D  n=$51 ins 5 dur 16
        NOTE    E_7,5,8                     ; 01781  n=$58 ins 5 dur 8
        NOTE    E_7,5,16                    ; 01785  n=$58 ins 5 dur 16
        NOTE    E_7,5,8                     ; 01789  n=$58 ins 5 dur 8
        NOTE    E_7,5,16                    ; 0178D  n=$58 ins 5 dur 16
        NOTE    A_6,5,16                    ; 01791  n=$51 ins 5 dur 16
        NOTE    E_7,5,8                     ; 01795  n=$58 ins 5 dur 8
        NOTE    E_7,5,16                    ; 01799  n=$58 ins 5 dur 16
        NOTE    E_7,5,8                     ; 0179D  n=$58 ins 5 dur 8
        NOTE    E_7,5,16                    ; 017A1  n=$58 ins 5 dur 16
        NOTE    Gs6,5,16                    ; 017A5  n=$50 ins 5 dur 16
        NOTE    E_7,5,8                     ; 017A9  n=$58 ins 5 dur 8
        NOTE    E_7,5,16                    ; 017AD  n=$58 ins 5 dur 16
        NOTE    E_7,5,8                     ; 017B1  n=$58 ins 5 dur 8
        NOTE    E_7,5,16                    ; 017B5  n=$58 ins 5 dur 16
        NOTE    Gs6,5,16                    ; 017B9  n=$50 ins 5 dur 16
        NOTE    E_7,5,8                     ; 017BD  n=$58 ins 5 dur 8
        NOTE    E_7,5,16                    ; 017C1  n=$58 ins 5 dur 16
        NOTE    E_7,5,8                     ; 017C5  n=$58 ins 5 dur 8
        NOTE    E_7,5,16                    ; 017C9  n=$58 ins 5 dur 16
        NOTE    F_6,5,16                    ; 017CD  n=$4D ins 5 dur 16
        NOTE    C_7,5,8                     ; 017D1  n=$54 ins 5 dur 8
        NOTE    C_7,5,16                    ; 017D5  n=$54 ins 5 dur 16
        NOTE    C_7,5,8                     ; 017D9  n=$54 ins 5 dur 8
        NOTE    C_7,5,16                    ; 017DD  n=$54 ins 5 dur 16
        NOTE    F_6,5,16                    ; 017E1  n=$4D ins 5 dur 16
        NOTE    C_7,5,8                     ; 017E5  n=$54 ins 5 dur 8
        NOTE    C_7,5,16                    ; 017E9  n=$54 ins 5 dur 16
        NOTE    C_7,5,8                     ; 017ED  n=$54 ins 5 dur 8
        NOTE    C_7,5,16                    ; 017F1  n=$54 ins 5 dur 16
        NOTE    Gs6,5,16                    ; 017F5  n=$50 ins 5 dur 16
        NOTE    E_7,5,8                     ; 017F9  n=$58 ins 5 dur 8
        NOTE    E_7,5,16                    ; 017FD  n=$58 ins 5 dur 16
        NOTE    E_7,5,8                     ; 01801  n=$58 ins 5 dur 8
        NOTE    E_7,5,16                    ; 01805  n=$58 ins 5 dur 16
        NOTE    Gs6,5,16                    ; 01809  n=$50 ins 5 dur 16
        NOTE    E_7,5,8                     ; 0180D  n=$58 ins 5 dur 8
        NOTE    E_7,5,8                     ; 01811  n=$58 ins 5 dur 8
        NOTE    E_7,5,4                     ; 01815  n=$58 ins 5 dur 4
        NOTE    D_7,5,4                     ; 01819  n=$56 ins 5 dur 4
        NOTE    C_7,5,4                     ; 0181D  n=$54 ins 5 dur 4
        NOTE    B_6,5,4                     ; 01821  n=$53 ins 5 dur 4
        NOTE    A_6,5,4                     ; 01825  n=$51 ins 5 dur 4
        NOTE    Gs6,5,4                     ; 01829  n=$50 ins 5 dur 4
        NOTE    Fs6,5,4                     ; 0182D  n=$4E ins 5 dur 4
        NOTE    E_6,5,4                     ; 01831  n=$4C ins 5 dur 4
        RETURN                              ; 01835
Mus03_Ch0:
        VOLUME  160                         ; 01836
        CALL    9,-5                        ; 01838  pattern, transpose
Loop_183B:
        CALL    13,-5                       ; 0183B  pattern, transpose
        JUMP    Loop_183B                   ; 0183E
Mus03_Ch1:
        VOLUME  160                         ; 01841
        CALL    10,-5                       ; 01843  pattern, transpose
Loop_1846:
        CALL    14,-5                       ; 01846  pattern, transpose
        JUMP    Loop_1846                   ; 01849
Mus03_Ch2:
        VOLUME  128                         ; 0184C
        CALL    11,-5                       ; 0184E  pattern, transpose
Loop_1851:
        CALL    15,-5                       ; 01851  pattern, transpose
        JUMP    Loop_1851                   ; 01854
Mus03_Ch3:
        VOLUME  200                         ; 01857
Loop_1859:
        CALL    16,-5                       ; 01859  pattern, transpose
        JUMP    Loop_1859                   ; 0185C
Pat09:
        NOTE    C_7,2,9                     ; 0185F  n=$54 ins 2 dur 9
        NOTE    D_7,2,9                     ; 01863  n=$56 ins 2 dur 9
        NOTE    Ds7,2,9                     ; 01867  n=$57 ins 2 dur 9
        NOTE    C_7,2,9                     ; 0186B  n=$54 ins 2 dur 9
        NOTE    As6,2,9                     ; 0186F  n=$52 ins 2 dur 9
        NOTE    D_7,2,9                     ; 01873  n=$56 ins 2 dur 9
        NOTE    Ds7,2,9                     ; 01877  n=$57 ins 2 dur 9
        NOTE    As6,2,9                     ; 0187B  n=$52 ins 2 dur 9
        NOTE    Gs6,2,9                     ; 0187F  n=$50 ins 2 dur 9
        NOTE    As6,2,9                     ; 01883  n=$52 ins 2 dur 9
        NOTE    C_7,2,9                     ; 01887  n=$54 ins 2 dur 9
        NOTE    F_6,2,9                     ; 0188B  n=$4D ins 2 dur 9
        NOTE    As6,2,9                     ; 0188F  n=$52 ins 2 dur 9
        NOTE    Gs6,2,9                     ; 01893  n=$50 ins 2 dur 9
        NOTE    G_6,2,9                     ; 01897  n=$4F ins 2 dur 9
        NOTE    F_6,2,9                     ; 0189B  n=$4D ins 2 dur 9
        NOTE    D_6,2,72                    ; 0189F  n=$4A ins 2 dur 72
        NOTE    As5,2,18                    ; 018A3  n=$46 ins 2 dur 18
        NOTE    C_6,2,18                    ; 018A7  n=$48 ins 2 dur 18
        NOTE    D_6,2,18                    ; 018AB  n=$4A ins 2 dur 18
        RETURN                              ; 018AF
Pat13:
        NOTE    G_7,2,12                    ; 018B0  n=$5B ins 2 dur 12
        NOTE    As6,2,12                    ; 018B4  n=$52 ins 2 dur 12
        NOTE    As6,2,12                    ; 018B8  n=$52 ins 2 dur 12
        NOTE    G_7,2,12                    ; 018BC  n=$5B ins 2 dur 12
        NOTE    As6,2,12                    ; 018C0  n=$52 ins 2 dur 12
        NOTE    As6,2,12                    ; 018C4  n=$52 ins 2 dur 12
        NOTE    Gs6,2,6                     ; 018C8  n=$50 ins 2 dur 6
        NOTE    As6,2,6                     ; 018CC  n=$52 ins 2 dur 6
        NOTE    C_7,2,6                     ; 018D0  n=$54 ins 2 dur 6
        NOTE    D_7,2,6                     ; 018D4  n=$56 ins 2 dur 6
        NOTE    Ds7,2,6                     ; 018D8  n=$57 ins 2 dur 6
        NOTE    F_7,2,6                     ; 018DC  n=$59 ins 2 dur 6
        NOTE    G_7,2,6                     ; 018E0  n=$5B ins 2 dur 6
        NOTE    As6,2,6                     ; 018E4  n=$52 ins 2 dur 6
        NOTE    C_7,2,6                     ; 018E8  n=$54 ins 2 dur 6
        NOTE    D_7,2,6                     ; 018EC  n=$56 ins 2 dur 6
        NOTE    Ds7,2,6                     ; 018F0  n=$57 ins 2 dur 6
        NOTE    F_7,2,6                     ; 018F4  n=$59 ins 2 dur 6
        NOTE    G_7,2,12                    ; 018F8  n=$5B ins 2 dur 12
        NOTE    As6,2,12                    ; 018FC  n=$52 ins 2 dur 12
        NOTE    As6,2,12                    ; 01900  n=$52 ins 2 dur 12
        NOTE    G_7,2,12                    ; 01904  n=$5B ins 2 dur 12
        NOTE    As6,2,12                    ; 01908  n=$52 ins 2 dur 12
        NOTE    As6,2,12                    ; 0190C  n=$52 ins 2 dur 12
        NOTE    C_7,2,6                     ; 01910  n=$54 ins 2 dur 6
        NOTE    C_7,1,6                     ; 01914  n=$54 ins 1 dur 6
        NOTE    As7,2,6                     ; 01918  n=$5E ins 2 dur 6
        NOTE    A_7,2,6                     ; 0191C  n=$5D ins 2 dur 6
        NOTE    Gs7,2,6                     ; 01920  n=$5C ins 2 dur 6
        NOTE    G_7,2,6                     ; 01924  n=$5B ins 2 dur 6
        NOTE    F_7,2,24                    ; 01928  n=$59 ins 2 dur 24
        NOTE    Fs7,2,12                    ; 0192C  n=$5A ins 2 dur 12
        NOTE    G_7,2,12                    ; 01930  n=$5B ins 2 dur 12
        NOTE    B_6,2,12                    ; 01934  n=$53 ins 2 dur 12
        NOTE    B_6,2,12                    ; 01938  n=$53 ins 2 dur 12
        NOTE    G_7,2,12                    ; 0193C  n=$5B ins 2 dur 12
        NOTE    B_6,2,12                    ; 01940  n=$53 ins 2 dur 12
        NOTE    B_6,2,12                    ; 01944  n=$53 ins 2 dur 12
        NOTE    F_7,2,6                     ; 01948  n=$59 ins 2 dur 6
        NOTE    Ds7,2,6                     ; 0194C  n=$57 ins 2 dur 6
        NOTE    F_7,2,6                     ; 01950  n=$59 ins 2 dur 6
        NOTE    Gs7,2,6                     ; 01954  n=$5C ins 2 dur 6
        NOTE    G_7,2,6                     ; 01958  n=$5B ins 2 dur 6
        NOTE    F_7,2,6                     ; 0195C  n=$59 ins 2 dur 6
        NOTE    D_7,2,6                     ; 01960  n=$56 ins 2 dur 6
        NOTE    As6,2,6                     ; 01964  n=$52 ins 2 dur 6
        NOTE    C_7,2,6                     ; 01968  n=$54 ins 2 dur 6
        NOTE    D_7,2,6                     ; 0196C  n=$56 ins 2 dur 6
        NOTE    Ds7,2,6                     ; 01970  n=$57 ins 2 dur 6
        NOTE    F_7,2,6                     ; 01974  n=$59 ins 2 dur 6
        NOTE    Gs7,2,12                    ; 01978  n=$5C ins 2 dur 12
        NOTE    C_7,2,12                    ; 0197C  n=$54 ins 2 dur 12
        NOTE    C_7,2,12                    ; 01980  n=$54 ins 2 dur 12
        NOTE    Gs7,2,12                    ; 01984  n=$5C ins 2 dur 12
        NOTE    C_7,2,12                    ; 01988  n=$54 ins 2 dur 12
        NOTE    C_7,2,12                    ; 0198C  n=$54 ins 2 dur 12
        NOTE    Gs7,2,12                    ; 01990  n=$5C ins 2 dur 12
        NOTE    C_7,2,12                    ; 01994  n=$54 ins 2 dur 12
        NOTE    C_7,2,12                    ; 01998  n=$54 ins 2 dur 12
        NOTE    C_7,1,12                    ; 0199C  n=$54 ins 1 dur 12
        NOTE    C_7,2,12                    ; 019A0  n=$54 ins 2 dur 12
        NOTE    C_7,2,12                    ; 019A4  n=$54 ins 2 dur 12
        NOTE    D_7,1,6                     ; 019A8  n=$56 ins 1 dur 6
        NOTE    As7,2,6                     ; 019AC  n=$5E ins 2 dur 6
        NOTE    F_7,2,6                     ; 019B0  n=$59 ins 2 dur 6
        NOTE    D_7,2,6                     ; 019B4  n=$56 ins 2 dur 6
        NOTE    As7,2,6                     ; 019B8  n=$5E ins 2 dur 6
        NOTE    F_7,2,6                     ; 019BC  n=$59 ins 2 dur 6
        NOTE    D_7,2,6                     ; 019C0  n=$56 ins 2 dur 6
        NOTE    As6,2,6                     ; 019C4  n=$52 ins 2 dur 6
        NOTE    F_7,2,6                     ; 019C8  n=$59 ins 2 dur 6
        NOTE    D_7,2,6                     ; 019CC  n=$56 ins 2 dur 6
        NOTE    As6,2,6                     ; 019D0  n=$52 ins 2 dur 6
        NOTE    F_6,2,6                     ; 019D4  n=$4D ins 2 dur 6
        NOTE    As6,2,6                     ; 019D8  n=$52 ins 2 dur 6
        NOTE    C_7,2,6                     ; 019DC  n=$54 ins 2 dur 6
        NOTE    D_7,2,6                     ; 019E0  n=$56 ins 2 dur 6
        NOTE    C_7,2,6                     ; 019E4  n=$54 ins 2 dur 6
        NOTE    D_7,2,6                     ; 019E8  n=$56 ins 2 dur 6
        NOTE    Ds7,2,6                     ; 019EC  n=$57 ins 2 dur 6
        NOTE    D_7,2,6                     ; 019F0  n=$56 ins 2 dur 6
        NOTE    Ds7,2,6                     ; 019F4  n=$57 ins 2 dur 6
        NOTE    F_7,2,6                     ; 019F8  n=$59 ins 2 dur 6
        NOTE    Ds7,2,6                     ; 019FC  n=$57 ins 2 dur 6
        NOTE    F_7,2,6                     ; 01A00  n=$59 ins 2 dur 6
        NOTE    G_7,2,6                     ; 01A04  n=$5B ins 2 dur 6
        NOTE    F_7,2,6                     ; 01A08  n=$59 ins 2 dur 6
        NOTE    G_7,2,6                     ; 01A0C  n=$5B ins 2 dur 6
        NOTE    Gs7,2,6                     ; 01A10  n=$5C ins 2 dur 6
        NOTE    Gs7,2,18                    ; 01A14  n=$5C ins 2 dur 18
        RETURN                              ; 01A18
Pat10:
        NOTE    Gs6,2,9                     ; 01A19  n=$50 ins 2 dur 9
        NOTE    As6,2,9                     ; 01A1D  n=$52 ins 2 dur 9
        NOTE    C_7,2,9                     ; 01A21  n=$54 ins 2 dur 9
        NOTE    Gs6,2,9                     ; 01A25  n=$50 ins 2 dur 9
        NOTE    G_6,2,9                     ; 01A29  n=$4F ins 2 dur 9
        NOTE    As6,2,9                     ; 01A2D  n=$52 ins 2 dur 9
        NOTE    As6,2,9                     ; 01A31  n=$52 ins 2 dur 9
        NOTE    G_6,2,9                     ; 01A35  n=$4F ins 2 dur 9
        NOTE    F_6,2,9                     ; 01A39  n=$4D ins 2 dur 9
        NOTE    G_6,2,9                     ; 01A3D  n=$4F ins 2 dur 9
        NOTE    As6,2,9                     ; 01A41  n=$52 ins 2 dur 9
        NOTE    C_6,2,9                     ; 01A45  n=$48 ins 2 dur 9
        NOTE    D_6,2,9                     ; 01A49  n=$4A ins 2 dur 9
        NOTE    C_6,2,9                     ; 01A4D  n=$48 ins 2 dur 9
        NOTE    As6,3,9                     ; 01A51  n=$52 ins 3 dur 9
        NOTE    Gs6,2,9                     ; 01A55  n=$50 ins 2 dur 9
        NOTE    As6,3,72                    ; 01A59  n=$52 ins 3 dur 72
        NOTE    F_6,3,18                    ; 01A5D  n=$4D ins 3 dur 18
        NOTE    Gs6,3,18                    ; 01A61  n=$50 ins 3 dur 18
        NOTE    As6,3,18                    ; 01A65  n=$52 ins 3 dur 18
        RETURN                              ; 01A69
Pat14:
        NOTE    Ds7,2,12                    ; 01A6A  n=$57 ins 2 dur 12
        NOTE    G_6,2,12                    ; 01A6E  n=$4F ins 2 dur 12
        NOTE    G_6,2,12                    ; 01A72  n=$4F ins 2 dur 12
        NOTE    Ds7,2,12                    ; 01A76  n=$57 ins 2 dur 12
        NOTE    G_6,2,12                    ; 01A7A  n=$4F ins 2 dur 12
        NOTE    G_6,2,12                    ; 01A7E  n=$4F ins 2 dur 12
        NOTE    F_6,2,6                     ; 01A82  n=$4D ins 2 dur 6
        NOTE    G_6,2,6                     ; 01A86  n=$4F ins 2 dur 6
        NOTE    Gs6,2,6                     ; 01A8A  n=$50 ins 2 dur 6
        NOTE    As6,2,6                     ; 01A8E  n=$52 ins 2 dur 6
        NOTE    C_7,2,6                     ; 01A92  n=$54 ins 2 dur 6
        NOTE    D_7,2,6                     ; 01A96  n=$56 ins 2 dur 6
        NOTE    Ds7,2,6                     ; 01A9A  n=$57 ins 2 dur 6
        NOTE    G_6,2,6                     ; 01A9E  n=$4F ins 2 dur 6
        NOTE    Gs6,2,6                     ; 01AA2  n=$50 ins 2 dur 6
        NOTE    As6,2,6                     ; 01AA6  n=$52 ins 2 dur 6
        NOTE    C_7,2,6                     ; 01AAA  n=$54 ins 2 dur 6
        NOTE    D_7,2,6                     ; 01AAE  n=$56 ins 2 dur 6
        NOTE    Ds7,2,12                    ; 01AB2  n=$57 ins 2 dur 12
        NOTE    G_6,2,12                    ; 01AB6  n=$4F ins 2 dur 12
        NOTE    G_6,2,12                    ; 01ABA  n=$4F ins 2 dur 12
        NOTE    Ds7,2,12                    ; 01ABE  n=$57 ins 2 dur 12
        NOTE    G_6,2,12                    ; 01AC2  n=$4F ins 2 dur 12
        NOTE    G_6,2,12                    ; 01AC6  n=$4F ins 2 dur 12
        NOTE    Gs6,2,6                     ; 01ACA  n=$50 ins 2 dur 6
        NOTE    Gs6,1,6                     ; 01ACE  n=$50 ins 1 dur 6
        NOTE    G_7,2,6                     ; 01AD2  n=$5B ins 2 dur 6
        NOTE    Fs7,2,6                     ; 01AD6  n=$5A ins 2 dur 6
        NOTE    F_7,2,6                     ; 01ADA  n=$59 ins 2 dur 6
        NOTE    Ds7,2,6                     ; 01ADE  n=$57 ins 2 dur 6
        NOTE    D_7,2,24                    ; 01AE2  n=$56 ins 2 dur 24
        NOTE    D_7,2,12                    ; 01AE6  n=$56 ins 2 dur 12
        NOTE    B_6,2,12                    ; 01AEA  n=$53 ins 2 dur 12
        NOTE    G_6,2,12                    ; 01AEE  n=$4F ins 2 dur 12
        NOTE    G_6,2,12                    ; 01AF2  n=$4F ins 2 dur 12
        NOTE    B_6,2,12                    ; 01AF6  n=$53 ins 2 dur 12
        NOTE    G_6,2,12                    ; 01AFA  n=$4F ins 2 dur 12
        NOTE    G_6,2,12                    ; 01AFE  n=$4F ins 2 dur 12
        NOTE    C_7,2,6                     ; 01B02  n=$54 ins 2 dur 6
        NOTE    C_7,2,6                     ; 01B06  n=$54 ins 2 dur 6
        NOTE    C_7,2,6                     ; 01B0A  n=$54 ins 2 dur 6
        NOTE    F_7,2,6                     ; 01B0E  n=$59 ins 2 dur 6
        NOTE    Ds7,2,6                     ; 01B12  n=$57 ins 2 dur 6
        NOTE    C_7,2,6                     ; 01B16  n=$54 ins 2 dur 6
        NOTE    As6,2,6                     ; 01B1A  n=$52 ins 2 dur 6
        NOTE    F_6,2,6                     ; 01B1E  n=$4D ins 2 dur 6
        NOTE    Gs6,2,6                     ; 01B22  n=$50 ins 2 dur 6
        NOTE    As6,2,6                     ; 01B26  n=$52 ins 2 dur 6
        NOTE    C_7,2,6                     ; 01B2A  n=$54 ins 2 dur 6
        NOTE    D_7,2,6                     ; 01B2E  n=$56 ins 2 dur 6
        NOTE    C_7,2,12                    ; 01B32  n=$54 ins 2 dur 12
        NOTE    Gs6,2,12                    ; 01B36  n=$50 ins 2 dur 12
        NOTE    Gs6,2,12                    ; 01B3A  n=$50 ins 2 dur 12
        NOTE    C_7,2,12                    ; 01B3E  n=$54 ins 2 dur 12
        NOTE    Gs6,2,12                    ; 01B42  n=$50 ins 2 dur 12
        NOTE    Gs6,2,12                    ; 01B46  n=$50 ins 2 dur 12
        NOTE    C_7,2,12                    ; 01B4A  n=$54 ins 2 dur 12
        NOTE    Gs6,2,12                    ; 01B4E  n=$50 ins 2 dur 12
        NOTE    Gs6,2,12                    ; 01B52  n=$50 ins 2 dur 12
        NOTE    Gs7,2,12                    ; 01B56  n=$5C ins 2 dur 12
        NOTE    Gs6,2,12                    ; 01B5A  n=$50 ins 2 dur 12
        NOTE    Gs6,2,12                    ; 01B5E  n=$50 ins 2 dur 12
        NOTE    As7,2,6                     ; 01B62  n=$5E ins 2 dur 6
        NOTE    F_7,2,6                     ; 01B66  n=$59 ins 2 dur 6
        NOTE    D_7,2,6                     ; 01B6A  n=$56 ins 2 dur 6
        NOTE    As6,2,6                     ; 01B6E  n=$52 ins 2 dur 6
        NOTE    F_7,2,6                     ; 01B72  n=$59 ins 2 dur 6
        NOTE    D_7,2,6                     ; 01B76  n=$56 ins 2 dur 6
        NOTE    As6,2,6                     ; 01B7A  n=$52 ins 2 dur 6
        NOTE    F_6,2,6                     ; 01B7E  n=$4D ins 2 dur 6
        NOTE    D_7,2,6                     ; 01B82  n=$56 ins 2 dur 6
        NOTE    As6,2,6                     ; 01B86  n=$52 ins 2 dur 6
        NOTE    F_6,2,6                     ; 01B8A  n=$4D ins 2 dur 6
        NOTE    D_6,2,6                     ; 01B8E  n=$4A ins 2 dur 6
        REST    18                          ; 01B92
        REST    18                          ; 01B96
        NOTE    As6,2,6                     ; 01B9A  n=$52 ins 2 dur 6
        NOTE    C_7,2,6                     ; 01B9E  n=$54 ins 2 dur 6
        NOTE    D_7,2,6                     ; 01BA2  n=$56 ins 2 dur 6
        NOTE    C_7,2,6                     ; 01BA6  n=$54 ins 2 dur 6
        NOTE    D_7,2,6                     ; 01BAA  n=$56 ins 2 dur 6
        NOTE    Ds7,2,6                     ; 01BAE  n=$57 ins 2 dur 6
        NOTE    D_7,2,6                     ; 01BB2  n=$56 ins 2 dur 6
        NOTE    Ds7,2,6                     ; 01BB6  n=$57 ins 2 dur 6
        NOTE    F_7,2,6                     ; 01BBA  n=$59 ins 2 dur 6
        NOTE    F_7,2,18                    ; 01BBE  n=$59 ins 2 dur 18
        RETURN                              ; 01BC2
Pat11:
        NOTE    C_7,2,36                    ; 01BC3  n=$54 ins 2 dur 36
        NOTE    As7,3,36                    ; 01BC7  n=$5E ins 3 dur 36
        NOTE    Gs7,3,36                    ; 01BCB  n=$5C ins 3 dur 36
        NOTE    F_7,3,72                    ; 01BCF  n=$59 ins 3 dur 72
        REST    36                          ; 01BD3
        NOTE    F_7,3,54                    ; 01BD7  n=$59 ins 3 dur 54
        RETURN                              ; 01BDB
Pat15:
        NOTE    Ds6,4,12                    ; 01BDC  n=$4B ins 4 dur 12
        NOTE    Ds6,3,12                    ; 01BE0  n=$4B ins 3 dur 12
        NOTE    Ds6,3,12                    ; 01BE4  n=$4B ins 3 dur 12
        NOTE    Ds6,4,12                    ; 01BE8  n=$4B ins 4 dur 12
        NOTE    Ds6,3,12                    ; 01BEC  n=$4B ins 3 dur 12
        NOTE    Ds6,3,12                    ; 01BF0  n=$4B ins 3 dur 12
        NOTE    F_6,4,12                    ; 01BF4  n=$4D ins 4 dur 12
        NOTE    Gs6,3,12                    ; 01BF8  n=$50 ins 3 dur 12
        NOTE    Gs6,3,12                    ; 01BFC  n=$50 ins 3 dur 12
        NOTE    Ds6,4,12                    ; 01C00  n=$4B ins 4 dur 12
        NOTE    Ds6,3,12                    ; 01C04  n=$4B ins 3 dur 12
        NOTE    Ds6,3,12                    ; 01C08  n=$4B ins 3 dur 12
        NOTE    Ds6,4,12                    ; 01C0C  n=$4B ins 4 dur 12
        NOTE    Ds7,3,6                     ; 01C10  n=$57 ins 3 dur 6
        NOTE    F_7,3,6                     ; 01C14  n=$59 ins 3 dur 6
        NOTE    G_7,3,12                    ; 01C18  n=$5B ins 3 dur 12
        NOTE    Ds6,4,12                    ; 01C1C  n=$4B ins 4 dur 12
        NOTE    Ds7,3,6                     ; 01C20  n=$57 ins 3 dur 6
        NOTE    F_7,3,6                     ; 01C24  n=$59 ins 3 dur 6
        NOTE    G_7,3,12                    ; 01C28  n=$5B ins 3 dur 12
        NOTE    F_6,4,12                    ; 01C2C  n=$4D ins 4 dur 12
        NOTE    As6,4,12                    ; 01C30  n=$52 ins 4 dur 12
        NOTE    As6,4,12                    ; 01C34  n=$52 ins 4 dur 12
        NOTE    As6,4,12                    ; 01C38  n=$52 ins 4 dur 12
        NOTE    D_7,4,12                    ; 01C3C  n=$56 ins 4 dur 12
        NOTE    D_7,4,12                    ; 01C40  n=$56 ins 4 dur 12
        NOTE    G_6,4,12                    ; 01C44  n=$4F ins 4 dur 12
        NOTE    G_7,4,12                    ; 01C48  n=$5B ins 4 dur 12
        NOTE    G_7,4,12                    ; 01C4C  n=$5B ins 4 dur 12
        NOTE    G_6,4,12                    ; 01C50  n=$4F ins 4 dur 12
        NOTE    G_7,4,12                    ; 01C54  n=$5B ins 4 dur 12
        NOTE    G_7,4,12                    ; 01C58  n=$5B ins 4 dur 12
        NOTE    Gs6,4,12                    ; 01C5C  n=$50 ins 4 dur 12
        NOTE    Gs7,4,12                    ; 01C60  n=$5C ins 4 dur 12
        NOTE    Gs7,4,12                    ; 01C64  n=$5C ins 4 dur 12
        NOTE    As6,4,12                    ; 01C68  n=$52 ins 4 dur 12
        NOTE    Gs7,4,12                    ; 01C6C  n=$5C ins 4 dur 12
        NOTE    Gs7,4,12                    ; 01C70  n=$5C ins 4 dur 12
        NOTE    Gs7,4,36                    ; 01C74  n=$5C ins 4 dur 36
        NOTE    Gs7,4,36                    ; 01C78  n=$5C ins 4 dur 36
        NOTE    Gs7,4,36                    ; 01C7C  n=$5C ins 4 dur 36
        NOTE    Gs7,4,36                    ; 01C80  n=$5C ins 4 dur 36
        REST    72                          ; 01C84
        NOTE    D_7,4,18                    ; 01C88  n=$56 ins 4 dur 18
        NOTE    D_7,4,18                    ; 01C8C  n=$56 ins 4 dur 18
        NOTE    D_7,4,18                    ; 01C90  n=$56 ins 4 dur 18
        NOTE    D_7,4,18                    ; 01C94  n=$56 ins 4 dur 18
        NOTE    As6,4,6                     ; 01C98  n=$52 ins 4 dur 6
        NOTE    C_7,4,6                     ; 01C9C  n=$54 ins 4 dur 6
        NOTE    D_7,4,6                     ; 01CA0  n=$56 ins 4 dur 6
        NOTE    D_7,4,18                    ; 01CA4  n=$56 ins 4 dur 18
        RETURN                              ; 01CA8
        dc.b    $50,$03,$24,$00,$4F,$03,$24,$00,$4D,$03,$24,$00,$52,$03,$48,$00; 01CA9  unreferenced data
        dc.b    $60,$00,$24,$00,$52,$03,$36,$00,$66; 01CB9
Pat16:
        NOTE    Ds6,3,12                    ; 01CC2  n=$4B ins 3 dur 12
        NOTE    Ds7,3,12                    ; 01CC6  n=$57 ins 3 dur 12
        NOTE    Ds7,3,12                    ; 01CCA  n=$57 ins 3 dur 12
        NOTE    Ds6,3,12                    ; 01CCE  n=$4B ins 3 dur 12
        NOTE    Ds7,3,12                    ; 01CD2  n=$57 ins 3 dur 12
        NOTE    Ds7,3,12                    ; 01CD6  n=$57 ins 3 dur 12
        NOTE    F_6,3,12                    ; 01CDA  n=$4D ins 3 dur 12
        NOTE    C_7,3,12                    ; 01CDE  n=$54 ins 3 dur 12
        NOTE    F_7,3,12                    ; 01CE2  n=$59 ins 3 dur 12
        NOTE    Ds6,3,12                    ; 01CE6  n=$4B ins 3 dur 12
        NOTE    As6,3,12                    ; 01CEA  n=$52 ins 3 dur 12
        NOTE    Ds7,3,12                    ; 01CEE  n=$57 ins 3 dur 12
        NOTE    Ds6,3,12                    ; 01CF2  n=$4B ins 3 dur 12
        NOTE    As6,3,6                     ; 01CF6  n=$52 ins 3 dur 6
        NOTE    Ds7,3,6                     ; 01CFA  n=$57 ins 3 dur 6
        NOTE    Ds7,3,12                    ; 01CFE  n=$57 ins 3 dur 12
        NOTE    Ds6,3,12                    ; 01D02  n=$4B ins 3 dur 12
        NOTE    As6,3,6                     ; 01D06  n=$52 ins 3 dur 6
        NOTE    Ds7,3,6                     ; 01D0A  n=$57 ins 3 dur 6
        NOTE    Ds7,3,12                    ; 01D0E  n=$57 ins 3 dur 12
        NOTE    F_6,3,12                    ; 01D12  n=$4D ins 3 dur 12
        NOTE    F_7,3,12                    ; 01D16  n=$59 ins 3 dur 12
        NOTE    F_7,3,12                    ; 01D1A  n=$59 ins 3 dur 12
        NOTE    As5,3,12                    ; 01D1E  n=$46 ins 3 dur 12
        NOTE    As6,3,12                    ; 01D22  n=$52 ins 3 dur 12
        NOTE    As6,3,12                    ; 01D26  n=$52 ins 3 dur 12
        NOTE    G_6,3,12                    ; 01D2A  n=$4F ins 3 dur 12
        NOTE    D_7,3,6                     ; 01D2E  n=$56 ins 3 dur 6
        NOTE    Ds7,3,6                     ; 01D32  n=$57 ins 3 dur 6
        NOTE    F_7,3,12                    ; 01D36  n=$59 ins 3 dur 12
        NOTE    G_6,3,12                    ; 01D3A  n=$4F ins 3 dur 12
        NOTE    D_7,3,6                     ; 01D3E  n=$56 ins 3 dur 6
        NOTE    Ds7,3,6                     ; 01D42  n=$57 ins 3 dur 6
        NOTE    F_7,3,12                    ; 01D46  n=$59 ins 3 dur 12
        NOTE    Gs6,3,12                    ; 01D4A  n=$50 ins 3 dur 12
        NOTE    Gs7,3,12                    ; 01D4E  n=$5C ins 3 dur 12
        NOTE    Gs7,3,12                    ; 01D52  n=$5C ins 3 dur 12
        NOTE    As6,3,12                    ; 01D56  n=$52 ins 3 dur 12
        NOTE    As7,3,12                    ; 01D5A  n=$5E ins 3 dur 12
        NOTE    As7,3,12                    ; 01D5E  n=$5E ins 3 dur 12
        NOTE    C_6,3,36                    ; 01D62  n=$48 ins 3 dur 36
        NOTE    Cs6,3,36                    ; 01D66  n=$49 ins 3 dur 36
        NOTE    D_6,3,36                    ; 01D6A  n=$4A ins 3 dur 36
        NOTE    Ds6,3,36                    ; 01D6E  n=$4B ins 3 dur 36
        NOTE    D_7,3,24                    ; 01D72  n=$56 ins 3 dur 24
        NOTE    As6,3,24                    ; 01D76  n=$52 ins 3 dur 24
        NOTE    F_6,3,24                    ; 01D7A  n=$4D ins 3 dur 24
        NOTE    As6,3,18                    ; 01D7E  n=$52 ins 3 dur 18
        NOTE    As6,3,18                    ; 01D82  n=$52 ins 3 dur 18
        NOTE    As6,3,18                    ; 01D86  n=$52 ins 3 dur 18
        NOTE    As6,3,18                    ; 01D8A  n=$52 ins 3 dur 18
        NOTE    As6,3,18                    ; 01D8E  n=$52 ins 3 dur 18
        NOTE    As6,3,18                    ; 01D92  n=$52 ins 3 dur 18
        RETURN                              ; 01D96
Mus04_Ch0:
        VOLUME  96                          ; 01D97
Loop_1D99:
        NOTE    Cs6,6,6                     ; 01D99  n=$49 ins 6 dur 6
        NOTE    E_6,6,6                     ; 01D9D  n=$4C ins 6 dur 6
        NOTE    G_6,6,6                     ; 01DA1  n=$4F ins 6 dur 6
        NOTE    Gs6,6,6                     ; 01DA5  n=$50 ins 6 dur 6
        NOTE    G_6,6,6                     ; 01DA9  n=$4F ins 6 dur 6
        NOTE    Gs6,6,6                     ; 01DAD  n=$50 ins 6 dur 6
        JUMP    Loop_1D99                   ; 01DB1
Mus04_Ch1:
        VOLUME  64                          ; 01DB4
        REST    4                           ; 01DB6
Loop_1DBA:
        NOTE    Cs6,6,6                     ; 01DBA  n=$49 ins 6 dur 6
        NOTE    E_6,6,6                     ; 01DBE  n=$4C ins 6 dur 6
        NOTE    G_6,6,6                     ; 01DC2  n=$4F ins 6 dur 6
        NOTE    Gs6,6,6                     ; 01DC6  n=$50 ins 6 dur 6
        NOTE    G_6,6,6                     ; 01DCA  n=$4F ins 6 dur 6
        NOTE    Gs6,6,6                     ; 01DCE  n=$50 ins 6 dur 6
        JUMP    Loop_1DBA                   ; 01DD2
Mus04_Ch2:
        VOLUME  255                         ; 01DD5
Loop_1DD7:
        NOTE    Cs6,5,18                    ; 01DD7  n=$49 ins 5 dur 18
        NOTE    F_6,5,18                    ; 01DDB  n=$4D ins 5 dur 18
        JUMP    Loop_1DD7                   ; 01DDF
Mus04_Ch3:
        ENDTRACK                            ; 01DE2
Mus05_Ch0:
        VOLUME  100                         ; 01DE3
        NOTE    A_7,3,6                     ; 01DE5  n=$5D ins 3 dur 6
        NOTE    G_7,3,6                     ; 01DE9  n=$5B ins 3 dur 6
        NOTE    A_7,3,6                     ; 01DED  n=$5D ins 3 dur 6
        NOTE    Fs7,3,6                     ; 01DF1  n=$5A ins 3 dur 6
        NOTE    A_7,3,6                     ; 01DF5  n=$5D ins 3 dur 6
        NOTE    E_7,3,6                     ; 01DF9  n=$58 ins 3 dur 6
        NOTE    A_7,3,6                     ; 01DFD  n=$5D ins 3 dur 6
        NOTE    D_7,3,6                     ; 01E01  n=$56 ins 3 dur 6
        NOTE    A_7,3,6                     ; 01E05  n=$5D ins 3 dur 6
        NOTE    G_7,3,6                     ; 01E09  n=$5B ins 3 dur 6
        NOTE    A_7,3,6                     ; 01E0D  n=$5D ins 3 dur 6
        NOTE    Fs7,3,6                     ; 01E11  n=$5A ins 3 dur 6
        NOTE    A_7,3,6                     ; 01E15  n=$5D ins 3 dur 6
        NOTE    E_7,3,6                     ; 01E19  n=$58 ins 3 dur 6
        NOTE    A_7,3,6                     ; 01E1D  n=$5D ins 3 dur 6
        NOTE    D_7,3,6                     ; 01E21  n=$56 ins 3 dur 6
        NOTE    A_7,3,6                     ; 01E25  n=$5D ins 3 dur 6
        NOTE    E_7,3,6                     ; 01E29  n=$58 ins 3 dur 6
        NOTE    A_7,3,6                     ; 01E2D  n=$5D ins 3 dur 6
        NOTE    Fs7,3,6                     ; 01E31  n=$5A ins 3 dur 6
        NOTE    G_7,3,6                     ; 01E35  n=$5B ins 3 dur 6
        NOTE    A_7,3,6                     ; 01E39  n=$5D ins 3 dur 6
        NOTE    Fs7,3,6                     ; 01E3D  n=$5A ins 3 dur 6
        NOTE    A_7,3,6                     ; 01E41  n=$5D ins 3 dur 6
        NOTE    Cs7,3,6                     ; 01E45  n=$55 ins 3 dur 6
        NOTE    E_7,3,6                     ; 01E49  n=$58 ins 3 dur 6
        NOTE    D_7,3,48                    ; 01E4D  n=$56 ins 3 dur 48
        REST    6                           ; 01E51
        ENDTRACK                            ; 01E55
Mus05_Ch1:
        VOLUME  100                         ; 01E56
        REST    3                           ; 01E58
        NOTE    A_7,3,6                     ; 01E5C  n=$5D ins 3 dur 6
        NOTE    G_7,3,6                     ; 01E60  n=$5B ins 3 dur 6
        NOTE    A_7,3,6                     ; 01E64  n=$5D ins 3 dur 6
        NOTE    Fs7,3,6                     ; 01E68  n=$5A ins 3 dur 6
        NOTE    A_7,3,6                     ; 01E6C  n=$5D ins 3 dur 6
        NOTE    E_7,3,6                     ; 01E70  n=$58 ins 3 dur 6
        NOTE    A_7,3,6                     ; 01E74  n=$5D ins 3 dur 6
        NOTE    D_7,3,6                     ; 01E78  n=$56 ins 3 dur 6
        NOTE    A_7,3,6                     ; 01E7C  n=$5D ins 3 dur 6
        NOTE    G_7,3,6                     ; 01E80  n=$5B ins 3 dur 6
        NOTE    A_7,3,6                     ; 01E84  n=$5D ins 3 dur 6
        NOTE    Fs7,3,6                     ; 01E88  n=$5A ins 3 dur 6
        NOTE    A_7,3,6                     ; 01E8C  n=$5D ins 3 dur 6
        NOTE    E_7,3,6                     ; 01E90  n=$58 ins 3 dur 6
        NOTE    A_7,3,6                     ; 01E94  n=$5D ins 3 dur 6
        NOTE    D_7,3,6                     ; 01E98  n=$56 ins 3 dur 6
        NOTE    A_7,3,6                     ; 01E9C  n=$5D ins 3 dur 6
        NOTE    E_7,3,6                     ; 01EA0  n=$58 ins 3 dur 6
        NOTE    A_7,3,6                     ; 01EA4  n=$5D ins 3 dur 6
        NOTE    Fs7,3,6                     ; 01EA8  n=$5A ins 3 dur 6
        NOTE    G_7,3,6                     ; 01EAC  n=$5B ins 3 dur 6
        NOTE    A_7,3,6                     ; 01EB0  n=$5D ins 3 dur 6
        NOTE    Fs7,3,6                     ; 01EB4  n=$5A ins 3 dur 6
        NOTE    A_7,3,6                     ; 01EB8  n=$5D ins 3 dur 6
        NOTE    Cs7,3,6                     ; 01EBC  n=$55 ins 3 dur 6
        NOTE    E_7,3,6                     ; 01EC0  n=$58 ins 3 dur 6
        NOTE    D_7,3,12                    ; 01EC4  n=$56 ins 3 dur 12
        REST    3                           ; 01EC8
        ENDTRACK                            ; 01ECC
Mus05_Ch2:
        VOLUME  200                         ; 01ECD
        REST    6                           ; 01ECF
        NOTE    A_7,3,6                     ; 01ED3  n=$5D ins 3 dur 6
        NOTE    G_7,3,6                     ; 01ED7  n=$5B ins 3 dur 6
        NOTE    A_7,3,6                     ; 01EDB  n=$5D ins 3 dur 6
        NOTE    Fs7,3,6                     ; 01EDF  n=$5A ins 3 dur 6
        NOTE    A_7,3,6                     ; 01EE3  n=$5D ins 3 dur 6
        NOTE    E_7,3,6                     ; 01EE7  n=$58 ins 3 dur 6
        NOTE    A_7,3,6                     ; 01EEB  n=$5D ins 3 dur 6
        NOTE    D_7,3,6                     ; 01EEF  n=$56 ins 3 dur 6
        NOTE    A_7,3,6                     ; 01EF3  n=$5D ins 3 dur 6
        NOTE    G_7,3,6                     ; 01EF7  n=$5B ins 3 dur 6
        NOTE    A_7,3,6                     ; 01EFB  n=$5D ins 3 dur 6
        NOTE    Fs7,3,6                     ; 01EFF  n=$5A ins 3 dur 6
        NOTE    A_7,3,6                     ; 01F03  n=$5D ins 3 dur 6
        NOTE    E_7,3,6                     ; 01F07  n=$58 ins 3 dur 6
        NOTE    A_7,3,6                     ; 01F0B  n=$5D ins 3 dur 6
        NOTE    D_7,3,6                     ; 01F0F  n=$56 ins 3 dur 6
        NOTE    A_7,3,6                     ; 01F13  n=$5D ins 3 dur 6
        NOTE    E_7,3,6                     ; 01F17  n=$58 ins 3 dur 6
        NOTE    A_7,3,6                     ; 01F1B  n=$5D ins 3 dur 6
        NOTE    Fs7,3,6                     ; 01F1F  n=$5A ins 3 dur 6
        NOTE    G_7,3,6                     ; 01F23  n=$5B ins 3 dur 6
        NOTE    A_7,3,6                     ; 01F27  n=$5D ins 3 dur 6
        NOTE    Fs7,3,6                     ; 01F2B  n=$5A ins 3 dur 6
        NOTE    A_7,3,6                     ; 01F2F  n=$5D ins 3 dur 6
        NOTE    Cs7,3,6                     ; 01F33  n=$55 ins 3 dur 6
        NOTE    E_7,3,6                     ; 01F37  n=$58 ins 3 dur 6
        NOTE    D_7,3,12                    ; 01F3B  n=$56 ins 3 dur 12
        ENDTRACK                            ; 01F3F
Mus05_Ch3:
        ENDTRACK                            ; 01F40
Mus06_Ch0:
        VOLUME  96                          ; 01F41
        NOTE    B_6,6,36                    ; 01F43  n=$53 ins 6 dur 36
        NOTE    B_6,6,12                    ; 01F47  n=$53 ins 6 dur 12
        NOTE    C_7,6,12                    ; 01F4B  n=$54 ins 6 dur 12
        NOTE    B_6,6,36                    ; 01F4F  n=$53 ins 6 dur 36
        VOLUME  106                         ; 01F53
        NOTE    B_6,6,36                    ; 01F55  n=$53 ins 6 dur 36
        NOTE    B_6,6,12                    ; 01F59  n=$53 ins 6 dur 12
        NOTE    C_7,6,12                    ; 01F5D  n=$54 ins 6 dur 12
        NOTE    B_6,6,36                    ; 01F61  n=$53 ins 6 dur 36
        VOLUME  116                         ; 01F65
        NOTE    A_6,6,12                    ; 01F67  n=$51 ins 6 dur 12
        NOTE    B_6,6,12                    ; 01F6B  n=$53 ins 6 dur 12
        NOTE    C_7,6,12                    ; 01F6F  n=$54 ins 6 dur 12
        NOTE    E_7,6,12                    ; 01F73  n=$58 ins 6 dur 12
        VOLUME  128                         ; 01F77
        NOTE    G_7,6,12                    ; 01F79  n=$5B ins 6 dur 12
        NOTE    G_7,6,6                     ; 01F7D  n=$5B ins 6 dur 6
        NOTE    G_7,6,6                     ; 01F81  n=$5B ins 6 dur 6
        NOTE    A_7,6,12                    ; 01F85  n=$5D ins 6 dur 12
        NOTE    G_7,6,6                     ; 01F89  n=$5B ins 6 dur 6
        NOTE    A_7,6,6                     ; 01F8D  n=$5D ins 6 dur 6
        VOLUME  160                         ; 01F91
        NOTE    B_7,6,128                   ; 01F93  n=$5F ins 6 dur 128
        ENDTRACK                            ; 01F97
Mus06_Ch1:
        VOLUME  64                          ; 01F98
        NOTE    D_6,6,36                    ; 01F9A  n=$4A ins 6 dur 36
        NOTE    D_6,6,12                    ; 01F9E  n=$4A ins 6 dur 12
        NOTE    D_6,6,12                    ; 01FA2  n=$4A ins 6 dur 12
        NOTE    D_6,6,36                    ; 01FA6  n=$4A ins 6 dur 36
        VOLUME  74                          ; 01FAA
        NOTE    E_6,6,36                    ; 01FAC  n=$4C ins 6 dur 36
        NOTE    E_6,6,12                    ; 01FB0  n=$4C ins 6 dur 12
        NOTE    E_6,6,12                    ; 01FB4  n=$4C ins 6 dur 12
        NOTE    E_6,6,36                    ; 01FB8  n=$4C ins 6 dur 36
        VOLUME  84                          ; 01FBC
        NOTE    C_6,6,12                    ; 01FBE  n=$48 ins 6 dur 12
        NOTE    C_6,6,12                    ; 01FC2  n=$48 ins 6 dur 12
        NOTE    E_6,6,12                    ; 01FC6  n=$4C ins 6 dur 12
        NOTE    A_6,6,12                    ; 01FCA  n=$51 ins 6 dur 12
        VOLUME  96                          ; 01FCE
        NOTE    C_7,6,12                    ; 01FD0  n=$54 ins 6 dur 12
        NOTE    C_7,6,6                     ; 01FD4  n=$54 ins 6 dur 6
        NOTE    C_7,6,6                     ; 01FD8  n=$54 ins 6 dur 6
        NOTE    D_7,2,12                    ; 01FDC  n=$56 ins 2 dur 12
        NOTE    D_7,6,6                     ; 01FE0  n=$56 ins 6 dur 6
        NOTE    D_7,6,6                     ; 01FE4  n=$56 ins 6 dur 6
        VOLUME  128                         ; 01FE8
        NOTE    D_7,6,128                   ; 01FEA  n=$56 ins 6 dur 128
        ENDTRACK                            ; 01FEE
Mus06_Ch2:
        VOLUME  160                         ; 01FEF
        NOTE    G_7,5,12                    ; 01FF1  n=$5B ins 5 dur 12
        NOTE    D_7,5,12                    ; 01FF5  n=$56 ins 5 dur 12
        NOTE    G_7,5,12                    ; 01FF9  n=$5B ins 5 dur 12
        NOTE    A_7,5,12                    ; 01FFD  n=$5D ins 5 dur 12
        VOLUME  180                         ; 02001
        NOTE    B_6,5,12                    ; 02003  n=$53 ins 5 dur 12
        NOTE    A_7,5,12                    ; 02007  n=$5D ins 5 dur 12
        NOTE    G_7,5,12                    ; 0200B  n=$5B ins 5 dur 12
        NOTE    D_7,5,12                    ; 0200F  n=$56 ins 5 dur 12
        VOLUME  200                         ; 02013
        NOTE    Gs7,5,12                    ; 02015  n=$5C ins 5 dur 12
        NOTE    D_7,5,12                    ; 02019  n=$56 ins 5 dur 12
        NOTE    Gs7,5,12                    ; 0201D  n=$5C ins 5 dur 12
        NOTE    A_7,5,12                    ; 02021  n=$5D ins 5 dur 12
        VOLUME  220                         ; 02025
        NOTE    B_6,5,12                    ; 02027  n=$53 ins 5 dur 12
        NOTE    A_7,5,12                    ; 0202B  n=$5D ins 5 dur 12
        NOTE    Gs7,5,12                    ; 0202F  n=$5C ins 5 dur 12
        NOTE    D_7,5,12                    ; 02033  n=$56 ins 5 dur 12
        VOLUME  240                         ; 02037
        NOTE    A_7,5,12                    ; 02039  n=$5D ins 5 dur 12
        NOTE    G_7,5,12                    ; 0203D  n=$5B ins 5 dur 12
        NOTE    E_7,5,12                    ; 02041  n=$58 ins 5 dur 12
        NOTE    C_7,5,12                    ; 02045  n=$54 ins 5 dur 12
        VOLUME  245                         ; 02049
        NOTE    A_7,5,12                    ; 0204B  n=$5D ins 5 dur 12
        NOTE    G_7,5,6                     ; 0204F  n=$5B ins 5 dur 6
        NOTE    G_7,5,6                     ; 02053  n=$5B ins 5 dur 6
        NOTE    E_7,5,12                    ; 02057  n=$58 ins 5 dur 12
        NOTE    C_7,5,6                     ; 0205B  n=$54 ins 5 dur 6
        NOTE    C_7,5,6                     ; 0205F  n=$54 ins 5 dur 6
        VOLUME  255                         ; 02063
        NOTE    G_6,5,128                   ; 02065  n=$4F ins 5 dur 128
        ENDTRACK                            ; 02069
Mus06_Ch3:
        VOLUME  64                          ; 0206A
        NOTE    G_6,6,36                    ; 0206C  n=$4F ins 6 dur 36
        NOTE    G_6,6,12                    ; 02070  n=$4F ins 6 dur 12
        NOTE    A_6,6,12                    ; 02074  n=$51 ins 6 dur 12
        NOTE    G_6,6,36                    ; 02078  n=$4F ins 6 dur 36
        NOTE    Gs6,6,36                    ; 0207C  n=$50 ins 6 dur 36
        NOTE    Gs6,6,12                    ; 02080  n=$50 ins 6 dur 12
        NOTE    A_6,6,12                    ; 02084  n=$51 ins 6 dur 12
        NOTE    Gs6,6,36                    ; 02088  n=$50 ins 6 dur 36
        NOTE    E_6,6,12                    ; 0208C  n=$4C ins 6 dur 12
        NOTE    E_6,6,12                    ; 02090  n=$4C ins 6 dur 12
        NOTE    A_6,6,12                    ; 02094  n=$51 ins 6 dur 12
        NOTE    C_7,6,12                    ; 02098  n=$54 ins 6 dur 12
        VOLUME  96                          ; 0209C
        NOTE    Ds7,6,12                    ; 0209E  n=$57 ins 6 dur 12
        NOTE    Ds7,6,6                     ; 020A2  n=$57 ins 6 dur 6
        NOTE    Ds7,6,6                     ; 020A6  n=$57 ins 6 dur 6
        NOTE    Fs7,6,12                    ; 020AA  n=$5A ins 6 dur 12
        NOTE    E_7,6,6                     ; 020AE  n=$58 ins 6 dur 6
        NOTE    Fs7,6,6                     ; 020B2  n=$5A ins 6 dur 6
        VOLUME  128                         ; 020B6
        NOTE    G_7,6,128                   ; 020B8  n=$5B ins 6 dur 128
        ENDTRACK                            ; 020BC
Mus07_Ch0:
        VOLUME  128                         ; 020BD
        NOTE    Fs7,6,12                    ; 020BF  n=$5A ins 6 dur 12
        NOTE    G_7,6,12                    ; 020C3  n=$5B ins 6 dur 12
        NOTE    Fs7,6,9                     ; 020C7  n=$5A ins 6 dur 9
        NOTE    F_7,6,9                     ; 020CB  n=$59 ins 6 dur 9
        NOTE    E_7,6,6                     ; 020CF  n=$58 ins 6 dur 6
        NOTE    Ds7,6,6                     ; 020D3  n=$57 ins 6 dur 6
        NOTE    D_7,6,6                     ; 020D7  n=$56 ins 6 dur 6
        NOTE    Cs7,6,6                     ; 020DB  n=$55 ins 6 dur 6
        NOTE    C_7,6,6                     ; 020DF  n=$54 ins 6 dur 6
        NOTE    B_6,6,6                     ; 020E3  n=$53 ins 6 dur 6
        NOTE    As6,6,6                     ; 020E7  n=$52 ins 6 dur 6
        NOTE    A_6,6,6                     ; 020EB  n=$51 ins 6 dur 6
        NOTE    Gs6,6,6                     ; 020EF  n=$50 ins 6 dur 6
        NOTE    G_6,6,6                     ; 020F3  n=$4F ins 6 dur 6
        NOTE    Fs6,6,24                    ; 020F7  n=$4E ins 6 dur 24
        ENDTRACK                            ; 020FB
Mus07_Ch1:
        VOLUME  96                          ; 020FC
        NOTE    Fs6,6,12                    ; 020FE  n=$4E ins 6 dur 12
        NOTE    F_6,6,12                    ; 02102  n=$4D ins 6 dur 12
        NOTE    Fs6,6,9                     ; 02106  n=$4E ins 6 dur 9
        NOTE    G_6,6,9                     ; 0210A  n=$4F ins 6 dur 9
        NOTE    Gs6,6,6                     ; 0210E  n=$50 ins 6 dur 6
        NOTE    A_6,6,6                     ; 02112  n=$51 ins 6 dur 6
        NOTE    As6,6,6                     ; 02116  n=$52 ins 6 dur 6
        NOTE    B_6,6,6                     ; 0211A  n=$53 ins 6 dur 6
        NOTE    C_6,6,6                     ; 0211E  n=$48 ins 6 dur 6
        NOTE    Cs6,6,6                     ; 02122  n=$49 ins 6 dur 6
        NOTE    D_6,6,6                     ; 02126  n=$4A ins 6 dur 6
        NOTE    Ds6,6,6                     ; 0212A  n=$4B ins 6 dur 6
        NOTE    E_6,6,6                     ; 0212E  n=$4C ins 6 dur 6
        NOTE    F_6,6,6                     ; 02132  n=$4D ins 6 dur 6
        NOTE    Fs6,6,24                    ; 02136  n=$4E ins 6 dur 24
        ENDTRACK                            ; 0213A
Mus07_Ch2:
        VOLUME  200                         ; 0213B
        NOTE    Fs6,5,12                    ; 0213D  n=$4E ins 5 dur 12
        NOTE    F_6,5,12                    ; 02141  n=$4D ins 5 dur 12
        NOTE    Fs6,5,9                     ; 02145  n=$4E ins 5 dur 9
        NOTE    G_6,5,9                     ; 02149  n=$4F ins 5 dur 9
        NOTE    Gs6,5,6                     ; 0214D  n=$50 ins 5 dur 6
        NOTE    A_6,5,6                     ; 02151  n=$51 ins 5 dur 6
        NOTE    As6,5,6                     ; 02155  n=$52 ins 5 dur 6
        NOTE    B_6,5,6                     ; 02159  n=$53 ins 5 dur 6
        NOTE    C_7,5,6                     ; 0215D  n=$54 ins 5 dur 6
        NOTE    B_6,5,6                     ; 02161  n=$53 ins 5 dur 6
        NOTE    As6,5,6                     ; 02165  n=$52 ins 5 dur 6
        NOTE    A_6,5,6                     ; 02169  n=$51 ins 5 dur 6
        NOTE    Gs6,5,6                     ; 0216D  n=$50 ins 5 dur 6
        NOTE    G_6,5,6                     ; 02171  n=$4F ins 5 dur 6
        NOTE    Fs6,5,24                    ; 02175  n=$4E ins 5 dur 24
        ENDTRACK                            ; 02179
Mus07_Ch3:
        ENDTRACK                            ; 0217A
Mus08_Ch0:
        VOLUME  128                         ; 0217B
        NOTE    G_7,6,3                     ; 0217D  n=$5B ins 6 dur 3
        NOTE    Fs7,6,3                     ; 02181  n=$5A ins 6 dur 3
        NOTE    F_7,6,3                     ; 02185  n=$59 ins 6 dur 3
        NOTE    E_7,6,4                     ; 02189  n=$58 ins 6 dur 4
        NOTE    Ds7,6,4                     ; 0218D  n=$57 ins 6 dur 4
        NOTE    D_7,6,4                     ; 02191  n=$56 ins 6 dur 4
        NOTE    Cs7,6,6                     ; 02195  n=$55 ins 6 dur 6
        NOTE    C_7,6,6                     ; 02199  n=$54 ins 6 dur 6
        NOTE    C_7,6,24                    ; 0219D  n=$54 ins 6 dur 24
        NOTE    C_7,6,8                     ; 021A1  n=$54 ins 6 dur 8
        NOTE    C_7,6,8                     ; 021A5  n=$54 ins 6 dur 8
        NOTE    C_7,6,8                     ; 021A9  n=$54 ins 6 dur 8
        NOTE    Ds7,6,24                    ; 021AD  n=$57 ins 6 dur 24
        NOTE    F_7,6,8                     ; 021B1  n=$59 ins 6 dur 8
        NOTE    Ds7,6,8                     ; 021B5  n=$57 ins 6 dur 8
        NOTE    F_7,6,8                     ; 021B9  n=$59 ins 6 dur 8
        NOTE    G_7,6,96                    ; 021BD  n=$5B ins 6 dur 96
        ENDTRACK                            ; 021C1
Mus08_Ch1:
        VOLUME  80                          ; 021C2
        NOTE    G_6,6,3                     ; 021C4  n=$4F ins 6 dur 3
        NOTE    Gs6,6,3                     ; 021C8  n=$50 ins 6 dur 3
        NOTE    A_6,6,3                     ; 021CC  n=$51 ins 6 dur 3
        NOTE    As6,6,4                     ; 021D0  n=$52 ins 6 dur 4
        NOTE    Ds7,6,4                     ; 021D4  n=$57 ins 6 dur 4
        NOTE    D_7,6,4                     ; 021D8  n=$56 ins 6 dur 4
        NOTE    Cs7,6,6                     ; 021DC  n=$55 ins 6 dur 6
        NOTE    C_7,6,6                     ; 021E0  n=$54 ins 6 dur 6
        NOTE    Ds7,6,24                    ; 021E4  n=$57 ins 6 dur 24
        NOTE    Ds7,6,8                     ; 021E8  n=$57 ins 6 dur 8
        NOTE    Ds7,6,8                     ; 021EC  n=$57 ins 6 dur 8
        NOTE    Ds7,6,8                     ; 021F0  n=$57 ins 6 dur 8
        NOTE    C_7,6,24                    ; 021F4  n=$54 ins 6 dur 24
        NOTE    D_7,6,8                     ; 021F8  n=$56 ins 6 dur 8
        NOTE    C_7,6,8                     ; 021FC  n=$54 ins 6 dur 8
        NOTE    D_7,6,8                     ; 02200  n=$56 ins 6 dur 8
        NOTE    B_6,6,96                    ; 02204  n=$53 ins 6 dur 96
        ENDTRACK                            ; 02208
Mus08_Ch2:
        VOLUME  255                         ; 02209
        NOTE    G_6,5,3                     ; 0220B  n=$4F ins 5 dur 3
        NOTE    Gs6,5,3                     ; 0220F  n=$50 ins 5 dur 3
        NOTE    A_6,5,3                     ; 02213  n=$51 ins 5 dur 3
        NOTE    As6,5,4                     ; 02217  n=$52 ins 5 dur 4
        NOTE    B_6,5,4                     ; 0221B  n=$53 ins 5 dur 4
        NOTE    C_6,5,4                     ; 0221F  n=$48 ins 5 dur 4
        NOTE    C_7,5,6                     ; 02223  n=$54 ins 5 dur 6
        NOTE    C_7,5,6                     ; 02227  n=$54 ins 5 dur 6
        NOTE    C_7,5,24                    ; 0222B  n=$54 ins 5 dur 24
        NOTE    C_7,5,8                     ; 0222F  n=$54 ins 5 dur 8
        NOTE    C_7,5,8                     ; 02233  n=$54 ins 5 dur 8
        NOTE    C_7,5,8                     ; 02237  n=$54 ins 5 dur 8
        NOTE    A_6,5,24                    ; 0223B  n=$51 ins 5 dur 24
        NOTE    A_6,5,8                     ; 0223F  n=$51 ins 5 dur 8
        NOTE    A_6,5,8                     ; 02243  n=$51 ins 5 dur 8
        NOTE    A_6,5,8                     ; 02247  n=$51 ins 5 dur 8
        NOTE    G_6,5,96                    ; 0224B  n=$4F ins 5 dur 96
        ENDTRACK                            ; 0224F
Mus08_Ch3:
        ENDTRACK                            ; 02250
Mus09_Ch0:
        VOLUME  128                         ; 02251
        CALL    17,0                        ; 02253  pattern, transpose
        CALL    17,-3                       ; 02256  pattern, transpose
        NOTE    C_4,6,6                     ; 02259  n=$30 ins 6 dur 6
        NOTE    E_4,6,6                     ; 0225D  n=$34 ins 6 dur 6
        NOTE    G_4,6,6                     ; 02261  n=$37 ins 6 dur 6
        NOTE    As4,6,6                     ; 02265  n=$3A ins 6 dur 6
        NOTE    C_5,6,6                     ; 02269  n=$3C ins 6 dur 6
        NOTE    E_5,6,6                     ; 0226D  n=$40 ins 6 dur 6
        NOTE    G_5,6,6                     ; 02271  n=$43 ins 6 dur 6
        NOTE    As5,6,6                     ; 02275  n=$46 ins 6 dur 6
        NOTE    C_6,6,6                     ; 02279  n=$48 ins 6 dur 6
        NOTE    E_6,6,6                     ; 0227D  n=$4C ins 6 dur 6
        NOTE    G_6,6,6                     ; 02281  n=$4F ins 6 dur 6
        NOTE    As6,6,6                     ; 02285  n=$52 ins 6 dur 6
        NOTE    C_7,6,6                     ; 02289  n=$54 ins 6 dur 6
        REST    24                          ; 0228D
        REST    24                          ; 02291
        REST    24                          ; 02295
        VOLUME  150                         ; 02299
        NOTE    F_6,1,6                     ; 0229B  n=$4D ins 1 dur 6
        NOTE    E_6,1,6                     ; 0229F  n=$4C ins 1 dur 6
        NOTE    F_6,1,12                    ; 022A3  n=$4D ins 1 dur 12
        NOTE    F_5,1,12                    ; 022A7  n=$41 ins 1 dur 12
        NOTE    F_6,1,6                     ; 022AB  n=$4D ins 1 dur 6
        NOTE    E_6,1,6                     ; 022AF  n=$4C ins 1 dur 6
        NOTE    F_6,1,12                    ; 022B3  n=$4D ins 1 dur 12
        NOTE    F_5,1,12                    ; 022B7  n=$41 ins 1 dur 12
        NOTE    A_5,1,12                    ; 022BB  n=$45 ins 1 dur 12
        NOTE    F_5,1,12                    ; 022BF  n=$41 ins 1 dur 12
        NOTE    A_5,1,12                    ; 022C3  n=$45 ins 1 dur 12
        NOTE    C_6,1,12                    ; 022C7  n=$48 ins 1 dur 12
        NOTE    F_6,1,36                    ; 022CB  n=$4D ins 1 dur 36
        NOTE    C_7,1,6                     ; 022CF  n=$54 ins 1 dur 6
        NOTE    As6,1,6                     ; 022D3  n=$52 ins 1 dur 6
        NOTE    A_6,1,6                     ; 022D7  n=$51 ins 1 dur 6
        NOTE    G_6,1,6                     ; 022DB  n=$4F ins 1 dur 6
        NOTE    F_6,1,6                     ; 022DF  n=$4D ins 1 dur 6
        NOTE    E_6,1,6                     ; 022E3  n=$4C ins 1 dur 6
        NOTE    D_7,1,6                     ; 022E7  n=$56 ins 1 dur 6
        NOTE    C_7,1,6                     ; 022EB  n=$54 ins 1 dur 6
        NOTE    As6,1,6                     ; 022EF  n=$52 ins 1 dur 6
        NOTE    A_6,1,6                     ; 022F3  n=$51 ins 1 dur 6
        NOTE    G_6,1,6                     ; 022F7  n=$4F ins 1 dur 6
        NOTE    F_6,1,6                     ; 022FB  n=$4D ins 1 dur 6
        NOTE    E_6,1,12                    ; 022FF  n=$4C ins 1 dur 12
        NOTE    G_6,1,12                    ; 02303  n=$4F ins 1 dur 12
        NOTE    C_7,1,12                    ; 02307  n=$54 ins 1 dur 12
        NOTE    E_7,1,12                    ; 0230B  n=$58 ins 1 dur 12
        NOTE    C_7,1,12                    ; 0230F  n=$54 ins 1 dur 12
        NOTE    E_7,1,12                    ; 02313  n=$58 ins 1 dur 12
        NOTE    F_7,1,12                    ; 02317  n=$59 ins 1 dur 12
        NOTE    F_6,1,12                    ; 0231B  n=$4D ins 1 dur 12
        NOTE    F_7,1,6                     ; 0231F  n=$59 ins 1 dur 6
        NOTE    E_7,1,6                     ; 02323  n=$58 ins 1 dur 6
        NOTE    F_7,1,12                    ; 02327  n=$59 ins 1 dur 12
        NOTE    F_6,1,12                    ; 0232B  n=$4D ins 1 dur 12
        NOTE    F_7,1,6                     ; 0232F  n=$59 ins 1 dur 6
        NOTE    E_7,1,6                     ; 02333  n=$58 ins 1 dur 6
        NOTE    F_7,1,12                    ; 02337  n=$59 ins 1 dur 12
        NOTE    F_6,1,24                    ; 0233B  n=$4D ins 1 dur 24
        NOTE    D_7,1,6                     ; 0233F  n=$56 ins 1 dur 6
        NOTE    C_7,1,6                     ; 02343  n=$54 ins 1 dur 6
        NOTE    As6,1,6                     ; 02347  n=$52 ins 1 dur 6
        NOTE    A_6,1,6                     ; 0234B  n=$51 ins 1 dur 6
        NOTE    G_6,1,6                     ; 0234F  n=$4F ins 1 dur 6
        NOTE    F_6,1,6                     ; 02353  n=$4D ins 1 dur 6
        NOTE    E_6,1,6                     ; 02357  n=$4C ins 1 dur 6
        NOTE    F_6,1,6                     ; 0235B  n=$4D ins 1 dur 6
        NOTE    G_6,1,6                     ; 0235F  n=$4F ins 1 dur 6
        NOTE    As6,1,6                     ; 02363  n=$52 ins 1 dur 6
        NOTE    A_6,1,6                     ; 02367  n=$51 ins 1 dur 6
        NOTE    E_6,1,6                     ; 0236B  n=$4C ins 1 dur 6
        NOTE    F_6,1,48                    ; 0236F  n=$4D ins 1 dur 48
        ENDTRACK                            ; 02373
Mus09_Ch1:
        VOLUME  80                          ; 02374
        REST    24                          ; 02376
        CALL    17,0                        ; 0237A  pattern, transpose
        CALL    17,-3                       ; 0237D  pattern, transpose
        NOTE    C_4,6,6                     ; 02380  n=$30 ins 6 dur 6
        NOTE    E_4,6,6                     ; 02384  n=$34 ins 6 dur 6
        NOTE    G_4,6,6                     ; 02388  n=$37 ins 6 dur 6
        NOTE    As4,6,6                     ; 0238C  n=$3A ins 6 dur 6
        NOTE    C_5,6,6                     ; 02390  n=$3C ins 6 dur 6
        NOTE    E_5,6,6                     ; 02394  n=$40 ins 6 dur 6
        NOTE    G_5,6,6                     ; 02398  n=$43 ins 6 dur 6
        NOTE    As5,6,6                     ; 0239C  n=$46 ins 6 dur 6
        NOTE    C_6,6,6                     ; 023A0  n=$48 ins 6 dur 6
        NOTE    E_6,6,6                     ; 023A4  n=$4C ins 6 dur 6
        NOTE    G_6,6,6                     ; 023A8  n=$4F ins 6 dur 6
        NOTE    As6,6,6                     ; 023AC  n=$52 ins 6 dur 6
        NOTE    C_7,6,6                     ; 023B0  n=$54 ins 6 dur 6
        REST    24                          ; 023B4
        REST    24                          ; 023B8
        VOLUME  100                         ; 023BC
        ENDTRACK                            ; 023BE
Mus09_Ch2:
        VOLUME  45                          ; 023BF
        REST    24                          ; 023C1
        REST    24                          ; 023C5
        CALL    17,0                        ; 023C9  pattern, transpose
        CALL    17,-3                       ; 023CC  pattern, transpose
        NOTE    C_4,6,6                     ; 023CF  n=$30 ins 6 dur 6
        NOTE    E_4,6,6                     ; 023D3  n=$34 ins 6 dur 6
        NOTE    G_4,6,6                     ; 023D7  n=$37 ins 6 dur 6
        NOTE    As4,6,6                     ; 023DB  n=$3A ins 6 dur 6
        NOTE    C_5,6,6                     ; 023DF  n=$3C ins 6 dur 6
        NOTE    E_5,6,6                     ; 023E3  n=$40 ins 6 dur 6
        NOTE    G_5,6,6                     ; 023E7  n=$43 ins 6 dur 6
        NOTE    As5,6,6                     ; 023EB  n=$46 ins 6 dur 6
        NOTE    C_6,6,6                     ; 023EF  n=$48 ins 6 dur 6
        NOTE    E_6,6,6                     ; 023F3  n=$4C ins 6 dur 6
        NOTE    G_6,6,6                     ; 023F7  n=$4F ins 6 dur 6
        NOTE    As6,6,6                     ; 023FB  n=$52 ins 6 dur 6
        NOTE    C_7,6,6                     ; 023FF  n=$54 ins 6 dur 6
        REST    24                          ; 02403
        VOLUME  100                         ; 02407
        REST    12                          ; 02409
        NOTE    A_5,2,12                    ; 0240D  n=$45 ins 2 dur 12
        NOTE    F_5,2,12                    ; 02411  n=$41 ins 2 dur 12
        NOTE    C_5,2,12                    ; 02415  n=$3C ins 2 dur 12
        NOTE    A_5,2,12                    ; 02419  n=$45 ins 2 dur 12
        NOTE    F_5,2,12                    ; 0241D  n=$41 ins 2 dur 12
        NOTE    C_5,2,12                    ; 02421  n=$3C ins 2 dur 12
        NOTE    A_5,2,12                    ; 02425  n=$45 ins 2 dur 12
        NOTE    F_5,2,12                    ; 02429  n=$41 ins 2 dur 12
        NOTE    C_5,2,12                    ; 0242D  n=$3C ins 2 dur 12
        NOTE    A_5,2,12                    ; 02431  n=$45 ins 2 dur 12
        NOTE    F_5,2,12                    ; 02435  n=$41 ins 2 dur 12
        NOTE    C_5,2,12                    ; 02439  n=$3C ins 2 dur 12
        NOTE    G_5,2,12                    ; 0243D  n=$43 ins 2 dur 12
        NOTE    C_5,2,12                    ; 02441  n=$3C ins 2 dur 12
        NOTE    C_5,2,12                    ; 02445  n=$3C ins 2 dur 12
        NOTE    G_5,2,12                    ; 02449  n=$43 ins 2 dur 12
        NOTE    C_5,2,12                    ; 0244D  n=$3C ins 2 dur 12
        NOTE    C_5,2,12                    ; 02451  n=$3C ins 2 dur 12
        NOTE    G_5,2,12                    ; 02455  n=$43 ins 2 dur 12
        NOTE    C_5,2,12                    ; 02459  n=$3C ins 2 dur 12
        NOTE    C_5,2,12                    ; 0245D  n=$3C ins 2 dur 12
        NOTE    G_5,2,12                    ; 02461  n=$43 ins 2 dur 12
        NOTE    C_5,2,12                    ; 02465  n=$3C ins 2 dur 12
        NOTE    C_5,2,12                    ; 02469  n=$3C ins 2 dur 12
        NOTE    A_5,2,12                    ; 0246D  n=$45 ins 2 dur 12
        NOTE    C_4,2,12                    ; 02471  n=$30 ins 2 dur 12
        NOTE    C_4,2,12                    ; 02475  n=$30 ins 2 dur 12
        NOTE    A_5,2,12                    ; 02479  n=$45 ins 2 dur 12
        NOTE    C_4,2,12                    ; 0247D  n=$30 ins 2 dur 12
        NOTE    C_4,2,12                    ; 02481  n=$30 ins 2 dur 12
        NOTE    A_5,2,12                    ; 02485  n=$45 ins 2 dur 12
        NOTE    C_4,2,12                    ; 02489  n=$30 ins 2 dur 12
        NOTE    C_4,2,12                    ; 0248D  n=$30 ins 2 dur 12
        NOTE    F_5,2,12                    ; 02491  n=$41 ins 2 dur 12
        NOTE    D_5,2,12                    ; 02495  n=$3E ins 2 dur 12
        NOTE    D_5,2,12                    ; 02499  n=$3E ins 2 dur 12
        NOTE    C_5,2,12                    ; 0249D  n=$3C ins 2 dur 12
        NOTE    E_5,2,12                    ; 024A1  n=$40 ins 2 dur 12
        NOTE    E_5,2,12                    ; 024A5  n=$40 ins 2 dur 12
        NOTE    A_5,2,48                    ; 024A9  n=$45 ins 2 dur 48
        ENDTRACK                            ; 024AD
Mus09_Ch3:
        VOLUME  25                          ; 024AE
        REST    24                          ; 024B0
        REST    24                          ; 024B4
        REST    24                          ; 024B8
        CALL    17,0                        ; 024BC  pattern, transpose
        CALL    17,-3                       ; 024BF  pattern, transpose
        NOTE    C_4,6,6                     ; 024C2  n=$30 ins 6 dur 6
        NOTE    E_4,6,6                     ; 024C6  n=$34 ins 6 dur 6
        NOTE    G_4,6,6                     ; 024CA  n=$37 ins 6 dur 6
        NOTE    As4,6,6                     ; 024CE  n=$3A ins 6 dur 6
        NOTE    C_5,6,6                     ; 024D2  n=$3C ins 6 dur 6
        NOTE    E_5,6,6                     ; 024D6  n=$40 ins 6 dur 6
        NOTE    G_5,6,6                     ; 024DA  n=$43 ins 6 dur 6
        NOTE    As5,6,6                     ; 024DE  n=$46 ins 6 dur 6
        NOTE    C_6,6,6                     ; 024E2  n=$48 ins 6 dur 6
        NOTE    E_6,6,6                     ; 024E6  n=$4C ins 6 dur 6
        NOTE    G_6,6,6                     ; 024EA  n=$4F ins 6 dur 6
        NOTE    As6,6,6                     ; 024EE  n=$52 ins 6 dur 6
        NOTE    C_7,6,6                     ; 024F2  n=$54 ins 6 dur 6
        VOLUME  200                         ; 024F6
        REST    12                          ; 024F8
        NOTE    F_6,4,12                    ; 024FC  n=$4D ins 4 dur 12
        NOTE    C_7,4,12                    ; 02500  n=$54 ins 4 dur 12
        NOTE    F_7,4,12                    ; 02504  n=$59 ins 4 dur 12
        NOTE    F_6,4,12                    ; 02508  n=$4D ins 4 dur 12
        NOTE    C_7,4,12                    ; 0250C  n=$54 ins 4 dur 12
        NOTE    F_7,4,12                    ; 02510  n=$59 ins 4 dur 12
        NOTE    F_6,4,12                    ; 02514  n=$4D ins 4 dur 12
        NOTE    C_7,4,12                    ; 02518  n=$54 ins 4 dur 12
        NOTE    F_7,4,12                    ; 0251C  n=$59 ins 4 dur 12
        NOTE    F_6,4,12                    ; 02520  n=$4D ins 4 dur 12
        NOTE    C_7,4,12                    ; 02524  n=$54 ins 4 dur 12
        NOTE    F_7,4,12                    ; 02528  n=$59 ins 4 dur 12
        NOTE    C_6,4,12                    ; 0252C  n=$48 ins 4 dur 12
        NOTE    C_7,4,12                    ; 02530  n=$54 ins 4 dur 12
        NOTE    C_7,4,12                    ; 02534  n=$54 ins 4 dur 12
        NOTE    C_6,4,12                    ; 02538  n=$48 ins 4 dur 12
        NOTE    C_7,4,12                    ; 0253C  n=$54 ins 4 dur 12
        NOTE    C_7,4,12                    ; 02540  n=$54 ins 4 dur 12
        NOTE    C_6,4,12                    ; 02544  n=$48 ins 4 dur 12
        NOTE    C_7,4,12                    ; 02548  n=$54 ins 4 dur 12
        NOTE    C_7,4,12                    ; 0254C  n=$54 ins 4 dur 12
        NOTE    C_6,4,12                    ; 02550  n=$48 ins 4 dur 12
        NOTE    C_7,4,12                    ; 02554  n=$54 ins 4 dur 12
        NOTE    C_7,4,12                    ; 02558  n=$54 ins 4 dur 12
        NOTE    F_6,4,12                    ; 0255C  n=$4D ins 4 dur 12
        NOTE    F_7,4,12                    ; 02560  n=$59 ins 4 dur 12
        NOTE    F_7,4,12                    ; 02564  n=$59 ins 4 dur 12
        NOTE    F_6,4,12                    ; 02568  n=$4D ins 4 dur 12
        NOTE    F_7,4,12                    ; 0256C  n=$59 ins 4 dur 12
        NOTE    F_7,4,12                    ; 02570  n=$59 ins 4 dur 12
        NOTE    F_6,4,12                    ; 02574  n=$4D ins 4 dur 12
        NOTE    F_7,4,12                    ; 02578  n=$59 ins 4 dur 12
        NOTE    F_7,4,12                    ; 0257C  n=$59 ins 4 dur 12
        NOTE    As6,4,12                    ; 02580  n=$52 ins 4 dur 12
        NOTE    As7,4,12                    ; 02584  n=$5E ins 4 dur 12
        NOTE    As7,4,12                    ; 02588  n=$5E ins 4 dur 12
        NOTE    C_6,4,12                    ; 0258C  n=$48 ins 4 dur 12
        NOTE    C_7,4,12                    ; 02590  n=$54 ins 4 dur 12
        NOTE    C_7,4,12                    ; 02594  n=$54 ins 4 dur 12
        NOTE    F_6,4,48                    ; 02598  n=$4D ins 4 dur 48
        ENDTRACK                            ; 0259C
Pat17:
        NOTE    G_4,6,6                     ; 0259D  n=$37 ins 6 dur 6
        NOTE    B_4,6,6                     ; 025A1  n=$3B ins 6 dur 6
        NOTE    G_4,6,6                     ; 025A5  n=$37 ins 6 dur 6
        NOTE    D_5,6,6                     ; 025A9  n=$3E ins 6 dur 6
        NOTE    B_4,6,6                     ; 025AD  n=$3B ins 6 dur 6
        NOTE    D_5,6,6                     ; 025B1  n=$3E ins 6 dur 6
        NOTE    G_5,6,6                     ; 025B5  n=$43 ins 6 dur 6
        NOTE    D_5,6,6                     ; 025B9  n=$3E ins 6 dur 6
        NOTE    G_5,6,6                     ; 025BD  n=$43 ins 6 dur 6
        NOTE    B_5,6,6                     ; 025C1  n=$47 ins 6 dur 6
        NOTE    G_5,6,6                     ; 025C5  n=$43 ins 6 dur 6
        NOTE    B_5,6,6                     ; 025C9  n=$47 ins 6 dur 6
        NOTE    D_6,6,6                     ; 025CD  n=$4A ins 6 dur 6
        NOTE    B_5,6,6                     ; 025D1  n=$47 ins 6 dur 6
        NOTE    D_6,6,6                     ; 025D5  n=$4A ins 6 dur 6
        NOTE    G_6,6,6                     ; 025D9  n=$4F ins 6 dur 6
        NOTE    D_6,6,6                     ; 025DD  n=$4A ins 6 dur 6
        NOTE    G_6,6,6                     ; 025E1  n=$4F ins 6 dur 6
        NOTE    B_6,6,6                     ; 025E5  n=$53 ins 6 dur 6
        NOTE    G_6,6,6                     ; 025E9  n=$4F ins 6 dur 6
        NOTE    B_6,6,6                     ; 025ED  n=$53 ins 6 dur 6
        NOTE    D_7,6,24                    ; 025F1  n=$56 ins 6 dur 24
        NOTE    Ds4,6,6                     ; 025F5  n=$33 ins 6 dur 6
        NOTE    G_4,6,6                     ; 025F9  n=$37 ins 6 dur 6
        NOTE    Ds4,6,6                     ; 025FD  n=$33 ins 6 dur 6
        NOTE    As4,6,6                     ; 02601  n=$3A ins 6 dur 6
        NOTE    G_4,6,6                     ; 02605  n=$37 ins 6 dur 6
        NOTE    As4,6,6                     ; 02609  n=$3A ins 6 dur 6
        NOTE    Ds5,6,6                     ; 0260D  n=$3F ins 6 dur 6
        NOTE    As4,6,6                     ; 02611  n=$3A ins 6 dur 6
        NOTE    Ds5,6,6                     ; 02615  n=$3F ins 6 dur 6
        NOTE    G_5,6,6                     ; 02619  n=$43 ins 6 dur 6
        NOTE    Ds5,6,6                     ; 0261D  n=$3F ins 6 dur 6
        NOTE    G_5,6,6                     ; 02621  n=$43 ins 6 dur 6
        NOTE    As5,6,6                     ; 02625  n=$46 ins 6 dur 6
        NOTE    G_5,6,6                     ; 02629  n=$43 ins 6 dur 6
        NOTE    As5,6,6                     ; 0262D  n=$46 ins 6 dur 6
        NOTE    Ds6,6,6                     ; 02631  n=$4B ins 6 dur 6
        NOTE    As5,6,6                     ; 02635  n=$46 ins 6 dur 6
        NOTE    Ds6,6,6                     ; 02639  n=$4B ins 6 dur 6
        NOTE    G_6,6,6                     ; 0263D  n=$4F ins 6 dur 6
        NOTE    Ds6,6,6                     ; 02641  n=$4B ins 6 dur 6
        NOTE    G_6,6,6                     ; 02645  n=$4F ins 6 dur 6
        NOTE    As6,6,24                    ; 02649  n=$52 ins 6 dur 24
        RETURN                              ; 0264D
Mus10_Ch0:
        VOLUME  50                          ; 0264E
        NOTE    D_6,6,6                     ; 02650  n=$4A ins 6 dur 6
        NOTE    G_6,6,6                     ; 02654  n=$4F ins 6 dur 6
        NOTE    B_6,6,60                    ; 02658  n=$53 ins 6 dur 60
        NOTE    G_6,6,12                    ; 0265C  n=$4F ins 6 dur 12
        NOTE    B_6,6,12                    ; 02660  n=$53 ins 6 dur 12
        NOTE    D_7,6,12                    ; 02664  n=$56 ins 6 dur 12
        NOTE    A_6,6,24                    ; 02668  n=$51 ins 6 dur 24
        NOTE    Fs6,6,24                    ; 0266C  n=$4E ins 6 dur 24
        NOTE    C_6,6,6                     ; 02670  n=$48 ins 6 dur 6
        NOTE    Ds6,6,6                     ; 02674  n=$4B ins 6 dur 6
        NOTE    Fs6,6,6                     ; 02678  n=$4E ins 6 dur 6
        NOTE    A_6,6,6                     ; 0267C  n=$51 ins 6 dur 6
        NOTE    Fs6,6,6                     ; 02680  n=$4E ins 6 dur 6
        NOTE    A_6,6,6                     ; 02684  n=$51 ins 6 dur 6
        NOTE    C_7,6,6                     ; 02688  n=$54 ins 6 dur 6
        NOTE    Ds7,6,6                     ; 0268C  n=$57 ins 6 dur 6
        NOTE    A_6,6,6                     ; 02690  n=$51 ins 6 dur 6
        NOTE    C_7,6,6                     ; 02694  n=$54 ins 6 dur 6
        NOTE    Ds7,6,6                     ; 02698  n=$57 ins 6 dur 6
        NOTE    Fs7,6,6                     ; 0269C  n=$5A ins 6 dur 6
        NOTE    C_7,6,6                     ; 026A0  n=$54 ins 6 dur 6
        NOTE    Ds7,6,6                     ; 026A4  n=$57 ins 6 dur 6
        NOTE    Fs7,6,6                     ; 026A8  n=$5A ins 6 dur 6
        NOTE    A_7,6,54                    ; 026AC  n=$5D ins 6 dur 54
        ENDTRACK                            ; 026B0
Mus10_Ch1:
        VOLUME  50                          ; 026B1
        REST    12                          ; 026B3
        NOTE    G_6,6,60                    ; 026B7  n=$4F ins 6 dur 60
        NOTE    D_6,6,12                    ; 026BB  n=$4A ins 6 dur 12
        NOTE    G_6,6,12                    ; 026BF  n=$4F ins 6 dur 12
        NOTE    B_6,6,12                    ; 026C3  n=$53 ins 6 dur 12
        NOTE    Fs6,6,24                    ; 026C7  n=$4E ins 6 dur 24
        NOTE    Ds6,6,24                    ; 026CB  n=$4B ins 6 dur 24
        NOTE    A_5,6,6                     ; 026CF  n=$45 ins 6 dur 6
        NOTE    C_6,6,6                     ; 026D3  n=$48 ins 6 dur 6
        NOTE    Ds6,6,6                     ; 026D7  n=$4B ins 6 dur 6
        NOTE    Fs6,6,6                     ; 026DB  n=$4E ins 6 dur 6
        NOTE    Ds6,6,6                     ; 026DF  n=$4B ins 6 dur 6
        NOTE    Fs6,6,6                     ; 026E3  n=$4E ins 6 dur 6
        NOTE    A_6,6,6                     ; 026E7  n=$51 ins 6 dur 6
        NOTE    C_7,6,6                     ; 026EB  n=$54 ins 6 dur 6
        NOTE    Fs6,6,6                     ; 026EF  n=$4E ins 6 dur 6
        NOTE    A_6,6,6                     ; 026F3  n=$51 ins 6 dur 6
        NOTE    C_7,6,6                     ; 026F7  n=$54 ins 6 dur 6
        NOTE    Ds7,6,6                     ; 026FB  n=$57 ins 6 dur 6
        NOTE    A_6,6,6                     ; 026FF  n=$51 ins 6 dur 6
        NOTE    C_7,6,6                     ; 02703  n=$54 ins 6 dur 6
        NOTE    Ds7,6,6                     ; 02707  n=$57 ins 6 dur 6
        NOTE    Fs7,6,54                    ; 0270B  n=$5A ins 6 dur 54
        ENDTRACK                            ; 0270F
Mus10_Ch2:
        VOLUME  128                         ; 02710
        REST    12                          ; 02712
        NOTE    G_6,5,72                    ; 02716  n=$4F ins 5 dur 72
        NOTE    B_6,5,24                    ; 0271A  n=$53 ins 5 dur 24
        NOTE    D_7,5,12                    ; 0271E  n=$56 ins 5 dur 12
        NOTE    Fs7,5,12                    ; 02722  n=$5A ins 5 dur 12
        NOTE    Fs7,5,24                    ; 02726  n=$5A ins 5 dur 24
        NOTE    Ds7,5,24                    ; 0272A  n=$57 ins 5 dur 24
        NOTE    C_7,5,24                    ; 0272E  n=$54 ins 5 dur 24
        NOTE    A_6,5,24                    ; 02732  n=$51 ins 5 dur 24
        NOTE    Fs6,5,24                    ; 02736  n=$4E ins 5 dur 24
        NOTE    Ds6,5,48                    ; 0273A  n=$4B ins 5 dur 48
        ENDTRACK                            ; 0273E
Mus10_Ch3:
        ENDTRACK                            ; 0273F
Mus11_Ch0:
        VOLUME  100                         ; 02740
        NOTE    D_6,2,6                     ; 02742  n=$4A ins 2 dur 6
        NOTE    A_5,2,6                     ; 02746  n=$45 ins 2 dur 6
        NOTE    D_6,2,6                     ; 0274A  n=$4A ins 2 dur 6
        NOTE    Fs6,2,6                     ; 0274E  n=$4E ins 2 dur 6
        NOTE    D_6,2,6                     ; 02752  n=$4A ins 2 dur 6
        NOTE    Fs6,2,6                     ; 02756  n=$4E ins 2 dur 6
        NOTE    E_6,2,6                     ; 0275A  n=$4C ins 2 dur 6
        NOTE    B_5,2,6                     ; 0275E  n=$47 ins 2 dur 6
        NOTE    E_6,2,6                     ; 02762  n=$4C ins 2 dur 6
        NOTE    G_6,2,6                     ; 02766  n=$4F ins 2 dur 6
        NOTE    E_6,2,6                     ; 0276A  n=$4C ins 2 dur 6
        NOTE    G_6,2,6                     ; 0276E  n=$4F ins 2 dur 6
        NOTE    Fs6,2,6                     ; 02772  n=$4E ins 2 dur 6
        NOTE    D_6,2,6                     ; 02776  n=$4A ins 2 dur 6
        NOTE    Fs6,2,6                     ; 0277A  n=$4E ins 2 dur 6
        NOTE    A_6,2,6                     ; 0277E  n=$51 ins 2 dur 6
        NOTE    Fs6,2,6                     ; 02782  n=$4E ins 2 dur 6
        NOTE    A_6,2,6                     ; 02786  n=$51 ins 2 dur 6
        NOTE    G_6,2,6                     ; 0278A  n=$4F ins 2 dur 6
        NOTE    E_6,2,6                     ; 0278E  n=$4C ins 2 dur 6
        NOTE    G_6,2,6                     ; 02792  n=$4F ins 2 dur 6
        NOTE    B_6,2,6                     ; 02796  n=$53 ins 2 dur 6
        NOTE    G_6,2,6                     ; 0279A  n=$4F ins 2 dur 6
        NOTE    B_6,2,6                     ; 0279E  n=$53 ins 2 dur 6
        NOTE    A_5,2,6                     ; 027A2  n=$45 ins 2 dur 6
        NOTE    Cs6,2,6                     ; 027A6  n=$49 ins 2 dur 6
        NOTE    E_6,2,6                     ; 027AA  n=$4C ins 2 dur 6
        NOTE    A_6,2,18                    ; 027AE  n=$51 ins 2 dur 18
        REST    18                          ; 027B2
        NOTE    Cs7,2,18                    ; 027B6  n=$55 ins 2 dur 18
        NOTE    D_7,2,72                    ; 027BA  n=$56 ins 2 dur 72
        ENDTRACK                            ; 027BE
Mus11_Ch1:
        VOLUME  100                         ; 027BF
        NOTE    D_5,3,18                    ; 027C1  n=$3E ins 3 dur 18
        NOTE    D_6,3,18                    ; 027C5  n=$4A ins 3 dur 18
        NOTE    E_5,3,18                    ; 027C9  n=$40 ins 3 dur 18
        NOTE    E_6,3,18                    ; 027CD  n=$4C ins 3 dur 18
        NOTE    Fs5,3,18                    ; 027D1  n=$42 ins 3 dur 18
        NOTE    Fs6,3,18                    ; 027D5  n=$4E ins 3 dur 18
        NOTE    G_5,3,18                    ; 027D9  n=$43 ins 3 dur 18
        NOTE    G_6,3,18                    ; 027DD  n=$4F ins 3 dur 18
        NOTE    A_5,3,36                    ; 027E1  n=$45 ins 3 dur 36
        NOTE    A_5,3,36                    ; 027E5  n=$45 ins 3 dur 36
        NOTE    D_5,3,72                    ; 027E9  n=$3E ins 3 dur 72
        ENDTRACK                            ; 027ED
Mus11_Ch2:
        VOLUME  60                          ; 027EE
        REST    18                          ; 027F0
        NOTE    Fs6,3,18                    ; 027F4  n=$4E ins 3 dur 18
        VOLUME  0                           ; 027F8
        REST    18                          ; 027FA
        VOLUME  100                         ; 027FE
        NOTE    G_6,3,18                    ; 02800  n=$4F ins 3 dur 18
        VOLUME  0                           ; 02804
        REST    18                          ; 02806
        VOLUME  100                         ; 0280A
        NOTE    A_6,3,18                    ; 0280C  n=$51 ins 3 dur 18
        VOLUME  0                           ; 02810
        REST    18                          ; 02812
        VOLUME  100                         ; 02816
        NOTE    B_6,3,18                    ; 02818  n=$53 ins 3 dur 18
        NOTE    E_6,3,6                     ; 0281C  n=$4C ins 3 dur 6
        NOTE    A_6,3,6                     ; 02820  n=$51 ins 3 dur 6
        NOTE    Cs7,3,6                     ; 02824  n=$55 ins 3 dur 6
        NOTE    Cs7,3,18                    ; 02828  n=$55 ins 3 dur 18
        REST    18                          ; 0282C
        NOTE    G_6,3,18                    ; 02830  n=$4F ins 3 dur 18
        NOTE    Fs6,3,72                    ; 02834  n=$4E ins 3 dur 72
        ENDTRACK                            ; 02838
Mus11_Ch3:
        VOLUME  100                         ; 02839
        NOTE    D_6,3,6                     ; 0283B  n=$4A ins 3 dur 6
        NOTE    Fs6,3,6                     ; 0283F  n=$4E ins 3 dur 6
        NOTE    A_6,3,6                     ; 02843  n=$51 ins 3 dur 6
        NOTE    D_7,3,6                     ; 02847  n=$56 ins 3 dur 6
        NOTE    A_6,3,6                     ; 0284B  n=$51 ins 3 dur 6
        NOTE    Fs6,3,6                     ; 0284F  n=$4E ins 3 dur 6
        NOTE    E_6,3,6                     ; 02853  n=$4C ins 3 dur 6
        NOTE    G_6,3,6                     ; 02857  n=$4F ins 3 dur 6
        NOTE    B_6,3,6                     ; 0285B  n=$53 ins 3 dur 6
        NOTE    E_7,3,6                     ; 0285F  n=$58 ins 3 dur 6
        NOTE    B_6,3,6                     ; 02863  n=$53 ins 3 dur 6
        NOTE    G_6,3,6                     ; 02867  n=$4F ins 3 dur 6
        NOTE    Fs6,3,6                     ; 0286B  n=$4E ins 3 dur 6
        NOTE    A_6,3,6                     ; 0286F  n=$51 ins 3 dur 6
        NOTE    D_7,3,6                     ; 02873  n=$56 ins 3 dur 6
        NOTE    Fs7,3,6                     ; 02877  n=$5A ins 3 dur 6
        NOTE    D_7,3,6                     ; 0287B  n=$56 ins 3 dur 6
        NOTE    A_6,3,6                     ; 0287F  n=$51 ins 3 dur 6
        NOTE    G_6,3,6                     ; 02883  n=$4F ins 3 dur 6
        NOTE    B_6,3,6                     ; 02887  n=$53 ins 3 dur 6
        NOTE    E_7,3,6                     ; 0288B  n=$58 ins 3 dur 6
        NOTE    G_7,3,6                     ; 0288F  n=$5B ins 3 dur 6
        NOTE    E_7,3,6                     ; 02893  n=$58 ins 3 dur 6
        NOTE    B_6,3,6                     ; 02897  n=$53 ins 3 dur 6
        NOTE    A_6,3,6                     ; 0289B  n=$51 ins 3 dur 6
        NOTE    Cs7,3,6                     ; 0289F  n=$55 ins 3 dur 6
        NOTE    E_7,3,6                     ; 028A3  n=$58 ins 3 dur 6
        REST    18                          ; 028A7
        NOTE    G_7,3,6                     ; 028AB  n=$5B ins 3 dur 6
        NOTE    E_7,3,6                     ; 028AF  n=$58 ins 3 dur 6
        NOTE    Cs7,3,6                     ; 028B3  n=$55 ins 3 dur 6
        NOTE    A_6,3,18                    ; 028B7  n=$51 ins 3 dur 18
        NOTE    A_6,3,72                    ; 028BB  n=$51 ins 3 dur 72
        ENDTRACK                            ; 028BF
Mus12_Ch0:
        VOLUME  64                          ; 028C0
        NOTE    Fs6,8,32                    ; 028C2  n=$4E ins 8 dur 32
        NOTE    C_7,8,32                    ; 028C6  n=$54 ins 8 dur 32
        NOTE    Cs7,8,48                    ; 028CA  n=$55 ins 8 dur 48
        NOTE    G_6,8,16                    ; 028CE  n=$4F ins 8 dur 16
        NOTE    Fs6,8,16                    ; 028D2  n=$4E ins 8 dur 16
        NOTE    C_7,8,16                    ; 028D6  n=$54 ins 8 dur 16
        NOTE    Cs7,8,16                    ; 028DA  n=$55 ins 8 dur 16
        NOTE    G_6,8,16                    ; 028DE  n=$4F ins 8 dur 16
        NOTE    Fs6,8,16                    ; 028E2  n=$4E ins 8 dur 16
        NOTE    C_7,8,16                    ; 028E6  n=$54 ins 8 dur 16
        NOTE    Cs7,8,16                    ; 028EA  n=$55 ins 8 dur 16
        NOTE    G_6,8,16                    ; 028EE  n=$4F ins 8 dur 16
        NOTE    B_6,8,32                    ; 028F2  n=$53 ins 8 dur 32
        NOTE    F_7,8,32                    ; 028F6  n=$59 ins 8 dur 32
        NOTE    Fs7,8,48                    ; 028FA  n=$5A ins 8 dur 48
        NOTE    C_7,8,16                    ; 028FE  n=$54 ins 8 dur 16
        NOTE    B_6,8,16                    ; 02902  n=$53 ins 8 dur 16
        NOTE    F_7,8,16                    ; 02906  n=$59 ins 8 dur 16
        NOTE    Fs7,8,16                    ; 0290A  n=$5A ins 8 dur 16
        NOTE    C_7,8,16                    ; 0290E  n=$54 ins 8 dur 16
        NOTE    B_6,8,16                    ; 02912  n=$53 ins 8 dur 16
        NOTE    F_7,8,16                    ; 02916  n=$59 ins 8 dur 16
        NOTE    Fs7,8,16                    ; 0291A  n=$5A ins 8 dur 16
        NOTE    C_7,8,16                    ; 0291E  n=$54 ins 8 dur 16
        NOTE    E_7,8,48                    ; 02922  n=$58 ins 8 dur 48
        NOTE    A_6,8,16                    ; 02926  n=$51 ins 8 dur 16
        NOTE    A_6,8,16                    ; 0292A  n=$51 ins 8 dur 16
        NOTE    B_6,8,16                    ; 0292E  n=$53 ins 8 dur 16
        NOTE    E_7,8,16                    ; 02932  n=$58 ins 8 dur 16
        NOTE    Ds7,8,16                    ; 02936  n=$57 ins 8 dur 16
        NOTE    D_7,8,48                    ; 0293A  n=$56 ins 8 dur 48
        NOTE    C_7,8,16                    ; 0293E  n=$54 ins 8 dur 16
        NOTE    Cs7,8,32                    ; 02942  n=$55 ins 8 dur 32
        NOTE    F_6,8,32                    ; 02946  n=$4D ins 8 dur 32
        JUMP    Mus12_Ch0                   ; 0294A
        ENDTRACK                            ; 0294D  unreachable: follows a JUMP
Mus12_Ch1:
        VOLUME  60                          ; 0294E
        CALL    19,-12                      ; 02950  pattern, transpose
        CALL    19,-12                      ; 02953  pattern, transpose
        CALL    19,-16                      ; 02956  pattern, transpose
        CALL    19,-16                      ; 02959  pattern, transpose
        CALL    19,-14                      ; 0295C  pattern, transpose
        NOTE    E_5,6,8                     ; 0295F  n=$40 ins 6 dur 8
        NOTE    E_5,6,8                     ; 02963  n=$40 ins 6 dur 8
        NOTE    E_5,6,8                     ; 02967  n=$40 ins 6 dur 8
        NOTE    E_5,6,8                     ; 0296B  n=$40 ins 6 dur 8
        NOTE    E_5,6,8                     ; 0296F  n=$40 ins 6 dur 8
        NOTE    E_5,6,8                     ; 02973  n=$40 ins 6 dur 8
        NOTE    E_5,6,8                     ; 02977  n=$40 ins 6 dur 8
        NOTE    E_5,6,8                     ; 0297B  n=$40 ins 6 dur 8
        NOTE    E_5,6,8                     ; 0297F  n=$40 ins 6 dur 8
        NOTE    E_5,6,8                     ; 02983  n=$40 ins 6 dur 8
        NOTE    E_5,6,8                     ; 02987  n=$40 ins 6 dur 8
        NOTE    E_5,6,8                     ; 0298B  n=$40 ins 6 dur 8
        NOTE    F_5,6,8                     ; 0298F  n=$41 ins 6 dur 8
        NOTE    F_5,6,8                     ; 02993  n=$41 ins 6 dur 8
        NOTE    F_5,6,8                     ; 02997  n=$41 ins 6 dur 8
        NOTE    F_5,6,8                     ; 0299B  n=$41 ins 6 dur 8
        JUMP    Mus12_Ch1                   ; 0299F
        ENDTRACK                            ; 029A2  unreachable: follows a JUMP
Pat19:
        NOTE    Fs6,6,8                     ; 029A3  n=$4E ins 6 dur 8
        NOTE    Fs6,6,8                     ; 029A7  n=$4E ins 6 dur 8
        NOTE    Fs6,6,8                     ; 029AB  n=$4E ins 6 dur 8
        NOTE    Fs6,6,8                     ; 029AF  n=$4E ins 6 dur 8
        NOTE    Fs6,6,8                     ; 029B3  n=$4E ins 6 dur 8
        NOTE    Fs6,6,8                     ; 029B7  n=$4E ins 6 dur 8
        NOTE    Fs6,6,8                     ; 029BB  n=$4E ins 6 dur 8
        NOTE    Fs6,6,8                     ; 029BF  n=$4E ins 6 dur 8
        NOTE    Fs6,6,8                     ; 029C3  n=$4E ins 6 dur 8
        NOTE    Fs6,6,8                     ; 029C7  n=$4E ins 6 dur 8
        NOTE    Fs6,6,8                     ; 029CB  n=$4E ins 6 dur 8
        NOTE    Fs6,6,8                     ; 029CF  n=$4E ins 6 dur 8
        NOTE    Fs6,6,8                     ; 029D3  n=$4E ins 6 dur 8
        NOTE    Fs6,6,8                     ; 029D7  n=$4E ins 6 dur 8
        NOTE    Fs6,6,8                     ; 029DB  n=$4E ins 6 dur 8
        NOTE    Fs6,6,8                     ; 029DF  n=$4E ins 6 dur 8
        RETURN                              ; 029E3
Mus12_Ch2:
        VOLUME  200                         ; 029E4
        NOTE    Fs6,5,128                   ; 029E6  n=$4E ins 5 dur 128
        NOTE    Fs6,5,128                   ; 029EA  n=$4E ins 5 dur 128
        NOTE    D_6,5,128                   ; 029EE  n=$4A ins 5 dur 128
        NOTE    D_6,5,128                   ; 029F2  n=$4A ins 5 dur 128
        NOTE    E_6,5,128                   ; 029F6  n=$4C ins 5 dur 128
        NOTE    E_6,5,96                    ; 029FA  n=$4C ins 5 dur 96
        NOTE    F_6,5,32                    ; 029FE  n=$4D ins 5 dur 32
        JUMP    Mus12_Ch2                   ; 02A02
        ENDTRACK                            ; 02A05  unreachable: follows a JUMP
Mus12_Ch3:
        VOLUME  255                         ; 02A06
        ENDTRACK                            ; 02A08
Mus13_Ch0:
        VOLUME  128                         ; 02A09
        NOTE    A_6,8,64                    ; 02A0B  n=$51 ins 8 dur 64
        NOTE    Gs6,8,40                    ; 02A0F  n=$50 ins 8 dur 40
        NOTE    G_6,8,8                     ; 02A13  n=$4F ins 8 dur 8
        NOTE    Fs6,8,8                     ; 02A17  n=$4E ins 8 dur 8
        NOTE    F_6,8,8                     ; 02A1B  n=$4D ins 8 dur 8
        NOTE    F_6,8,64                    ; 02A1F  n=$4D ins 8 dur 64
        NOTE    E_6,8,16                    ; 02A23  n=$4C ins 8 dur 16
        NOTE    G_6,8,24                    ; 02A27  n=$4F ins 8 dur 24
        NOTE    Gs6,8,24                    ; 02A2B  n=$50 ins 8 dur 24
        NOTE    A_6,8,64                    ; 02A2F  n=$51 ins 8 dur 64
        NOTE    Gs6,8,40                    ; 02A33  n=$50 ins 8 dur 40
        NOTE    G_6,8,8                     ; 02A37  n=$4F ins 8 dur 8
        NOTE    Fs6,8,8                     ; 02A3B  n=$4E ins 8 dur 8
        NOTE    F_6,8,8                     ; 02A3F  n=$4D ins 8 dur 8
        NOTE    F_6,8,64                    ; 02A43  n=$4D ins 8 dur 64
        NOTE    E_6,8,16                    ; 02A47  n=$4C ins 8 dur 16
        NOTE    A_6,8,24                    ; 02A4B  n=$51 ins 8 dur 24
        NOTE    B_6,8,24                    ; 02A4F  n=$53 ins 8 dur 24
        NOTE    C_7,8,64                    ; 02A53  n=$54 ins 8 dur 64
        NOTE    B_6,8,40                    ; 02A57  n=$53 ins 8 dur 40
        NOTE    As6,8,8                     ; 02A5B  n=$52 ins 8 dur 8
        NOTE    A_6,8,8                     ; 02A5F  n=$51 ins 8 dur 8
        NOTE    Gs6,8,8                     ; 02A63  n=$50 ins 8 dur 8
        NOTE    F_6,8,64                    ; 02A67  n=$4D ins 8 dur 64
        NOTE    E_6,8,64                    ; 02A6B  n=$4C ins 8 dur 64
        JUMP    Mus13_Ch0                   ; 02A6F
        ENDTRACK                            ; 02A72  unreachable: follows a JUMP
Mus13_Ch1:
        VOLUME  64                          ; 02A73
        CALLN   20,-12,3                    ; 02A75  pattern, transpose, plays 4x
        CALLN   20,-7,3                     ; 02A79  pattern, transpose, plays 4x
        CALLN   20,-12,3                    ; 02A7D  pattern, transpose, plays 4x
        JUMP    Mus13_Ch1                   ; 02A81
        ENDTRACK                            ; 02A84  unreachable: follows a JUMP
Pat20:
        NOTE    A_6,6,8                     ; 02A85  n=$51 ins 6 dur 8
        NOTE    A_6,6,8                     ; 02A89  n=$51 ins 6 dur 8
        NOTE    A_6,6,8                     ; 02A8D  n=$51 ins 6 dur 8
        NOTE    C_7,6,8                     ; 02A91  n=$54 ins 6 dur 8
        NOTE    A_6,6,8                     ; 02A95  n=$51 ins 6 dur 8
        NOTE    A_6,6,8                     ; 02A99  n=$51 ins 6 dur 8
        NOTE    A_6,6,8                     ; 02A9D  n=$51 ins 6 dur 8
        NOTE    C_7,6,8                     ; 02AA1  n=$54 ins 6 dur 8
        RETURN                              ; 02AA5
Mus13_Ch2:
        VOLUME  255                         ; 02AA6
        NOTE    A_6,5,128                   ; 02AA8  n=$51 ins 5 dur 128
        NOTE    A_6,5,128                   ; 02AAC  n=$51 ins 5 dur 128
        NOTE    D_6,5,128                   ; 02AB0  n=$4A ins 5 dur 128
        NOTE    D_6,5,128                   ; 02AB4  n=$4A ins 5 dur 128
        NOTE    A_6,5,128                   ; 02AB8  n=$51 ins 5 dur 128
        NOTE    A_6,5,128                   ; 02ABC  n=$51 ins 5 dur 128
        JUMP    Mus13_Ch2                   ; 02AC0
        ENDTRACK                            ; 02AC3  unreachable: follows a JUMP
Mus13_Ch3:
        VOLUME  255                         ; 02AC4
        ENDTRACK                            ; 02AC6
Mus14_Ch0:
        VOLUME  100                         ; 02AC7
        NOTE    E_4,6,6                     ; 02AC9  n=$34 ins 6 dur 6
        NOTE    A_4,6,6                     ; 02ACD  n=$39 ins 6 dur 6
        NOTE    C_5,6,6                     ; 02AD1  n=$3C ins 6 dur 6
        NOTE    A_4,6,6                     ; 02AD5  n=$39 ins 6 dur 6
        NOTE    C_5,6,6                     ; 02AD9  n=$3C ins 6 dur 6
        NOTE    E_5,6,6                     ; 02ADD  n=$40 ins 6 dur 6
        NOTE    C_5,6,6                     ; 02AE1  n=$3C ins 6 dur 6
        NOTE    E_5,6,6                     ; 02AE5  n=$40 ins 6 dur 6
        NOTE    A_5,6,6                     ; 02AE9  n=$45 ins 6 dur 6
        NOTE    E_5,6,6                     ; 02AED  n=$40 ins 6 dur 6
        NOTE    A_5,6,6                     ; 02AF1  n=$45 ins 6 dur 6
        NOTE    C_6,6,6                     ; 02AF5  n=$48 ins 6 dur 6
        NOTE    A_5,6,6                     ; 02AF9  n=$45 ins 6 dur 6
        NOTE    C_6,6,6                     ; 02AFD  n=$48 ins 6 dur 6
        NOTE    E_6,6,6                     ; 02B01  n=$4C ins 6 dur 6
        NOTE    C_6,6,6                     ; 02B05  n=$48 ins 6 dur 6
        NOTE    E_6,6,6                     ; 02B09  n=$4C ins 6 dur 6
        NOTE    A_6,6,6                     ; 02B0D  n=$51 ins 6 dur 6
        NOTE    Gs6,6,6                     ; 02B11  n=$50 ins 6 dur 6
        NOTE    B_6,6,6                     ; 02B15  n=$53 ins 6 dur 6
        NOTE    D_7,6,6                     ; 02B19  n=$56 ins 6 dur 6
        NOTE    E_7,6,96                    ; 02B1D  n=$58 ins 6 dur 96
        ENDTRACK                            ; 02B21
Mus14_Ch1:
        VOLUME  80                          ; 02B22
        REST    18                          ; 02B24
        NOTE    E_4,6,6                     ; 02B28  n=$34 ins 6 dur 6
        NOTE    A_4,6,6                     ; 02B2C  n=$39 ins 6 dur 6
        NOTE    C_5,6,6                     ; 02B30  n=$3C ins 6 dur 6
        NOTE    A_4,6,6                     ; 02B34  n=$39 ins 6 dur 6
        NOTE    C_5,6,6                     ; 02B38  n=$3C ins 6 dur 6
        NOTE    E_5,6,6                     ; 02B3C  n=$40 ins 6 dur 6
        NOTE    C_5,6,6                     ; 02B40  n=$3C ins 6 dur 6
        NOTE    E_5,6,6                     ; 02B44  n=$40 ins 6 dur 6
        NOTE    A_5,6,6                     ; 02B48  n=$45 ins 6 dur 6
        NOTE    E_5,6,6                     ; 02B4C  n=$40 ins 6 dur 6
        NOTE    A_5,6,6                     ; 02B50  n=$45 ins 6 dur 6
        NOTE    C_6,6,6                     ; 02B54  n=$48 ins 6 dur 6
        NOTE    A_5,6,6                     ; 02B58  n=$45 ins 6 dur 6
        NOTE    C_6,6,6                     ; 02B5C  n=$48 ins 6 dur 6
        NOTE    E_6,6,6                     ; 02B60  n=$4C ins 6 dur 6
        NOTE    E_6,6,6                     ; 02B64  n=$4C ins 6 dur 6
        NOTE    Gs6,6,6                     ; 02B68  n=$50 ins 6 dur 6
        NOTE    B_6,6,6                     ; 02B6C  n=$53 ins 6 dur 6
        NOTE    B_6,6,96                    ; 02B70  n=$53 ins 6 dur 96
        ENDTRACK                            ; 02B74
Mus14_Ch2:
        VOLUME  70                          ; 02B75
        REST    36                          ; 02B77
        NOTE    E_4,6,6                     ; 02B7B  n=$34 ins 6 dur 6
        NOTE    A_4,6,6                     ; 02B7F  n=$39 ins 6 dur 6
        NOTE    C_5,6,6                     ; 02B83  n=$3C ins 6 dur 6
        NOTE    A_4,6,6                     ; 02B87  n=$39 ins 6 dur 6
        NOTE    C_5,6,6                     ; 02B8B  n=$3C ins 6 dur 6
        NOTE    E_5,6,6                     ; 02B8F  n=$40 ins 6 dur 6
        NOTE    C_5,6,6                     ; 02B93  n=$3C ins 6 dur 6
        NOTE    E_5,6,6                     ; 02B97  n=$40 ins 6 dur 6
        NOTE    A_5,6,6                     ; 02B9B  n=$45 ins 6 dur 6
        NOTE    E_5,6,6                     ; 02B9F  n=$40 ins 6 dur 6
        NOTE    A_5,6,6                     ; 02BA3  n=$45 ins 6 dur 6
        NOTE    C_6,6,6                     ; 02BA7  n=$48 ins 6 dur 6
        NOTE    C_6,6,6                     ; 02BAB  n=$48 ins 6 dur 6
        NOTE    E_6,6,6                     ; 02BAF  n=$4C ins 6 dur 6
        NOTE    Gs6,6,6                     ; 02BB3  n=$50 ins 6 dur 6
        VOLUME  180                         ; 02BB7
        NOTE    E_6,5,96                    ; 02BB9  n=$4C ins 5 dur 96
        ENDTRACK                            ; 02BBD
Mus14_Ch3:
        VOLUME  100                         ; 02BBE
        REST    54                          ; 02BC0
        NOTE    E_4,6,6                     ; 02BC4  n=$34 ins 6 dur 6
        NOTE    A_4,6,6                     ; 02BC8  n=$39 ins 6 dur 6
        NOTE    C_5,6,6                     ; 02BCC  n=$3C ins 6 dur 6
        NOTE    A_4,6,6                     ; 02BD0  n=$39 ins 6 dur 6
        NOTE    C_5,6,6                     ; 02BD4  n=$3C ins 6 dur 6
        NOTE    E_5,6,6                     ; 02BD8  n=$40 ins 6 dur 6
        NOTE    C_5,6,6                     ; 02BDC  n=$3C ins 6 dur 6
        NOTE    E_5,6,6                     ; 02BE0  n=$40 ins 6 dur 6
        NOTE    A_5,6,6                     ; 02BE4  n=$45 ins 6 dur 6
        NOTE    Gs5,6,6                     ; 02BE8  n=$44 ins 6 dur 6
        NOTE    B_5,6,6                     ; 02BEC  n=$47 ins 6 dur 6
        NOTE    D_6,6,5                     ; 02BF0  n=$4A ins 6 dur 5
        NOTE    Gs6,6,96                    ; 02BF4  n=$50 ins 6 dur 96
        ENDTRACK                            ; 02BF8
Sfx00_Ch3:
        ENDTRACK                            ; 02BF9
Sfx01_Ch3:
        VOLUME  255                         ; 02BFA
        NOTE    A_5,9,96                    ; 02BFC  n=$45 ins 9 dur 96
        ENDTRACK                            ; 02C00
Sfx02_Ch3:
        VOLUME  255                         ; 02C01
        NOTE    A_5,10,10                   ; 02C03  n=$45 ins 10 dur 10
        NOTE    A_5,10,12                   ; 02C07  n=$45 ins 10 dur 12
        NOTE    A_5,10,24                   ; 02C0B  n=$45 ins 10 dur 24
        ENDTRACK                            ; 02C0F
Sfx03_Ch3:
        VOLUME  255                         ; 02C10
        NOTE    A_5,11,96                   ; 02C12  n=$45 ins 11 dur 96
        ENDTRACK                            ; 02C16
Sfx04_Ch3:
        VOLUME  255                         ; 02C17
        NOTE    A_5,12,96                   ; 02C19  n=$45 ins 12 dur 96
        ENDTRACK                            ; 02C1D
Sfx05_Ch3:
        VOLUME  255                         ; 02C1E
        NOTE    A_5,13,96                   ; 02C20  n=$45 ins 13 dur 96
        ENDTRACK                            ; 02C24
Sfx06_Ch3:
        VOLUME  255                         ; 02C25
        NOTE    A_5,14,96                   ; 02C27  n=$45 ins 14 dur 96
        ENDTRACK                            ; 02C2B
Sfx07_Ch3:
        VOLUME  255                         ; 02C2C
        NOTE    A_5,15,96                   ; 02C2E  n=$45 ins 15 dur 96
        ENDTRACK                            ; 02C32
Sfx08_Ch3:
        VOLUME  255                         ; 02C33
        NOTE    A_5,16,96                   ; 02C35  n=$45 ins 16 dur 96
        ENDTRACK                            ; 02C39
Sfx09_Ch3:
        VOLUME  255                         ; 02C3A
        NOTE    A_5,17,96                   ; 02C3C  n=$45 ins 17 dur 96
        ENDTRACK                            ; 02C40
Sfx10_Ch3:
        VOLUME  255                         ; 02C41
        NOTE    A_5,18,96                   ; 02C43  n=$45 ins 18 dur 96
        ENDTRACK                            ; 02C47
Sfx11_Ch3:
        VOLUME  255                         ; 02C48
        NOTE    A_5,19,96                   ; 02C4A  n=$45 ins 19 dur 96
        ENDTRACK                            ; 02C4E
Sfx12_Ch3:
        VOLUME  255                         ; 02C4F
        NOTE    A_5,20,96                   ; 02C51  n=$45 ins 20 dur 96
        ENDTRACK                            ; 02C55
Sfx13_Ch3:
        VOLUME  255                         ; 02C56
        NOTE    A_5,21,96                   ; 02C58  n=$45 ins 21 dur 96
        ENDTRACK                            ; 02C5C
Sfx14_Ch3:
        VOLUME  255                         ; 02C5D
        NOTE    A_5,22,96                   ; 02C5F  n=$45 ins 22 dur 96
        ENDTRACK                            ; 02C63
Sfx15_Ch3:
        VOLUME  255                         ; 02C64
        NOTE    As5,23,96                   ; 02C66  n=$46 ins 23 dur 96
        ENDTRACK                            ; 02C6A
Sfx16_Ch3:
        VOLUME  255                         ; 02C6B
        NOTE    A_5,24,96                   ; 02C6D  n=$45 ins 24 dur 96
        ENDTRACK                            ; 02C71
Sfx17_Ch3:
        VOLUME  255                         ; 02C72
        NOTE    A_5,25,96                   ; 02C74  n=$45 ins 25 dur 96
        ENDTRACK                            ; 02C78
Sfx18_Ch3:
        VOLUME  255                         ; 02C79
        NOTE    A_5,26,96                   ; 02C7B  n=$45 ins 26 dur 96
        ENDTRACK                            ; 02C7F
Sfx19_Ch3:
        VOLUME  255                         ; 02C80
        NOTE    A_5,27,96                   ; 02C82  n=$45 ins 27 dur 96
        ENDTRACK                            ; 02C86
Sfx20_Ch3:
        VOLUME  255                         ; 02C87
        NOTE    A_5,28,96                   ; 02C89  n=$45 ins 28 dur 96
        ENDTRACK                            ; 02C8D
Sfx21_Ch3:
        VOLUME  255                         ; 02C8E
        NOTE    A_5,29,12                   ; 02C90  n=$45 ins 29 dur 12
        NOTE    A_5,29,12                   ; 02C94  n=$45 ins 29 dur 12
        NOTE    A_5,29,24                   ; 02C98  n=$45 ins 29 dur 24
        ENDTRACK                            ; 02C9C
Sfx22_Ch3:
        VOLUME  255                         ; 02C9D
        NOTE    A_5,30,6                    ; 02C9F  n=$45 ins 30 dur 6
        NOTE    As5,30,6                    ; 02CA3  n=$46 ins 30 dur 6
        NOTE    A_5,30,6                    ; 02CA7  n=$45 ins 30 dur 6
        NOTE    As5,30,6                    ; 02CAB  n=$46 ins 30 dur 6
        NOTE    A_5,30,6                    ; 02CAF  n=$45 ins 30 dur 6
        NOTE    As5,30,6                    ; 02CB3  n=$46 ins 30 dur 6
        ENDTRACK                            ; 02CB7
Sfx23_Ch3:
        VOLUME  255                         ; 02CB8
        NOTE    A_5,31,96                   ; 02CBA  n=$45 ins 31 dur 96
        ENDTRACK                            ; 02CBE
Sfx24_Ch3:
        VOLUME  255                         ; 02CBF
        NOTE    A_5,32,96                   ; 02CC1  n=$45 ins 32 dur 96
        ENDTRACK                            ; 02CC5
Sfx25_Ch3:
        VOLUME  255                         ; 02CC6
        NOTE    A_5,33,96                   ; 02CC8  n=$45 ins 33 dur 96
        ENDTRACK                            ; 02CCC
Sfx26_Ch3:
        VOLUME  255                         ; 02CCD
        NOTE    A_5,34,96                   ; 02CCF  n=$45 ins 34 dur 96
        ENDTRACK                            ; 02CD3
Sfx27_Ch3:
        VOLUME  255                         ; 02CD4
        NOTE    A_5,35,96                   ; 02CD6  n=$45 ins 35 dur 96
        ENDTRACK                            ; 02CDA
Sfx28_Ch3:
        VOLUME  255                         ; 02CDB
        NOTE    A_5,36,96                   ; 02CDD  n=$45 ins 36 dur 96
        ENDTRACK                            ; 02CE1
Sfx29_Ch3:
        VOLUME  255                         ; 02CE2
        NOTE    D_5,37,24                   ; 02CE4  n=$3E ins 37 dur 24
        ENDTRACK                            ; 02CE8
        dc.b    $00                         ; 02CE9  unreferenced data
PatternTable:
        dc.w    Pat00-*                     ; 02CEA  pattern 0
        dc.w    Pat01-*                     ; 02CEC  pattern 1
        dc.w    Pat02-*                     ; 02CEE  pattern 2
        dc.w    Pat03-*                     ; 02CF0  pattern 3
        dc.w    Pat04-*                     ; 02CF2  pattern 4
        dc.w    Pat05-*                     ; 02CF4  pattern 5
        dc.w    Pat06-*                     ; 02CF6  pattern 6
        dc.w    Pat07-*                     ; 02CF8  pattern 7
        dc.w    Pat08-*                     ; 02CFA  pattern 8
        dc.w    Pat09-*                     ; 02CFC  pattern 9
        dc.w    Pat10-*                     ; 02CFE  pattern 10
        dc.w    Pat11-*                     ; 02D00  pattern 11
        dc.w    $EFA7                       ; 02D02  pattern 12 (unused)
        dc.w    Pat13-*                     ; 02D04  pattern 13
        dc.w    Pat14-*                     ; 02D06  pattern 14
        dc.w    Pat15-*                     ; 02D08  pattern 15
        dc.w    Pat16-*                     ; 02D0A  pattern 16
        dc.w    Pat17-*                     ; 02D0C  pattern 17
        dc.w    Pat18-*                     ; 02D0E  pattern 18
        dc.w    Pat19-*                     ; 02D10  pattern 19
        dc.w    Pat20-*                     ; 02D12  pattern 20
        dc.b    $C8,$D2,$DC,$E6,$F0,$FA,$FF,$FA,$F0,$E6,$DC,$C8,$C3,$BE,$B9,$B4; 02D14  unreferenced data
        dc.b    $AF,$AA,$A5,$A0,$9B,$96,$94,$92,$90,$8E,$8C,$8A,$88,$86,$84,$82; 02D24
        dc.b    $80,$80,$80,$80,$80,$80,$80,$80,$80,$80,$80,$80,$80,$80,$80,$80; 02D34
        dc.b    $80,$80,$80,$80,$80,$80,$80,$80,$80,$80,$80,$80,$80,$80,$80,$80; 02D44
        dc.b    $80,$80,$80,$80,$80,$80,$80,$80,$80,$7E,$7C,$7A,$78,$76,$74,$72; 02D54
        dc.b    $70,$6E,$6C,$6A,$68,$66,$64,$62,$60,$5E,$5C,$5A,$58,$56,$54,$52; 02D64
        dc.b    $50,$4E,$4C,$4A,$48,$46,$45,$44,$43,$42,$41,$40,$3F,$3E,$3D,$3C; 02D74
        dc.b    $3B,$3A,$39,$38,$37,$36,$35,$34,$33,$32,$31,$30,$2F,$2E,$2D,$2C; 02D84
        dc.b    $2B,$2A,$29,$28,$27,$26,$25,$24,$23,$22,$21,$20,$1F,$1E,$1D,$1C; 02D94
        dc.b    $1B,$1A,$19,$18,$17,$16,$15,$14,$13,$12,$11,$10,$0F,$0E,$0D,$0C; 02DA4
        dc.b    $0B,$0A,$09,$09,$08,$08,$07,$07,$06,$06,$05,$05,$04,$04,$03,$03; 02DB4
        dc.b    $03,$02,$02,$02,$02,$01,$01,$01,$01,$00,$00; 02DC4
VolEnv_2DCF:
        dc.b    250,220,200,210,210,210,210,210,200,200,200,200,190,190,190,190,190,180,180,180,180,170,170,170,170,170,160,160,160,160,150,150,150,150,150,140,140,140,140,130,130,130,130,130,120,120,120,120,110,110,110,110,110,100,100,100,100,90,90,90,90,90,80,80,80,80,80,70,70,70,70,70,60,60,60,60,60,50,50,50,50,50,40,40,40,40,40,30,30,30,30,30,20,20,20,20,20,19,18,17,16,15,14,13,12,11,10,9,8,7,6,5,4,3,2,1,0; 02DCF  volume steps (vol = (n+1)*chanvol*insvol>>16), 0 = end
        dc.b    $00,$00,$00,$00             ; 02E44  unreferenced data
VolEnv_2E48:
        dc.b    250,220,200,180,160,140,150,150,150,150,150,150,150,150,150,150,150,150,150,150,150,150,150,150,150,150,150,140,140,140,140,140,140,140,140,140,140,140,140,140,140,140,140,140,140,140,140,130,130,130,130,130,130,130,130,130,130,120,120,120,120,120,120,120,120,120,120,120,110,110,110,110,110,110,110,110,110,100,100,100,100,100,95,90,85,80,75,70,65,60,55,50,45,40,35,30,28,26,24,22,20,19,18,17,16,15,14,13,12,11,10,9,9,8,8,7,7,7,6,6,6,6,5,5,5,5,4,4,4,4,4,3,3,3,3,3,2,2,2,2,2,1,1,1,1,2,1,1,1,0; 02E48  volume steps (vol = (n+1)*chanvol*insvol>>16), 0 = end
        dc.b    $00,$FF,$FF,$00,$00,$01,$01,$00,$00,$FF,$FF,$00,$00,$01,$01,$00; 02EDE  unreferenced data
        dc.b    $00,$FF,$FF,$00,$00,$01,$01,$00,$00,$FF,$FF,$00,$00,$01,$01,$00; 02EEE
        dc.b    $00,$FF,$FF,$00,$00,$01,$01,$00,$00,$FF,$FF,$00,$00,$01,$01,$00; 02EFE
        dc.b    $00,$FF,$FF,$00,$00,$01,$01,$00,$00,$FF,$FF,$00,$00,$01,$01,$00; 02F0E
        dc.b    $00,$FF,$FF,$00,$00,$01,$01,$00,$00,$FF,$FF,$00,$00,$01,$01,$00; 02F1E
        dc.b    $00,$FF,$FF,$00,$00,$01,$01,$00,$00,$FF,$FF,$00,$00,$01,$01,$00; 02F2E
        dc.b    $00,$FF,$FF,$00,$00,$01,$01,$00,$00,$FF,$FF,$00,$00,$01,$01,$00; 02F3E
        dc.b    $00,$FF,$FF,$00,$00,$01,$01,$00,$00,$FF,$FF,$00,$00,$01,$01,$00; 02F4E
        dc.b    $00,$FF,$FF,$00,$00,$01,$01,$00,$00,$FF,$FF,$00,$00,$FF; 02F5E
PitchTable:
        dc.w    $D745,$D42A,$D124,$CE24,$CB30,$C846,$C567,$C292; 02F6C  semitone 0 (octave 0)
        dc.w    $BFC8,$BD08,$BA53,$B7A7,$B505,$B26C,$AFDD,$AD58; 02F7C  semitone 2
        dc.w    $AADC,$A869,$A5FF,$A39D,$A145,$9EF5,$9CAE,$9A6E; 02F8C  semitone 4
        dc.w    $9838,$9609,$93E2,$91C4,$8FAD,$8D9D,$8B96,$8995; 02F9C  semitone 6
        dc.w    $879C,$85AB,$83C0,$81DC,$7FA6,$7E2A,$7C5B,$7A92; 02FAC  semitone 8
        dc.w    $78D1,$761B,$7560,$73B1,$7209,$7066,$6ECA,$6D33; 02FBC  semitone 10
        dc.w    $6BA2,$6A15,$6892,$6712,$6598,$6423,$62B3,$6149; 02FCC  semitone 12 (octave 1)
        dc.w    $5FE4,$5E84,$5D29,$5BD3,$5A82,$5936,$57EE,$56AC; 02FDC  semitone 14
        dc.w    $556E,$5434,$52FF,$51CE,$50A2,$4F7A,$4E57,$4D37; 02FEC  semitone 16
        dc.w    $4C1C,$4B04,$49F1,$48E2,$47D6,$46CE,$45CB,$44CA; 02FFC  semitone 18
        dc.w    $43CE,$42D5,$41E0,$40EE,$3FD3,$3F15,$3E2D,$3D49; 0300C  semitone 20
        dc.w    $3C68,$3B0D,$3AB0,$39D8,$3904,$3833,$3765,$3699; 0301C  semitone 22
        dc.w    $35D1,$350A,$3449,$3389,$32CC,$3211,$3159,$30A4; 0302C  semitone 24 (octave 2)
        dc.w    $2FF2,$2F42,$2E94,$2DE9,$2D41,$2C9B,$2BF7,$2B56; 0303C  semitone 26
        dc.w    $2AB7,$2A1A,$297F,$28E7,$2851,$27BD,$272B,$269B; 0304C  semitone 28
        dc.w    $260E,$2582,$24F8,$2471,$23EB,$2367,$22E5,$2265; 0305C  semitone 30
        dc.w    $21E7,$216A,$20F0,$2077,$1FE9,$1F8A,$1F16,$1EA4; 0306C  semitone 32
        dc.w    $1E34,$1D86,$1D58,$1CEC,$1C82,$1C19,$1BB2,$1B4C; 0307C  semitone 34
        dc.w    $1AE8,$1A85,$1A24,$19C4,$1966,$1908,$18AC,$1852; 0308C  semitone 36 (octave 3)
        dc.w    $17F9,$17A1,$174A,$16F4,$16A0,$164D,$15FB,$15AB; 0309C  semitone 38
        dc.w    $155B,$150D,$14BF,$1473,$1428,$13DE,$1395,$134D; 030AC  semitone 40
        dc.w    $1307,$12C1,$127C,$1238,$11F5,$11B3,$1172,$1132; 030BC  semitone 42
        dc.w    $10F3,$10B5,$1078,$103B,$0FF4,$0FC5,$0F8B,$0F52; 030CC  semitone 44
        dc.w    $0F1A,$0EC3,$0EAC,$0E76,$0E41,$0E0C,$0DD9,$0DA6; 030DC  semitone 46
        dc.w    $0D74,$0D42,$0D12,$0CE2,$0CB3,$0C84,$0C56,$0C29; 030EC  semitone 48 (octave 4)
        dc.w    $0BFC,$0BD0,$0BA5,$0B7A,$0B50,$0B26,$0AFD,$0AD5; 030FC  semitone 50
        dc.w    $0AAD,$0A86,$0A5F,$0A39,$0A14,$09EF,$09CA,$09A6; 0310C  semitone 52
        dc.w    $0983,$0960,$093E,$091C,$08FA,$08D9,$08B9,$0899; 0311C  semitone 54
        dc.w    $0879,$085A,$083C,$081D,$07FA,$07E2,$07C5,$07A9; 0312C  semitone 56
        dc.w    $078D,$0761,$0756,$073B,$0720,$0706,$06EC,$06D3; 0313C  semitone 58
        dc.w    $06BA,$06A1,$0689,$0671,$0659,$0642,$062B,$0614; 0314C  semitone 60 (octave 5)
        dc.w    $05FE,$05E8,$05D2,$05BD,$05A8,$0593,$057E,$056A; 0315C  semitone 62
        dc.w    $0556,$0543,$052F,$051C,$050A,$04F7,$04E5,$04D3; 0316C  semitone 64
        dc.w    $04C1,$04B0,$049F,$048E,$047D,$046C,$045C,$044C; 0317C  semitone 66
        dc.w    $043C,$042D,$041E,$040E,$03FD,$03F1,$03E2,$03D4; 0318C  semitone 68
        dc.w    $03C6,$03B0,$03AB,$039D,$0390,$0383,$0376,$0369; 0319C  semitone 70
        dc.w    $035D,$0350,$0344,$0338,$032C,$0321,$0315,$030A; 031AC  semitone 72 (octave 6)
        dc.w    $02FF,$02F4,$02E9,$02DE,$02D4,$02C9,$02BF,$02B5; 031BC  semitone 74
        dc.w    $02AB,$02A1,$0297,$028E,$0285,$027B,$0272,$0269; 031CC  semitone 76
        dc.w    $0260,$0258,$024F,$0247,$023E,$0236,$022E,$0226; 031DC  semitone 78
        dc.w    $021E,$0216,$020F,$0207,$01FE,$01F8,$01F1,$01EA; 031EC  semitone 80
        dc.w    $01E3,$01D8,$01D5,$01CE,$01C8,$01C1,$01BB,$01B4; 031FC  semitone 82
        dc.w    $01AE,$01A8,$01A2,$019C,$0196,$0190,$018A,$0185; 0320C  semitone 84 (octave 7)
        dc.w    $017F,$017A,$0174,$016F,$016A,$0164,$015F,$015A; 0321C  semitone 86
        dc.w    $0155,$0150,$014B,$0147,$0142,$013D,$0139,$0134; 0322C  semitone 88
        dc.w    $0130,$012C,$0127,$0123,$011F,$011B,$0117,$0113; 0323C  semitone 90
        dc.w    $010F,$010B,$0107,$0103,$00FF,$00FC,$00F8,$00F5; 0324C  semitone 92
        dc.w    $00F1,$00EC,$00EA,$00E7,$00E4,$00E0,$00DD,$00DA; 0325C  semitone 94
DriverVars:
        dcb.b   $34E,0                      ; 0326C  driver variables (see DRV_* / VC_* equates)
NullSample:
SampleBase:
        dcb.b   64,0                        ; 035BA  silent 32-word sample used for stopped channels
SmpHdr00:
        dc.b    $00,$00,$02,$E8,$36,$B0     ; 035FA  sample 0 header: length 744 bytes, 14000 Hz (not used by the driver)
Smp00:
        incbin  "samples/gng_music_1mb_smp00.raw",0,744; 03600  744 bytes
SmpHdr01:
        dc.b    $00,$00,$01,$74,$36,$B0     ; 038E8  sample 1 header: length 372 bytes, 14000 Hz (not used by the driver)
Smp01:
        incbin  "samples/gng_music_1mb_smp01.raw",0,372; 038EE  372 bytes
SmpHdr02:
        dc.b    $00,$00,$00,$F8,$36,$B0     ; 03A62  sample 2 header: length 248 bytes, 14000 Hz (not used by the driver)
Smp02:
        incbin  "samples/gng_music_1mb_smp02.raw",0,248; 03A68  248 bytes
SmpHdr03:
        dc.b    $00,$00,$00,$AA,$36,$B0     ; 03B60  sample 3 header: length 170 bytes, 14000 Hz (not used by the driver)
Smp03:
        incbin  "samples/gng_music_1mb_smp03.raw",0,170; 03B66  170 bytes
SmpHdr04:
        dc.b    $00,$00,$00,$74,$36,$B0     ; 03C10  sample 4 header: length 116 bytes, 14000 Hz (not used by the driver)
Smp04:
        incbin  "samples/gng_music_1mb_smp04.raw",0,116; 03C16  116 bytes
SmpHdr05:
        dc.b    $00,$00,$22,$50,$37,$14     ; 03C8A  sample 5 header: length 8784 bytes, 14100 Hz (not used by the driver)
Smp05:
        incbin  "samples/gng_music_1mb_smp05.raw",0,8784; 03C90  8784 bytes
SmpHdr06:
        dc.b    $00,$00,$0C,$C8,$37,$14     ; 05EE0  sample 6 header: length 3272 bytes, 14100 Hz (not used by the driver)
Smp06:
        incbin  "samples/gng_music_1mb_smp06.raw",0,3272; 05EE6  3272 bytes
SmpHdr07:
        dc.b    $00,$00,$0F,$82,$37,$14     ; 06BAE  sample 7 header: length 3970 bytes, 14100 Hz (not used by the driver)
Smp07:
        incbin  "samples/gng_music_1mb_smp07.raw",0,3970; 06BB4  3970 bytes
SmpHdr08:
        dc.b    $00,$00,$34,$E6,$37,$14     ; 07B36  sample 8 header: length 13542 bytes, 14100 Hz (not used by the driver)
Smp08:
        incbin  "samples/gng_music_1mb_smp08.raw",0,13542; 07B3C  13542 bytes
SmpHdr09:
        dc.b    $00,$00,$0C,$56,$37,$14     ; 0B022  sample 9 header: length 3158 bytes, 14100 Hz (not used by the driver)
Smp09:
        incbin  "samples/gng_music_1mb_smp09.raw",0,3158; 0B028  3158 bytes
SmpHdr10:
        dc.b    $00,$00,$08,$E4,$27,$10     ; 0BC7E  sample 10 header: length 2276 bytes, 10000 Hz (not used by the driver)
Smp10:
        incbin  "samples/gng_music_1mb_smp10.raw",0,2276; 0BC84  2276 bytes
SmpHdr11:
        dc.b    $00,$00,$07,$9E,$27,$10     ; 0C568  sample 11 header: length 1950 bytes, 10000 Hz (not used by the driver)
Smp11:
        incbin  "samples/gng_music_1mb_smp11.raw",0,1950; 0C56E  1950 bytes
SmpHdr12:
        dc.b    $00,$00,$05,$84,$27,$10     ; 0CD0C  sample 12 header: length 1412 bytes, 10000 Hz (not used by the driver)
Smp12:
        incbin  "samples/gng_music_1mb_smp12.raw",0,1412; 0CD12  1412 bytes
SmpHdr13:
        dc.b    $00,$00,$07,$82,$27,$10     ; 0D296  sample 13 header: length 1922 bytes, 10000 Hz (not used by the driver)
Smp13:
        incbin  "samples/gng_music_1mb_smp13.raw",0,1922; 0D29C  1922 bytes
SmpHdr14:
        dc.b    $00,$00,$10,$5A,$1F,$40     ; 0DA1E  sample 14 header: length 4186 bytes, 8000 Hz (not used by the driver)
Smp14:
        incbin  "samples/gng_music_1mb_smp14.raw",0,4186; 0DA24  4186 bytes
SmpHdr15:
        dc.b    $00,$00,$0C,$7E,$1F,$40     ; 0EA7E  sample 15 header: length 3198 bytes, 8000 Hz (not used by the driver)
Smp15:
        incbin  "samples/gng_music_1mb_smp15.raw",0,3198; 0EA84  3198 bytes
SmpHdr16:
        dc.b    $00,$00,$0D,$E8,$1F,$40     ; 0F702  sample 16 header: length 3560 bytes, 8000 Hz (not used by the driver)
Smp16:
        incbin  "samples/gng_music_1mb_smp16.raw",0,3560; 0F708  3560 bytes
SmpHdr17:
        dc.b    $00,$00,$0D,$68,$1F,$40     ; 104F0  sample 17 header: length 3432 bytes, 8000 Hz (not used by the driver)
Smp17:
        incbin  "samples/gng_music_1mb_smp17.raw",0,2100; 104F6  2100 bytes
Smp17_834:
        incbin  "samples/gng_music_1mb_smp17.raw",2100,1332; 10D2A  1332 bytes
SmpHdr18:
        dc.b    $00,$00,$12,$02,$1F,$40     ; 1125E  sample 18 header: length 4610 bytes, 8000 Hz (not used by the driver)
Smp18:
        incbin  "samples/gng_music_1mb_smp18.raw",0,4610; 11264  4610 bytes
SmpHdr19:
        dc.b    $00,$00,$0E,$BE,$1F,$40     ; 12466  sample 19 header: length 3774 bytes, 8000 Hz (not used by the driver)
Smp19:
        incbin  "samples/gng_music_1mb_smp19.raw",0,3774; 1246C  3774 bytes
SmpHdr20:
        dc.b    $00,$00,$22,$B0,$1D,$4C     ; 1332A  sample 20 header: length 8880 bytes, 7500 Hz (not used by the driver)
Smp20:
        incbin  "samples/gng_music_1mb_smp20.raw",0,8880; 13330  8880 bytes
SmpHdr21:
        dc.b    $00,$00,$07,$80,$27,$10     ; 155E0  sample 21 header: length 1920 bytes, 10000 Hz (not used by the driver)
Smp21:
        incbin  "samples/gng_music_1mb_smp21.raw",0,1920; 155E6  1920 bytes
SmpHdr22:
        dc.b    $00,$00,$0B,$9C,$27,$10     ; 15D66  sample 22 header: length 2972 bytes, 10000 Hz (not used by the driver)
Smp22:
        incbin  "samples/gng_music_1mb_smp22.raw",0,2972; 15D6C  2972 bytes
SmpHdr23:
        dc.b    $00,$00,$02,$5C,$27,$10     ; 16908  sample 23 header: length 604 bytes, 10000 Hz (not used by the driver)
Smp23:
        incbin  "samples/gng_music_1mb_smp23.raw",0,604; 1690E  604 bytes
SmpHdr24:
        dc.b    $00,$00,$02,$40,$27,$10     ; 16B6A  sample 24 header: length 576 bytes, 10000 Hz (not used by the driver)
Smp24:
        incbin  "samples/gng_music_1mb_smp24.raw",0,576; 16B70  576 bytes
SmpHdr25:
        dc.b    $00,$00,$20,$D0,$1D,$4C     ; 16DB0  sample 25 header: length 8400 bytes, 7500 Hz (not used by the driver)
Smp25:
        incbin  "samples/gng_music_1mb_smp25.raw",0,8400; 16DB6  8400 bytes
SmpHdr26:
        dc.b    $00,$00,$0C,$84,$27,$10     ; 18E86  sample 26 header: length 3204 bytes, 10000 Hz (not used by the driver)
Smp26:
        incbin  "samples/gng_music_1mb_smp26.raw",0,3204; 18E8C  3204 bytes
SmpHdr27:
        dc.b    $00,$00,$18,$7E,$27,$10     ; 19B10  sample 27 header: length 6270 bytes, 10000 Hz (not used by the driver)
Smp27:
        incbin  "samples/gng_music_1mb_smp27.raw",0,6270; 19B16  6270 bytes
