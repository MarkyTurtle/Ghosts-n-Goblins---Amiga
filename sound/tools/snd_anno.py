"""Annotations for the GnG sound driver (shared by both sound files; offsets are file offsets)."""
NOTE_SYM = ['C_', 'Cs', 'D_', 'Ds', 'E_', 'F_', 'Fs', 'G_', 'Gs', 'A_', 'As', 'B_']

CODE_NAMES = {
    0x20: 'SndEntry', 0x28: 'SndCommandTable', 0x38: 'CmdPlayTune', 0xC6: 'CmdPlaySfx', 0x154: 'CmdSetUserValue',
    0x164: 'CmdTick', 0x182: 'TickVoiceLoop', 0x192: 'VoiceNextEvent', 0x1B4: 'MusicVoiceEvent', 0x1C4: 'ReadBytecode',
    0x1DE: 'BcNop', 0x1E0: 'BytecodeTable', 0x260: 'BcRest', 0x280: 'BcEnd', 0x29E: 'BcVolume', 0x2AE: 'BcJump',
    0x2C0: 'BcPortaOn', 0x2D4: 'BcPortaOff', 0x2E0: 'BcCall', 0x2E8: 'BcCallN', 0x2F0: 'BcCallPush', 0x316: 'BcReturn',
    0x326: 'BcReturnPop', 0x338: 'BcNote', 0x36A: 'NoteNoGlide', 0x372: 'NoteSetTarget', 0x406: 'NoteStartSound',
    0x43E: 'StartChannelDMA', 0x4D2: 'NoLoopPart', 0x4E4: 'VoiceEffects', 0x524: 'DoPortamento', 0x564: 'DoPitchEnvelope',
    0x592: 'NoPitchEnvelope', 0x5A0: 'WritePeriod', 0x5C6: 'NextVoice', 0x5DA: 'DebugWaitMouse',
}

HEADERS = {
0x20: """=====================================================================
Ghosts'n Goblins sound driver - Richard Frankish's music player,
music & sound effects by Mark Cooksey (Elite, 1990).
Loaded raw (hunk header left in place); entry = file+$20.

Call with d0.l = (argument << 16) | command:
   0  CmdTick          - call once per vertical blank (VblIRQ does)
   1  CmdPlayTune      - start tune <argument> on the 4 music voices
   2  CmdPlaySfx       - start effect <argument> on the 4 sfx voices
   3  CmdSetUserValue  - store <argument> in DRV_UserValue (never read)
The game reaches this through vector $60 (MUSIC_PLAYER).

8 voices: 4 music (DRV_Mus0-3) + 4 sound effect (DRV_Sfx0-3); voice n
plays on Paula channel n&3. While an sfx voice is active on a channel
the music voice for that channel keeps running silently (it still
advances through its data but does not touch the hardware).
=====================================================================""",
0x28: "Command dispatch: 4-byte entries indexed by command*4",
0x38: """CmdPlayTune - a1 = MusicTable + tune*16 (4 self-relative longs, one per
channel, 0 = channel unused). Each used voice gets its data pointer,
duration 0 (start next tick) and an empty call stack.""",
0xC6: "CmdPlaySfx - same, from SfxTable, into the four sfx voices",
0x154: "CmdSetUserValue - stores the argument in DRV_UserValue. Nothing reads it.",
0x164: """CmdTick - run every voice once per frame.
d7 = $70,$60..$00: voice index = d7>>4 (7..0), channel = (d7>>4)&3,
bit 2 of the index = sound-effect voice. Sfx voices (7-4) are done
first so they can claim their channel (DRV_SfxChans) before the music
voice for that channel runs. a2 = CUSTOM, a3 = DriverVars,
a4 = CUSTOM + channel*16 (so AUD_xx(a4) = AUDnxx), a5 = voice.""",
0x192: """Duration expired: fetch the next event.
DRV_Owns = this voice may write to its Paula channel:
  sfx voice   - always (and marks the channel busy in DRV_SfxChans)
  music voice - only when no sfx voice holds the channel
NOTE: DRV_Owns is only refreshed here, so the per-tick effects below
use the value left by the last voice that read an event.""",
0x1C4: """ReadBytecode - one byte: $00-$5F = note, $60-$7F = command
(bit 7 is masked off, so $E0-$FF alias $60-$7F; never used).""",
0x1E0: """Bytecode commands ($60 + index):
 $60 REST dur.w,0     $63 VOLUME v        $64 CALL pat,transpose
 $65 CALLN pat,tr,n   $66 RETURN          $67 END
 $68 JUMP rel.w       $69 PORTA_ON time   $6B PORTA_OFF
 $61,$62,$6A,$6C-$7F = no-op""",
0x260: "REST: duration.w, spare byte; mutes the channel (AUDxVOL = 0) if owned",
0x280: "END: voice stops; channel gets the silent sample, volume 0",
0x29E: "VOLUME: channel volume 0-255 (multiplied with the instrument volume)",
0x2AE: "JUMP: signed 16-bit offset relative to the $68 byte",
0x2C0: "PORTA_ON: following notes glide from the previous pitch over <time> ticks",
0x2E0: "CALL pattern,transpose (play once)",
0x2E8: """CALLN pattern,transpose,count - plays count+1 times.
Call stack frame (10 bytes, grows down from VC_Duration): count.w,
pattern start.l, return address.l - room for 4 nested calls.
Patterns are found through PatternTable (signed self-relative words).""",
0x316: "RETURN: repeat the pattern while the count lasts, else pop and clear transpose",
0x338: """NOTE: note.b, instrument.b, duration.b, spare.b
pitch = (note + transpose) * 4  (PitchTable has 4 steps per semitone)
With portamento on, the glide step = ((new-old)<<4) / time.""",
0x372: """Load the instrument record (InstrumentTable -> 28 bytes):
 +0  attack sample offset.l (from SampleBase, 0 = none)
 +4  loop sample offset.l   (0 = none: silence after the attack)
 +8  volume envelope.l (self-relative)   +12 pitch envelope.l (self-rel.)
 +16 attack length.w  +18 loop length.w (words, = AUDxLEN)
 +20 attack period multiplier.w   +22 loop period multiplier.w
 +24 volume env speed.b  +25 pitch env speed.b  +26 volume.w (0-256)""",
0x406: """Period = PitchTable[pitch] * multiplier >> 16. An instrument without an
attack sample just changes the loop sample/period (legato).""",
0x43E: """Start the sample: with interrupts off, stop the channel's DMA, set a
period of 1 and wait for the channel's audio interrupt twice so Paula
is idle, load attack LC/LEN/PER, enable DMA, wait for the interrupt
that says Paula has latched it, then load the loop part (or the
silent sample) so it plays after the attack.""",
0x4E4: """Per-tick effects (also runs while a note is held):
volume envelope - every <speed> ticks the next byte n gives
  vol = (n+1) * channel volume * instrument volume >> 16; 0 ends it""",
0x524: "Portamento: move the current pitch (x16 fixed point) towards the target",
0x564: "Pitch envelope: every <speed> ticks subtract the next signed byte (1/4 semitones) from the pitch; $80 ends it",
0x5A0: "Write the period for the current pitch (attack or loop multiplier)",
0x5DA: """DebugWaitMouse - NOT CALLED. Developer breakpoint left in the driver:
shows colour d6 in COLOR00 until the left mouse button is pressed, then
waits for release (with delays).""",
}

COMMENTS = {
    0x24: 'dispatch on command', 0x3E: 'a3 = driver variables', 0x48: 'a1 = MusicTable',
    0x4C: '16 bytes per tune', 0x50: 'channel 0 data (self-relative long)', 0x5C: 'voice data pointer',
    0x60: 'duration 0: start next tick', 0x64: 'empty call stack', 0xD6: 'a1 = SfxTable',
    0x174: 'silent sample for stopped channels', 0x17C: 'start with voice 7 (sfx, channel 3)',
    0x18A: 'note still sounding?', 0x196: 'sound-effect voice?', 0x1A2: 'sfx voice owns its channel',
    0x1A6: 'mark channel taken by sfx', 0x1BC: 'channel free of sfx?', 0x1CE: 'command byte?',
    0x1DA: 'jump to command handler', 0x2FA: 'push return address', 0x30A: 'push pattern start',
    0x30C: 'push repeat count', 0x33C: 'quarter-semitone pitch index', 0x3EC: 'volume = ins vol * chan vol >> 8',
    0x3FA: '0-255 -> 0-63', 0x41A: 'no attack sample: just retune', 0x450: 'INTENA: master off',
    0x456: 'DMACON: channel DMA off', 0x45A: 'period 1', 0x466: 'clear AUDn interrupt request',
    0x46E: 'wait for AUDn interrupt (DMA stopped)', 0x490: 'attack sample', 0x4A6: 'DMACON: channel DMA on',
    0x4AE: 'wait until Paula has latched the attack', 0x4C6: 'loop sample follows the attack',
    0x4CA: 'INTENA: master on', 0x4D8: 'no loop: silent sample', 0x4FC: 'envelope byte 0 = end',
    0x57C: '$80 (overflow on neg) = end', 0x5CA: 'next voice', 0x5D0: 'until voice 0 done',
}

VOICE_FIELDS = {0x00: 'VC_DataPtr', 0x04: 'VC_Instrument', 0x05: 'VC_Spare', 0x06: 'VC_AttackPtr', 0x0A: 'VC_LoopPtr',
    0x0E: 'VC_AttackLen', 0x10: 'VC_LoopLen', 0x12: 'VC_AttackMul', 0x14: 'VC_LoopMul', 0x1A: 'VC_StackPtr',
    0x46: 'VC_Duration', 0x48: 'VC_ChanVolume', 0x4A: 'VC_Volume', 0x4C: 'VC_InsVolume', 0x4E: 'VC_VolEnvPtr',
    0x52: 'VC_VolEnvSpeed', 0x53: 'VC_VolEnvCount', 0x54: 'VC_PitchEnvPtr', 0x58: 'VC_PitchEnvSpeed',
    0x59: 'VC_PitchEnvCount', 0x5A: 'VC_Pitch', 0x5C: 'VC_TargetPitch', 0x5E: 'VC_Transpose', 0x60: 'VC_GlideFrom',
    0x62: 'VC_GlideTime', 0x64: 'VC_GlideStep', 0x66: 'VC_GlideOn', 0x67: 'VC_InAttack'}
VOICE_CMT = {'VC_DataPtr': 'current position in the bytecode (0 = voice idle)', 'VC_Spare': '4th note byte (always 0, unused)',
    'VC_StackPtr': 'call stack pointer (stack: $1E-$45, 4 frames x 10 bytes)', 'VC_Duration': 'ticks left (also stack top)',
    'VC_ChanVolume': 'VOLUME command value 0-255', 'VC_Volume': 'current volume 0-255 (AUDxVOL = /4)',
    'VC_Pitch': 'current pitch, 1/4 semitones', 'VC_TargetPitch': 'note pitch, 1/4 semitones', 'VC_InAttack': '-1 while the attack part plays'}
VAR_FIELDS = {0x00: 'DRV_Owns', 0x01: 'DRV_SfxChans', 0x02: 'DRV_UserValue', 0x04: 'DRV_Mus0', 0x6C: 'DRV_Mus1',
    0xD4: 'DRV_Mus2', 0x13C: 'DRV_Mus3', 0x1A4: 'DRV_Sfx0', 0x20C: 'DRV_Sfx1', 0x274: 'DRV_Sfx2', 0x2DC: 'DRV_Sfx3',
    0x344: 'DRV_SilentPtr'}
VAR_CMT = {'DRV_Owns': 'current voice may write to Paula', 'DRV_SfxChans': 'bit n = channel n held by a sound effect',
    'DRV_UserValue': 'set by command 3, never read', 'DRV_SilentPtr': 'address of the silent sample'}
AUD_FIELDS = {0xA0: 'AUD_LC', 0xA4: 'AUD_LEN', 0xA6: 'AUD_PER', 0xA8: 'AUD_VOL', 0xAA: 'AUD_DAT'}

def reg_context(o):
    if 0x38 <= o < 0x164: return {'a3': 'vars', 'a4': 'voice', 'a0': 'custom'}
    if 0x164 <= o < 0x5DA: return {'a2': 'custom', 'a3': 'vars', 'a4': 'aud', 'a5': 'voice'}
    return {}

HUNK_CMT = {0: 'HUNK_HEADER', 4: 'no resident libraries', 8: 'table size 1', 0xC: 'first hunk 0',
            0x10: 'last hunk 0', 0x14: 'hunk 0 size (longs)', 0x18: 'HUNK_CODE', 0x1C: 'size (longs)'}

TUNES = {0: 'start-of-game fanfare (after the intro)', 1: 'name entry - new top score', 2: 'level music, levels 0-1',
    3: 'name entry - high score', 4: 'hurry up! (0:15 left, loops)', 5: 'boss beaten - key appears', 6: 'name entered',
    7: 'game over (also Esc abort)', 8: 'life lost', 9: 'not referenced by the game', 10: 'not referenced by the game',
    11: 'not referenced by the game', 12: 'level music, levels 5-6', 13: 'level music, levels 2-4', 14: 'intro cut-scene'}
SFX = {1: 'Arthur hit (armour lost)', 4: 'jump', 5: 'land', 6: 'throw weapon', 10: 'weapon shot event',
    11: 'torch flame (1MB build)', 12: 'weapon / boss hit', 17: 'enemy event (crow, blue killer, ghost, skeleton)',
    20: 'enemy event (flying knight, zombie, Astaroth)', 28: 'key / item collected'}
def song_name(kind, i):
    if kind == 'tune': return TUNES.get(i, '')
    return SFX.get(i, '')

def gap_comment(name, o): return 'unreferenced data'

def _note_equates():
    lines = []
    for n in range(96):
        lines.append(f'{NOTE_SYM[n % 12]}{n // 12}\tequ\t{n}')
    return '\n'.join(lines)

def _fields(d, cm, prefix_cmt=''):
    return '\n'.join(f'{v:<18}equ\t${k:03X}' + (f'\t; {cm[v]}' if v in cm else '') for k, v in sorted(d.items()))

PRELUDE = """; =========================================================================
; Ghosts'n Goblins (Elite, 1990) - sound driver + data: {name}
; Source file: {fn}  (loaded raw at ${base:X}, called at ${base:X}+$20)
; Driver: Richard Frankish's music player; music/sfx: Mark Cooksey.
; Assemble: vasmm68k_mot -Fbin -m68000 -no-opt -o {name}.bin {name}.s
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
""" + _fields(AUD_FIELDS, {}) + """

; driver variables (offsets from DriverVars)
""" + _fields(VAR_FIELDS, VAR_CMT) + """
DRV_VOICE_SIZE	equ	$68

; voice structure
""" + _fields(VOICE_FIELDS, VOICE_CMT) + """

; ---- note names: C_4 = note 48 etc. (driver note numbers, octave = n/12)
""" + _note_equates() + """

; ---- music bytecode
NOTE	macro			; note,instrument,duration
	dc.b	\\1,\\2,\\3,0
	endm
REST	macro			; duration (16-bit)
	dc.b	$60,(\\1)>>8,(\\1)&$FF,0
	endm
VOLUME	macro			; 0-255
	dc.b	$63,\\1
	endm
CALL	macro			; pattern,transpose
	dc.b	$64,\\1,\\2
	endm
CALLN	macro			; pattern,transpose,count (plays count+1 times)
	dc.b	$65,\\1,\\2,\\3
	endm
RETURN	macro
	dc.b	$66
	endm
ENDTRACK macro
	dc.b	$67
	endm
JUMP	macro			; label (offset is relative to the $68 byte)
jmp\\@	dc.b	$68,((\\1-jmp\\@)>>8)&$FF,(\\1-jmp\\@)&$FF
	endm
PORTA_ON macro			; glide time in ticks
	dc.b	$69,\\1
	endm
PORTA_OFF macro
	dc.b	$6B
	endm

	org	${base:X}
"""
