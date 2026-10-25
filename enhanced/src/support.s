;---------------------------------------------------------------------------
; ==================================================================
; One program for every machine (enhanced branch)
; ==================================================================
; support.s - included by gng_game.s: the enhanced game's start-up and loading
; code that has no place in the original's routines (enhanced/docs/FEATURES.md, MEMORY.md):
;   ReadProfile       the machine (Profile) from the bootblock's description
;   LoadSound         the sound package for the machine
;   LoadLevelTables   a level's map tables file
;   LoadEnemySets     only the level's sets of the enemy graphics file (LoadOffset)
;   CacheInit         the file cache's memory on an expanded machine
;   LoadFile          a file by its id: from the file cache, or from the disk (LoadDisk, with the
;                     4489_byteloader; FileDir: the disk's file table)
;   IrqLevel1 / 3     the interrupt entries that give the handlers their a6
;   EnhRelocate       the program's move to expansion memory (ApplyRelocs)
;   CacheGraphics     with 1MB of chip RAM: every graphic cached with masks (BuildMaskedGfx),
;                     and the test page's BOB viewer loaded (bobviewer.s, at VIEWER_ORG)
; ==================================================================
; ReadProfile - Start, first thing: Profile from the bootblock's machine description
; (MACHINE_INFO). With 1MB or more of chip RAM (any chip RAM above $80000: Kickstart 1.3 keeps the
; top of a 1MB machine's chip RAM for itself and lists it as ending at $FE800): PF_CACHE, PF_MUSIC - the 1MB program's
; features (PF_EVERY, drawing every frame, is set for every machine). With less chip RAM:
; PF_MUSIC as well (the 1MB package where the program was, if it moved to an expansion; else
; the 512K music package, LoadSound). Without a description (the original bootblock): the
; 512K program, effects only. Also the two texts the 1MB program has its own way: the credit line
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
        move.b  #(1<<PF_MUSIC)|(1<<PF_EVERY),(Profile).l   ; music on every machine
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
; LoadSound - the sound package: with 1MB of chip RAM (PF_CACHE) the 1MB one (music and
; effects, for MUSIC1M_FILE in upper chip RAM); with the program moved to an expansion the 1MB
; one where the program was (MUSICB_FILE); otherwise, with PF_MUSIC, the 512K music package
; (the 512K effects and the tunes) and without it the 512K effects package, at MUSIC_FILE.
;---------------------------------------------------------------------------
LoadSound:
        lea.l   (FileMusic).l,a1
        btst    #PF_MUSIC,(Profile).l
        beq.w   LoadFile
        btst    #PF_CACHE,(Profile).l
        bne.b   ls_music
        tst.b   (RelocDone).l
        bne.b   ls_music
        lea.l   (FileMusic512).l,a1             ; 512K: the music package at MUSIC_FILE
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
FileMusic512:
	FENTRY	MUSIC_FILE,MUSIC512_LEN,FID_MUSIC512    ; the music for 512K (enhanced/sound/gng_music_512k.s)
FileViewer:
	FENTRY	VIEWER_ORG,VIEWER_LEN,FID_VIEWER        ; the BOB viewer (1MB of chip RAM: CacheGraphics)
MfmBuf:
        dc.l    MFM_BUFFER                      ; LoadFile's MFM buffer (the progress map sets PM_MFM)

;---------------------------------------------------------------------------
; The file cache. On a machine with memory to spare, the files the game loads again and
; again are kept after their first load, and later loads copy them from there instead of
; reading the disk:
;  * the program moved to slow / fast RAM (512K of chip RAM): the rest of that region, after
;    the program and its relocation file: the enemy graphics (all of it, the first time a
;    level needs any of it; LoadEnemySets then copies the level's sets), the small BOBs, the
;    progress map, the levels' tile and table files;
;  * 1MB of chip RAM or more (PF_CACHE: the graphics are cached already): the largest of the
;    chip RAM above the upper chip RAM caches and the BOB viewer (VIEWER_ORG + VIEWER_LEN) and
;    the slow and fast RAM regions, which nothing else uses then: the levels' tile and table
;    files.
; Files are kept first come, first served, as long as there is room (they never change).
; CacheInit (Start, after ReadProfile) finds the memory; nothing is kept without a machine
; description or on a plain 512K machine.
;---------------------------------------------------------------------------
CACHE_MOVED     equ     (1<<FID_SMALLBOBS)|(1<<FID_ENEMYBOBS)|(1<<FID_PROGMAP)|($7F<<FID_LEVEL0)|($7F<<FID_TABLES0)
CACHE_CHIP      equ     ($7F<<FID_LEVEL0)|($7F<<FID_TABLES0)

CacheInit:
        movem.l d0-d6/a0-a1,-(a7)
        clr.l   (CacheEnd).l
        lea.l   (MACHINE_INFO).l,a0
        cmpi.l  #'GNGM',MI_MAGIC(a0)
        bne.b   .out
        tst.b   (RelocDone).l
        beq.b   .chip
        move.l  (RelocBase).l,d0                ; moved: the copy's base ...
        movem.l 24(a0),d1-d2                    ; ... in the fast RAM region, else the slow one
        cmp.l   d1,d0
        bcs.b   .slow
        cmp.l   d2,d0
        bcs.b   .region
.slow:  move.l  20(a0),d2
.region:
        add.l   #RELOC_ROOM+3,d0                ; after the program and its relocation file
        and.w   #-4,d0
        move.l  #CACHE_MOVED,d3
        bra.b   .set
.chip:  btst    #PF_CACHE,(Profile).l
        beq.b   .out
        move.l  #VIEWER_ORG+VIEWER_LEN,d0       ; chip RAM above the upper caches and the viewer ...
        move.l  MI_CHIP_UPPER(a0),d2
        movem.l 16(a0),d1/d4                    ; ... or slow RAM ...
        bsr.b   .bigger
        movem.l 24(a0),d1/d4                    ; ... or fast RAM: the largest
        bsr.b   .bigger
        addq.l  #3,d0
        and.w   #-4,d0
        move.l  #CACHE_CHIP,d3
.set:   cmp.l   d0,d2
        bls.b   .out
        move.l  d0,(CachePtr).l
        move.l  d2,(CacheEnd).l
        move.l  d3,(CacheMask).l
.out:   movem.l (a7)+,d0-d6/a0-a1
        rts
.bigger:                                        ; d1-d4 a region (upper 0: none): if larger than d0-d2, it
        tst.l   d4
        beq.b   .keep
        move.l  d4,d5
        sub.l   d1,d5
        move.l  d2,d6
        sub.l   d0,d6
        cmp.l   d6,d5
        bls.b   .keep
        move.l  d1,d0
        move.l  d4,d2
.keep:  rts

;---------------------------------------------------------------------------
; LoadFile - a1 -> file record (FENTRY: dest.l, length.l, file id.w) -> a5 = the end of the
; loaded data, a0 = CUSTOM (as the original's track loader left them); other registers kept.
; LoadOffset: start this far into the file (LoadEnemySets). A file in the cache (CacheTable)
; is copied from there; a file the cache keeps (CacheMask) is loaded whole into the cache the
; first time, if there is room, then copied; otherwise it is read from the disk (LoadDisk).
;---------------------------------------------------------------------------
LoadFile:
        movem.l d0-d7/a1-a4/a6,-(a7)
        tst.l   (CacheEnd).l
        beq.w   lf_disk
        moveq   #0,d4
        move.w  8(a1),d4                        ; file id
        move.l  (CacheMask).l,d0
        btst    d4,d0
        beq.w   lf_disk
        lea.l   (CacheTable).l,a2
        move.w  d4,d1
        lsl.w   #2,d1
        move.l  (a2,d1.w),d2                    ; in the cache?
        bne.b   lf_copy
        lea.l   (FileDir).l,a3                  ; no: the whole file, if there is room
        cmpi.l  #'GNGF',(a3)
        bne.w   lf_disk
        move.w  d4,d0
        lsl.w   #3,d0
        move.l  FT_ENTRY+4(a3,d0.w),d3          ; its length
        move.l  (CachePtr).l,d2
        move.l  d3,d0
        addq.l  #3,d0
        and.w   #-4,d0
        add.l   d2,d0
        cmp.l   (CacheEnd).l,d0
        bhi.b   lf_disk
        move.l  d0,(CachePtr).l
        move.l  d2,(a2,d1.w)
        move.l  (LoadOffset).l,-(a7)
        clr.l   (LoadOffset).l
        movem.l d2/a1,-(a7)
        lea.l   (CacheRec).l,a1
        move.l  d2,(a1)
        move.l  d3,4(a1)
        move.w  d4,8(a1)
        bsr.w   LoadDisk
        movem.l (a7)+,d2/a1
        move.l  (a7)+,(LoadOffset).l
lf_copy:                                        ; d2 = the file in the cache
        movea.l d2,a0
        adda.l  (LoadOffset).l,a0
        movea.l (a1),a5                         ; destination
        move.l  4(a1),d5                        ; length
        move.l  a0,d0
        move.l  a5,d1
        or.l    d1,d0
        btst    #0,d0
        bne.b   lf_bytes
        move.l  d5,d0
        lsr.l   #2,d0
        bra.b   lf_lnext
lf_long:
        move.l  (a0)+,(a5)+
lf_lnext:
        subq.l  #1,d0
        bcc.b   lf_long
        moveq   #3,d0
        and.l   d5,d0
        bra.b   lf_bnext
lf_bytes:
        move.l  d5,d0
        bra.b   lf_bnext
lf_byte:
        move.b  (a0)+,(a5)+
lf_bnext:
        subq.l  #1,d0
        bcc.b   lf_byte
        lea.l   CUSTOM,a0
        movem.l (a7)+,d0-d7/a1-a4/a6
        rts
lf_disk:
        movem.l (a7)+,d0-d7/a1-a4/a6
        bra.w   LoadDisk
CachePtr:       dc.l    0               ; the cache's free memory: from here ...
CacheEnd:       dc.l    0               ; ... to here (0: no cache)
CacheMask:      dc.l    0               ; the file ids it keeps
CacheTable:     dcb.l   FID_COUNT,0     ; where each file is kept (0: not)
CacheRec:       dc.l    0,0             ; a file record for loading a whole file into the cache
                dc.w    0

;---------------------------------------------------------------------------
; LoadDisk - LoadFile from the disk.
; The disk is an ordinary AmigaDOS-format disk (11 sectors a track) with a file table at
; FT_OFFSET (boot_4489.s; build_game.py writes it): read once into FileDir, then each file is
; loaded from its offset by the 4489_byteloader (ByteLoader), the exact number of bytes. A
; failed load is tried again until it works (after 8 failures COLOR00 shows red).
; Every load reads the drive the game was booted from (BootDrive: the bootblock's machine
; description, version 2, read at the first load; DF0 with an older one or none).
; The byteloader uses a6, so the interrupt handlers load a6 themselves (IrqLevel1/3).
;---------------------------------------------------------------------------
LoadDisk:
        movem.l d0-d7/a1-a4/a6,-(a7)
        movea.l (a1),a5                         ; destination
        move.l  4(a1),d5                        ; length
        moveq   #0,d4
        move.w  8(a1),d4                        ; file id
        lea.l   (FileDir).l,a2
        cmpi.l  #'GNGF',(a2)                    ; the file table, the first time
        beq.b   lf_dir
        lea.l   (MACHINE_INFO).l,a0             ; and the drive booted from: the bootblock's
        moveq   #0,d0                           ; description (version 2), still intact at the
        cmpi.l  #'GNGM',MI_MAGIC(a0)            ; first load; DF0 without one
        bne.b   lf_drive
        cmpi.b  #2,MI_VERSION(a0)
        bcs.b   lf_drive
        move.l  MI_DRIVE(a0),d0
        andi.w  #3,d0
lf_drive:
        move.l  d0,(BootDrive).l
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
        add.l   (LoadOffset).l,d0               ; (from this far into the file: LoadEnemySets)
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
        move.l  (BootDrive).l,d2                ; the drive booted from (LoadDisk's first load)
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
LoadOffset:
        dc.l    0                               ; LoadFile: where in the file to start (normally 0)
BootDrive:
        dc.l    0                               ; the drive the disk is read from: 0-3 (DF0-DF3)

;---------------------------------------------------------------------------
; LoadEnemySets - LoadLevel (no PF_CACHE): the level's BOB sets (LevelBobSetMask) from the
; enemy graphics file, each to its place in SCREEN_0 as the whole file would put it, without
; the sets the level does not use: the whole file is 118,850 bytes, a level's sets 22-65 KB.
; Sets less than a track (5,632 bytes) apart in the file load as one piece, the gap with them
; (into its place: nothing else is there), as the disk reads whole tracks anyway
; (BobSetFileOrder: the sets by their offset in the file).
;---------------------------------------------------------------------------
LoadEnemySets:
        movem.l d0-d7/a0-a5,-(a7)
        move.w  g_Level(a6),d0
        lsl.w   #2,d0
        lea.l   (LevelBobSetMask).l,a0
        move.l  (a0,d0.w),d6                    ; the level's sets
        lea.l   (BobSetFileOrder).l,a2
        lea.l   (BobSetOffsets).l,a3
        lea.l   (BobSetSizes).l,a4
        moveq   #0,d2                           ; the piece: its offset in the file,
        moveq   #0,d3                           ; its length (0: none yet)
.next:  moveq   #0,d7
        move.b  (a2)+,d7                        ; the next set in the file ($FF: the end)
        bmi.b   .last
        btst    d7,d6
        beq.b   .next
        move.w  d7,d0
        add.w   d0,d0
        moveq   #0,d1
        move.w  (a4,d0.w),d1                    ; its size
        beq.b   .next
        add.w   d0,d0
        move.l  (a3,d0.w),d0                    ; its offset
        tst.l   d3
        beq.b   .start
        move.l  d0,d4
        sub.l   d2,d4
        sub.l   d3,d4                           ; the gap after the piece
        cmp.l   #11*512,d4                      ; under a track: the piece grows to take it in
        bcc.b   .flush
        add.l   d4,d3
        add.l   d1,d3
        bra.b   .next
.flush: bsr.b   .load
.start: move.l  d0,d2
        move.l  d1,d3
        bra.b   .next
.last:  tst.l   d3
        beq.b   .done
        bsr.b   .load
.done:  movem.l (a7)+,d0-d7/a0-a5
        rts
.load:  movem.l d0-d1/a0-a2,-(a7)               ; the piece d2, d3 to SCREEN_0 + d2
        lea.l   (EnemyPiece).l,a1
        move.l  #SCREEN_0,(a1)
        add.l   d2,(a1)
        move.l  d3,4(a1)
        move.l  d2,(LoadOffset).l
        jsr     (LoadFile).l
        clr.l   (LoadOffset).l
        movem.l (a7)+,d0-d1/a0-a2
        rts
EnemyPiece:
        dc.l    0,0                             ; a file record for a piece (destination, length)
        dc.w    FID_ENEMYBOBS
BobSetFileOrder:
	dc.b	19,6,1,5,12,17,2,13,8,0,18,4,20,9,10,3,11,14,7,15,$FF	; the sets by their offset in the file
        even
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
        dc.l    0                               ; the a6 the level 1 handler interrupted
IrqA6L3:
        dc.l    0                               ; ... and the level 3 handler
FileTables:                                     ; the levels' map table files (LoadLevelTables)
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
        move.l  d6,d0                           ; and where it is (CacheInit)
        add.l   #RelocBase-IMAGE_BASE,d0
        movea.l d0,a0
        move.l  d6,(a0)
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

RelocBase:
        dc.l    0                               ; the moved copy's base (EnhRelocate)
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
        lea.l   (FileViewer).l,a1               ; the test page's BOB viewer (bobviewer.s): only here
        bsr.w   LoadFile
        st.b    (ViewerOn).l
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
