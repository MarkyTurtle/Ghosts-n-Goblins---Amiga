"""Walk Arthur right / left / stand, using the verified model, with a redraw that takes
LAT camera steps to finish. Prints when origins are requested and switched, the fine
scroll, and freezes."""
from camera import model
def sim(speed_per_step, steps, lat, direction):
    tx, ty, fx = 10, 0, 0; nx, ny = tx, ty; done = 0xFF; busy = 0; camx = tx*16
    arthur = camx + 128; log = []; freezes = 0
    for k in range(steps):
        arthur += speed_per_step
        target = int(arthur) - 128
        s = dict(camdx=target-16*tx, camdy=0, pendx=target-16*nx, pendy=0, tilex=tx, tiley=ty, newx=nx, newy=ny,
                 done=done, jump=0, fall=0, ladder=0, dir=direction, skip=0, vely=0)
        sw, fx, fy, skip, nnx, nny, req = model(s)
        ev = []
        if sw: tx, ty = nx, ny; ev.append(f'switch to tile {tx}')
        if req: nx, ny = nnx, nny; done = 0; busy = lat; ev.append(f'request tile {nx}')
        if skip: freezes += 1; ev.append('FREEZE'); arthur -= speed_per_step   # logic stopped: Arthur did not move
        if not done:
            busy -= 1
            if busy <= 0: done = 0xFF
        log.append((k, round(target - 16*tx, 2), fx, ' '.join(ev)))
    return log, freezes
for lat in (1, 2, 4):
    log, fr = sim(2.25, 60, lat, 1)
    print(f'walking right 2.25 px per camera step, redraw takes {lat} step(s): {fr} freeze steps')
    for k, off, fx, ev in log[:24]:
        if ev: print(f'   step {k:2d}: target-origin {off:6.2f} fine {fx:3d}  {ev}')

print()
for lat in range(1,12):
    _, fr = sim(2.25, 400, lat, 1)
    print(f'walking right, redraw latency {lat:2d} camera steps: {fr} freeze steps in 400')
log,_=sim(-2.25, 30, 2, -1)
print('walking left (latency 2):')
for k,off,fx,ev in log[:20]:
    if ev: print(f'   step {k:2d}: target-origin {off:6.2f} fine {fx:3d}  {ev}')
def fall(speed, steps, lat):
    tx,ty=10,40; nx,ny=tx,ty; done=0xFF; busy=0; y=ty*16; fr=0; log=[]
    for k in range(steps):
        y-=speed
        s=dict(camdx=0,camdy=y-16*ty,pendx=0,pendy=y-16*ny,tilex=tx,tiley=ty,newx=nx,newy=ny,done=done,jump=0,fall=0xFF,ladder=0,dir=0,skip=0,vely=5)
        sw,fx,fy,skip,nnx,nny,req=model(s); ev=[]
        if sw: tx,ty=nx,ny; ev.append(f'switch to row {ty}')
        if req: nx,ny=nnx,nny; done=0; busy=lat; ev.append(f'request row {ny}')
        if skip: fr+=1; ev.append('FREEZE'); y+=speed
        if not done:
            busy-=1
            if busy<=0: done=0xFF
        log.append((k,y-16*ty,fy,' '.join(ev)))
    return log,fr
for lat in (1,2,3):
    log,fr=fall(10,40,lat)
    print(f'falling 10 px per camera step (5 px/frame), latency {lat}: {fr} freeze steps in 40')
    for k,off,fy,ev in log[:10]:
        if ev: print(f'   step {k:2d}: target-origin {off:4d} fine {fy:3d}  {ev}')
