;==============================================================================
; fps50_patches.s - the 512K program draws every frame (left out by build_enh.py --fps25).
; PlayFrame skips the camera and drawing on even frames ($6E76: btst #0,g_GameFrame+1 /
; beq), so the original 512K program shows 25 frames a second. The 1MB program has no
; such test and draws every frame; without it the 512K one does the same. (The game logic
; already runs every frame in both.) When a frame's work does not fit in the frame,
; VblIRQ skips the next logic run, so busy scenes drop to 25 fps rather than tear.
;==============================================================================

;@patch $6E76 $6E80
                nop
                nop
                nop
                nop
                nop
