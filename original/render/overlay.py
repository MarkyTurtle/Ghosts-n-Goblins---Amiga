import struct
from PIL import Image, ImageDraw
G=open('../bin/main_512k.bin','rb').read();B=0x80
def rb(a,n): return G[a-B:a-B+n]
def w(a): return struct.unpack('>h',rb(a,2))[0]
NAMES={0:'WoodyPig',1:'Crow',2:'PetiteDevil',3:'FlyKnight',4:'BlueKiller',5:'RedArremer',6:'Satan',7:'Magician',8:'Unicorn',9:'Skeleton',
10:'BigMan',11:'Zombie',12:'Dragon',13:'Astaroth',14:'Fire',15:'Princess',17:'Plant',18:'FirePillar'}
ITEMS={0:'pickup',1:'pot',2:'platform',3:'platform',4:'platform',5:'platform'}
for lv in range(7):
    x0c,x1c,y1c,y0c=rb(0x4466+4*lv,4)
    im=Image.open(f'out/level{lv}.png').convert('RGB'); d=ImageDraw.Draw(im)
    def put(x,y,txt,col):
        X=x-x0c*256; Y=(y1c-y0c+1)*256-(y-y0c*256)
        d.rectangle([X-6,Y-6,X+6,Y+6],outline=col); d.text((X+8,Y-6),txt,fill=col)
    for tbl,names,col in ((0x3b22,NAMES,(255,255,0)),(0x3b14,ITEMS,(0,255,255))):
        a=tbl+2*lv; a+=w(a); n=w(a); a+=2
        for i in range(n):
            ty,pa=rb(a,2); x,y=struct.unpack('>hh',rb(a+2,4)); a+=6
            put(x,y,f'{names.get(ty,ty)}/{pa}',col)
    # arthur start
    sx,sy=rb(0x449e+2*lv,2); put(sx+x0c*256 if False else sx, sy,'START',(255,0,255))
    im.save(f'out/level{lv}_objects.png')
