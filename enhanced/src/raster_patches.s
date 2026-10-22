;==============================================================================
; raster_patches.s - only for the timing build (build_enh.py --raster): the game
; logic's start and end set the background colour, so that with the module's own
; colours (RASTER in module.s) each part of a frame shows as a band of colour down the
; screen. Applied after patches.s.
;   grey   game logic (Level1Logic)            red    scroller: new edges, restore
;   orange text replay                         blue   BOBs
;   yellow copper list                         green  waiting for line $44 (ShowBackBuffer)
;   black  idle (logic finished)
;==============================================================================

;@patch Level1Logic Level1LogicEnd
                jsr     EnhLogicStart           ; (does the INTREQ write it replaces)
                nop

;@patch LogicExit LogicExitEnd
                jmp     EnhLogicEnd             ; (movem + rte)

;@patch PlayFrameExit PlayFrameExitEnd
                jmp     EnhLogicEnd
