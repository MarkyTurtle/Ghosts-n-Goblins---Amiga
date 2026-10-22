import capstone,re
D=open('../bin/bootblock.bin','rb').read()
md=capstone.Cs(capstone.CS_ARCH_M68K,capstone.CS_MODE_M68K_000)
# code ranges executed: $0C-$6A in place, $6A-$31A copied to $7FC00 (pc-relative, so labels stay valid)
code=[(0x0C,0x31A)]
ins={}
for s,e in code:
    a=s
    while a<e:
        i=next(md.disasm(D[a:a+12],a),None)
        ins[a]=(i.size,i.mnemonic,i.op_str); a+=i.size
names={0x0C:'BootEntry',0x6A:'Loader',0x196:'SeekTrack0',0x1AE:'SeekTrack',0x1EE:'StepHead',0x234:'LoadTracks',
       0x2FE:'Level3IRQ',0x31A:'CopperListA',0x34E:'CopperListB',0x382:'LoadScreenPalette'}
hdr={0x0C:"""Bootblock entry - called by Kickstart's boot code with a6 = ExecBase.
Kills all interrupts and DMA. Points the privilege-violation vector ($20)
at the next instruction, then executes MOVE #$2000,SR: in supervisor mode
that simply sets SR, in user mode it traps to the same place - so either
way the CPU continues in supervisor mode at IPL 0. Then works out where
the main program can go, copies the loader to $7FC00 and jumps to it.""",
0x6A:"""Loader - runs from $7FC00 (copied from bootblock offset $6A).
 1. fade COLOR00 from white to black over 16 frames
 2. set up CIA-B drive control, select DF0, motor on, seek to track 0
 3. load $18300 bytes from track 1 to $60000 (loading picture)
 4. show it: HAM6 interlaced (BPLCON0 $6804), two copper lists
    swapped on the long-frame bit by Level3IRQ
 5. load $18A80 bytes of main program:
      $4.w == 0 (512K):   from track 110 to $80
      otherwise:          from track 17 to the address in $4.w
 6. motor off and JMP $20(base) - first code byte after the hunk header""",
0x196:"Step outward until CIA-A PRA bit 4 (/TRK0) goes low; LDR cylinder = 0",
0x1AE:"Seek to cylinder ($28.w >> 1) and select head ($28.w bit 0)",
0x1EE:"One step pulse, then wait on CIA-B TOD: $2F ticks, $11D after a direction change",
0x234:"""LoadTracks - a5 = destination, d7 = tracks-1, $28.w = first track
DSKSYNC $A245, MFM read of $1900 words to $7C000 per track.
Track block: track number word, $62A longs data (odd then even bits,
$18AC bytes apart), checksum long = NOT(sum of data).
8 tries per track; wrong track number -> recalibrate and retry.""",
0x2FE:"Level 3 IRQ: acknowledge, select copper list by the long-frame bit (interlace)",
0x31A:"Copper lists: bitplane pointers for even/odd fields of the interlaced picture",
0x382:"Loading-screen palette (16 colours)"}
cmt={0x12:'INTENA: disable all',0x18:'DMACON: disable all',0x1E:'privilege-violation vector -> next instr',
0x28:'supervisor, IPL 0',0x2C:'ExecBase',0x30:'Exec above 512K? use that region',0x38:'stack above $80000? (1MB chip)',
0x40:'-> load main program at $80000',0x46:'$4.w = main program base (0 = load at $80)',0x4A:'stack = $80000 + base',
0x52:'copy $CE longs of loader to $7FC00',0x68:'run the loader',0x6E:'COLOR00 = white, fade down',
0x7C:'wait VBL',0x94:'CIA-B CRB: TOD counts',0xA6:'deselect all drives',0xA8:'motor on',0xAC:'select DF0',
0xB0:'seek track 0',0xB4:'loading screen -> $60000',0xBA:'$18300 bytes',0xC8:'/6312 bytes per track',
0xCE:'start at track 1',0xE8:'BPLEN off',0xEE:'BPLCON0 $6804: 6 planes, HAM, interlace',
0x128:'COP1LC = list A',0x130:'COP2LC = list B',0x13C:'level 3 vector',0x142:'enable VERTB',0x148:'DMA: bitplanes + copper',
0x14E:'main program: $18A80 bytes',0x162:'$4.w == 0 -> 512K machine',0x168:'load to $80',0x172:'from track 110',
0x17A:'expanded memory: load to base',0x17C:'from track 17',0x186:'motor off',0x192:'enter main program',
0x256:'DSKSYNC = $A245',0x25C:'DSKPT = $7C000',0x264:'DSKLEN = $1900 words (written twice)',
0x270:'wait DSKBLK',0x2A2:'$62A longs',0x2CA:'checksum = NOT(sum)',0x2E4:'expected track?'}
labels=set(names)
for a,(sz,m,op) in ins.items():
    b=m.split('.')[0]
    if b in('bra','bsr') or b.startswith('db') or (b.startswith('b') and b not in('btst','bchg','bclr','bset')):
        labels.add(int(re.findall(r'\$([0-9a-f]+)',op)[-1],16))
    for mm in re.finditer(r'\$([0-9a-f]+)\(pc',op): labels.add(int(mm.group(1),16))
def ln(a): return names.get(a,f'.L{a:03X}' if a in ins else f'D{a:03X}')
out=["; Ghosts'n Goblins (Elite, 1990, v3) - bootblock (track 0, sectors 0-1)",
"; Assemble: vasmm68k_mot -Fbin -m68000 -no-opt -o boot.bin gng_boot.s","","\torg\t0","",
"\tdc.b\t'DOS',0\t\t\t; DOS bootblock id",f"\tdc.l\t${int.from_bytes(D[4:8],'big'):08X}\t\t; bootblock checksum",
"\tdc.l\t0\t\t\t; root block (unused)"]
a=0x0C
while a<1024:
    if a in hdr:
        out+=['',';'+'-'*70]+['; '+l for l in hdr[a].split('\n')]+[';'+'-'*70]
    if a in labels or a in names: out.append(ln(a)+':')
    if a in ins:
        sz,m,op=ins[a]
        def rep(mm):
            v=int(mm.group(1),16); return ln(v)
        b=m.split('.')[0]
        if b in('btst','bchg','bclr','bset'): m=b
        isbr= b in('bra','bsr') or b.startswith('db') or (b.startswith('b') and b not in('btst','bchg','bclr','bset'))
        if isbr: op=re.sub(r'\$([0-9a-f]+)$',rep,op)
        op=re.sub(r'\$([0-9a-f]+)\(pc',lambda mm: ln(int(mm.group(1),16))+'(pc',op)
        if m=='moveq':
            mm=re.match(r'#\$([0-9a-f]+), (d\d)',op); v=int(mm.group(1),16)
            if v>127: op=f'#{v-256}, {mm.group(2)}'
        line=(f'\t{m}\t{op.replace(", ",",")}').expandtabs(8).ljust(44)+f'; {a:03X}'+(f'  {cmt[a]}' if a in cmt else '')
        out.append(line); a+=sz
    else:
        e=a+1
        while e<1024 and e not in labels and e not in hdr: e+=1
        if all(b==0 for b in D[a:e]) and e-a>8:
            out.append(f'\tdcb.b\t{e-a},0'); a=e; continue
        for p in range(a,e,16): out.append('\tdc.w\t'+','.join(f'${int.from_bytes(D[q:q+2],"big"):04X}' for q in range(p,min(e,p+16),2)))
        a=e
# fix label lines
fixed=[]
for l in out:
    if re.fullmatch(r'\.?[A-Za-z_][\w]*:',l) and l.startswith('.'): l=l
    fixed.append(l)
open('gng_boot.s','w').write('\n'.join(fixed)+'\n')
