;==============================================================================
; fps50_patches.s - only for the 50 fps 512K build (build_enh.py --fps50): PlayFrame
; skips the camera and drawing on even frames ($6E76: btst #0,g_GameFrame+1 / beq),
; so the 512K program shows 25 frames a second. The 1MB program has no such test and
; draws every frame; without it the 512K one does the same. (The game logic itself
; already runs every frame in both.)
;==============================================================================

;@patch $6E76 $6E80
                nop
                nop
                nop
                nop
                nop
