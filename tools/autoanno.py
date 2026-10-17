"""Generate anno_auto.py: automatic line comments for the object/enemy code, plus a per-enemy fact sheet."""
import json, re, struct, collections, sys
sys.path.insert(0,'.')
t=json.load(open('trace.json'))
ins={int(k,16):v for k,v in t['insn'].items()}
D=open('main.bin','rb').read(); B=0x80
ENEMY={0xC65A:'WoodyPig',0xCBAC:'Crow',0xD160:'PetiteDevil',0xDA38:'FlyingKnight',0xDC8C:'BlueKiller',0xE1FA:'RedArremer',
 0xEE1C:'Satan',0xF422:'Magician',0xF5DC:'Unicorn',0x10082:'Skeleton',0x103BA:'BigMan',0x109C4:'Zombie',0x10CCE:'Dragon',
 0x11640:'Astaroth',0x119DA:'Fire',0x11B1A:'Princess/Plant',0x11CC8:'FirePillar'}
starts=sorted(ENEMY); 
def owner(a):
    for i,s in enumerate(starts):
        e=starts[i+1] if i+1<len(starts) else 0x121FA
        if s<=a<e: return ENEMY[s]
    return None
SFXN={1:'Arthur hit',4:'jump',5:'land',6:'throw',10:'weapon hit',11:'torch flame',12:'weapon/boss hit',17:'enemy event',20:'enemy event',28:'item collected'}
CALLS={0xBCC8:'sfx',0xAE9E:'score',0xC646:'shotslot',0xAE26:'Random',0xADA4:'DirectionToArthur',0xABC8:'SetAnim',0xABBC:'SetAnimIndexed',
 0xABD0:'Animate',0xAD7E:'ApplyMoveTable',0xAD1A:'CheckOnScreen',0xAD54:'CheckFarAway',0xC15E:'ObjectMapCollide',0xAB8E:'SetBoxClass',0xAC9E:'BossKilled'}
CMT={'shotslot':'find a free enemy-projectile slot (fires a shot)','Random':'random number','DirectionToArthur':'direction towards Arthur',
 'SetAnim':'start animation','SetAnimIndexed':'start animation for current direction','Animate':'animate','ApplyMoveTable':'move by the movement table',
 'CheckOnScreen':'visible?','CheckFarAway':'remove when far off-screen','ObjectMapCollide':'on the floor? (Z set = yes, Y snapped onto it)','SetBoxClass':'change size class','BossKilled':'boss defeated'}
def score(i):
    a=0xae42+4*(i-1)-B; v=D[a:a+4].hex().lstrip('0') or '0'; return v
out={}; facts=collections.defaultdict(lambda: collections.defaultdict(set))
keys=sorted(ins)
for n,a in enumerate(keys):
    if not (0xC646<=a<0x121FA or 0xABFC<=a<0xAC9E): continue
    sz,m,op,hx=ins[a]; who=owner(a); c=None
    prev=[ins[keys[n-k]] for k in range(1,4) if n-k>=0]
    if m.startswith(('bsr','jsr')):
        tg=re.findall(r'\$([0-9a-f]+)',op)
        if tg:
            kind=CALLS.get(int(tg[-1],16))
            if kind in ('sfx','score'):
                v=None
                for p in prev:
                    mm=re.match(r'#\$([0-9a-f]+), d0',p[2]) if p[1]=='moveq' else None
                    if mm: v=int(mm.group(1),16); break
                if kind=='sfx': c=f'sound effect {v}' + (f' ({SFXN[v]})' if v in SFXN else '') if v is not None else 'sound effect'
                else: c=f'score +{score(v)}' if v is not None else 'add score'
                if who and v is not None: facts[who][kind].add(v if kind=='sfx' else score(v))
            elif kind:
                c=CMT[kind]
                if who: facts[who]['calls'].add(kind)
    mm=re.match(r'#\$([0-9a-f]+), \$3\(a5\)$',op)
    if m=='move.b' and mm: c=f'-> state {int(mm.group(1),16)} ' + ['(spawn)','(active)','(hit/dying)','(remove)'][min(3,int(mm.group(1),16))]
    if m=='clr.b' and op=='$3(a5)': c='-> state 0 (spawn)'
    if m=='addq.b' and op=='#$1, $4(a5)': c='next step'
    if m=='clr.b' and op=='(a5)': c='free this enemy slot'
    if c: out[a]=c
    if who:
        if m=='move.b' and op.endswith('$1b(a5)'): facts[who]['hp'].add(op.split(',')[0])
open('anno_auto.py','w').write('AUTO_COMMENTS = '+repr(out)+'\n')
print('auto comments',len(out))
for s in starts:
    w=ENEMY[s]; f=facts[w]
    print(f'{w:15s} sfx={sorted(f["sfx"])} score={sorted(f["score"])} calls={sorted(f["calls"])} hp={sorted(f["hp"])}')

# ---- automatic names for state / step dispatch targets
jt={int(k,16):v for k,v in t['jtabs'].items()}
names={}
STN=['Main','State1','Killed','Remove']
def table_targets(T,n):
    out=[]
    for k in range(n):
        q=T+4*k; w=D[q-B:q-B+2]
        if w==b'\x60\x00': out.append(q+2+struct.unpack('>h',D[q-B+2:q-B+4])[0])
        else: out.append(q+2+struct.unpack('b',w[1:2])[0])
    return out
cur_state={}
for T in sorted(jt):
    if not (0xC646<=T<0x121FA): continue
    who=owner(T)
    if not who: continue
    # find the instruction that loaded d0 for this dispatch
    pre=[a for a in keys if T-24<=a<T]
    src=None
    for a in reversed(pre):
        if 'd0' in ins[a][2] and ins[a][1].startswith('move.b'):
            src=ins[a][2].split(',')[0]; break
    base=re.sub(r'[^A-Za-z0-9]','',who)
    tg=table_targets(T,jt[T])
    if src=='$3(a5)':
        for i,a in enumerate(tg):
            nm=f'{base}_{STN[i] if i<4 else "State"+str(i)}'
            names.setdefault(a,nm)
    elif src in ('$4(a5)','$5(a5)'):
        # which state routine are we in? nearest preceding named state
        lvl='Step' if src=='$4(a5)' else 'Sub'
        ok=(lambda n:'_Step' not in n and '_Sub' not in n) if lvl=='Step' else (lambda n:'_Sub' not in n)
        prev=[a for a in names if a<=T and names[a].startswith(base+'_') and ok(names[a])]
        parent=names[max(prev)] if prev else base
        for i,a in enumerate(tg):
            names.setdefault(a,f'{parent}_{lvl}{i}')
seen={}
for a in sorted(names):
    n=names[a]
    if n in seen:
        k=2
        while f'{n}_{k}' in seen: k+=1
        n=f'{n}_{k}'
    seen[n]=a; names[a]=n
with open('anno_auto.py','a') as f: f.write('AUTO_NAMES = '+repr(names)+'\n')
print('auto names',len(names))
