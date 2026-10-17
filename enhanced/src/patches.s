;==============================================================================
; patches.s - changes to the original 512K main program for the enhanced build.
;
; Each block replaces the original code in place, from its first address up to (not
; including) the second; tools/build_enh.py assembles every block on its own at its
; address and checks that it fits, so everything else in the program stays where it
; was. Blocks may use the original's labels (orig_syms.i), the module's (module_syms.i),
; MODULE_ORG / MODULE_LEN / MODULE_TRACK (from the build) and the labels of the blocks
; before them (patch_syms.i).
;
; The code left behind a patched block is never reached any more.
;==============================================================================

;@patch RedrawScreen CollisionBoxes
; RedrawScreen -> the module. Its old space also holds the loader stub.
                jmp     EnhRedrawScreen
EnhLoad:        lea     EnhModuleFile(pc),a1    ; the module (its own track)
                bsr.w   LoadFile
                jsr     EnhInit
                lea     FileCopyrightScreen(pc),a1      ; then what Start loaded here before
                bra.w   LoadFile
EnhModuleFile:  dc.l    MODULE_ORG,MODULE_LEN   ; a FileTable entry: address, length, track
                dc.w    MODULE_TRACK
EnhRedrawBg:    jmp     EnhRedrawBackground     ; (RedrawEntry's bsr.w reaches here)

;@patch $5D32 $5D3A
; Start: load the scroller module (EnhLoad, in RedrawScreen's old space) before the
; copyright screen.
                jsr     EnhLoad
                nop

;@patch SwapScreens ShowBackBuffer
                jmp     EnhSwapScreens

;@patch ShowBackBuffer ArthurSpritePos
                jmp     EnhShowBackBuffer

;@patch SetBitplanePtrs SetMapBitplanePtrs
                jmp     EnhSetBitplanePtrs

;@patch RestoreBackground DrawBobs
                jmp     EnhRestoreBackground

;@patch DrawBobs DrawBob
                jmp     EnhDrawBobs

;@patch l_0B0D6 l_0B0E2
; PrintChar, playfield text: through the module (the ring needs the lines copied).
                jmp     EnhPrintField

;@patch RedrawEntry Level1Logic
; RedrawEntry (where VblIRQ sends user mode when a redraw is pending - the camera asks for
; one at almost every step): nothing needs redrawing any more, since the scroller keeps the
; buffers up to date; EnhRedrawBg only reports it done. The rest is as before: the logic
; is let run again (a camera clamp may have frozen it) and user mode idles.
                bsr.w   EnhRedrawBg
                clr.b   g_SkipLogic(a6)
                bra.b   *

;@patch CameraJump SwapScreens
; CameraJump - the camera switches to the origin 'redrawn' at g_NewTileX/Y: the same
; fine-scroll rules, but no buffers to rotate (SwapScreens, which it used to fall into).
                jmp     EnhCameraJump
