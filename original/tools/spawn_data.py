"""MapZoneTable / ZoneSpawners / SpawnScripts ($4637-$4FB0 in the 512K build) as readable
assembler (SPAWNER / SPAWN macros) for gen.py's DATA_BLOCKS. build(D) takes main.bin (512K,
loaded at $80) and returns (start, end, lines)."""
import struct,sys
def build(D, B=0x80):
    rb=lambda a:D[a-B]; rw=lambda a:struct.unpack('>h',D[a-B:a-B+2])[0]; ruw=lambda a:struct.unpack('>H',D[a-B:a-B+2])[0]
    NAMES={0:'WoodyPig',1:'Crow',2:'PetiteDevil',3:'FlyingKnight',4:'BlueKiller',5:'RedArremer',6:'Satan',7:'Magician',8:'Unicorn',9:'Skeleton',10:'BigMan',11:'Zombie',12:'Dragon',13:'Astaroth',14:'Fire',15:'Princess',16:'Type16'}
    WM=0x44D6; MZT=0x4637; ZS=0x4798; SS=0x48D5
    NZ=107; NT=17
    L=[]  # (addr, size, text) emitted in order
    def out(a,size,text): L.append((a,size,text))
    # ---- MapZoneTable
    L.append((MZT,0,'MapZoneTable:'))
    for r in range(11):
        a=MZT+32*r
        out(a,32,'\tdc.b\t'+','.join(f'{rb(a+i)}' for i in range(32))+f'\t; map row {r} (bottom row = 0)')
    out(MZT+352,1,f'\tdc.b\t{rb(MZT+352)}\t\t; cell $63 (the throne room)')
    # ---- ZoneSpawners offset table
    lists={}
    for z in range(NZ):
        la=ZS+z+rb(ZS+z); lists.setdefault(la,[]).append(z)
    lab_list={la:f'ZoneList_{min(zs):03d}' for la,zs in lists.items()}
    for c in ['','; ZoneSpawners - per zone, a byte offset to its spawner list: count.b, then SPAWNER',
              '; type, script, flags (bit 0 world coordinates, bit 1 runs once). Zones that share a list',
              '; point at the same one. Started by UpdateMapZone when the camera enters the zone.']:
        L.append((ZS,0,c))
    L.append((ZS,0,'ZoneSpawners:'))
    for z in range(NZ):
        la=ZS+z+rb(ZS+z)
        out(ZS+z,1,f'\tdc.b\t{lab_list[la]}-*\t; zone {z}')
    # lists in address order
    for la in sorted(lists):
        n=rb(la)
        L.append((la,0,f'{lab_list[la]}:\t\t\t; zone(s) '+', '.join(map(str,lists[la]))))
        out(la,1,f'\tdc.b\t{n}\t\t\t; spawners')
        for k in range(n):
            b1,b2=rb(la+1+2*k),rb(la+2+2*k); t=b1>>4; sc=((b1&15)<<4)|(b2&15); f=b2>>4
            fl=[]; 
            if f&1: fl.append('world coords')
            if f&2: fl.append('runs once')
            out(la+1+2*k,2,f'\tSPAWNER\t{t},{sc},{f}\t\t; {NAMES[t]} script {sc}'+(' - '+', '.join(fl) if fl else ''))
    USED=set()
    for z in range(NZ):
        la=ZS+z+rb(ZS+z)
        for k in range(rb(la)):
            b1,b2=rb(la+1+2*k),rb(la+2+2*k); USED.add((b1>>4,((b1&15)<<4)|(b2&15)))
    # ---- SpawnScripts type table
    offs=[SS+t+rb(SS+t) for t in range(NT)]
    for c in ['','; SpawnScripts - per enemy type, a byte offset to its table of word offsets to scripts.',
              '; Script: count.w, then SPAWN x, y, enemy param, frames to the next entry (run by',
              '; UpdateSpawners; x, y are camera-relative unless the spawner has world coordinates).',
              '; Scripts not reached from any zone list are still listed (unused).']:
        L.append((SS,0,c))
    L.append((SS,0,'SpawnScripts:'))
    for t in range(NT):
        lab=f'SpawnTable_{NAMES[t]}' if offs[t]!=SS+t else '*'
        out(SS+t,1,f'\tdc.b\t{lab}-*\t; type {t} {NAMES[t]}'+('  (empty: points at itself)' if offs[t]==SS+t else ''))
    tabs=sorted(set(o for o in offs if o>=SS+NT))
    scr={}  # script addr -> label
    keys={}
    tabentries={}
    for i,ta in enumerate(tabs):
        t=offs.index(ta)
        # entries until next table or first script
        tabentries[ta]=t
    # compute script addresses
    allscripts=set()
    end_tab={}
    first_script=None
    for i,ta in enumerate(tabs):
        nxt=tabs[i+1] if i+1<len(tabs) else None
        k=0; 
        while True:
            q=ta+2*k
            if nxt and q>=nxt: break
            if first_script and q>=first_script: break
            sp=q+rw(q); allscripts.add(sp)
            if first_script is None or sp<first_script: first_script=sp
            k+=1
        end_tab[ta]=k
    for ta in tabs:
        t=tabentries[ta]
        L.append((ta,0,f'SpawnTable_{NAMES[t]}:'))
        for k in range(end_tab[ta]):
            q=ta+2*k; sp=q+rw(q)
            scr.setdefault(sp,f'Spawn_{NAMES[t]}_{k}'); keys.setdefault(sp,(t,k))
            out(q,2,f'\tdc.w\t{scr[sp]}-*\t; script {k}')
    for sp in sorted(scr):
        cnt=ruw(sp)
        used=keys[sp] in USED or keys[sp]==(7,0)
        L.append((sp,0,f'{scr[sp]}:'+('' if used else '\t\t; (not started by any zone)')))
        out(sp,2,f'\tdc.w\t{cnt}\t\t\t; entries')
        for k in range(cnt):
            q=sp+2+6*k; x,y=rw(q),rw(q+2)
            out(q,6,f'\tSPAWN\t{x},{y},{rb(q+4)},{rb(q+5)}')
    # check contiguity
    addr=MZT; lines=[]
    for a,s,tx in L:
        if s==0: lines.append(tx); continue
        if a!=addr:
            if a>addr:
                lines.append('\tdc.b\t'+','.join(f'${rb(i):02X}' for i in range(addr,a))+'\t; (unused)')
                addr=a
            else: raise ValueError(f'overlap at {a:X} expected {addr:X}')
        lines.append(tx); addr+=s
    labels={tx.split(':')[0]:a for a,sz,tx in L if sz==0 and ':' in tx and not tx.startswith(';')}
    return MZT,addr,lines,labels
