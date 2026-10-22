import struct
import numpy as np
from PIL import Image, ImageDraw
G=open('../bin/main_512k.bin','rb').read();B=0x80
def rb(a,n): return G[a-B:a-B+n]
def w(a): return struct.unpack('>h',rb(a,2))[0]
def uw(a): return struct.unpack('>H',rb(a,2))[0]
def L(a): return struct.unpack('>I',rb(a,4))[0]
def readfile(t,n):
    b=b''
    while len(b)<n: b+=open(f'../bin/tracks/t{t:03d}.bin','rb').read(); t+=1
    return b[:n]
F=readfile(38,0x1d042)
pal=[uw(0x4fb0+2*i) for i in range(32)]
P=np.array([((v>>8&15)*17,(v>>4&15)*17,(v&15)*17) for v in pal],dtype=np.uint8)
sizes=[uw(0x67c4+2*i) for i in range(21)]; offs=[L(0x53aa+4*i) for i in range(21)]
def frame_img(blk,off,wd,h):
    words=wd//16; ps=words*2*h; idx=np.zeros((h,wd),dtype=np.uint8)
    for p in range(5):
        for y in range(h):
            for x in range(wd):
                o=off+(y*5+p)*words*2+(x//16)*2
                if o+1<len(blk) and ((blk[o]<<8|blk[o+1])>>(15-x%16))&1: idx[y,x]|=1<<p
    return idx
starts=[]
for t in range(21):
    if t<19: d=0x4ff0+2*t; d=d+w(d)
    elif t==19: d=0x538e
    else: d=0x5056
    starts.append(d)
allst=sorted(set(starts+[0x538e+4*7,0x53aa]))
sheets=[]
for t in range(21):
    blk=F[offs[t]:offs[t]+sizes[t]]
    # descriptor table
    if t<19: dt=0x4ff0+2*t; dt=dt+w(dt)
    elif t==19: dt=0x538e
    else: dt=0x5056
    descs=[]; k=0
    nmax=([x for x in allst if x>dt] or [dt+256])[0]
    while k<(nmax-dt)//4:
        o=uw(dt+4*k); yo=rb(dt+4*k+2,1)[0]; h=rb(dt+4*k+3,1)[0]
        if o>=len(blk) or h==0 or h>96: break
        descs.append((o,h)); k+=1
    uniq=sorted(set(o for o,h in descs))+[len(blk)]
    frames=[]
    for o,h in descs:
        nxt=[u for u in uniq if u>o][0]; sz=nxt-o
        words=sz//(10*h) if h else 0
        if words<1 or words>6: words=max(1,min(6,words))
        frames.append((o,h,words*16))
    print(f'set {t:2d} off {offs[t]:05X} size {sizes[t]:5X} desc@{dt:05X} frames {len(frames)}', [(f"{o:X}",h,wd) for o,h,wd in frames[:6]])
    if not frames: continue
    seen=[];imgs=[]
    for o,h,wd in frames:
        if o in seen: continue
        seen.append(o); imgs.append(P[frame_img(blk,o,wd,h)])
    W=sum(i.shape[1]+4 for i in imgs)+4; H=max(i.shape[0] for i in imgs)+4
    sh=np.full((H,W,3),40,dtype=np.uint8); x=2
    for i in imgs:
        sh[2:2+i.shape[0],x:x+i.shape[1]]=i; x+=i.shape[1]+4
    sheets.append((t,sh))
# compose
scale=2
rowsimg=[]
for t,sh in sheets:
    im=Image.fromarray(sh).resize((sh.shape[1]*scale,sh.shape[0]*scale),Image.NEAREST)
    lab=Image.new('RGB',(im.width+80,im.height),(40,40,40)); lab.paste(im,(80,0))
    NM={0:'WoodyPig',1:'Crow',2:'PetiteDevil',3:'FlyKnight',4:'BlueKiller',5:'RedArremer',6:'Satan',7:'Magician',8:'Unicorn',9:'Skeleton',10:'BigMan',11:'Zombie',12:'Dragon',13:'Astaroth',14:'Fire',15:'Princess',17:'Plant',18:'FirePillar',19:'Bat',20:'RedCrow'}
    ImageDraw.Draw(lab).text((4,4),f'{t} {NM.get(t,"")}',fill=(255,255,0)); rowsimg.append(lab)
Wt=max(r.width for r in rowsimg); Ht=sum(r.height+4 for r in rowsimg)
out=Image.new('RGB',(min(Wt,2400),Ht),(20,20,20)); y=0
for r in rowsimg: out.paste(r,(0,y)); y+=r.height+4
out.save('out/bobs.png'); print(out.size)
