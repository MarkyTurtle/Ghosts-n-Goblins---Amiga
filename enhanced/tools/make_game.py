"""Make src/gng_game.s - the one program for every machine - from the merged source gng_main.s
(both original programs, ifd BUILD_1MB blocks). Kept so the step can be repeated and checked;
once the scroller is folded in, gng_game.s is edited by hand.

The 512K view is the base (memory map, absolute addresses). Each ifd block where the 1MB
program differs in something other than addressing becomes a choice made at run time from
Profile (set by ReadProfile from the bootblock's machine description):
 * sound: the 1MB program's tune and effect calls run only with its music package (PF_MUSIC);
   otherwise the 512K code runs, so each profile does exactly what its original did. The
   choice keeps the condition codes (move sr / move ccr), so code after it sees the flags its
   original saw (all game logic runs in supervisor mode, in interrupts);
 * the rest by hand (below): caches, masked drawing, level loading, frame rate, texts.

  python3 make_game.py        (then build_game.py, compare_game.py)"""
import os, re, sys
import srcedit

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, '..', '..')
OUT = os.path.join(HERE, '..', 'src', 'gng_game.s')

# block numbers (srcedit.blocks order in gng_main.s) of the sound differences ...
SOUND = {69, 70, 71, 72, 73, 79, 80, 81, 82, 83, 84, 88, 90, 93, 94, 106, 107, 108, 112, 113, 134, 135,
         136, 137, 138, 139, 141, 142, 144, 145, 146, 148, 149, 150, 151, 152, 153, 156}
# ... and of those edited by hand: markers ';@@ PROFILE n' / ';@@ END n' around the 512K lines
MARK = {58, 59, 60, 61, 62, 63, 64, 65, 66, 68, 76, 77, 78, 85, 86, 87, 91, 95, 96, 117, 118, 119, 120,
        121, 122, 123, 124, 125, 127, 128, 129, 130, 131, 132, 133, 154}
NBLOCKS = 158

HEADER = """; Ghosts'n Goblins (Elite, 1990, v3) - main program, ONE PROGRAM FOR EVERY MACHINE
; (enhanced branch). Loaded raw by the bootblock to $80, entered at $A0, on every machine.
; Made by enhanced/tools/make_game.py from the merged gng_main.s; build: build_game.py.
;
; The original disk has two programs: the 512K one and the expanded-memory (1MB) one, which
; caches the graphics with their masks (one-blit BOBs), keeps the progress map and plays music.
; This is both in one: the 512K program (its memory map, absolute addresses), plus the 1MB
; program's features, chosen at start-up from the machine description the bootblock leaves at
; MACHINE_INFO (see enhanced/docs/SCROLLER.md):
;   Profile bit PF_CACHE  - 1MB of chip RAM or more: the upper 512K of chip RAM ($80000-) holds
;                           the music package, the progress map and the graphics caches with
;                           masks; BOBs are drawn in one blit (DrawBobMasked), levels load no
;                           graphics, frame offsets are doubled (CacheGraphics)
;   Profile bit PF_MUSIC  - the 1MB music package is loaded: its tunes and its extra effects
;   Profile bit PF_EVERY  - draw every frame (the 1MB program has no odd-frame test)
; Otherwise the program does exactly what the 512K original does. Where the two originals differ,
; both versions are here, chosen at run time (search for 'Profile').
; The address column still gives the original addresses (512K/1MB)."""


def view(lines, one):
    out, st = [], [True]
    for l in lines:
        m = re.match(r'^\t(ifd|ifnd)\tBUILD_1MB', l)
        if m: st.append(st[-1] and ((m.group(1) == 'ifd') == one)); continue
        if l.startswith('\telse') and len(st) > 1: st[-1] = (not st[-1]) and st[-2]; continue
        if l.startswith('\tendc') and len(st) > 1: st.pop(); continue
        if st[-1]: out.append(l)
    return out


I = lambda c, cm='': ('        ' + c).ljust(48) + ('; ' + cm if cm else '')


# jump-table entries (a list of bra.w): the entry stays one bra.w, to the choice holding its 1MB target
JUMPTAB = {111, 143, 147}


def sound_choice(n, one, five):
    """the 1MB lines with PF_MUSIC, else the 512K lines; the flags kept for both"""
    out = [f'snd{n}_go:', I('move    sr,-(a7)', 'sound: the 1MB code with its music package, else the 512K code'),
           I('btst    #PF_MUSIC,(Profile).l'), I(f'beq.b   snd{n}_512'), I('move    (a7)+,ccr')]
    out += one + [I(f'bra.w   snd{n}_end'), f'snd{n}_512:', I('move    (a7)+,ccr')] + five + [f'snd{n}_end:']
    return out


def first_pass(src):
    L = src.split('\n')
    bl = {b[0]: (n, b) for n, b in enumerate(srcedit.blocks(L), 1)}
    assert len(bl) == NBLOCKS, f'{len(bl)} blocks in gng_main.s, expected {NBLOCKS}: renumber SOUND/MARK'
    owner = {}                               # 1MB label -> the sound choice that holds it
    for k, (n, b) in bl.items():
        if n in SOUND:
            for l in srcedit.sides(L, b)[0]:
                m = re.match(r'^(l1m_[0-9A-F]{5}):', l)
                if m: owner[m.group(1)] = n
    out, k = [], 0
    while k < len(L):
        if k in bl:
            n, b = bl[k]; one, five = srcedit.sides(L, b)
            if n in JUMPTAB:
                (line,) = [l for l in one if srcedit.code(l)]
                out.append(re.sub(r'\b(l1m_[0-9A-F]{5})\b', lambda m: f'snd{owner[m.group(1)]}_go', line))
            elif n in SOUND: out += sound_choice(n, one, five)
            elif n in MARK: out += [f';@@ PROFILE {n}'] + five + [f';@@ END {n}']
            else: out += five
            k = b[2] + 1; continue
        out.append(L[k]); k += 1
    i = out.index('; HOW TO READ THIS FILE') - 1
    return '\n'.join(HEADER.split('\n') + out[i:]).replace('\tinclude\t"gng_equates.i"', '\tinclude\t"gng_game.i"')


def grab(V1, start, end, suffix):
    """a routine of the 1MB view, its own labels renamed (so it can live beside the 512K one)"""
    i = next(k for k, l in enumerate(V1) if l.startswith(start + ':'))
    j = next(k for k, l in enumerate(V1) if k > i and l.startswith(end))
    t = '\n'.join(V1[i:j])
    for d in sorted(set(re.findall(r'^(l1?m?_[0-9A-F]{5}):', t, re.M)), key=len, reverse=True):
        t = re.sub(r'\b' + d + r'\b', d + suffix, t)
    assert 'g_BaseAddr' not in t
    return t


class Src:
    def __init__(self, s): self.s = s
    def block(self, n):
        a = self.s.index(f';@@ PROFILE {n}\n'); e = self.s.index(f';@@ END {n}\n') + len(f';@@ END {n}\n')
        return a, e, self.s[a + len(f';@@ PROFILE {n}\n'):e - len(f';@@ END {n}\n')]
    def rep(self, n, new):
        a, e, inner = self.block(n); self.s = self.s[:a] + new.replace('{5K}', inner) + self.s[e:]
    def sub(self, old, new, count=1):
        assert self.s.count(old) == count, (old[:70], self.s.count(old)); self.s = self.s.replace(old, new)
    def resub(self, pat, new):
        self.s, n = re.subn(pat, new, self.s); assert n, pat


def level_tables(S):
    """the map cells' tables move to per-level files (build_game.py makes them from the original
    program): BlockTiles and CellTiles leave the program; MapTileAt and the scroller's DrawTile
    find a cell's slot in the level's table (LEVEL_SLOTS)"""
    s = S.s
    i = s.index('BlockTiles:\n'); j = s.index(';---------------------------------------------------------------------------\n; TileAttr - 4 banks')
    s = s[:i] + '; (BlockTiles: in the per-level table files now - LEVEL_BLOCKS, LoadLevelTables)\n\n' + s[j:]
    i = s.index('CellTiles:\n'); j = s.index(';---------------------------------------------------------------------------\n; HUNK_END and padding.')
    s = s[:i] + '; (CellTiles: in the per-level table files now - LEVEL_CELLS, LoadLevelTables)\n\n' + s[j:]
    S.s = s
    S.sub("""        swap    d0                              ; 05AA6/05A26
        lsl.w   #$6,d0                          ; 05AA8/05A28
        lea.l   BlockTiles(pc),a1               ; 05AAA/05A2A
        adda.w  d0,a1                           ; 05AAE/05A2E
""", """        swap    d0                              ; 05AA6/05A26
        andi.w  #$FF,d0                         ; the cell's slot in this level's tables
        lea.l   (LEVEL_SLOTS).l,a1
        move.b  (a1,d0.w),d0
        lsl.w   #$6,d0                          ; 05AA8/05A28
        lea.l   (LEVEL_BLOCKS).l,a1             ; its BlockTiles
        adda.w  d0,a1                           ; 05AAE/05A2E
""")


def hand_edits(S, V1):
    level_tables(S)
    S.sub("\torg\t$80\n", "\tifd\tRELOC_ORG\t\t; build_game.py's relocation pass\n\torg\tRELOC_ORG\n\telse\n\torg\t$80\n\tendc\n"
          "\tifnd\tRELOC_LEN\nRELOC_LEN\tequ\t0\t\t; the relocation file (EnhRelocate), from build_game.py\n\tendc\n"
          "RELOC_TRACK\tequ\t17\t\t; (the original 1MB program's tracks, free on this disk)\n")
    hdr = lambda t: ';---------------------------------------------------------------------------\n' + t + \
        '\n;---------------------------------------------------------------------------\n'
    # --- Start: profile, caches, sound, level 0 --------------------------------------
    S.sub("        move    a6,usp                          ; 05B2A/       USP = globals block (user-mode stack grows down from here)\n",
          "        move    a6,usp                          ; 05B2A/       USP = globals block (user-mode stack grows down from here)\n"
          + I('bsr.w   ReadProfile', 'what machine this is (Profile)') + '\n'
          + I('bsr.w   LoadSound', 'the sound package first: whole tracks run past its end, into') + '\n'
          + I('', 'buffers loaded after it (the 512K effects at MAP_LOW, the music where the program was)') + '\n')
    S.sub("\nStart:\n", "\nStart:\n" + I('jsr     EnhRelocate', 'with an expansion and under 1MB of chip RAM: the program moves there') + '\n')
    for n in (58, 59, 60, 62, 63, 64, 65): S.rep(n, '')
    S.rep(61, I('bsr.w   CacheGraphics', '1MB+ chip: cache the graphics with masks, the progress map') + '\n')
    S.sub("""        lea.l   FileMusic(pc),a1                ; 05D2A/05D76
        bsr.w   LoadFile                        ; 05D2E/05D7A  load music/sfx player (tracks 126-131) -> $28E54
""", '')
    S.sub("        bsr.w   LoadFile                        ; 05D36/05D94  load FAST copyright warning screen (tracks 82-83, RLE packed) -> $4DC68\n",
          "        bsr.w   LoadFile                        ; 05D36/05D94  load FAST copyright warning screen (tracks 82-83, RLE packed) -> $4DC68\n"
          + I('btst    #PF_CACHE,(Profile).l', 'the 1MB program loads level 0 here, so the title') + '\n'
          + I('beq.b   st_lv0late', 'shows the level behind it; the 512K one after InitHardware') + '\n'
          + I('lea.l   FileLevel0(pc),a1') + '\n' + I('bsr.w   LoadFile') + '\nst_lv0late:\n')
    S.rep(66, I('btst    #PF_CACHE,(Profile).l') + '\n' + I('bne.b   l_05E36', '(loaded before)') + '\n{5K}')
    S.rep(96, I('movea.l (MusicPlayerPtr).l,a1') + '\n' + I('move.l  a1,(VEC_SPURIOUS).w', 'vector $60 = the sound driver loaded (LoadSound)') + '\n')
    S.rep(68, '{5K}'); S.rep(117, '{5K}')         # patched by ReadProfile
    # --- the odd-frame test --------------------------------------------------------------
    S.rep(85, '{5K}'); S.rep(87, '{5K}')
    S.rep(86, 'l_06E76:\n' + I('btst    #PF_EVERY,(Profile).l', 'every frame (1MB profile): no odd-frame test') + '\n'
          + I('bne.b   l_06E80') + '\n' + """        btst    #$0,g_GameFrame+1(a6)           ; 06E76/       even frames: no camera or drawing
        beq.w   l_07192                         ; 06E7C/
l_06E80:
""")
    # --- key pickup: the 512K effect when there is no music -----------------------------
    S.rep(95, I('btst    #PF_MUSIC,(Profile).l', 'with music the 1MB game plays the boss tune instead (Key_Wait)') + '\n'
          + I('bne.b   kt_nosfx') + '\n{5K}kt_nosfx:\n')
    # --- BuildFrameTable: with the cache the frame table points into it -----------------
    S.rep(133, I('btst    #PF_CACHE,(Profile).l', 'the cache is chip RAM and stays: the frame') + '\n'
          + I('bne.b   bft_cached', 'table points into it (the 1MB program copies)') + '\n{5K}'
          + I('bra.b   l_0C46E') + '\nbft_cached:\n' + I('move.l  a1,-$4(a0)') + '\n')
    # --- LoadLevel ------------------------------------------------------------------------
    S.rep(76, I('btst    #PF_CACHE,(Profile).l', 'cache: the graphics are already in memory') + '\n' + I('bne.b   ll_cached') + '\n{5K}ll_cached:\n')
    S.rep(77, '{5K}' + I('btst    #PF_CACHE,(Profile).l') + '\n' + I('beq.b   ll_sets') + '\n'
          + I('lea.l   (ENEMY_GFX_CACHE).l,a5', 'the masked enemy sets') + '\nll_sets:\n')
    S.rep(78, I('btst    #PF_CACHE,(Profile).l') + '\n' + I('beq.b   ll_small') + '\n' + I('lea.l   (SMALLBOB_CACHE).l,a5', 'the masked small sets') + '\nll_small:\n')
    # --- ProgressMap, Astaroth_Dying --------------------------------------------------------
    S.rep(91, I('btst    #PF_MUSIC,(Profile).l') + '\n' + I('beq.b   pm_nomus') + '\n'
          + I('moveq   #TUNE_START,d0', 'with music: the start tune') + '\n' + I('bsr.w   PlayMusic') + '\npm_nomus:\n'
          + I('btst    #PF_CACHE,(Profile).l') + '\n' + I('beq.b   pm_load') + '\n'
          + I('lea.l   (PROGRESS_MAP_CACHE).l,a0', '1MB: the map from the cache') + '\n' + I('bra.b   pm_have') + '\npm_load:\n{5K}pm_have:\n')
    S.rep(154, I('btst    #PF_MUSIC,(Profile).l') + '\n' + I('beq.b   ad_explode') + '\n'
          + I('moveq   #TUNE_ASTAROTH_BEATEN,d0', 'with music: the final tune (the explosion starts next frame)') + '\n'
          + I('bra.w   PlayMusic') + '\nad_explode:\n{5K}')
    # --- DrawBob / scenery: masked versions beside the 512K ones ----------------------------
    for n in (118, 119, 120, 121, 122, 123, 124, 127, 128, 129, 130, 131): S.rep(n, '{5K}')
    S.sub("\nDrawBob:\n", "\nDrawBob:\n" + I('btst    #PF_CACHE,(Profile).l', 'cached graphics carry their masks: one blit') + '\n' + I('bne.w   DrawBobMasked') + '\n')
    S.sub("\nDrawSceneryOnRedraw:\n", "\nDrawSceneryOnRedraw:\n" + I('btst    #PF_CACHE,(Profile).l') + '\n' + I('bne.w   DrawSceneryMasked') + '\n')
    draw = grab(V1, 'DrawBob', 'WaitBlitIRQ', '_m').replace('DrawBob:', 'DrawBobMasked:', 1)
    scen = grab(V1, 'DrawSceneryOnRedraw', 'BuildMaskedGfx', '_m').replace('DrawSceneryOnRedraw:', 'DrawSceneryMasked:', 1)
    bmg = grab(V1, 'BuildMaskedGfx', 'NullRoutine', '')
    S.rep(125, hdr("; PlayMusic - d0 = tune number (see sound/SOUND.md): calls the sound driver through\n"
                   "; vector $60 with command 1 (d0.l = tune<<16 | 1). Only with the music package (PF_MUSIC);\n"
                   "; the callers choose by profile, this is a safety net.")
          + "PlayMusic:\n" + I('btst    #PF_MUSIC,(Profile).l') + '\n' + I('beq.b   pmu_none') + '\n'
          + I('move.l  a1,-(a7)') + '\n' + I('swap    d0') + '\n' + I('addq.w  #$1,d0') + '\n' + I('movea.l (VEC_SPURIOUS).w,a1') + '\n'
          + I('jsr     (a1)') + '\n' + I('movea.l (a7)+,a1') + '\npmu_none:\n' + I('rts') + '\n\n'
          + hdr("; DrawBobMasked - DrawBob for graphics that carry their masks (the cache, PF_CACHE):\n; the 1MB program's DrawBob") + draw + '\n')
    S.rep(132, hdr("; DrawSceneryMasked - DrawSceneryOnRedraw for masked graphics (the 1MB program's)") + scen + '\n' + bmg + '\n')
    # --- draw queues: the item / shot graphics wherever they are ---------------------------------
    S.resub(r'lea\.l   \(ITEM_GFX_BUF\)\.l,a1  ', 'movea.l (ItemGfxPtr).l,a1   ')
    S.resub(r'lea\.l   \(ESHOT_GFX_BUF\)\.l,a1 ', 'movea.l (EShotGfxPtr).l,a1  ')
    # --- the 1MB music file, then the support routines and variables (after the file table:
    # tools/disk/mkdisk.py finds the table by LevelFileIndex just before it) -------------------------
    S.sub("""FileLevel6:
	FENTRY	LEVEL_FILE,$019A0,108                  ; tracks 108-109: level 6 tiles
""", """FileLevel6:
	FENTRY	LEVEL_FILE,$019A0,108                  ; tracks 108-109: level 6 tiles
FileMusic1M:
	FENTRY	MUSIC1M_FILE,$1B394,64                 ; tracks 64-81: the 1MB music package (PF_MUSIC), for upper chip RAM
FileRelocs:
	FENTRY	0,RELOC_LEN,RELOC_TRACK                ; the relocation tables (EnhRelocate; build_game.py)

""" + open(os.path.join(HERE, 'make_game_support.s')).read())
    # --- FRAME runs, for CacheGraphics ---------------------------------------------------------
    L = S.s.split('\n'); runs = []; cur = None
    for k, l in enumerate(L):
        if re.match(r'^\s+FRAME\s', l):
            if cur is None: cur = [k, k]; runs.append(cur)
            cur[1] = k
        elif l.strip() and not l.strip().startswith(';') and not re.match(r'^[A-Za-z]\w*:', l): cur = None
    assert len(runs) == 2, runs
    for n, (a, b) in reversed(list(enumerate(runs, 1))):
        L.insert(b + 1, f'FrameOffsets{n}End:'); L.insert(a, f'FrameOffsets{n}:')
    S.s = '\n'.join(L)
    # --- references out of reach of pc-relative addressing now -----------------------------------
    for lab in ('Satan_AnimWings', 'Satan_AnimFlap', 'FloorProfile', 'Satan_AnimReturnR'):
        S.resub(r'lea\.l   ' + lab + r'\(pc\),(a\d)  ', 'lea.l   (' + lab + r').l,\1')
    S.sub("        move.w  LevelSmallBobMask(pc,d0.w),d0   ; 06884/068DE\n",
          "        lea.l   LevelSmallBobMask(pc),a4        ; (out of reach of an indexed pc read now)\n"
          "        move.w  (a4,d0.w),d0                    ; 06884/068DE\n")
    S.resub(r'bsr\.b   Magician_FaceArthur ', 'bsr.w   Magician_FaceArthur ')
    S.sub("        move.b  WoodyPigLoopOdds(pc,d0.w),d0    ; 0C900/0C838\n",
          "        move.l  a0,-(a7)                        ; (the table is out of reach of an indexed pc\n"
          "        lea.l   WoodyPigLoopOdds(pc),a0         ; read now; a0 kept, the flags as before)\n"
          "        move.b  (a0,d0.w),d0                    ; 0C900/0C838\n"
          "        movea.l (a7)+,a0\n")
    # --- MapTileAt: a cell read past the map and the tables after it is an empty cell ---------------
    # (an object far below the level - Y negative - made the original read its own code as map
    # cells; what it found depended on the program's layout, so the 512K and 1MB programs, and
    # any changed program, behave differently there. compare_game.py fixes the originals alike.)
    S.sub("""        adda.w  d0,a1                           ; 05A8C/05A0C
        move.b  (a1),d0                         ; 05A8E/05A0E
""", """        adda.w  d0,a1                           ; 05A8C/05A0C
        cmpa.l  #FrameOffsets1,a1               ; past the map and the tables after it (the
        bcs.b   mt_inside                       ; original read code there as map cells):
        lea.l   MapCellEmpty(pc),a1             ; an empty cell
mt_inside:
        move.b  (a1),d0                         ; 05A8E/05A0E
""")
    S.sub("\nMapTileAt:\n", "\nMapCellEmpty:\n\tdc.b\t$67\t\t\t; a cell type with nothing in it (MapTileAt)\n\teven\nMapTileAt:\n")
    fold_scroller(S)
    assert ';@@' not in S.s


def fold_scroller(S):
    """the scroller (src/scroller.s, src/scroll.s) in place of the original display code: the
    game's routines call it as the earlier enhanced builds' patches did (src/patches.s)"""
    jmp = lambda label, target, why: S.sub(f'\n{label}:\n', f'\n{label}:\n' + I(f'jmp     {target}', why) + '\n')
    jmp('RedrawScreen', 'EnhRedrawScreen', 'the scroller: draw the pristine buffer')
    jmp('SwapScreens', 'EnhSwapScreens', 'the scroller')
    jmp('ShowBackBuffer', 'EnhShowBackBuffer', 'the scroller')
    jmp('SetBitplanePtrs', 'EnhSetBitplanePtrs', 'the scroller')
    jmp('RestoreBackground', 'EnhRestoreBackground', 'the scroller')
    jmp('DrawBobs', 'EnhDrawBobs', 'the scroller')
    jmp('CameraJump', 'EnhCameraJump', 'the scroller: the same fine-scroll rules, no buffers to rotate')
    jmp('l_0B0D6', 'EnhPrintField', 'playfield text: through the scroller (the ring needs the lines copied)')
    S.sub("        bsr.w   RedrawScreen                    ; 05EAC/05F02  the redraw VblIRQ asked for (user mode)\n",
          I('jsr     EnhRedrawBackground', 'nothing to redraw: the scroller keeps the buffers current') + '\n')
    S.sub("        lea.l   FileCopyrightScreen(pc),a1      ; 05D32/05D88\n",
          I('jsr     EnhInit', 'the scroller\'s records (and the machine description)') + '\n'
          "        lea.l   FileCopyrightScreen(pc),a1      ; 05D32/05D88\n")
    S.sub("        bsr.w   BuildFrameTable                 ; 0689C/068FA\n",
          "        bsr.w   BuildFrameTable                 ; 0689C/068FA\n"
          + I('jsr     BuildLevelMasks', '512K: the one-plane masks of the level\'s images') + '\n')
    S.sub("        bsr.w   RedrawScreen                    ; 0627C/062DA\n",
          I('jsr     EnhRedrawSame', 'the background is unchanged: kept when the pristine buffer holds it') + '\n')
    # end of a level: the original's drawing slowed right down while it printed these, which
    # kept them on screen far longer than their frame counts; at 50 fps they flashed by
    S.sub("        move.b  #$24,g_StateTimer(a6)           ; 0ACDE/0AD42\n",
          "        move.b  #250,g_StateTimer(a6)           ; 'TAKE A KEY FOR COMING IN !': 5 s (the original: 36 frames)\n")
    S.sub("        move.b  #$40,g_StateTimer(a6)           ; 06500/0655E\n",
          "        move.b  #150,g_StateTimer(a6)           ; 'BONUS' and the amount: 3 s (the original: 64 frames)\n")
    S.sub("CheckGameStart:\n        btst    #$7,$bfe001.l                   ; 05F74/05FCA\n",
          "CheckGameStart:\n" + I('jsr     EnhCheatKey', "the title / high scores: 'C' turns the cheat on or off") + '\n'
          "        btst    #$7,$bfe001.l                   ; 05F74/05FCA\n")
    S.sub("        bsr.w   DrawCreditsScreen               ; 05EF0/05F46\n",
          "        bsr.w   DrawCreditsScreen               ; 05EF0/05F46\n" + I('jsr     EnhShowMachine', 'and the memory the bootblock found') + '\n')
    # the timing build: the logic's start and end colour the background
    S.sub("Level1Logic:\n        move.w  #INTF_SOFTINT,CUSTOM+INTREQ     ; 05EB6/05F0C\n",
          "Level1Logic:\n\tifd\tRASTER_BUILD\n" + I('jsr     EnhLogicStart', 'timing build: (does the INTREQ write) grey') + '\n\telse\n'
          "        move.w  #INTF_SOFTINT,CUSTOM+INTREQ     ; 05EB6/05F0C\n\tendc\n")
    for old in ("LogicExit:\n        movem.l (a7)+,d0-d7/a0-a5               ; 06BF2/06C50\n        rte                                     ; 06BF6/06C54\n",):
        S.sub(old, "LogicExit:\n\tifd\tRASTER_BUILD\n" + I('jmp     EnhLogicEnd', 'timing build: black, then this') + '\n\tendc\n' + old[len('LogicExit:\n'):])
    S.sub("        movem.l (a7)+,d0-d7/a0-a5               ; 071E6/0724E\n        rte                                     ; 071EA/07252\n",
          "\tifd\tRASTER_BUILD\n" + I('jmp     EnhLogicEnd') + '\n\tendc\n'
          "        movem.l (a7)+,d0-d7/a0-a5               ; 071E6/0724E\n        rte                                     ; 071EA/07252\n")
    # the scroller's code after the support routines (CacheGraphics' cg_longs ends them):
    # inside the program file, before its end, which the globals overlay at run time
    i = S.s.index('cg_longs:\n'); j = S.s.index('        rts\n', i) + len('        rts\n')
    S.s = S.s[:j] + '\n\tinclude\t"scroller.s"\n' + S.s[j:]


def widen_branches(path):
    """short branches (.b) the inserted code has put out of reach become word branches; assemble
    again until none is left"""
    import subprocess
    vasm = os.environ.get('VASM', 'vasmm68k_mot'); n = 0
    while True:
        r = subprocess.run([vasm, '-Fbin', '-m68000', '-no-opt', '-quiet', '-maxerrors=10000',
                            '-I', os.path.dirname(path), '-o', os.devnull,
                            '-DRASTER_BUILD=1', '-DNASTY_WAIT=1', path],   # (the largest build)
                           capture_output=True, text=True)
        out = r.stdout + r.stderr
        bad = [(int(m.group(2)), m.group(1)) for m in re.finditer(r'error (2029|2030) in line (\d+) of "[^"]*gng_game\.s"', out)]
        if not bad:
            assert 'error' not in out, out[:2000]
            return n
        L = open(path).read().split('\n')
        for k, e in bad:
            if e == '2029':                   # short branch -> word branch; word bsr / bra -> jsr / jmp
                new = re.sub(r'^(\s+b(?:ra|sr|eq|ne|cc|cs|pl|mi|hi|ls|ge|gt|le|lt|vc|vs))\.b(\s)', r'\1.w\2', L[k - 1])
                if new == L[k - 1]:
                    new = re.sub(r'^(\s+)bsr\.w(\s+)(\w+)', r'\1jsr  \2(\3).l', L[k - 1])
                    new = re.sub(r'^(\s+)bra\.w(\s+)(\w+)', r'\1jmp  \2(\3).l', new)
            else:                             # lea x(pc) out of reach -> lea (x).l (no flags either way)
                new = re.sub(r'^(\s+lea\.l\s+)(\w+)\(pc\),(a\d)', r'\1(\2).l,\3', L[k - 1])
                if new == L[k - 1]:           # pea x(pc), move x(pc),... -> (x).l
                    new = re.sub(r'^(\s+\S+\s+)(\w+)\(pc\)', r'\1(\2).l', L[k - 1])
            assert new != L[k - 1], L[k - 1]
            L[k - 1] = new; n += 1
        open(path, 'w').write('\n'.join(L))


def main():
    src = open(os.path.join(ROOT, 'gng_main.s')).read()
    V1 = view(src.split('\n'), True)
    S = Src(first_pass(src))
    hand_edits(S, V1)
    S.sub("""ll_cached:
        lea.l   LevelFileIndex(pc),a1           ; 06842/06898
""", """ll_cached:
        move.w  g_Level(a6),d0                  ; the level's map tables (LoadLevelTables), then its
        jsr     LoadLevelTables                 ; tile file
        lea.l   LevelFileIndex(pc),a1           ; 06842/06898
""")
    n = len(re.findall(r'\n        lea\.l   FileLevel0\(pc\),a1', S.s))
    assert n == 2, n                  # Start loads level 0's tile file (1MB early, 512K later): its tables too
    ins = I('moveq   #0,d0', "level 0's map tables (the title shows level 0)") + '\n        jsr     LoadLevelTables\n'
    S.s = re.sub(r'\n(        lea\.l   FileLevel0\(pc\),a1)', lambda m: '\n' + ins + m.group(1), S.s)
    open(OUT, 'w').write(S.s.rstrip('\n') + '\n')
    n = widen_branches(OUT)
    print(f'{os.path.relpath(OUT, ROOT)}: {S.s.count(chr(10))} lines; {n} references out of reach made longer')


if __name__ == '__main__':
    main()
