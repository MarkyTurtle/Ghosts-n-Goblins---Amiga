;==============================================================================
; scroll_test.s - the scroller core on its own at $7A000, for the unit tests
; (tools/test_scroll.py, tools/test_bobs.py), with a jump table at the start.
; Assemble from enhanced/src with -I ../.. (for gng_equates.i).
;==============================================================================
                include "gng_equates.i"

CellTiles       equ     $1222C          ; game data (512K build addresses)
ItemBoxSizes    equ     $540E
SmallBobSizes   equ     $A992
MASKBUF         equ     $79800          ; BOB mask (test memory)

                org     $7A000
                bra.w   ScrFullDraw
                bra.w   ScrScrollTo
                bra.w   ScrBuildCopper
                bra.w   ScrRestore
                bra.w   ScrDrawBobs

                include "scroll.s"
