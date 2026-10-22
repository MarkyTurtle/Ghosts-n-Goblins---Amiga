"""How long a tune plays: channel_length() follows a channel's voice bytecode (NOTE / REST
durations, CALL / CALLN patterns expanded) to the end or the JUMP that loops it; used for
the tune lengths in SOUND.md."""
import struct
def channel_length(f,start):
    """Ticks for one pass of a channel: expands CALL/CALLN repeats; stops at END or JUMP. Returns (ticks, ended_by)."""
    d=f.d
    def run(a,depth=0):
        t=0
        while True:
            b=d[a]; c=b&0x7f
            if c<0x60: t+=d[a+2]; a+=4; continue
            if c==0x60: t+=(d[a+1]<<8)|d[a+2]; a+=4; continue
            if c==0x63: a+=2; continue
            if c in (0x64,0x65):
                p=d[a+1]; n=(d[a+3]+1) if c==0x65 else 1
                sub,how=run(f.pattern_ptr(p),depth+1); t+=sub*n; a+=4 if c==0x65 else 3; continue
            if c==0x66: return t,'return'
            if c==0x67: return t,'end'
            if c==0x68: return t,'loop'
            if c==0x69: a+=2; continue
            a+=1
    return run(start)
