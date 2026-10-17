"""Render the weapon icons shown in the status bar (WeaponIcons, $55DC). Run from render/.
Each icon is $80 bytes: two $40 halves; even/odd bytes feed two sprites each (8 pixels, DATA/DATB
per line), the second half holding the attached partner sprites: 16x16 pixels, 16 colours (COLOR16-31)."""
import struct, numpy as np
from PIL import Image
G=open('../bin/main_512k.bin','rb').read(); B=0x80
pal=[struct.unpack('>H',G[0x4fb0-B+2*i:0x4fb0-B+2*i+2])[0] for i in range(32)]
P=np.array([((v>>8&15)*17,(v>>4&15)*17,(v&15)*17) for v in pal],dtype=np.uint8)
def icon(n):
    a=0x55dc+0x80*n-B; h0=G[a:a+0x40]; h1=G[a+0x40:a+0x80]
    idx=np.zeros((16,16),dtype=np.uint8)
    for y in range(16):
        for half,(src_even,src_odd) in enumerate(((h0,h1),)):
            pass
        for x in range(16):
            col= 0 if x<8 else 1                  # even bytes -> left sprite, odd -> right sprite
            bit=7-(x%8)
            d0=h0[(y*2)*2+col]; d1=h0[(y*2+1)*2+col]      # DATA / DATB of the low-plane sprite
            d2=h1[(y*2)*2+col]; d3=h1[(y*2+1)*2+col]      # attached partner
            v=(d0>>bit&1)|((d1>>bit&1)<<1)|((d2>>bit&1)<<2)|((d3>>bit&1)<<3)
            idx[y,x]=v
    im=P[idx+16]; im[idx==0]=(40,40,40); return im
icons=[icon(n) for n in range(5)]
s=np.full((20,5*20,3),20,dtype=np.uint8)
for n,im in enumerate(icons): s[2:18,n*20+2:n*20+18]=im
Image.fromarray(s).resize((s.shape[1]*6,s.shape[0]*6),Image.NEAREST).save('out/weapon_icons.png')
