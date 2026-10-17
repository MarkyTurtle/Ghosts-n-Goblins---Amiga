import sys,capstone
d=open(sys.argv[1],'rb').read()
base=int(sys.argv[2],16) if len(sys.argv)>2 else 0
start=int(sys.argv[3],16) if len(sys.argv)>3 else 0
end=int(sys.argv[4],16) if len(sys.argv)>4 else len(d)
md=capstone.Cs(capstone.CS_ARCH_M68K,capstone.CS_MODE_M68K_000)
p=start
while p<end:
    got=False
    for i in md.disasm(d[p:end],base+p):
        print(f"{i.address:06x}  {i.bytes.hex():<20} {i.mnemonic:<8} {i.op_str}"); p=i.address-base+i.size; got=True
    if p<end:
        print(f"{base+p:06x}  {d[p:p+2].hex():<20} dc.w     ${d[p:p+2].hex()}"); p+=2
