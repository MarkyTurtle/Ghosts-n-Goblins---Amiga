"""Render the loading screen, copyright screen, progress map, and the item / enemy-shot BOB blocks.
Run from render/: python3 pictures.py"""
import struct, numpy as np
from PIL import Image
G=open('../bin/main_512k.bin','rb').read(); B=0x80
F=lambda n: open('../disk/files/'+n,'rb').read()
def pal32(a): return np.array([((v>>8&15)*17,(v>>4&15)*17,(v&15)*17) for v in (struct.unpack('>H',G[a-B+2*i:a-B+2*i+2])[0] for i in range(32))],dtype=np.uint8)
P=pal32(0x4fb0)
def unpack(src,rows,planebytes,lead,trail):
    out=bytearray(); s=0
    for r in range(rows):
        for p in range(5):
            out+=b'\0'*lead; n=0
            while n<planebytes:
                c=src[s]; s+=1
                if c<128: out+=src[s:s+c+1]; s+=c+1; n+=c+1
                elif c!=128: k=257-c; out+=bytes([src[s]])*k; s+=1; n+=k
        out+=b'\0'*trail
    return bytes(out)
def planar(buf,rows,line,pstride,pbytes,fn,scale=2,pal=None):
    PP=P if pal is None else pal
    W=pbytes*8; idx=np.zeros((rows,W),dtype=np.uint8)
    for y in range(rows):
        for p in range(5):
            o=y*line+p*pstride; bits=np.unpackbits(np.frombuffer(buf[o:o+pbytes],dtype=np.uint8)); idx[y,:len(bits)]|=bits.astype(np.uint8)<<p
    Image.fromarray(PP[idx]).resize((W*scale,rows*scale),Image.NEAREST).save(fn)
# While the copyright screen is shown only COLOR00-03 are set (Start, $5E14): black, white, $BBB, $888.
# The picture uses only those four colours.
CP=np.array([(0,0,0),(255,255,255),(187,187,187),(136,136,136)]+[(0,0,0)]*28,dtype=np.uint8)
planar(unpack(F('t082-083_copyright_screen.rle'),224,32,4,0),224,180,36,36,'out/copyright_screen.png',pal=CP)
planar(unpack(F('t062-063_progress_map.rle'),80,44,4,2),80,242,48,48,'out/progress_map.png')
# loading screen: HAM6 interlaced, palette in the bootblock at $382
d=F('t001-016_loading_screen.bin'); boot=F('t000_bootblock.bin')
lp=[struct.unpack('>H',boot[0x382+2*i:0x384+2*i])[0] for i in range(16)]
c12=lambda v:((v>>8&15)*17,(v>>4&15)*17,(v&15)*17)
img=np.zeros((516,256,3),dtype=np.uint8)
for r in range(516):
    base=(r//2)*384+(r%2)*192; rgb=c12(lp[0])
    for x in range(256):
        v=0
        for p in range(6):
            o=base+p*32+x//8
            if o<len(d) and d[o]>>(7-x%8)&1: v|=1<<p
        ctl,dat=v>>4,v&15; R,Gc,Bc=rgb
        rgb=c12(lp[dat]) if ctl==0 else (R,Gc,dat*17) if ctl==1 else (dat*17,Gc,Bc) if ctl==2 else (R,dat*17,Bc)
        img[r,x]=rgb
Image.fromarray(img).resize((512,516),Image.NEAREST).save('out/loadscreen.png')
# BOB blocks: memory order $1A298 = t058, t059, t057
blk=F('t058_enemy_shot_gfx.bin')+F('t059-060_item_gfx.bin')+F('t057_item_gfx_part2.bin')
def descs(tab,lo,n):
    # n = number of 4-byte descriptors: offset.w, y-adjust.b, height.b
    out=[]
    for k in range(n):
        a=tab+4*k; o=struct.unpack('>h',G[a-B:a-B+2])[0]+lo; y=G[a-B+2]; h=G[a-B+3]
        out.append((o,h,y))
    return out
def sheet(ds,limit,fn):
    uniq=sorted(set(o for o,h,y in ds))+[limit]; imgs=[]; seen=set()
    for o,h,yadj in ds:
        if o in seen: continue
        seen.add(o)
        nxt=[u for u in uniq if u>o][0]; words=max(1,min(4,(nxt-o)//(10*h)))
        idx=np.zeros((h,words*16),dtype=np.uint8)
        for y in range(h):
            for p in range(5):
                for x in range(words*16):
                    q=o+(y*5+p)*words*2+(x//16)*2
                    if q+1<len(blk) and ((blk[q]<<8|blk[q+1])>>(15-x%16))&1: idx[y,x]|=1<<p
        im=P[idx]; im[idx==0]=(40,40,40); imgs.append((yadj,im))
    W=sum(i.shape[1]+4 for y,i in imgs); H=max(y+i.shape[0] for y,i in imgs)
    s=np.full((H+4,W+4,3),20,dtype=np.uint8); x=2
    for y,i in imgs: s[2+y:2+y+i.shape[0],x:x+i.shape[1]]=i; x+=i.shape[1]+4
    Image.fromarray(s).resize((s.shape[1]*3,s.shape[0]*3),Image.NEAREST).save(fn)
# The two descriptor tables are back to back: $9002 has ($908E-$9002)/4 = 35 entries,
# $908E has ($916A-$908E)/4 = 55 (UpdateShots code follows). Frames are drawn at their y-adjust.
sheet(descs(0x9002,0,35),0x1234,'out/enemy_shot_gfx.png')
sheet(descs(0x908e,0x1234,55),len(blk),'out/item_gfx.png')
print('ok')
