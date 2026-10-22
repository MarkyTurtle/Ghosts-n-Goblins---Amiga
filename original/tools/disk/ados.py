"""Decode the AmigaDOS-format (11-sector, $4489 sync) tracks of a raw MFM track dump: used
while reading the original disk image (track 0, the bootblock, is a standard AmigaDOS track)."""
import sys
def load(fn):
    d=open(fn,'rb').read(); n=len(d)*8; v=int.from_bytes(d,'big'); s=bin(v)[2:].zfill(n); return s+s[:20000],n
def rd(s,pos,nlong):
    # read nlong 32-bit MFM longs (each 32 bits raw -> 16? no: amiga long = 64 raw bits split odd/even)
    return [int(s[pos+i*32:pos+i*32+32],2) for i in range(nlong)]
def decode_oddeven(raw, nlong):
    odd=raw[:nlong]; even=raw[nlong:2*nlong]
    return [((o&0x55555555)<<1)|(e&0x55555555) for o,e in zip(odd,even)]
def ados_track(fn):
    s,n=load(fn); pat='0100010010001001'*2; out={}
    i=s.find(pat)
    while i!=-1 and i<n:
        p=i+32
        hdr=decode_oddeven(rd(s,p,2),1)[0]; p+=64
        fmt,trk,sec,left=(hdr>>24)&255,(hdr>>16)&255,(hdr>>8)&255,hdr&255
        p+=8*32  # label
        p+=2*32  # hdr chk
        dchk=decode_oddeven(rd(s,p,2),1)[0]; p+=64
        raw=rd(s,p,256); data=decode_oddeven(raw,128)
        c=0
        for x in raw: c^=x
        c&=0x55555555
        out[sec]=(b''.join(x.to_bytes(4,'big') for x in data), c==dchk, trk, fmt)
        i=s.find(pat,i+64)
    return out
if __name__=='__main__':
    o=ados_track(sys.argv[1])
    for k in sorted(o): print(k,o[k][1],o[k][2],hex(o[k][3]),o[k][0][:16].hex())
