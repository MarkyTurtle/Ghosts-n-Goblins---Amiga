"""Run the real Ghosts'n Goblins sound driver in a 68000 emulator and render Paula output to WAV."""
import struct, wave, sys
from unicorn import Uc, UC_ARCH_M68K, UC_MODE_BIG_ENDIAN, UC_HOOK_MEM_WRITE, UC_HOOK_MEM_READ
from unicorn.m68k_const import *
PAL_CLOCK=3546895; FPS=50; RATE=44100
RET=0x1ffff0; STACK=0x1f0000
class Driver:
    def __init__(self,fn,base):
        self.data=open(fn,'rb').read(); self.base=base
        u=self.u=Uc(UC_ARCH_M68K,UC_MODE_BIG_ENDIAN)
        try: u.ctl_set_cpu_model(UC_CPU_M68K_M68000)
        except Exception: pass
        u.mem_map(0,0x200000); u.mem_map(0xdff000,0x1000); u.mem_map(0xbfd000,0x2000)
        u.mem_write(base,self.data)
        u.mem_write(RET,b'\x4e\x71\x4e\x71')            # landing pad
        self.writes=[]
        u.hook_add(UC_HOOK_MEM_WRITE,self._w,begin=0xdff000,end=0xdff1ff)
        u.hook_add(UC_HOOK_MEM_READ,self._r,begin=0xdff01e,end=0xdff01f)
    def _w(self,uc,access,addr,size,value,ud):
        self.writes.append((addr-0xdff000,size,value))
    def _r(self,uc,access,addr,size,value,ud):
        uc.mem_write(0xdff01e,b'\x07\x80')              # audio IRQ request bits always set
    def call(self,cmd,arg=0):
        u=self.u
        u.reg_write(UC_M68K_REG_D0,((arg&0xffff)<<16)|cmd)
        sp=STACK-4; u.mem_write(sp,struct.pack('>I',RET)); u.reg_write(UC_M68K_REG_A7,sp)
        u.emu_start(self.base+0x20,RET,count=2000000)
    def vars(self):
        o=self.base+self.var_off
        return self.u.mem_read(o,0x350)
class Paula:
    def __init__(self,mem):
        self.mem=mem   # function(addr,n)->bytes
        self.ch=[dict(lc=0,len=0,per=0,vol=0,on=False,cur=0,clen=0,pos=0.0) for _ in range(4)]
    def write(self,reg,size,val):
        regs=[(reg,val)] if size==2 else [(reg,(val>>16)&0xffff),(reg+2,val&0xffff)]
        for r,v in regs:
            if r==0x96:
                for c in range(4):
                    if v&(1<<c):
                        ch=self.ch[c]
                        if v&0x8000:
                            if not ch['on']: ch['on']=True; ch['cur']=ch['lc']; ch['clen']=ch['len'] or 0x10000; ch['pos']=0.0
                        else: ch['on']=False
            elif 0xa0<=r<0xe0:
                c=(r-0xa0)>>4; o=(r-0xa0)&15; ch=self.ch[c]
                if o==0: ch['lc']=(ch['lc']&0xffff)|(v<<16)
                elif o==2: ch['lc']=(ch['lc']&0xffff0000)|(v&0xfffe)
                elif o==4: ch['len']=v
                elif o==6: ch['per']=v
                elif o==8: ch['vol']=min(v&0x7f,64)
    def render(self,nsamp):
        L=[0]*nsamp; R=[0]*nsamp
        for c,ch in enumerate(self.ch):
            if not ch['on'] or ch['per']<64: continue
            step=PAL_CLOCK/ch['per']/RATE; vol=ch['vol']
            buf=L if c in (0,3) else R
            nbytes=ch['clen']*2; data=self.mem(ch['cur'],nbytes); pos=ch['pos']
            for i in range(nsamp):
                ip=int(pos)
                if ip>=nbytes:
                    pos-=nbytes; ch['cur']=ch['lc']; ch['clen']=ch['len'] or 0x10000
                    nbytes=ch['clen']*2; data=self.mem(ch['cur'],nbytes); ip=int(pos)
                    if ip>=nbytes: pos=0; ip=0
                s=data[ip]; s=s-256 if s>127 else s
                buf[i]+=s*vol; pos+=step
            ch['pos']=pos
        return L,R
def render(fn,base,cmd,num,seconds,out,var_off,stop_when_silent=True):
    d=Driver(fn,base)
    p=Paula(lambda a,n: bytes(d.u.mem_read(a,n)))
    d.call(cmd,num)
    for w in d.writes: p.write(*w)
    d.writes.clear()
    frames=[]; per=RATE//FPS; quiet=0
    for t in range(int(seconds*FPS)):
        d.call(0)
        for w in d.writes: p.write(*w)
        d.writes.clear()
        L,R=p.render(per); frames.append((L,R))
        # stop when every voice pointer in this group is 0 and channels silent
        v=bytes(d.u.mem_read(base+var_off,0x350))
        first=4 if cmd==1 else 0x1a4
        active=any(struct.unpack('>I',v[first+k*0x68:first+k*0x68+4])[0] for k in range(4))
        if stop_when_silent and not active:
            quiet+=1
            if quiet>FPS: break
        else: quiet=0
    w=wave.open(out,'wb'); w.setnchannels(2); w.setsampwidth(2); w.setframerate(RATE)
    buf=bytearray()
    for L,R in frames:
        for l,r in zip(L,R):
            buf+=struct.pack('<hh',max(-32768,min(32767,l*2)),max(-32768,min(32767,r*2)))
    w.writeframes(bytes(buf)); w.close()
    return len(frames)/FPS
if __name__=='__main__':
    fn,base,cmd,num,sec,out,varoff=sys.argv[1],int(sys.argv[2],16),int(sys.argv[3]),int(sys.argv[4]),float(sys.argv[5]),sys.argv[6],int(sys.argv[7],16)
    print(render(fn,base,cmd,num,sec,out,varoff))
