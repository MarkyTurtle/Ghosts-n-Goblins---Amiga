; Ghosts'n Goblins (Elite, 1990, v3) - main program, expanded-memory (1MB) build
; Tracks 17-32. The bootblock loads it raw to the address it leaves in $4.w (fast or slow RAM)
; and enters at load+$20. The code is position independent through g_BaseAddr ($2(a6)): every
; program address is assembled as an offset from the start of the file and has the load address
; added at run time (adda.l g_BaseAddr(a6) / adda.l a0). Chip-RAM buffers are absolute.
; So this source is assembled at org 0 and the labels are file offsets.
;
; Generated from the 512K build's annotations (gng_main.s) through an instruction-level alignment
; of the two builds. Lines marked [1MB] have no counterpart in the 512K build, and << >> notes
; mark every place where the two builds differ.
;
; Assemble: vasmm68k_mot -Fbin -m68000 -no-opt -o main_1mb.bin gng_main_1mb.s

	include	"gng_equates_1mb.i"

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

	org	0
