import capstone,re,json,sys
BASE=0x80
D=open('main.bin','rb').read()
END=BASE+len(D)
CODE_END=0xa0+0x1888c
md=capstone.Cs(capstone.CS_ARCH_M68K,capstone.CS_MODE_M68K_000)
def dis1(a):
    for i in md.disasm(D[a-BASE:a-BASE+12],a): return i
    return None
seeds=json.load(open('seeds.json')) if __import__('os').path.exists('seeds.json') else {}
entries=[int(k,16) for k in seeds.get('code',[])]+[0xa0]
tables=seeds.get('jumptables',{})   # addr of table -> [count, kind]
insn={}       # addr -> (size, mnem, ops)
labels={}     # addr -> kind
indirect=[]
jtabs={}
pcrefs=set()
work=list(entries)
for e in entries: labels[e]='entry'
HEX=re.compile(r'\$([0-9a-f]+)')
while work:
    a=work.pop()
    while True:
        if a in insn or a<0xa0 or a>=CODE_END: break
        i=dis1(a)
        if i is None: print('BAD decode at',hex(a),file=sys.stderr); break
        m=i.mnemonic; op=i.op_str
        # overlap check
        insn[a]=(i.size,m,op,i.bytes.hex())
        nxt=a+i.size
        tgt=None
        base=m.split('.')[0]
        if base in('bra','bsr') or base.startswith('db') or (base.startswith('b') and base not in('btst','bchg','bclr','bset','bkpt')):
            tgt=int(HEX.findall(op)[-1],16)
        for mm in re.finditer(r'\$([0-9a-f]+)\(pc',op): pcrefs.add((int(mm.group(1),16),a,m))
        if base in('jmp','jsr'):
            mm=re.match(r'^\$([0-9a-f]+)(\.[wl])?$',op)
            if mm: tgt=int(mm.group(1),16)
            elif re.match(r'^\$([0-9a-f]+)\(pc\)$',op): tgt=int(HEX.findall(op)[0],16)
            elif re.match(r'^\$([0-9a-f]+)\(pc, d\d\.w\)$',op):
                T=int(HEX.findall(op)[0],16); k=0; tg=[]
                while True:
                    q=T+4*k
                    fw=[x for x in tg if x>T]
                    if q>=CODE_END or (fw and q>=min(fw)): break
                    w=D[q-BASE:q-BASE+2]
                    if w==b'\x60\x00': tg.append(q+2+int.from_bytes(D[q-BASE+2:q-BASE+4],'big',signed=True))
                    elif w[0]==0x60 and w[1]!=0 and D[q-BASE+2:q-BASE+4]==b'\x4e\x71': tg.append(q+2+int.from_bytes(w[1:2],'big',signed=True))
                    else: break
                    labels.setdefault(q,'lbl'); work.append(q); k+=1
                jtabs[T]=k
                labels[T]='jtab'
            else: indirect.append((a,m,op))
        if tgt is not None:
            labels.setdefault(tgt,'sub' if base in('bsr','jsr') else 'lbl')
            if base in('bsr','jsr'): labels[tgt]='sub'
            work.append(tgt)
        if base in('bra','jmp','rts','rte','rtr') or (m=='illegal'): break
        a=nxt
    # jump tables
for t,(cnt,kind) in tables.items():
    pass
json.dump({'insn':{hex(k):v for k,v in insn.items()},'labels':{hex(k):v for k,v in labels.items()},
  'indirect':[(hex(a),m,o) for a,m,o in indirect],'jtabs':{hex(k):v for k,v in jtabs.items()},'pcrefs':sorted([(hex(t),hex(a),m) for t,a,m in pcrefs])},open('trace.json','w'))
cov=sum(v[0] for v in insn.values())
print('instructions',len(insn),'code bytes',cov,'of',CODE_END-0xa0,'labels',len(labels))
print('jtabs',{hex(k):v for k,v in jtabs.items()})
print('indirect:',len(indirect))
for x in indirect: print('  ',hex(x[0]),x[1],x[2])
