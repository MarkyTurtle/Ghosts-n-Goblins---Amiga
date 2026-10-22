import struct,sys
from PIL import Image
G=open('../bin/main_512k.bin','rb').read();B=0x80
def rb(a,n): return G[a-B:a-B+n]
def w(a): return struct.unpack('>h',rb(a,2))[0]
pal=[struct.unpack('>H',rb(0x4fb0+2*i,2))[0] for i in range(32)]
def c12(v): return ((v>>8&15)*17,(v>>4&15)*17,(v&15)*17)
lvfiles=[(84,0x7440),(89,0xc120),(97,0x5460),(101,0x4880),(104,0x2760),(106,0x29e0),(108,0x19a0)]
def readfile(t,n):
    b=b''
    while len(b)<n: b+=open(f'../bin/tracks/t{t:03d}.bin','rb').read(); t+=1
    return b[:n]
WORLD=0x44d6; WROWS=11
import numpy as np
def w2(a): return struct.unpack('>h',rb(a,2))[0]
for lv in range(7):
    T=readfile(*lvfiles[lv]); ntiles=len(T)//160
    x0c,x1c,y1c,y0c=rb(0x4466+4*lv,4)
    # map origin: LevelMapTable entry is an offset from the table START ($44BA)
    origin=0x44ba+w2(0x44ba+2*lv)
    P=np.array([c12(v) for v in pal],dtype=np.uint8)
    tiles=np.zeros((ntiles,16,16),dtype=np.uint8)
    for t in range(ntiles):
        for y in range(16):
            for pl in range(5):
                o=t*160+(y*5+pl)*2; wd=(T[o]<<8)|T[o+1]
                for x in range(16):
                    if wd>>(15-x)&1: tiles[t,y,x]|=1<<pl
    cw=x1c-x0c+1; ch=y1c-y0c+1; over=[]
    idx=np.zeros((ch*256,cw*256),dtype=np.uint8)
    for rr in range(ch):            # rr = cell rows upwards from the origin
        for cc in range(cw):
            cell=G[origin-B+rr*32+cc]
            for tr in range(16):
                for tc in range(16):
                    # cell $67 = tile 0 everywhere; tile 0 is a real tile (first in the level file)
                    t=0 if cell==0x67 else G[0x1222c-B+((cell<<4)+tr)*16+tc]
                    if t and lv==1 and (cell==0x1f or (cell==0x1d and t<9)): t+=0x100
                    elif lv==1 and cell==0x1d and t==9: t=0x100
                    if t>=ntiles: over.append((rr,cc,tr,tc,t)); continue
                    X=cc*256+tc*16; Y=(ch-1-rr)*256+tr*16
                    idx[Y:Y+16,X:X+16]=tiles[t]
    Image.fromarray(P[idx]).save(f'out/level{lv}.png')
    print('level',lv,'origin',hex(origin),'cells',cw,'x',ch,'tiles',ntiles,'beyond file',len(over))
