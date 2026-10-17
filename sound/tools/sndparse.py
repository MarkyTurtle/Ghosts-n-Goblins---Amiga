"""Parser for the Richard Frankish / Mark Cooksey sound driver files used in Ghosts'n Goblins (Elite 1990)."""
import struct, sys, json
NOTE=['C-','C#','D-','D#','E-','F-','F#','G-','G#','A-','A#','B-']
CMD={0x60:'REST',0x61:'NOP61',0x62:'NOP62',0x63:'VOLUME',0x64:'CALL',0x65:'CALLN',0x66:'RETURN',0x67:'END',
     0x68:'JUMP',0x69:'PORTA_ON',0x6a:'NOP6A',0x6b:'PORTA_OFF'}
class SndFile:
    def __init__(self,fn):
        self.d=d=open(fn,'rb').read()
        rel=lambda o: o+2+struct.unpack('>h',d[o+2:o+4])[0]
        self.songtab=rel(0x48); self.calltab=rel(0x2fc); self.instab=rel(0x38e)
        self.pitch=rel(0x406); self.vars=rel(0x3e); self.smpbase=rel(0x174)
        self.code_end=0x5da
        self.sfxtab=rel(0xd6)
        self.nmusic=(self.sfxtab-self.songtab)//16
        self.nsfx=(self.instab-self.sfxtab)//16
        self.nsongs=self.nmusic+self.nsfx
        self.cov={}   # offset -> region tag
    def W(self,o): return struct.unpack('>H',self.d[o:o+2])[0]
    def L(self,o): return struct.unpack('>i',self.d[o:o+4])[0]
    def mark(self,a,n,tag):
        for i in range(n): self.cov.setdefault(a+i,tag)
    def table(self,base,n):
        out=[]
        for s in range(n):
            ch=[]
            for c in range(4):
                a=base+s*16+c*4; v=self.L(a); ch.append(a+v if v else None)
            out.append(ch)
        return out
    def music(self): return self.table(self.songtab,self.nmusic)
    def sfx(self): return self.table(self.sfxtab,self.nsfx)
    def ninstr(self):
        # instrument table: word self-relative offsets, until first record
        first=min(self.instab+2*i+self.W(self.instab+2*i) for i in range(1))
        n=0; lo=1<<30
        while self.instab+2*n<lo:
            lo=min(lo,self.instab+2*n+self.W(self.instab+2*n)); n+=1
        return n
    def instrument(self,i):
        a=self.instab+2*i; r=a+self.W(a)
        d=self.d
        s0,s1,ve,pe=struct.unpack('>iiii',d[r:r+16])
        l0,l1,m0,m1=struct.unpack('>HHHH',d[r+16:r+24])
        vs,ps=d[r+24],d[r+25]; vol=self.W(r+26)
        return dict(rec=r,attack=s0,loop=s1,venv=(r+8+ve) if ve else None,penv=(r+12+pe) if pe else None,
                    attack_len=l0,loop_len=l1,attack_mul=m0,loop_mul=m1,venv_speed=vs,penv_speed=ps,volume=vol,
                    attack_has=bool(s0) ,loop_has=bool(s1))
    def npatterns(self):
        n=(self.pitch-self.calltab)//2
        return n
    def pattern_ptr(self,p):
        a=self.calltab+2*p; return a+struct.unpack('>h',self.d[a:a+2])[0]
    def decode_stream(self,a,tag,maxlen=100000):
        """Decode a bytecode stream until END/RETURN/JUMP. Returns list of (addr,bytes,text)."""
        d=self.d; out=[]; seen=set()
        while a not in seen and len(out)<maxlen:
            seen.add(a); b=d[a]; c=b&0x7f
            if c<0x60:
                n,ins,dur,x=d[a],d[a+1],d[a+2],d[a+3]
                txt=f'NOTE {NOTE[n%12]}{n//12} (#{n:02X}) ins {ins} dur {dur} x{x:02X}' + (' [b7]' if b&0x80 else '')
                out.append((a,4,txt)); a+=4; continue
            k=0x60+(c-0x60)
            if k==0x60:
                dur=(d[a+1]<<8)|d[a+2]; out.append((a,4,f'REST dur {dur} x{d[a+3]:02X}')); a+=4; continue
            if k==0x63: out.append((a,2,f'VOLUME {d[a+1]}')); a+=2; continue
            if k==0x64: out.append((a,3,f'CALL pattern {d[a+1]} transpose {struct.unpack("b",d[a+2:a+3])[0]}')); a+=3; continue
            if k==0x65: out.append((a,4,f'CALL pattern {d[a+1]} transpose {struct.unpack("b",d[a+2:a+3])[0]} times {d[a+3]+1}')); a+=4; continue
            if k==0x66: out.append((a,1,'RETURN')); break
            if k==0x67: out.append((a,1,'END')); break
            if k==0x68:
                off=struct.unpack('>h',d[a+1:a+3])[0]; out.append((a,3,f'JUMP {a+off:05X}')); break
            if k==0x69: out.append((a,2,f'PORTA_ON speed {d[a+1]}')); a+=2; continue
            if k==0x6b: out.append((a,1,'PORTA_OFF')); a+=1; continue
            out.append((a,1,f'NOP ${b:02X}')); a+=1
        return out
if __name__=='__main__':
    f=SndFile(sys.argv[1])
    print(f'songtab {f.songtab:X} instab {f.instab:X} calltab {f.calltab:X} pitch {f.pitch:X} vars {f.vars:X} smpbase {f.smpbase:X} songs {f.nsongs} instr {f.ninstr()} patterns {f.npatterns()} filelen {len(f.d):X}')

def coverage(f):
    cov={}
    def mark(a,n,tag):
        for i in range(n): cov.setdefault(a+i,tag)
    mark(0,0x20,'hunk header'); mark(0x20,f.code_end-0x20,'driver code')
    mark(f.songtab,f.instab-f.songtab,'song tables')
    ni=f.ninstr(); mark(f.instab,2*ni,'instrument table')
    smp=[]
    streams=[]
    for tab in (f.music(),f.sfx()):
        for ch in tab:
            for p in ch:
                if p: streams.append(p)
    pats=set(); todo=list(streams); done=set()
    while todo:
        a=todo.pop()
        if a in done: continue
        done.add(a)
        for (x,n,t) in f.decode_stream(a,''):
            mark(x,n,'sequence/pattern data')
            if t.startswith('CALL'):
                p=int(t.split()[2]); pats.add(p); todo.append(f.pattern_ptr(p))
    np_=(max(pats)+1) if pats else 0
    mark(f.calltab,2*np_,'pattern table')
    mark(f.pitch,384*2+2,'pitch table'); 
    for i in range(ni):
        I=f.instrument(i); mark(I['rec'],28,'instrument records')
        for k in ('venv','penv'):
            if I[k]:
                a=I[k]
                while True:
                    b=f.d[a]; mark(a,1,'envelopes'); a+=1
                    if (k=='venv' and b==0) or (k=='penv' and b==0x80): break
        if I['attack'] or I['loop']:
            smp.append((I['attack'],I['attack_len'],I['loop'],I['loop_len']))
    mark(f.vars,f.smpbase-f.vars,'driver variables')
    for s0,l0,s1,l1 in smp:
        if s0: mark(f.smpbase+s0,2*l0,'sample data')
        if s1: mark(f.smpbase+s1,2*l1,'sample data')
    return cov,pats,smp
