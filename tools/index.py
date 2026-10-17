import json,re,collections,sys
sys.path.insert(0,'.')
from hw import CUSTOM
t=json.load(open('trace.json'))
ins={int(k,16):v for k,v in t['insn'].items()}
labs={int(k,16):v for k,v in t['labels'].items()}
subs=sorted(a for a,k in labs.items() if k in('sub','entry'))
seeds=json.load(open('seeds.json'))
for s in seeds['code']: subs.append(int(s,16))
subs=sorted(set(subs))
starts=sorted(ins)
def owner(a):
    import bisect
    i=bisect.bisect_right(subs,a)-1
    return subs[i] if i>=0 else None
callers=collections.defaultdict(set); callees=collections.defaultdict(set)
hwu=collections.defaultdict(set); gv=collections.defaultdict(set); size=collections.Counter()
for a in starts:
    sz,m,op,hx=ins[a]; o=owner(a); size[o]+=sz
    if m.startswith(('bsr','jsr')):
        h=re.findall(r'\$([0-9a-f]+)',op)
        if h and '(' not in op or 'pc)' in op:
            tg=int(h[-1],16); callers[tg].add(o); callees[o].add(tg)
    for v in re.findall(r'\$(dff[0-9a-f]{3})',op): hwu[o].add(CUSTOM.get(int(v,16)-0xdff000,v))
    for v in re.findall(r'(?<![\w$-])\$([0-9a-f]+)\(a6\)',op): gv[o].add(int(v,16))
    if '(a6)' in op and not re.search(r'\$[0-9a-f]+\(a6\)',op): gv[o].add(0)
lo=int(sys.argv[1],16) if len(sys.argv)>1 else 0; hi=int(sys.argv[2],16) if len(sys.argv)>2 else 1<<30
for s in subs:
    if not lo<=s<hi: continue
    print(f"{s:05X} sz={size[s]:4} from={','.join(f'{c:X}' for c in sorted(x for x in callers[s] if x))[:60]} calls={','.join(f'{c:X}' for c in sorted(callees[s]))[:70]} hw={','.join(sorted(hwu[s]))[:50]} g={','.join(f'{v:X}' for v in sorted(gv[s]))[:80]}")
