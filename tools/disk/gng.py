"""Decode the original disk's custom tracks (sync $A245, 6,312 data bytes a track) from raw
MFM track dumps (tracks/tNNN.bin): the first decoder; mkdisk.py and extract_files.py are the
tools to use now."""
import sys,os,struct
M=0x55555555
def load(fn):
    d=open(fn,'rb').read(); n=len(d)*8; s=bin(int.from_bytes(d,'big'))[2:].zfill(n); return s+s,n
def decode(t):
    fn=f'tracks/t{t:03d}.bin'
    if os.path.getsize(fn)==0: return None
    s,n=load(fn); pat=format(0xA245,'016b'); res=[]
    i=s.find(pat)
    while i!=-1 and i<n:
        p=i+16+16  # skip sync + first stored word (loader starts at $7C002)
        w=lambda k: int(s[p+k*16:p+k*16+16],2)
        hdr=((w(0)&0x5555)<<1)|(w(1)&0x5555)
        q=p+32
        L=lambda k: int(s[q+k*32:q+k*32+32],2)
        out=[];cs=0
        for k in range(0x62A):
            v=(L(k+0x62B)&M)|((L(k)&M)<<1); v&=0xffffffff; out.append(v); cs=(cs+v)&0xffffffff
        ck=(L(0x62A+0x62B)&M)|((L(0x62A)&M)<<1)
        res.append((hdr,((~cs)&0xffffffff)==ck,b''.join(struct.pack('>I',x) for x in out),i))
        i=s.find(pat,i+1)
    return res
if __name__=='__main__':
    os.makedirs('dec',exist_ok=True)
    for t in range(1,168):
        r=decode(t)
        if r is None: continue
        good=[x for x in r if x[1]]
        print(t, [(hex(x[0]),x[1]) for x in r])
        if good: open(f'dec/t{t:03d}.bin','wb').write(good[0][2])
