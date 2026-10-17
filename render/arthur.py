import struct, numpy as np
from PIL import Image
G=open('../bin/main_512k.bin','rb').read();B=0x80
def uw(a): return struct.unpack('>H',G[a-B:a-B+2])[0]
b=b'';t=33
while len(b)<0x5400: b+=open(f'../bin/tracks/t{t:03d}.bin','rb').read(); t+=1
pal=[uw(0x4fb0+2*i) for i in range(32)]
P=np.array([((v>>8&15)*17,(v>>4&15)*17,(v&15)*17) for v in pal],dtype=np.uint8)
N=42; frames=[]
for f in range(N):
    idx=np.zeros((32,32),dtype=np.uint8)
    for y in range(32):
        o=(f*32+y)*16
        for p in range(4):
            for half in range(2):
                wd=(b[o+(p*2+half)*2]<<8)|b[o+(p*2+half)*2+1]
                for x in range(16):
                    if wd>>(15-x)&1: idx[y,half*16+x]|=1<<p
    img=P[idx+16]; img[idx==0]=(40,40,40); frames.append(img)
cols=14; rows=(N+cols-1)//cols
sheet=np.full((rows*36,cols*36,3),20,dtype=np.uint8)
for i,f in enumerate(frames): sheet[(i//cols)*36+2:(i//cols)*36+34,(i%cols)*36+2:(i%cols)*36+34]=f
Image.fromarray(sheet).resize((cols*36*3,rows*36*3),Image.NEAREST).save('out/arthur.png')
