"""Render the 10 small BOB images of track 37 (item / platform graphics). Run from render/."""
import struct, numpy as np
from PIL import Image, ImageDraw
G=open('../bin/main_512k.bin','rb').read(); B=0x80
F=open('../disk/files/t037_small_bob_sets.bin','rb').read()
P=np.array([((v>>8&15)*17,(v>>4&15)*17,(v&15)*17) for v in (struct.unpack('>H',G[0x4fb0-B+2*i:0x4fb0-B+2*i+2])[0] for i in range(32))],dtype=np.uint8)
offs=[struct.unpack('>I',G[0x543c-B+4*i:0x543c-B+4*i+4])[0] for i in range(10)]
sizes=[struct.unpack('>H',G[0x67ee-B+2*i:0x67ee-B+2*i+2])[0] for i in range(10)]
yh=[(G[0xa992-B+2*i],G[0xa992-B+2*i+1]) for i in range(10)]
imgs=[]
for i in range(10):
    y,h=yh[i]; sz=sizes[i]
    words=sz//(10*h) if h else 0
    print(f'set {i}: offset ${offs[i]:04X} size {sz} height {h} y-adjust {y} -> {words*16} px wide', '' if words and words*10*h==sz else '(size not a whole frame)')
    if not words: continue
    idx=np.zeros((h,words*16),dtype=np.uint8)
    for yy in range(h):
        for p in range(5):
            for x in range(words*16):
                q=offs[i]+(yy*5+p)*words*2+(x//16)*2
                if q+1<len(F) and ((F[q]<<8|F[q+1])>>(15-x%16))&1: idx[yy,x]|=1<<p
    im=P[idx]; im[idx==0]=(40,40,40); imgs.append((i,im))
W=sum(im.shape[1]+12 for i,im in imgs); H=max(im.shape[0] for i,im in imgs)+14
s=Image.new('RGB',(W*3,H*3),(20,20,20)); x=6
for i,im in imgs:
    s.paste(Image.fromarray(im).resize((im.shape[1]*3,im.shape[0]*3),Image.NEAREST),(x*3,14*3//1))
    ImageDraw.Draw(s).text((x*3,4),str(i),fill=(255,255,0)); x+=im.shape[1]+12
s.save('out/small_bobs_t037.png')
