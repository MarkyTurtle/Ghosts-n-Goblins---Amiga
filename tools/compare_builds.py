import capstone,difflib,re
md=capstone.Cs(capstone.CS_ARCH_M68K,capstone.CS_MODE_M68K_000)
def lin(fn,base):
    D=open(fn,'rb').read(); out=[]; a=0x20
    end=0x20+int.from_bytes(D[0x14:0x18],'big')*4
    while a<end:
        i=next(md.disasm(D[a:a+12],base+a),None)
        if not i: out.append((base+a,'dc.w',D[a:a+2].hex())); a+=2; continue
        op=re.sub(r'\$[0-9a-f]+','N',i.op_str)  # normalise addresses/immediates
        out.append((base+a,i.mnemonic,op)); a+=i.size
    return out
A=lin('../bin/main_512k.bin',0x80); Bh=lin('../bin/main_1mb.bin',0)
sa=[m+' '+o for _,m,o in A]; sb=[m+' '+o for _,m,o in Bh]
sm=difflib.SequenceMatcher(None,sa,sb,autojunk=False)
import json
code={int(k,16) for k in json.load(open('trace.json'))['insn']}
for tag,i1,i2,j1,j2 in sm.get_opcodes():
    if tag=='equal': continue
    ca=[x for x in A[i1:i2] if x[0] in code]
    if not ca and tag!='insert': continue
    a0=A[min(i1,len(A)-1)][0]
    print(f'== {tag} 512K ${a0:05X} ({i2-i1} ins, {len(ca)} traced)  1MB +${Bh[min(j1,len(Bh)-1)][0]:05X} ({j2-j1})')
    for x in A[i1:min(i2,i1+6)]: print('   512K',f'{x[0]:05X}',x[1],x[2])
    for x in Bh[j1:min(j2,j1+6)]: print('   1MB ',f'+{x[0]:05X}',x[1],x[2])
