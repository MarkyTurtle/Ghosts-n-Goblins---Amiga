"""Arthur's animation tables ($8BAC-$8C8A in the 512K build) as readable source.
Table: two word offsets (facing right, facing left) to scripts. Script: AFRAME frame,frames
... ending with ALOOP frame,frames,target (time byte negated, then a word offset back).
Frames for facing left are the mirrored copies, written ~n (= the NOT of frame n)."""
import struct
TABLES={0x8BAC:'ArthurAnims',0x8BD0:'ArthurAnimFrog',0x8BE8:'ArthurAnimJump',0x8BF4:'ArthurAnimJumpFwd',
 0x8C00:'ArthurAnimFrogJump',0x8C14:'ArthurAnimCrouch',0x8C20:'ArthurAnimThrow',0x8C30:'ArthurAnimThrowCrouch',
 0x8C4E:'ArthurAnimKnockback',0x8C5A:'ArthurAnimKnockbackBare',0x8C6A:'ArthurAnimDie1',0x8C7A:'ArthurAnimDie2'}
SCRIPTS={0x8C40:'ArthurAnimClimb',0x8C46:'ArthurAnimLadderTop1',0x8C4A:'ArthurAnimLadderTop2'}
START,END=0x8BAC,0x8C8A
def fr(b):
    return f'~{(~b)&0xff}' if b&0x80 else f'{b}'
def build(D,B=0x80):
    rb=lambda a:D[a-B]; rw=lambda a:struct.unpack('>h',D[a-B:a-B+2])[0]
    # find every script start / loop target
    names=dict(SCRIPTS); targets={}
    for t,n in TABLES.items():
        names[t]=n
        names.setdefault(t+rw(t),n+'_R'); names.setdefault(t+2+rw(t+2),n+'_L')
    a=START; lines=[]
    # first pass: loop targets
    scan=START
    while scan<END:
        if scan in TABLES: scan+=4; continue
        f,tm=rb(scan),rb(scan+1)
        if tm&0x80:
            tg=scan+2+rw(scan+2); targets[tg]=None; scan+=4
        else: scan+=2
    lab={}
    for tg in sorted(targets):
        if tg in names: lab[tg]=names[tg]
        else:
            owner=max(x for x in names if x<tg); lab[tg]=f'{names[owner]}_{tg-owner}'
    allnames={**names,**lab}
    for k,v in TABLES.items(): allnames[k]=v
    a=START
    while a<END:
        if a in allnames: lines.append(f'{allnames[a]}:')
        if a in TABLES:
            lines.append(f'\tdc.w\t{allnames[a+rw(a)]}-*,{allnames[a+2+rw(a+2)]}-*\t; facing right, facing left')
            a+=4; continue
        f,tm=rb(a),rb(a+1)
        if tm&0x80:
            tg=a+2+rw(a+2)
            lines.append(f'\tALOOP\t{fr(f)},{(-tm)&0xff},{allnames[tg]}'); a+=4
        else:
            lines.append(f'\tAFRAME\t{fr(f)},{tm}'); a+=2
    assert a==END, hex(a)
    labels={v:k for k,v in allnames.items()}
    return START,END,lines,labels
