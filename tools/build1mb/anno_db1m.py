"""Annotations for the 1MB build, carried over from the 512K database (../anno_db.py,
../anno_auto.py) through the instruction alignment in map.json (mkmap.py)."""
import json,bisect,sys,os,re
HERE=os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0,os.path.join(HERE,'..'))
import anno_db as A5
try:
    import anno_auto as AU5
except Exception: AU5=None
_m=json.load(open(os.path.join(HERE,'map.json')))
AMAP={int(k,16):v for k,v in _m['amap'].items()}
_ks=sorted(AMAP)
UNMAPPED=[]
def addr(a):
    """512K address -> 1MB file offset (None if it falls in code that differs)."""
    if a in AMAP: return AMAP[a]
    i=bisect.bisect_right(_ks,a)
    lo=_ks[i-1] if i else None; hi=_ks[i] if i<len(_ks) else None
    if lo is not None and hi is not None and AMAP[lo]-lo==AMAP[hi]-hi: return a+AMAP[lo]-lo
    if a>=_m['A_end']: return a-_m['A_end']+_m['B_end']
    return None
def var(o):   # a6 offsets: the 1MB build inserts g_BaseAddr (long) at +2
    return o+4 if o>=2 else o
def remap(d,what,exact=False):
    out={}
    for a,v in d.items():
        b=AMAP.get(a) if exact else addr(a)
        if b is None: UNMAPPED.append((what,a,v)); continue
        out[b]=v
    return out
NAMES=remap(A5.NAMES,'name'); HEADERS=remap(A5.HEADERS,'header'); COMMENTS=remap(A5.COMMENTS,'comment',True)
AUTO_COMMENTS=remap(getattr(AU5,'AUTO_COMMENTS',{}),'auto',True) if AU5 else {}
AUTO_NAMES=remap(getattr(AU5,'AUTO_NAMES',{}),'autoname') if AU5 else {}
VARS={var(o):v for o,v in A5.VARS.items()}
VARS[2]=('g_BaseAddr','1MB build only: load address of the program (from $4.w); added to every program address')
REGIONS=[(addr(s) or s,addr(e) or e,p) for s,e,p in A5.REGIONS]
OBJ_FIELDS=A5.OBJ_FIELDS
TYPE_FIELDS=[(addr(lo),addr(hi),{o:v for o,v in fm.items()}) for lo,hi,fm in getattr(A5,'TYPE_FIELDS',[])]
DATA_BLOCKS={addr(_s):(addr(_e),_l) for _s,(_e,_l) in getattr(A5,'DATA_BLOCKS',{}).items()}
# Data blocks are placed by finding their exact bytes in the 1MB binary (the instruction
# alignment can interpolate wrongly across long data runs); labels inside move with them.
_D5=open(os.path.join(os.path.dirname(os.path.abspath(A5.__file__)),'main.bin'),'rb').read()
_D1=open(next(x for x in [os.environ.get('MAIN1M',''),os.path.join(HERE,'main1m.bin'),
          os.path.join(HERE,'..','..','bin','main_1mb.bin')] if x and os.path.exists(x)),'rb').read()
for _s,(_e,_l) in getattr(A5,'DATA_BLOCKS',{}).items():
    _blk=_D5[_s-0x80:_e-0x80]
    if _D1.count(_blk)!=1:
        DATA_BLOCKS.pop(addr(_s),None); continue   # differs in the 1MB build: left as plain data
    _b=_D1.find(_blk)
    DATA_BLOCKS.pop(addr(_s),None); DATA_BLOCKS[_b]=(_b+_e-_s,_l)
    for _a,_n in A5.NAMES.items():
        if _s<=_a<_e:
            _old=addr(_a)
            if _old is not None and NAMES.get(_old)==_n: del NAMES[_old]
            NAMES[_b+_a-_s]=_n
    if _s in A5.HEADERS:
        _old=addr(_s)
        if _old is not None and HEADERS.get(_old)==A5.HEADERS[_s]: del HEADERS[_old]
        HEADERS[_b]=A5.HEADERS[_s]
# Blocks whose bytes differ (frame tables of the pre-masked graphics, the copper template):
# decode the 1MB bytes with the same builders when the table has the same size and shape.
def _decode_1mb(_s, _e):
    _b, _be = addr(_s), addr(_e)
    if _b is None or _be is None: return None
    if A5.NAMES.get(_s) == 'BobFrameDescs':      # different frame offsets (pre-masked graphics)
        import tables2_data, struct
        _be = _b + _e - _s                        # same size; the 1MB build adds BobSetOffsetsCached after it
        _rel = lambda a: a + struct.unpack('>h', _D1[a:a+2])[0]
        _nm = {_b: 'BobFrameDescs', _b+16: 'BobFrameDescsUnicorn', _rel(_b+2): 'BobFrameDescsRedCrow',
               _b + 0x538E - _s: 'BobFrameDescsBat'}
        for a in [a for a, n in NAMES.items() if (_b <= a < _be) or n in _nm.values()]:
            del NAMES[a]                          # names interpolated from the 512K layout
        NAMES.update(_nm)
        try:
            return _b, tables2_data.bob_frame_descs(_D1, 0, _b, _be, _b + 0x538E - _s, _nm)
        except AssertionError: return None
    if _be-_b != _e-_s: return None
    _Dx = bytearray(_D5); _Dx[_s-0x80:_e-0x80] = _D1[_b:_be]; _Dx = bytes(_Dx)
    import anim_data, tables_data, tables2_data
    for _f in (lambda: tables2_data.build(_Dx, names=A5.NAMES), lambda: anim_data.build(_Dx, names=A5.NAMES),
               lambda: tables_data.build(_Dx)):
        try: _bl = _f()
        except Exception: continue
        for _x in _bl:
            if _x[0] == _s and _x[1] == _e: return _b, _x
    return None
_NOTE1M = {0x908E: '\n1MB build: the offsets are doubled (cached graphics with mask lines).'}
for _s,(_e,_l) in getattr(A5,'DATA_BLOCKS',{}).items():
    if _D1.count(_D5[_s-0x80:_e-0x80]) == 1: continue
    _r = _decode_1mb(_s, _e)
    if not _r: continue
    _b, (_, _, _lines, _lab) = _r
    _out = []
    for _ln in _lines:
        _mm = _ln[:-1] if _ln.endswith(':') and not _ln.startswith(('\t', ';')) else None
        if _mm and _lab.get(_mm) not in (None, _s) and _lab[_mm] in A5.HEADERS:
            _out += ['', ';'+'-'*75] + ['; '+x if x else ';' for x in (A5.HEADERS[_lab[_mm]]+_NOTE1M.get(_lab[_mm], '')).split('\n')] + [';'+'-'*75]
        _out.append(_ln)
    DATA_BLOCKS[_b] = (_b + (_r[1][1]-_r[1][0]), _out)
    _same = _r[1][0] == _s                       # block built from 512K addresses?
    for _n, _a in _lab.items():
        _new = _b+_a-_s if _same else _a
        _old = addr(_a) if _same else None
        if _old is not None and NAMES.get(_old) == _n: del NAMES[_old]
        for _k in [k for k, v in NAMES.items() if v == _n and k != _new]: del NAMES[_k]
        NAMES[_new] = _n
    if _s in A5.HEADERS:
        HEADERS[_b] = A5.HEADERS[_s]
VAR_RANGES=[(var(o),n) for o,n in getattr(A5,'VAR_RANGES',[])]
OBJ_RANGES=[(addr(s),addr(e)) for s,e in A5.OBJ_RANGES]
DATAFMT=remap(getattr(A5,'DATAFMT',{}),'fmt')
# memory map: 512K absolute -> 1MB value seen in the same instruction
_mem={int(k,16):v for k,v in _m['mem'].items()}
MEM={}; MEMC={}
for a,n in A5.MEM.items():
    if a<0x80: MEM[a]=n; MEMC[a]=A5.MEMC.get(a,''); continue
    if a in _mem:
        MEM[_mem[a]]=n; MEMC[_mem[a]]=(A5.MEMC.get(a,'')+f' [512K: ${a:05X}]').strip()
GLOBALS_1M=0x1893A
MEM[GLOBALS_1M]='GLOBALS'; MEMC[GLOBALS_1M]='offset from g_BaseAddr [512K: absolute $1898C]'

# ---------------------------------------------------------------------------
# 1MB-specific annotations (override anything carried over)
# ---------------------------------------------------------------------------
NAMES1M={
 0x00:'HunkHeader', 0x20:'ProgramEntry', 0x6898:'LoadLevel', 0xBC48:'PlayMusic',
 0xC304:'BuildMaskedGfx', 0x532A:'BobSetOffsetsCached',
 0x3F82:'CacheSizesSmallBobs', 0x42AA:'CacheSizesEnemyGfx', 0x4346:'CacheSizesItemGfx2',
 0x4352:'CacheSizesEnemyShots', 0x435E:'CacheSizesItems',
 0x4FD6:'BobFrameDescsRedCrow',   # (placed again by the frame-table decoder above)
}
HEADERS1M={
 0x00:"AmigaDOS hunk header, left in place. The bootblock loads this file raw to the\naddress in $4.w and jumps to load+$20.",
 0x20:"Program entry point (load address + $20).",
 0x5C66:"""1MB build: load the common graphics once and keep them (the 512K build reloads the
enemy graphics for every level). Each file is loaded to the staging area, then
BuildMaskedGfx converts it into a permanent buffer with a mask line stored after every
plane line, so drawing needs no blitter mask pass. Then the progress map is cached and the
111KB music package is loaded and hooked to vector $60.""",
 0x6898:"""Sub state 0: load the level (1MB build).
Only the per-level file is loaded (tracks 84-109): the enemy graphics are already cached,
so BuildFrameTable points the frame tables into the cache (BobSetOffsetsCached) instead.""",
 0xBC48:"""PlayMusic - 1MB build only. d0 = tune number (see sound/SOUND.md): calls the sound
driver through vector $60 with command 1 (d0.l = tune<<16 | 1).""",
 0xBC58:"""PlaySfx - d0 = effect number (0-29). Calls the sound driver through vector $60
with command 2 (d0.l = number<<16 | 2). Driver source: sound/gng_music_1mb.s.""",
 0xC304:"""BuildMaskedGfx - 1MB build only. Convert d7+1 graphics blocks from a1 (5 planes,
line-interleaved) to a2, writing after every plane line a mask line (the OR of the
5 planes). a3 -> (width in pixels, height) words per block.""",
 0x4F70:A5.HEADERS[0x4FF0]+"""
1MB build: the same tables, but every graphics offset is doubled - the cached graphics
(BuildMaskedGfx) have a mask line after every plane line.""",
 0x9060:A5.HEADERS[0x9002]+"\n1MB build: the offsets are doubled (cached graphics with mask lines).",
 0x532A:"BobSetOffsetsCached - 1MB build: offset of each BOB set inside the cached enemy graphics",
 0x3F82:"BuildMaskedGfx size tables (width px, height) for each cached file",
}
for _a,_n in NAMES1M.items():
    for _k in [k for k,v in NAMES.items() if v==_n and k!=_a]: del NAMES[_k]
    NAMES[_a]=_n
for _a,_h in HEADERS1M.items(): HEADERS[_a]=_h
MANUAL_C={0x5D84,0x5C96,0xBB82,0xBC24}
COMMENTS[0xBB82]='a4 = mask line: in the 1MB build every plane line is followed by its mask (BuildMaskedGfx)'
COMMENTS[0xBC24]='A = stored mask, B = BOB, C/D = screen: no mask-building blit needed'
COMMENTS[0x5D84]='vector $60 = music driver ($3604C + $20)'
COMMENTS[0x5C96]='cache: enemy graphics (tracks 38-56)'
for _a,_n,_c in [(0xB480,'SCREEN_1','chip RAM'),(0x21C80,'SCREEN_3','chip RAM'),
  (0x26E42,'ENEMY_GFX_CACHE','offset from g_BaseAddr: cached enemy graphics with masks'),
  (0x250E6,'PROGRESS_MAP_CACHE','offset from g_BaseAddr: cached progress map file'),
  (0x3604C,'MUSIC_FILE','chip RAM: 111KB music package (tracks 64-81)'),
  (0x3606C,'MUSIC_PLAYER','music driver entry'),
  (0x34300,'ITEM_GFX2_BUF','chip RAM: masked item graphics 2'),
  (0x2E914,'ESHOT_GFX_BUF','chip RAM: masked enemy projectile graphics'),
  (0x30D7C,'ITEM_GFX_BUF','chip RAM: masked item graphics')]:
    MEM[_a]=_n; MEMC[_a]=_c
for _a in (0x80,0x16880):
    MEMC[_a]=(MEMC.get(_a,'')+' (chip RAM)').strip()

# ---- comments on the 1MB-only code (1MB addresses)
COMMENTS1M={
 0x5A6E:'a6 = GLOBALS + load address (from $4.w); the user stack sits below it',
 0x5A7C:'g_BaseAddr: added to every absolute program address from here on',
 0x5AC4:'the sprite banks move with the load address',
 0x5C9C:'enemy graphics: 39 sets, masks added',
 0x5CAA:'item graphics 2 (track 57) into chip RAM, masks added',
 0x5CC8:'enemy shot graphics (track 58)',
 0x5CE6:'item graphics (tracks 59-60)',
 0x5D52:'keep a copy of the packed progress map (no reload between levels)',
 0x5D76:'the music package (driver + 15 tunes + 30 effects, tracks 64-81)',
 0xBB96:'mask lines interleave the plane lines: the A/B modulo skips the other line',
 0xBC10:'one blit draws all 5 planes: 5 x height lines, one plane line each',
 0x8D30:'effect 14: extra life',
 0x9400:'effect 11: the torch bursts into flame on the ground',
 0xC7E2:'effect 18: Woody Pig flying',
 0xCDBC:'effect 27 every 64 frames while the crow sits',
 0xEACE:'effect 19: hit',
 0xF856:'effect 24: Unicorn step',
 0xFB8C:'effect 9: heavy landing',
 0xFCE0:'effect 9',
 0xFD34:'effect 9',
 0x10114:'effect 22: skeleton hop',
 0x10434:'effect 19: hit',
 0x10506:'effect 9: footstep',
 0x10704:'effect 9: footstep',
 0x110BE:'effect 24: the dragon attacks',
 0x11656:'effect 9: footstep',
 0x11E00:'effect 23: the fire pillar flares',
}
for _a,_t in COMMENTS1M.items():
    COMMENTS[_a]=_t
MANUAL_C|=set(COMMENTS1M)
HEADERS[0xBAC8]="""DrawBob - masked blit of one BOB (1MB build).
In: a1 = frame graphics, d1,d2 = level x,y (y up), d3 = width, d4 = height.
Same clipping, background save and $3000-byte save limit as the 512K build, but the
graphics were converted at start-up (BuildMaskedGfx) so that every plane line is
followed by its mask line. One cookie-cut blit (A = mask, B = BOB, C/D = screen) then
draws all 5 planes: 5 x height blitter lines, with the A/B modulo skipping the other
line and the C/D modulo stepping through the interleaved screen. The 512K build needs
two mask-building blits and five plane blits."""
