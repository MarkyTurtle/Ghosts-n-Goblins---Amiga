"""Check the harness: the original game's display (redrawn by its own code in the emulator)
must equal the level picture made independently by render/levels.py, at many camera origins."""
import numpy as np, random, sys
from PIL import Image
from original import Original

def expected(level_png, tx, ty):
    L = np.array(Image.open(level_png).convert('RGB')); H = L.shape[0]
    top = H - (ty*16 + 256)            # the bottom 16 lines are below the view
    return L[top:top+240, tx*16:tx*16+256]

def rgb(o, img):
    pal = o.palette()
    P = np.array([((c >> 8 & 15)*17, (c >> 4 & 15)*17, (c & 15)*17) for c in pal], dtype=np.uint8)
    return P[img]

def main():
  bad = 0; n = 0
  for lv in (0, 1, 2, 3):
      o = Original(lv); png = f'../../render/out/level{lv}.png'
      H, W = np.array(Image.open(png)).shape[:2]
      rnd = random.Random(lv)
      for _ in range(4):
          tx = rnd.randrange(0, (W-272)//16); ty = rnd.randrange(0, max(1, (H-256)//16))
          got = rgb(o, o.show(tx, ty))[16:]; exp = expected(png, tx, ty)[16:]   # top 16 lines: the HUD strip
          n += 1
          if got.shape != exp.shape or (got != exp).any(1).any():
              diff = (got != exp).any(2).sum() if got.shape == exp.shape else 'shape'
              print(f'level {lv} origin ({tx},{ty}): {diff} pixels differ'); bad += 1
  print(f'{n-bad} of {n} views identical to the level pictures')

if __name__ == '__main__':
    main()
