"""The whole WorldMap (32 x 11 cells of 256 x 256 px, plus the throne room) as one picture:
each cell cut from the rendered level images (run levels.py first), scaled down, with its
cell number and a border in its level's colour. Writes out/worldmap_cells.png."""
import struct
from PIL import Image, ImageDraw, ImageFont
G = open('../bin/main_512k.bin', 'rb').read(); B = 0x80
WM, LMT, LB = 0x44D6, 0x44BA, 0x4466
S = 72                      # pixels per cell in the picture
COL = [(230, 80, 80), (240, 170, 60), (220, 220, 70), (90, 200, 90), (80, 180, 230), (150, 110, 230), (230, 110, 200)]
W, H = 33*S, 11*S+40
img = Image.new('RGB', (W, H), (24, 24, 28)); d = ImageDraw.Draw(img)
try: font = ImageFont.truetype('DejaVuSansMono-Bold.ttf', 13)
except Exception: font = ImageFont.load_default()
def cellbox(r, c):                      # map row r (0 = bottom), column c
    return c*S, (10-r)*S
placed = {}
for lv in range(7):
    off = struct.unpack('>H', G[LMT-B+2*lv:LMT-B+2*lv+2])[0] + LMT - WM
    x0, x1, y1, y0 = G[LB-B+4*lv:LB-B+4*lv+4]
    cw, ch = x1-x0+1, y1-y0+1
    r0, c0 = divmod(off, 32)
    lvimg = Image.open(f'out/level{lv}.png')
    for rr in range(ch):
        for cc in range(cw):
            tile = lvimg.crop((cc*256, (ch-1-rr)*256, cc*256+256, (ch-rr)*256)).resize((S, S), Image.LANCZOS)
            r, c = r0+rr, c0+cc
            if r == 11: x, y = 32*S, 0          # the throne room: drawn top right
            else: x, y = cellbox(r, c)
            img.paste(tile, (x, y)); placed[(x, y)] = lv
for r in range(11):
    for c in range(32):
        x, y = cellbox(r, c)
        cell = G[WM-B+32*r+c]
        lv = placed.get((x, y))
        if lv is None: d.rectangle([x, y, x+S-1, y+S-1], outline=(60, 60, 66))
        else: d.rectangle([x, y, x+S-1, y+S-1], outline=COL[lv], width=2)
        d.text((x+4, y+3), f'{cell:02X}', fill=(255, 255, 255) if lv is not None else (110, 110, 120), font=font,
               stroke_width=2, stroke_fill=(0, 0, 0))
x, y = 32*S, 0
d.rectangle([x, y, x+S-1, y+S-1], outline=COL[6], width=2)
d.text((x+4, y+3), f'{G[WM-B+352]:02X}', fill=(255, 255, 255), font=font, stroke_width=2, stroke_fill=(0, 0, 0))
d.text((x+2, y+S+4), 'throne', fill=COL[6], font=font)
for lv in range(7):
    d.rectangle([10+lv*120, 11*S+12, 26+lv*120, 11*S+28], fill=COL[lv])
    d.text((32+lv*120, 11*S+12), f'level {lv}', fill=(230, 230, 230), font=font)
d.text((10+7*120, 11*S+12), 'cell numbers = WorldMap bytes (hex); row 0 at the bottom', fill=(170, 170, 180), font=font)
img.save('out/worldmap_cells.png')
print('out/worldmap_cells.png', img.size)
