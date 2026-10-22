; Ghosts'n Goblins (Elite, 1990, v3) - main program, 512K build
; Loaded raw by the bootblock to $80 from tracks 110-125, entered at $A0.
; Assemble: vasmm68k_mot -Fbin -m68000 -no-opt -o main.bin gng_main.s

	include	"gng_equates.i"

; ---- data macros
SPAWNER	macro			; enemy type, script number, flags (bit 0 world coords, bit 1 runs once)
	dc.b	((\1)<<4)|((\2)>>4),((\3)<<4)|((\2)&15)
	endm
SPAWN	macro			; x, y (camera-relative unless the spawner has world coords), param, delay
	dc.w	\1,\2
	dc.b	\3,\4
	endm

AFRAME	macro			; animation step: frame (~n = mirrored), frames to show it
	dc.b	\1,\2
	endm
ALOOP	macro			; last step: frame, frames (stored negated), then loop back to the label
	dc.b	\1,-(\2)
	dc.w	\3-*
	endm

AF	macro	; frame, ticks (enemy / shot animation entry)
	dc.b	\1,\2
	endm
AL	macro	; frame, ticks, next: last entry, then continue at 'next'
	dc.b	\1,(\2)|$80
	dc.w	\3-*
	endm

FRAME	macro	; BOB frame: offset into the graphics set, y adjust, height
	dc.w	\1
	dc.b	\2,\3
	endm
ISTEP	macro	; platform script entry: step number, frames
	dc.b	\1,\2
	endm
ILOOP	macro	; last entry: step, frames, then continue at the label
	dc.b	\1,(\2)|$80
	dc.w	\3-*
	endm
DSTEP	macro	; Dragon path entry: frames, direction (0 right, 4 down, 8 left, 12 up)
	dc.b	\1,\2
	endm
DLOOP	macro	; last entry: frames, direction, then continue at the label
	dc.b	(\1)|$80,\2
	dc.w	\3-*
	endm
FENTRY	macro	; file table entry: load address, length in bytes, first track
	dc.l	\1,\2
	dc.w	\3
	endm
PLACE	macro	; type, param, x, y (world pixels, Y up)
	dc.b	\1,\2
	dc.w	\3,\4
	endm
; enemy types (O_Type of enemies)
E_WOODYPIG	equ	0
E_CROW	equ	1
E_PETITEDEVIL	equ	2
E_FLYINGKNIGHT	equ	3
E_BLUEKILLER	equ	4
E_REDARREMER	equ	5
E_SATAN	equ	6
E_MAGICIAN	equ	7
E_UNICORN	equ	8
E_SKELETON	equ	9
E_BIGMAN	equ	10
E_ZOMBIE	equ	11
E_DRAGON	equ	12
E_ASTAROTH	equ	13
E_FIRE	equ	14
E_PRINCESS	equ	15
E_TYPE16	equ	16
E_PLANT	equ	17
E_FIREPILLAR	equ	18
; item types (O_Type of items): touch trigger / pickup, shootable scenery, platforms
I_TOUCH	equ	0
I_SCENERY	equ	1
I_PLATFORM2	equ	2
I_PLATFORM3	equ	3
I_PLATFORM4	equ	4
I_PLATFORM5	equ	5

	org	$80
