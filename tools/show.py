import sys,capstone
D=open('main.bin','rb').read();B=0x80
md=capstone.Cs(capstone.CS_ARCH_M68K,capstone.CS_MODE_M68K_000)
a=int(sys.argv[1],16);e=int(sys.argv[2],16)
while a<e:
    i=next(md.disasm(D[a-B:a-B+12],a),None)
    if not i: print(f"{a:x} dc.w ${D[a-B:a-B+2].hex()}");a+=2;continue
    print(f"{a:x} {i.mnemonic} {i.op_str.replace(', ',',')}");a+=i.size
