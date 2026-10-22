import json,re,sys,os
sys.path.insert(0,'.')
from hw import CUSTOM,CIAA,CIAB
import importlib
A=importlib.import_module('anno_db') if os.path.exists('anno_db.py') else None
NAMES=getattr(A,'NAMES',{}); REGIONS=getattr(A,'REGIONS',[]); OBJF=getattr(A,'OBJ_FIELDS',{}); OBJR=getattr(A,'OBJ_RANGES',[]);
try:
    import anno_auto; AUTO=anno_auto.AUTO_COMMENTS
    for _k,_v in getattr(anno_auto,'AUTO_NAMES',{}).items():
        NAMES.setdefault(_k,_v)
except Exception: AUTO={}
DBLK=getattr(A,'DATA_BLOCKS',{}); TYPEF=getattr(A,'TYPE_FIELDS',[]); VRANGES=getattr(A,'VAR_RANGES',[])
HDR=getattr(A,'HEADERS',{}); CMT=getattr(A,'COMMENTS',{})
VARS=getattr(A,'VARS',{}); MEM=getattr(A,'MEM',{}); DATAFMT=getattr(A,'DATAFMT',{})
BASE=0x80
D=open('main.bin','rb').read(); IMG_END=BASE+len(D)
t=json.load(open('trace.json'))
ins={int(k,16):v for k,v in t['insn'].items()}
labkind={int(k,16):v for k,v in t['labels'].items()}
seeds=json.load(open('seeds.json')); orph={int(x,16) for x in seeds.get('orphans',[])}
starts=sorted(ins)
# overlap check
inside={}
for a in starts:
    for k in range(1,ins[a][0]): inside[a+k]=a
ov=[a for a in starts if a in inside]
if ov: print('OVERLAP',[hex(x) for x in ov],file=sys.stderr)
HEX=re.compile(r'\$([0-9a-f]+)')
refs={}   # addr->kind
def addref(a,k):
    if BASE<=a<IMG_END: refs.setdefault(a,k)
for a,(sz,m,op,hx) in ins.items():
    for mm in re.finditer(r'\$([0-9a-f]+)\(pc',op): addref(int(mm.group(1),16),'dat')
    for mm in re.finditer(r'(?<![#\w])\$([0-9a-f]+)\.l',op): addref(int(mm.group(1),16),'dat')
for a,k in labkind.items(): refs[a]={'sub':'sub','entry':'sub','jtab':'jtab'}.get(k,'lbl')
def lname(a):
    if a in NAMES: return NAMES[a][0] if isinstance(NAMES[a],tuple) else NAMES[a]
    k=refs.get(a,'lbl')
    if a not in ins: k='dat'
    pre=''
    for s0,e0,p in REGIONS:
        if s0<=a<e0 and k=='sub': pre=p
    if pre: return pre+f'{a:05X}'
    return {'sub':'sub','lbl':'l','jtab':'jtab','dat':'dat'}[k]+f'_{a:05X}'
# labels must be global for local-less naming; use L_ prefix for branch labels
def lab(a):
    if a in refs or a in NAMES:
        if a in ins or not (a in inside):
            return lname(a)
    if a in inside:
        b=inside[a]; return f'{lab(b)}+{a-b}'
    return None
allabels=set(refs)|set(k for k in NAMES if BASE<=k<IMG_END)
def symaddr(a):
    if BASE<=a<IMG_END:
        if a in allabels and not a in inside: return lname(a)
        if a in inside and inside[a] in allabels: return f'{lname(inside[a])}+{a-inside[a]}'
        # nearest label below
        return None
    return None
def ext(v):
    return f'${v:X}'
REG=re.compile(r'\b(a[0-7]|d[0-7])\b')
def convert(a,m,op,state):
    base=m.split('.')[0]
    o=op
    # branch target
    isbr = base in('bra','bsr') or base.startswith('db') or (base.startswith('b') and base not in('btst','bchg','bclr','bset'))
    if isbr:
        tgt=int(HEX.findall(o)[-1],16); s=symaddr(tgt) or ext(tgt)
        o=re.sub(r'\$[0-9a-f]+$',s,o)
    def pcsub(mm):
        v=int(mm.group(1),16); s=symaddr(v); return (s or f'${v:x}')+'(pc'
    o=re.sub(r'\$([0-9a-f]+)\(pc',pcsub,o)
    def abssub(mm):
        v=int(mm.group(1),16); sz=mm.group(2)
        if v==0xdff000: return 'CUSTOM'
        if 0xdff000<=v<0xdff200 and (v-0xdff000) in CUSTOM: return 'CUSTOM+'+CUSTOM[v-0xdff000]
        if 0xbfe001<=v<0xbff000 and (v-0xbfe001) in CIAA: return CIAA[v-0xbfe001]
        if 0xbfd000<=v<0xbfe000 and (v-0xbfd000) in CIAB: return CIAB[v-0xbfd000]
        if v in MEM and sz=='.l': return f'({MEM[v]}).l'
        if v in MEM and sz=='.w': return f'({MEM[v]}).w'
        if sz=='.l':
            s=symaddr(v)
            if s: return f'({s}).l'
        return mm.group(0)
    o=re.sub(r'(?<![#\w-])\$([0-9a-f]+)(\.[wl])',abssub,o)
    # custom base register offsets
    def regoff(mm):
        off=int(mm.group(1),16); r=mm.group(2)
        if state.get(r)=='custom' and off in CUSTOM: return f'{CUSTOM[off]}({r})'
        if r=='a6' and off in VARS: return f'{VARS[off][0]}(a6)'
        if r=='a6':
            for v0,n0 in VRANGES:
                if v0<off<v0+n0 and v0 in VARS: return f'{VARS[v0][0]}+{off-v0}(a6)'
        if r=='a5':
            for lo,hi,fm in TYPEF:
                if lo<=a<hi and off in fm: return f'{fm[off][0]}(a5)'
        if r=='a5' and off in OBJF and any(lo<=a<hi for lo,hi in OBJR): return f'{OBJF[off][0]}(a5)'
        return mm.group(0)
    o=re.sub(r'(?<![\w$-])\$([0-9a-f]+)\((a[0-7])\)',regoff,o)
    if r'(a6)' in o and re.search(r'(?<![\w$-])\(a6\)',o) and 0 in VARS and state.get('a6')!='x':
        o=re.sub(r'(?<![\w$-])\(a6\)',f'{VARS[0][0]}(a6)',o) if False else o
    # moveq range fix
    if base=='moveq':
        mm=re.match(r'#\$([0-9a-f]+), (d\d)',o); v=int(mm.group(1),16)
        if v>127: o=f'#{v-256}, {mm.group(2)}'
    # update state
    mm=re.match(r'^\$dff000\.l, (a\d)$',op)
    if base=='lea' and mm: state[mm.group(1)]='custom'
    else:
        dst=op.split(', ')[-1] if ', ' in op else ''
        if re.fullmatch(r'a\d',dst): state.pop(dst,None)
        for r in re.findall(r'\((a\d)\)\+|-\((a\d)\)',op):
            for x in r:
                if x: state.pop(x,None)
    if base in('rts','rte','bra','jmp'): state.clear()
    return o
out=[]
out.append(__import__('readable').with_equates(open('prelude.s').read()))
a=BASE; state={}
def emit_data(a,e):
    # emit bytes a..e
    fmt=DATAFMT.get(a)
    lines=[]
    p=a
    while p<e:
        q=min(e,p+16)
        # string detection
        seg=D[p-BASE:e-BASE]
        k=0
        while k<len(seg) and 32<=seg[k]<127 and seg[k]!=0x27: k+=1
        if k>=6:
            lines.append(f"\tdc.b\t'{seg[:k].decode()}'"); p+=k; continue
        if fmt=='w' and (q-p)%2==0 and p%2==0:
            lines.append('\tdc.w\t'+','.join(f'${int.from_bytes(D[i-BASE:i-BASE+2],"big"):04X}' for i in range(p,q,2)))
        else:
            # stop string-able runs from breaking: emit up to next potential string start
            j=p
            while j<q:
                s2=D[j-BASE:e-BASE]; k2=0
                while k2<len(s2) and 32<=s2[k2]<127 and s2[k2]!=0x27: k2+=1
                if k2>=6 and j>p: break
                j+=1
            q=j
            lines.append('\tdc.b\t'+','.join(f'${b:02X}' for b in D[p-BASE:q-BASE]))
        p=q
    return lines
bounds=sorted(set([x for x in allabels if BASE<=x<IMG_END and x not in inside])|set(starts))
while a<IMG_END:
    if a in HDR:
        out.append(''); out.append(';'+'-'*75)
        for l in HDR[a].strip('\n').split('\n'): out.append('; '+l if l else ';')
        out.append(';'+'-'*75)
    if a in DBLK:
        e_,blines=DBLK[a]
        for x in allabels:
            if a<x<e_ and x not in inside and not any(l.startswith(lname(x)+':') for l in blines):
                raise SystemExit(f'label {lname(x)} inside data block {a:X}-{e_:X} is not defined by it')
        out.extend(blines); a=e_; continue
    if a in allabels and a not in inside:
        nm=lname(a)
        extra=''
        if a in orph: extra='\t; (no references found - unused/debug code)'
        out.append(f'{nm}:{extra}')
    if a in ins:
        sz,m,op,hx=ins[a]
        o=convert(a,m,op,state)
        if m.split('.')[0] in ('btst','bchg','bclr','bset'): m=m.split('.')[0]
        line=f'\t{m}\t{o.replace(", ",",")}'.rstrip()
        c=CMT.get(a) or AUTO.get(a)
        line=line.expandtabs(8)
        line=line.ljust(48)+f'; {a:05X}'+(f'  {c}' if c else '')
        out.append(line)
        a+=sz
    else:
        state={}
        e=a+1
        while e<IMG_END and e not in ins and not (e in allabels and e not in inside) and e not in HDR and e not in DBLK: e+=1
        for l in emit_data(a,e): out.append(l)
        a=e
out=__import__('readable').process(out)
open('gng_main.s','w').write('\n'.join(out)+'\n')
print('lines',len(out))
