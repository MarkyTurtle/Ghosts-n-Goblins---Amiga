;---------------------------------------------------------------------------
; ==================================================================
; One program for every machine (enhanced branch)
; ==================================================================
; ReadProfile - Start, first thing: Profile from the bootblock's machine description
; (MACHINE_INFO). With 1MB or more of chip RAM (any chip RAM above $80000: Kickstart 1.3 keeps the
; top of a 1MB machine's chip RAM for itself and lists it as ending at $FE800): PF_CACHE, PF_MUSIC - the 1MB program's
; features (PF_EVERY, drawing every frame, is set for every machine). With less chip RAM but the
; program moved to an expansion (EnhRelocate): PF_MUSIC as well. Otherwise (or without a
; description: the original bootblock) none, the 512K program. Also the two texts the 1MB program has its own way: the credit line
; ('MUSIC' for 'SOUND') and the initials stored for a blank name ('501' for '504').
;---------------------------------------------------------------------------
ReadProfile:
        lea.l   (MACHINE_INFO).l,a0
        cmpi.l  #'GNGM',MI_MAGIC(a0)
        bne.b   rp_done
        cmpi.l  #$80000,MI_CHIP_UPPER(a0)       ; more than 512K of chip RAM: 1MB or more (exec
        bls.b   rp_small                        ; may keep the top for itself: 1.3 lists $FE800)
        move.b  #(1<<PF_CACHE)|(1<<PF_MUSIC)|(1<<PF_EVERY),(Profile).l
rp_texts:
        lea.l   (TxtCreditSound).l,a0           ; 'SOUND' -> 'MUSIC'
        lea.l   TxtMusic(pc),a1
        moveq   #4,d0
rp_text:
        move.b  (a1)+,(a0)+
        dbra    d0,rp_text
        move.b  #'1',(NameBlank+2).l            ; '504' -> '501'
rp_done:
        rts
rp_small:
        tst.b   (RelocDone).l                   ; moved out of chip RAM (EnhRelocate): the music,
        beq.b   rp_done                         ; in the chip RAM the program left
        move.b  #(1<<PF_MUSIC)|(1<<PF_EVERY),(Profile).l
        bra.b   rp_texts
TxtMusic:
        dc.b    'MUSIC'
Profile:
        dc.b    1<<PF_EVERY                     ; PF_ bits: every machine draws every frame now (the
                                                ; scroller has no redraw to wait for)
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
        tst.b   (RelocDone).l                   ; the program moved out of chip RAM: the package
        bne.b   ls_low                          ; goes where it was
        bsr.w   LoadFile
        move.l  #MUSIC1M_PLAYER,(MusicPlayerPtr).l
        rts
ls_low:
        move.l  #MUSICB_FILE,(a1)
        bsr.w   LoadFile
        movea.l (MusicRelocs).l,a3              ; its relocations (EnhRelocate loaded them)
        lea.l   (MUSICB_FILE).l,a2
        move.l  #MUSICB_FILE-MUSIC1M_FILE,d5
        bsr.w   ApplyRelocs
        move.l  #MUSICB_FILE+$20,(MusicPlayerPtr).l
        rts

;---------------------------------------------------------------------------
; LoadLevelTables - d0 = level: its map tables (per-level files build_game.py makes from the
; original program's BlockTiles and CellTiles, which are no longer in the program), to
; LEVEL_TABLES: the cells' slots (LEVEL_SLOTS: 256 bytes, cell -> slot; a cell the level
; never reads -> slot 0, cell $67's: empty), their BlockTiles (LEVEL_BLOCKS, 64 bytes a slot)
; and their CellTiles (LEVEL_CELLS, 256 bytes a slot). All registers kept.
;---------------------------------------------------------------------------
LoadLevelTables:
        movem.l d0-d7/a0-a6,-(a7)
        lea.l   (FileTables).l,a1
        mulu.w  #10,d0
        adda.w  d0,a1
        jsr     (LoadFile).l
        movem.l (a7)+,d0-d7/a0-a6
        rts
MfmBuf:
        dc.l    MFM_BUFFER                      ; LoadFile's MFM buffer (the progress map sets PM_MFM)

;---------------------------------------------------------------------------
; LoadFile - a1 -> file record (FENTRY: dest.l, length.l, file id.w) -> a5 = the end of the
; loaded data, a0 = CUSTOM (as the original's track loader left them); other registers kept.
; The disk is an ordinary AmigaDOS-format disk (11 sectors a track) with a file table at
; FT_OFFSET (boot_4489.s; build_game.py writes it): read once into FileDir, then each file is
; loaded from its offset by the 4489_byteloader (ByteLoader), the exact number of bytes. A
; failed load is tried again until it works (after 8 failures COLOR00 shows red).
; The byteloader uses a6, so the interrupt handlers load a6 themselves (IrqLevel1/3).
;---------------------------------------------------------------------------
LoadFile:
        movem.l d0-d7/a1-a4/a6,-(a7)
        movea.l (a1),a5                         ; destination
        move.l  4(a1),d5                        ; length
        moveq   #0,d4
        move.w  8(a1),d4                        ; file id
        lea.l   (FileDir).l,a2
        cmpi.l  #'GNGF',(a2)                    ; the file table, the first time
        beq.b   lf_dir
        movem.l d4-d5/a5,-(a7)
        moveq   #0,d0
        move.w  #FT_OFFSET,d0
        move.l  #FT_SIZE,d1
        movea.l a2,a0
        bsr.b   lf_load
        movem.l (a7)+,d4-d5/a5
lf_dir:
        lea.l   (FileDir).l,a2                  ; (the byteloader keeps no registers)
        lsl.w   #$3,d4
        move.l  FT_ENTRY(a2,d4.w),d0            ; the file's offset on the disk
        move.l  d5,d1
        movea.l a5,a0
        movem.l d5/a5,-(a7)
        bsr.b   lf_load
        movem.l (a7)+,d5/a5
        adda.l  d5,a5
        lea.l   CUSTOM,a0
        movem.l (a7)+,d0-d7/a1-a4/a6
        rts
lf_load:                                        ; d0 = offset, d1 = length, a0 = destination
        moveq   #0,d6
lf_try:
        movem.l d0-d1/d6/a0/a5,-(a7)
        moveq   #0,d2                           ; DF0
        movea.l (MfmBuf).l,a1
        bsr.w   ByteLoader
        move.l  d0,d7
        movem.l (a7)+,d0-d1/d6/a0/a5
        tst.l   d7
        beq.b   lf_ok
        addq.w  #$1,d6
        cmp.w   #$8,d6
        bcs.b   lf_try
        move.w  #$f00,CUSTOM+COLOR00            ; a disk error: red, and on trying
        bra.b   lf_try
lf_ok:
        rts
FileDir:
        dcb.b   FT_SIZE,0                       ; the disk's file table (LoadFile)
ByteLoader:
	include	"byteloader.i"
        even

;---------------------------------------------------------------------------
; IrqLevel1 / IrqLevel3 - the level 1 and level 3 autovectors: a6 = GLOBALS for the handlers
; (Level1Logic, VblIRQ), which take it as given; the interrupted a6 back on the way out
; (IrqExit1 / IrqExit3, where the handlers return). The byteloader uses a6 while a file
; loads with the interrupts running.
;---------------------------------------------------------------------------
IrqLevel1:
        move.l  a6,(IrqA6L1).l
        lea.l   (GLOBALS).l,a6
        jmp     Level1Logic
IrqExit1:
        movea.l (IrqA6L1).l,a6
        rte
IrqLevel3:
        move.l  a6,(IrqA6L3).l
        lea.l   (GLOBALS).l,a6
        jmp     VblIRQ
IrqExit3:
        movea.l (IrqA6L3).l,a6
        rte
IrqA6L1:
        dc.l    0
IrqA6L3:
        dc.l    0
FileTables:
	FENTRY	LEVEL_TABLES,TBLLEN0,FID_TABLES0+0
	FENTRY	LEVEL_TABLES,TBLLEN1,FID_TABLES0+1
	FENTRY	LEVEL_TABLES,TBLLEN2,FID_TABLES0+2
	FENTRY	LEVEL_TABLES,TBLLEN3,FID_TABLES0+3
	FENTRY	LEVEL_TABLES,TBLLEN4,FID_TABLES0+4
	FENTRY	LEVEL_TABLES,TBLLEN5,FID_TABLES0+5
	FENTRY	LEVEL_TABLES,TBLLEN6,FID_TABLES0+6

;---------------------------------------------------------------------------
; EnhRelocate - Start, first thing, still at $80: with less than 1MB of chip RAM and an
; expansion (fast RAM, else slow RAM: MACHINE_INFO) with room, the program moves there -
; everything from $80 to the memory map (MAP_LOW: the code, the tables, the globals; the
; memory map stays where it is, in chip RAM). It is copied, the relocation file (tables of
; the program's and the 1MB music package's absolute addresses, made by build_game.py by
; assembling each at two origins) is loaded after it, the program's addresses are moved,
; and Start runs again there (RelocDone: once). The chip RAM from $80 is then free for the
; 1MB music package (ReadProfile: PF_MUSIC; LoadSound). The CPU alone reads the program: the
; blitter, copper, sprites and Paula read only the memory map.
;---------------------------------------------------------------------------
IMAGE_BASE      equ     $80                     ; where the bootblock loads the program
IMAGE_SIZE      equ     (MAP_LOW-IMAGE_BASE+3)&-4
RELOC_ROOM      equ     IMAGE_SIZE+RELOC_LEN    ; (LoadFile loads exactly the file's bytes)
EnhRelocate:
        tst.b   (RelocDone).l
        bne.w   er_out
        tst.l   (FileRelocs+4).l                ; (a build without the relocation file)
        beq.w   er_out
        lea.l   (MACHINE_INFO).l,a0
        cmpi.l  #'GNGM',MI_MAGIC(a0)
        bne.w   er_out
        cmpi.l  #$80000,MI_CHIP_UPPER(a0)       ; 1MB of chip RAM (more than 512K): the program
        bhi.w   er_out                          ; stays
        movem.l 24(a0),d0-d1                    ; fast RAM: lower, upper
        bsr.w   er_fit
        beq.b   er_go
        lea.l   (MACHINE_INFO).l,a0
        movem.l 16(a0),d0-d1                    ; slow RAM
        bsr.w   er_fit
        bne.w   er_out
er_go:  move.l  d0,d6                           ; d6 = where it goes
        lea.l   (IMAGE_BASE).w,a1
        movea.l d0,a2
        move.w  #IMAGE_SIZE/4-1,d7
er_copy:
        move.l  (a1)+,(a2)+
        dbra    d7,er_copy
        move.l  a2,-(a7)                        ; the relocation file after it
        lea.l   (FileRelocs).l,a1
        move.l  a2,(a1)
        move.l  d6,-(a7)
        jsr     (LoadFile).l
        move.l  (a7)+,d6
        movea.l (a7)+,a3
        movea.l d6,a2                           ; the program's addresses: + (d6 - $80)
        move.l  d6,d5
        sub.l   #IMAGE_BASE,d5
        bsr.w   ApplyRelocs                     ; (a3 = the music package's table after it)
        move.l  d6,d0                           ; in the copy: the music table, done, and on
        add.l   #MusicRelocs-IMAGE_BASE,d0
        movea.l d0,a0
        move.l  a3,(a0)
        move.l  d6,d0
        add.l   #RelocDone-IMAGE_BASE,d0
        movea.l d0,a0
        st.b    (a0)
        addq.l  #4,a7                           ; (Start called this)
        add.l   #Start-IMAGE_BASE,d6
        movea.l d6,a0
        jmp     (a0)
er_out:
        rts
; d0 = lower, d1 = upper end of a region -> d0 = where the program would go (on 256 bytes);
; Z set if it fits
er_fit:
        tst.l   d1
        beq.b   er_no
        add.l   #$FF,d0
        and.l   #$FFFFFF00,d0
        move.l  d1,d2
        sub.l   d0,d2
        bls.b   er_no
        cmp.l   #RELOC_ROOM,d2
        bcs.b   er_no
        moveq   #0,d2
        rts
er_no:  moveq   #1,d2
        rts

; ApplyRelocs - a3 = a table (count.l, then word gaps between the offsets of the longs to
; move), a2 = the image's base, d5 = how far it moved -> a3 = after the table
ApplyRelocs:
        move.l  (a3)+,d7
        beq.b   ar_done
ar_next:
        moveq   #0,d0
        move.w  (a3)+,d0
        adda.l  d0,a2
        add.l   d5,(a2)
        subq.l  #1,d7
        bne.b   ar_next
ar_done:
        rts

RelocDone:
        dc.b    0                               ; this is the copy (EnhRelocate)
        even
MusicRelocs:
        dc.l    0                               ; the music package's relocation table

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

