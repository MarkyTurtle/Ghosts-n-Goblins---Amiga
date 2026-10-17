import sys,os,importlib
sys.path.insert(0,'.')
from hw import CUSTOM,CIAA,CIAB
import anno_db1m as A
L=['; Ghosts\'n Goblins - equates for the 1MB build','',
'CUSTOM\t\tequ\t$DFF000\t; custom chip base','; custom chip register offsets']
for o,n in sorted(CUSTOM.items()): L.append(f'{n:<12}\tequ\t${o:03X}')
L+=['','; CIA-A (base $BFE001, odd addresses)']
for o,n in sorted(CIAA.items()): L.append(f'{n:<12}\tequ\t${0xbfe001+o:06X}')
L+=['','; CIA-B (base $BFD000, even addresses)']
for o,n in sorted(CIAB.items()): L.append(f'{n:<12}\tequ\t${0xbfd000+o:06X}')
if A:
    L+=['','; ---- Memory map (1MB build). Values used with adda g_BaseAddr are offsets from the load address;','; ---- the rest (screens, copper lists, sprites: chip RAM) are absolute. [512K value] in comments.']
    for a,n in sorted(getattr(A,'MEM',{}).items()):
        c=getattr(A,'MEMC',{}).get(a,''); L.append(f'{n:<20}\tequ\t${a:05X}'+(f'\t; {c}' if c else ''))
    L+=['','; ---- Global variables: offsets from a6 (GLOBALS = load address + $1893A; offsets >= 2 are 4 more than in the 512K build) ----']
    for o,(n,c) in sorted(getattr(A,'VARS',{}).items()):
        L.append(f'{n:<20}\tequ\t${o:03X}'+(f'\t; {c}' if c else ''))
L+=['','; ---- Object slot fields (enemies $3C, shots $26, items $1C share this header) ----']
for o,(n,c) in sorted(getattr(A,'OBJ_FIELDS',{}).items()):
    L.append(f'{n:<20}\tequ\t${o:02X}'+(f'\t; {c}' if c else ''))
L+=['','; ---- Per-enemy fields (slot offsets $1C-$3B differ by enemy type) ----']
for lo,hi,fm in getattr(A,'TYPE_FIELDS',[]):
    for o,(n,c) in sorted(fm.items()):
        L.append(f'{n:<20}\tequ\t${o:02X}'+(f'\t; {c}' if c else ''))
open('gng_equates_1mb.i','w').write('\n'.join(L)+'\n')
