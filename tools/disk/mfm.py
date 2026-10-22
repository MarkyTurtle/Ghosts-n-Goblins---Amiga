"""Raw MFM helpers for the original disk's track dumps: the bit offsets of a sync word, and how
often each known sync appears on a track (to tell the AmigaDOS track from the custom ones)."""
import sys,collections
def bits(fn):
    d=open(fn,'rb').read(); return int.from_bytes(d,'big'), len(d)*8
def words_at_syncs(fn, sync):
    v,n=bits(fn); s=bin(v)[2:].zfill(n); s2=s+s[:4096]
    pat=format(sync,'016b'); out=[];i=s2.find(pat)
    while i!=-1 and i<n: out.append(i); i=s2.find(pat,i+1)
    return s2,out
def syncstats(fn):
    v,n=bits(fn); s=bin(v)[2:].zfill(n)
    c=collections.Counter()
    for sync in (0x4489,0x8914,0x4521,0x2245,0xA245,0x8912,0x9521,0x5224,0xA144,0x448A,0x4A84):
        k=s.count(format(sync,'016b'))
        if k: c[hex(sync)]=k
    return c
if __name__=='__main__':
    for t in range(0,168):
        fn=f'tracks/t{t:03d}.bin'
        import os
        if os.path.getsize(fn)==0: continue
        print(t, dict(syncstats(fn)))
