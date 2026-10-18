;---------------------------------------------------------------------------
; ==================================================================
; One program for every machine (enhanced branch)
; ==================================================================
; ReadProfile - Start, first thing: Profile from the bootblock's machine description
; (MACHINE_INFO). With 1MB or more of chip RAM: PF_CACHE, PF_MUSIC, PF_EVERY - the 1MB
; program's features. Without a description (the original bootblock) or with less chip RAM:
; none, the 512K program. Also the two texts the 1MB program has its own way: the credit line
; ('MUSIC' for 'SOUND') and the initials stored for a blank name ('501' for '504').
;---------------------------------------------------------------------------
ReadProfile:
        lea.l   (MACHINE_INFO).l,a0
        cmpi.l  #'GNGM',MI_MAGIC(a0)
        bne.b   rp_done
        cmpi.l  #$100000,MI_CHIP_UPPER(a0)      ; end of chip RAM: 1MB or more?
        bcs.b   rp_done
        move.b  #(1<<PF_CACHE)|(1<<PF_MUSIC)|(1<<PF_EVERY),(Profile).l
        lea.l   (TxtCreditSound).l,a0           ; 'SOUND' -> 'MUSIC'
        lea.l   TxtMusic(pc),a1
        moveq   #4,d0
rp_text:
        move.b  (a1)+,(a0)+
        dbra    d0,rp_text
        move.b  #'1',(NameBlank+2).l            ; '504' -> '501'
rp_done:
        rts
TxtMusic:
        dc.b    'MUSIC'
Profile:
        dc.b    0                               ; PF_ bits
        even
MusicPlayerPtr:
        dc.l    MUSIC_PLAYER                    ; the sound driver's entry (LoadSound)
ItemGfxPtr:
        dc.l    ITEM_GFX_BUF                    ; item / explosion graphics (CacheGraphics: masked)
EShotGfxPtr:
        dc.l    ESHOT_GFX_BUF                   ; enemy shot graphics

;---------------------------------------------------------------------------
; LoadSound - the sound package: with PF_MUSIC the 1MB one (music and effects, assembled
; for MUSIC1M_FILE in upper chip RAM), otherwise the 512K effects package.
;---------------------------------------------------------------------------
LoadSound:
        btst    #PF_MUSIC,(Profile).l
        bne.b   ls_music
        lea.l   (FileMusic).l,a1
        bra.w   LoadFile
ls_music:
        lea.l   (FileMusic1M).l,a1
        bsr.w   LoadFile
        move.l  #MUSIC1M_PLAYER,(MusicPlayerPtr).l
        rts

;---------------------------------------------------------------------------
; CacheGraphics - with PF_CACHE, as the 1MB program's Start: every BOB graphics file is
; loaded once and converted by BuildMaskedGfx into a buffer in upper chip RAM with a mask
; line after every plane line (the item, shot and font files are already loaded to their
; 512K places); the packed progress map is kept; the frame offsets are doubled to match.
;---------------------------------------------------------------------------
CacheGraphics:
        btst    #PF_CACHE,(Profile).l
        beq.w   cg_done
        lea.l   (FileSmallBobs).l,a1
        bsr.w   LoadFile
        lea.l   (FileSmallBobs).l,a1
        movea.l (a1),a1
        lea.l   (SMALLBOB_CACHE).l,a2
        lea.l   (CacheSizesSmallBobs).l,a3
        moveq   #$9,d7
        bsr.w   BuildMaskedGfx
        lea.l   (FileEnemyBobs).l,a1
        bsr.w   LoadFile
        lea.l   (FileEnemyBobs).l,a1
        movea.l (a1),a1
        lea.l   (ENEMY_GFX_CACHE).l,a2
        lea.l   (CacheSizesEnemyGfx).l,a3
        moveq   #$26,d7
        bsr.w   BuildMaskedGfx
        lea.l   (FileItemGfx2).l,a1
        movea.l (a1),a1
        lea.l   (MITEM_GFX2_BUF).l,a2
        lea.l   (CacheSizesItemGfx2).l,a3
        moveq   #$2,d7
        bsr.w   BuildMaskedGfx
        lea.l   (FileEnemyShotGfx).l,a1
        movea.l (a1),a1
        lea.l   (MESHOT_GFX_BUF).l,a2
        lea.l   (CacheSizesEnemyShots).l,a3
        moveq   #$2,d7
        bsr.w   BuildMaskedGfx
        lea.l   (FileItemGfx).l,a1
        movea.l (a1),a1
        lea.l   (MITEM_GFX_BUF).l,a2
        lea.l   (CacheSizesItems).l,a3
        moveq   #$3,d7
        bsr.w   BuildMaskedGfx
        move.l  #MITEM_GFX_BUF,(ItemGfxPtr).l
        move.l  #MESHOT_GFX_BUF,(EShotGfxPtr).l
        lea.l   (FileProgressMap).l,a1          ; keep the packed progress map
        bsr.w   LoadFile
        lea.l   (FileProgressMap).l,a2
        movea.l (a2)+,a1
        move.l  (a2)+,d7
        lsr.l   #$2,d7
        subq.l  #$1,d7
        lea.l   (PROGRESS_MAP_CACHE).l,a2
cg_map:
        move.l  (a1)+,(a2)+
        dbra    d7,cg_map
        lea.l   (FrameOffsets1).l,a0            ; the BOB frame tables (FRAME): offsets x 2
        move.w  #(FrameOffsets1End-FrameOffsets1)/4-1,d0
        bsr.b   cg_frames
        lea.l   (FrameOffsets2).l,a0
        move.w  #(FrameOffsets2End-FrameOffsets2)/4-1,d0
        bsr.b   cg_frames
        lea.l   (BobSetOffsets).l,a0            ; set offsets (longs) x 2
        moveq   #21-1,d0
        bsr.b   cg_longs
        lea.l   (SmallBobSetOffsets).l,a0
        moveq   #10-1,d0
        bsr.b   cg_longs
cg_done:
        rts
cg_frames:
        move.w  (a0),d1
        add.w   d1,d1
        move.w  d1,(a0)
        addq.l  #4,a0
        dbra    d0,cg_frames
        rts
cg_longs:
        move.l  (a0),d1
        add.l   d1,d1
        move.l  d1,(a0)+
        dbra    d0,cg_longs
        rts

