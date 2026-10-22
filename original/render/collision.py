"""Overlay the collision data on each level map (as MapTileAt / ArthurFloorCheck / WallCheck* /
LadderCheck read it). Run from render/ after levels.py.
  green line  = floor surface (FloorProfile height within the 16x16 quadrant)
  red edge    = wall (WallProfileR / WallProfileL non-zero)
  yellow      = ladder (profile $40-$7D)
  cyan tint   = flags bits 6-7 set (floor probe ignores the quadrant)
Profile bytes are sign-extended before indexing the tables, as in the game."""
import struct
from PIL import Image, ImageDraw
G=open('../bin/main_512k.bin','rb').read(); B=0x80
g=lambda a: G[a-B]
w2=lambda a: struct.unpack('>h',G[a-B:a-B+2])[0]
import sys
FLIP=len(sys.argv)>1
stats={}
for lv in range(7):
    x0c,x1c,y1c,y0c=G[0x4466-B+4*lv:0x4466-B+4*lv+4]
    origin=0x44ba+w2(0x44ba+2*lv); cw=x1c-x0c+1; ch=y1c-y0c+1
    im=Image.open(f'out/level{lv}.png').convert('RGBA'); ov=Image.new('RGBA',im.size,(0,0,0,0)); d=ImageDraw.Draw(ov)
    cnt=dict(floor=0,wall=0,ladder=0,flag=0)
    for rr in range(ch):
        for cc in range(cw):
            cell=g(origin+rr*32+cc); page=g(0xa4+cell)<<8
            for qy in range(16):          # 16px rows, 0 = bottom of the cell
                for qx in range(16):
                    t=g(0x114+cell*64+(qx//2)*8+(qy//2))
                    rec=0x1b14+page+t*8; q=(2 if qx&1 else 0)+(1 if qy&1 else 0)
                    p=g(rec+q); f=g(rec+4+q)
                    X=cc*256+qx*16; Ytop=(ch-1-rr)*256+(qy if FLIP else 15-qy)*16   # image y of the quadrant's top
                    if f&0xc0:
                        d.rectangle([X,Ytop,X+15,Ytop+15],fill=(0,255,255,60)); cnt['flag']+=1
                    if 0x40<=p<=0x7d and not (f&0xc0):
                        d.rectangle([X+5,Ytop,X+10,Ytop+15],outline=(255,255,0,220)); cnt['ladder']+=1
                    sp=p-256 if p>127 else p          # profile is sign-extended (ext.w) by the game
                    fh=g(0x42aa+sp)
                    if fh and not (f&0xc0):
                        y=Ytop+16-fh; d.line([X,y,X+15,y],fill=(0,255,0,255),width=2); cnt['floor']+=1
                    if g(0x40aa+sp) or g(0x41aa+sp):
                        d.line([X,Ytop,X,Ytop+15],fill=(255,0,0,255),width=1); d.line([X+15,Ytop,X+15,Ytop+15],fill=(255,0,0,255),width=1); cnt['wall']+=1
    Image.alpha_composite(im,ov).convert('RGB').save(f'out/level{lv}_collision{"_flip" if FLIP else ""}.png')
    stats[lv]=cnt
print(stats)
