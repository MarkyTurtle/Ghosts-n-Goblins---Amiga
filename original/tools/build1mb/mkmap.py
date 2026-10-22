# Build an address map 512K build (absolute, base $80) -> 1MB build (file offset, base 0)
import capstone,difflib,re,json,collections
md=capstone.Cs(capstone.CS_ARCH_M68K,capstone.CS_MODE_M68K_000)
A_D=open('../main.bin','rb').read(); B_D=open('../../bin/main_1mb.bin','rb').read()
TA={int(k,16) for k in json.load(open('../trace.json'))['insn']}
TB={int(k,16) for k in json.load(open('trace1m.json'))['insn']}
def lin(D,base):
    T=TA if base else TB
    out=[];a=0x20;end=len(D)
    while a<end:
        i=next(md.disasm(D[a:a+12],base+a),None) if base+a in T else None
        if not i: out.append((base+a,2,'dc.w',D[a:a+2].hex(),'')); a+=2; continue
        out.append((base+a,i.size,i.mnemonic,re.sub(r'\$[0-9a-f]+','N',i.op_str),i.op_str)); a+=i.size
    return out,base+end
A,AE=lin(A_D,0x80); B,BE=lin(B_D,0)
sm=difflib.SequenceMatcher(None,[x[2]+' '+x[3] for x in A],[x[2]+' '+x[3] for x in B],autojunk=False)
amap={}      # exact instruction-start map
pairs=[]     # (512k insn, 1mb insn) for equal blocks
blocks=[]
for tag,i1,i2,j1,j2 in sm.get_opcodes():
    blocks.append((tag,i1,i2,j1,j2))
    if tag=='equal':
        for k in range(i2-i1):
            a,b=A[i1+k],B[j1+k]; amap[a[0]]=b[0]; pairs.append((a,b))
# ---- verify matched pairs: branch / pc-relative targets must map onto each other and
# immediates must be equal; otherwise the pair is code that changed between builds.
import bisect
def tgt(op,m):
    r=[int(x,16) for x in re.findall(r'\$([0-9a-f]+)\(pc',op)]
    base=m.split('.')[0]
    if base in('bra','bsr') or base.startswith('db') or (base.startswith('b') and base not in('btst','bchg','bclr','bset')):
        r.append(int(re.findall(r'\$([0-9a-f]+)',op)[-1],16))
    return r
def imms(op): return re.findall(r'#(-?\$?[0-9a-f]+)',op)
for it in range(3):
    ks=sorted(amap)
    def addr(x):
        if x in amap: return amap[x]
        i=bisect.bisect_right(ks,x); lo=ks[i-1] if i else None; hi=ks[i] if i<len(ks) else None
        if lo is not None and hi is not None and amap[lo]-lo==amap[hi]-hi: return x+amap[lo]-lo
        return None
    bad=[]
    for a,b in pairs:
        ta=tgt(a[4],a[2]); tb=tgt(b[4],b[2])
        if any(addr(x) is not None and addr(x)!=y for x,y in zip(ta,tb)) or imms(a[4])!=imms(b[4]): bad.append((a,b))
    if not bad: break
    for a,b in bad: amap.pop(a[0],None)
    badset={id(p) for p in bad}
    pairs=[p for p in pairs if (p[0][0] in amap)]
    print('pass',it,'unmatched',len(bad))
CHANGED=[]
# a6 offsets and absolute values seen in matched pairs
HEX=re.compile(r'\$([0-9a-f]+)')
a6diff=collections.Counter(); absmap=collections.defaultdict(collections.Counter)
for a,b in pairs:
    ha=HEX.findall(a[4]); hb=HEX.findall(b[4])
    if len(ha)!=len(hb): continue
    for x,y,ta in zip(ha,hb,re.findall(r'\$[0-9a-f]+(\S*)',a[4])):
        x=int(x,16); y=int(y,16)
        if ta.startswith('(a6'): 
            if x!=y: a6diff[(x,y)]+=1
        elif ta.startswith('.l') and x!=y: absmap[x][y]+=1
print('matched insns',len(pairs),'of',len(A),len(B))
print('a6 offset differences',a6diff.most_common(10))
# per-block delta for abs value pairs (map memory equates)
mem={}
for x,c in absmap.items():
    y,n=c.most_common(1)[0]; mem[x]=y
print('abs value pairs',len(mem))
EQB=[(A[i1+k],B[j1+k]) for tag,i1,i2,j1,j2 in blocks if tag=='equal' for k in range(i2-i1)]
json.dump({'amap':{hex(k):v for k,v in amap.items()},'mem':{hex(k):v for k,v in mem.items()},
           'A_end':AE,'B_end':BE,'blocks':blocks},open('map.json','w'))
same=collections.Counter()
allp=collections.defaultdict(collections.Counter)
for a,b in pairs:
    for x,y in zip(re.findall(r'(-?\$[0-9a-f]+|)\(a6',a[4]),re.findall(r'(-?\$[0-9a-f]+|)\(a6',b[4])):
        xv=int(x.replace('$',''),16) if x else 0; yv=int(y.replace('$',''),16) if y else 0
        allp[xv][yv]+=1
bad={x:c for x,c in allp.items() if len(c)>1}
print('inconsistent',{hex(k):dict(v) for k,v in bad.items()})
d=collections.Counter((y-x) for x,c in allp.items() for y in c)
print('deltas',d)
print('offsets with delta 0', sorted(hex(x) for x,c in allp.items() if list(c)[0]==x)[:40])
print('min off delta4', hex(min(x for x,c in allp.items() if list(c)[0]-x==4)))
json.dump({hex(x):list(c)[0] for x,c in allp.items()},open('a6map.json','w'))
# ---- notes on every place the builds differ (traced code only)
import sys; sys.path.insert(0,'..'); import anno_db; MEM512=set(anno_db.MEM)
notes={}; only1m=[]; symok=[]
for a,b in EQB:
    if a[0] in TA and a[0] not in amap:
        only1m.append(b[0]); notes[b[0]]=f'changed from the 512K build (${a[0]:05X}: {a[2]} {a[4]})'
A_IMG=(0x80,0x80+len(A_D))
for a,b in pairs:
    for x in re.findall(r'(?<![#\w-])\$([0-9a-f]+)\.l',a[4]):
        if A_IMG[0]<=int(x,16)<A_IMG[1] and int(x,16) not in MEM512: symok.append(b[0])
for tag,i1,i2,j1,j2 in blocks:
    if tag=='equal': continue
    ca=[x for x in A[i1:i2] if x[0] in TA]; cb=[x for x in B[j1:j2] if x[0] in TB]
    if not ca and not cb: continue
    for x in cb: only1m.append(x[0])
    where=B[j1][0] if j1<len(B) else None
    if tag=='insert':
        t=f'1MB only: {len(cb)} instruction(s) not in the 512K build'
    elif tag=='delete':
        t=f'512K build has {len(ca)} more instruction(s) here (at ${ca[0][0]:05X}), removed in the 1MB build' if ca else None
    else:
        t=f'differs from the 512K build: {len(cb)} instruction(s) here replace {len(ca)} at ${ca[0][0]:05X}' if ca else f'1MB only: {len(cb)} instruction(s)'
    if t and where is not None:
        if tag=='delete':
            # attach to next traced 1MB instruction
            k=j1
            while k<len(B) and B[k][0] not in TB: k+=1
            where=B[k][0] if k<len(B) else where
        notes[where]=(notes[where]+'; '+t) if where in notes else t
json.dump({'notes':{hex(k):v for k,v in notes.items()},'only1m':only1m,'symok':symok},open('diff.json','w'))
print('diff notes',len(notes),'1MB-only instructions',len(only1m))
